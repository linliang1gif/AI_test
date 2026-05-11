"""
Visual Baseline Service - 视觉基线生命周期管理服务。

职责：
  - list_baselines        列出所有基线（含 metadata + DB 中最近一次 diff）
  - get_baseline_detail   单个基线详情（meta + 最近 N 次 current/diff 历史）
  - approve_baseline      批准更新：用某次 current 覆盖基线 + 写历史
  - update_baseline_config  更新阈值/算法/masks
  - delete_baseline       删除基线 + sidecar + 关联 current/diff（可选）
  - list_pending_reviews  扫描最近 runs 的 visual_results，找出 failed 待审核

所有路径均经 visual_diff._safe_baseline_path 校验，杜绝路径穿越。
"""
import os
import json
import shutil
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session

from services.visual_diff import (
    BASELINE_DIR, CURRENT_DIR, DIFF_DIR, META_DIR, VERSIONS_DIR,
    _safe_baseline_path, _safe_name, make_baseline_id,
    read_meta, write_meta, _now_iso, _init_meta,
    DEFAULT_THRESHOLD, DEFAULT_ENV, DEFAULT_VIEWPORT, DEFAULT_BRANCH,
    parse_baseline_id,
    meta_lock, update_meta_atomic,
    snapshot_version, list_versions, rollback_to_version, _versions_dir_for,
)

logger = logging.getLogger(__name__)


# ──────────────────────────── 公共辅助 ────────────────────────────
def _list_baseline_files() -> List[str]:
    """列出 baselines 目录下的 *.png（仅文件名）。"""
    if not os.path.isdir(BASELINE_DIR):
        return []
    return sorted([f for f in os.listdir(BASELINE_DIR) if f.endswith(".png")])


def _bid_from_filename(fname: str) -> str:
    return fname[:-4] if fname.endswith(".png") else fname


