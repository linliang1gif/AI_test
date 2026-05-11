"""
Phase 16: 批量执行中心 - API 路由

POST   /api/v2/batch-runs               创建批量任务
GET    /api/v2/batch-runs               列表
GET    /api/v2/batch-runs/{batch_id}     详情
GET    /api/v2/batch-runs/{batch_id}/progress  实时进度
POST   /api/v2/batch-runs/{batch_id}/stop      停止
GET    /api/v2/batch-runs/{batch_id}/report    报告
"""

import logging

logger = logging.getLogger(__name__)

import json
import threading
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.session import get_db
from services.batch_run_service import (
    BatchRunService,
    get_batch_progress,
    stop_batch,
)

router = APIRouter(prefix="/api/v2/batch-runs", tags=["batch-runs"])


# ── 请求/响应模型 ─────────────────────────────────────

class BatchRunCreateRequest(BaseModel):
    project_id: int = 1
    environment_id: int = 1
    case_ids: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = Field(default=None, description="筛选条件: status, api_pattern, module_prefix, title_keyword")
    batch_size: int = Field(default=50, ge=1, le=500)
    concurrency: int = Field(default=5, ge=1, le=20)


class BatchRunResponse(BaseModel):
    batch_id: str
    status: str
    total_cases: int
    message: str


class BatchRunDetailResponse(BaseModel):
    batch_id: str
    status: str
    trigger_type: str
    total_cases: int
    passed_cases: int
    failed_cases: int
    skipped_cases: int
    pass_rate: float
    duration_seconds: Optional[float]
    created_at: Optional[str]
    started_at: Optional[str]
    finished_at: Optional[str]
    summary: Optional[dict]
    run_cases: Optional[List[dict]] = None


class ProgressResponse(BaseModel):
    batch_id: str
    total: int
    executed: int
    passed: int
    failed: int
    skipped: int
    running: int
    stopped: bool
    progress_pct: float
    elapsed_seconds: float
    failure_categories: Dict[str, int]
    status: str = ""


# ── 路由 ──────────────────────────────────────────────

