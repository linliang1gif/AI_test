#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试删除API的响应格式
"""

import requests
import json

BASE_URL = "http://localhost:8000"

# 获取一个测试用例ID
r = requests.get(f"{BASE_URL}/api/test-cases")
cases = r.json()['data']

if len(cases) > 0:
    test_id = cases[-1]['id']
    print(f"测试删除 ID: {test_id}")
    print(f"ID类型: {type(test_id)}")
    
    # 调用删除API
    r = requests.post(
        f"{BASE_URL}/api/testcases/batch-delete",
        json={"ids": [test_id]},
        timeout=10
    )
    
    print(f"\n状态码: {r.status_code}")
    print(f"响应内容:")
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))
else:
    print("没有测试用例")
