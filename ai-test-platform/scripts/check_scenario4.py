#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查场景4的详细数据"""

import sys
import sqlite3
import json
from pathlib import Path

project_root = Path(__file__).parent.parent
DB_PATH = project_root / "data" / "test_platform.db"

run_id = "RUN_20260501173523_dd8fa6ec"

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
    print(f"❌ 未找到记录")
    sys.exit(1)

print(f"RunCase ID: {row[0]}")
print(f"TestCaseID: {row[1]}")
print(f"Status: {row[2]}")
print(f"Duration: {row[3]}")
print(f"ErrorMessage: {row[4]}")
print(f"ErrorType: {row[5]}")
print(f"AssertionsPassed: {row[8]}")
print(f"AssertionsFailed: {row[9]}")

assertion_details = row[10]
if assertion_details:
    try:
        details = json.loads(assertion_details) if isinstance(assertion_details, str) else assertion_details
        print(f"\nAssertionDetails:")
        print(json.dumps(details, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"解析失败: {e}")
else:
    print("\nAssertionDetails: None")

resp_snapshot = row[7]
if resp_snapshot:
    try:
        resp = json.loads(resp_snapshot) if isinstance(resp_snapshot, str) else resp_snapshot
        print(f"\nResponseSnapshot:")
        print(f"  StatusCode: {resp.get('status_code')}")
        print(f"  Body: {str(resp.get('body', ''))[:200]}")
    except Exception as e:
        print(f"解析失败: {e}")
