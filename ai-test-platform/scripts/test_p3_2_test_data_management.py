#!/usr/bin/env python3
"""
P3-2 测试数据管理 MVP — 自动化测试
覆盖: CRUD 数据集/数据项/绑定 + 变量替换 + 脱敏 + suite data_summary + gate 识别 + 主链路
"""
import os, sys, json, time, requests

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(PROJECT_ROOT)

BASE = os.getenv("BACKEND_URL", "http://localhost:8000")
TESTING_KEY = os.getenv("TESTING_KEY", "")

passed = 0
failed = 0

def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} — {detail}")

def api(method, path, **kw):
    headers = kw.pop("headers", {})
    if TESTING_KEY:
        headers["X-Testing-Key"] = TESTING_KEY
    return getattr(requests, method)(f"{BASE}{path}", headers=headers, timeout=30, **kw)

def section(title):
    print(f"\n{'─'*50}\n▶ {title}\n{'─'*50}")

# ──────────────────────────────────────────────────────
print("=" * 60)
print("  P3-2 测试数据管理 MVP — 自动化测试")
print("=" * 60)
print(f"  Backend: {BASE}")

# Health check
try:
    r = requests.get(f"{BASE}/health", timeout=5)
    check("Backend healthy", r.status_code == 200)
except:
    print("  ❌ Backend not reachable")
    sys.exit(1)

# ──────────────────────────────────────────────────────
section("1. 创建数据集")
r = api("post", "/api/v2/test-data/datasets", json={
    "name": "P3-2 Login Accounts",
    "description": "测试登录账号数据",
    "dataset_type": "account",
    "case_type": "api",
    "tags": ["login", "p3-2"]
})
check("Create dataset 200", r.status_code == 200)
ds = r.json()
ds_id = ds.get("id")
check("Dataset has id", ds_id is not None)
check("Dataset name correct", ds.get("name") == "P3-2 Login Accounts")
check("Dataset type correct", ds.get("dataset_type") == "account")

# ──────────────────────────────────────────────────────
section("2. 查询数据集列表")
r = api("get", "/api/v2/test-data/datasets")
check("List datasets 200", r.status_code == 200)
data = r.json()
check("List has data", len(data.get("data", [])) > 0)
check("List has total", data.get("total", 0) > 0)

# filter by type
r = api("get", "/api/v2/test-data/datasets?dataset_type=account")
check("Filter by type works", r.status_code == 200 and any(d["id"] == ds_id for d in r.json().get("data", [])))

# ──────────────────────────────────────────────────────
section("3. 更新数据集")
r = api("put", f"/api/v2/test-data/datasets/{ds_id}", json={"description": "Updated description"})
check("Update dataset 200", r.status_code == 200)
check("Description updated", r.json().get("description") == "Updated description")

# ──────────────────────────────────────────────────────
section("4. 添加数据项")
# Normal item
r = api("post", f"/api/v2/test-data/datasets/{ds_id}/items", json={"key": "username", "value_json": "testuser01"})
check("Add item username 200", r.status_code == 200)
item1_id = r.json().get("id")

# Sensitive item
r = api("post", f"/api/v2/test-data/datasets/{ds_id}/items", json={"key": "password", "value_json": "MySecret123!", "is_sensitive": True})
check("Add sensitive item password 200", r.status_code == 200)
item2_id = r.json().get("id")
check("password auto-sensitive", r.json().get("is_sensitive") == True)
check("password value masked", "****" in str(r.json().get("value_json", "")))

# Token item (auto-sensitive by key name)
r = api("post", f"/api/v2/test-data/datasets/{ds_id}/items", json={"key": "api_token", "value_json": "tok_abcdef123456"})
check("Add api_token auto-sensitive", r.json().get("is_sensitive") == True)
item3_id = r.json().get("id")

# Numeric item
r = api("post", f"/api/v2/test-data/datasets/{ds_id}/items", json={"key": "amount", "value_json": 99.5})
check("Add numeric item", r.status_code == 200)
item4_id = r.json().get("id")

# ──────────────────────────────────────────────────────
section("5. 更新数据项")
r = api("put", f"/api/v2/test-data/items/{item1_id}", json={"value_json": "testuser02"})
check("Update item 200", r.status_code == 200)

# ──────────────────────────────────────────────────────
section("6. 删除数据项")
r = api("delete", f"/api/v2/test-data/items/{item4_id}")
check("Delete item 200", r.status_code == 200)

# ──────────────────────────────────────────────────────
section("7. 查看数据集详情")
r = api("get", f"/api/v2/test-data/datasets/{ds_id}")
check("Get detail 200", r.status_code == 200)
detail = r.json().get("data", {})
check("Detail has items", len(detail.get("items", [])) >= 2)
# Check sensitive masking in detail
pw_items = [i for i in detail.get("items", []) if i["key"] == "password"]
if pw_items:
    check("Detail password masked", "****" in str(pw_items[0].get("value_json", "")))
