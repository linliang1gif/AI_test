# -*- coding: utf-8 -*-
"""
P3-3B: 缺陷闭环 MVP 路由
9 个 API 端点: CRUD + 状态流转 + 从 run_case/failure_analysis 创建 + 重复检测 + 关联 run
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session

from database import get_db
from services.defect_service import (
    create_defect, list_defects, get_defect, update_defect,
    transition_defect, check_duplicates, create_from_run_case,
    create_from_failure_analysis, link_run, get_defect_summary_for_gate,
)

router = APIRouter(prefix="/api/v2/defects", tags=["缺陷管理"])


# ── Schemas ───────────────────────────────────────────
class DefectCreateRequest(BaseModel):
    title: str
    description: Optional[str] = ""
    project_id: Optional[int] = None
    module: Optional[str] = ""
    severity: Optional[str] = "major"
    priority: Optional[str] = "P2"
    source: Optional[str] = "manual"
    failure_category: Optional[str] = ""
    case_id: Optional[str] = None
    run_id: Optional[str] = None
    run_case_id: Optional[str] = None
    report_id: Optional[str] = None
    trace_path: Optional[str] = None
    screenshot_path: Optional[str] = None
    evidence_json: Optional[dict] = None
    created_by: Optional[str] = "system"
    assigned_to: Optional[str] = None


class DefectUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    module: Optional[str] = None
    severity: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    failure_category: Optional[str] = None
    updated_by: Optional[str] = "system"


class TransitionRequest(BaseModel):
    to_status: str
    comment: Optional[str] = ""
    by: Optional[str] = "system"


class FromRunCaseRequest(BaseModel):
    run_case_id: str
    title: Optional[str] = None
    description: Optional[str] = ""
    severity: Optional[str] = "major"
    priority: Optional[str] = "P2"
    module: Optional[str] = ""
    project_id: Optional[int] = None
    created_by: Optional[str] = "system"


class FromFailureAnalysisRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = ""
    case_id: Optional[str] = None
    run_id: Optional[str] = None
    run_case_id: Optional[str] = None
    failure_category: Optional[str] = "unknown"
    error_message: Optional[str] = ""
    suggested_action: Optional[str] = ""
    console_errors: Optional[list] = []
    network_errors: Optional[list] = []
    screenshot_path: Optional[str] = None
    trace_path: Optional[str] = None
    severity: Optional[str] = "major"
    priority: Optional[str] = "P2"
    module: Optional[str] = ""
    project_id: Optional[int] = None
    created_by: Optional[str] = "system"


class LinkRunRequest(BaseModel):
    run_id: str
    by: Optional[str] = "system"


# ── 1. POST /api/v2/defects — 创建缺陷 ──
@router.post("")
def api_create_defect(req: DefectCreateRequest, db: Session = Depends(get_db)):
    result = create_defect(db, req.model_dump())
    return result


# ── 2. GET /api/v2/defects — 查询缺陷列表 ──
@router.get("")
def api_list_defects(
    project_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return list_defects(db, project_id=project_id, status=status, severity=severity,
                        source=source, keyword=keyword, limit=limit, offset=offset)


# ── 3. GET /api/v2/defects/{defect_id} — 缺陷详情 ──
@router.get("/{defect_id}")
def api_get_defect(defect_id: int, db: Session = Depends(get_db)):
    result = get_defect(db, defect_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Defect {defect_id} not found")
    return result


# ── 4. PUT /api/v2/defects/{defect_id} — 更新缺陷 ──
@router.put("/{defect_id}")
def api_update_defect(defect_id: int, req: DefectUpdateRequest, db: Session = Depends(get_db)):
    data = {k: v for k, v in req.model_dump().items() if v is not None}
    result = update_defect(db, defect_id, data)
    if not result:
        raise HTTPException(status_code=404, detail=f"Defect {defect_id} not found")
    return result


# ── 5. POST /api/v2/defects/{defect_id}/transition — 状态流转 ──
@router.post("/{defect_id}/transition")
def api_transition(defect_id: int, req: TransitionRequest, db: Session = Depends(get_db)):
    result = transition_defect(db, defect_id, req.to_status, req.comment, req.by)
    if "error" in result:
        if result["error"] == "defect_not_found":
            raise HTTPException(status_code=404, detail="Defect not found")
        raise HTTPException(status_code=400, detail=result)
    return result


# ── 6. POST /api/v2/defects/from-run-case — 从 run_case 创建 ──
@router.post("/from-run-case")
def api_from_run_case(req: FromRunCaseRequest, db: Session = Depends(get_db)):
    result = create_from_run_case(db, req.run_case_id, req.model_dump())
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ── 7. POST /api/v2/defects/from-failure-analysis — 从失败归因创建 ──
@router.post("/from-failure-analysis")
def api_from_failure_analysis(req: FromFailureAnalysisRequest, db: Session = Depends(get_db)):
    result = create_from_failure_analysis(db, req.model_dump())
    return result


# ── 8. GET /api/v2/defects/duplicates/check — 检查重复 ──
@router.get("/duplicates/check")
def api_check_duplicates(
    project_id: Optional[int] = Query(None),
    case_id: Optional[str] = Query(None),
    failure_category: Optional[str] = Query(None),
    error_message: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    return check_duplicates(db, project_id, case_id, failure_category, error_message)


# ── 9. POST /api/v2/defects/{defect_id}/link-run — 关联执行记录 ──
@router.post("/{defect_id}/link-run")
def api_link_run(defect_id: int, req: LinkRunRequest, db: Session = Depends(get_db)):
    result = link_run(db, defect_id, req.run_id, req.by)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ── 10. GET /api/v2/defects/summary/for-gate — 质量门禁缺陷摘要 ──
@router.get("/summary/for-gate")
def api_defect_summary(
    run_id: Optional[str] = Query(None),
    case_ids: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    cids = case_ids.split(",") if case_ids else None
    return get_defect_summary_for_gate(db, case_ids=cids, run_id=run_id)
