"""
测试用例一键执行路由 (Phase 11 + 12 + 13)

POST /api/v2/test-cases/{case_id}/execute

从数据库读取TestCase → 变量替换 → 真实HTTP请求 → 断言校验 → 写入RunCase
"""

import uuid
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.session import get_db
from database.models import TestCase, TestRun, RunCase, Environment
from services.variable_resolver import (
    resolve_variables, extract_variables, has_unresolved_variables,
    sanitize_sensitive_data,
)
from app.executor_v2.execution_engine import ExecutionEngineV2
from app.executor_v2.models import (
    AssertionDef, AssertionType, TestCaseV2, ExecutionResult, ExecutionStatus,
)

router = APIRouter(prefix="/api/v2/test-cases", tags=["TestCase-Execute"])


# ---------- Request / Response Models ----------

class ExecuteRequest(BaseModel):
    environment_id: Optional[int] = Field(None, description="环境ID，提供base_url")
    base_url: Optional[str] = Field(None, description="直接指定base_url，优先于environment_id")
    dataset_id: Optional[str] = Field(None, description="数据集ID，用于变量替换")
    variables: Optional[Dict[str, Any]] = Field(None, description="直接传入变量，优先于dataset_id")


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


# ---------- 路由 ----------

@router.post("/{case_id}/execute", response_model=ExecuteResponse)
async def execute_test_case(
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

    exec_config = tc.execution_config or {}
    if not exec_config.get('method') or not exec_config.get('url'):
        raise HTTPException(
            status_code=400,
            detail=f"用例 {case_id} 缺少执行配置(method/url)，无法执行接口测试"
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

    # 3. 准备请求数据
    method = exec_config.get('method', 'GET').upper()
    url_path = exec_config.get('url', '/')
    headers = exec_config.get('headers', {})
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
        engine = ExecutionEngineV2(base_url=base_url)
        run_id = f"RUN_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
        result = engine.execute_case(case_v2, run_id=run_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行引擎异常: {str(e)}")

    # 7. 判定最终状态 (Phase 13: 无断言 → no_assertion)
    final_status = result.status
    if not has_assertions and result.status == ExecutionStatus.PASSED.value:
        final_status = "no_assertion"

    # 8. 写入数据库
    try:
        # 创建 TestRun
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
        )
        db.add(test_run)

        # 构建快照（脱敏）
        req_snapshot = {
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
