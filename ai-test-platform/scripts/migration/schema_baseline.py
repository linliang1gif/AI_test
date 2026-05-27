#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移基线导出工具。

用途：
- 对比 SQLAlchemy 模型声明与当前数据库实际结构。
- 固化 startup.py 中仍在运行时执行的 DDL 补丁清单。
- 为后续迁移框架接入提供只读基线，不修改数据库。
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import inspect as sa_inspect  # noqa: E402

from database.models import Base  # noqa: E402
from database.session import DATABASE_URL, engine  # noqa: E402


STARTUP_DDL_BASELINE: List[Dict[str, Any]] = [
    {
        "phase": "Phase 16",
        "operation": "add_columns",
        "table": "test_cases",
        "columns": ["risk_level", "api_pattern", "destructive", "last_reviewed_at"],
    },
    {
        "phase": "P2-3",
        "operation": "add_columns",
        "table": "test_cases",
        "columns": ["case_type"],
    },
    {
        "phase": "Phase 19",
        "operation": "create_tables",
        "tables": ["ai_report_analyses"],
    },
    {
        "phase": "D2-3A.2",
        "operation": "add_columns",
        "table": "iteration_test_points",
        "columns": ["recommended_api", "execution_config"],
    },
    {
        "phase": "P2-10",
        "operation": "create_tables",
        "tables": ["test_suites", "test_suite_cases"],
    },
    {
        "phase": "P3-2",
        "operation": "create_tables",
        "tables": ["test_datasets", "test_dataset_items", "test_data_bindings"],
    },
    {
        "phase": "P3-3B",
        "operation": "create_tables",
        "tables": ["defects", "defect_events"],
    },
    {
        "phase": "Phase C1",
        "operation": "create_tables",
        "tables": [
            "code_snapshots",
            "requirement_points",
            "code_compare_reports",
            "code_compare_findings",
            "requirement_confirm_questions",
        ],
    },
    {
        "phase": "P3-5.1",
        "operation": "create_indexes",
        "indexes": [
            "ix_test_runs_created_at",
            "ix_test_runs_project_id",
            "ix_test_runs_status",
            "ix_test_runs_trigger_type",
            "ix_run_cases_run_id",
            "ix_run_cases_case_id",
            "ix_run_cases_status",
            "ix_test_cases_case_type",
            "ix_test_cases_module",
            "ix_test_cases_priority",
            "ix_test_cases_status",
            "ix_defects_project_id",
            "ix_defects_status",
            "ix_defects_severity",
            "ix_defects_case_id",
            "ix_defects_duplicate_key",
            "ix_tsc_suite_id",
            "ix_tsc_case_id",
            "ix_tdb_case_id",
            "ix_tdb_dataset_id",
            "ix_de_defect_id",
            "ix_de_event_type",
        ],
    },
    {
        "phase": "Product Studio",
        "operation": "create_tables",
        "tables": [
            "product_ideas",
            "product_studio_runs",
            "product_artifacts",
            "product_artifact_trace_links",
        ],
    },
    {
        "phase": "Product Studio Phase 3",
        "operation": "add_columns",
        "table": "product_artifact_trace_links",
        "columns": [
            "quality_score",
            "quality_reason",
            "review_reason",
            "reviewed_at",
            "reviewed_by",
            "promoted_at",
            "promoted_target_id",
        ],
    },
    {
        "phase": "Dev Studio Phase 6",
        "operation": "create_tables",
        "tables": ["dev_tasks", "dev_studio_runs", "dev_artifacts"],
    },
    {
        "phase": "Dev Studio Phase 6.2",
        "operation": "add_columns",
        "table": "dev_studio_runs/dev_artifacts",
        "columns": [
            "dev_studio_runs.batch_id",
            "dev_artifacts.batch_id",
            "dev_artifacts.batch_index",
            "dev_artifacts.parent_artifact_id",
            "dev_artifacts.reference_artifact_ids",
        ],
    },
    {
        "phase": "Phase 7 CodeMap",
        "operation": "create_tables",
        "tables": ["code_map_snapshots", "code_map_files"],
    },
]


def _column_type(column: Any) -> str:
    return str(column.type)


