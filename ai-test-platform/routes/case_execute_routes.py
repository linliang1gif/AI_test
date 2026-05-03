"""
测试用例一键执行路由 (Phase 11 + 12 + 13)

POST /api/v2/test-cases/{case_id}/execute

从数据库读取TestCase → 变量替换 → 真实HTTP请求 → 断言校验 → 写入RunCase
"""

import os
import uuid
import time
import json
import base64
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.session import get_db
from database.models import TestCase, TestRun, RunCase, Environment
from services.auth_service import AuthService
from services.variable_resolver import (
    resolve_variables, extract_variables, has_unresolved_variables,
    sanitize_sensitive_data,
)
from app.executor_v2.execution_engine import ExecutionEngineV2
from app.executor_v2.auth_manager import AuthManager
from app.executor_v2.models import (
    AssertionDef, AssertionResult, AssertionType, TestCaseV2, ExecutionResult, ExecutionStatus,
)

router = APIRouter(prefix="/api/v2/test-cases", tags=["TestCase-Execute"])

UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

def _get_app_mode() -> str:
    return os.getenv("APP_MODE", "mock")


# ---------- Request / Response Models ----------

class ExecuteRequest(BaseModel):
    environment_id: Optional[int] = Field(None, description="环境ID，提供base_url")
    base_url: Optional[str] = Field(None, description="直接指定base_url，优先于environment_id")
    dataset_id: Optional[str] = Field(None, description="数据集ID，用于变量替换")
    variables: Optional[Dict[str, Any]] = Field(None, description="直接传入变量，优先于dataset_id")
    allow_unsafe_methods: bool = Field(False, description="real模式下是否允许执行写操作")


class ExecuteResponse(BaseModel):
    success: bool
    run_id: str = ""
    case_id: str = ""
    status: str = ""
    message: str = ""
    duration_ms: float = 0
    assertion_summary: Optional[dict] = None
    assertion_details: Optional[list] = None
    request_snapshot: Optional[dict] = None
    response_snapshot: Optional[dict] = None
    error_message: str = ""


class BatchExecuteRequest(ExecuteRequest):
    case_ids: Optional[List[str]] = Field(None, description="测试用例ID列表（与 preset 二选一）")
    preset: Optional[str] = Field(None, description="推荐测试集: smoke/regression/query-safe/failed-rerun/p0")
    allow_write_operations: bool = Field(True, description="是否允许执行写操作接口（Dev环境默认允许）")
    skip_destructive: bool = Field(False, description="跳过 destructive=true 的用例")
    # allow_unsafe_methods inherited from ExecuteRequest


class BatchExecuteResponse(BaseModel):
    success: bool
    run_id: str = ""
    status: str = ""
    message: str = ""
    total_cases: int = 0
    passed_cases: int = 0
    failed_cases: int = 0
    skipped_cases: int = 0
    no_assertion_cases: int = 0
    error_cases: int = 0
    duration_ms: float = 0
    pass_rate: float = 0.0
    failure_categories: Dict[str, int] = {}
    skipped_reasons: Dict[str, int] = {}
    results: List[dict] = []


def _extract_module_prefix(url_path: str) -> str:
    """
    从 URL 路径提取模块前缀。
    例如: /basic/basicWarehouseInfo/list → /basic/basicWarehouseInfo
          /basic/basicCurrency/page → /basic/basicCurrency
    """
    import re
    # 去掉末尾的操作后缀
    cleaned = re.sub(r'/(page|list|detail|get|info|query|save|add|create|insert|update|edit|modify|delete|remove)$', '', url_path, flags=re.I)
    return cleaned


def _extract_uuid_from_response(body: dict) -> str:
    """
    从 list/page 接口响应中提取第一条数据的 uuid。
    支持格式:
      - {"code":200, "data": [{"uuid":"..."}, ...]}           (list)
      - {"code":200, "data": {"list": [{"uuid":"..."}, ...]}} (page)
    """
    if body.get("code") not in (200, "200", 0, "0"):
        return ""
    data = body.get("data")
    if isinstance(data, dict):
        items = data.get("list") or data.get("records") or data.get("rows") or []
    elif isinstance(data, list):
        items = data
    else:
        return ""
    if items and isinstance(items, list) and len(items) > 0:
        first = items[0]
        if isinstance(first, dict):
            return str(first.get("uuid") or first.get("id") or first.get("ID") or "")
    return ""


# Phase 16+18: 失败分类 (8 类) ── 统一分类函数
def _classify_failure_category(final_status: str, error_message: str, resp_snapshot: dict) -> str:
    err = (error_message or '').lower()
    sc = resp_snapshot.get('status_code', 0) if isinstance(resp_snapshot, dict) else 0
    body = resp_snapshot.get('body', {}) if isinstance(resp_snapshot, dict) else {}
    biz_code = body.get('code') if isinstance(body, dict) else None
    # 1. auth_error
    if sc in (401, 403) or 'unauthorized' in err or '401' in err or '403' in err:
        return 'auth_error'
    # 2. timeout_error
    if 'timeout' in err or 'timed out' in err:
        return 'timeout_error'
    # 3. env_error
    if 'connect' in err or 'connection' in err or 'dns' in err or 'refused' in err or (sc == 0 and err):
        return 'env_error'
    # 4. request_error
    if sc in (400, 405, 406, 415) or 'required' in err or 'missing' in err:
        return 'request_error'
    # 5. response_error
    if sc == 404 or sc >= 500:
        return 'response_error'
    # 6. dependency_error (biz code > 40000 = business status error)
    if isinstance(biz_code, int) and biz_code >= 40000:
        return 'dependency_error'
    if 'dependency' in err or '前置' in err or '依赖' in err or 'status not allowed' in err:
        return 'dependency_error'
    # 7. assertion_error
    if 'assert' in err or final_status == 'failed':
        return 'assertion_error'
    # 8. unknown_error
    return 'unknown_error'


def _detect_write_api(method: str, url: str) -> bool:
    method = (method or "").upper()
    url = (url or "").lower()
    if method in {"PUT", "PATCH", "DELETE"}:
        return True
    return any(key in url for key in ["/modify", "/update", "/save", "/add", "/create", "/delete", "/remove", "/import"])


