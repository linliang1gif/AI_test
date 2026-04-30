#!/usr/bin/env python3
import requests

# 测试生成测试用例API
print("测试生成测试用例API...")

# 创建一个测试文件
files = {
    'file': ('test_requirement.txt', b'Test requirement content', 'text/plain')
}

response = requests.post(
    "http://localhost:8000/api/testcases/generate",
    files=files
)

print(f"状态码: {response.status_code}")
print(f"响应: {response.json()}")
