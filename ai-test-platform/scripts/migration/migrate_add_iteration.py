#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration: 添加迭代管理
1. 创建 iterations 表（通过 init_db 自动完成）
2. 给 test_cases 表添加 iteration_id 列
3. 给 test_runs 表添加 iteration_id 列
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, inspect
from database.session import engine, init_db


def run_migration():
    """执行迭代管理相关的数据库迁移"""
    # Step 1: init_db 会创建 iterations 表（如果不存在）
    print("Step 1: 创建 iterations 表...")
    init_db()

    inspector = inspect(engine)

    with engine.connect() as conn:
        # Step 2: test_cases 表添加 iteration_id
        tc_columns = [c['name'] for c in inspector.get_columns('test_cases')]
        if 'iteration_id' not in tc_columns:
            print("Step 2: test_cases 添加 iteration_id 列...")
            conn.execute(text("ALTER TABLE test_cases ADD COLUMN iteration_id INTEGER REFERENCES iterations(id)"))
            conn.commit()
            print("  ✅ test_cases.iteration_id 已添加")
        else:
            print("Step 2: test_cases.iteration_id 已存在，跳过")

        # Step 3: test_runs 表添加 iteration_id
        tr_columns = [c['name'] for c in inspector.get_columns('test_runs')]
        if 'iteration_id' not in tr_columns:
            print("Step 3: test_runs 添加 iteration_id 列...")
            conn.execute(text("ALTER TABLE test_runs ADD COLUMN iteration_id INTEGER REFERENCES iterations(id)"))
            conn.commit()
            print("  ✅ test_runs.iteration_id 已添加")
        else:
            print("Step 3: test_runs.iteration_id 已存在，跳过")

    print("\n✅ 迭代管理迁移完成！")


if __name__ == "__main__":
    run_migration()