# ---------- 路由 ----------

@router.post("/batch-execute", response_model=BatchExecuteResponse)
def batch_execute_test_cases(
    req: BatchExecuteRequest,
    db: Session = Depends(get_db),
):
    """
    批量执行接口测试用例（Phase 16）。

    多个用例共用一个 TestRun，每个用例写入一条 RunCase。
    """
    # Phase 16: 支持 preset 加载推荐测试集
    if req.preset and not req.case_ids:
        from services.case_governance_service import CaseGovernanceService
        gov_svc = CaseGovernanceService(db)
        preset_map = {
            'smoke': gov_svc.recommend_smoke,
            'regression': gov_svc.recommend_regression,
            'query-safe': gov_svc.recommend_query_safe,
            'failed-rerun': gov_svc.recommend_failed_rerun,
            'p0': gov_svc.recommend_p0,
        }
        loader = preset_map.get(req.preset)
        if not loader:
            raise HTTPException(status_code=400, detail=f"未知推荐集: {req.preset}，可选: {', '.join(preset_map.keys())}")
        preset_cases = loader(limit=2000)
        req.case_ids = [tc.id for tc in preset_cases]

    if not req.case_ids:
        raise HTTPException(status_code=400, detail="请选择要执行的测试用例或指定 preset")

    # 确定 base_url
    base_url = req.base_url or ""
    env_id = req.environment_id
    if not base_url and env_id:
        env = db.query(Environment).filter(Environment.id == env_id).first()
        if env:
            base_url = env.base_url
    if not base_url:
        envs = db.query(Environment).all()
        if envs:
            base_url = envs[0].base_url
            env_id = envs[0].id
    if not base_url:
        raise HTTPException(
            status_code=400,
            detail="未配置测试环境地址。请在请求中传入 base_url 或先在项目中创建环境。"
        )

    auth_context = _prepare_environment_auth(db, env_id)
    cases = db.query(TestCase).filter(TestCase.id.in_(req.case_ids)).all()
    found_ids = {tc.id for tc in cases}
    missing_ids = [cid for cid in req.case_ids if cid not in found_ids]
    if not cases:
        raise HTTPException(status_code=404, detail="未找到可执行的测试用例")

    # P2-3: 过滤掉 web_ui 用例
    web_ui_cases = [tc for tc in cases if getattr(tc, 'case_type', None) == 'web_ui']
    if web_ui_cases:
        cases = [tc for tc in cases if getattr(tc, 'case_type', None) != 'web_ui']
        if not cases:
            raise HTTPException(status_code=400, detail="所选用例均为 Web UI 用例，暂不支持执行。Playwright 执行引擎将在 P2-4 支持。")

    # 真实项目安全执行保护 — 批量
    app_mode = _get_app_mode()
    if app_mode == "real" and not req.allow_unsafe_methods:
        unsafe_cases = []
        for tc in cases:
            cfg = tc.execution_config or {}
            m = (cfg.get('method') or 'GET').upper()
            if m in UNSAFE_METHODS:
                unsafe_cases.append({"case_id": tc.id, "title": tc.title, "method": m, "url": cfg.get('url', '')})
        if unsafe_cases:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "REAL_MODE_UNSAFE_METHOD_BLOCKED",
                    "message": f"真实项目模式下默认禁止执行写操作，批量中包含 {len(unsafe_cases)} 个危险方法用例，请手动确认后再执行",
                    "unsafe_count": len(unsafe_cases),
                    "unsafe_cases": unsafe_cases[:20],
                    "app_mode": app_mode,
                }
            )

    skipped_write_cases = []
    skipped_destructive_cases = []    # list of tc.id
    skipped_destructive_info = []     # Phase 18: full info dicts
    # Phase 16+18: 跳过 destructive 用例
    if req.skip_destructive:
        safe = []
        for tc in cases:
            if getattr(tc, 'destructive', False):
                skipped_destructive_cases.append(tc.id)
                skipped_destructive_info.append({
                    "case_id": tc.id,
                    "case_name": tc.title,
                    "module_name": getattr(tc, 'module_name', '') or tc.module or '',
                    "risk_level": getattr(tc, 'risk_level', '') or '',
                })
            else:
                safe.append(tc)
        cases = safe

    if not req.allow_write_operations:
        safe_cases = []
        for tc in cases:
            exec_config = tc.execution_config or {}
            if _detect_write_api(exec_config.get("method"), exec_config.get("url")):
                skipped_write_cases.append(tc.id)
            else:
                safe_cases.append(tc)
        cases = safe_cases

    if not cases:
        raise HTTPException(
            status_code=400,
            detail=f"无可执行用例。跳过写操作: {len(skipped_write_cases)}，跳过破坏性: {len(skipped_destructive_cases)}"
        )

    # ---- 智能排序：查询类先执行，写操作类后执行 ----
    _PATTERN_ORDER = {"page": 0, "list": 1, "detail": 2, "other": 3, "save": 4, "update": 5, "delete": 6}
    def _sort_key(tc):
        cfg = tc.execution_config or {}
        p = _detect_api_pattern_from_url(cfg.get("url", ""))
        return _PATTERN_ORDER.get(p, 3)
    cases.sort(key=_sort_key)

    # uuid_pool: 按模块前缀存储从 list/page 接口提取的真实 uuid
    # key = 模块前缀 (如 "/basic/basicWarehouse"), value = uuid
    uuid_pool: Dict[str, str] = {}

    run_id = f"RUN_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
    trace_id = f"TRACE_{uuid.uuid4().hex}"
    start_time = datetime.now()
    engine = ExecutionEngineV2(base_url=base_url, auth_env_key=auth_context["env_key"], default_timeout=5.0)
    results = []
    counters = {"passed": 0, "failed": 0, "no_assertion": 0, "error": 0}

    test_run = TestRun(
        id=run_id,
        project_id=1,
        environment_id=env_id,
        trigger_type='manual_batch',
        status='running',
        trace_id=trace_id,
        start_time=start_time,
        total_cases=len(cases) + len(skipped_write_cases) + len(skipped_destructive_cases),
        passed_cases=0,
        failed_cases=0,
        skipped_cases=len(skipped_write_cases) + len(skipped_destructive_cases),
    )
    db.add(test_run)
    db.flush()

    for skipped_case_id in skipped_write_cases:
        db.add(RunCase(
            run_id=run_id,
            test_case_id=skipped_case_id,
            status="skipped",
            start_time=start_time,
            end_time=start_time,
            duration=0,
            error_message="写操作接口默认阻止执行",
            error_type="write_blocked",
            assertion_details=[],
        ))

    # Phase 18: 为 skipped destructive 用例写入 RunCase
    for skipped_case_id in skipped_destructive_cases:
        db.add(RunCase(
            run_id=run_id,
            test_case_id=skipped_case_id,
            status="skipped",
            start_time=start_time,
            end_time=start_time,
            duration=0,
            error_message="已跳过破坏性接口，避免修改或删除数据",
            error_type="destructive",
            assertion_details=[],
        ))

    variables = req.variables or (_load_dataset_variables(req.dataset_id, db) if req.dataset_id else {})

    for tc in cases:
        case_start = datetime.now()
        final_status = "error"
        error_message = ""
        req_snapshot = {}
        resp_snapshot = {}
        assertion_detail_list = []
        assertion_summary = {"total": 0, "passed": 0, "failed": 0}
        duration_ms = 0

        try:
            exec_config = tc.execution_config or {}
            if not exec_config.get('method') or not exec_config.get('url'):
                raise ValueError(f"用例 {tc.id} 缺少执行配置(method/url)")

            method = exec_config.get('method', 'GET').upper()
            url_path = exec_config.get('url', '/')
            headers = _merge_headers(auth_context["default_headers"], exec_config.get('headers', {}))
            query_params = exec_config.get('query_params', {})
            body = exec_config.get('body')
            if isinstance(body, dict):
                body = body.copy()
            timeout = exec_config.get('timeout', 30)

            cur_pattern = _detect_api_pattern_from_url(url_path)

            # ---- 数据关联：为写操作/详情接口注入真实 uuid ----
            if cur_pattern in ("update", "delete", "detail") and isinstance(body, dict):
                module_prefix = _extract_module_prefix(url_path)
                real_uuid = uuid_pool.get(module_prefix)
                if real_uuid:
                    if "uuid" in body or not body:
                        body["uuid"] = real_uuid

            if variables:
                url_path, m1 = resolve_variables(url_path, variables)
                headers, m2 = resolve_variables(headers, variables)
                query_params, m3 = resolve_variables(query_params, variables)
                body, m4 = resolve_variables(body, variables) if body else (body, [])
                missing_vars = list(dict.fromkeys(m1 + m2 + m3 + m4))
                if missing_vars:
                    raise ValueError(f"缺少变量: {', '.join(missing_vars)}")

            assertions = _convert_assertions(tc.assertions or [])
            has_assertions = len(assertions) > 0

            case_v2 = TestCaseV2(
                id=tc.id,
                title=tc.title,
                method=method,
                path=url_path,
                base_url=base_url,
                headers=headers if isinstance(headers, dict) else {},
                query_params=query_params if isinstance(query_params, dict) else {},
                body=body,
                timeout=timeout,
                assertions=assertions,
            )

            result = engine.execute_case(case_v2, run_id=run_id)
            _apply_business_code_assertion(result, url_path=url_path)
            final_status = result.status
            if not has_assertions and result.status == ExecutionStatus.PASSED.value:
                final_status = "no_assertion"

            duration_ms = result.duration_ms
            error_message = result.error_message or ""
            resp_snapshot = result.response.to_dict() if result.response else {}
            assertion_detail_list = [a.to_dict() for a in result.assertions] if result.assertions else []
            assertion_summary = result.assertion_summary if result.assertions else assertion_summary

            # ---- 数据关联：从 list/page 响应提取 uuid 存入池 ----
            if cur_pattern in ("page", "list") and result.response and isinstance(result.response.body, dict):
                module_prefix = _extract_module_prefix(url_path)
                extracted = _extract_uuid_from_response(result.response.body)
                if extracted and module_prefix:
                    uuid_pool[module_prefix] = extracted

            req_snapshot = result.request.to_dict() if result.request else {
                "method": method,
                "url": f"{base_url.rstrip('/')}/{url_path.lstrip('/')}",
                "headers": sanitize_sensitive_data(headers) if isinstance(headers, dict) else {},
                "query_params": query_params,
                "body": sanitize_sensitive_data(body) if isinstance(body, dict) else body,
            }
        except Exception as e:
            final_status = "error"
            error_message = str(e)
            duration_ms = (datetime.now() - case_start).total_seconds() * 1000

        counters[final_status if final_status in counters else "error"] += 1
        case_end = datetime.now()

        db.add(RunCase(
            run_id=run_id,
            test_case_id=tc.id,
            status=final_status,
            start_time=case_start,
            end_time=case_end,
            duration=duration_ms / 1000,
            error_message=error_message or None,
            request_snapshot=_json_safe(req_snapshot),
            response_snapshot=_json_safe(resp_snapshot),
            assertions_passed=assertion_summary.get("passed", 0),
            assertions_failed=assertion_summary.get("failed", 0),
            assertion_details=_json_safe(assertion_detail_list),
        ))

        tc.status = final_status
        tc.updated_at = datetime.now()
        # Phase 16: 写回治理字段
        tc.last_run_status = final_status
        if final_status in ('failed', 'error'):
            tc.failure_category = _classify_failure_category(
                final_status, error_message,
                resp_snapshot if isinstance(resp_snapshot, dict) else {}
            )
        else:
            tc.failure_category = None

        results.append({
            "case_id": tc.id,
            "case_name": tc.title,
            "status": final_status,
            "duration_ms": round(duration_ms, 2),
            "assertion_summary": assertion_summary,
            "error_message": error_message,
            "failure_category": tc.failure_category,
        })

    end_time = datetime.now()
    total_duration = (end_time - start_time).total_seconds()
    overall_status = "passed"
    if counters["error"] > 0:
        overall_status = "error"
    elif counters["failed"] > 0:
        overall_status = "failed"
    elif counters["no_assertion"] > 0 and counters["passed"] == 0:
        overall_status = "no_assertion"
    elif counters["no_assertion"] > 0:
        overall_status = "passed"

    # Phase 18: 聚合 failure_categories + skipped_reasons
    fc_agg = {}
    for r in results:
        cat = r.get("failure_category")
        if cat:
            fc_agg[cat] = fc_agg.get(cat, 0) + 1
    sk_reasons = {}
    if skipped_destructive_cases:
        sk_reasons["destructive"] = len(skipped_destructive_cases)
    if skipped_write_cases:
        sk_reasons["write_blocked"] = len(skipped_write_cases)

    total_all = len(cases) + len(skipped_write_cases) + len(skipped_destructive_cases)
    total_skipped = len(skipped_write_cases) + len(skipped_destructive_cases)
    executed_count = counters["passed"] + counters["failed"] + counters["error"] + counters["no_assertion"]
    pass_rate_val = round(counters["passed"] / max(executed_count, 1) * 100, 1)

    test_run.status = overall_status
    test_run.end_time = end_time
    test_run.duration = total_duration
    test_run.total_cases = total_all
    test_run.passed_cases = counters["passed"]
    test_run.failed_cases = counters["failed"] + counters["error"]
    test_run.skipped_cases = total_skipped
    test_run.summary = json.dumps({
        "app_mode": app_mode,
        "allow_unsafe_methods": req.allow_unsafe_methods,
        "missing_case_ids": missing_ids,
        "skipped_write_case_ids": skipped_write_cases,
        "skipped_destructive_case_ids": skipped_destructive_cases,
        "no_assertion_cases": counters["no_assertion"],
        "error_cases": counters["error"],
        "preset": req.preset or None,
        "failure_categories": fc_agg,
        "skipped_reasons": sk_reasons,
        "pass_rate": pass_rate_val,
    }, ensure_ascii=False)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"批量执行结果入库失败: {str(e)}")

    # Phase 18: 在 results 中追加 skipped 条目
    for info in skipped_destructive_info:
        results.append({
            "case_id": info["case_id"],
            "case_name": info["case_name"],
            "status": "skipped",
            "duration_ms": 0,
            "assertion_summary": {"total": 0, "passed": 0, "failed": 0},
            "error_message": "已跳过破坏性接口，避免修改或删除数据",
            "failure_category": None,
            "skipped_reason": "destructive",
            "skipped_message": "已跳过破坏性接口，避免修改或删除数据",
        })

    return BatchExecuteResponse(
        success=overall_status in ("passed", "no_assertion"),
        run_id=run_id,
        status=overall_status,
        message=f"批量执行完成：通过 {counters['passed']}，失败 {counters['failed']}，跳过 {total_skipped}，通过率 {pass_rate_val}%",
        total_cases=total_all,
        passed_cases=counters["passed"],
        failed_cases=counters["failed"] + counters["error"],
        skipped_cases=total_skipped,
        no_assertion_cases=counters["no_assertion"],
        error_cases=counters["error"],
        duration_ms=round(total_duration * 1000, 2),
        pass_rate=pass_rate_val,
        failure_categories=fc_agg,
        skipped_reasons=sk_reasons,
        results=results,
    )

