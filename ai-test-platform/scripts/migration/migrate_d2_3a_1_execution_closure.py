#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
D2-3A.1 迁移：创建 iteration_execution_set_cases 关联表
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database.session import engine
from sqlalchemy import text, inspect

def migrate():
    insp = inspect(engine)
    existing = insp.get_table_names()

    with engine.begin() as conn:
        if 'iteration_execution_set_cases' not in existing:
            conn.execute(text("""
                CREATE TABLE iteration_execution_set_cases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_set_id INTEGER NOT NULL,
                    test_case_id VARCHAR(100) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (execution_set_id) REFERENCES iteration_execution_sets(id),
                    FOREIGN KEY (test_case_id) REFERENCES test_cases(id)
                )
            """))
            print("✅ 创建表 iteration_execution_set_cases")
        else:
            print("⏭️  表 iteration_execution_set_cases 已存在")

    print("✅ D2-3A.1 迁移完成")

if __name__ == '__main__':
    migrate()
