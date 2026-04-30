#!/usr/bin/env python3
"""测试创建鉴权配置"""

import requests
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
env_file = Path(__file__).parent / ".env.bluedot"
load_dotenv(env_file)

BACKEND_URL = "http://localhost:8000"
PROJECT_ID = 8
BLUEDOT_TOKEN = os.getenv("BLUEDOT_TOKEN", "")

print("测试创建鉴权配置...")
data = {
    "project_id": PROJECT_ID,
    "name": "蓝点Bearer Token",
    "auth_type": "bearer",
    "config": {
        "token": BLUEDOT_TOKEN
    }
}

print(f"请求数据: {json.dumps({**data, 'config': {'token': '***'}}, ensure_ascii=False, indent=2)}")

response = requests.post(f"{BACKEND_URL}/api/v2/auth-profiles", json=data, timeout=30)

print(f"\n状态码: {response.status_code}")
print(f"响应: {response.text}")