def _execute_web_ui_case(tc, req, db):
    """P2-4: 执行 Web UI 用例并写入结果"""
    from services.playwright_engine import execute_web_ui, _is_playwright_available
    import uuid as _uuid

    if not _is_playwright_available():
        raise HTTPException(
            status_code=503,
            detail="Playwright 未安装。请运行: pip install playwright && python -m playwright install chromium"
        )

    exec_config = tc.execution_config or {}
    steps = tc.steps or []
    assertions = tc.assertions or []

    # P2-5: generate run_id first so visual regression can use it for file naming
    run_id = f"RUN_{datetime.now().strftime('%Y%m%d%H%M%S')}_{_uuid.uuid4().hex[:8]}"

    pw_result = execute_web_ui(
        steps=steps,
        assertions=assertions,
        execution_config=exec_config,
        case_id=tc.id,
        run_id=run_id,
    )

    if pw_result.status == "error" and "仅支持 chromium" in pw_result.error_message:
        raise HTTPException(status_code=400, detail=pw_result.error_message)
    final_status = pw_result.status if pw_result.status in ("passed", "failed") else "failed"

    try:
        test_run = TestRun(
            id=run_id,
            project_id=1,
            environment_id=req.environment_id if req.environment_id else None,
            trigger_type="manual",
            status=final_status,
            trace_id=f"TRACE_{_uuid.uuid4().hex}",
            start_time=datetime.fromisoformat(pw_result.started_at) if pw_result.started_at else datetime.now(),
            end_time=datetime.fromisoformat(pw_result.finished_at) if pw_result.finished_at else datetime.now(),
            duration=pw_result.duration_ms / 1000,
            total_cases=1,
            passed_cases=1 if final_status == "passed" else 0,
            failed_cases=1 if final_status == "failed" else 0,
            summary=json.dumps({"engine": "playwright", "case_type": "web_ui", "skipped_count": pw_result.skipped_count,
                                "has_high_risk_actions": pw_result.has_high_risk_actions}, ensure_ascii=False),
        )
        db.add(test_run)

        # 断言统计
        a_passed = sum(1 for a in pw_result.assertion_results if a.passed)
        a_failed = sum(1 for a in pw_result.assertion_results if not a.passed)
        assertion_details = [
            {"type": a.type, "value": a.value, "target": a.target, "passed": a.passed,
             "actual": a.actual, "error_message": a.error_message, "description": a.description}
            for a in pw_result.assertion_results
        ]

        run_case = RunCase(
            run_id=run_id,
            test_case_id=tc.id,
            status=final_status,
            start_time=test_run.start_time,
            end_time=test_run.end_time,
            duration=pw_result.duration_ms / 1000,
            error_message=pw_result.error_message or None,
            request_snapshot={"engine": "playwright", "steps_count": len(steps), "assertions_count": len(assertions)},
            response_snapshot={"screenshots": [sr.screenshot_path for sr in pw_result.step_results if sr.screenshot_path],
                               "failure_screenshot": pw_result.failure_screenshot,
                               "visual_results": pw_result.visual_results,
                               "trace_path": pw_result.trace_path,
                               "console_error_count": len(pw_result.console_logs),
                               "network_error_count": len(pw_result.network_errors)},
            assertions_passed=a_passed,
            assertions_failed=a_failed,
            assertion_details=assertion_details,
        )
        db.add(run_case)
        db.flush()  # 获取 run_case.id

        # 写入 run_steps
        from database.models import RunStep
        for sr in pw_result.step_results:
            # P2-6A.1: sanitize high-risk action data in run_steps
            step_target = sr.target
            step_value = sr.value
            if sr.action == "eval_js":
                step_target = (sr.target[:50] + "…") if len(sr.target) > 50 else sr.target
                step_value = "[JS]"
            elif sr.action == "save_cookies":
                step_value = "[cookie_data]"
            run_step = RunStep(
                run_case_id=run_case.id,
                step_name=f"{sr.action}: {step_target or step_value or sr.description}",
                step_order=sr.step_index,
                status=sr.status,
                start_time=test_run.start_time,
                end_time=test_run.end_time,
                duration=sr.duration_ms / 1000,
                input_snapshot={
                    "action": sr.action,
                    "target": step_target,
                    "value": step_value,
                    "description": sr.description,
                },
                output_snapshot={
                    "current_url": sr.current_url,
                    "screenshot_path": sr.screenshot_path,
                },
                error_message=sr.error_message or None,
                error_type="step_error" if sr.status == "failed" else None,
            )
            db.add(run_step)

        # 断言也作为 step 记录
        for i, ar in enumerate(pw_result.assertion_results):
            run_step = RunStep(
                run_case_id=run_case.id,
                step_name=f"assert:{ar.type} — {ar.description or ar.value}",
                step_order=len(pw_result.step_results) + i,
                status="passed" if ar.passed else "failed",
                start_time=test_run.start_time,
                end_time=test_run.end_time,
                duration=0,
                input_snapshot={
                    "type": ar.type,
                    "target": ar.target,
                    "value": ar.value,
                    "description": ar.description,
                },
                output_snapshot={
                    "actual": ar.actual,
                    "passed": ar.passed,
                },
                error_message=ar.error_message or None,
                error_type="assertion_error" if not ar.passed else None,
            )
            db.add(run_step)

        # 更新用例状态
        tc.status = final_status
        tc.updated_at = datetime.now()
        tc.last_run_status = final_status
        if final_status == "failed":
            tc.failure_category = "ui_step_error"
        else:
            tc.failure_category = None

        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"Web UI 执行结果写入失败: {e}")

    return ExecuteResponse(
        success=True,
        case_id=tc.id,
        run_id=run_id,
        status=final_status,
        duration_ms=round(pw_result.duration_ms, 2),
        assertion_summary={"passed": a_passed if pw_result.assertion_results else 0,
                           "failed": a_failed if pw_result.assertion_results else 0},
        assertion_details=assertion_details if pw_result.assertion_results else [],
        error_message=pw_result.error_message or "",
        request_snapshot={"engine": "playwright"},
        response_snapshot={
            "failure_screenshot": pw_result.failure_screenshot,
            "skipped_count": pw_result.skipped_count,
            "step_results": [
                {"index": sr.step_index, "action": sr.action, "target": sr.target,
                 "status": sr.status, "duration_ms": round(sr.duration_ms, 2),
                 "error": sr.error_message, "screenshot": sr.screenshot_path,
                 "url": sr.current_url, "description": sr.description}
                for sr in pw_result.step_results
            ],
            "visual_results": pw_result.visual_results,
            "has_high_risk_actions": pw_result.has_high_risk_actions,
            "trace_path": pw_result.trace_path,
            "console_logs": pw_result.console_logs[:50],
            "network_errors": pw_result.network_errors[:50],
        },
    )


