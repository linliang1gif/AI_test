"""
视觉测试 Webhook 通知器（企业级）。

设计目标：
  - 主流程零阻塞：后台 daemon 线程异步发送，失败不影响视觉对比/批准。
  - 零额外依赖：使用 stdlib urllib，不引入 requests。
  - 可签名：可选 HMAC-SHA256（请求头 X-Visual-Signature: sha256=...）。
  - 可过滤：通过 VISUAL_WEBHOOK_EVENTS（逗号分隔白名单）选择性订阅。
  - 可注入：通过 set_test_sink(callback) 让单测捕获事件、跳过真实 HTTP。

事件命名（统一 visual.<domain>.<action>）：
  visual.diff.failed              视觉对比失败（diff_ratio > threshold）
  visual.diff.passed              视觉对比通过（默认不发，可显式订阅）
  visual.baseline.created         新建基线
  visual.baseline.approved        基线被批准（覆盖）
  visual.baseline.deleted         基线被删除
  visual.baseline.config_updated  基线配置（threshold/算法/mask）被更新

环境变量：
  VISUAL_WEBHOOK_URL       ── 必填触发开关，为空时不发任何事件
  VISUAL_WEBHOOK_TIMEOUT   ── 单次发送超时（秒），默认 5
  VISUAL_WEBHOOK_SECRET    ── 可选 HMAC-SHA256 签名密钥
  VISUAL_WEBHOOK_EVENTS    ── 可选订阅白名单，如 "visual.diff.failed,visual.baseline.approved"
                              不设则默认订阅除 visual.diff.passed 之外所有事件
"""
from __future__ import annotations

import os
import json
import hmac
import time
import hashlib
import logging
import threading
import urllib.request
import urllib.error
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 5.0
DEFAULT_SUBSCRIBE_ALL_EXCEPT = {"visual.diff.passed"}

# Phase 7: 重试策略 — 默认指数退避 1s / 2s / 4s（共 1 + 3 = 4 次尝试）
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_BASE = 1.0    # 秒；第 i 次重试睡 base * 2**(i-1)


def _max_retries() -> int:
    try:
        return max(0, int(os.getenv("VISUAL_WEBHOOK_MAX_RETRIES", str(DEFAULT_MAX_RETRIES))))
    except ValueError:
        return DEFAULT_MAX_RETRIES


def _backoff_base() -> float:
    try:
        return max(0.0, float(os.getenv("VISUAL_WEBHOOK_BACKOFF_BASE", str(DEFAULT_BACKOFF_BASE))))
    except ValueError:
        return DEFAULT_BACKOFF_BASE

# 单测注入点：若不为 None，所有事件改写到这个回调，跳过真实 HTTP
_test_sink: Optional[Callable[[str, Dict[str, Any]], None]] = None


def set_test_sink(cb: Optional[Callable[[str, Dict[str, Any]], None]]) -> None:
    """单测专用：注入回调以捕获事件；传 None 取消。"""
    global _test_sink
    _test_sink = cb


# ──────────────── 配置读取（每次调用动态读，便于运行时切换） ────────────────
def _load_subscriptions() -> Optional[Set[str]]:
    raw = os.getenv("VISUAL_WEBHOOK_EVENTS", "").strip()
    if not raw:
        return None
    return {x.strip() for x in raw.split(",") if x.strip()}


def _is_subscribed(event_type: str) -> bool:
    sub = _load_subscriptions()
    if sub is None:
        return event_type not in DEFAULT_SUBSCRIBE_ALL_EXCEPT
    return event_type in sub


def _webhook_url() -> str:
    return os.getenv("VISUAL_WEBHOOK_URL", "").strip()


def _webhook_timeout() -> float:
    try:
        return float(os.getenv("VISUAL_WEBHOOK_TIMEOUT", str(DEFAULT_TIMEOUT)))
    except ValueError:
        return DEFAULT_TIMEOUT


def _webhook_secret() -> str:
    return os.getenv("VISUAL_WEBHOOK_SECRET", "")


# ──────────────── 发送 ────────────────
def _build_payload(event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "event": event_type,
        "ts": datetime.now().isoformat(timespec="seconds"),
        "source": "visual_testing",
        "data": data,
    }


def _sign(body: bytes, secret: str) -> str:
    mac = hmac.new(secret.encode("utf-8"), body, hashlib.sha256)
    return f"sha256={mac.hexdigest()}"