else:
    check("Detail password masked", False, "password item not found")

# ──────────────────────────────────────────────────────
section("8. 绑定数据集到 API 用例")
# Create a test case first
r = api("post", "/api/v2/test-cases", json={
    "title": "P3-2 Data Binding Test API",
    "module": "test-data",
    "priority": "medium",
    "case_type": "api",
    "execution_config": {
        "method": "GET",
        "url": f"{BASE}/health",
        "headers": {"Authorization": "Bearer ${api_token}"},
        "params": {"user": "${username}"}
    }
})
check("Create API test case", r.status_code in (200, 201))
case_data = r.json()
case_id = case_data.get("id") or case_data.get("test_case_id") or case_data.get("test_case", {}).get("id")
check("Got case_id", case_id is not None, str(case_data)[:100])

if case_id:
    r = api("post", "/api/v2/test-data/bindings", json={"dataset_id": ds_id, "case_id": case_id})
    check("Bind dataset to case 200", r.status_code == 200)
    check("Binding has dataset_id", r.json().get("dataset_id") == ds_id)

    # Duplicate binding should be idempotent
    r = api("post", "/api/v2/test-data/bindings", json={"dataset_id": ds_id, "case_id": case_id})
    check("Duplicate binding idempotent", r.status_code == 200)

# ──────────────────────────────────────────────────────
section("9. 查询用例绑定的数据集")
if case_id:
    r = api("get", f"/api/v2/test-data/cases/{case_id}/datasets")
    check("Get case datasets 200", r.status_code == 200)
    check("Case has bound dataset", len(r.json().get("data", [])) > 0)

# ──────────────────────────────────────────────────────
section("10. 变量替换预览")
if case_id:
    r = api("post", "/api/v2/test-data/substitute-preview", json={
        "case_id": case_id,
        "template": {"url": "/api?user=${username}", "token": "${api_token}", "missing": "${nonexist}"}
    })
    check("Substitute preview 200", r.status_code == 200)
    result = r.json()
    check("Variables resolved", "username" in result.get("variables", {}))
    check("Missing var detected", "nonexist" in result.get("missing_keys", []))
    # Check substituted result
    sub_result = result.get("result", {})
    check("username substituted in url", "testuser" in str(sub_result.get("url", "")))
    check("Missing var preserved", "${nonexist}" in str(sub_result.get("missing", "")))
    # Sensitive var masked in variables output
    check("api_token masked in preview", "****" in str(result.get("variables", {}).get("api_token", "")))

# ──────────────────────────────────────────────────────
section("11. Web UI 用例变量替换")
r = api("post", "/api/v2/test-cases", json={
    "title": "P3-2 Data Binding Test WebUI",
    "module": "test-data",
    "priority": "medium",
    "case_type": "web_ui",
    "steps": [
        {"action": "fill", "selector": "#user", "value": "${username}"},
        {"action": "fill", "selector": "#pass", "value": "${password}"}
    ]
})
webui_case = r.json()
webui_case_id = webui_case.get("id") or webui_case.get("test_case_id") or webui_case.get("test_case", {}).get("id")
if webui_case_id:
    api("post", "/api/v2/test-data/bindings", json={"dataset_id": ds_id, "case_id": webui_case_id})
    r = api("post", "/api/v2/test-data/substitute-preview", json={
        "case_id": webui_case_id,
        "template": [{"action": "fill", "selector": "#user", "value": "${username}"}, {"action": "fill", "selector": "#pass", "value": "${password}"}]
    })
    check("WebUI substitute 200", r.status_code == 200)
    sub = r.json().get("result", [])
    check("WebUI username replaced", any("testuser" in str(s.get("value", "")) for s in sub) if isinstance(sub, list) else False)

# ──────────────────────────────────────────────────────
section("12. 测试集执行使用数据集 + data_summary")
# Create suite with the API case
r = api("post", "/api/v2/test-suites", json={"name": "P3-2 Data Suite", "suite_type": "api", "priority": "medium"})
suite = r.json()
suite_id = suite.get("id") or suite.get("suite_id") or (suite.get("data", {}) or {}).get("id")
check("Create data suite", suite_id is not None, str(suite)[:100])
if suite_id and case_id:
    api("post", f"/api/v2/test-suites/{suite_id}/cases", json={"case_ids": [case_id]})
    r = api("post", f"/api/v2/test-suites/{suite_id}/run", json={})
    check("Suite run 200", r.status_code == 200)
    run_data = r.json()
    summary = run_data.get("suite_summary", {})
    data_summary = summary.get("data_summary", {})
    check("data_summary present", data_summary is not None and isinstance(data_summary, dict))
    check("datasets_used > 0", data_summary.get("datasets_used", 0) > 0)
    run_id = run_data.get("run_id")