@router.post("/{case_id}/execute", response_model=ExecuteResponse)
def execute_test_case(
    case_id: str,
    req: ExecuteRequest = ExecuteRequest(),
    db: Session = Depends(get_db),
):
    """
    一键执行接口测试用例。

    1. 从数据库读取TestCase及其execution_config
    2. 解析变量并替换（如有dataset_id）
    3. 调用ExecutionEngineV2发送真实HTTP请求
    4. 执行断言校验
    5. 结果写入TestRun + RunCase表
    """
    # 1. 查找测试用例
    tc = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not tc:
        raise HTTPException(status_code=404, detail=f"测试用例不存在: {case_id}")

    # P2-4: web_ui 用例走 PlaywrightEngine
    if getattr(tc, 'case_type', None) == 'web_ui' or (tc.execution_config or {}).get('engine') == 'playwright':
        return _execute_web_ui_case(tc, req, db)

    exec_config = tc.execution_config or {}
    if not exec_config.get('method') or not exec_config.get('url'):
        raise HTTPException(
            status_code=400,
            detail=f"用例 {case_id} 缺少执行配置(method/url)，无法执行接口测试"
        )

    # 1.5 真实项目安全执行保护
    app_mode = _get_app_mode()
    method_upper = (exec_config.get('method', 'GET')).upper()
    if app_mode == "real" and method_upper in UNSAFE_METHODS and not req.allow_unsafe_methods:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "REAL_MODE_UNSAFE_METHOD_BLOCKED",
                "message": "真实项目模式下默认禁止执行写操作，请手动确认后再执行",
                "method": method_upper,
                "url": exec_config.get('url', ''),
                "app_mode": app_mode,
            }
        )

    # 2. 确定 base_url
    base_url = req.base_url or ""
    env_id = req.environment_id
    if not base_url and env_id:
        env = db.query(Environment).filter(Environment.id == env_id).first()
        if env:
            base_url = env.base_url
    if not base_url:
        # 尝试从项目的第一个环境获取
        envs = db.query(Environment).all()
        if envs:
            base_url = envs[0].base_url
            env_id = envs[0].id
    if not base_url:
        raise HTTPException(
            status_code=400,
            detail="未配置测试环境地址。请在请求中传入 base_url 或先在项目中创建环境。"
        )
    auth_context = _prepare_environment_auth(db, env_id)

    # 3. 准备请求数据
    method = exec_config.get('method', 'GET').upper()
    url_path = exec_config.get('url', '/')
    headers = _merge_headers(auth_context["default_headers"], exec_config.get('headers', {}))
    query_params = exec_config.get('query_params', {})
    body = exec_config.get('body')
    timeout = exec_config.get('timeout', 30)

    # 4. 变量替换 (Phase 12)
    variables = {}
    if req.variables:
        variables = req.variables
    elif req.dataset_id:
        variables = _load_dataset_variables(req.dataset_id, db)

    missing_vars = []
    if variables:
        url_path, m1 = resolve_variables(url_path, variables)
        headers, m2 = resolve_variables(headers, variables)
        query_params, m3 = resolve_variables(query_params, variables)
        body, m4 = resolve_variables(body, variables) if body else (body, [])
        missing_vars = list(dict.fromkeys(m1 + m2 + m3 + m4))

        if missing_vars:
            raise HTTPException(
                status_code=400,
                detail=f"缺少变量: {', '.join(missing_vars)}。请检查数据集是否包含这些变量。"
            )

        # 检查替换后是否还有未处理的变量
        unresolved = has_unresolved_variables(body) if body else []
        unresolved += has_unresolved_variables(url_path)
        if unresolved:
            raise HTTPException(
                status_code=400,
                detail=f"变量未完全替换: {', '.join(unresolved)}"
            )

    # 5. 构建断言 (Phase 13)
    raw_assertions = tc.assertions or []
    assertions = _convert_assertions(raw_assertions)
    has_assertions = len(assertions) > 0

    # 6. 构建 TestCaseV2 并执行
    case_v2 = TestCaseV2(
        id=tc.id,
        title=tc.title,
        method=method,
        path=url_path,
        base_url=base_url,
        headers=headers if isinstance(headers, dict) else {},
        query_params=query_params if isinstance(query_params, dict) else {},
        body=body,
        timeout=timeout,
        assertions=assertions,
    )

    try:
        engine = ExecutionEngineV2(base_url=base_url, auth_env_key=auth_context["env_key"])
        run_id = f"RUN_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
        result = engine.execute_case(case_v2, run_id=run_id)
        _apply_business_code_assertion(result, url_path=url_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行引擎异常: {str(e)}")

    # 7. 判定最终状态 (Phase 13: 无断言 → no_assertion)
    final_status = result.status
    if not has_assertions and result.status == ExecutionStatus.PASSED.value:
        final_status = "no_assertion"

    # 8. 写入数据库
    try:
        # 创建 TestRun
        run_summary = json.dumps({
            "app_mode": app_mode,
            "allow_unsafe_methods": req.allow_unsafe_methods,
        }, ensure_ascii=False)
        test_run = TestRun(
            id=run_id,
            project_id=1,  # 默认项目
            environment_id=env_id,
            trigger_type='manual',
            status=final_status,
            trace_id=f"TRACE_{uuid.uuid4().hex}",
            start_time=datetime.fromisoformat(result.started_at) if result.started_at else datetime.now(),
            end_time=datetime.fromisoformat(result.finished_at) if result.finished_at else datetime.now(),
            duration=result.duration_ms / 1000,
            total_cases=1,
            passed_cases=1 if final_status == 'passed' else 0,
            failed_cases=1 if final_status in ('failed', 'error') else 0,
            summary=run_summary,
        )
        db.add(test_run)

        # 构建快照（脱敏）
        req_snapshot = result.request.to_dict() if result.request else {
            "method": method,
            "url": f"{base_url.rstrip('/')}/{url_path.lstrip('/')}",
            "headers": sanitize_sensitive_data(headers) if isinstance(headers, dict) else {},
            "query_params": query_params,
            "body": sanitize_sensitive_data(body) if isinstance(body, dict) else body,
        }
        resp_snapshot = result.response.to_dict() if result.response else {}

        assertion_detail_list = [a.to_dict() for a in result.assertions] if result.assertions else []

        # 创建 RunCase
        run_case = RunCase(
            run_id=run_id,
            test_case_id=tc.id,
            status=final_status,
            start_time=test_run.start_time,
            end_time=test_run.end_time,
            duration=result.duration_ms / 1000,
            error_message=result.error_message or None,
            request_snapshot=req_snapshot,
            response_snapshot=resp_snapshot,
            assertions_passed=sum(1 for a in result.assertions if a.passed) if result.assertions else 0,
            assertions_failed=sum(1 for a in result.assertions if not a.passed) if result.assertions else 0,
            assertion_details=assertion_detail_list,
        )
        db.add(run_case)

        # 更新用例状态
        tc.status = final_status
        tc.updated_at = datetime.now()
        # Phase 16: 写回治理字段
        tc.last_run_status = final_status
        if final_status in ('failed', 'error'):
            tc.failure_category = _classify_failure_category(
                final_status, result.error_message or '',
                resp_snapshot if isinstance(resp_snapshot, dict) else {}
            )
        else:
            tc.failure_category = None

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"⚠️  写入执行记录失败: {e}")

    # 9. 返回结果
    return ExecuteResponse(
        success=final_status in ('passed', 'no_assertion'),
        run_id=run_id,
        case_id=tc.id,
        status=final_status,
        message=_status_message(final_status, has_assertions),
        duration_ms=round(result.duration_ms, 2),
        assertion_summary=result.assertion_summary if result.assertions else {"total": 0, "passed": 0, "failed": 0},
        assertion_details=assertion_detail_list if 'assertion_detail_list' in dir() else [],
        request_snapshot=req_snapshot if 'req_snapshot' in dir() else None,
        response_snapshot=resp_snapshot if 'resp_snapshot' in dir() else None,
        error_message=result.error_message or "",
    )


