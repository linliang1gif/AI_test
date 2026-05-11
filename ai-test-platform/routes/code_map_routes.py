"""
AI Dev Studio Phase 7 — CodeMap 路由
代码结构扫描 + 增强影响文件分析
"""

import os
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from database.session import get_db
from sqlalchemy.orm import Session
from services.code_map_service import CodeMapService

router = APIRouter(prefix="/api/v2/dev-studio/code-map", tags=["CodeMap"])

# ── 默认项目根目录 ──
_DEFAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class ScanRequest(BaseModel):
    project_root: Optional[str] = None
    dev_task_id: Optional[str] = None


class FileImpactV2Request(BaseModel):
    snapshot_id: str


# ── 扫描项目 ────────────────────────────────────────────────

@router.post("/scan")
def scan_project(req: ScanRequest = ScanRequest(), db: Session = Depends(get_db)):
    root = req.project_root or _DEFAULT_ROOT
    result = CodeMapService.scan_project(db, root, dev_task_id=req.dev_task_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ── 查询 Snapshot ────────────────────────────────────────────

@router.get("/snapshots")
def list_snapshots(
    dev_task_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    return {"snapshots": CodeMapService.list_snapshots(db, dev_task_id)}


@router.get("/snapshots/{snapshot_id}")
def get_snapshot(snapshot_id: str, db: Session = Depends(get_db)):
    result = CodeMapService.get_snapshot(db, snapshot_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Snapshot 不存在: {snapshot_id}")
    return result


@router.get("/snapshots/{snapshot_id}/files")
def get_snapshot_files(
    snapshot_id: str,
    category: Optional[str] = Query(None),
    file_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    result = CodeMapService.get_snapshot_files(db, snapshot_id, category=category, file_type=file_type)
    return {"snapshot_id": snapshot_id, "files": result, "count": len(result)}


# ── 增强影响文件分析 ────────────────────────────────────────

@router.post("/tasks/{dev_task_id}/file-impact-v2")
def generate_file_impact_v2(
    dev_task_id: str,
    req: FileImpactV2Request,
    db: Session = Depends(get_db),
):
    result = CodeMapService.generate_file_impact_v2(db, dev_task_id, req.snapshot_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"DevTask 不存在: {dev_task_id}")
    if isinstance(result, dict) and result.get("_not_found") == "snapshot":
        raise HTTPException(status_code=404, detail=f"Snapshot 不存在: {req.snapshot_id}")
    return result
