#!/usr/bin/env python3
"""测试获取项目列表"""

import requests
import json

BACKEND_URL = "http://localhost:8000"

print("获取项目列表...")
response = requests.get(f"{BACKEND_URL}/api/v2/projects", timeout=30)

print(f"状态码: {response.status_code}")
print(f"\n响应内容:")
result = response.json()
print(json.dumps(result, ensure_ascii=False, indent=2))
print(f"\n数据类型: {type(result)}")

if isinstance(result, list):
    print(f"项目数量: {len(result)}")
    if result:
        print(f"\n第一个项目:")
        print(json.dumps(result[0], ensure_ascii=False, indent=2))
