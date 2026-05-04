#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P2-10: 测试集管理路由
POST   /api/v2/test-suites                     创建测试集
GET    /api/v2/test-suites                     查询测试集列表
GET    /api/v2/test-suites/{suite_id}          查看详情
PUT    /api/v2/test-suites/{suite_id}          更新测试集
DELETE /api/v2/test-suites/{suite_id}          软删除
POST   /api/v2/test-suites/{suite_id}/cases    添加用例
DELETE /api/v2/test-suites/{suite_id}/cases/{case_id}  移除用例
POST   /api/v2/test-suites/{suite_id}/run      执行测试集
"""
import os
import json
import time
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.session import get_db
from database.models import TestSuite, TestSuiteCase, TestCase, TestRun, RunCase, TestDataBinding

logger = logging.getLogger("test_suite_routes")

router = APIRouter(prefix="/api/v2/test-suites", tags=["test-suites"])

VALID_SUITE_TYPES = ["smoke", "regression", "release", "api", "web_ui", "visual", "performance", "mixed"]
VALID_PRIORITIES = ["critical", "high", "medium", "low"]


# ── Request / Response Models ──

class CreateSuiteRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    project_id: Optional[int] = None
    suite_type: str = "mixed"
    priority: str = "medium"
    created_by: str = "system"

class UpdateSuiteRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    suite_type: Optional[str] = None
    priority: Optional[str] = None
    project_id: Optional[int] = None

class AddCasesRequest(BaseModel):
    case_ids: List[str]

class RunSuiteRequest(BaseModel):
    environment_id: Optional[int] = None
    base_url: Optional[str] = ""
    allow_unsafe_methods: bool = False


# ── Helpers ──

def _suite_to_dict(suite: TestSuite, include_cases: bool = False, db: Session = None) -> dict:
    d = {
        "id": suite.id,
        "name": suite.name,
        "description": suite.description or "",
        "project_id": suite.project_id,
        "suite_type": suite.suite_type,
        "priority": suite.priority,
        "status": suite.status,
        "created_by": suite.created_by,
        "created_at": suite.created_at.isoformat() if suite.created_at else None,
        "updated_at": suite.updated_at.isoformat() if suite.updated_at else None,
        "case_count": len([sc for sc in suite.suite_cases if sc.enabled]) if suite.suite_cases else 0,
    }
    if include_cases and suite.suite_cases:
        cases = []
        for sc in sorted(suite.suite_cases, key=lambda x: x.sort_order or 0):
            case_info = {
                "id": sc.id,
                "case_id": sc.case_id,
                "case_type": sc.case_type,
                "sort_order": sc.sort_order,
                "enabled": sc.enabled,
            }
            if db:
                tc = db.query(TestCase).filter(TestCase.id == sc.case_id).first()
                if tc:
                    case_info["title"] = tc.title
                    case_info["module"] = tc.module
                    case_info["priority"] = tc.priority
                    case_info["status"] = tc.status
            cases.append(case_info)
        d["cases"] = cases
    return d


# ── 1. POST /api/v2/test-suites ──

@router.post("")
def create_suite(req: CreateSuiteRequest, db: Session = Depends(get_db)):
    if req.suite_type not in VALID_SUITE_TYPES:
        raise HTTPException(400, f"Invalid suite_type: {req.suite_type}. Must be one of {VALID_SUITE_TYPES}")
    if req.priority not in VALID_PRIORITIES:
        raise HTTPException(400, f"Invalid priority: {req.priority}. Must be one of {VALID_PRIORITIES}")

    suite = TestSuite(
        name=req.name,
        description=req.description or "",
        project_id=req.project_id,
        suite_type=req.suite_type,
        priority=req.priority,
        created_by=req.created_by,
    )
    db.add(suite)
    db.commit()
    db.refresh(suite)
    return {"success": True, "suite_id": suite.id, "data": _suite_to_dict(suite)}


# ── 2. GET /api/v2/test-suites ──

@router.get("")
def list_suites(
    project_id: Optional[int] = None,
    suite_type: Optional[str] = None,
    keyword: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    q = db.query(TestSuite).filter(TestSuite.status != "deleted")
    if project_id is not None:
        q = q.filter(TestSuite.project_id == project_id)
    if suite_type:
        q = q.filter(TestSuite.suite_type == suite_type)
    if keyword:
        q = q.filter(TestSuite.name.like(f"%{keyword}%"))
    total = q.count()
    suites = q.order_by(TestSuite.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "data": [_suite_to_dict(s) for s in suites],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


# ── 3. GET /api/v2/test-suites/{suite_id} ──

@router.get("/{suite_id}")
def get_suite(suite_id: int, db: Session = Depends(get_db)):
    suite = db.query(TestSuite).filter(TestSuite.id == suite_id, TestSuite.status != "deleted").first()
    if not suite:
        raise HTTPException(404, f"测试集不存在: {suite_id}")
    return {"data": _suite_to_dict(suite, include_cases=True, db=db)}


# ── 4. PUT /api/v2/test-suites/{suite_id} ──

@router.put("/{suite_id}")
def update_suite(suite_id: int, req: UpdateSuiteRequest, db: Session = Depends(get_db)):
    suite = db.query(TestSuite).filter(TestSuite.id == suite_id, TestSuite.status != "deleted").first()
    if not suite:
        raise HTTPException(404, f"测试集不存在: {suite_id}")
    if req.name is not None:
        suite.name = req.name
    if req.description is not None:
        suite.description = req.description
    if req.suite_type is not None:
        if req.suite_type not in VALID_SUITE_TYPES:
            raise HTTPException(400, f"Invalid suite_type: {req.suite_type}")
        suite.suite_type = req.suite_type
    if req.priority is not None:
        if req.priority not in VALID_PRIORITIES:
            raise HTTPException(400, f"Invalid priority: {req.priority}")
        suite.priority = req.priority
    if req.project_id is not None:
        suite.project_id = req.project_id
    suite.updated_at = datetime.now()
    db.commit()
    db.refresh(suite)
    return {"success": True, "data": _suite_to_dict(suite)}


# ── 5. DELETE /api/v2/test-suites/{suite_id} ──

@router.delete("/{suite_id}")
def delete_suite(suite_id: int, db: Session = Depends(get_db)):
    suite = db.query(TestSuite).filter(TestSuite.id == suite_id, TestSuite.status != "deleted").first()
    if not suite:
        raise HTTPException(404, f"测试集不存在: {suite_id}")
    suite.status = "deleted"
    suite.updated_at = datetime.now()
    db.commit()
    return {"success": True, "message": f"测试集 {suite_id} 已删除"}


# ── 6. POST /api/v2/test-suites/{suite_id}/cases ──

@router.post("/{suite_id}/cases")
def add_cases(suite_id: int, req: AddCasesRequest, db: Session = Depends(get_db)):
    suite = db.query(TestSuite).filter(TestSuite.id == suite_id, TestSuite.status != "deleted").first()
    if not suite:
        raise HTTPException(404, f"测试集不存在: {suite_id}")

    if not req.case_ids:
        raise HTTPException(400, "case_ids 不能为空")

    added = []
    skipped = []
    errors = []
    max_order = db.query(TestSuiteCase).filter(TestSuiteCase.suite_id == suite_id).count()

    for cid in req.case_ids:
        tc = db.query(TestCase).filter(TestCase.id == cid).first()
        if not tc:
            errors.append({"case_id": cid, "reason": "用例不存在"})
            continue
        existing = db.query(TestSuiteCase).filter(
            TestSuiteCase.suite_id == suite_id,
            TestSuiteCase.case_id == cid,
        ).first()
        if existing:
            skipped.append(cid)
            continue
        sc = TestSuiteCase(
            suite_id=suite_id,
            case_id=cid,
            case_type=getattr(tc, "case_type", "api") or "api",
            sort_order=max_order,
            enabled=True,
        )
        db.add(sc)
        max_order += 1
        added.append(cid)

    db.commit()
    return {
        "success": True,
        "added": added,
        "skipped": skipped,
        "errors": errors,
        "total_cases": db.query(TestSuiteCase).filter(TestSuiteCase.suite_id == suite_id).count(),
    }


# ── 7. DELETE /api/v2/test-suites/{suite_id}/cases/{case_id} ──

@router.delete("/{suite_id}/cases/{case_id}")
def remove_case(suite_id: int, case_id: str, db: Session = Depends(get_db)):
    suite = db.query(TestSuite).filter(TestSuite.id == suite_id, TestSuite.status != "deleted").first()
    if not suite:
        raise HTTPException(404, f"测试集不存在: {suite_id}")
    sc = db.query(TestSuiteCase).filter(
        TestSuiteCase.suite_id == suite_id,
        TestSuiteCase.case_id == case_id,
    ).first()
    if not sc:
        raise HTTPException(404, f"用例 {case_id} 不在测试集 {suite_id} 中")
    db.delete(sc)
    db.commit()
    return {"success": True, "message": f"用例 {case_id} 已从测试集移除"}


# ── 8. POST /api/v2/test-suites/{suite_id}/run ──

@router.post("/{suite_id}/run")
def run_suite(suite_id: int, req: RunSuiteRequest = RunSuiteRequest(), db: Session = Depends(get_db)):
    suite = db.query(TestSuite).filter(TestSuite.id == suite_id, TestSuite.status != "deleted").first()
    if not suite:
        raise HTTPException(404, f"测试集不存在: {suite_id}")

    # 读取 enabled 用例
    suite_cases = db.query(TestSuiteCase).filter(
        TestSuiteCase.suite_id == suite_id,
        TestSuiteCase.enabled == True,
    ).order_by(TestSuiteCase.sort_order).all()

    if not suite_cases:
        raise HTTPException(400, "测试集中没有可执行的用例")

    # 按 case_type 分组
    cases_by_type = {}
    for sc in suite_cases:
        tc = db.query(TestCase).filter(TestCase.id == sc.case_id).first()
        if not tc:
            continue
        ct = sc.case_type or getattr(tc, "case_type", "api") or "api"
        cases_by_type.setdefault(ct, []).append(tc)

    # 创建 test_run
    run_id = f"RUN_{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.urandom(4).hex()}"
    trace_id = f"SUITE_{suite.id}_{os.urandom(4).hex()}"
    test_run = TestRun(
        id=run_id,
        project_id=suite.project_id,
        environment_id=req.environment_id,
        trigger_type="suite",
        status="running",
        trace_id=trace_id,
        start_time=datetime.now(),
        total_cases=sum(len(v) for v in cases_by_type.values()),
    )
    db.add(test_run)
    db.commit()

    # P3-2: 变量替换准备
    all_missing_vars = []
    all_binding_errors = []
    datasets_used_set = set()
    try:
        from services.test_data_service import resolve_variables, substitute
        _has_data_service = True
    except Exception:
        _has_data_service = False

    # 执行用例
    passed = 0
    failed = 0
    skipped = 0
    case_results = []
    start_ts = time.time()

    # ── real 模式安全检查 ──
    app_mode = os.getenv("APP_MODE", "mock")

    for case_type, cases in cases_by_type.items():
        for tc in cases:
            rc = RunCase(
                run_id=run_id,
                test_case_id=tc.id,
                status="running",
                start_time=datetime.now(),
            )
            db.add(rc)
            db.commit()
            db.refresh(rc)

            # P3-2: 变量替换
            if _has_data_service:
                try:
                    _vars, _warns = resolve_variables(tc.id, db)
                    if _vars:
                        for _b in db.query(TestDataBinding).filter(TestDataBinding.case_id == tc.id).all():
                            datasets_used_set.add(_b.dataset_id)
                        if tc.execution_config:
                            tc.execution_config, _, _miss = substitute(tc.execution_config, _vars)
                            all_missing_vars.extend(_miss)
                        if tc.steps:
                            tc.steps, _, _miss = substitute(tc.steps, _vars)
                            all_missing_vars.extend(_miss)
                    all_binding_errors.extend(_warns)
                except Exception as _de:
                    all_binding_errors.append(f"data resolve error for {tc.id}: {str(_de)[:100]}")

            try:
                if case_type == "functional":
                    # functional 用例不自动执行
                    rc.status = "skipped"
                    rc.error_message = "functional 用例需手动执行"
                    rc.end_time = datetime.now()
                    rc.duration = 0
                    skipped += 1
                    case_results.append({"case_id": tc.id, "case_type": case_type, "status": "skipped", "reason": "manual"})

                elif case_type == "api":
                    result = _execute_api_case(tc, req, db, app_mode)
                    rc.status = result["status"]
                    rc.error_message = result.get("error", "")
                    rc.response_snapshot = result.get("snapshot")
                    rc.end_time = datetime.now()
                    rc.duration = result.get("duration", 0)
                    if result["status"] == "passed":
                        passed += 1
                    else:
                        failed += 1
                    case_results.append({"case_id": tc.id, "case_type": case_type, "status": result["status"]})

                elif case_type in ("web_ui", "visual"):
                    result = _execute_webui_case(tc, req, db, app_mode)
                    rc.status = result["status"]
                    rc.error_message = result.get("error", "")
                    rc.response_snapshot = result.get("snapshot")
                    rc.end_time = datetime.now()
                    rc.duration = result.get("duration", 0)
                    if result["status"] == "passed":
                        passed += 1
                    else:
                        failed += 1
                    case_results.append({"case_id": tc.id, "case_type": case_type, "status": result["status"]})

                elif case_type == "performance":
                    # performance 用例通过 API 执行引擎
                    result = _execute_api_case(tc, req, db, app_mode)
                    rc.status = result["status"]
                    rc.error_message = result.get("error", "")
                    rc.end_time = datetime.now()
                    rc.duration = result.get("duration", 0)
                    if result["status"] == "passed":
                        passed += 1
                    else:
                        failed += 1
                    case_results.append({"case_id": tc.id, "case_type": case_type, "status": result["status"]})

                else:
                    # unsupported case_type → skip, not 500
                    rc.status = "skipped"
                    rc.error_message = f"Unsupported case_type: {case_type}"
                    rc.end_time = datetime.now()
                    skipped += 1
                    case_results.append({"case_id": tc.id, "case_type": case_type, "status": "skipped", "reason": f"unsupported: {case_type}"})

            except HTTPException as he:
                rc.status = "failed"
                rc.error_message = str(he.detail)
                rc.end_time = datetime.now()
                failed += 1
                case_results.append({"case_id": tc.id, "case_type": case_type, "status": "failed", "error": str(he.detail)})
            except Exception as e:
                rc.status = "failed"
                rc.error_message = str(e)[:500]
                rc.end_time = datetime.now()
                failed += 1
                case_results.append({"case_id": tc.id, "case_type": case_type, "status": "failed", "error": str(e)[:200]})

            db.commit()

    duration_ms = round((time.time() - start_ts) * 1000)

    # 构建 suite_summary
    type_counts = {}
    for ct, cl in cases_by_type.items():
        type_counts[f"{ct}_cases"] = len(cl)

    # P3-2: data_summary
    data_summary = {
        "datasets_used": len(datasets_used_set),
        "missing_variables": len(set(all_missing_vars)),
        "missing_variable_names": list(set(all_missing_vars))[:10],
        "data_binding_errors": len(all_binding_errors),
    }

    suite_summary = {
        "suite_id": suite.id,
        "suite_name": suite.name,
        "suite_type": suite.suite_type,
        "total_cases": passed + failed + skipped,
        **type_counts,
        "passed_cases": passed,
        "failed_cases": failed,
        "skipped_cases": skipped,
        "duration_ms": duration_ms,
        "data_summary": data_summary,
    }

    # 更新 test_run
    test_run.status = "passed" if failed == 0 else "failed"
    test_run.end_time = datetime.now()
    test_run.duration = round(duration_ms / 1000, 2)
    test_run.passed_cases = passed
    test_run.failed_cases = failed
    test_run.skipped_cases = skipped
    test_run.summary = json.dumps({"suite_summary": suite_summary}, ensure_ascii=False)
    db.commit()

    return {
        "success": True,
        "run_id": run_id,
        "suite_summary": suite_summary,
        "case_results": case_results,
    }


# ── Execution helpers ──

def _execute_api_case(tc: TestCase, req: RunSuiteRequest, db: Session, app_mode: str) -> dict:
    """Execute an API case via the existing execution route."""
    exec_config = tc.execution_config or {}
    method = (exec_config.get("method", "GET")).upper()
    url = exec_config.get("url", "")

    if not method or not url:
        return {"status": "failed", "error": "缺少 method/url 配置", "duration": 0}

    # real-mode safety
    UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
    if app_mode == "real" and method in UNSAFE_METHODS and not req.allow_unsafe_methods:
        return {"status": "failed", "error": "REAL_MODE_UNSAFE_METHOD_BLOCKED", "duration": 0}

    base_url = req.base_url or ""
    if not base_url and req.environment_id:
        from database.models import Environment
        env = db.query(Environment).filter(Environment.id == req.environment_id).first()
        if env:
            base_url = env.base_url

    full_url = base_url.rstrip("/") + "/" + url.lstrip("/") if base_url else url

    import requests as http_requests
    start = time.time()
    try:
        resp = http_requests.request(
            method=method,
            url=full_url,
            headers=exec_config.get("headers", {}),
            json=exec_config.get("body"),
            timeout=exec_config.get("timeout", 30),
        )
        dur = round(time.time() - start, 3)

        # Check assertions
        assertions = tc.assertions or []
        all_pass = True
        for a in assertions:
            at = a.get("type", "")
            if at == "status_code":
                if resp.status_code != a.get("expected"):
                    all_pass = False
            elif at == "contains":
                if a.get("expected", "") not in resp.text:
                    all_pass = False
            elif at == "json_path":
                pass  # MVP: skip complex json_path assertions

        status = "passed" if all_pass else "failed"
        return {
            "status": status,
            "duration": dur,
            "snapshot": {"status_code": resp.status_code, "body_preview": resp.text[:500]},
        }
    except Exception as e:
        return {"status": "failed", "error": str(e)[:300], "duration": round(time.time() - start, 3)}


def _execute_webui_case(tc: TestCase, req: RunSuiteRequest, db: Session, app_mode: str) -> dict:
    """Execute a web_ui case via PlaywrightEngine."""
    exec_config = tc.execution_config or {}
    steps = tc.steps or []
    assertions = tc.assertions or []

    if not steps:
        return {"status": "failed", "error": "Web UI 用例无步骤", "duration": 0}

    # eval_js high-risk check
    if app_mode == "real":
        for step in steps:
            action = step.get("action", "")
            if action == "eval_js" and not req.allow_unsafe_methods:
                return {"status": "failed", "error": "real 模式禁止 eval_js", "duration": 0}

    start = time.time()
    try:
        from services.playwright_engine import execute_web_ui
        result = execute_web_ui(steps, assertions, exec_config)
        dur = round(time.time() - start, 3)

        status = "passed" if result.get("success") else "failed"
        return {
            "status": status,
            "duration": dur,
            "error": result.get("error", ""),
            "snapshot": {
                "screenshots": result.get("screenshots", []),
                "console_error_count": len(result.get("console_logs", [])),
            },
        }
    except Exception as e:
        return {"status": "failed", "error": str(e)[:300], "duration": round(time.time() - start, 3)}
