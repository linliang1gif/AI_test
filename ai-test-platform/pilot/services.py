from __future__ import annotations

import json
import tempfile
import traceback
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import requests
from fastapi import HTTPException
from sqlalchemy import delete, desc, select
from sqlalchemy.orm import Session, selectinload

from modules.executor.real_execution_engine import get_execution_engine
from modules.swagger.api_spec_loader import ApiSpecLoader

from .models import (
    ApiSpecModel,
    EnvironmentModel,
    HealingRecordModel,
    ProjectModel,
    ReportModel,
    RunStepModel,
    SystemSettingModel,
    TestCaseModel,
    TestRunModel,
)
from .security import is_write_method, mask_sensitive_map


RUN_STATUSES = {"created", "queued", "preparing", "running", "healing", "passed", "failed", "aborted"}


def _normalize_env_type(value: str) -> str:
    mapping = {"development": "dev", "production": "prod"}
    return mapping.get(value, value)


def _safe_json(data: Any) -> Any:
    try:
        json.dumps(data, ensure_ascii=False)
        return data
    except TypeError:
        return str(data)


def _truncate_text(value: Any, limit: int = 4000) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False)
    else:
        text = str(value)
    if len(text) <= limit:
        return _safe_json(value)
    return text[:limit] + "...<truncated>"


def _format_dt(value: Optional[datetime]) -> Optional[str]:
    return value.isoformat() if value else None


def _project_stats(db: Session, project_id: int) -> Dict[str, Any]:
    cases = db.execute(select(TestCaseModel).where(TestCaseModel.project_id == project_id)).scalars().all()
    runs = db.execute(
        select(TestRunModel).where(TestRunModel.project_id == project_id).order_by(desc(TestRunModel.id)).limit(5)
    ).scalars().all()
    apis = db.execute(select(ApiSpecModel.id).where(ApiSpecModel.project_id == project_id)).scalars().all()
    total_cases = len(cases)
    passed_cases = len([case for case in cases if case.status == "passed"])
    coverage = round((passed_cases / total_cases) * 100, 1) if total_cases else 0.0
    recent_runs = ["success" if run.status == "passed" else "failed" for run in runs]
    return {
        "testsCount": total_cases,
        "coverage": coverage,
        "failedCount": len([run for run in runs if run.status == "failed"]),
        "recentRuns": recent_runs,
        "lastRun": _format_dt(runs[0].ended_at or runs[0].started_at) if runs else "从未运行",
        "totalApis": len(apis),
        "totalRuns": db.execute(select(TestRunModel.id).where(TestRunModel.project_id == project_id)).scalars().all().__len__(),
    }


def _serialize_environment(environment: EnvironmentModel, include_secret: bool = False) -> Dict[str, Any]:
    auth_config = environment.auth_config or {}
    display_auth = auth_config if include_secret else mask_sensitive_map(auth_config)
    return {
        "id": environment.id,
        "project_id": environment.project_id,
        "name": environment.name,
        "environment_type": _normalize_env_type(environment.environment_type),
        "base_url": environment.base_url,
        "auth_type": environment.auth_type,
        "auth_config": display_auth,
        "has_secret": any(bool(value) for value in auth_config.values()),
        "openapi_source": environment.openapi_source or {},
        "default_headers": mask_sensitive_map(environment.default_headers or {}),
        "timeout_seconds": environment.timeout_seconds,
        "retry_policy": environment.retry_policy or {},
        "env_var_mapping": environment.env_var_mapping or {},
        "data_isolation_key": environment.data_isolation_key,
        "allow_write_operations": environment.allow_write_operations,
        "allow_self_healing": environment.allow_self_healing,
        "allow_auto_test_data": environment.allow_auto_test_data,
        "is_default": environment.is_default,
        "created_at": _format_dt(environment.created_at),
        "updated_at": _format_dt(environment.updated_at),
    }


def _serialize_project(project: ProjectModel, db: Session, include_environments: bool = False) -> Dict[str, Any]:
    payload = {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "status": project.status,
        "owner": project.owner,
        "team": project.team,
        "default_role": project.default_role,
        "createdAt": _format_dt(project.created_at),
        "updatedAt": _format_dt(project.updated_at),
    }
    payload.update(_project_stats(db, project.id))
    default_environment = next((env for env in project.environments if env.is_default), None)
    if default_environment:
        payload["environment"] = _normalize_env_type(default_environment.environment_type)
        payload["baseUrl"] = default_environment.base_url
        payload["default_environment_id"] = default_environment.id
        payload["default_environment_name"] = default_environment.name
    if include_environments:
        payload["environments"] = [_serialize_environment(env) for env in project.environments]
    return payload


def _serialize_api(api: ApiSpecModel) -> Dict[str, Any]:
    return {
        "id": api.id,
        "project_id": api.project_id,
        "name": api.name,
        "summary": api.summary,
        "description": api.description,
        "method": api.method,
        "path": api.path,
        "tags": api.tags or [],
        "parameters": api.parameters or [],
        "requestBody": api.request_body or {},
        "responses": api.responses or {},
        "source_type": api.source_type,
        "source_location": api.source_location,
        "spec_version": api.spec_version,
        "imported_at": _format_dt(api.imported_at),
    }