def _file_stat(path: str) -> Dict[str, Any]:
    try:
        st = os.stat(path)
        return {"size": st.st_size, "mtime": datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds")}
    except Exception:
        return {"size": 0, "mtime": ""}


def _list_recent_currents_for(bid: str, limit: int = 20) -> List[Dict[str, Any]]:
    """列出某 baseline_id 对应的最近 N 张 current 截图。"""
    if not os.path.isdir(CURRENT_DIR):
        return []
    prefix = bid + "_"
    items = []
    for f in os.listdir(CURRENT_DIR):
        if f.startswith(prefix) and f.endswith(".png"):
            full = os.path.join(CURRENT_DIR, f)
            st = _file_stat(full)
            run_part = f[len(prefix):-4]   # 去掉前缀和 .png
            items.append({
                "filename": f,
                "run_id": run_part,
                "size": st["size"],
                "mtime": st["mtime"],
            })
    items.sort(key=lambda x: x["mtime"], reverse=True)
    return items[:limit]


def _list_recent_diffs_for(bid: str, limit: int = 20) -> List[Dict[str, Any]]:
    if not os.path.isdir(DIFF_DIR):
        return []
    prefix = bid + "_"
    items = []
    for f in os.listdir(DIFF_DIR):
        if f.startswith(prefix) and f.endswith("_diff.png"):
            full = os.path.join(DIFF_DIR, f)
            st = _file_stat(full)
            mid = f[len(prefix):-len("_diff.png")]
            items.append({
                "filename": f,
                "run_id": mid,
                "size": st["size"],
                "mtime": st["mtime"],
            })
    items.sort(key=lambda x: x["mtime"], reverse=True)
    return items[:limit]


# ──────────────────────────── 列表 / 详情 ────────────────────────────
def list_baselines(
    case_id: Optional[str] = None,
    name: Optional[str] = None,
    env: Optional[str] = None,
    viewport: Optional[str] = None,
    branch: Optional[str] = None,
    limit: int = 200,
) -> List[Dict[str, Any]]:
    """
    返回所有基线的轻量摘要列表。
    可选过滤：case_id / name 子串 / env / viewport / branch（精确匹配，"default" 也是合法值）。
    """
    out: List[Dict[str, Any]] = []
    for fname in _list_baseline_files():
        bid = _bid_from_filename(fname)
        meta = read_meta(bid) or {}
        # 命名空间字段：优先 sidecar，其次从 baseline_id 解析（兼容旧基线）
        parsed = parse_baseline_id(bid)
        item_env = meta.get("env") or parsed["env"]
        item_vp = meta.get("viewport") or parsed["viewport"]
        item_branch = meta.get("branch") or parsed["branch"]

        c_id = meta.get("case_id", "")
        n = meta.get("name", "")
        if case_id and c_id and c_id != case_id:
            continue
        if name and n and name.lower() not in n.lower():
            continue
        if env and item_env != env:
            continue
        if viewport and item_vp != viewport:
            continue
        if branch and item_branch != branch:
            continue

        full = os.path.join(BASELINE_DIR, fname)
        st = _file_stat(full)
        out.append({
            "baseline_id": bid,
            "filename": fname,
            "case_id": c_id,
            "name": n,
            "env": item_env,
            "viewport": item_vp,
            "branch": item_branch,
            "threshold": meta.get("threshold", DEFAULT_THRESHOLD),
            "algorithm": meta.get("algorithm", "pixel"),
            "masks_count": len(meta.get("masks") or []),
            "approve_count": meta.get("approve_count", 0),
            "updated_at": meta.get("updated_at", st["mtime"]),
            "updated_by": meta.get("updated_by", "system"),
            "last_run_id": meta.get("last_run_id", ""),
            "size": st["size"],
            "has_sidecar": bool(meta),
        })
        if len(out) >= limit:
            break
    return out


def list_namespaces() -> Dict[str, List[str]]:
    """
    扫描所有基线，归类出现过的 env / viewport / branch 值，供前端下拉选择器用。
    """
    envs, vps, branches = set(), set(), set()
    for fname in _list_baseline_files():
        bid = _bid_from_filename(fname)
        meta = read_meta(bid) or {}
        parsed = parse_baseline_id(bid)
        envs.add(meta.get("env") or parsed["env"])
        vps.add(meta.get("viewport") or parsed["viewport"])
        branches.add(meta.get("branch") or parsed["branch"])
    return {
        "envs": sorted(envs),
        "viewports": sorted(vps),
        "branches": sorted(branches),
    }


def get_baseline_detail(bid: str) -> Dict[str, Any]:
    """
    返回单个基线的完整详情。
    包含：metadata、最近 current/diff 列表。
    """
    baseline_path = _safe_baseline_path(bid, ".png")
    if not os.path.exists(baseline_path):
        raise FileNotFoundError(f"基线不存在: {bid}")
    meta = read_meta(bid) or {}
    st = _file_stat(baseline_path)
    return {
        "baseline_id": bid,
        "exists": True,
        "size": st["size"],
        "mtime": st["mtime"],
        "metadata": meta,
        "recent_currents": _list_recent_currents_for(bid, 20),
        "recent_diffs": _list_recent_diffs_for(bid, 20),
    }


# ──────────────────────────── 批准更新 ────────────────────────────
def approve_baseline(
    bid: str,
    source: str,
    run_id: Optional[str] = None,
    by: str = "user",
    note: str = "",
) -> Dict[str, Any]:
    """
    将某次 current 截图批准为新基线。

    Args:
        bid:   baseline_id
        source: 'latest_current' | 'specific_run'
        run_id: 当 source='specific_run' 时指定
        by:    操作人
        note:  备注

    Returns:
        {success, new_baseline_size, history_entry, ...}
    """
    baseline_path = _safe_baseline_path(bid, ".png")
    if not os.path.exists(baseline_path):
        raise FileNotFoundError(f"基线不存在: {bid}")

    # 选 source
    if source == "specific_run" and run_id:
        safe_run = _safe_name(run_id)
        candidate = os.path.join(CURRENT_DIR, f"{bid}_{safe_run}.png")
        if not os.path.exists(candidate):
            raise FileNotFoundError(f"未找到 run_id={run_id} 的当前截图: {candidate}")
    elif source == "latest_current":
        recents = _list_recent_currents_for(bid, 1)
        if not recents:
            raise FileNotFoundError(f"未找到 {bid} 的任何 current 截图")
        candidate = os.path.join(CURRENT_DIR, recents[0]["filename"])
    else:
        raise ValueError(f"非法 source: {source!r}")

    # 备份路径（实际备份在锁内执行）
    backup_path = baseline_path + ".prev"

    # 整个 approve 流程加锁：覆盖基线 png + 备份 + sidecar 写入串行化，
    # 防止两个并发批准互相踩踏（一个写完前另一个又把 prev 复制掉）。
    with meta_lock(bid):
        prev_size = os.path.getsize(baseline_path)

        # 覆盖（拿锁后再做备份+复制）
        try:
            if os.path.exists(backup_path):
                os.remove(backup_path)
            shutil.copy2(baseline_path, backup_path)
        except Exception as e:
            logger.warning(f"旧基线备份失败 {bid}: {e}")

        shutil.copy2(candidate, baseline_path)
        new_size = os.path.getsize(baseline_path)

        # 更新 sidecar
        meta = read_meta(bid)
        if not meta:
            meta = _init_meta(bid, "", "", DEFAULT_THRESHOLD)
            meta["baseline_id"] = bid
        meta["updated_at"] = _now_iso()
        meta["updated_by"] = by or "user"
        meta["last_run_id"] = run_id or meta.get("last_run_id", "")
        meta["approve_count"] = int(meta.get("approve_count", 0)) + 1
        history_entry = {
            "event": "approved",
            "run_id": run_id or "",
            "by": by or "user",
            "at": _now_iso(),
            "note": note or "",
            "prev_size": prev_size,
            "new_size": new_size,
            "source": source,
        }
        meta.setdefault("history", []).append(history_entry)
        write_meta(bid, meta)
        # Phase 6: 批准后归档为一个新版本
        try:
            snapshot_version(bid, by=by or "user", source="approved",
                             from_run_id=run_id or "", note=note or "")
        except Exception as e:
            logger.warning(f"snapshot version (approved) 失败 {bid}: {e}")

    try:
        from services.visual_notifier import send_event
        send_event("visual.baseline.approved", {
            "baseline_id": bid,
            "by": by or "user",
            "run_id": run_id or "",
            "source": source,
            "prev_size": prev_size,
            "new_size": new_size,
            "approve_count": int(meta.get("approve_count", 0)),
            "note": note or "",
        })
    except Exception as _e:
        logger.warning("[P1] visual_notifier emit: %s", _e)

    return {
        "success": True,
        "baseline_id": bid,
        "prev_size": prev_size,
        "new_size": new_size,
        "history_entry": history_entry,
    }


def update_baseline_config(
    bid: str,
    threshold: Optional[float] = None,
    algorithm: Optional[str] = None,
    masks: Optional[List[Dict[str, int]]] = None,
    by: str = "user",
    note: str = "",
) -> Dict[str, Any]:
    """更新基线的对比配置（阈值 / 算法 / mask 区域）。"""
    baseline_path = _safe_baseline_path(bid, ".png")
    if not os.path.exists(baseline_path):
        raise FileNotFoundError(f"基线不存在: {bid}")

    # update_config 也加锁：read-modify-write 原子化
    with meta_lock(bid):
        meta = read_meta(bid) or _init_meta(bid, "", "", DEFAULT_THRESHOLD)
        result_meta = _apply_config_changes(meta, threshold, algorithm, masks, by, note)
        changed = result_meta.pop("_changed", [])
        write_meta(bid, result_meta)

    try:
        from services.visual_notifier import send_event
        send_event("visual.baseline.config_updated", {
            "baseline_id": bid,
            "by": by or "user",
            "changed": changed,
            "threshold": result_meta.get("threshold"),
            "algorithm": result_meta.get("algorithm"),
            "masks_count": len(result_meta.get("masks") or []),
            "note": note or "",
        })
    except Exception as _e:
        logger.warning("[P1] visual_notifier emit: %s", _e)

    return {"success": True, "baseline_id": bid, "changed": changed, "metadata": result_meta}


def _apply_config_changes(
    meta: Dict[str, Any],
    threshold: Optional[float],
    algorithm: Optional[str],
    masks: Optional[List[Dict[str, Any]]],
    by: str,
    note: str,
) -> Dict[str, Any]:
    """将配置变更应用到 meta 上（不写盘）。"""
    changed: List[str] = []
    if threshold is not None:
        if not (0 <= float(threshold) <= 1):
            raise ValueError("threshold 必须在 [0, 1] 区间")
        meta["threshold"] = round(float(threshold), 6)
        changed.append("threshold")
    if algorithm is not None:
        if algorithm not in ("pixel", "ssim"):
            raise ValueError("algorithm 必须是 'pixel' 或 'ssim'")
        meta["algorithm"] = algorithm
        changed.append("algorithm")
    if masks is not None:
        # 校验 + 规范化：支持 rect / selector 两种类型
        if not isinstance(masks, list):
            raise ValueError("masks 必须是数组")
        cleaned = []
        for m in masks:
            if not isinstance(m, dict):
                continue
            mtype = (m.get("type") or "rect").lower()
            if mtype == "selector":
                sel = (m.get("selector") or "").strip()
                if not sel:
                    continue
                # selector mask：bbox 由引擎在执行时填充；这里只存配置
                item = {
                    "type": "selector",
                    "selector": sel[:300],   # 限制长度
                    "padding": int(m.get("padding", 0) or 0),
                }
                cleaned.append(item)
            else:  # rect / unknown 都按 rect 处理
                cleaned.append({
                    "type": "rect",
                    "x": int(m.get("x", 0)),
                    "y": int(m.get("y", 0)),
                    "w": int(m.get("w", 0)),
                    "h": int(m.get("h", 0)),
                })
        meta["masks"] = cleaned
        changed.append(f"masks({len(cleaned)})")

    meta["updated_at"] = _now_iso()
    meta["updated_by"] = by or "user"
    meta.setdefault("history", []).append({
        "event": "config_updated",
        "by": by or "user",
        "at": _now_iso(),
        "note": note or "",
        "changed": changed,
        "threshold": meta.get("threshold"),
        "algorithm": meta.get("algorithm"),
        "masks_count": len(meta.get("masks") or []),
    })
    meta["_changed"] = changed
    return meta


# ──────────────────────────── 删除 ────────────────────────────
def delete_baseline(
    bid: str,
    delete_currents: bool = False,
    delete_diffs: bool = False,
    by: str = "user",
) -> Dict[str, Any]:
    """
    删除基线 + sidecar。可选连带删除 current / diff 历史。
    """
    baseline_path = _safe_baseline_path(bid, ".png")
    if not os.path.exists(baseline_path):
        raise FileNotFoundError(f"基线不存在: {bid}")

    removed = {"baseline": False, "meta": False, "currents": 0, "diffs": 0, "backup": False, "versions": 0}

    try:
        os.remove(baseline_path)
        removed["baseline"] = True
    except Exception as e:
        logger.warning(f"删除基线失败 {bid}: {e}")

    # 备份
    backup = baseline_path + ".prev"
    if os.path.exists(backup):
        try:
            os.remove(backup)
            removed["backup"] = True
        except Exception as _e:
            logger.exception("[P0] baseline data write/delete: %s", _e)

    # sidecar
    try:
        meta_path = _safe_baseline_path(bid, ".meta.json")
        if os.path.exists(meta_path):
            os.remove(meta_path)
            removed["meta"] = True
    except Exception as e:
        logger.warning(f"删除 sidecar 失败 {bid}: {e}")

    if delete_currents:
        prefix = bid + "_"
        for f in os.listdir(CURRENT_DIR) if os.path.isdir(CURRENT_DIR) else []:
            if f.startswith(prefix) and f.endswith(".png"):
                try:
                    os.remove(os.path.join(CURRENT_DIR, f))
                    removed["currents"] += 1
                except Exception as _e:
                    logger.exception("[P0] baseline data write/delete: %s", _e)

    if delete_diffs:
        prefix = bid + "_"
        for f in os.listdir(DIFF_DIR) if os.path.isdir(DIFF_DIR) else []:
            if f.startswith(prefix) and f.endswith("_diff.png"):
                try:
                    os.remove(os.path.join(DIFF_DIR, f))
                    removed["diffs"] += 1
                except Exception as _e:
                    logger.exception("[P0] baseline data write/delete: %s", _e)

    # Phase 6: 清理版本快照目录（无论 delete_currents/diffs，版本归当前 bid 私有）
    try:
        vdir = _versions_dir_for(bid)
        if os.path.isdir(vdir):
            for f in os.listdir(vdir):
                try:
                    os.remove(os.path.join(vdir, f))
                    removed["versions"] += 1
                except Exception as _e:
                    logger.exception("[P0] baseline data write/delete: %s", _e)
            try:
                os.rmdir(vdir)
            except OSError:
                pass
    except Exception as e:
        logger.warning(f"清理 versions 失败 {bid}: {e}")

    logger.info(f"删除基线 {bid} by={by} 结果={removed}")
    try:
        from services.visual_notifier import send_event
        send_event("visual.baseline.deleted", {
            "baseline_id": bid,
            "by": by or "user",
            "removed": removed,
        })
    except Exception as _e:
        logger.warning("[P1] visual_notifier emit: %s", _e)
    return {"success": True, "baseline_id": bid, "removed": removed}


# ──────────────────────────── 待审核扫描 ────────────────────────────
def list_pending_reviews(
    db: Session,
    days: int = 7,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    扫描最近 N 天的 RunCase.response_snapshot.visual_results，
    返回 status='failed' 且尚未被批准过的视觉结果（按 baseline_id 去重，仅取每个 bid 最近一次）。
    """
    from database.models import RunCase
    cutoff = datetime.now() - timedelta(days=max(1, days))

    rows = (
        db.query(RunCase)
        .filter(RunCase.start_time >= cutoff)
        .order_by(RunCase.start_time.desc())
        .limit(2000)  # 上限，防全表扫
        .all()
    )

    seen_bids: Dict[str, Dict[str, Any]] = {}
    for rc in rows:
        resp = rc.response_snapshot or {}
        if isinstance(resp, str):
            try:
                resp = json.loads(resp)
            except Exception:
                continue
        for vr in (resp.get("visual_results") or []):
            if vr.get("status") != "failed":
                continue
            bid = vr.get("baseline_id") or ""
            if not bid:
                # 兼容老数据：尝试从 baseline_path 推断
                bp = vr.get("baseline_path") or ""
                if bp:
                    bid = _bid_from_filename(os.path.basename(bp))
            if not bid:
                continue
            # 已批准（且批准时间晚于此 run）则跳过
            meta = read_meta(bid) or {}
            approved_after = False
            for h in meta.get("history", []):
                if h.get("event") == "approved" and h.get("at", "") > (rc.start_time.isoformat() if rc.start_time else ""):
                    approved_after = True
                    break
            if approved_after:
                continue
            if bid in seen_bids:
                continue
            parsed = parse_baseline_id(bid)
            seen_bids[bid] = {
                "baseline_id": bid,
                "case_id": meta.get("case_id", ""),
                "name": meta.get("name", vr.get("name", "")),
                "env": vr.get("env") or meta.get("env") or parsed["env"],
                "viewport": vr.get("viewport") or meta.get("viewport") or parsed["viewport"],
                "branch": vr.get("branch") or meta.get("branch") or parsed["branch"],
                "run_id": rc.run_id,
                "run_case_id": rc.id,
                "test_case_id": rc.test_case_id,
                "diff_ratio": vr.get("diff_ratio", 0),
                "threshold": vr.get("threshold", DEFAULT_THRESHOLD),
                "algorithm": vr.get("algorithm", meta.get("algorithm", "pixel")),
                "diff_path": os.path.basename(vr.get("diff_path") or ""),
                "current_path": os.path.basename(vr.get("current_path") or ""),
                "started_at": rc.start_time.isoformat() if rc.start_time else "",
                "error_message": vr.get("error_message", ""),
            }
            if len(seen_bids) >= limit:
                break
        if len(seen_bids) >= limit:
            break
    return list(seen_bids.values())


# ──────────────────────────── 批量操作 ────────────────────────────
def bulk_approve(
    baseline_ids: List[str],
    source: str = "latest_current",
    by: str = "user",
    note: str = "",
) -> Dict[str, Any]:
    """
    批量批准多个基线（每个用各自最近一次 current 覆盖）。
    返回 {success_count, fail_count, results: [{bid, ok, error?}, ...]}
    """
    results = []
    ok_n, fail_n = 0, 0
    for bid in baseline_ids:
        try:
            r = approve_baseline(bid, source=source, by=by, note=note or "批量批准")
            results.append({"baseline_id": bid, "ok": True, "result": r})
            ok_n += 1
        except Exception as e:
            results.append({"baseline_id": bid, "ok": False, "error": str(e)[:200]})
            fail_n += 1
    return {"success_count": ok_n, "fail_count": fail_n, "total": len(baseline_ids), "results": results}


def bulk_delete(
    baseline_ids: List[str],
    delete_currents: bool = False,
    delete_diffs: bool = False,
    by: str = "user",
) -> Dict[str, Any]:
    """批量删除基线。"""
    results = []
    ok_n, fail_n = 0, 0
    for bid in baseline_ids:
        try:
            r = delete_baseline(bid, delete_currents=delete_currents, delete_diffs=delete_diffs, by=by)
            results.append({"baseline_id": bid, "ok": True, "result": r})
            ok_n += 1
        except Exception as e:
            results.append({"baseline_id": bid, "ok": False, "error": str(e)[:200]})
            fail_n += 1
    return {"success_count": ok_n, "fail_count": fail_n, "total": len(baseline_ids), "results": results}


def bulk_update_config(
    baseline_ids: List[str],
    threshold: Optional[float] = None,
    algorithm: Optional[str] = None,
    masks: Optional[List[Dict[str, Any]]] = None,
    by: str = "user",
    note: str = "",
) -> Dict[str, Any]:
    """批量更新阈值/算法/masks。任意为 None 的字段不变。"""
    results = []
    ok_n, fail_n = 0, 0
    for bid in baseline_ids:
        try:
            r = update_baseline_config(
                bid, threshold=threshold, algorithm=algorithm, masks=masks,
                by=by, note=note or "批量配置更新",
            )
            results.append({"baseline_id": bid, "ok": True, "result": r})
            ok_n += 1
        except Exception as e:
            results.append({"baseline_id": bid, "ok": False, "error": str(e)[:200]})
            fail_n += 1
    return {"success_count": ok_n, "fail_count": fail_n, "total": len(baseline_ids), "results": results}
