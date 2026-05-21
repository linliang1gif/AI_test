"""验证 Phase 8: Token 认证注入"""
import requests
import json

BASE = "http://localhost:8000"
BLUEDOT_URL = "https://dev-recycle.szhibu.com/dev-api/recycle"

TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdXBwbGllcklkIjoiIiwidXNlcl9uYW1lIjoibGRzaXQiLCJtb2JpbGUiOiIxMzU0MjY1ODk2MyIsImF2YXRhciI6bnVsbCwidXNlcklkIjoiMTE2ZDMyYTY0MGIwNGE1NWJkMTViMWI5MTBmY2Y3NzgiLCJ1dWlkIjoiZjI4Y2I1NTNlOWM4NDZmMzkzOTdkNmE1ZWNjZWY5NWYiLCJjbGllbnRfaWQiOiJkZXZfYmx1ZV9yZWN5Y2xlIiwidXJsIjpudWxsLCJyZWFsTmFtZSI6Imxkc2l0IiwiYXVkIjpbIkRFRkFVTFRfUkVTT1VSQ0VfSUQiXSwicGluIjoiMTAxNCIsInNjb3BlIjpbImFsbCJdLCJ3c3QiOiJ3c0xBQWN6TEFzREJ5QXZJd1FMS3lnc0J3c29Md2d2RHdzZ0FEQUROemNmT3dzakN3YzRQQWR3RDBjNEJDdENwQ3cvYUNxbmJDZ3pUREE4S3pnREx4d3dMeXNyTUNzTU14OEhBQU16RHpNUE5BY0FDeWdvTURBb0F3OG9BIiwiaWQiOjE5OTMxMzE3MjI5MTY4OTI2NzQsImV4cCI6MTc3Nzg4ODUwMSwianRpIjoiZjA2OTVkMWItNGNkMi00OWIxLWE3MGQtNGM0ZWE0ZGNiM2RmIiwiZW1haWwiOiIxMzU0MjY1ODk2M0BxcS5jb20ifQ.tqNrCe8FDnPCzIUF5hQnUbzKH95Rk3RwpeW9x7rQ52ZVr9dxDlAB7lu56aFdgZlmwlrh1waxl3p-qSwLCaCdYxK7h_MG36L4D_QpN9OlgWBi6KFg7ClnYLejUHfifONVdSJrqTxQ_yHN1SyJigBe3BDX9ASy5KSMBoeUoECkCkU"

# 1. 设置 Token
print("=== 1. 设置 Token ===")
resp = requests.post(f"{BASE}/api/v2/execute/auth/set-token", json={
    "token": TOKEN,
    "auth_type": "bearer",
})
print(f"  {resp.json()}")

# 2. 查看状态
print("\n=== 2. 认证状态 ===")
resp = requests.get(f"{BASE}/api/v2/execute/auth/status")
print(f"  {resp.json()}")

# 3. 带认证执行蓝点接口
print("\n=== 3. 带 Token 执行蓝点接口 ===")
resp = requests.post(f"{BASE}/api/v2/execute/batch", json={
    "base_url": BLUEDOT_URL,
    "cases": [
        {
            "title": "客户信息-分页(需认证)",
            "method": "POST",
            "path": "/davinci/crm/customer/page",
            "body": {"pageNum": 1, "pageSize": 5},
            "assertions": [
                {"type": "status_code", "expected": 200},
                {"type": "field_exists", "path": "data"},
            ]
        },
        {
            "title": "采购订单-分页(需认证)",
            "method": "POST",
            "path": "/purchaseOrder/page",
            "body": {"pageNum": 1, "pageSize": 5},
            "assertions": [
                {"type": "status_code", "expected": 200},
            ]
        },
        {
            "title": "采购订单-列表(需认证)",
            "method": "POST",
            "path": "/purchaseOrder/list",
            "body": {},
            "assertions": [
                {"type": "status_code", "expected": 200},
            ]
        },
    ]
})
data = resp.json()
for r in data["results"]:
    status = r["status"].upper()
    title = r["case_title"]
    http_code = r.get("response", {}).get("status_code", "N/A") if r.get("response") else "N/A"
    duration = r["duration_ms"]
    # Check if Authorization header was injected
    req_headers = r.get("request", {}).get("headers", {})
    has_auth = "Authorization" in req_headers
    print(f"  [{status:>6}] {title}  HTTP {http_code}  {duration:.0f}ms  Auth={has_auth}")
    if r.get("error_message"):
        print(f"          Error: {r['error_message'][:100]}")

summary = data["summary"]
print(f"\n汇总: {summary['passed']}/{summary['total']} 通过")
print("✅ Phase 8 认证注入验证完成")
