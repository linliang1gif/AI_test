from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


_DB_DIR = Path.home() / ".ai_testgen"
_DB_PATH = _DB_DIR / "history.db"


def _get_conn() -> sqlite3.Connection:
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS generation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            source_file TEXT NOT NULL,
            output_file TEXT,
            project_name TEXT,
            module_name TEXT,
            model_used TEXT,
            cases_count INTEGER DEFAULT 0,
            raw_count INTEGER DEFAULT 0,
            dedup_removed INTEGER DEFAULT 0,
            quality_score INTEGER DEFAULT 0,
            coverage_json TEXT,
            status TEXT DEFAULT 'success'
        )
    """)
    conn.commit()
    return conn


def record_generation(
    source_file: str,
    output_file: str,
    project_name: str,
    module_name: str,
    model_used: str,
    cases_count: int,
    raw_count: int,
    dedup_removed: int,
    quality_score: int,
    coverage: Optional[Dict] = None,
    status: str = "success",
) -> int:
    """Record a generation run. Returns the record ID."""
    conn = _get_conn()
    try:
        cursor = conn.execute(
            """INSERT INTO generation_history
               (timestamp, source_file, output_file, project_name, module_name,
                model_used, cases_count, raw_count, dedup_removed, quality_score,
                coverage_json, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.now().isoformat(),
                source_file,
                output_file,
                project_name,
                module_name,
                model_used,
                cases_count,
                raw_count,
                dedup_removed,
                quality_score,
                json.dumps(coverage or {}, ensure_ascii=False),
                status,
            ),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_recent_history(limit: int = 50) -> List[dict]:
    """Get recent generation history."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM generation_history ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_stats() -> dict:
    """Get aggregate statistics."""
    conn = _get_conn()
    try:
        row = conn.execute("""
            SELECT
                COUNT(*) as total_runs,
                SUM(cases_count) as total_cases,
                AVG(quality_score) as avg_quality,
                SUM(dedup_removed) as total_dedup
            FROM generation_history
            WHERE status = 'success'
        """).fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()
