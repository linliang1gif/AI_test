"""
AI Product Studio — 路由层
前缀: /api/v2/product-studio
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from database import get_db
from services.product_studio_service import ProductStudioService

router = APIRouter(prefix="/api/v2/product-studio", tags=["Product Studio"])


# ── 请求体 ──────────────────────────────────────────────────────

class CreateIdeaRequest(BaseModel):
    title: str
    product_direction: str = ""
    target_users: str = ""
    pain_points: str = ""
    existing_assets: str = ""
    current_blockers: str = ""
    constraints: str = ""
    project_id: Optional[int] = None


class UpdateArtifactRequest(BaseModel):
    title: Optional[str] = None
    content_markdown: Optional[str] = None
    status: Optional[str] = None


class GenerateRequest(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None


class ReviewRequest(BaseModel):
    review_reason: str = ""


# ── 接口 ────────────────────────────────────────────────────────

@router.post("/ideas")
def create_idea(req: CreateIdeaRequest, db: Session = Depends(get_db)):
    if not req.title.strip():
        raise HTTPException(status_code=400, detail="产品名称不能为空")
    svc = ProductStudioService(db)
    return svc.create_idea(req.dict())


@router.get("/ideas")
def list_ideas(
    keyword: Optional[str] = Query(None),
    project_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    svc = ProductStudioService(db)
    return svc.list_ideas(keyword=keyword, project_id=project_id, page=page, page_size=page_size)


@router.get("/ideas/{idea_id}")
def get_idea_detail(idea_id: str, db: Session = Depends(get_db)):
    svc = ProductStudioService(db)
    result = svc.get_idea_detail(idea_id)
    if not result:
        raise HTTPException(status_code=404, detail="产品想法不存在")
    return result


def _do_generate(db: Session, idea_id: str, run_type: str, req: GenerateRequest):
    svc = ProductStudioService(db)
    try:
        return svc.generate(idea_id, run_type, provider=req.provider, model=req.model)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/ideas/{idea_id}/generate-solution")
def generate_solution(idea_id: str, req: GenerateRequest = GenerateRequest(), db: Session = Depends(get_db)):
    return _do_generate(db, idea_id, "product_solution", req)


@router.post("/ideas/{idea_id}/generate-prd")
def generate_prd(idea_id: str, req: GenerateRequest = GenerateRequest(), db: Session = Depends(get_db)):
    return _do_generate(db, idea_id, "prd", req)


@router.post("/ideas/{idea_id}/generate-prototype")
def generate_prototype(idea_id: str, req: GenerateRequest = GenerateRequest(), db: Session = Depends(get_db)):
    return _do_generate(db, idea_id, "prototype", req)


@router.post("/ideas/{idea_id}/generate-test-strategy")
def generate_test_strategy(idea_id: str, req: GenerateRequest = GenerateRequest(), db: Session = Depends(get_db)):
    return _do_generate(db, idea_id, "test_strategy", req)


@router.post("/ideas/{idea_id}/generate-acceptance-criteria")
def generate_acceptance_criteria(idea_id: str, req: GenerateRequest = GenerateRequest(), db: Session = Depends(get_db)):
    return _do_generate(db, idea_id, "acceptance_criteria", req)


@router.get("/artifacts/{artifact_id}")
def get_artifact(artifact_id: str, db: Session = Depends(get_db)):
    svc = ProductStudioService(db)
    result = svc.get_artifact(artifact_id)
    if not result:
        raise HTTPException(status_code=404, detail="Artifact 不存在")
    return result


@router.put("/artifacts/{artifact_id}")
def update_artifact(artifact_id: str, req: UpdateArtifactRequest, db: Session = Depends(get_db)):
    svc = ProductStudioService(db)
    result = svc.update_artifact(artifact_id, req.dict(exclude_none=True))
    if not result:
        raise HTTPException(status_code=404, detail="Artifact 不存在")
    return result


@router.post("/artifacts/{artifact_id}/export")
def export_artifact(artifact_id: str, db: Session = Depends(get_db)):
    svc = ProductStudioService(db)
    result = svc.export_artifact(artifact_id)
    if not result:
        raise HTTPException(status_code=404, detail="Artifact 不存在")
    return Response(
        content=result["content"],
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename={result['filename']}"},
    )


@router.get("/runs/{run_id}")
def get_run(run_id: str, db: Session = Depends(get_db)):
    svc = ProductStudioService(db)
    result = svc.get_run(run_id)
    if not result:
        raise HTTPException(status_code=404, detail="Run 不存在")
    return result


# ── Phase 2: Artifact → 测试资产 ────────────────────────────────

@router.post("/artifacts/{artifact_id}/generate-requirement-points")
def generate_requirement_points(artifact_id: str, db: Session = Depends(get_db)):
    svc = ProductStudioService(db)
    try:
        return svc.generate_requirement_points(artifact_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TypeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/artifacts/{artifact_id}/generate-test-cases")
def generate_test_cases(artifact_id: str, db: Session = Depends(get_db)):
    svc = ProductStudioService(db)
    try:
        return svc.generate_test_cases(artifact_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TypeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/artifacts/{artifact_id}/trace-links")
def get_trace_links(artifact_id: str, db: Session = Depends(get_db)):
    svc = ProductStudioService(db)
    result = svc.get_trace_links(artifact_id)
    if not result:
        raise HTTPException(status_code=404, detail="Artifact 不存在")
    return result


@router.post("/trace-links/{link_id}/confirm")
def confirm_trace_link(link_id: str, req: ReviewRequest = ReviewRequest(), db: Session = Depends(get_db)):
    svc = ProductStudioService(db)
    result = svc.confirm_trace_link(link_id, review_reason=req.review_reason)
    if not result:
        raise HTTPException(status_code=404, detail="TraceLink 不存在")
    return result


@router.post("/trace-links/{link_id}/reject")
def reject_trace_link(link_id: str, req: ReviewRequest = ReviewRequest(), db: Session = Depends(get_db)):
    svc = ProductStudioService(db)
    result = svc.reject_trace_link(link_id, review_reason=req.review_reason)
    if not result:
        raise HTTPException(status_code=404, detail="TraceLink 不存在")
    return result


# ── Phase 3: 质量治理 ────────────────────────────────────────────

@router.post("/trace-links/{link_id}/score")
def score_trace_link(link_id: str, db: Session = Depends(get_db)):
    svc = ProductStudioService(db)
    result = svc.score_trace_link(link_id)
    if not result:
        raise HTTPException(status_code=404, detail="TraceLink 不存在")
    return result


@router.post("/artifacts/{artifact_id}/score-trace-links")
def score_artifact_trace_links(artifact_id: str, db: Session = Depends(get_db)):
    svc = ProductStudioService(db)
    result = svc.score_artifact_trace_links(artifact_id)
    if not result:
        raise HTTPException(status_code=404, detail="Artifact 不存在")
    return result


@router.post("/trace-links/{link_id}/promote-to-test-case")
def promote_to_test_case(link_id: str, db: Session = Depends(get_db)):
    svc = ProductStudioService(db)
    try:
        result = svc.promote_to_test_case(link_id)
    except TypeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not result:
        raise HTTPException(status_code=404, detail="TraceLink 不存在")
    return result


@router.get("/artifacts/{artifact_id}/quality-summary")
def get_quality_summary(artifact_id: str, db: Session = Depends(get_db)):
    svc = ProductStudioService(db)
    result = svc.get_quality_summary(artifact_id)
    if not result:
        raise HTTPException(status_code=404, detail="Artifact 不存在")
    return result


# ── Phase 5: 质量报告与演示闭环 ─────────────────────────────────

class BatchPromoteRequest(BaseModel):
    min_quality_score: float = 0.8
    only_confirmed: bool = True
    max_count: int = 20


@router.get("/ideas/{idea_id}/quality-dashboard")
def get_quality_dashboard(idea_id: str, db: Session = Depends(get_db)):
    svc = ProductStudioService(db)
    result = svc.get_quality_dashboard(idea_id)
    if not result:
        raise HTTPException(status_code=404, detail="产品想法不存在")
    return result


@router.post("/ideas/{idea_id}/generate-quality-report")
def generate_quality_report(idea_id: str, db: Session = Depends(get_db)):
    svc = ProductStudioService(db)
    result = svc.generate_quality_report(idea_id)
    if not result:
        raise HTTPException(status_code=404, detail="产品想法不存在")
    return result


@router.post("/ideas/{idea_id}/batch-promote-test-cases")
def batch_promote_test_cases(idea_id: str, req: BatchPromoteRequest = BatchPromoteRequest(),
                              db: Session = Depends(get_db)):
    svc = ProductStudioService(db)
    result = svc.batch_promote_test_cases(
        idea_id, min_quality_score=req.min_quality_score,
        only_confirmed=req.only_confirmed, max_count=req.max_count)
    if result is None:
        raise HTTPException(status_code=404, detail="产品想法不存在")
    return result