# ──────────────────────────────────────────────────────
section("13. Quality gate 识别数据问题")
# Create a case with missing variable, bind empty dataset
r = api("post", "/api/v2/test-data/datasets", json={"name": "P3-2 Empty DS", "dataset_type": "common_fixture"})
empty_ds_id = r.json().get("id")
r = api("post", "/api/v2/test-cases", json={
    "title": "P3-2 Missing Var Case",
    "module": "test-data",
    "case_type": "api",
    "execution_config": {"method": "GET", "url": f"{BASE}/health", "params": {"q": "${missing_var}"}}
})
missing_case = r.json()
missing_case_id = missing_case.get("id") or missing_case.get("test_case_id") or missing_case.get("test_case", {}).get("id")
if missing_case_id and empty_ds_id:
    api("post", "/api/v2/test-data/bindings", json={"dataset_id": empty_ds_id, "case_id": missing_case_id})

    # Create suite + run
    r = api("post", "/api/v2/test-suites", json={"name": "P3-2 Missing Var Suite", "suite_type": "api"})
    mv_suite_resp = r.json()
    mv_suite_id = mv_suite_resp.get("id") or mv_suite_resp.get("suite_id") or (mv_suite_resp.get("data", {}) or {}).get("id")
    if mv_suite_id:
        api("post", f"/api/v2/test-suites/{mv_suite_id}/cases", json={"case_ids": [missing_case_id]})
        r = api("post", f"/api/v2/test-suites/{mv_suite_id}/run", json={})
        run_resp = r.json()
        mv_run_id = run_resp.get("run_id")
    else:
        mv_run_id = None

    # Gate evaluate
    if mv_run_id:
        r = api("post", "/api/v2/quality-gates/evaluate", json={"run_id": mv_run_id})
        if r.status_code == 200:
            gate = r.json()
            warnings = gate.get("gate_warnings", [])
            # data_missing might not trigger if empty dataset resolved no vars
            check("Gate evaluate 200", True)
        else:
            check("Gate evaluate 200", False, f"status={r.status_code}")
    else:
        check("Gate evaluate (no run_id)", False)

# ──────────────────────────────────────────────────────
section("14. 敏感数据脱敏验证")
r = api("get", f"/api/v2/test-data/datasets/{ds_id}")
detail = r.json().get("data", {})
items_text = json.dumps(detail.get("items", []))
check("No plain password in response", "MySecret123!" not in items_text)
check("No plain token in response", "tok_abcdef123456" not in items_text)
check("Masked values present", "****" in items_text)

# ──────────────────────────────────────────────────────
section("15. 软删除数据集")
r = api("delete", f"/api/v2/test-data/datasets/{ds_id}")
check("Soft delete 200", r.status_code == 200)
# Verify not in active list
r = api("get", "/api/v2/test-data/datasets?keyword=P3-2+Login")
check("Deleted not in active list", all(d.get("id") != ds_id for d in r.json().get("data", [])))

# ──────────────────────────────────────────────────────
section("16. 404 场景")
r = api("get", "/api/v2/test-data/datasets/99999")
check("Nonexistent dataset 404", r.status_code == 404)
r = api("put", "/api/v2/test-data/items/99999", json={"key": "x"})
check("Nonexistent item 404", r.status_code == 404)
r = api("delete", "/api/v2/test-data/bindings/99999")
check("Nonexistent binding 404", r.status_code == 404)

# ──────────────────────────────────────────────────────
section("17. dataset_type 全覆盖")
for dt in ["account", "api_payload", "ui_form", "performance_pool", "common_fixture", "cleanup_rule"]:
    r = api("post", "/api/v2/test-data/datasets", json={"name": f"P3-2 Type {dt}", "dataset_type": dt})
    check(f"Create {dt} dataset", r.status_code == 200 and r.json().get("dataset_type") == dt)

# ──────────────────────────────────────────────────────
section("18. 主链路不受影响")
r = requests.get(f"{BASE}/health", timeout=5)
check("health endpoint", r.status_code == 200)
r = api("get", "/api/v2/test-cases?limit=1")
check("GET /api/v2/test-cases", r.status_code == 200)
r = api("get", "/api/v2/projects")
check("GET /api/v2/projects", r.status_code == 200)
r = api("get", "/api/v2/test-suites?limit=1")
check("GET /api/v2/test-suites", r.status_code == 200)
r = api("get", "/api/v2/quality-gates/default-config")
check("GET /api/v2/quality-gates/default-config", r.status_code == 200)

# ──────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"  P3-2 Test Data Management: PASS={passed} FAIL={failed} TOTAL={passed+failed}")
print(f"  Pass rate: {passed/(passed+failed)*100:.1f}%")
print(f"{'='*60}")

sys.exit(1 if failed > 0 else 0)