@router.post("/{case_id}/preview-variables")
async def preview_variables(
    case_id: str,
    dataset_id: Optional[str] = None,
    variables: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
):
    """预览变量替换结果（不实际执行）"""
    tc = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not tc:
        raise HTTPException(status_code=404, detail=f"测试用例不存在: {case_id}")

    exec_config = tc.execution_config or {}
    body = exec_config.get('body')
    url_path = exec_config.get('url', '/')
    headers = exec_config.get('headers', {})

    # 提取所有变量
    all_vars = extract_variables(body) + extract_variables(url_path) + extract_variables(headers)
    all_vars = list(dict.fromkeys(all_vars))

    # 加载数据集
    ds_vars = {}
    if variables:
        ds_vars = variables
    elif dataset_id:
        ds_vars = _load_dataset_variables(dataset_id, db)

    # 构建预览
    preview = []
    for var_name in all_vars:
        preview.append({
            "name": var_name,
            "value": ds_vars.get(var_name),
            "missing": var_name not in ds_vars,
        })

    has_missing = any(p["missing"] for p in preview)

    return {
        "success": True,
        "variables": preview,
        "has_missing": has_missing,
        "total": len(all_vars),
        "resolved": len([p for p in preview if not p["missing"]]),
    }


# ---------- 辅助函数 ----------

