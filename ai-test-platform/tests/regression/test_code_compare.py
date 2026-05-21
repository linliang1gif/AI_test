import requests

BASE = "http://127.0.0.1:8001"

# 1. Test reports list (should be empty)
r = requests.get(f"{BASE}/api/v2/code-compare/reports")
print(f"GET reports: {r.status_code} -> {r.json()}")

# 2. Test cache requirement
r = requests.post(f"{BASE}/api/v2/code-compare/cache-requirement", json={
    "features": [{"name": "新增付款单"}, {"name": "审核付款单"}],
    "rules": ["金额不能为负", "审核后不可修改"],
    "modules": [],
    "fields": [],
    "axure_notes": [],
    "stats": {"features": 2, "rules": 2},
})
print(f"POST cache-requirement: {r.status_code} -> {r.json()}")
