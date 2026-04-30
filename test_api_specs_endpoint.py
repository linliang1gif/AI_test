#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API规范接口
"""

import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 80)
print("测试API规范接口")
print("=" * 80)

# 1. 获取所有API规范
print("\n[1/3] 获取所有API规范...")
try:
    response = requests.get(f"{BASE_URL}/api/v2/swagger/api-specs")
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"❌ 错误: {e}")

# 2. 获取项目8的API规范
print("\n[2/3] 获取项目8的API规范...")
try:
    response = requests.get(f"{BASE_URL}/api/v2/swagger/api-specs?project_id=8")
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    if isinstance(data, list) and len(data) > 0:
        print(f"\n✓ 找到 {len(data)} 个API规范")
        for spec in data:
            print(f"  - ID: {spec.get('id')}, API数量: {spec.get('api_count')}, 文件路径: {spec.get('raw_spec_path')}")
except Exception as e:
    print(f"❌ 错误: {e}")

# 3. 获取API规范7的详情
print("\n[3/3] 获取API规范7的详情...")
try:
    response = requests.get(f"{BASE_URL}/api/v2/swagger/api-specs/7")
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    if 'raw_spec_path' in data:
        print(f"\n✓ API规范文件路径: {data['raw_spec_path']}")
        print(f"  API数量: {data.get('api_count')}")
        print(f"  项目ID: {data.get('project_id')}")
except Exception as e:
    print(f"❌ 错误: {e}")

print("\n" + "=" * 80)