def _load_dataset_variables(dataset_id: str, db: Session) -> Dict[str, Any]:
    """从数据集加载变量"""
    # 尝试从内存数据管理器加载
    try:
        from app.core.data_manager import DataManager
        dm = DataManager()
        datasets = dm.get_data("datasets") or []
        for ds in datasets:
            if str(ds.get('id')) == str(dataset_id):
                return ds.get('variables', {}) or ds.get('data', {}) or {}
    except Exception:
        pass
    return {}


def _json_safe(value):
    """确保JSON字段在旧SQLite表结构中也能安全写入"""
    return json.loads(json.dumps(value, ensure_ascii=False, default=str))


def _merge_headers(default_headers: Optional[Dict[str, str]], case_headers: Any) -> Dict[str, str]:
    headers = {}
    if isinstance(default_headers, dict):
        headers.update(default_headers)
    if isinstance(case_headers, dict):
        headers.update(case_headers)
    return headers


def _prepare_environment_auth(db: Session, env_id: Optional[int]) -> Dict[str, Any]:
    env_key = f"env_{env_id}" if env_id else "default"
    context = {"env_key": env_key, "default_headers": {}}
    if not env_id:
        return context

    try:
        service = AuthService(db)
        auth_profile = service.get_by_environment(env_id)
        if not auth_profile:
            AuthManager.clear_token(env_key)
            return context

        context["default_headers"] = auth_profile.default_headers or {}
        auth_config = service.get_decrypted_config(auth_profile) or {}
        if isinstance(auth_config, str):
            auth_config = json.loads(auth_config)
        auth_type = auth_profile.auth_type

        if auth_type == "none":
            AuthManager.clear_token(env_key)
        elif auth_type == "bearer":
            token = auth_config.get("token", "")
            if token:
                AuthManager.set_token(token=token, auth_type="bearer", env_key=env_key)
        elif auth_type == "basic":
            username = auth_config.get("username", "")
            password = auth_config.get("password", "")
            if username or password:
                token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8")
                AuthManager.set_token(token=token, auth_type="basic", env_key=env_key)
        elif auth_type == "oauth2":
            # 自动获取 OAuth2 Token（带缓存和自动刷新）
            from app.executor_v2.oauth2_token_fetcher import fetch_oauth2_token
            try:
                access_token, token_type = fetch_oauth2_token(auth_config, env_key=env_key)
                AuthManager.set_token(
                    token=access_token,
                    auth_type="custom",
                    env_key=env_key,
                    extra={"header_name": "Authorization", "prefix": f"{token_type} "},
                )
            except Exception as e:
                print(f"⚠️  OAuth2 自动获取 Token 失败: {e}")
                # 回退: 尝试使用配置中的静态 access_token
                fallback_token = auth_config.get("access_token", "")
                if fallback_token:
                    token_type = auth_config.get("token_type", "Bearer")
                    AuthManager.set_token(token=fallback_token, auth_type="custom", env_key=env_key, extra={"header_name": "Authorization", "prefix": f"{token_type} "})
        elif auth_type == "apikey":
            token = auth_config.get("key_value", "")
            header_name = auth_config.get("key_name", "X-API-Key")
            if token:
                AuthManager.set_token(token=token, auth_type="api_key", env_key=env_key, extra={"header_name": header_name})
        elif auth_type == "cookie":
            token = auth_config.get("token") or auth_config.get("cookie_value", "")
            cookie_name = auth_config.get("cookie_name", "session")
            if token:
                AuthManager.set_token(token=token, auth_type="cookie", env_key=env_key, extra={"cookie_name": cookie_name})
        elif auth_type == "custom":
            token = auth_config.get("token") or auth_config.get("value", "")
            header_name = auth_config.get("header_name", "Authorization")
            prefix = auth_config.get("prefix", "")
            if token:
                AuthManager.set_token(token=token, auth_type="custom", env_key=env_key, extra={"header_name": header_name, "prefix": prefix})
    except Exception as e:
        print(f"⚠️  加载环境鉴权配置失败: {e}")
    return context


