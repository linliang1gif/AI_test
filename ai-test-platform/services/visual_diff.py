"""
Visual Regression - 工程级视觉回归服务。

Directories:
  data/artifacts/visual/baselines/    - 基线图（被比对的目标）
  data/artifacts/visual/current/      - 每次执行的当前截图
  data/artifacts/visual/diff/         - 差异图
  data/artifacts/visual/meta/         - 基线 sidecar 元数据（.meta.json）

Features:
  - 像素级 diff（默认）+ SSIM 结构相似度（可选，需 scikit-image）
  - 区域屏蔽（mask）：忽略动态时间戳/广告/头像等区域
  - 基线元数据 sidecar：记录 mask、阈值、批准历史、最后更新人/时间
  - 路径穿越防御：所有 baseline_id 必须经过 _safe_baseline_path 校验
"""
import os
import re
import json
import time
import logging
import contextlib
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Callable

logger = logging.getLogger(__name__)

BASE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "artifacts", "visual",
)
BASELINE_DIR = os.path.join(BASE_DIR, "baselines")
CURRENT_DIR = os.path.join(BASE_DIR, "current")
DIFF_DIR = os.path.join(BASE_DIR, "diff")
META_DIR = os.path.join(BASE_DIR, "meta")
VERSIONS_DIR = os.path.join(BASE_DIR, "versions")   # Phase 6: 历史版本物理副本
DEFAULT_THRESHOLD = 0.05

# Phase 6: 默认保留最近 N 个版本（可由环境变量覆盖，范围 [1, 50]）
def _keep_versions() -> int:
    try:
        v = int(os.getenv("VISUAL_KEEP_VERSIONS", "5"))
    except ValueError:
        v = 5
    return max(1, min(50, v))

# baseline_id 字符集：
#   字母 / 数字 / _ / . / - / 中文 / @（命名空间分隔符）
#   不允许：/ \ .. : ; | * ? " < > 等所有路径敏感字符
_SAFE_BASELINE_ID_RE = re.compile(r"^[A-Za-z0-9_.\-@\u4e00-\u9fff]+$")

# 命名空间默认值
DEFAULT_ENV = "default"
DEFAULT_VIEWPORT = "default"   # 也接受 "{w}x{h}" 格式如 "1920x1080"
DEFAULT_BRANCH = "default"

# 命名空间分隔符（不可与正常字符冲突）
NS_SEP = "@"


@dataclass
class VisualResult:
    type: str = "screenshot_match"
    name: str = ""
    status: str = "pending"
    baseline_created: bool = False
    baseline_path: str = ""
    current_path: str = ""
    diff_path: str = ""
    diff_ratio: float = 0.0
    threshold: float = DEFAULT_THRESHOLD
    error_message: str = ""
    reason: str = ""
    algorithm: str = "pixel"        # pixel | ssim
    masks_applied: int = 0          # 屏蔽了多少个区域
    baseline_id: str = ""           # 标准 baseline_id，便于前端定位
    env: str = DEFAULT_ENV          # 命名空间：环境
    viewport: str = DEFAULT_VIEWPORT  # 命名空间：视口
    branch: str = DEFAULT_BRANCH    # 命名空间：分支


def _ensure_dirs():
    for d in (BASELINE_DIR, CURRENT_DIR, DIFF_DIR, META_DIR, VERSIONS_DIR):
        os.makedirs(d, exist_ok=True)


def _safe_name(name: str) -> str:
    """清洗用户提供的 name，防止路径穿越。"""
    if not name:
        return "default"
    return name.replace("/", "_").replace("\\", "_").replace("..", "_").strip()


def _norm_ns(value: str, default: str) -> str:
    """命名空间值标准化：清洗 + 默认回退。"""
    if not value:
        return default
    v = str(value).strip()
    if not v:
        return default
    # 复用 _safe_name 的清洗规则（去 / \ ..），再去掉 @（命名空间分隔符）
    v = _safe_name(v).replace(NS_SEP, "_")
    return v or default


