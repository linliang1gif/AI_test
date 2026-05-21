# -*- coding: utf-8 -*-
"""
P3-3B: 缺陷闭环 MVP 路由
9 个 API 端点: CRUD + 状态流转 + 从 run_case/failure_analysis 创建 + 重复检测 + 关联 run
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
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

    @field_validator("run_case_id", mode="before")
    @classmethod
    def normalize_run_case_id(cls, v):
        return None if v is None else str(v)


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

    @field_validator("run_case_id", mode="before")
    @classmethod
    def normalize_run_case_id(cls, v):
        return "" if v is None else str(v)


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

    @field_validator("run_case_id", mode="before")
    @classmethod
    def normalize_run_case_id(cls, v):
        return None if v is None else str(v)


class LinkRunRequest(BaseModel):
    run_id: str
    by: Optional[str] = "system"


class PushToTapdRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    module: Optional[str] = None
    severity: Optional[str] = None
    priority: Optional[str] = None
    reporter: Optional[str] = None


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


@router.post("/{defect_id}/push-to-tapd")
def api_push_defect_to_tapd(defect_id: int, req: PushToTapdRequest, db: Session = Depends(get_db)):
    from database.models import Defect, DefectEvent
    from services.tapd_service import load_tapd_config, push_bug_to_tapd

    config = load_tapd_config()
    if not config.get("workspace_id"):
        raise HTTPException(status_code=400, detail="请先配置 TAPD 信息")

    defect = db.query(Defect).filter(Defect.id == defect_id).first()
    if not defect:
        raise HTTPException(status_code=404, detail=f"Defect {defect_id} not found")

    evidence = defect.evidence_json or {}
    if evidence.get("tapd_bug_id"):
        return {
            "success": True,
            "already_pushed": True,
            "bug_id": evidence.get("tapd_bug_id"),
            "url": evidence.get("tapd_url", ""),
            "message": "该缺陷已推送过 TAPD",
        }

    description_parts = []
    if req.description or defect.description:
        description_parts.append(req.description or defect.description or "")
    if defect.failure_category:
        description_parts.append(f"失败分类：{defect.failure_category}")
    if defect.case_id:
        description_parts.append(f"用例ID：{defect.case_id}")
    if defect.run_id:
        description_parts.append(f"执行ID：{defect.run_id}")
    if defect.run_case_id:
        description_parts.append(f"执行用例ID：{defect.run_case_id}")
    if defect.trace_path:
        description_parts.append(f"Trace：{defect.trace_path}")
    if defect.screenshot_path:
        description_parts.append(f"截图：{defect.screenshot_path}")

    result = push_bug_to_tapd(
        config=config,
        title=req.title or defect.title,
        description="\n".join(description_parts) or defect.title,
        severity=req.severity or defect.severity or "major",
        priority=req.priority or defect.priority or "P2",
        module=req.module if req.module is not None else (defect.module or ""),
        reporter=req.reporter or config.get("default_reporter", ""),
    )

    if result.get("success"):
        evidence.update({
            "tapd_bug_id": result.get("bug_id"),
            "tapd_url": result.get("url"),
            "tapd_pushed_at": datetime.now().isoformat(),
        })
        defect.evidence_json = evidence
        event = DefectEvent(
            defect_id=defect.id,
            event_type="tapd_push",
            comment=f"推送到 TAPD: {result.get('bug_id')}",
            evidence_json={"tapd_bug_id": result.get("bug_id"), "tapd_url": result.get("url")},
            created_by="system",
        )
        db.add(event)
        db.commit()
        db.refresh(defect)

    return result


# ── TAPD → 本地缺陷状态机映射 ──
TAPD_TO_LOCAL_STATUS = {
    "in_progress": "confirmed",
    "resolved": "fixed",
    "verified": "verified",
    "closed": "closed",
    "reopened": "reopened",
    "rejected": "rejected",
    # new / postponed: 不动
}


def _shortest_transition_path(current: str, target: str) -> List[str]:
    """BFS 计算从 current 到 target 经过状态机的最短路径（不含 current 自己）

    返回中间状态序列（含 target）。无法到达返回空列表。
    """
    from services.defect_service import ALLOWED_TRANSITIONS
    if current == target:
        return []
    from collections import deque
    visited = {current}
    queue = deque([(current, [])])
    while queue:
        node, path = queue.popleft()
        for nxt in ALLOWED_TRANSITIONS.get(node, set()):
            if nxt in visited:
                continue
            new_path = path + [nxt]
            if nxt == target:
                return new_path
            visited.add(nxt)
            queue.append((nxt, new_path))
    return []


def _do_sync_one_defect(db, defect, force_advance: bool = True) -> dict:
    """单条缺陷的 TAPD 反向同步逻辑（内部复用）"""
    from database.models import DefectEvent
    from services.tapd_service import load_tapd_config, fetch_tapd_bug_status

    evidence = defect.evidence_json or {}
    bug_id = evidence.get("tapd_bug_id")
    if not bug_id:
        return {"success": False, "code": "NOT_PUSHED", "message": "该缺陷未推送过 TAPD"}

    config = load_tapd_config()
    if not config.get("workspace_id"):
        return {"success": False, "code": "NO_TAPD_CONFIG", "message": "请先配置 TAPD"}

    fetch = fetch_tapd_bug_status(config, bug_id)
    if not fetch.get("success"):
        return {
            "success": False,
            "code": fetch.get("code", "TAPD_API_ERROR"),
            "message": fetch.get("message", "TAPD 查询失败"),
        }

    tapd_status = fetch.get("tapd_status") or "unknown"
    tapd_status_name = fetch.get("tapd_status_name") or "未知"

    # 写回最新 TAPD 状态到 evidence
    evidence.update({
        "tapd_status": tapd_status,
        "tapd_status_name": tapd_status_name,
        "tapd_last_sync_at": datetime.now().isoformat(),
    })
    if fetch.get("tapd_modified"):
        evidence["tapd_modified"] = fetch["tapd_modified"]
    defect.evidence_json = evidence

    # 计算目标本地状态
    target_local = TAPD_TO_LOCAL_STATUS.get(tapd_status)
    advanced_steps = []
    skipped_reason = None

    if not target_local:
        skipped_reason = f"TAPD 状态 {tapd_status} 无映射"
    elif defect.status == target_local:
        skipped_reason = "本地状态与目标一致"
    elif force_advance:
        path = _shortest_transition_path(defect.status, target_local)
        if not path:
            skipped_reason = f"状态机不可达: {defect.status} → {target_local}"
        else:
            for nxt in path:
                from_status = defect.status
                defect.status = nxt
                if nxt == "closed":
                    defect.closed_at = datetime.now()
                advanced_steps.append({"from": from_status, "to": nxt})
                ev = DefectEvent(
                    defect_id=defect.id,
                    event_type="tapd_sync",
                    from_status=from_status,
                    to_status=nxt,
                    comment=f"TAPD 联动: {tapd_status_name}",
                    evidence_json={"tapd_status": tapd_status, "tapd_bug_id": bug_id},
                    created_by="system",
                )
                db.add(ev)

    # 即便没推进也记一次同步事件，方便审计
    if not advanced_steps:
        ev = DefectEvent(
            defect_id=defect.id,
            event_type="tapd_sync_check",
            comment=f"TAPD 状态: {tapd_status_name}" + (f" ({skipped_reason})" if skipped_reason else ""),
            evidence_json={"tapd_status": tapd_status, "tapd_bug_id": bug_id, "skipped": skipped_reason},
            created_by="system",
        )
        db.add(ev)

    db.commit()
    db.refresh(defect)

    return {
        "success": True,
        "defect_id": defect.id,
        "tapd_bug_id": bug_id,
        "tapd_status": tapd_status,
        "tapd_status_name": tapd_status_name,
        "local_status": defect.status,
        "advanced_steps": advanced_steps,
        "skipped_reason": skipped_reason,
    }


# ── 12. POST /api/v2/defects/{defect_id}/sync-tapd-status — 单条同步 ──
@router.post("/{defect_id}/sync-tapd-status")
def api_sync_defect_tapd_status(defect_id: int, db: Session = Depends(get_db)):
    """从 TAPD 拉取最新 Bug 状态并联动本地缺陷状态机"""
    from database.models import Defect
    defect = db.query(Defect).filter(Defect.id == defect_id).first()
    if not defect:
        raise HTTPException(status_code=404, detail=f"Defect {defect_id} not found")

    return _do_sync_one_defect(db, defect, force_advance=True)


# ── 13. POST /api/v2/defects/sync-tapd-status-batch — 批量同步 ──
class BatchSyncTapdRequest(BaseModel):
    defect_ids: Optional[List[int]] = None  # 指定 ID；为空则扫描所有已推送的缺陷
    project_id: Optional[int] = None        # 缩小批量范围
    force_advance: bool = True


@router.post("/sync-tapd-status-batch")
def api_sync_defects_tapd_status_batch(req: BatchSyncTapdRequest, db: Session = Depends(get_db)):
    """批量同步多条已推送 TAPD 的缺陷状态"""
    from database.models import Defect

    q = db.query(Defect)
    if req.defect_ids:
        q = q.filter(Defect.id.in_(req.defect_ids))
    if req.project_id is not None:
        q = q.filter(Defect.project_id == req.project_id)

    targets = q.all()
    pushed_only = [d for d in targets if (d.evidence_json or {}).get("tapd_bug_id")]

    results = []
    advanced_count = 0
    failed_count = 0
    for d in pushed_only:
        try:
            r = _do_sync_one_defect(db, d, force_advance=req.force_advance)
        except Exception as exc:
            r = {"success": False, "defect_id": d.id, "code": "EXCEPTION", "message": str(exc)}
        results.append(r)
        if r.get("success"):
            if r.get("advanced_steps"):
                advanced_count += 1
        else:
            failed_count += 1

    return {
        "success": True,
        "total": len(pushed_only),
        "advanced": advanced_count,
        "failed": failed_count,
        "no_tapd_link": len(targets) - len(pushed_only),
        "results": results,
    }


# ── 10. GET /api/v2/defects/summary/for-gate — 质量门禁缺陷摘要 ──
@router.get("/summary/for-gate")
def api_defect_summary(
    run_id: Optional[str] = Query(None),
    case_ids: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    cids = case_ids.split(",") if case_ids else None
    return get_defect_summary_for_gate(db, case_ids=cids, run_id=run_id)
