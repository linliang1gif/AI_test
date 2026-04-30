#!/usr/bin/env python3
import requests

BACKEND_URL = "http://localhost:8000"
PROJECT_ID = 8

# 查询API规范
print("查询API规范...")
response = requests.get(f"{BACKEND_URL}/api/v2/swagger/api-specs?project_id={PROJECT_ID}", timeout=10)
print(f"状态码: {response.status_code}")
if response.status_code == 200:
    specs = response.json()
    print(f"API规范数量: {len(specs)}")
    for spec in specs:
        print(f"  - ID: {spec.get('id')}, 名称: {spec.get('name')}, API数: {spec.get('api_count', 0)}")
else:
    print(f"响应: {response.text}")

# 查询API列表
print("\n查询API列表...")
response = requests.get(f"{BACKEND_URL}/api/v2/projects/{PROJECT_ID}/apis?limit=10", timeout=10)
print(f"状态码: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    apis = result.get("apis", [])
    total = result.get("total", 0)
    print(f"API总数: {total}")
    print(f"前10个API:")
    for api in apis[:10]:
        print(f"  - {api.get('method')} {api.get('path')} - {api.get('summary')}")
else:
    print(f"响应: {response.text}")
