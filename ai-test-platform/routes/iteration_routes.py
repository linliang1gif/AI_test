#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迭代管理路由
POST   /api/v2/projects/{project_id}/iterations          创建迭代
GET    /api/v2/projects/{project_id}/iterations          列表(支持 status 过滤)
GET    /api/v2/iterations/{iteration_id}                 详情(含统计)
PUT    /api/v2/iterations/{iteration_id}                 更新
DELETE /api/v2/iterations/{iteration_id}                 删除(confirm_text 守卫)
POST   /api/v2/iterations/{iteration_id}/assign-cases    批量分配用例
POST   /api/v2/iterations/{iteration_id}/unassign-cases  批量移除用例
"""
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.session import get_db
from database.models import Iteration, TestCase, TestRun, Project, IterationRequirement, IterationTestPoint
from backend.danger_guard import check_confirm

logger = logging.getLogger("iteration_routes")

router = APIRouter(tags=["iterations"])

VALID_STATUSES = ["planning", "in_progress", "completed", "archived"]


# ── Request / Response Models ──

class CreateIterationRequest(BaseModel):
    name: str
    code: Optional[str] = None
    description: Optional[str] = ""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: str = "planning"
    owner: Optional[str] = ""


class UpdateIterationRequest(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: Optional[str] = None
    owner: Optional[str] = None


class DeleteIterationRequest(BaseModel):
    confirm: bool = False
    confirm_text: str = ""


class AssignCasesRequest(BaseModel):
    case_ids: List[str]


# ── Helpers ──

def _iter_to_dict(it: Iteration, stats: dict = None) -> dict:
    d = {
        "id": it.id,
        "project_id": it.project_id,
        "name": it.name,
        "code": it.code or "",
        "description": it.description or "",
        "start_date": it.start_date or "",
        "end_date": it.end_date or "",
        "status": it.status,
        "owner": it.owner or "",
        "created_at": it.created_at.isoformat() if it.created_at else None,
        "updated_at": it.updated_at.isoformat() if it.updated_at else None,
    }
    if stats:
        d.update(stats)
    return d


def _get_iteration_stats(db: Session, iteration_id: int) -> dict:
    """获取迭代统计: 用例数、通过率、最近执行"""
    total_cases = db.query(func.count(TestCase.id)).filter(
        TestCase.iteration_id == iteration_id
    ).scalar() or 0

    passed_cases = db.query(func.count(TestCase.id)).filter(
        TestCase.iteration_id == iteration_id,
        TestCase.last_run_status == 'passed',
    ).scalar() or 0

    failed_cases = db.query(func.count(TestCase.id)).filter(
        TestCase.iteration_id == iteration_id,
        TestCase.last_run_status == 'failed',
    ).scalar() or 0

    total_runs = db.query(func.count(TestRun.id)).filter(
        TestRun.iteration_id == iteration_id,
    ).scalar() or 0

    last_run = db.query(TestRun).filter(
        TestRun.iteration_id == iteration_id,
    ).order_by(TestRun.created_at.desc()).first()

    requirement_count = db.query(func.count(IterationRequirement.id)).filter(
        IterationRequirement.iteration_id == iteration_id
    ).scalar() or 0

    test_point_total = db.query(func.count(IterationTestPoint.id)).filter(
        IterationTestPoint.iteration_id == iteration_id
    ).scalar() or 0

    test_point_confirmed = db.query(func.count(IterationTestPoint.id)).filter(
        IterationTestPoint.iteration_id == iteration_id,
        IterationTestPoint.confirmed == True,
    ).scalar() or 0

    return {
        "total_cases": total_cases,
        "passed_cases": passed_cases,
        "failed_cases": failed_cases,
        "pass_rate": round(passed_cases / total_cases * 100, 1) if total_cases > 0 else 0,
        "total_runs": total_runs,
        "last_run_id": last_run.id if last_run else None,
        "last_run_at": last_run.created_at.isoformat() if last_run and last_run.created_at else None,
        "requirement_count": requirement_count,
        "test_point_total": test_point_total,
        "test_point_confirmed": test_point_confirmed,
    }


# ── Routes ──

@router.get("/api/v2/projects/{project_id}/iterations")
def list_iterations(
    project_id: int,
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """获取项目的迭代列表"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    q = db.query(Iteration).filter(Iteration.project_id == project_id)
    if status and status in VALID_STATUSES:
        q = q.filter(Iteration.status == status)
    items = q.order_by(Iteration.created_at.desc()).all()

    result = []
    for it in items:
        stats = _get_iteration_stats(db, it.id)
        result.append(_iter_to_dict(it, stats))

    return {"iterations": result, "total": len(result)}