def normalize_viewport(viewport) -> str:
    """
    视口标准化：
      - 接受 "1920x1080" / (1920, 1080) / {"width":1920,"height":1080} / None
      - 返回 "1920x1080" 或 "default"
    """
    if not viewport:
        return DEFAULT_VIEWPORT
    if isinstance(viewport, str):
        s = viewport.strip().lower()
        if s in ("", "default"):
            return DEFAULT_VIEWPORT
        # 验证格式
        if re.match(r"^\d+x\d+$", s):
            return s
        return DEFAULT_VIEWPORT
    if isinstance(viewport, (list, tuple)) and len(viewport) == 2:
        try:
            return f"{int(viewport[0])}x{int(viewport[1])}"
        except Exception:
            return DEFAULT_VIEWPORT
    if isinstance(viewport, dict):
        try:
            w = int(viewport.get("width") or viewport.get("w") or 0)
            h = int(viewport.get("height") or viewport.get("h") or 0)
            if w and h:
                return f"{w}x{h}"
        except Exception as _e:
            logger.debug("[P2] viewport parse: %s", _e)
    return DEFAULT_VIEWPORT


def make_baseline_id(case_id: str, name: str,
                     env: Optional[str] = None,
                     viewport=None,
                     branch: Optional[str] = None) -> str:
    """
    标准 baseline_id 拼接：

      默认值情况 → 仅 {case_id}_{name}（向后兼容旧基线）
      非默认值   → {case_id}_{name}@env@viewport@branch（按需拼接，省略默认段）

    举例：
      make_baseline_id("tc1", "home")                                  → "tc1_home"
      make_baseline_id("tc1", "home", env="prod")                      → "tc1_home@prod"
      make_baseline_id("tc1", "home", env="prod", viewport=(375, 667)) → "tc1_home@prod@375x667"
      make_baseline_id("tc1", "home", branch="feat-x")                 → "tc1_home@default@default@feat-x"

    NS 段从前往后省略：如果 env=default 但 branch=非默认，则填默认占位。
    """
    base = f"{case_id}_{_safe_name(name)}"
    e = _norm_ns(env, DEFAULT_ENV)
    v = normalize_viewport(viewport)
    b = _norm_ns(branch, DEFAULT_BRANCH)
    # 全默认 → 不加后缀
    if e == DEFAULT_ENV and v == DEFAULT_VIEWPORT and b == DEFAULT_BRANCH:
        return base
    # 否则按 env / viewport / branch 顺序补齐到最后一个非默认段
    parts = [e, v, b]
    last_nondefault = max(
        (i for i, val in enumerate(parts)
         if val != (DEFAULT_ENV if i == 0 else DEFAULT_VIEWPORT if i == 1 else DEFAULT_BRANCH)),
        default=-1,
    )
    return base + "".join(NS_SEP + parts[i] for i in range(last_nondefault + 1))


def parse_baseline_id(bid: str) -> Dict[str, str]:
    """
    解析 baseline_id 还原各命名空间字段。
    无 NS_SEP → 全 default。
    """
    if NS_SEP not in bid:
        return {"core": bid, "env": DEFAULT_ENV, "viewport": DEFAULT_VIEWPORT, "branch": DEFAULT_BRANCH}
    head, *tail = bid.split(NS_SEP)
    e = tail[0] if len(tail) > 0 and tail[0] else DEFAULT_ENV
    v = tail[1] if len(tail) > 1 and tail[1] else DEFAULT_VIEWPORT
    b = tail[2] if len(tail) > 2 and tail[2] else DEFAULT_BRANCH
    return {"core": head, "env": e, "viewport": v, "branch": b}


def _safe_baseline_path(bid: str, suffix: str = ".png") -> str:
    """
    路径穿越防御：根据 baseline_id 拼接安全的基线/元数据路径。
    bid 必须只含 字母/数字/_/./-/中文。
    suffix ∈ {".png", ".meta.json"}
    """
    if not bid or not _SAFE_BASELINE_ID_RE.match(bid) or ".." in bid:
        raise ValueError(f"非法 baseline_id: {bid!r}")
    if suffix == ".png":
        path = os.path.join(BASELINE_DIR, bid + ".png")
        root = BASELINE_DIR
    elif suffix == ".meta.json":
        path = os.path.join(META_DIR, bid + ".meta.json")
        root = META_DIR
    else:
        raise ValueError(f"不支持的 suffix: {suffix!r}")
    abs_root = os.path.abspath(root)
    abs_path = os.path.abspath(path)
    if not abs_path.startswith(abs_root + os.sep) and abs_path != abs_root:
        raise ValueError(f"路径穿越拦截: {bid!r}")
    return path


