#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
D2-3A 迭代中心数据库迁移
- iterations 表新增列: version, test_owner, planned_start_time, planned_release_time
- 新建表: iteration_requirements, iteration_test_points, iteration_execution_sets
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, inspect
from database.session import get_db_session


def migrate():
    with get_db_session() as db:
        inspector = inspect(db.bind)
        existing_tables = set(inspector.get_table_names())

        # ── 1. iterations 表新增列 ──
        if "iterations" in existing_tables:
            cols = {c["name"] for c in inspector.get_columns("iterations")}
            new_cols = [
                ("version", "VARCHAR(50) DEFAULT ''"),
                ("test_owner", "VARCHAR(100) DEFAULT ''"),
                ("planned_start_time", "VARCHAR(30) DEFAULT ''"),
                ("planned_release_time", "VARCHAR(30) DEFAULT ''"),
            ]
            for col_name, col_def in new_cols:
                if col_name not in cols:
                    db.execute(text(f"ALTER TABLE iterations ADD COLUMN {col_name} {col_def}"))
                    print(f"  + iterations.{col_name}")
                else:
                    print(f"  = iterations.{col_name} (已存在)")
            db.commit()

        # ── 2. iteration_requirements 表 ──
        if "iteration_requirements" not in existing_tables:
            db.execute(text("""
                CREATE TABLE iteration_requirements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    iteration_id INTEGER NOT NULL REFERENCES iterations(id),
                    title VARCHAR(500) NOT NULL,
                    content TEXT DEFAULT '',
                    source_type VARCHAR(50) DEFAULT 'manual',
                    source_url VARCHAR(1000) DEFAULT '',
                    ai_summary TEXT DEFAULT '',
                    risk_level VARCHAR(10) DEFAULT 'P1',
                    confirm_questions TEXT DEFAULT '',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("  + 表 iteration_requirements 已创建")
        else:
            print("  = 表 iteration_requirements 已存在")

        # ── 3. iteration_test_points 表 ──
        if "iteration_test_points" not in existing_tables:
            db.execute(text("""
                CREATE TABLE iteration_test_points (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    iteration_id INTEGER NOT NULL REFERENCES iterations(id),
                    requirement_id INTEGER REFERENCES iteration_requirements(id),
                    module_name VARCHAR(200) DEFAULT '',
                    test_point TEXT NOT NULL,
                    risk_level VARCHAR(10) DEFAULT 'P1',
                    priority VARCHAR(10) DEFAULT 'medium',
                    test_type VARCHAR(50) DEFAULT 'functional',
                    ai_generated BOOLEAN DEFAULT 0,
                    confirmed BOOLEAN DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("  + 表 iteration_test_points 已创建")
        else:
            print("  = 表 iteration_test_points 已存在")

        # ── 4. iteration_execution_sets 表 ──
        if "iteration_execution_sets" not in existing_tables:
            db.execute(text("""
                CREATE TABLE iteration_execution_sets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    iteration_id INTEGER NOT NULL REFERENCES iterations(id),
                    name VARCHAR(200) NOT NULL,
                    type VARCHAR(50) DEFAULT 'iteration',
                    status VARCHAR(50) DEFAULT 'created',
                    case_count INTEGER DEFAULT 0,
                    run_id VARCHAR(100),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("  + 表 iteration_execution_sets 已创建")
        else:
            print("  = 表 iteration_execution_sets 已存在")

        db.commit()
        print("\nD2-3A 迁移完成！")


if __name__ == "__main__":
    migrate()
