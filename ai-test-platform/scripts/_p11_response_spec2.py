"""Phase 11B: 通过 V2 引擎分析蓝点接口响应规范 (使用 AuthManager Token)"""
import requests, json

BACKEND = "http://localhost:8000"
BLUEDOT = "https://dev-recycle.szhibu.com/dev-api/recycle"

test_apis = [
    # 分页接口
    {"name": "currency/page", "path": "/basic/basicCurrency/page", "body": {"pageNum": 1, "pageSize": 5}},
    {"name": "warehouse/page", "path": "/basic/basicWarehouseInfo/page", "body": {"pageNum": 1, "pageSize": 5}},
    {"name": "purchaseOrder/page", "path": "/purchaseOrder/page", "body": {"pageNum": 1, "pageSize": 5}},
    # 列表接口
    {"name": "currency/list", "path": "/basic/basicCurrency/list", "body": {}},
    {"name": "exchangeRate/list", "path": "/basic/basicExchangeRate/list", "body": {}},
    # 详情接口 (用假uuid)
    {"name": "currency/info", "path": "/basic/basicCurrency/info", "body": {"uuid": "00000000-0000-0000-0000-000000000000"}},
    # 不存在路径
    {"name": "nonexistent", "path": "/nonexistent/api/xyz", "body": {}},
]

print("=" * 80)
print("蓝点接口响应规范分析 (通过 V2 引擎, AuthManager 注入 Token)")
print("=" * 80)

# 先确认 Token 状态
r = requests.get(f"{BACKEND}/api/v2/execute/auth/status")
envs = r.json().get("envs", {})
if "default" in envs:
    print(f"Token: {envs['default']['type']}, expired={envs['default']['expired']}\n")
else:
    print("WARNING: No token set!\n")

for api in test_apis:
    r = requests.post(f"{BACKEND}/api/v2/execute", json={
        "base_url": BLUEDOT,
        "title": api["name"],
        "method": "POST",
        "path": api["path"],
        "body": api["body"],
        "assertions": [],
    })
    result = r.json().get("result", {})
    resp = result.get("response", {})
    body = resp.get("body", {}) or {}
    http_code = resp.get("status_code", 0)

    print(f"\n--- {api['name']} ---")
    print(f"  HTTP: {http_code}")
    if isinstance(body, dict):
        print(f"  body keys: {list(body.keys())[:15]}")
        print(f"  code: {body.get('code')}")
        print(f"  message: {body.get('message') or body.get('msg')}")
        data = body.get("data")
        if data is None:
            print(f"  data: null")
        elif isinstance(data, dict):
            print(f"  data type: dict, keys={list(data.keys())[:10]}")
            if "records" in data:
                recs = data["records"]
                print(f"  data.records: list[{len(recs)}]")
                if recs and isinstance(recs[0], dict):
                    print(f"  data.records[0] keys: {list(recs[0].keys())[:8]}")
            if "total" in data:
                print(f"  data.total: {data['total']}")
            if "pages" in data:
                print(f"  data.pages: {data['pages']}")
            if "current" in data:
                print(f"  data.current: {data['current']}")
            if "size" in data:
                print(f"  data.size: {data['size']}")
        elif isinstance(data, list):
            print(f"  data type: list[{len(data)}]")
            if data and isinstance(data[0], dict):
                print(f"  data[0] keys: {list(data[0].keys())[:8]}")
        else:
            print(f"  data type: {type(data).__name__}, value: {str(data)[:50]}")
    else:
        print(f"  body type: {type(body).__name__}")
        print(f"  body[:200]: {str(body)[:200]}")