def _resolve_mask_rect(m: Dict[str, Any]) -> Optional[Dict[str, int]]:
    """
    把任意 mask 描述统一为 {x, y, w, h}（已 resolve 的）。

    支持的输入格式：
      1. {"type":"rect", "x":, "y":, "w":, "h":}          → 直接返回
      2. {"x":, "y":, "w":, "h":}（旧格式）                 → 等价于 type=rect
      3. {"type":"selector", "bbox":{"x":,"y":,"w":,"h":}} → 用 bbox（已被 engine 展开）
      4. {"type":"selector", "selector":"..."}              → 未展开 → 返回 None（无法应用）

    返回 None 时调用方应跳过该 mask。
    """
    if not isinstance(m, dict):
        return None
    mtype = (m.get("type") or "rect").lower()
    if mtype == "rect" or mtype == "rect_resolved":
        try:
            return {
                "x": int(m.get("x", 0)),
                "y": int(m.get("y", 0)),
                "w": int(m.get("w", 0)),
                "h": int(m.get("h", 0)),
            }
        except Exception:
            return None
    if mtype == "selector":
        bbox = m.get("bbox")
        if not bbox:
            return None
        padding = int(m.get("padding", 0) or 0)
        try:
            x = int(bbox.get("x", 0)) - padding
            y = int(bbox.get("y", 0)) - padding
            w = int(bbox.get("w", 0)) + 2 * padding
            h = int(bbox.get("h", 0)) + 2 * padding
            return {"x": x, "y": y, "w": w, "h": h}
        except Exception:
            return None
    return None


def _apply_masks(img, masks: List[Dict[str, Any]]):
    """
    在图像上将 mask 区域填充为黑色，使该区域不参与 diff。

    masks 元素支持：
      矩形：       {"type":"rect"|缺省, "x":, "y":, "w":, "h":}
      已展开选择器：{"type":"selector", "selector":"...", "bbox":{x,y,w,h}, "padding":4}
      未展开选择器：{"type":"selector", "selector":"..."}（缺 bbox → 跳过 + warning）
    """
    if not masks:
        return img, 0
    from PIL import ImageDraw
    img2 = img.copy()
    draw = ImageDraw.Draw(img2)
    applied = 0
    skipped = 0
    w_max, h_max = img2.size
    for m in masks:
        rect = _resolve_mask_rect(m)
        if rect is None:
            skipped += 1
            sel = m.get("selector") if isinstance(m, dict) else None
            if sel:
                logger.warning(f"selector mask 缺 bbox 已跳过: {sel}")
            continue
        try:
            x = max(0, rect["x"])
            y = max(0, rect["y"])
            w = rect["w"]
            h = rect["h"]
            if w <= 0 or h <= 0:
                skipped += 1
                continue
            x2 = min(w_max, x + w)
            y2 = min(h_max, y + h)
            if x2 <= x or y2 <= y:
                skipped += 1
                continue
            draw.rectangle([x, y, x2, y2], fill=(0, 0, 0))
            applied += 1
        except Exception as e:
            skipped += 1
            logger.warning(f"mask 应用失败 {m}: {e}")
    if skipped:
        logger.info(f"mask 应用: {applied} 成功, {skipped} 跳过")
    return img2, applied


