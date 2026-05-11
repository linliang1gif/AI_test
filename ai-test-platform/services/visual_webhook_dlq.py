"""
视觉测试 Webhook 死信队列（DLQ）。

为什么独立 sqlite 文件而不是主 DB：
  - 死信只在 webhook 发送彻底失败时才写，写入路径不应依赖主业务 ORM（避免循环依赖）
  - 字段简单（5 列），无需迁移系统
  - 独立文件便于运维：可单独清理/备份/迁移

线程/进程并发：
  - sqlite3 内置文件锁；写操作短小，不需要额外的 Python 级锁
  - 所有方法每次自己开/关连接（避免 Python sqlite "thread safety" 问题）
"""
from __future__ import annotations

import os
import json
import sqlite3
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "visual_webhook_dlq.sqlite",
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS dead_letters (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type    TEXT NOT NULL,
    payload_json  TEXT NOT NULL,
    last_error    TEXT,
    attempts      INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL,
    last_attempt_at TEXT,
    resolved      INTEGER NOT NULL DEFAULT 0,
    resolved_at   TEXT
);
CREATE INDEX IF NOT EXISTS idx_dl_resolved ON dead_letters(resolved);
CREATE INDEX IF NOT EXISTS idx_dl_event ON dead_letters(event_type);
CREATE INDEX IF NOT EXISTS idx_dl_created ON dead_letters(created_at);
"""


def _conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    c = sqlite3.connect(DB_PATH, timeout=10.0, isolation_level=None)
    c.row_factory = sqlite3.Row
    c.executescript(_SCHEMA)
    return c


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def add(event_type: str, payload: Dict[str, Any], last_error: str, attempts: int) -> int:
    """所有重试失败后入库，返回 id。"""
    body = json.dumps(payload, ensure_ascii=False)
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO dead_letters(event_type, payload_json, last_error, attempts,"
            " created_at, last_attempt_at, resolved) VALUES(?, ?, ?, ?, ?, ?, 0)",
            (event_type, body, (last_error or "")[:1000], int(attempts),
             _now_iso(), _now_iso()),
        )
        return int(cur.lastrowid)


def list_recent(
    limit: int = 50,
    include_resolved: bool = False,
    event_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """最近的死信，最新在前。"""
    sql = "SELECT * FROM dead_letters WHERE 1=1"
    args: List[Any] = []
    if not include_resolved:
        sql += " AND resolved = 0"
    if event_type:
        sql += " AND event_type = ?"
        args.append(event_type)
    sql += " ORDER BY id DESC LIMIT ?"
    args.append(int(limit))
    with _conn() as c:
        rows = c.execute(sql, args).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        try:
            d["payload"] = json.loads(d.pop("payload_json") or "{}")
        except Exception:
            d["payload"] = {}
        d["resolved"] = bool(d["resolved"])
        out.append(d)
    return out


def get(dlq_id: int) -> Optional[Dict[str, Any]]:
    with _conn() as c:
        r = c.execute("SELECT * FROM dead_letters WHERE id = ?", (int(dlq_id),)).fetchone()
    if not r:
        return None
    d = dict(r)
    try:
        d["payload"] = json.loads(d.pop("payload_json") or "{}")
    except Exception:
        d["payload"] = {}
    d["resolved"] = bool(d["resolved"])
    return d


def mark_attempt(dlq_id: int, last_error: str = "") -> None:
    """重试失败时更新 attempts 计数 + last_error。"""
    with _conn() as c:
        c.execute(
            "UPDATE dead_letters SET attempts = attempts + 1, last_attempt_at = ?,"
            " last_error = ? WHERE id = ?",
            (_now_iso(), (last_error or "")[:1000], int(dlq_id)),
        )


def mark_resolved(dlq_id: int) -> None:
    """重试成功时标记 resolved。"""
    with _conn() as c:
        c.execute(
            "UPDATE dead_letters SET resolved = 1, resolved_at = ? WHERE id = ?",
            (_now_iso(), int(dlq_id)),
        )


def delete(dlq_id: int) -> bool:
    with _conn() as c:
        cur = c.execute("DELETE FROM dead_letters WHERE id = ?", (int(dlq_id),))
        return cur.rowcount > 0


def stats() -> Dict[str, Any]:
    """简要统计：总数 / 未解决 / 已解决 / 各事件类型分布。"""
    with _conn() as c:
        total = c.execute("SELECT COUNT(*) FROM dead_letters").fetchone()[0]
        unresolved = c.execute("SELECT COUNT(*) FROM dead_letters WHERE resolved=0").fetchone()[0]
        by_type = {
            r["event_type"]: r["c"]
            for r in c.execute(
                "SELECT event_type, COUNT(*) AS c FROM dead_letters WHERE resolved=0"
                " GROUP BY event_type"
            ).fetchall()
        }
    return {"total": total, "unresolved": unresolved, "by_event_type": by_type}


def clear_all_for_test() -> None:
    """仅供测试使用。"""
    with _conn() as c:
        c.execute("DELETE FROM dead_letters")