def _serialize_case(case: TestCaseModel) -> Dict[str, Any]:
    return {
        "id": case.id,
        "project_id": case.project_id,
        "api_spec_id": case.api_spec_id,
        "title": case.title,
        "module": case.module,
        "priority": case.priority,
        "status": case.status,
        "type": case.case_type,
        "data_type": case.scenario_type,
        "expected_behavior": case.expected_behavior,
        "source": case.source,
        "description": case.description,
        "steps": case.steps or [],
        "expected": case.expected,
        "tags": case.tags or [],
        "execution_config": case.execution_config or {},
        "created_at": _format_dt(case.created_at),
        "updated_at": _format_dt(case.updated_at),
    }


def _serialize_run(run: TestRunModel) -> Dict[str, Any]:
    summary = run.summary or {}
    return {
        "id": run.id,
        "project_id": run.project_id,
        "environment_id": run.environment_id,
        "report_id": run.report_id,
        "name": run.name,
        "status": run.status,
        "created_at": _format_dt(run.created_at),
        "startTime": _format_dt(run.started_at),
        "endTime": _format_dt(run.ended_at),
        "trace_id": run.trace_id,
        "request_id": run.request_id,
        "totalTests": summary.get("total", 0),
        "passed": summary.get("passed", 0),
        "failed": summary.get("failed", 0),
        "pending": summary.get("pending", 0),
        "progress": summary.get("progress", 0),
        "last_error": run.last_error,
        "status_history": run.status_history or [],
    }


def _serialize_report(report: ReportModel) -> Dict[str, Any]:
    summary = report.summary or {}
    return {
        "id": report.id,
        "project_id": report.project_id,
        "run_id": report.run_id,
        "name": report.name,
        "type": report.report_type,
        "summary": summary,
        "content": report.content or {},
        "failure_overview": report.failure_overview or {},
        "created_at": _format_dt(report.created_at),
        "trace_id": report.trace_id,
        "passRate": summary.get("pass_rate", 0),
        "testRuns": 1 if report.run_id else 0,
    }


def list_projects(db: Session) -> List[Dict[str, Any]]:
    projects = db.execute(
        select(ProjectModel).options(selectinload(ProjectModel.environments)).order_by(ProjectModel.id.desc())
    ).scalars().all()
    return [_serialize_project(project, db, include_environments=True) for project in projects]


def create_project(db: Session, payload: Dict[str, Any]) -> Dict[str, Any]:
    project = ProjectModel(
        name=payload["name"],
        description=payload.get("description", ""),
        owner=payload.get("owner", "unknown"),
        team=payload.get("team", ""),
        status=payload.get("status", "active"),
        default_role="admin",
        tags=[],
    )
    db.add(project)
    db.flush()
    environment = EnvironmentModel(
        project_id=project.id,
        name="默认测试环境",
        environment_type=_normalize_env_type(payload.get("environment", "test")),
        base_url=payload.get("baseUrl", ""),
        auth_type="none",
        auth_config={},
        openapi_source={},
        default_headers={},
        timeout_seconds=30,
        retry_policy={"max_retries": 1, "retry_backoff_seconds": 1},
        env_var_mapping={},
        data_isolation_key=project.name,
        allow_write_operations=False,
        allow_self_healing=True,
        allow_auto_test_data=True,
        is_default=True,
    )
    db.add(environment)
    db.commit()
    db.refresh(project)
    return _serialize_project(project, db, include_environments=True)


def get_project_detail(db: Session, project_id: int) -> Dict[str, Any]:
    project = db.execute(
        select(ProjectModel).options(selectinload(ProjectModel.environments)).where(ProjectModel.id == project_id)
    ).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return _serialize_project(project, db, include_environments=True)


