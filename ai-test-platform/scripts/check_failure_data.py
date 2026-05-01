#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查失败场景的数据库记录"""

import sys
import sqlite3
import json
from pathlib import Path

project_root = Path(__file__).parent.parent
DB_PATH = project_root / "data" / "test_platform.db"

def check_run_case_details(run_id: str):
    """检查run_case的详细信息"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            id, test_case_id, status, duration,
            error_message, error_type,
            request_snapshot, response_snapshot,
            assertions_passed, assertions_failed,
            assertion_details
        FROM run_cases 
        WHERE run_id = ?
    """, (run_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        print(f"❌ 未找到 run_id={run_id} 的记录")
        return
    
    print(f"\n{'=' * 80}")
    print(f"RunCase 详情: run_id={run_id}")
    print(f"{'=' * 80}")
    print(f"ID: {row[0]}")
    print(f"TestCaseID: {row[1]}")
    print(f"Status: {row[2]}")
    print(f"Duration: {row[3]}")
    print(f"ErrorMessage: {row[4]}")
    print(f"ErrorType: {row[5]}")
    print(f"AssertionsPassed: {row[8]}")
    print(f"AssertionsFailed: {row[9]}")
    
    # 检查快照
    req_snapshot = row[6]
    resp_snapshot = row[7]
    assertion_details = row[10]
    
    print(f"\nRequestSnapshot: {'存在' if req_snapshot else '不存在'}")
    if req_snapshot:
        try:
            req_data = json.loads(req_snapshot) if isinstance(req_snapshot, str) else req_snapshot
            print(f"  Method: {req_data.get('method')}")
            print(f"  URL: {req_data.get('url')}")
        except:
            pass
    
    print(f"\nResponseSnapshot: {'存在' if resp_snapshot else '不存在'}")
    if resp_snapshot:
        try:
            resp_data = json.loads(resp_snapshot) if isinstance(resp_snapshot, str) else resp_snapshot
            print(f"  StatusCode: {resp_data.get('status_code')}")
            print(f"  Body: {str(resp_data.get('body', ''))[:100]}")
        except:
            pass
    
    print(f"\nAssertionDetails: {'存在' if assertion_details else '不存在'}")
    if assertion_details:
        try:
            details = json.loads(assertion_details) if isinstance(assertion_details, str) else assertion_details
            print(f"  断言数量: {len(details) if isinstance(details, list) else 0}")
        except:
            pass

if __name__ == "__main__":
    # 检查最近的几个失败场景
    test_runs = [
        "RUN_20260501173300_19dc7bc2",  # 404
        "RUN_20260501173305_952d21e7",  # 500
        "RUN_20260501173310_0b780d40",  # 超时
        "RUN_20260501173315_317f70ee",  # 断言失败
    ]
    
    for run_id in test_runs:
        check_run_case_details(run_id)
