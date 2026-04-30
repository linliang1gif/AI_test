#!/usr/bin/env python3
"""测试创建环境"""

import requests
import json

BACKEND_URL = "http://localhost:8000"
PROJECT_ID = 8

print("测试创建环境...")
data = {
    "project_id": PROJECT_ID,
    "name": "test",  # 使用枚举值
    "base_url": "https://dev-recycle.szhibu.com/dev-api/recycle",
    "description": "蓝点项目测试环境"
}

print(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")

response = requests.post(f"{BACKEND_URL}/api/v2/environments", json=data, timeout=30)

print(f"\n状态码: {response.status_code}")
print(f"响应: {response.text}")
