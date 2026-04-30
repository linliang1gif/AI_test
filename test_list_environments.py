#!/usr/bin/env python3
"""测试获取环境列表"""

import requests
import json

BACKEND_URL = "http://localhost:8000"
PROJECT_ID = 8

print(f"获取项目 {PROJECT_ID} 的环境列表...")
response = requests.get(f"{BACKEND_URL}/api/v2/environments?project_id={PROJECT_ID}", timeout=30)

print(f"状态码: {response.status_code}")
print(f"\n响应内容:")
result = response.json()
print(json.dumps(result, ensure_ascii=False, indent=2))