def update_project(db: Session, project_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    project = db.get(ProjectModel, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    for key in ["name", "description", "owner", "team", "status"]:
        if payload.get(key) is not None:
            setattr(project, key, payload[key])
    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)
    return _serialize_project(project, db, include_environments=True)


def delete_project(db: Session, project_id: int) -> None:
    project = db.get(ProjectModel, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    db.delete(project)
    db.commit()


def _apply_environment_update(environment: EnvironmentModel, payload: Dict[str, Any]) -> None:
    for key in [
        "name",
        "base_url",
        "auth_type",
        "openapi_source",
        "default_headers",
        "timeout_seconds",
        "retry_policy",
        "env_var_mapping",
        "data_isolation_key",
        "allow_write_operations",
        "allow_self_healing",
        "allow_auto_test_data",
        "is_default",
    ]:
        if key in payload and payload[key] is not None:
            setattr(environment, key, payload[key])
    if payload.get("environment_type") is not None:
        environment.environment_type = _normalize_env_type(payload["environment_type"])
    if payload.get("auth_config") is not None:
        updated = environment.auth_config or {}
        for key, value in payload["auth_config"].items():
            if value not in (None, ""):
                updated[key] = value
        environment.auth_config = updated
    environment.updated_at = datetime.utcnow()


def create_environment(db: Session, payload: Dict[str, Any]) -> Dict[str, Any]:
    project = db.get(ProjectModel, payload["project_id"])
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    environment = EnvironmentModel(
        project_id=payload["project_id"],
        name=payload["name"],
        environment_type=_normalize_env_type(payload["environment_type"]),
        base_url=payload["base_url"],
        auth_type=payload.get("auth_type", "none"),
        auth_config=payload.get("auth_config", {}),
        openapi_source=payload.get("openapi_source", {}),
        default_headers=payload.get("default_headers", {}),
        timeout_seconds=payload.get("timeout_seconds", 30),
        retry_policy=payload.get("retry_policy", {"max_retries": 1, "retry_backoff_seconds": 1}),
        env_var_mapping=payload.get("env_var_mapping", {}),
        data_isolation_key=payload.get("data_isolation_key", project.name),
        allow_write_operations=payload.get("allow_write_operations", False),
        allow_self_healing=payload.get("allow_self_healing", True),
        allow_auto_test_data=payload.get("allow_auto_test_data", True),
        is_default=payload.get("is_default", False),
    )
    if environment.is_default:
        db.execute(
            select(EnvironmentModel).where(EnvironmentModel.project_id == environment.project_id)
        ).scalars().all()
        for item in db.execute(select(EnvironmentModel).where(EnvironmentModel.project_id == environment.project_id)).scalars():
            item.is_default = False
    db.add(environment)
    db.commit()
    db.refresh(environment)
    return _serialize_environment(environment)


def update_environment(db: Session, environment_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    environment = db.get(EnvironmentModel, environment_id)
    if not environment:
        raise HTTPException(status_code=404, detail="环境不存在")
    _apply_environment_update(environment, payload)
    if environment.is_default:
        for item in db.execute(
            select(EnvironmentModel).where(
                EnvironmentModel.project_id == environment.project_id, EnvironmentModel.id != environment.id
            )
        ).scalars():
            item.is_default = False
    db.commit()
    db.refresh(environment)
    return _serialize_environment(environment)


def list_apis(db: Session, project_id: Optional[int] = None) -> List[Dict[str, Any]]:
    stmt = select(ApiSpecModel).order_by(ApiSpecModel.id.desc())
    if project_id:
        stmt = stmt.where(ApiSpecModel.project_id == project_id)
    return [_serialize_api(api) for api in db.execute(stmt).scalars().all()]


def _save_uploaded_bytes(content: bytes, suffix: str) -> Path:
    handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    with open(handle.name, "wb") as file_handle:
        file_handle.write(content)
    return Path(handle.name)


def _import_openapi_document(db: Session, project_id: int, environment_id: int, source_type: str, source_location: str, file_path: Path) -> Dict[str, Any]:
    environment = db.get(EnvironmentModel, environment_id)
    if not environment or environment.project_id != project_id:
        raise HTTPException(status_code=404, detail="环境不存在")

    loader = ApiSpecLoader(str(file_path))
    info = loader.get_spec_info()
    apis = loader.get_all_apis()

    db.execute(delete(ApiSpecModel).where(ApiSpecModel.project_id == project_id))
    for api in apis:
        db.add(
            ApiSpecModel(
                project_id=project_id,
                source_type=source_type,
                source_location=source_location,
                spec_version=info.get("version", ""),
                method=api.get("method", "GET"),
                path=api.get("path", "/"),
                name=api.get("summary") or api.get("operation_id") or f"{api.get('method', 'GET')} {api.get('path', '/')}",
                summary=api.get("summary", ""),
                description=api.get("description", ""),
                tags=api.get("tags", []),
                parameters=api.get("parameters", []),
                request_body=api.get("request_body", {}),
                responses=api.get("responses", {}),
                raw_definition=api,
                imported_at=datetime.utcnow(),
            )
        )
    environment.openapi_source = {
        "source_type": source_type,
        "location": source_location,
        "imported_at": datetime.utcnow().isoformat(),
        "spec_version": info.get("version", ""),
    }
    environment.updated_at = datetime.utcnow()
    db.commit()
    imported = list_apis(db, project_id=project_id)
    return {
        "spec_info": info,
        "apis": imported,
        "count": len(imported),
    }


def import_openapi_from_url(db: Session, project_id: int, environment_id: int, url: str) -> Dict[str, Any]:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    suffix = ".json" if "json" in response.headers.get("content-type", "").lower() else ".yaml"
    file_path = _save_uploaded_bytes(response.content, suffix)
    try:
        return _import_openapi_document(db, project_id, environment_id, "url", url, file_path)
    finally:
        file_path.unlink(missing_ok=True)


def import_openapi_from_file(db: Session, project_id: int, environment_id: int, filename: str, content: bytes) -> Dict[str, Any]:
    suffix = Path(filename).suffix or ".json"
    file_path = _save_uploaded_bytes(content, suffix)
    try:
        return _import_openapi_document(db, project_id, environment_id, "file", filename, file_path)
    finally:
        file_path.unlink(missing_ok=True)


def _default_value_from_schema(schema: Dict[str, Any]) -> Any:
    schema_type = schema.get("type")
    if "example" in schema:
        return schema["example"]
    if schema_type == "integer":
        return schema.get("minimum", 1)
    if schema_type == "number":
        return schema.get("minimum", 1)
    if schema_type == "boolean":
        return True
    if schema_type == "array":
        return []
    if schema_type == "object":
        return {
            key: _default_value_from_schema(value)
            for key, value in (schema.get("properties") or {}).items()
        }
    if schema.get("enum"):
        return schema["enum"][0]
    if schema.get("minLength", 0) > 0:
        return "x" * schema["minLength"]
    return "sample"


def _build_request_template(api: ApiSpecModel) -> Dict[str, Any]:
    params = {}
    body = {}
    for param in api.parameters or []:
        params[param.get("name")] = _default_value_from_schema(param.get("schema") or param)
    request_body = api.request_body or {}
    schema = request_body.get("schema") or {}
    for key, value in (schema.get("properties") or {}).items():
        body[key] = _default_value_from_schema(value)
    return {"params": params, "body": body}


def _build_generated_cases(api: ApiSpecModel, include_auth_failure: bool) -> List[Dict[str, Any]]:
    template = _build_request_template(api)
    required = [param for param in (api.parameters or []) if param.get("required")]
    cases = [
        {
            "title": f"{api.method} {api.path} - 基础成功路径",
            "case_type": "功能测试",
            "scenario_type": "valid",
            "expected_behavior": "success",
            "steps": ["使用默认请求头和合法参数发起请求", "校验返回状态与结构"],
            "expected": "接口返回成功状态，响应结构符合定义",
            "execution_config": {
                "method": api.method,
                "path": api.path,
                "params": template["params"],
                "body": template["body"],
                "expected_status": 200,
            },
        },
        {
            "title": f"{api.method} {api.path} - 参数类型错误",
            "case_type": "异常测试",
            "scenario_type": "invalid",
            "expected_behavior": "client_error",
            "steps": ["构造错误类型参数后发起请求", "校验接口返回校验错误"],
            "expected": "接口拒绝非法参数，返回4xx错误",
            "execution_config": {
                "method": api.method,
                "path": api.path,
                "params": {key: "invalid_type" for key in template["params"].keys()},
                "body": {key: "invalid_type" for key in template["body"].keys()},
                "expected_status": 400,
            },
        },
        {
            "title": f"{api.method} {api.path} - 边界值",
            "case_type": "边界测试",
            "scenario_type": "boundary",
            "expected_behavior": "success",
            "steps": ["构造最小边界参数", "执行请求并核对接口行为"],
            "expected": "接口在边界输入下行为可预测，不出现5xx",
            "execution_config": {
                "method": api.method,
                "path": api.path,
                "params": template["params"],
                "body": template["body"],
                "expected_status": 200,
            },
        },
    ]
    if required:
        cases.append(
            {
                "title": f"{api.method} {api.path} - 必填参数缺失",
                "case_type": "异常测试",
                "scenario_type": "invalid",
                "expected_behavior": "client_error",
                "steps": ["移除必填参数", "校验接口返回缺参提示"],
                "expected": "接口返回明确的缺少参数错误",
                "execution_config": {
                    "method": api.method,
                    "path": api.path,
                    "params": {key: value for key, value in template["params"].items() if key not in {item['name'] for item in required}},
                    "body": template["body"],
                    "expected_status": 400,
                },
            }
        )
    if include_auth_failure:
        cases.append(
            {
                "title": f"{api.method} {api.path} - 鉴权失败",
                "case_type": "安全测试",
                "scenario_type": "invalid",
                "expected_behavior": "auth_error",
                "steps": ["移除或伪造认证信息后发起请求", "校验接口拒绝访问"],
                "expected": "接口返回401/403，且无敏感数据泄露",
                "execution_config": {
                    "method": api.method,
                    "path": api.path,
                    "params": template["params"],
                    "body": template["body"],
                    "auth_override": "invalid",
                    "expected_status": 401,
                },
            }
        )
    return cases


def generate_openapi_cases(db: Session, project_id: int, api_ids: Optional[List[int]]) -> Dict[str, Any]:
    apis_stmt = select(ApiSpecModel).where(ApiSpecModel.project_id == project_id).order_by(ApiSpecModel.id.asc())
    if api_ids:
        apis_stmt = apis_stmt.where(ApiSpecModel.id.in_(api_ids))
    apis = db.execute(apis_stmt).scalars().all()
    if not apis:
        raise HTTPException(status_code=404, detail="未找到可生成用例的 API")
    environment = db.execute(
        select(EnvironmentModel).where(EnvironmentModel.project_id == project_id, EnvironmentModel.is_default == True)
    ).scalar_one_or_none()
    include_auth_failure = bool(environment and environment.auth_type != "none")
    target_api_ids = [api.id for api in apis]
    db.execute(
        delete(TestCaseModel).where(
            TestCaseModel.project_id == project_id,
            TestCaseModel.api_spec_id.in_(target_api_ids),
            TestCaseModel.source == "openapi_generated",
        )
    )
    created = []
    for api in apis:
        for item in _build_generated_cases(api, include_auth_failure):
            model = TestCaseModel(
                project_id=project_id,
                api_spec_id=api.id,
                title=item["title"],
                module=(api.tags or ["default"])[0],
                priority="high" if item["scenario_type"] == "valid" else "medium",
                status="pending",
                case_type=item["case_type"],
                scenario_type=item["scenario_type"],
                expected_behavior=item["expected_behavior"],
                source="openapi_generated",
                description=f"由 OpenAPI 接口 {api.method} {api.path} 自动生成",
                steps=item["steps"],
                expected=item["expected"],
                tags=api.tags or [],
                execution_config=item["execution_config"],
            )
            db.add(model)
            created.append(model)
    db.commit()
    for item in created:
        db.refresh(item)
    return {
        "count": len(created),
        "test_cases": [_serialize_case(item) for item in created],
    }


def list_test_cases(db: Session, project_id: Optional[int] = None) -> List[Dict[str, Any]]:
    stmt = select(TestCaseModel).order_by(TestCaseModel.id.desc())
    if project_id:
        stmt = stmt.where(TestCaseModel.project_id == project_id)
    return [_serialize_case(item) for item in db.execute(stmt).scalars().all()]


def _append_status(run: TestRunModel, status: str, message: str) -> None:
    if status not in RUN_STATUSES:
        raise ValueError(f"Unsupported status: {status}")
    history = list(run.status_history or [])
    history.append({"status": status, "message": message, "time": datetime.utcnow().isoformat()})
    run.status_history = history
    run.status = status


def _create_step(
    db: Session,
    run: TestRunModel,
    test_case_id: Optional[int],
    step_name: str,
    step_index: int,
    status: str,
    input_snapshot: Dict[str, Any],
    trace_id: str,
    request_id: str,
) -> RunStepModel:
    step = RunStepModel(
        run_id=run.id,
        test_case_id=test_case_id,
        step_name=step_name,
        step_index=step_index,
        status=status,
        start_time=datetime.utcnow(),
        trace_id=trace_id,
        request_id=request_id,
        input_snapshot=_safe_json(input_snapshot),
        output_snapshot={},
        retry_count=0,
    )
    db.add(step)
    db.flush()
    return step


def _finalize_step(
    step: RunStepModel,
    status: str,
    output_snapshot: Dict[str, Any],
    error_message: Optional[str] = None,
    stack_trace: Optional[str] = None,
    retry_count: Optional[int] = None,
) -> None:
    step.status = status
    step.end_time = datetime.utcnow()
    step.output_snapshot = _safe_json(output_snapshot)
    step.error_message = error_message
    step.stack_trace = stack_trace
    if retry_count is not None:
        step.retry_count = retry_count


def _resolve_environment_headers(environment: EnvironmentModel, auth_override: Optional[str] = None) -> Dict[str, str]:
    headers = dict(environment.default_headers or {})
    auth_type = environment.auth_type
    auth = environment.auth_config or {}
    if auth_override == "invalid":
        if auth_type == "bearer_token":
            headers["Authorization"] = "Bearer invalid-token"
        elif auth_type == "api_key":
            key_name = auth.get("header_name") or auth.get("query_name") or "X-API-Key"
            headers[key_name] = "invalid-key"
        elif auth_type == "cookie":
            headers["Cookie"] = "invalid_cookie=true"
        elif auth_type == "custom_header":
            key_name = auth.get("header_name") or "X-Custom-Auth"
            headers[key_name] = "invalid"
        return headers
    if auth_type == "bearer_token" and auth.get("token"):
        headers["Authorization"] = f"Bearer {auth['token']}"
    elif auth_type == "api_key" and auth.get("api_key"):
        key_name = auth.get("header_name") or "X-API-Key"
        headers[key_name] = auth["api_key"]
    elif auth_type == "cookie" and auth.get("cookie"):
        headers["Cookie"] = auth["cookie"]
    elif auth_type == "custom_header" and auth.get("header_name") and auth.get("header_value"):
        headers[auth["header_name"]] = auth["header_value"]
    return headers


def _execute_case_with_healing(
    db: Session,
    run: TestRunModel,
    environment: EnvironmentModel,
    test_case: TestCaseModel,
    step_index: int,
) -> Dict[str, Any]:
    config = test_case.execution_config or {}
    method = config.get("method", "GET").upper()
    if _normalize_env_type(environment.environment_type) == "prod" and is_write_method(method) and not environment.allow_write_operations:
        raise HTTPException(status_code=400, detail="生产环境默认禁止写操作测试，请显式允许后再执行")

    headers = _resolve_environment_headers(environment, config.get("auth_override"))
    request_body = config.get("body") or {}
    params = config.get("params") or {}
    url = environment.base_url.rstrip("/") + "/" + config.get("path", "").lstrip("/")
    timeout = environment.timeout_seconds
    retry_policy = environment.retry_policy or {}
    max_retries = int(retry_policy.get("max_retries", 1))
    trace_id = str(uuid.uuid4())
    request_id = str(uuid.uuid4())
    step = _create_step(
        db,
        run,
        test_case.id,
        test_case.title,
        step_index,
        "running",
        {
            "url": url,
            "method": method,
            "headers": mask_sensitive_map(headers),
            "params": params,
            "body": _truncate_text(request_body),
            "expected_status": config.get("expected_status"),
        },
        trace_id,
        request_id,
    )
    db.commit()

    engine = get_execution_engine()
    retries = 0
    result = None
    healing_applied = False
    while retries <= max_retries:
        result = engine.execute(
            {
                "id": str(test_case.id),
                "name": test_case.title,
                "execution_type": "api",
                "config": {
                    "url": url,
                    "method": method,
                    "headers": headers,
                    "body": request_body if method != "GET" else params,
                },
                "timeout": timeout,
            }
        )
        expected_status = int(config.get("expected_status", 200))
        success = result.success and (result.status_code == expected_status or expected_status >= 400)
        if success:
            break
        retryable = result.error_type in {"timeout", "connection_error"} or (result.status_code or 0) >= 500
        if not environment.allow_self_healing or retries >= max_retries or not retryable:
            break
        healing_applied = True
        healing = HealingRecordModel(
            run_id=run.id,
            run_step_id=step.id,
            test_case_id=test_case.id,
            action_type="retry" if result.error_type != "timeout" else "timeout_retry",
            risk_level="low",
            before_snapshot={"timeout": timeout, "retry_count": retries},
            after_snapshot={"timeout": timeout + 5 if result.error_type == "timeout" else timeout, "retry_count": retries + 1},
            reason=result.error_message or "temporary execution failure",
            success=False,
            created_at=datetime.utcnow(),
            trace_id=trace_id,
        )
        db.add(healing)
        timeout = timeout + 5 if result.error_type == "timeout" else timeout
        retries += 1
        step.retry_count = retries
        db.commit()

    expected_status = int(config.get("expected_status", 200))
    success = bool(result and result.status_code is not None and (result.status_code == expected_status or (expected_status >= 400 and result.status_code >= 400)))
    response_snapshot = {
        "status_code": result.status_code if result else None,
        "elapsed_ms": int((result.duration if result else 0) * 1000),
        "response_headers": mask_sensitive_map(result.response_headers if result else {}),
        "response_body": _truncate_text(result.response if result else None),
        "error_type": result.error_type if result else None,
        "error_message": result.error_message if result else None,
    }
    _finalize_step(
        step,
        "passed" if success else "failed",
        response_snapshot,
        error_message=None if success else (result.error_message if result else "执行失败"),
        stack_trace=result.error_details if result else None,
        retry_count=retries,
    )
    test_case.status = "passed" if success else "failed"
    test_case.updated_at = datetime.utcnow()
    if healing_applied:
        for record in db.execute(
            select(HealingRecordModel).where(HealingRecordModel.run_step_id == step.id)
        ).scalars():
            record.success = success
    db.commit()
    return {
        "success": success,
        "step_id": step.id,
        "trace_id": trace_id,
        "request_id": request_id,
        "status_code": result.status_code if result else None,
        "error": None if success else (result.error_message if result else "执行失败"),
    }


def _generate_report_for_run(db: Session, run_id: int) -> ReportModel:
    run = db.execute(
        select(TestRunModel)
        .options(selectinload(TestRunModel.run_steps), selectinload(TestRunModel.healing_records))
        .where(TestRunModel.id == run_id)
    ).scalar_one()
    project = db.get(ProjectModel, run.project_id)
    steps = run.run_steps
    total = len([step for step in steps if step.test_case_id is not None])
    passed = len([step for step in steps if step.test_case_id is not None and step.status == "passed"])
    failed = len([step for step in steps if step.test_case_id is not None and step.status == "failed"])
    summary = {
        "total": total,
        "passed": passed,
        "failed": failed,
        "pending": 0,
        "pass_rate": round((passed / total) * 100, 1) if total else 0,
        "generated_at": datetime.utcnow().isoformat(),
    }
    failures = [
        {
            "step_name": step.step_name,
            "error_message": step.error_message,
            "trace_id": step.trace_id,
            "request_id": step.request_id,
            "output": step.output_snapshot,
        }
        for step in steps
        if step.test_case_id is not None and step.status == "failed"
    ]
    content = {
        "run": _serialize_run(run),
        "steps": [
            {
                "id": step.id,
                "step_name": step.step_name,
                "status": step.status,
                "start_time": _format_dt(step.start_time),
                "end_time": _format_dt(step.end_time),
                "trace_id": step.trace_id,
                "request_id": step.request_id,
                "input_snapshot": step.input_snapshot,
                "output_snapshot": step.output_snapshot,
                "error_message": step.error_message,
                "retry_count": step.retry_count,
            }
            for step in steps
        ],
        "healing_records": [
            {
                "id": record.id,
                "action_type": record.action_type,
                "risk_level": record.risk_level,
                "before_snapshot": record.before_snapshot,
                "after_snapshot": record.after_snapshot,
                "reason": record.reason,
                "success": record.success,
                "trace_id": record.trace_id,
            }
            for record in run.healing_records
        ],
    }
    if run.report_id:
        report = db.get(ReportModel, run.report_id)
        report.summary = summary
        report.content = content
        report.failure_overview = {"failures": failures}
        report.created_at = datetime.utcnow()
        report.trace_id = run.trace_id
    else:
        report = ReportModel(
            project_id=run.project_id,
            run_id=run.id,
            name=f"{project.name} - 执行报告 #{run.id}",
            report_type="execution",
            summary=summary,
            content=content,
            failure_overview={"failures": failures},
            created_at=datetime.utcnow(),
            trace_id=run.trace_id,
        )
        db.add(report)
        db.flush()
        run.report_id = report.id
    db.commit()
    db.refresh(report)
    return report


def execute_run(db: Session, run_id: int) -> None:
    run = db.execute(
        select(TestRunModel).where(TestRunModel.id == run_id)
    ).scalar_one_or_none()
    if not run:
        return
    environment = db.get(EnvironmentModel, run.environment_id)
    project = db.get(ProjectModel, run.project_id)
    if not project or not environment:
        run.status = "aborted"
        run.last_error = "项目或环境不存在"
        run.ended_at = datetime.utcnow()
        db.commit()
        return

    _append_status(run, "queued", "任务已进入队列")
    run.trace_id = run.trace_id or str(uuid.uuid4())
    run.request_id = run.request_id or str(uuid.uuid4())
    db.commit()

    _append_status(run, "preparing", "正在准备环境与用例")
    run.started_at = datetime.utcnow()
    db.commit()

    selected_ids = run.selected_case_ids or []
    stmt = select(TestCaseModel).where(TestCaseModel.project_id == run.project_id).order_by(TestCaseModel.id.asc())
    if selected_ids:
        stmt = stmt.where(TestCaseModel.id.in_(selected_ids))
    test_cases = db.execute(stmt).scalars().all()
    if not test_cases:
        run.last_error = "没有可执行的测试用例"
        _append_status(run, "aborted", "未找到可执行用例")
        run.ended_at = datetime.utcnow()
        db.commit()
        return

    run.summary = {"total": len(test_cases), "passed": 0, "failed": 0, "pending": len(test_cases), "progress": 0}
    _append_status(run, "running", "开始逐条执行测试用例")
    db.commit()

    passed = 0
    failed = 0
    for index, test_case in enumerate(test_cases, start=1):
        try:
            result = _execute_case_with_healing(db, run, environment, test_case, index)
            if result["success"]:
                passed += 1
            else:
                failed += 1
                run.last_error = result["error"]
        except HTTPException as exc:
            failed += 1
            run.last_error = str(exc.detail)
            step = _create_step(
                db,
                run,
                test_case.id,
                test_case.title,
                index,
                "failed",
                {"reason": "validation"},
                str(uuid.uuid4()),
                str(uuid.uuid4()),
            )
            _finalize_step(step, "failed", {}, error_message=str(exc.detail), stack_trace=None, retry_count=0)
            db.commit()
        except Exception as exc:
            failed += 1
            run.last_error = str(exc)
            stack = traceback.format_exc()
            step = _create_step(
                db,
                run,
                test_case.id,
                test_case.title,
                index,
                "failed",
                {"reason": "unexpected"},
                str(uuid.uuid4()),
                str(uuid.uuid4()),
            )
            _finalize_step(step, "failed", {}, error_message=str(exc), stack_trace=stack, retry_count=0)
            db.commit()

        pending = len(test_cases) - index
        run.summary = {
            "total": len(test_cases),
            "passed": passed,
            "failed": failed,
            "pending": pending,
            "progress": int((index / len(test_cases)) * 100),
        }
        if any(record.run_id == run.id for record in db.execute(select(HealingRecordModel).where(HealingRecordModel.run_id == run.id)).scalars()):
            _append_status(run, "healing", "本次执行触发了低风险自愈")
        db.commit()

    run.ended_at = datetime.utcnow()
    _append_status(run, "passed" if failed == 0 else "failed", "执行结束")
    db.commit()
    report = _generate_report_for_run(db, run.id)
    run.report_id = report.id
    db.commit()


def create_test_run(db: Session, payload: Dict[str, Any], requested_by_role: str) -> Dict[str, Any]:
    project = db.get(ProjectModel, payload["project_id"])
    environment = db.get(EnvironmentModel, payload["environment_id"])
    if not project or not environment or environment.project_id != project.id:
        raise HTTPException(status_code=404, detail="项目或环境不存在")
    selected_case_ids = payload.get("test_case_ids") or [
        case.id for case in db.execute(select(TestCaseModel.id).where(TestCaseModel.project_id == project.id)).scalars()
    ]
    now = datetime.utcnow()
    run = TestRunModel(
        project_id=project.id,
        environment_id=environment.id,
        name=payload.get("name") or f"{project.name} - {environment.name} - {now.strftime('%Y%m%d%H%M%S')}",
        status="created",
        trigger_source=payload.get("trigger_source", "manual"),
        requested_by_role=requested_by_role,
        created_at=now,
        trace_id=str(uuid.uuid4()),
        request_id=str(uuid.uuid4()),
        selected_case_ids=selected_case_ids,
        summary={"total": len(selected_case_ids), "passed": 0, "failed": 0, "pending": len(selected_case_ids), "progress": 0},
        status_history=[{"status": "created", "message": "任务已创建", "time": now.isoformat()}],
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return _serialize_run(run)


def list_runs(db: Session, project_id: Optional[int] = None) -> List[Dict[str, Any]]:
    stmt = select(TestRunModel).order_by(TestRunModel.id.desc())
    if project_id:
        stmt = stmt.where(TestRunModel.project_id == project_id)
    return [_serialize_run(run) for run in db.execute(stmt).scalars().all()]


def get_run_detail(db: Session, run_id: int) -> Dict[str, Any]:
    run = db.execute(
        select(TestRunModel)
        .options(selectinload(TestRunModel.run_steps), selectinload(TestRunModel.healing_records))
        .where(TestRunModel.id == run_id)
    ).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    environment = db.get(EnvironmentModel, run.environment_id) if run.environment_id else None
    project = db.get(ProjectModel, run.project_id)
    report = db.get(ReportModel, run.report_id) if run.report_id else None
    return {
        **_serialize_run(run),
        "project_name": project.name if project else "",
        "environment": _normalize_env_type(environment.environment_type) if environment else "",
        "environment_name": environment.name if environment else "",
        "steps": [
            {
                "id": step.id,
                "test_case_id": step.test_case_id,
                "step_name": step.step_name,
                "status": step.status,
                "start_time": _format_dt(step.start_time),
                "end_time": _format_dt(step.end_time),
                "trace_id": step.trace_id,
                "request_id": step.request_id,
                "input_snapshot": step.input_snapshot,
                "output_snapshot": step.output_snapshot,
                "error_message": step.error_message,
                "stack_trace": step.stack_trace,
                "retry_count": step.retry_count,
            }
            for step in sorted(run.run_steps, key=lambda item: item.step_index)
        ],
        "healing_records": [
            {
                "id": record.id,
                "action_type": record.action_type,
                "risk_level": record.risk_level,
                "before_snapshot": record.before_snapshot,
                "after_snapshot": record.after_snapshot,
                "reason": record.reason,
                "success": record.success,
            }
            for record in run.healing_records
        ],
        "report": _serialize_report(report) if report else None,
    }


def list_reports(db: Session, project_id: Optional[int] = None) -> List[Dict[str, Any]]:
    stmt = select(ReportModel).order_by(ReportModel.id.desc())
    if project_id:
        stmt = stmt.where(ReportModel.project_id == project_id)
    return [_serialize_report(report) for report in db.execute(stmt).scalars().all()]


def get_report_detail(db: Session, report_id: int) -> Dict[str, Any]:
    report = db.get(ReportModel, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    payload = _serialize_report(report)
    run = db.get(TestRunModel, report.run_id) if report.run_id else None
    if run:
        payload["run"] = get_run_detail(db, run.id)
    return payload


def regenerate_report(db: Session, run_id: int) -> Dict[str, Any]:
    report = _generate_report_for_run(db, run_id)
    return _serialize_report(report)


def get_system_settings(db: Session) -> List[Dict[str, Any]]:
    return [
        {
            "key": item.key,
            "value": item.value,
            "description": item.description,
            "updated_at": _format_dt(item.updated_at),
        }
        for item in db.execute(select(SystemSettingModel).order_by(SystemSettingModel.key.asc())).scalars().all()
    ]


def upsert_system_setting(db: Session, key: str, value: Dict[str, Any], description: str) -> Dict[str, Any]:
    setting = db.execute(select(SystemSettingModel).where(SystemSettingModel.key == key)).scalar_one_or_none()
    if setting is None:
        setting = SystemSettingModel(key=key, value=value, description=description, updated_at=datetime.utcnow())
        db.add(setting)
    else:
        setting.value = value
        setting.description = description
        setting.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(setting)
    return {
        "key": setting.key,
        "value": setting.value,
        "description": setting.description,
        "updated_at": _format_dt(setting.updated_at),
    }
