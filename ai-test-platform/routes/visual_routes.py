"""
Visual Testing REST API - 视觉基线管理 / 审核 / 趋势接口。

挂载点：/api/v2/visual

Endpoints:
    GET    /baselines                       列出所有基线
    GET    /baselines/{baseline_id}         单个基线详情
    POST   /baselines/{baseline_id}/approve 批准更新基线（用最近 current 或指定 run）
    POST   /baselines/{baseline_id}/config  更新阈值/算法/masks
    DELETE /baselines/{baseline_id}         删除基线
    GET    /pending-reviews                 待审核失败列表
    GET    /stats                           汇总统计

所有路径都经 services.visual_diff._safe_baseline_path 校验，杜绝路径穿越。
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from services.visual_baseline_service import (
    list_baselines, get_baseline_detail,
    approve_baseline, update_baseline_config, delete_baseline,
    list_pending_reviews, list_namespaces,
    bulk_approve, bulk_delete, bulk_update_config,
)
from services.visual_diff import list_versions, rollback_to_version
from backend.danger_guard import check_confirm

router = APIRouter(prefix="/api/v2/visual", tags=["视觉测试"])

# Phase 10A: 危险操作 confirm_text 映射表
# 调用方需在请求体提供 confirm=True 且 confirm_text=对应字符串
CONFIRM_DELETE_BASELINE = "DELETE_BASELINE"
CONFIRM_BULK_DELETE = "BULK_DELETE_BASELINES"
CONFIRM_ROLLBACK = "ROLLBACK_BASELINE"
CONFIRM_DELETE_DLQ = "DELETE_DEAD_LETTER"
CONFIRM_TEST_WEBHOOK = "TEST_WEBHOOK"


# ──────────────────────────── DTO ────────────────────────────
class ApproveBaselineRequest(BaseModel):
    source: str = Field("latest_current", description="latest_current | specific_run")
    run_id: Optional[str] = Field(None, description="source=specific_run 时使用")
    by: Optional[str] = Field("user", description="操作人")
    note: Optional[str] = Field("", description="批准备注")


class MaskItem(BaseModel):
    """
    Mask 描述：支持矩形或元素选择器两种类型。
      rect:     {"type":"rect", "x":,"y":,"w":,"h":}
      selector: {"type":"selector", "selector":".banner", "padding":4}
    旧请求体（无 type 的纯 x/y/w/h）也兼容（默认按 rect 处理）。
    """
    type: Optional[str] = Field("rect", description="rect | selector")
    # rect 字段
    x: int = 0
    y: int = 0
    w: int = 0
    h: int = 0
    # selector 字段
    selector: Optional[str] = Field(None, description="CSS / Playwright selector")
    padding: Optional[int] = Field(0, ge=0, le=200, description="bbox 外扩像素")


class UpdateConfigRequest(BaseModel):
    threshold: Optional[float] = Field(None, ge=0, le=1)
    algorithm: Optional[str] = Field(None, description="pixel | ssim")
    masks: Optional[List[MaskItem]] = None
    by: Optional[str] = "user"
    note: Optional[str] = ""


class DeleteBaselineRequest(BaseModel):
    delete_currents: bool = False
    delete_diffs: bool = False
    by: Optional[str] = "user"
    # Phase 10A: 危险操作确认
    confirm: bool = False
    confirm_text: str = ""


# ──────────────────────────── 列表 / 详情 / 命名空间 ────────────────────────────
@router.get("/baselines")
def api_list_baselines(
    case_id: Optional[str] = Query(None),
    name: Optional[str] = Query(None, description="名称模糊匹配"),
    env: Optional[str] = Query(None, description="过滤指定环境"),
    viewport: Optional[str] = Query(None, description="过滤指定视口（如 1920x1080）"),
    branch: Optional[str] = Query(None, description="过滤指定分支"),
    limit: int = Query(200, ge=1, le=1000),
):
    items = list_baselines(
        case_id=case_id, name=name,
        env=env, viewport=viewport, branch=branch,
        limit=limit,
    )
    return {"success": True, "total": len(items), "items": items}


@router.get("/namespaces")
def api_list_namespaces():
    """返回所有出现过的 env / viewport / branch 值，给前端筛选器用。"""
    return {"success": True, "namespaces": list_namespaces()}


@router.get("/baselines/{baseline_id}")
def api_baseline_detail(baseline_id: str):
    try:
        detail = get_baseline_detail(baseline_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"success": True, "baseline": detail}


# ──────────────────────────── 批准 / 更新 ────────────────────────────
@router.post("/baselines/{baseline_id}/approve")
def api_approve_baseline(baseline_id: str, body: ApproveBaselineRequest):
    try:
        result = approve_baseline(
            baseline_id,
            source=body.source,
            run_id=body.run_id,
            by=body.by or "user",
            note=body.note or "",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return result


@router.post("/baselines/{baseline_id}/config")
def api_update_baseline_config(baseline_id: str, body: UpdateConfigRequest):
    try:
        masks = [m.model_dump() for m in body.masks] if body.masks else None
        result = update_baseline_config(
            baseline_id,
            threshold=body.threshold,
            algorithm=body.algorithm,
            masks=masks,
            by=body.by or "user",
            note=body.note or "",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return result


# ──────────────────────────── 删除 ────────────────────────────
@router.delete("/baselines/{baseline_id}")
def api_delete_baseline(baseline_id: str, body: Optional[DeleteBaselineRequest] = Body(None)):
    body = body or DeleteBaselineRequest()
    # Phase 10A: 危险操作守卫
    check_confirm(CONFIRM_DELETE_BASELINE, body.confirm, body.confirm_text)
    try:
        result = delete_baseline(
            baseline_id,
            delete_currents=body.delete_currents,
            delete_diffs=body.delete_diffs,
            by=body.by or "user",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return result


# ──────────────────────────── 待审核 / 统计 ────────────────────────────
@router.get("/pending-reviews")
def api_pending_reviews(
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    items = list_pending_reviews(db, days=days, limit=limit)
    return {"success": True, "total": len(items), "items": items}


# ──────────────────────────── 批量操作 ────────────────────────────
class BulkApproveRequest(BaseModel):
    baseline_ids: List[str]
    source: str = "latest_current"
    by: Optional[str] = "user"
    note: Optional[str] = ""


class BulkDeleteRequest(BaseModel):
    baseline_ids: List[str]
    delete_currents: bool = False
    delete_diffs: bool = False
    by: Optional[str] = "user"
    # Phase 10A: 危险操作确认
    confirm: bool = False
    confirm_text: str = ""


class BulkUpdateConfigRequest(BaseModel):
    baseline_ids: List[str]
    threshold: Optional[float] = Field(None, ge=0, le=1)
    algorithm: Optional[str] = None
    masks: Optional[List[Dict[str, Any]]] = None
    by: Optional[str] = "user"
    note: Optional[str] = ""


@router.post("/bulk/approve")
def api_bulk_approve(body: BulkApproveRequest):
    if not body.baseline_ids:
        raise HTTPException(status_code=400, detail="baseline_ids 不能为空")
    if len(body.baseline_ids) > 200:
        raise HTTPException(status_code=400, detail="单次批量上限 200 个")
    return bulk_approve(body.baseline_ids, source=body.source,
                        by=body.by or "user", note=body.note or "")


@router.post("/bulk/delete")
def api_bulk_delete(body: BulkDeleteRequest):
    if not body.baseline_ids:
        raise HTTPException(status_code=400, detail="baseline_ids 不能为空")
    if len(body.baseline_ids) > 200:
        raise HTTPException(status_code=400, detail="单次批量上限 200 个")
    # Phase 10A: 危险操作守卫
    check_confirm(CONFIRM_BULK_DELETE, body.confirm, body.confirm_text)
    return bulk_delete(body.baseline_ids,
                       delete_currents=body.delete_currents,
                       delete_diffs=body.delete_diffs,
                       by=body.by or "user")


@router.post("/bulk/config")
def api_bulk_config(body: BulkUpdateConfigRequest):
    if not body.baseline_ids:
        raise HTTPException(status_code=400, detail="baseline_ids 不能为空")
    if len(body.baseline_ids) > 200:
        raise HTTPException(status_code=400, detail="单次批量上限 200 个")
    return bulk_update_config(
        body.baseline_ids,
        threshold=body.threshold, algorithm=body.algorithm, masks=body.masks,
        by=body.by or "user", note=body.note or "",
    )


# ──────────────────────────── 基线版本历史 / 回滚 ────────────────────────────
class RollbackRequest(BaseModel):
    version_id: str = Field(..., description="要回滚到的版本 id")
    by: Optional[str] = "user"
    note: Optional[str] = ""
    # Phase 10A: 危险操作确认
    confirm: bool = False
    confirm_text: str = ""


@router.get("/baselines/{baseline_id}/versions")
def api_list_versions(baseline_id: str):
    """返回该基线的版本历史（最新在最后），包含 file 字段可拼成 /visual/versions/{bid}/{file} 直接预览。"""
    try:
        items = list_versions(baseline_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    # 直接暴露相对挂载路径供前端预览
    for v in items:
        if v.get("file"):
            v["preview_url"] = f"/visual/versions/{baseline_id}/{v['file']}"
    return {"success": True, "baseline_id": baseline_id, "total": len(items), "versions": items}


@router.post("/baselines/{baseline_id}/rollback")
def api_rollback_baseline(baseline_id: str, body: RollbackRequest):
    # Phase 10A: 危险操作守卫
    check_confirm(CONFIRM_ROLLBACK, body.confirm, body.confirm_text)
    try:
        result = rollback_to_version(
            baseline_id, body.version_id,
            by=body.by or "user", note=body.note or "",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return result


# ──────────────────────────── Webhook 配置 / 测试 ────────────────────────────
@router.get("/webhook/config")
def api_webhook_config():
    """
    返回当前 webhook 运行时配置（不暴露 secret 明文，仅显示是否设置）。
    便于前端展示「已配置 / 未配置」。
    """
    import os as _os
    from services.visual_notifier import _load_subscriptions, DEFAULT_SUBSCRIBE_ALL_EXCEPT
    sub = _load_subscriptions()
    return {
        "success": True,
        "config": {
            "url_configured": bool(_os.getenv("VISUAL_WEBHOOK_URL")),
            "secret_configured": bool(_os.getenv("VISUAL_WEBHOOK_SECRET")),
            "timeout_seconds": float(_os.getenv("VISUAL_WEBHOOK_TIMEOUT", "5")),
            "subscriptions": (
                sorted(sub) if sub is not None
                else f"<default: all except {sorted(DEFAULT_SUBSCRIBE_ALL_EXCEPT)}>"
            ),
        },
    }


@router.get("/webhook/dead-letters")
def api_webhook_dlq_list(
    limit: int = Query(50, ge=1, le=500),
    include_resolved: bool = Query(False),
    event_type: Optional[str] = Query(None),
):
    """死信列表（最新在前），默认仅未解决项。"""
    from services import visual_webhook_dlq
    items = visual_webhook_dlq.list_recent(
        limit=limit, include_resolved=include_resolved, event_type=event_type,
    )
    return {"success": True, "total": len(items), "items": items,
            "stats": visual_webhook_dlq.stats()}


@router.post("/webhook/dead-letters/{dlq_id}/retry")
def api_webhook_dlq_retry(dlq_id: int):
    """从 UI 手动重发一条死信。成功后自动 resolved。"""
    from services.visual_notifier import retry_dead_letter
    result = retry_dead_letter(dlq_id)
    if result.get("status") == "not_found":
        raise HTTPException(status_code=404, detail="死信不存在")
    if result.get("status") == "no_url":
        raise HTTPException(status_code=400, detail=result.get("error") or "未配置 webhook URL")
    return result


class DeleteDLQRequest(BaseModel):
    confirm: bool = False
    confirm_text: str = ""


@router.delete("/webhook/dead-letters/{dlq_id}")
def api_webhook_dlq_delete(dlq_id: int, body: Optional[DeleteDLQRequest] = Body(None)):
    body = body or DeleteDLQRequest()
    # Phase 10A: 危险操作守卫
    check_confirm(CONFIRM_DELETE_DLQ, body.confirm, body.confirm_text)
    from services import visual_webhook_dlq
    ok = visual_webhook_dlq.delete(dlq_id)
    if not ok:
        raise HTTPException(status_code=404, detail="死信不存在")
    return {"success": True, "id": dlq_id}


class WebhookTestRequest(BaseModel):
    event: str = Field("visual.diff.failed", description="测试事件名")
    payload: Optional[Dict[str, Any]] = Field(None, description="自定义负载，默认 demo 数据")
    # Phase 10A: 危险操作确认（webhook test 会触发外部回调）
    confirm: bool = False
    confirm_text: str = ""


@router.post("/webhook/test")
def api_webhook_test(body: WebhookTestRequest):
    # Phase 10A: 危险操作守卫
    check_confirm(CONFIRM_TEST_WEBHOOK, body.confirm, body.confirm_text)
    """
    手动触发一条 webhook 事件，便于联调。
    若未配置 VISUAL_WEBHOOK_URL，返回 dry_run=True。
    """
    import os as _os
    from services.visual_notifier import send_event
    payload = body.payload or {
        "case_id": "demo_case",
        "name": "demo_screen",
        "diff_ratio": 0.123,
        "threshold": 0.05,
        "note": "手动测试",
    }
    send_event(body.event, payload)
    return {
        "success": True,
        "dispatched": bool(_os.getenv("VISUAL_WEBHOOK_URL")),
        "event": body.event,
        "dry_run": not bool(_os.getenv("VISUAL_WEBHOOK_URL")),
    }


@router.get("/stats")
def api_stats(db: Session = Depends(get_db)):
    """简单聚合：基线总数、配置 mask 数量、SSIM 占比、近 7 天待审核数。"""
    items = list_baselines(limit=10000)
    pending = list_pending_reviews(db, days=7, limit=500)
    total = len(items)
    with_masks = sum(1 for x in items if x.get("masks_count", 0) > 0)
    ssim_count = sum(1 for x in items if x.get("algorithm") == "ssim")
    approved = sum(1 for x in items if x.get("approve_count", 0) > 0)
    return {
        "success": True,
        "stats": {
            "total_baselines": total,
            "with_masks": with_masks,
            "ssim_count": ssim_count,
            "approved_count": approved,
            "pending_review_count": len(pending),
        },
    }