def _detect_api_pattern_from_url(url: str) -> str:
    """从 URL 路径检测接口模式"""
    url_lower = (url or "").lower()
    if url_lower.endswith("/page"):
        return "page"
    if url_lower.endswith("/list"):
        return "list"
    for suffix in ("/detail", "/get", "/info", "/query"):
        if url_lower.endswith(suffix):
            return "detail"
    for suffix in ("/save", "/add", "/create", "/insert"):
        if url_lower.endswith(suffix):
            return "save"
    for suffix in ("/update", "/edit", "/modify"):
        if url_lower.endswith(suffix):
            return "update"
    for suffix in ("/delete", "/remove"):
        if url_lower.endswith(suffix):
            return "delete"
    return "other"


# 写操作接口允许的业务错误码（参数不全、数据不存在等属于正常连通性验证）
_WRITE_ACCEPTABLE_CODES = {
    400, 10000, 1100001, 1100002, 1100003, 1100004, 1100005,
    "400", "10000", "1100001", "1100002", "1100003", "1100004", "1100005",
}


def _apply_business_code_assertion(result: ExecutionResult, url_path: str = "") -> None:
    if not result.response or not isinstance(result.response.body, dict):
        return
    body = result.response.body
    if "code" not in body:
        return

    actual = body.get("code")
    pattern = _detect_api_pattern_from_url(url_path)
    is_write_api = pattern in ("save", "update", "delete")

    # 查询类：必须 code=200
    # 写操作类：code=200 通过，业务错误码也算"连通性通过"
    if actual in (0, 200, "0", "200"):
        passed = True
        message = ""
    elif is_write_api and (actual in _WRITE_ACCEPTABLE_CODES or isinstance(actual, int) and actual > 1000):
        passed = True
        message = f"写操作连通性验证通过(业务码: code={actual}, message={body.get('message') or body.get('msg') or ''})"
    else:
        passed = False
        message = f"业务响应码异常: code={actual}, message={body.get('message') or body.get('msg') or ''}"

    expected_desc = [0, 200] if not is_write_api else [0, 200, "或业务错误码(连通性)"]
    assertion = AssertionResult(
        type="business_code",
        passed=passed,
        expected=expected_desc,
        actual=actual,
        path="code",
        message=message,
    )
    result.assertions.append(assertion)
    if not passed and result.status == ExecutionStatus.PASSED.value:
        result.status = ExecutionStatus.FAILED.value


