"""
P3-5: 智能选测与风险推荐 API
POST /api/v2/test-selection/recommend  — 生成推荐
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from database import get_db
from services.test_selection_service import generate_recommendation
from typing import Optional

router = APIRouter(prefix="/api/v2/test-selection", tags=["test-selection"])

MAX_DAYS = 90


@router.post("/recommend")
def api_recommend(
    body: dict = Body(default={}),
    db: Session = Depends(get_db),
):
    project_id = body.get("project_id")
    days = body.get("days", 14)
    target = body.get("target")
    include_case = body.get("include_case_recommendations", True)
    include_skip = body.get("include_skip_candidates", True)
    suite_type = body.get("suite_type")

    if not isinstance(days, int) or days < 1 or days > MAX_DAYS:
        raise HTTPException(status_code=400, detail=f"days must be 1-{MAX_DAYS}")

    return generate_recommendation(
        db,
        project_id=project_id,
        days=days,
        target=target,
        include_case_recommendations=include_case,
        include_skip_candidates=include_skip,
        suite_type=suite_type,
    )
