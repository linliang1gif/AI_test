"""Phase 11A: 构造 passed/failed/error 三个用例, 执行后输出 run_id 供浏览器验证"""
import requests, json

BACKEND = "http://localhost:8000"
BLUEDOT = "https://dev-recycle.szhibu.com/dev-api/recycle"

cases = [
    {
        "id": "p11-passed",
        "title": "[PASSED] 币别列表-正常查询",
        "method": "POST",
        "path": "/basic/basicCurrency/list",
        "body": {},
        "assertions": [
            {"type": "status_code", "expected": 200},
            {"type": "response_time", "expected": 5000},
            {"type": "field_exists", "path": "data"},
        ]
    },
    {
        "id": "p11-failed",
        "title": "[FAILED] 币别列表-断言失败(期望404)",
        "method": "POST",
        "path": "/basic/basicCurrency/list",
        "body": {},
        "assertions": [
            {"type": "status_code", "expected": 404},
            {"type": "field_exists", "path": "nonexistent_xyz"},
            {"type": "field_equals", "path": "code", "expected": 999},
        ]
    },
    {
        "id": "p11-error",
        "title": "[ERROR] 不可达地址-连接超时",
        "method": "GET",
        "path": "/test",
        "base_url": "http://192.168.255.255:9999",
        "assertions": [
            {"type": "status_code", "expected": 200},
        ]
    },
]

r = requests.post(f"{BACKEND}/api/v2/execute/batch", json={
    "base_url": BLUEDOT,
    "run_id": "p11-verify",
    "cases": cases,
})
data = r.json()
print(f"run_id: {data.get('run_id')}")
print(f"summary: {json.dumps(data.get('summary',{}), indent=2)}")
for res in data.get("results", []):
    s = res.get("status", "?")
    t = res.get("case_title", "?")
    http = res.get("response", {}).get("status_code", 0)
    dur = res.get("duration_ms", 0)
    err = res.get("error_message", "")
    asr = res.get("assertions", [])
    print(f"\n  [{s:>6}] {t}")
    print(f"    HTTP {http}, {dur:.0f}ms")
    if err:
        print(f"    error: {err[:80]}")
    for a in asr:
        print(f"    {a['type']:>15}: passed={a['passed']}  exp={a.get('expected')} act={a.get('actual','')}")
    # 检查请求头脱敏
    req = res.get("request", {})
    auth_header = req.get("headers", {}).get("Authorization", "")
    if auth_header:
        print(f"    Auth header present: {auth_header[:30]}...")

print(f"\n浏览器验证: http://localhost:5173/executor-v2")
print(f"在页面输入 run_id: p11-verify 查看结果详情")
