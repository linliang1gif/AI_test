import requests

# 测试API端点
url = "http://localhost:8000/api/v2/test/run-intelligent"
payload = {"test_case_ids": [2, 3, 4]}

print(f"测试: POST {url}")
print(f"请求体: {payload}")

try:
    r = requests.post(url, json=payload, timeout=10)
    print(f"\n状态码: {r.status_code}")
    print(f"响应: {r.text}")
except Exception as e:
    print(f"错误: {e}")