def _pixel_diff(
    baseline_path: str,
    current_path: str,
    diff_path: str,
    masks: Optional[List[Dict[str, int]]] = None,
) -> Tuple[float, int]:
    """返回 (diff_ratio, masks_applied)。生成 diff_path 图像。"""
    from PIL import Image, ImageChops
    base_img = Image.open(baseline_path).convert("RGB")
    curr_img = Image.open(current_path).convert("RGB")
    if base_img.size != curr_img.size:
        curr_img = curr_img.resize(base_img.size, Image.LANCZOS)
    masks_applied = 0
    if masks:
        base_img, n1 = _apply_masks(base_img, masks)
        curr_img, _ = _apply_masks(curr_img, masks)
        masks_applied = n1
    diff_img = ImageChops.difference(base_img, curr_img)
    diff_img.save(diff_path)
    pixels = list(diff_img.getdata())
    total = len(pixels)
    if total == 0:
        return 0.0, masks_applied
    changed = sum(1 for r, g, b in pixels if r + g + b > 30)
    return round(changed / total, 6), masks_applied


def _ssim_diff(
    baseline_path: str,
    current_path: str,
    diff_path: str,
    masks: Optional[List[Dict[str, int]]] = None,
) -> Tuple[float, int]:
    """
    SSIM 结构相似度对比。返回 (1 - ssim_score) 作为 diff_ratio。
    需要 scikit-image。失败时回退到像素 diff。
    """
    try:
        from skimage.metrics import structural_similarity as ssim
        import numpy as np
        from PIL import Image
    except ImportError:
        logger.warning("scikit-image 未安装，回退到 pixel diff")
        return _pixel_diff(baseline_path, current_path, diff_path, masks)

    base_img = Image.open(baseline_path).convert("RGB")
    curr_img = Image.open(current_path).convert("RGB")
    if base_img.size != curr_img.size:
        curr_img = curr_img.resize(base_img.size, Image.LANCZOS)
    masks_applied = 0
    if masks:
        base_img, n1 = _apply_masks(base_img, masks)
        curr_img, _ = _apply_masks(curr_img, masks)
        masks_applied = n1
    base_arr = np.asarray(base_img.convert("L"))
    curr_arr = np.asarray(curr_img.convert("L"))
    score, diff_arr = ssim(base_arr, curr_arr, full=True)
    diff_arr = ((1 - diff_arr) * 255).astype("uint8")
    Image.fromarray(diff_arr).save(diff_path)
    return round(1.0 - float(score), 6), masks_applied


# ──────────────── 文件锁 / 原子写 ────────────────
# 跨平台文件锁：用 O_CREAT|O_EXCL 抢占式创建 .lock 文件，POSIX/Windows 同语义。
# 失败时轮询等待，超时抛 TimeoutError。stale lock（>60s）自动清理。
_DEFAULT_LOCK_TIMEOUT = 10.0
_DEFAULT_LOCK_POLL = 0.05
_STALE_LOCK_AGE = 60.0


class _FileLock:
    """进程间互斥文件锁（Windows + POSIX 通用）。"""

    def __init__(self, lock_path: str, timeout: float = _DEFAULT_LOCK_TIMEOUT,
                 poll: float = _DEFAULT_LOCK_POLL):
        self.lock_path = lock_path
        self.timeout = timeout
        self.poll = poll
        self._fd: Optional[int] = None

    def __enter__(self):
        os.makedirs(os.path.dirname(self.lock_path), exist_ok=True)
        deadline = time.time() + self.timeout
        while True:
            try:
                self._fd = os.open(
                    self.lock_path,
                    os.O_CREAT | os.O_EXCL | os.O_RDWR,
                )
                # 写 owner 信息便于诊断
                try:
                    os.write(self._fd, f"pid={os.getpid()}\nat={_now_iso()}\n".encode())
                except OSError:
                    pass
                return self
            except FileExistsError:
                # 检查 stale lock 自愈
                try:
                    age = time.time() - os.path.getmtime(self.lock_path)
                    if age > _STALE_LOCK_AGE:
                        try:
                            os.remove(self.lock_path)
                            logger.warning(f"清理 stale lock: {self.lock_path} (age={age:.1f}s)")
                            continue
                        except OSError:
                            pass
                except OSError:
                    pass
                if time.time() > deadline:
                    raise TimeoutError(f"获取文件锁超时 ({self.timeout}s): {self.lock_path}")
                time.sleep(self.poll)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._fd is not None:
            try:
                os.close(self._fd)
            except OSError:
                pass
            self._fd = None
        try:
            os.remove(self.lock_path)
        except OSError:
            pass
        return False


