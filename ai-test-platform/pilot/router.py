from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from .db import get_db
from .schemas import (
    EnvironmentCreate,
    EnvironmentUpdate,
    OpenApiGenerateCasesRequest,
    OpenApiImportFromUrl,
    ProjectCreate,
    ProjectUpdate,
    ReportGenerateRequest,
    SystemSettingUpdate,
    TestRunCreate,
)
from .security import require_role
from .services import (
    create_environment,
    create_project,
    create_test_run,
    delete_project,
    execute_run,
    generate_openapi_cases,
    get_project_detail,
    get_report_detail,
    get_run_detail,
    get_system_settings,
    import_openapi_from_file,
    import_openapi_from_url,
    list_apis,
    list_projects,
    list_reports,
    list_runs,
    list_test_cases,
    regenerate_report,
    update_environment,
    update_project,
    upsert_system_setting,
)


router = APIRouter(prefix="/api/pilot", tags=["pilot"])


@router.get("/projects")
def api_list_projects(db: Session = Depends(get_db)):
    projects = list_projects(db)
    return {"success": True, "projects": projects, "count": len(projects)}


@router.post("/projects")
def api_create_project(payload: ProjectCreate, db: Session = Depends(get_db), _: str = Depends(require_role("admin"))):
    project = create_project(db, payload.model_dump())
    return {"success": True, "project": project}


@router.get("/projects/{project_id}")
def api_get_project(project_id: int, db: Session = Depends(get_db)):
    return {"success": True, "project": get_project_detail(db, project_id)}


@router.put("/projects/{project_id}")
def api_update_project(project_id: int, payload: ProjectUpdate, db: Session = Depends(get_db), _: str = Depends(require_role("admin"))):
    return {"success": True, "project": update_project(db, project_id, payload.model_dump(exclude_none=True))}


@router.delete("/projects/{project_id}")
def api_delete_project(project_id: int, db: Session = Depends(get_db), _: str = Depends(require_role("admin"))):
    delete_project(db, project_id)
    return {"success": True}


@router.post("/environments")
def api_create_environment(payload: EnvironmentCreate, db: Session = Depends(get_db), _: str = Depends(require_role("admin"))):
    return {"success": True, "environment": create_environment(db, payload.model_dump())}


@router.put("/environments/{environment_id}")
def api_update_environment(environment_id: int, payload: EnvironmentUpdate, db: Session = Depends(get_db), _: str = Depends(require_role("admin"))):
    return {"success": True, "environment": update_environment(db, environment_id, payload.model_dump(exclude_none=True))}


@router.post("/openapi/import-url")
def api_import_openapi_url(payload: OpenApiImportFromUrl, db: Session = Depends(get_db), _: str = Depends(require_role("operator"))):
    return {"success": True, **import_openapi_from_url(db, payload.project_id, payload.environment_id, payload.url)}


@router.post("/openapi/import-file")
async def api_import_openapi_file(
    project_id: int = Query(...),
    environment_id: int = Query(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: str = Depends(require_role("operator")),
):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="上传文件为空")
    return {"success": True, **import_openapi_from_file(db, project_id, environment_id, file.filename, content)}


@router.get("/apis")
def api_list_apis(project_id: int | None = Query(default=None), db: Session = Depends(get_db)):
    apis = list_apis(db, project_id=project_id)
    return {"success": True, "apis": apis, "count": len(apis)}


@router.post("/test-cases/generate")
def api_generate_cases(payload: OpenApiGenerateCasesRequest, db: Session = Depends(get_db), _: str = Depends(require_role("operator"))):
    result = generate_openapi_cases(db, payload.project_id, payload.api_ids)
    return {"success": True, **result}


@router.get("/test-cases")
def api_list_cases(project_id: int | None = Query(default=None), db: Session = Depends(get_db)):
    cases = list_test_cases(db, project_id=project_id)
    return {"success": True, "test_cases": cases, "count": len(cases)}


@router.get("/test-runs")
def api_list_runs(project_id: int | None = Query(default=None), db: Session = Depends(get_db)):
    runs = list_runs(db, project_id=project_id)
    return {"success": True, "testRuns": runs, "count": len(runs)}


@router.post("/test-runs")
def api_create_run(
    payload: TestRunCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    role: str = Depends(require_role("operator")),
):
    run = create_test_run(db, payload.model_dump(), role)
    background_tasks.add_task(_background_execute_run, payload.model_dump()["project_id"], run["id"])
    return {"success": True, "testRun": run}


def _background_execute_run(project_id: int, run_id: int) -> None:
    from .db import SessionLocal

    with SessionLocal() as db:
        execute_run(db, run_id)


@router.get("/test-runs/{run_id}")
def api_get_run(run_id: int, db: Session = Depends(get_db)):
    return {"success": True, "testRun": get_run_detail(db, run_id)}


@router.get("/reports")
def api_list_reports(project_id: int | None = Query(default=None), db: Session = Depends(get_db)):
    reports = list_reports(db, project_id=project_id)
    return {"success": True, "reports": reports, "count": len(reports)}


@router.post("/reports/generate")
def api_generate_report(payload: ReportGenerateRequest, db: Session = Depends(get_db), _: str = Depends(require_role("operator"))):
    return {"success": True, "report": regenerate_report(db, payload.run_id)}


@router.get("/reports/{report_id}")
def api_get_report(report_id: int, db: Session = Depends(get_db)):
    return {"success": True, "report": get_report_detail(db, report_id)}


@router.get("/system/settings")
def api_get_settings(db: Session = Depends(get_db), _: str = Depends(require_role("viewer"))):
    settings = get_system_settings(db)
    return {"success": True, "settings": settings}


@router.put("/system/settings")
def api_put_setting(payload: SystemSettingUpdate, db: Session = Depends(get_db), _: str = Depends(require_role("admin"))):
    setting = upsert_system_setting(db, payload.key, payload.value, payload.description)
    return {"success": True, "setting": setting}
