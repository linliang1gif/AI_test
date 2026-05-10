"""
AI Dev Studio — 路由层
前缀: /api/v2/dev-studio
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from database import get_db
from services.dev_studio_service import DevStudioService

router = APIRouter(prefix="/api/v2/dev-studio", tags=["Dev Studio"])


# ── 请求体 ──────────────────────────────────────────────────────

class CreateTaskRequest(BaseModel):
    source_type: str = "manual"
    source_id: Optional[str] = None
    idea_id: Optional[str] = None
    project_id: Optional[int] = None
    title: str = ""
    description: str = ""


class UpdateArtifactRequest(BaseModel):
    title: Optional[str] = None
    content_markdown: Optional[str] = None
    status: Optional[str] = None


class GenerateAllRequest(BaseModel):
    artifact_types: Optional[list] = None
    continue_on_error: bool = True
    regenerate_existing: bool = True


class GeneratePatchDraftRequest(BaseModel):
    source_file_impact_artifact_id: Optional[str] = None
    snapshot_id: Optional[str] = None
    max_files: int = 10


class ReviewPatchDraftRequest(BaseModel):
    strict_mode: bool = True
    include_test_mapping: bool = True
    include_security_check: bool = True


# ── Task 接口 ────────────────────────────────────────────────────

@router.post("/tasks")
def create_task(req: CreateTaskRequest, db: Session = Depends(get_db)):
    try:
        result = DevStudioService.create_task(db, req.dict())
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks")
def list_tasks(
    keyword: Optional[str] = Query(None),
    project_id: Optional[int] = Query(None),
    idea_id: Optional[str] = Query(None),
    source_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return DevStudioService.list_tasks(db, keyword, project_id, idea_id, source_type, page, page_size)


@router.get("/tasks/{dev_task_id}")
def get_task_detail(dev_task_id: str, db: Session = Depends(get_db)):
    result = DevStudioService.get_task_detail(db, dev_task_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"DevTask 不存在: {dev_task_id}")
    return result


# ── 生成接口 ──────────────────────────────────────────────────────

@router.post("/tasks/{dev_task_id}/generate-dev-plan")
def generate_dev_plan(dev_task_id: str, db: Session = Depends(get_db)):
    result = DevStudioService.generate_dev_plan(db, dev_task_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"DevTask 不存在: {dev_task_id}")
    return result


@router.post("/tasks/{dev_task_id}/generate-api-design")
def generate_api_design(dev_task_id: str, db: Session = Depends(get_db)):
    result = DevStudioService.generate_api_design(db, dev_task_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"DevTask 不存在: {dev_task_id}")
    return result


@router.post("/tasks/{dev_task_id}/generate-db-design")
def generate_db_design(dev_task_id: str, db: Session = Depends(get_db)):
    result = DevStudioService.generate_db_design(db, dev_task_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"DevTask 不存在: {dev_task_id}")
    return result


@router.post("/tasks/{dev_task_id}/generate-file-impact")
def generate_file_impact(dev_task_id: str, db: Session = Depends(get_db)):
    result = DevStudioService.generate_file_impact(db, dev_task_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"DevTask 不存在: {dev_task_id}")
    return result


@router.post("/tasks/{dev_task_id}/generate-test-plan")
def generate_test_plan(dev_task_id: str, db: Session = Depends(get_db)):
    result = DevStudioService.generate_test_plan(db, dev_task_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"DevTask 不存在: {dev_task_id}")
    return result


# ── Patch Draft 生成 ──────────────────────────────────────────────

@router.post("/tasks/{dev_task_id}/generate-patch-draft")
def generate_patch_draft(dev_task_id: str, req: GeneratePatchDraftRequest = GeneratePatchDraftRequest(), db: Session = Depends(get_db)):
    if req.max_files > 20:
        raise HTTPException(status_code=400, detail="max_files 不能超过 20")
    result = DevStudioService.generate_patch_draft(
        db, dev_task_id,
        source_file_impact_artifact_id=req.source_file_impact_artifact_id,
        snapshot_id=req.snapshot_id,
        max_files=req.max_files,
    )
    if result is None:
        raise HTTPException(status_code=404, detail=f"DevTask 不存在: {dev_task_id}")
    if isinstance(result, dict) and result.get("_error") == "no_file_impact":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


# ── 批量生成 ──────────────────────────────────────────────────────

@router.post("/tasks/{dev_task_id}/generate-all")
def generate_all(dev_task_id: str, req: GenerateAllRequest = GenerateAllRequest(), db: Session = Depends(get_db)):
    try:
        result = DevStudioService.generate_all_artifacts(
            db, dev_task_id,
            artifact_types=req.artifact_types,
            continue_on_error=req.continue_on_error,
            regenerate_existing=req.regenerate_existing,
        )
    except TypeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if result is None:
        raise HTTPException(status_code=404, detail=f"DevTask 不存在: {dev_task_id}")
    return result


# ── 开发包接口 ──────────────────────────────────────────────────────

@router.get("/tasks/{dev_task_id}/packages")
def list_packages(dev_task_id: str, db: Session = Depends(get_db)):
    result = DevStudioService.list_packages(db, dev_task_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"DevTask 不存在: {dev_task_id}")
    return result


@router.get("/tasks/{dev_task_id}/packages/{batch_id}")
def get_package_detail(dev_task_id: str, batch_id: str, db: Session = Depends(get_db)):
    result = DevStudioService.get_package_detail(db, dev_task_id, batch_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"DevTask 不存在: {dev_task_id}")
    if isinstance(result, dict) and result.get("_not_found"):
        raise HTTPException(status_code=404, detail=f"开发包不存在: {batch_id}")
    return result


# ── Artifact 接口 ──────────────────────────────────────────────────

@router.get("/artifacts/{dev_artifact_id}")
def get_artifact(dev_artifact_id: str, db: Session = Depends(get_db)):
    result = DevStudioService.get_artifact(db, dev_artifact_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"DevArtifact 不存在: {dev_artifact_id}")
    return result


@router.put("/artifacts/{dev_artifact_id}")
def update_artifact(dev_artifact_id: str, req: UpdateArtifactRequest, db: Session = Depends(get_db)):
    result = DevStudioService.update_artifact(db, dev_artifact_id, req.dict(exclude_none=True))
    if result is None:
        raise HTTPException(status_code=404, detail=f"DevArtifact 不存在: {dev_artifact_id}")
    return result


@router.post("/artifacts/{dev_artifact_id}/export")
def export_artifact(dev_artifact_id: str, db: Session = Depends(get_db)):
    result = DevStudioService.export_artifact(db, dev_artifact_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"DevArtifact 不存在: {dev_artifact_id}")
    return Response(
        content=result["content"],
        media_type=result["content_type"],
        headers={"Content-Disposition": f'attachment; filename="{result["filename"]}"'},
    )


# ── Patch Review 接口 ──────────────────────────────────────────────

@router.post("/artifacts/{dev_artifact_id}/review-patch-draft")
def review_patch_draft(dev_artifact_id: str, req: ReviewPatchDraftRequest = ReviewPatchDraftRequest(), db: Session = Depends(get_db)):
    result = DevStudioService.review_patch_draft(
        db, dev_artifact_id,
        strict_mode=req.strict_mode,
        include_test_mapping=req.include_test_mapping,
        include_security_check=req.include_security_check,
    )
    if result is None:
        raise HTTPException(status_code=404, detail=f"DevArtifact 不存在: {dev_artifact_id}")
    if isinstance(result, dict) and result.get("_error") == "not_patch_draft":
        raise HTTPException(status_code=400, detail=result["message"])
    if isinstance(result, dict) and result.get("_error") == "empty_content":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


# ── Run 接口 ──────────────────────────────────────────────────────

@router.get("/runs/{run_id}")
def get_run(run_id: str, db: Session = Depends(get_db)):
    result = DevStudioService.get_run(db, run_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"DevStudioRun 不存在: {run_id}")
    return result