def _meta_lock_path(bid: str) -> str:
    """sidecar 锁文件路径。bid 已被 _safe_name 处理过，文件名安全。"""
    safe_bid = _safe_name(bid)
    return os.path.join(META_DIR, f".{safe_bid}.lock")


@contextlib.contextmanager
def meta_lock(bid: str, timeout: float = _DEFAULT_LOCK_TIMEOUT):
    """
    针对单个 baseline 的 sidecar 加进程级互斥锁。

    用法：
        with meta_lock(bid):
            meta = read_meta(bid)
            meta[...] = ...
            write_meta(bid, meta)
    """
    _ensure_dirs()
    lock = _FileLock(_meta_lock_path(bid), timeout=timeout)
    with lock:
        yield


def _atomic_write_json(path: str, data: Dict[str, Any]) -> None:
    """临时文件 + os.replace 原子替换，避免读到半截 JSON。"""
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.flush()
        try:
            os.fsync(f.fileno())
        except OSError:
            pass
    os.replace(tmp_path, path)


# ──────────────── metadata sidecar ────────────────
def read_meta(bid: str) -> Dict[str, Any]:
    """读取基线 sidecar metadata；不存在则返回默认骨架。"""
    try:
        meta_path = _safe_baseline_path(bid, ".meta.json")
    except ValueError:
        return {}
    if not os.path.exists(meta_path):
        return {}
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"读取 meta 失败 {bid}: {e}")
        return {}


def write_meta(bid: str, meta: Dict[str, Any]) -> None:
    """写 sidecar metadata（原子写入）。建议用 update_meta_atomic 以保证并发安全。"""
    _ensure_dirs()
    meta_path = _safe_baseline_path(bid, ".meta.json")
    _atomic_write_json(meta_path, meta)


def update_meta_atomic(
    bid: str,
    mutator: Callable[[Dict[str, Any]], Optional[Dict[str, Any]]],
    timeout: float = _DEFAULT_LOCK_TIMEOUT,
) -> Dict[str, Any]:
    """
    原子化 read-modify-write sidecar，跨进程安全。

    Args:
        bid: baseline_id
        mutator: 接收 meta dict，返回新 meta（或 None 表示放弃保存，但仍会返回当前 meta）
                 mutator **可以**直接修改入参并 return 它（in-place 修改）
        timeout: 获取锁超时秒数

    Returns:
        最终生效的 meta dict
    """
    with meta_lock(bid, timeout=timeout):
        meta = read_meta(bid)
        new_meta = mutator(meta)
        if new_meta is None:
            return meta
        write_meta(bid, new_meta)
        return new_meta


# ──────────────── Phase 6: 版本快照 / 回滚 ────────────────
def _versions_dir_for(bid: str) -> str:
    """每个基线一个独立子目录，方便清理。"""
    safe_bid = _safe_name(bid)
    return os.path.join(VERSIONS_DIR, safe_bid)


def _gen_version_id() -> str:
    """版本 id：v_{ISO 时间戳, 文件名安全}_{4 位短随机}"""
    import uuid
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    return f"v_{ts}_{uuid.uuid4().hex[:4]}"


