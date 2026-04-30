#!/usr/bin/env python3
import requests
import json

BACKEND_URL = "http://localhost:8000"
API_SPEC_ID = 7  # 使用最新的

print(f"查询API规范详情 (ID: {API_SPEC_ID})...")
response = requests.get(f"{BACKEND_URL}/api/v2/swagger/api-specs/{API_SPEC_ID}", timeout=10)
print(f"状态码: {response.status_code}")

if response.status_code == 200:
    spec = response.json()
    print(f"\nAPI规范信息:")
    print(f"  ID: {spec.get('id')}")
    print(f"  项目ID: {spec.get('project_id')}")
    print(f"  API数量: {spec.get('api_count')}")
    print(f"  创建时间: {spec.get('created_at')}")
    
    # 查看spec_data
    spec_data = spec.get('spec_data')
    if spec_data:
        if isinstance(spec_data, str):
            spec_data = json.loads(spec_data)
        
        paths = spec_data.get('paths', {})
        print(f"\n  Paths数量: {len(paths)}")
        print(f"\n  前5个API:")
        for i, (path, methods) in enumerate(list(paths.items())[:5]):
            for method, details in methods.items():
                print(f"    {i+1}. {method.upper()} {path} - {details.get('summary', '')}")
else:
    print(f"响应: {response.text}")
