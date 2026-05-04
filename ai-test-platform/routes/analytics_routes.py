"""
P3-4A: 质量驾驶舱 API 路由
GET /api/v2/analytics/overview
GET /api/v2/analytics/test-suite-trend
GET /api/v2/analytics/gate-trend
GET /api/v2/analytics/failure-modules
GET /api/v2/analytics/failure-categories
GET /api/v2/analytics/defect-summary
GET /api/v2/analytics/data-issues
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from services.analytics_service import (
    get_overview,
    get_test_suite_trend,
    get_gate_trend,
    get_failure_modules,
    get_failure_categories,
    get_defect_summary,
    get_data_issues,
    MAX_DAYS,
)

router = APIRouter(prefix="/api/v2/analytics", tags=["质量驾驶舱"])


def _validate_days(days: int) -> int:
    if days > MAX_DAYS:
        raise HTTPException(status_code=400, detail=f"days 不能超过 {MAX_DAYS}")
    return max(days, 1)


@router.get("/overview")
def api_overview(
    project_id: Optional[int] = Query(None),
    days: int = Query(7, ge=1),
    db: Session = Depends(get_db),
):
    days = _validate_days(days)
    return get_overview(db, project_id=project_id, days=days)


@router.get("/test-suite-trend")
def api_suite_trend(
    project_id: Optional[int] = Query(None),
    days: int = Query(7, ge=1),
    suite_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    days = _validate_days(days)
    return get_test_suite_trend(db, project_id=project_id, days=days, suite_type=suite_type)


@router.get("/gate-trend")
def api_gate_trend(
    project_id: Optional[int] = Query(None),
    days: int = Query(7, ge=1),
    db: Session = Depends(get_db),
):
    days = _validate_days(days)
    return get_gate_trend(db, project_id=project_id, days=days)


@router.get("/failure-modules")
def api_failure_modules(
    project_id: Optional[int] = Query(None),
    days: int = Query(7, ge=1),
    top: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    days = _validate_days(days)
    return get_failure_modules(db, project_id=project_id, days=days, top=top)


@router.get("/failure-categories")
def api_failure_categories(
    project_id: Optional[int] = Query(None),
    days: int = Query(7, ge=1),
    db: Session = Depends(get_db),
):
    days = _validate_days(days)
    return get_failure_categories(db, project_id=project_id, days=days)


@router.get("/defect-summary")
def api_defect_summary(
    project_id: Optional[int] = Query(None),
    days: Optional[int] = Query(None, ge=1),
    db: Session = Depends(get_db),
):
    if days and days > MAX_DAYS:
        raise HTTPException(status_code=400, detail=f"days 不能超过 {MAX_DAYS}")
    return get_defect_summary(db, project_id=project_id, days=days)


@router.get("/data-issues")
def api_data_issues(
    project_id: Optional[int] = Query(None),
    days: int = Query(7, ge=1),
    db: Session = Depends(get_db),
):
    days = _validate_days(days)
    return get_data_issues(db, project_id=project_id, days=days)