def snapshot_version(
    bid: str,
    *,
    by: str = "system",
    source: str = "approved",
    from_run_id: str = "",
    note: str = "",
) -> Dict[str, Any]:
    """
    把当前生效的 {bid}.png 复制一份到 versions/{bid}/{vid}.png，并把版本条目追加到 sidecar.versions。
    超出 _keep_versions() 上限时，最旧的物理文件 + sidecar 条目会被剪掉。

    NOTE: 调用方必须**已经持有** meta_lock（典型场景：approve_baseline / compare_screenshot 创建分支内）。
    """
    import shutil
    _ensure_dirs()
    baseline_path = _safe_baseline_path(bid, ".png")
    if not os.path.exists(baseline_path):
        return {}
    vdir = _versions_dir_for(bid)
    os.makedirs(vdir, exist_ok=True)
    vid = _gen_version_id()
    fname = f"{vid}.png"
    vpath = os.path.join(vdir, fname)
    try:
        shutil.copy2(baseline_path, vpath)
    except Exception as e:
        logger.warning(f"snapshot_version 复制失败 {bid}/{vid}: {e}")
        return {}
    entry = {
        "id": vid,
        "at": _now_iso(),
        "by": by or "system",
        "size": os.path.getsize(vpath),
        "source": source,
        "from_run_id": from_run_id or "",
        "note": (note or "")[:300],
        "file": fname,
    }
    # 写入 sidecar（注意：本函数假定调用方已持锁；若是首次创建场景，调用方会一次性写盘）
    meta = read_meta(bid) or {}
    meta.setdefault("versions", []).append(entry)
    # 剪枝：超出上限的最旧版本（先删物理文件，再剔除 sidecar 条目）
    keep = _keep_versions()
    versions = meta["versions"]
    if len(versions) > keep:
        excess = versions[: len(versions) - keep]
        meta["versions"] = versions[len(versions) - keep:]
        for old in excess:
            try:
                old_path = os.path.join(vdir, old.get("file") or "")
                if old.get("file") and os.path.exists(old_path):
                    os.remove(old_path)
            except Exception as e:
                logger.warning(f"snapshot_version 剪枝失败 {bid}/{old.get('id')}: {e}")
    try:
        write_meta(bid, meta)
    except Exception as e:
        logger.warning(f"snapshot_version 写 sidecar 失败 {bid}: {e}")
    return entry


def list_versions(bid: str) -> List[Dict[str, Any]]:
    """返回 sidecar.versions（最新在最后），附带 file_path 字段供下载/预览。"""
    meta = read_meta(bid) or {}
    versions = list(meta.get("versions") or [])
    vdir = _versions_dir_for(bid)
    enriched = []
    for v in versions:
        v2 = dict(v)
        fname = v.get("file") or ""
        v2["file_path"] = os.path.join(vdir, fname) if fname else ""
        v2["exists"] = bool(fname) and os.path.exists(v2["file_path"])
        enriched.append(v2)
    return enriched


def rollback_to_version(bid: str, version_id: str, by: str = "user", note: str = "") -> Dict[str, Any]:
    """
    把 versions/{bid}/{version_id}.png 复制回 {bid}.png，作为新的"当前生效基线"。
    回滚本身**也会被记录为一次新版本**（source=rollback），形成可前进可后退的链路。
    线程/进程安全：内部加 meta_lock。
    """
    import shutil
    if not version_id:
        raise ValueError("version_id 不能为空")
    baseline_path = _safe_baseline_path(bid, ".png")
    if not os.path.exists(baseline_path):
        raise FileNotFoundError(f"基线不存在: {bid}")

    with meta_lock(bid):
        meta = read_meta(bid) or {}
        versions = meta.get("versions") or []
        target = next((v for v in versions if v.get("id") == version_id), None)
        if not target:
            raise FileNotFoundError(f"版本不存在: {version_id}")
        vdir = _versions_dir_for(bid)
        src = os.path.join(vdir, target.get("file") or "")
        if not os.path.exists(src):
            raise FileNotFoundError(f"版本物理文件丢失: {target.get('file')}")

        prev_size = os.path.getsize(baseline_path)
        # 1) 在覆盖前先归档"当前生效基线"为一个独立版本，避免回滚后无路返回
        snapshot_version(bid, by=by, source="pre_rollback",
                         note=f"回滚到 {version_id} 之前自动留存")
        # 2) 用目标版本覆盖
        shutil.copy2(src, baseline_path)
        new_size = os.path.getsize(baseline_path)
        # 3) 再插入一条 source=rollback 的版本条目
        snapshot_version(bid, by=by, source="rollback",
                         note=note or f"回滚到 {version_id}")
        # 4) 在 sidecar.history 里也留一条事件
        meta = read_meta(bid) or meta
        meta.setdefault("history", []).append({
            "event": "rolled_back",
            "by": by or "user",
            "at": _now_iso(),
            "note": note or "",
            "rollback_to": version_id,
            "prev_size": prev_size,
            "new_size": new_size,
        })
        meta["updated_at"] = _now_iso()
        meta["updated_by"] = by or "user"
        write_meta(bid, meta)

    return {
        "success": True,
        "baseline_id": bid,
        "rollback_to": version_id,
        "prev_size": prev_size,
        "new_size": new_size,
    }


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _init_meta(bid: str, case_id: str, name: str, threshold: float,
               masks: Optional[List[Dict[str, int]]] = None,
               algorithm: str = "pixel",
               env: str = DEFAULT_ENV,
               viewport: str = DEFAULT_VIEWPORT,
               branch: str = DEFAULT_BRANCH) -> Dict[str, Any]:
    return {
        "baseline_id": bid,
        "case_id": case_id,
        "name": name,
        "env": env,
        "viewport": viewport,
        "branch": branch,
        "threshold": threshold,
        "algorithm": algorithm,
        "masks": masks or [],
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "updated_by": "system",
        "last_run_id": "",
        "approve_count": 0,
        "history": [],   # [{event, run_id, by, at, note, prev_size}]
    }