def _convert_assertions(raw_assertions: list) -> list:
    """
    将数据库中的断言格式转换为 AssertionDef 列表。
    兼容 Swagger 生成的格式和标准格式。
    """
    defs = []
    for a in raw_assertions:
        if not isinstance(a, dict):
            continue
        a_type = a.get('type', '')

        if a_type == 'status_code':
            defs.append(AssertionDef(
                type=AssertionType.STATUS_CODE.value,
                expected=a.get('expected'),
                operator=a.get('operator', 'eq'),
            ))
        elif a_type == 'response_time_less_than':
            defs.append(AssertionDef(
                type=AssertionType.RESPONSE_TIME.value,
                expected=a.get('expected', 10000),
            ))
        elif a_type == 'json_path_equals':
            path = a.get('path', '').lstrip('$.')
            defs.append(AssertionDef(
                type=AssertionType.JSON_PATH.value,
                path=path,
                expected=a.get('expected'),
                operator='eq',
            ))
        elif a_type == 'json_path_exists':
            path = a.get('path', '').lstrip('$.')
            defs.append(AssertionDef(
                type=AssertionType.FIELD_EXISTS.value,
                path=path,
            ))
        elif a_type == 'json_path_not_empty':
            path = a.get('path', '').lstrip('$.')
            defs.append(AssertionDef(
                type=AssertionType.FIELD_EXISTS.value,
                path=path,
            ))
        elif a_type == 'contains':
            defs.append(AssertionDef(
                type=AssertionType.CONTAINS.value,
                expected=a.get('expected', ''),
            ))
        elif a_type == 'json_path':
            # Swagger 生成格式: {"type": "json_path", "field": "code", "operator": "exists"}
            field = a.get('field', a.get('path', ''))
            op = a.get('operator', 'eq')
            if op == 'exists':
                defs.append(AssertionDef(
                    type=AssertionType.FIELD_EXISTS.value,
                    path=field,
                ))
            elif op == 'type_check':
                # 类型检查断言 → 转为存在性检查
                defs.append(AssertionDef(
                    type=AssertionType.FIELD_EXISTS.value,
                    path=field,
                ))
            else:
                defs.append(AssertionDef(
                    type=AssertionType.JSON_PATH.value,
                    path=field,
                    expected=a.get('expected'),
                    operator=op,
                ))
        else:
            # 尝试通用处理
            if a.get('path') or a.get('field'):
                defs.append(AssertionDef(
                    type=AssertionType.JSON_PATH.value,
                    path=a.get('path', a.get('field', '')),
                    expected=a.get('expected'),
                    operator=a.get('operator', 'eq'),
                ))

    return defs


def _status_message(status: str, has_assertions: bool) -> str:
    """生成状态消息"""
    if status == 'passed':
        return "执行完成，所有断言通过"
    elif status == 'no_assertion':
        return "执行完成，但无断言规则，建议添加断言"
    elif status == 'failed':
        return "执行完成，部分断言失败"
    elif status == 'error':
        return "执行出错"
    else:
        return f"执行状态: {status}"


# ---------- Token 快捷更新 ----------

@router.post("/quick-token")
async def update_quick_token(request: dict, db: Session = Depends(get_db)):
    """
    快捷更新环境 Bearer Token（前端一键粘贴）。
    请求体: {"token": "eyJ...", "environment_id": 1}
    """
    token = (request.get("token") or "").strip()
    env_id = request.get("environment_id", 1)
    if not token:
        raise HTTPException(status_code=400, detail="请提供 token")

    # 更新 auth_profiles 表
    service = AuthService(db)
    auth_profile = service.get_by_environment(env_id)
    if not auth_profile:
        raise HTTPException(status_code=404, detail=f"未找到环境 {env_id} 的认证配置")

    # 解析 JWT 提取 pin（如有）
    pin = ""
    try:
        import base64 as b64
        payload = token.split(".")[1]
        payload += "=" * (4 - len(payload) % 4)
        decoded = json.loads(b64.urlsafe_b64decode(payload))
        pin = str(decoded.get("pin", ""))
    except Exception:
        pass

    # 更新配置
    new_config = {"token": token, "header_name": "Authorization", "prefix": "Bearer "}
    encoded = base64.b64encode(json.dumps(new_config).encode()).decode()
    auth_profile.auth_type = "custom"
    auth_profile.auth_config = encoded

    # 更新 default_headers 中的 pin
    headers = auth_profile.default_headers or {}
    if isinstance(headers, str):
        try:
            headers = json.loads(headers)
        except Exception:
            headers = {}
    if pin:
        headers["pin"] = pin
    headers.setdefault("Content-Type", "application/json")
    auth_profile.default_headers = headers

    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(auth_profile, "auth_config")
    flag_modified(auth_profile, "default_headers")
    db.commit()

    # 立即刷新内存中的 token
    env_key = f"env_{env_id}"
    AuthManager.set_token(token=token, auth_type="custom", env_key=env_key,
                          extra={"header_name": "Authorization", "prefix": "Bearer "})

    return {
        "success": True,
        "message": f"Token 已更新 (pin={pin or '未检测到'})",
        "environment_id": env_id,
        "pin": pin,
    }