def collect_model_schema() -> Dict[str, Any]:
    tables: Dict[str, Any] = {}
    for table in sorted(Base.metadata.sorted_tables, key=lambda item: item.name):
        tables[table.name] = {
            "columns": [
                {
                    "name": column.name,
                    "type": _column_type(column),
                    "nullable": column.nullable,
                    "primary_key": column.primary_key,
                    "default": str(column.default.arg) if column.default is not None else None,
                    "foreign_keys": sorted(str(fk.column) for fk in column.foreign_keys),
                }
                for column in table.columns
            ],
            "indexes": sorted(index.name for index in table.indexes),
        }
    return tables


def collect_database_schema() -> Dict[str, Any]:
    inspector = sa_inspect(engine)
    tables: Dict[str, Any] = {}
    for table_name in sorted(inspector.get_table_names()):
        tables[table_name] = {
            "columns": [
                {
                    "name": column["name"],
                    "type": str(column["type"]),
                    "nullable": column.get("nullable"),
                    "default": column.get("default"),
                    "primary_key": bool(column.get("primary_key")),
                }
                for column in inspector.get_columns(table_name)
            ],
            "indexes": sorted(index["name"] for index in inspector.get_indexes(table_name)),
            "foreign_keys": inspector.get_foreign_keys(table_name),
        }
    return tables


def _table_columns(schema: Dict[str, Any], table_name: str) -> set[str]:
    return {column["name"] for column in schema.get(table_name, {}).get("columns", [])}


def compare_schema(model_schema: Dict[str, Any], database_schema: Dict[str, Any]) -> Dict[str, Any]:
    model_tables = set(model_schema)
    database_tables = set(database_schema)

    common_tables = sorted(model_tables & database_tables)
    column_diff = {}
    for table_name in common_tables:
        model_columns = _table_columns(model_schema, table_name)
        database_columns = _table_columns(database_schema, table_name)
        missing_in_database = sorted(model_columns - database_columns)
        extra_in_database = sorted(database_columns - model_columns)
        if missing_in_database or extra_in_database:
            column_diff[table_name] = {
                "missing_in_database": missing_in_database,
                "extra_in_database": extra_in_database,
            }

    return {
        "missing_tables_in_database": sorted(model_tables - database_tables),
        "extra_tables_in_database": sorted(database_tables - model_tables),
        "column_diff": column_diff,
    }


def collect_startup_patch_status(database_schema: Dict[str, Any]) -> List[Dict[str, Any]]:
    existing_tables = set(database_schema)
    statuses: List[Dict[str, Any]] = []

    for patch in STARTUP_DDL_BASELINE:
        status = dict(patch)
        if patch["operation"] == "create_tables":
            tables = patch.get("tables", [])
            status["missing_tables"] = [table for table in tables if table not in existing_tables]
            status["applied"] = not status["missing_tables"]
        elif patch["operation"] == "add_columns":
            table = patch["table"]
            if "/" in table:
                status["applied"] = None
                status["note"] = "multi-table patch; inspect columns field manually"
            elif table not in existing_tables:
                status["applied"] = False
                status["missing_table"] = table
            else:
                existing_columns = _table_columns(database_schema, table)
                status["missing_columns"] = [column for column in patch.get("columns", []) if column not in existing_columns]
                status["applied"] = not status["missing_columns"]
        elif patch["operation"] == "create_indexes":
            existing_indexes = {
                index_name
                for table in database_schema.values()
                for index_name in table.get("indexes", [])
            }
            status["missing_indexes"] = [index for index in patch.get("indexes", []) if index not in existing_indexes]
            status["applied"] = not status["missing_indexes"]
        statuses.append(status)

    return statuses


def build_report() -> Dict[str, Any]:
    model_schema = collect_model_schema()
    database_schema = collect_database_schema()
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "database_url": DATABASE_URL,
        "summary": {
            "model_table_count": len(model_schema),
            "database_table_count": len(database_schema),
            "startup_patch_count": len(STARTUP_DDL_BASELINE),
        },
        "diff": compare_schema(model_schema, database_schema),
        "startup_patch_status": collect_startup_patch_status(database_schema),
        "model_schema": model_schema,
        "database_schema": database_schema,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="导出数据库迁移基线 JSON")
    parser.add_argument("--output", "-o", help="输出 JSON 文件路径；不传则打印到 stdout")
    parser.add_argument("--pretty", action="store_true", help="格式化 JSON 输出")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_report()
    json_text = json.dumps(report, ensure_ascii=False, indent=2 if args.pretty else None)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json_text, encoding="utf-8")
        print(f"数据库迁移基线已导出: {output_path}")
        return
    print(json_text)


if __name__ == "__main__":
    main()