def compare_screenshot(
    current_png_bytes: bytes,
    case_id: str,
    run_id: str,
    name: str,
    threshold: float = DEFAULT_THRESHOLD,
    masks: Optional[List[Dict[str, int]]] = None,
    algorithm: str = "pixel",
    env: Optional[str] = None,
    viewport=None,
    branch: Optional[str] = None,
) -> VisualResult:
    """
    核心对比函数。被 PlaywrightEngine 调用。

    Args:
        current_png_bytes: 截图字节
        case_id / run_id / name: 标识
        threshold: 用例 assertion 提供的阈值（仅用于首次基线初始化和首次比对时的兜底）
        masks: 可选屏蔽区域列表，支持两种类型：
               矩形：{"x":int,"y":int,"w":int,"h":int} 或 {"type":"rect", ...}
               选择器（已展开为 bbox）：{"type":"selector", "bbox":{"x":,"y":,"w":,"h":}, "selector": "..."}
        algorithm: 'pixel' | 'ssim'，可被 sidecar 覆盖
        env / viewport / branch: 命名空间隔离维度（默认 "default"），决定 baseline_id 的命名空间归属

    NOTE: 已存在的基线会优先使用其 sidecar metadata 中的 threshold/masks/algorithm。
    """
    _ensure_dirs()
    eff_env = _norm_ns(env, DEFAULT_ENV)
    eff_viewport = normalize_viewport(viewport)
    eff_branch = _norm_ns(branch, DEFAULT_BRANCH)
    bid = make_baseline_id(case_id, name, env=eff_env, viewport=eff_viewport, branch=eff_branch)
    vr = VisualResult(
        name=name, threshold=threshold, baseline_id=bid,
        env=eff_env, viewport=eff_viewport, branch=eff_branch,
    )

    try:
        baseline_path = _safe_baseline_path(bid, ".png")
    except ValueError as e:
        vr.status = "failed"
        vr.error_message = str(e)
        return vr

    safe_run_id = _safe_name(run_id) if run_id else "norun"
    current_file = f"{bid}_{safe_run_id}.png"
    current_path = os.path.join(CURRENT_DIR, current_file)

    with open(current_path, "wb") as f:
        f.write(current_png_bytes)
    vr.current_path = current_path

    # 首次：创建基线 + 写 sidecar（加锁，避免两个并发首跑都创建/覆盖）
    if not os.path.exists(baseline_path):
        try:
            with meta_lock(bid):
                # double-check（拿锁后可能别的进程已经创建）
                if not os.path.exists(baseline_path):
                    import shutil
                    shutil.copy2(current_path, baseline_path)
                    meta = _init_meta(bid, case_id, name, threshold,
                                      masks=masks, algorithm=algorithm,
                                      env=eff_env, viewport=eff_viewport, branch=eff_branch)
                    meta["last_run_id"] = run_id or ""
                    meta["history"].append({
                        "event": "created", "run_id": run_id or "", "by": "system",
                        "at": _now_iso(), "note": "首次执行自动创建基线",
                    })
                    write_meta(bid, meta)
                    vr.baseline_created = True
                    # Phase 6: 把首版基线归档进 versions/
                    try:
                        snapshot_version(bid, by="system", source="created",
                                         from_run_id=run_id or "", note="首次自动创建")
                    except Exception as e:
                        logger.warning(f"snapshot 首版失败 {bid}: {e}")
        except Exception as e:
            logger.warning(f"基线初始化失败 {bid}: {e}")
        vr.baseline_path = baseline_path
        if vr.baseline_created:
            vr.status = "baseline_created"
            vr.reason = "Baseline did not exist; created from current screenshot."
            vr.algorithm = algorithm
            logger.info("Baseline created: %s", baseline_path)
            try:
                from services.visual_notifier import send_event
                send_event("visual.baseline.created", {
                    "baseline_id": bid,
                    "case_id": case_id,
                    "name": name,
                    "run_id": run_id or "",
                    "env": eff_env, "viewport": eff_viewport, "branch": eff_branch,
                })
            except Exception as _e:
                logger.warning("[P1] visual_notifier emit: %s", _e)
            return vr
        # 落到此处说明并发的另一个进程已创建基线，继续走 diff 流程

    vr.baseline_path = baseline_path

    # 优先使用 sidecar 中的配置
    meta = read_meta(bid)
    eff_threshold = float(meta.get("threshold", threshold)) if meta else threshold
    # Mask 优先级：调用方显式传入 > sidecar 配置（fallback）
    # 原因：engine 上层已经合并 sidecar.masks 并解析了 selector → bbox，
    # 此处再读 sidecar 会用回未解析（无 bbox）的版本，导致 selector mask 失效。
    if masks is not None:
        eff_masks = masks
    else:
        eff_masks = (meta.get("masks") if meta else None) or []
    eff_algorithm = (meta.get("algorithm") if meta else None) or algorithm

    diff_file = f"{bid}_{safe_run_id}_diff.png"
    diff_path = os.path.join(DIFF_DIR, diff_file)

    try:
        if eff_algorithm == "ssim":
            ratio, n_masks = _ssim_diff(baseline_path, current_path, diff_path, eff_masks)
        else:
            ratio, n_masks = _pixel_diff(baseline_path, current_path, diff_path, eff_masks)
    except Exception as e:
        vr.status = "failed"
        vr.error_message = f"Diff error: {e}"
        return vr

    vr.diff_path = diff_path
    vr.diff_ratio = ratio
    vr.threshold = eff_threshold
    vr.algorithm = eff_algorithm
    vr.masks_applied = n_masks

    # 更新 sidecar last_run_id（仅记录，不改 history）— 原子锁
    if meta:
        try:
            def _set_last_run(m):
                if not m:
                    return None
                m["last_run_id"] = run_id or ""
                return m
            update_meta_atomic(bid, _set_last_run, timeout=2.0)
        except Exception as _e:
            logger.exception("[P0] baseline meta write: %s", _e)

    if ratio <= eff_threshold:
        vr.status = "passed"
        vr.reason = f"diff_ratio={ratio} <= threshold={eff_threshold} ({eff_algorithm})"
    else:
        vr.status = "failed"
        vr.reason = f"diff_ratio={ratio} > threshold={eff_threshold} ({eff_algorithm})"
        vr.error_message = f"Visual diff {ratio:.4f} exceeds threshold {eff_threshold}"

    # webhook 事件（默认仅 failed 触发；passed 默认不订阅）
    try:
        from services.visual_notifier import send_event
        send_event(f"visual.diff.{vr.status}", {
            "baseline_id": bid,
            "case_id": case_id,
            "name": name,
            "run_id": run_id or "",
            "env": eff_env, "viewport": eff_viewport, "branch": eff_branch,
            "diff_ratio": vr.diff_ratio,
            "threshold": eff_threshold,
            "algorithm": eff_algorithm,
            "masks_applied": vr.masks_applied,
            "diff_path": os.path.basename(vr.diff_path) if vr.diff_path else "",
        })
    except Exception as _e:
        logger.warning("[P1] visual_notifier emit: %s", _e)

    return vr
