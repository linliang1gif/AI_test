"""Phase 11B: 分析蓝点接口响应规范"""
import requests, json

BLUEDOT = "https://dev-recycle.szhibu.com/dev-api/recycle"
TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdXBwbGllcklkIjoiIiwidXNlcl9uYW1lIjoibGRzaXQiLCJtb2JpbGUiOiIxMzU0MjY1ODk2MyIsImF2YXRhciI6bnVsbCwidXNlcklkIjoiMTE2ZDMyYTY0MGIwNGE1NWJkMTViMWI5MTBmY2Y3NzgiLCJ1dWlkIjoiZjI4Y2I1NTNlOWM4NDZmMzkzOTdkNmE1ZWNjZWY5NWYiLCJjbGllbnRfaWQiOiJkZXZfYmx1ZV9yZWN5Y2xlIiwidXJsIjpudWxsLCJyZWFsTmFtZSI6Imxkc2l0IiwiYXVkIjpbIkRFRkFVTFRfUkVTT1VSQ0VfSUQiXSwicGluIjoiMTAxNCIsInNjb3BlIjpbImFsbCJdLCJ3c3QiOiJ3c0xBQWN6TEFzREJ5QXZJd1FMS3lnc0J3c29Nd2d2RHdzZ0FEQUROemNmT3dzakN3YzRQQWR3RDBjNEJDdENwQ3cvYUNxbmJDZ3pUREE4S3pnREx4d3dMeXNyTUNzTU14OEhBQU16RHpNUE5BY0FDeWdvTURBb0F3OG9BIiwiaWQiOjE5OTMxMzE3MjI5MTY4OTI2NzQsImV4cCI6MTc3Nzg4ODUwMSwianRpIjoiZjA2OTVkMWItNGNkMi00OWIxLWE3MGQtNGM0ZWE0ZGNiM2RmIiwiZW1haWwiOiIxMzU0MjY1ODk2M0BxcS5jb20ifQ.tqNrCe8FDnPCzIUF5hQnUbzKH95Rk3RwpeW9x7rQ52ZVr9dxDlAB7lu56aFdgZlmwlrh1waxl3p-qSwLCaCdYxK7h_MG36L4D_QpN9OlgWBi6KFg7ClnYLejUHfifONVdSJrqTxQ_yHN1SyJigBe3BDX9ASy5KSMBoeUoECkCkU"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

test_apis = [
    # 分页接口
    {"name": "currency/page", "method": "POST", "path": "/basic/basicCurrency/page", "body": {"pageNum": 1, "pageSize": 5}},
    {"name": "warehouse/page", "method": "POST", "path": "/basic/basicWarehouseInfo/page", "body": {"pageNum": 1, "pageSize": 5}},
    {"name": "purchaseOrder/page", "method": "POST", "path": "/purchaseOrder/page", "body": {"pageNum": 1, "pageSize": 5}},
    # 列表接口
    {"name": "currency/list", "method": "POST", "path": "/basic/basicCurrency/list", "body": {}},
    {"name": "exchangeRate/list", "method": "POST", "path": "/basic/basicExchangeRate/list", "body": {}},
    # 详情接口
    {"name": "currency/info", "method": "POST", "path": "/basic/basicCurrency/info", "body": {"uuid": "00000000-0000-0000-0000-000000000000"}},
    # 不存在路径
    {"name": "nonexistent", "method": "POST", "path": "/nonexistent/api/xyz", "body": {}},
    # 无Token (单独请求)
    {"name": "noauth/page", "method": "POST", "path": "/purchaseOrder/page", "body": {"pageNum": 1, "pageSize": 5}, "no_auth": True},
]

print("=" * 80)
print("蓝点接口响应规范分析")
print("=" * 80)

results = []
for api in test_apis:
    headers = {} if api.get("no_auth") else HEADERS
    headers["Content-Type"] = "application/json"
    url = BLUEDOT + api["path"]
    try:
        r = requests.request(api["method"], url, json=api["body"], headers=headers, timeout=10)
        body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
    except Exception as e:
        body = {"_error": str(e)}
        r = type('R', (), {'status_code': 0})()

    info = {
        "name": api["name"],
        "http_status": r.status_code,
        "body_keys": list(body.keys()) if isinstance(body, dict) else [],
        "code": body.get("code"),
        "message": body.get("message") or body.get("msg"),
        "data_type": type(body.get("data")).__name__ if "data" in body else "missing",
        "has_total": "total" in body,
        "has_rows": "rows" in body,
        "has_records": "records" in body,
        "has_pageNum": "pageNum" in body,
        "has_list": "list" in body,
    }

    # 检查 data 里的分页结构
    data = body.get("data")
    if isinstance(data, dict):
        info["data_keys"] = list(data.keys())[:10]
        if "records" in data:
            info["data_has_records"] = True
            info["data_records_type"] = type(data["records"]).__name__
        if "total" in data:
            info["data_has_total"] = True
        if "rows" in data:
            info["data_has_rows"] = True
    elif isinstance(data, list):
        info["data_list_len"] = len(data)
        if data:
            info["data_item_keys"] = list(data[0].keys())[:8] if isinstance(data[0], dict) else []

    results.append(info)
    print(f"\n--- {api['name']} ---")
    print(f"  HTTP: {info['http_status']}")
    print(f"  body keys: {info['body_keys']}")
    print(f"  code: {info['code']}")
    print(f"  message: {info['message']}")
    print(f"  data type: {info['data_type']}")
    for k, v in info.items():
        if k.startswith("data_") or k.startswith("has_"):
            print(f"  {k}: {v}")

# 总结
print("\n" + "=" * 80)
print("规范总结")
print("=" * 80)

codes = set(r["code"] for r in results if r["code"] is not None)
print(f"所有 code 值: {sorted(codes)}")

msg_fields = set()
for r in results:
    for k in r["body_keys"]:
        if k in ("message", "msg"):
            msg_fields.add(k)
print(f"消息字段: {msg_fields}")

data_types = set(r["data_type"] for r in results)
print(f"data 字段类型: {data_types}")