@router.post("", response_model=BatchRunResponse)
async def create_batch_run(req: BatchRunCreateRequest, db: Session = Depends(get_db)):
    """创建批量执行任务并在后台启动"""
    service = BatchRunService(db)
    try:
        test_run = service.create_batch_run(
            project_id=req.project_id,
            environment_id=req.environment_id,
            case_ids=req.case_ids,
            filters=req.filters,
            batch_size=req.batch_size,
            concurrency=req.concurrency,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 后台线程执行
    batch_id = test_run.id
    t = threading.Thread(target=_run_batch_in_background, args=(batch_id,), daemon=True)
    t.start()

    return BatchRunResponse(
        batch_id=batch_id,
        status="created",
        total_cases=test_run.total_cases,
        message=f"批量任务已创建，共 {test_run.total_cases} 条用例，后台执行中",
    )


def _run_batch_in_background(batch_id: str):
    """后台线程执行批量任务（execute_batch 内部自建 DB session）"""
    try:
        service = BatchRunService(db=None)
        service.execute_batch(batch_id)
    except Exception as e:
        logger.info(f"⚠️  批量任务 {batch_id} 执行异常: {e}")
        import traceback
        traceback.print_exc()


@router.get("", response_model=List[dict])
async def list_batch_runs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """获取批量执行任务列表"""
    service = BatchRunService(db)
    runs = service.list_batch_runs(skip=skip, limit=limit)
    result = []
    for r in runs:
        summary = json.loads(r.summary or "{}") if isinstance(r.summary, str) else (r.summary or {})
        pass_rate = round(r.passed_cases / max(r.total_cases, 1) * 100, 1) if r.total_cases else 0
        result.append({
            "batch_id": r.id,
            "status": r.status,
            "total_cases": r.total_cases,
            "passed_cases": r.passed_cases,
            "failed_cases": r.failed_cases,
            "skipped_cases": r.skipped_cases,
            "pass_rate": pass_rate,
            "duration_seconds": round(r.duration or 0, 2),
            "created_at": r.created_at.isoformat() if r.created_at else "",
            "failure_categories": summary.get("failure_categories", {}),
        })
    return result


@router.get("/{batch_id}", response_model=BatchRunDetailResponse)
async def get_batch_run(batch_id: str, include_cases: bool = Query(False), db: Session = Depends(get_db)):
    """获取批量任务详情"""
    service = BatchRunService(db)
    test_run = service.get_batch_run(batch_id)
    if not test_run:
        raise HTTPException(status_code=404, detail=f"批量任务 {batch_id} 不存在")

    summary = json.loads(test_run.summary or "{}") if isinstance(test_run.summary, str) else (test_run.summary or {})
    pass_rate = round(test_run.passed_cases / max(test_run.total_cases, 1) * 100, 1) if test_run.total_cases else 0

    run_cases_data = None
    if include_cases:
        from database.models import RunCase
        run_cases = db.query(RunCase).filter(RunCase.run_id == batch_id).all()
        run_cases_data = []
        for rc in run_cases:
            run_cases_data.append({
                "id": rc.id,
                "test_case_id": rc.test_case_id,
                "status": rc.status,
                "error_type": rc.error_type,
                "error_message": (rc.error_message or "")[:200],
                "duration_ms": round((rc.duration or 0) * 1000, 2),
                "assertions_passed": rc.assertions_passed,
                "assertions_failed": rc.assertions_failed,
            })

    return BatchRunDetailResponse(
        batch_id=test_run.id,
        status=test_run.status,
        trigger_type=test_run.trigger_type or "",
        total_cases=test_run.total_cases,
        passed_cases=test_run.passed_cases,
        failed_cases=test_run.failed_cases,
        skipped_cases=test_run.skipped_cases or 0,
        pass_rate=pass_rate,
        duration_seconds=round(test_run.duration or 0, 2),
        created_at=test_run.created_at.isoformat() if test_run.created_at else "",
        started_at=test_run.start_time.isoformat() if test_run.start_time else "",
        finished_at=test_run.end_time.isoformat() if test_run.end_time else "",
        summary=summary,
        run_cases=run_cases_data,
    )


@router.get("/{batch_id}/progress", response_model=ProgressResponse)
async def get_batch_progress_api(batch_id: str, db: Session = Depends(get_db)):
    """获取实时执行进度"""
    progress = get_batch_progress(batch_id)
    if progress:
        data = progress.to_dict()
        data["status"] = "running"
        return ProgressResponse(**data)

    # 已完成的任务从数据库读
    service = BatchRunService(db)
    test_run = service.get_batch_run(batch_id)
    if not test_run:
        raise HTTPException(status_code=404, detail=f"批量任务 {batch_id} 不存在")

    summary = json.loads(test_run.summary or "{}") if isinstance(test_run.summary, str) else (test_run.summary or {})
    return ProgressResponse(
        batch_id=batch_id,
        total=test_run.total_cases,
        executed=test_run.passed_cases + test_run.failed_cases + (test_run.skipped_cases or 0),
        passed=test_run.passed_cases,
        failed=test_run.failed_cases,
        skipped=test_run.skipped_cases or 0,
        running=0,
        stopped=test_run.status == "aborted",
        progress_pct=100.0 if test_run.status != "created" else 0.0,
        elapsed_seconds=round(test_run.duration or 0, 2),
        failure_categories=summary.get("failure_categories", {}),
        status=test_run.status,
    )


@router.post("/{batch_id}/stop")
async def stop_batch_run(batch_id: str, db: Session = Depends(get_db)):
    """停止批量执行任务"""
    if stop_batch(batch_id):
        return {"success": True, "message": f"批量任务 {batch_id} 已发送停止信号"}

    # 可能已完成
    service = BatchRunService(db)
    test_run = service.get_batch_run(batch_id)
    if not test_run:
        raise HTTPException(status_code=404, detail=f"批量任务 {batch_id} 不存在")
    if test_run.status in ("passed", "failed", "aborted"):
        return {"success": False, "message": f"任务已结束 (状态: {test_run.status})"}
    return {"success": False, "message": "任务不在执行中"}


@router.get("/{batch_id}/report")
async def get_batch_report(batch_id: str, db: Session = Depends(get_db)):
    """获取批量执行报告 JSON"""
    service = BatchRunService(db)
    try:
        report = service.generate_report(batch_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return report
