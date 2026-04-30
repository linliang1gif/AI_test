from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, declarative_base, sessionmaker


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_PATH = DATA_DIR / "platform_pilot.db"

engine = create_engine(
    f"sqlite:///{DATABASE_PATH}",
    future=True,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def get_db() -> Iterable[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _coerce_json(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default
    return default


def _read_legacy_payload() -> Dict[str, Any]:
    candidates = [
        BASE_DIR / "data" / "platform_data.json",
        BASE_DIR.parent / "data" / "platform_data.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return json.loads(candidate.read_text(encoding="utf-8"))
    return {}


def init_database() -> None:
    from .models import (
        ApiSpecModel,
        DatasetModel,
        EnvironmentModel,
        HealingRecordModel,
        ProjectModel,
        ReportModel,
        RunStepModel,
        SystemSettingModel,
        TestCaseModel,
        TestRunModel,
    )

    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        existing_project = db.execute(select(ProjectModel.id).limit(1)).scalar_one_or_none()
        if existing_project is not None:
            return

        legacy = _read_legacy_payload()
        legacy_projects = legacy.get("projects", [])
        legacy_apis = legacy.get("apis", [])
        legacy_cases = legacy.get("test_cases", [])
        legacy_runs = legacy.get("test_runs", [])
        legacy_reports = legacy.get("reports", [])

        if not legacy_projects:
            seed_project = ProjectModel(
                name="真实项目试点示例",
                description="用于验证首个真实项目接入闭环的默认项目",
                status="active",
                owner="system",
                team="pilot",
                default_role="admin",
                tags=["pilot"],
            )
            db.add(seed_project)
            db.flush()
            db.add(
                EnvironmentModel(
                    project_id=seed_project.id,
                    name="测试环境",
                    environment_type="test",
                    base_url="https://jsonplaceholder.typicode.com",
                    auth_type="none",
                    default_headers={},
                    timeout_seconds=30,
                    retry_policy={"max_retries": 1, "retry_backoff_seconds": 1},
                    env_var_mapping={},
                    data_isolation_key="pilot",
                    allow_write_operations=False,
                    allow_self_healing=True,
                    allow_auto_test_data=True,
                    is_default=True,
                )
            )
            db.add(
                SystemSettingModel(
                    key="platform_security",
                    value={
                        "default_role": "admin",
                        "masked_fields": ["authorization", "token", "api_key", "cookie"],
                    },
                    description="Pilot security defaults",
                    updated_at=datetime.utcnow(),
                )
            )
            db.commit()
            return

        project_id_map: Dict[str, int] = {}
        for project in legacy_projects:
            model = ProjectModel(
                name=project.get("name", "未命名项目"),
                description=project.get("description", ""),
                status=project.get("status", "active"),
                owner=project.get("owner") or project.get("team") or "unknown",
                team=project.get("team", ""),
                default_role="admin",
                tags=[],
            )
            db.add(model)
            db.flush()
            project_id_map[str(project.get("id"))] = model.id

            db.add(
                EnvironmentModel(
                    project_id=model.id,
                    name=f"{project.get('environment', 'test')} 环境",
                    environment_type=project.get("environment", "test"),
                    base_url=project.get("baseUrl", ""),
                    auth_type="none",
                    default_headers={},
                    timeout_seconds=30,
                    retry_policy={"max_retries": 1, "retry_backoff_seconds": 1},
                    env_var_mapping={},
                    data_isolation_key=model.name,
                    allow_write_operations=False,
                    allow_self_healing=True,
                    allow_auto_test_data=True,
                    is_default=True,
                )
            )

        fallback_project_id = next(iter(project_id_map.values()))

        for api in legacy_apis:
            db.add(
                ApiSpecModel(
                    project_id=fallback_project_id,
                    source_type="legacy_json",
                    source_location="platform_data.json",
                    method=api.get("method", "GET"),
                    path=api.get("path", "/"),
                    name=api.get("name") or api.get("summary") or api.get("path", "/"),
                    summary=api.get("summary", ""),
                    description=api.get("description", ""),
                    tags=_coerce_json(api.get("tags"), []),
                    parameters=_coerce_json(api.get("parameters"), []),
                    request_body=_coerce_json(api.get("requestBody"), {}),
                    responses=_coerce_json(api.get("responses"), {}),
                    raw_definition=api,
                    imported_at=datetime.utcnow(),
                )
            )

        for case in legacy_cases:
            db.add(
                TestCaseModel(
                    project_id=fallback_project_id,
                    api_spec_id=None,
                    title=case.get("title", "未命名用例"),
                    module=case.get("module", "default"),
                    priority=str(case.get("priority", "medium")),
                    status=str(case.get("status", "pending")),
                    case_type=case.get("type", "功能测试"),
                    scenario_type=case.get("data_type", "valid"),
                    expected_behavior=case.get("expected_behavior", "success"),
                    source=case.get("source", "legacy_json"),
                    description=case.get("description", ""),
                    steps=case.get("steps", []),
                    expected=case.get("expected", ""),
                    tags=case.get("tags", []),
                    execution_config=case.get("execution_config", {}),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
            )

        for run in legacy_runs:
            db.add(
                TestRunModel(
                    project_id=fallback_project_id,
                    environment_id=None,
                    report_id=None,
                    name=run.get("name") or run.get("testcase_title") or "legacy-run",
                    status=run.get("status", "failed"),
                    trigger_source="legacy_json",
                    requested_by_role="admin",
                    created_at=datetime.utcnow(),
                    started_at=datetime.utcnow(),
                    ended_at=datetime.utcnow(),
                    trace_id=run.get("trace_id"),
                    request_id=run.get("trace_id"),
                    selected_case_ids=[],
                    summary={
                        "total": run.get("totalTests", 0),
                        "passed": run.get("passed", 0),
                        "failed": run.get("failed", 0),
                    },
                    status_history=[],
                    last_error=run.get("stderr") or run.get("error"),
                )
            )

        for report in legacy_reports:
            db.add(
                ReportModel(
                    project_id=fallback_project_id,
                    run_id=None,
                    name=report.get("name", "legacy-report"),
                    report_type=report.get("type", "legacy"),
                    summary=report,
                    content=report,
                    failure_overview={},
                    created_at=datetime.utcnow(),
                    trace_id=None,
                )
            )

        db.add(
            DatasetModel(
                project_id=fallback_project_id,
                name="默认试点数据集",
                description="系统初始化数据集",
                tags=["seed"],
                schema={},
                data={"note": "legacy migration bootstrap"},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )
        db.add(
            SystemSettingModel(
                key="platform_security",
                value={
                    "default_role": "admin",
                    "masked_fields": ["authorization", "token", "api_key", "cookie"],
                },
                description="Pilot security defaults",
                updated_at=datetime.utcnow(),
            )
        )
        db.commit()