@router.post("/api/v2/projects/{project_id}/iterations")
def create_iteration(
    project_id: int,
    req: CreateIterationRequest,
    db: Session = Depends(get_db),
):
    """创建迭代"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    if req.status and req.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"无效状态: {req.status}, 可选: {VALID_STATUSES}")

    it = Iteration(
        project_id=project_id,
        name=req.name,
        code=req.code or "",
        description=req.description or "",
        start_date=req.start_date or "",
        end_date=req.end_date or "",
        status=req.status,
        owner=req.owner or "",
    )
    db.add(it)
    db.commit()
    db.refresh(it)
    logger.info(f"迭代创建: id={it.id}, name={it.name}, project_id={project_id}")
    return _iter_to_dict(it)


@router.get("/api/v2/iterations/{iteration_id}")
def get_iteration(
    iteration_id: int,
    db: Session = Depends(get_db),
):
    """获取迭代详情(含统计)"""
    it = db.query(Iteration).filter(Iteration.id == iteration_id).first()
    if not it:
        raise HTTPException(status_code=404, detail="迭代不存在")

    stats = _get_iteration_stats(db, it.id)
    return _iter_to_dict(it, stats)


@router.put("/api/v2/iterations/{iteration_id}")
def update_iteration(
    iteration_id: int,
    req: UpdateIterationRequest,
    db: Session = Depends(get_db),
):
    """更新迭代"""
    it = db.query(Iteration).filter(Iteration.id == iteration_id).first()
    if not it:
        raise HTTPException(status_code=404, detail="迭代不存在")

    if req.status is not None and req.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"无效状态: {req.status}, 可选: {VALID_STATUSES}")

    update_fields = req.dict(exclude_unset=True)
    for k, v in update_fields.items():
        setattr(it, k, v)
    it.updated_at = datetime.now()
    db.commit()
    db.refresh(it)
    logger.info(f"迭代更新: id={it.id}, fields={list(update_fields.keys())}")
    return _iter_to_dict(it)


@router.delete("/api/v2/iterations/{iteration_id}")
def delete_iteration(
    iteration_id: int,
    body: DeleteIterationRequest = Body(DeleteIterationRequest()),
    db: Session = Depends(get_db),
):
    """删除迭代(confirm_text 守卫)"""
    check_confirm("DELETE_ITERATION", body.confirm, body.confirm_text)

    it = db.query(Iteration).filter(Iteration.id == iteration_id).first()
    if not it:
        raise HTTPException(status_code=404, detail="迭代不存在")

    # 解除关联的用例和执行
    db.query(TestCase).filter(TestCase.iteration_id == iteration_id).update(
        {TestCase.iteration_id: None}, synchronize_session='fetch'
    )
    db.query(TestRun).filter(TestRun.iteration_id == iteration_id).update(
        {TestRun.iteration_id: None}, synchronize_session='fetch'
    )
    db.delete(it)
    db.commit()
    logger.info(f"迭代删除: id={iteration_id}")
    return {"message": "迭代已删除", "id": iteration_id}


@router.post("/api/v2/iterations/{iteration_id}/assign-cases")
def assign_cases_to_iteration(
    iteration_id: int,
    req: AssignCasesRequest,
    db: Session = Depends(get_db),
):
    """批量分配用例到迭代"""
    it = db.query(Iteration).filter(Iteration.id == iteration_id).first()
    if not it:
        raise HTTPException(status_code=404, detail="迭代不存在")

    updated = db.query(TestCase).filter(TestCase.id.in_(req.case_ids)).update(
        {TestCase.iteration_id: iteration_id}, synchronize_session='fetch'
    )
    db.commit()
    logger.info(f"用例分配到迭代: iteration_id={iteration_id}, count={updated}")
    return {"message": f"已分配 {updated} 个用例到迭代", "updated": updated}


@router.post("/api/v2/iterations/{iteration_id}/unassign-cases")
def unassign_cases_from_iteration(
    iteration_id: int,
    req: AssignCasesRequest,
    db: Session = Depends(get_db),
):
    """批量从迭代移除用例"""
    updated = db.query(TestCase).filter(
        TestCase.id.in_(req.case_ids),
        TestCase.iteration_id == iteration_id,
    ).update({TestCase.iteration_id: None}, synchronize_session='fetch')
    db.commit()
    logger.info(f"用例从迭代移除: iteration_id={iteration_id}, count={updated}")
    return {"message": f"已从迭代移除 {updated} 个用例", "updated": updated}
