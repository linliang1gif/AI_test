#!/usr/bin/env python3
import requests

# 测试绑定API
response = requests.post(
    "http://localhost:8000/api/test-cases/1/bind-dataset",
    json={"dataset_id": "test123"}
)

print(f"状态码: {response.status_code}")
print(f"响应: {response.text}")
