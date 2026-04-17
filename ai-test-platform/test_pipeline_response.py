"""查看Pipeline返回数据"""
import requests
import json

r = requests.post(
    "http://localhost:8000/api/pipeline/run",
    json={
        "requirement": "用户登录功能",
        "context": {"priority": "P1"}
    },
    timeout=30
)

print("Status Code:", r.status_code)
print("\nResponse:")
print(json.dumps(r.json(), indent=2, ensure_ascii=False))