def _post(url: str, body: bytes, headers: Dict[str, str], timeout: float) -> int:
    """实际 HTTP POST（独立函数便于测试 mock）。返回 status code。"""
    req = urllib.request.Request(url, data=body, method="POST")
    for k, v in headers.items():
        req.add_header(k, v)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status


def _send_once(url: str, event_type: str, payload: Dict[str, Any]) -> int:
    """单次发送（不重试）；2xx 返回 status，否则抛异常。"""
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "ai-test-platform-visual-notifier/1.0",
        "X-Visual-Event": event_type,
    }
    secret = _webhook_secret()
    if secret:
        headers["X-Visual-Signature"] = _sign(body, secret)
    status = _post(url, body, headers, _webhook_timeout())
    if status >= 300:
        raise IOError(f"non-2xx status={status}")
    return status


def _send_sync(event_type: str, payload: Dict[str, Any]) -> None:
    """
    同步发送（在后台线程内调用）+ 指数退避重试 + 失败入 DLQ。

    重试策略：第 i 次重试睡 base * 2**(i-1) 秒，base 默认 1s。
    最多 _max_retries() 次重试（即总尝试次数 = 1 + max_retries）。
    所有尝试都失败后写入 DLQ。
    """
    url = _webhook_url()
    if not url:
        return

    max_retries = _max_retries()
    base = _backoff_base()
    last_err = ""
    for attempt in range(0, max_retries + 1):
        try:
            _send_once(url, event_type, payload)
            if attempt > 0:
                logger.info(f"webhook 重试 {attempt} 次后成功 event={event_type}")
            return
        except urllib.error.URLError as e:
            last_err = f"URLError: {e}"
        except IOError as e:
            last_err = str(e)
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
        # 还有重试机会则退避
        if attempt < max_retries:
            sleep_s = base * (2 ** attempt)
            logger.warning(
                f"webhook 失败 event={event_type} attempt={attempt + 1}/{max_retries + 1}"
                f" err={last_err} → {sleep_s:.1f}s 后重试"
            )
            time.sleep(sleep_s)

    # 所有重试都失败 → DLQ
    logger.warning(
        f"webhook 最终失败 event={event_type} attempts={max_retries + 1} err={last_err} → 写入 DLQ"
    )
    try:
        from services import visual_webhook_dlq
        visual_webhook_dlq.add(event_type, payload, last_err, attempts=max_retries + 1)
    except Exception as e:
        logger.warning(f"DLQ 写入失败 event={event_type}: {e}")


def retry_dead_letter(dlq_id: int) -> Dict[str, Any]:
    """
    从 DLQ 里手动重发一条（UI 调用）：
      - 成功 → 标 resolved
      - 失败 → attempts += 1，更新 last_error，仍留在 DLQ
    返回 {success, status: 'sent'|'failed', error?, dlq}。
    """
    from services import visual_webhook_dlq
    item = visual_webhook_dlq.get(dlq_id)
    if not item:
        return {"success": False, "status": "not_found"}
    url = _webhook_url()
    if not url:
        return {"success": False, "status": "no_url", "error": "VISUAL_WEBHOOK_URL 未配置"}
    try:
        _send_once(url, item["event_type"], item["payload"])
        visual_webhook_dlq.mark_resolved(dlq_id)
        return {"success": True, "status": "sent", "dlq": visual_webhook_dlq.get(dlq_id)}
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
        visual_webhook_dlq.mark_attempt(dlq_id, last_error=err)
        return {"success": False, "status": "failed", "error": err,
                "dlq": visual_webhook_dlq.get(dlq_id)}


def send_event(event_type: str, data: Dict[str, Any]) -> None:
    """
    发送一条视觉测试事件。

    - 主流程零阻塞：默认在 daemon 线程内异步发送
    - 单测：若注入了 _test_sink，则同步调用回调，不走 HTTP
    - 未配置 URL 时静默跳过
    - 不订阅的事件类型直接丢弃
    """
    try:
        if not _is_subscribed(event_type):
            return
        payload = _build_payload(event_type, data)

        # 单测注入优先，且同步执行（便于断言）
        if _test_sink is not None:
            try:
                _test_sink(event_type, payload)
            except Exception as e:
                logger.warning(f"test_sink 异常: {e}")
            return

        if not _webhook_url():
            return

        threading.Thread(
            target=_send_sync,
            args=(event_type, payload),
            daemon=True,
            name=f"visual-webhook-{event_type}",
        ).start()
    except Exception as e:
        # 通知器自身永远不应拖垮主流程
        logger.warning(f"send_event 异常 {event_type}: {e}")
