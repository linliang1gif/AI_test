#!/usr/bin/env python3
import requests

BACKEND_URL = "http://localhost:8000"
API_SPEC_ID = 7

print(f"从API规范生成测试用例 (API Spec ID: {API_SPEC_ID})...")
response = requests.post(
    f"{BACKEND_URL}/api/v2/swagger/generate-test-cases",
    json={"api_spec_id": API_SPEC_ID},
    timeout=60
)

print(f"状态码: {response.status_code}")
if response.status_code in [200, 201]:
    result = response.json()
    print(f"✓ 测试用例生成成功")
    print(f"  生成数量: {result.get('test_case_count', 0)}")
    print(f"  测试用例IDs: {result.get('test_case_ids', [])[:10]}...")
else:
    print(f"✗ 生成失败")
    print(f"响应: {response.text[:500]}")
