#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轻量级数据库迁移登记器。

当前阶段只建立版本表并登记启动期 DDL 基线；历史启动补丁仍由
backend.startup._run_migrations 兜底执行，后续可逐步迁入独立 revision。
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, Iterable, List

from sqlalchemy import inspect as sa_inspect, text

from database.session import get_db_session

logger = logging.getLogger("migration_registry")

SCHEMA_MIGRATIONS_TABLE = "schema_migrations"
STARTUP_BASELINE_VERSION = "202605_startup_ddl_baseline"

STARTUP_BASELINE_PATCHES: List[Dict[str, Any]] = [
    {"phase": "Phase 16", "operation": "add_columns", "table": "test_cases"},
    {"phase": "P2-3", "operation": "add_columns", "table": "test_cases"},
    {"phase": "Phase 19", "operation": "create_tables", "tables": ["ai_report_analyses"]},
    {"phase": "D2-3A.2", "operation": "add_columns", "table": "iteration_test_points"},
    {"phase": "P2-10", "operation": "create_tables", "tables": ["test_suites", "test_suite_cases"]},
    {"phase": "P3-2", "operation": "create_tables", "tables": ["test_datasets", "test_dataset_items", "test_data_bindings"]},
    {"phase": "P3-3B", "operation": "create_tables", "tables": ["defects", "defect_events"]},
    {"phase": "Phase C1", "operation": "create_tables", "tables": ["code_snapshots", "requirement_points", "code_compare_reports", "code_compare_findings", "requirement_confirm_questions"]},
    {"phase": "P3-5.1", "operation": "create_indexes"},
    {"phase": "Product Studio", "operation": "create_tables", "tables": ["product_ideas", "product_studio_runs", "product_artifacts", "product_artifact_trace_links"]},
    {"phase": "Product Studio Phase 3", "operation": "add_columns", "table": "product_artifact_trace_links"},
    {"phase": "Dev Studio Phase 6", "operation": "create_tables", "tables": ["dev_tasks", "dev_studio_runs", "dev_artifacts"]},
    {"phase": "Dev Studio Phase 6.2", "operation": "add_columns", "table": "dev_studio_runs/dev_artifacts"},
    {"phase": "Phase 7 CodeMap", "operation": "create_tables", "tables": ["code_map_snapshots", "code_map_files"]},
]


def _table_exists(table_names: Iterable[str], table_name: str) -> bool:
    return table_name in set(table_names)


def ensure_schema_migrations_table() -> None:
    """创建迁移版本表；幂等执行。"""
    with get_db_session() as db:
        inspector = sa_inspect(db.bind)
        tables = inspector.get_table_names()
        if _table_exists(tables, SCHEMA_MIGRATIONS_TABLE):
            return

        db.execute(text(f"""
            CREATE TABLE {SCHEMA_MIGRATIONS_TABLE} (
                version VARCHAR(100) PRIMARY KEY,
                description VARCHAR(500) NOT NULL,
                applied_at DATETIME NOT NULL,
                checksum VARCHAR(100),
                details TEXT
            )
        """))
        logger.info("数据库迁移版本表已创建: %s", SCHEMA_MIGRATIONS_TABLE)


def _has_version(version: str) -> bool:
    with get_db_session() as db:
        result = db.execute(
            text(f"SELECT 1 FROM {SCHEMA_MIGRATIONS_TABLE} WHERE version = :version"),
            {"version": version},
        ).first()
        return result is not None


def stamp_startup_baseline() -> None:
    """登记当前 startup.py 运行时补丁基线；不替代补丁执行。"""
    ensure_schema_migrations_table()
    if _has_version(STARTUP_BASELINE_VERSION):
        logger.info("启动期 DDL 基线已登记: %s", STARTUP_BASELINE_VERSION)
        return

    details = {
        "source": "backend.startup._run_migrations",
        "strategy": "legacy startup DDL remains as compatibility fallback",
        "patches": STARTUP_BASELINE_PATCHES,
    }
    with get_db_session() as db:
        db.execute(
            text(f"""
                INSERT INTO {SCHEMA_MIGRATIONS_TABLE}
                    (version, description, applied_at, checksum, details)
                VALUES
                    (:version, :description, :applied_at, :checksum, :details)
            """),
            {
                "version": STARTUP_BASELINE_VERSION,
                "description": "Baseline registry for legacy startup DDL patches",
                "applied_at": datetime.now(),
                "checksum": str(len(STARTUP_BASELINE_PATCHES)),
                "details": json.dumps(details, ensure_ascii=False),
            },
        )
        logger.info("启动期 DDL 基线已登记: %s", STARTUP_BASELINE_VERSION)


def run_registered_migrations() -> None:
    """运行已登记的轻量迁移。"""
    stamp_startup_baseline()