#!/usr/bin/env python3
"""
P3-3A 测试数据增强与清理机制 — 专项测试
覆盖: 健康检查 / 数据集 clone / cleanup_rule / 执行前校验 / 执行后清理 / 质量门禁增强
"""
import sys, os, time, json, requests

BASE = os.getenv("BASE_URL", "http://localhost:8000")
PASS = 0
FAIL = 0
RESULTS = []


def api(method, path, **kw):
    return getattr(requests, method)(f"{BASE}{path}", timeout=30, **kw)


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        RESULTS.append(("PASS", name))
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        RESULTS.append(("FAIL", name, detail))
        print(f"  ❌ {name}  {detail[:120]}")


print("=" * 60)
print("P3-3A 测试数据增强与清理机制")
print("=" * 60)

# ── Section 1: 健康检查 — 正常数据集 ──
print("\n▶ Section 1: 健康检查 - 正常数据集")
r = api("post", "/api/v2/test-data/datasets", json={"name": "P3-3A Valid DS", "dataset_type": "common_fixture", "case_type": "api"})
ds = r.json()
ds_id = ds.get("id")
check("Create normal dataset", ds_id is not None)
# 添加一些数据项
api("post", f"/api/v2/test-data/datasets/{ds_id}/items", json={"key": "server", "value_json": "localhost"})
api("post", f"/api/v2/test-data/datasets/{ds_id}/items", json={"key": "port", "value_json": "8080"})
r = api("post", f"/api/v2/test-data/datasets/{ds_id}/validate")
check("Validate 200", r.status_code == 200)
vr = r.json()
check("Valid = true", vr.get("valid") is True)
check("No errors", len(vr.get("errors", [])) == 0)

# ── Section 2: 空数据集健康检查 ──
print("\n▶ Section 2: 空数据集健康检查")
r = api("post", "/api/v2/test-data/datasets", json={"name": "P3-3A Empty DS", "dataset_type": "common_fixture"})
empty_id = r.json().get("id")
r = api("post", f"/api/v2/test-data/datasets/{empty_id}/validate")
vr = r.json()
check("Empty DS valid=true (no errors)", vr.get("valid") is True)
check("Empty DS has warnings", len(vr.get("warnings", [])) > 0)
has_empty_warn = any("无数据项" in w for w in vr.get("warnings", []))
check("Warning mentions empty", has_empty_warn)

# ── Section 3: account 缺 password 检查 ──
print("\n▶ Section 3: account 类型缺 password")
r = api("post", "/api/v2/test-data/datasets", json={"name": "P3-3A Account No Pass", "dataset_type": "account"})
acc_id = r.json().get("id")
api("post", f"/api/v2/test-data/datasets/{acc_id}/items", json={"key": "username", "value_json": "admin"})
r = api("post", f"/api/v2/test-data/datasets/{acc_id}/validate")
vr = r.json()
check("Account valid=true (no errors, just warnings)", vr.get("valid") is True)
has_pass_warn = any("password" in w.lower() for w in vr.get("warnings", []))
check("Warning about missing password", has_pass_warn)

# ── Section 4: 敏感字段识别 ──
print("\n▶ Section 4: 敏感字段识别")
r = api("post", "/api/v2/test-data/datasets", json={"name": "P3-3A Sensitive", "dataset_type": "common_fixture"})
sens_id = r.json().get("id")
api("post", f"/api/v2/test-data/datasets/{sens_id}/items", json={"key": "api_token", "value_json": "tok_secret_abc123"})
api("post", f"/api/v2/test-data/datasets/{sens_id}/items", json={"key": "normal_key", "value_json": "hello"})
r = api("post", f"/api/v2/test-data/datasets/{sens_id}/validate")
vr = r.json()
check("Sensitive fields detected", "api_token" in vr.get("sensitive_fields", []))

# ── Section 5: 绑定已删除用例检查 ──
print("\n▶ Section 5: 绑定已删除用例检查")
# 创建一个测试用例
r = api("post", "/api/v2/test-cases", json={"title": "P3-3A Bind Test Case", "case_type": "api", "priority": "low",
    "execution_config": {"method": "GET", "url": f"{BASE}/health"}})
tc_resp = r.json()
tc_id = tc_resp.get("id") or tc_resp.get("test_case_id") or tc_resp.get("test_case", {}).get("id")
check("Create test case for binding", tc_id is not None, str(tc_resp)[:100])
if tc_id and ds_id:
    api("post", "/api/v2/test-data/bindings", json={"dataset_id": ds_id, "case_id": tc_id})
    r = api("post", f"/api/v2/test-data/datasets/{ds_id}/validate")
    vr = r.json()
    check("Bound case exists -> valid=true", vr.get("valid") is True)

# ── Section 6: 数据集 clone ──
print("\n▶ Section 6: 数据集 clone")
r = api("post", f"/api/v2/test-data/datasets/{ds_id}/clone")
check("Clone 200", r.status_code == 200)
clone = r.json()
clone_id = clone.get("id")
check("Clone has new id", clone_id is not None and clone_id != ds_id)
check("Clone name has -copy", "-copy" in clone.get("name", ""))
check("Clone items copied", clone.get("items_copied", 0) >= 2)
check("Clone bindings not copied (default)", clone.get("bindings_copied", 0) == 0)

# clone with bindings
if tc_id:
    r = api("post", f"/api/v2/test-data/datasets/{ds_id}/clone?copy_bindings=true")
    clone2 = r.json()
    check("Clone with bindings", clone2.get("bindings_copied", 0) > 0)

# ── Section 7: cleanup_rule dry-run ──
print("\n▶ Section 7: cleanup_rule dry-run")
r = api("post", "/api/v2/test-data/datasets", json={"name": "P3-3A Cleanup Rule", "dataset_type": "cleanup_rule"})
cleanup_id = r.json().get("id")
api("post", f"/api/v2/test-data/datasets/{cleanup_id}/items", json={
    "key": "delete_temp",
    "value_json": {"method": "DELETE", "url": "/api/v2/test-data/datasets/99999"}
})
r = api("post", "/api/v2/test-data/cleanup/run", json={"dataset_id": cleanup_id, "case_id": "", "allow_cleanup": False})
check("Cleanup dry-run 200", r.status_code == 200)
cr = r.json()
check("Cleanup status=dry_run", cr.get("status") == "dry_run")

# ── Section 8: real 模式 cleanup 默认拦截 ──
print("\n▶ Section 8: cleanup allow=true (mock mode, safe)")
r = api("post", "/api/v2/test-data/cleanup/run", json={"dataset_id": cleanup_id, "case_id": "", "allow_cleanup": True})
cr = r.json()
check("Cleanup allow=true returns result", cr.get("status") in ("completed", "blocked"))

# ── Section 9: cleanup 禁止清理关键路径 ──
print("\n▶ Section 9: cleanup 禁止 forbidden patterns")
r = api("post", "/api/v2/test-data/datasets", json={"name": "P3-3A Forbidden Cleanup", "dataset_type": "cleanup_rule"})
forbidden_id = r.json().get("id")
api("post", f"/api/v2/test-data/datasets/{forbidden_id}/items", json={
    "key": "bad_cleanup",
    "value_json": {"method": "DELETE", "url": "/data/test_platform.db"}
})
r = api("post", "/api/v2/test-data/cleanup/run", json={"dataset_id": forbidden_id, "case_id": "", "allow_cleanup": True})
cr = r.json()
has_blocked = any(x.get("status") == "blocked" for x in cr.get("results", []))
check("Forbidden pattern blocked", cr.get("status") == "completed" and has_blocked)

# ── Section 10: performance_pool 数量不足 ──
print("\n▶ Section 10: performance_pool 数量不足检查")
r = api("post", "/api/v2/test-data/datasets", json={"name": "P3-3A Perf Pool", "dataset_type": "performance_pool"})
perf_id = r.json().get("id")
api("post", f"/api/v2/test-data/datasets/{perf_id}/items", json={"key": "user1", "value_json": "val1"})
r = api("post", f"/api/v2/test-data/datasets/{perf_id}/validate")
vr = r.json()
has_perf_warn = any("数据量不足" in w for w in vr.get("warnings", []))
check("Performance pool insufficient warning", has_perf_warn)

# ── Section 11: 测试集执行前数据校验 + data_summary ──
print("\n▶ Section 11: 测试集执行 + data_summary validation fields")
if tc_id:
    # 创建测试集
    r = api("post", "/api/v2/test-suites", json={"name": "P3-3A Validation Suite", "suite_type": "api", "priority": "medium"})
    suite = r.json()
    suite_id = suite.get("id") or suite.get("suite_id") or (suite.get("data", {}) or {}).get("id")
    check("Create suite", suite_id is not None, str(suite)[:100])
    if suite_id:
        api("post", f"/api/v2/test-suites/{suite_id}/cases", json={"case_ids": [tc_id]})
        r = api("post", f"/api/v2/test-suites/{suite_id}/run", json={})
        check("Suite run 200", r.status_code == 200)
        run_data = r.json()
        summary = run_data.get("suite_summary", {})
        ds_summary = summary.get("data_summary", {})
        check("data_summary present", isinstance(ds_summary, dict))
        check("data_validation_errors key present", "data_validation_errors" in ds_summary)
        check("cleanup_results key present", "cleanup_results" in ds_summary)
        check("cleanup_failed key present", "cleanup_failed" in ds_summary)
        run_id = run_data.get("run_id")
    else:
        run_id = None
else:
    run_id = None

# ── Section 12: quality gate 识别 data_validation_failed ──
print("\n▶ Section 12: quality gate data_validation_failed / cleanup_failed")
# Construct a fake suite_summary with validation errors
fake_summary = {
    "total_cases": 10,
    "passed_cases": 8,
    "failed_cases": 2,
    "skipped_cases": 0,
    "data_summary": {
        "datasets_used": 1,
        "missing_variables": 0,
        "missing_variable_names": [],
        "data_binding_errors": 0,
        "data_validation_errors": 3,
        "data_validation_messages": ["绑定数据集 999 不存在或已归档"],
        "cleanup_results": [],
        "cleanup_failed": 0,
    }
}
r = api("post", "/api/v2/quality-gates/evaluate-summary", json={"suite_summary": fake_summary, "gate_config": {"data_validation_policy": "fail"}})
check("Gate evaluate 200", r.status_code == 200, str(r.text[:200]))
gate = r.json()
check("Gate status=failed (data_validation)", gate.get("gate_status") == "failed", str(gate)[:200])
has_dv_rule = any(f.get("rule") == "data_validation_failed" for f in gate.get("gate_failures", []))
check("Gate has data_validation_failed rule", has_dv_rule, str(gate.get("gate_failures", []))[:200])

# Test with warn policy
r = api("post", "/api/v2/quality-gates/evaluate-summary", json={"suite_summary": fake_summary, "gate_config": {"data_validation_policy": "warn"}})
gate2 = r.json()
has_dv_warn = any(w.get("rule") == "data_validation_failed" for w in gate2.get("gate_warnings", []))
check("Gate data_validation as warning (warn policy)", has_dv_warn, str(gate2.get("gate_warnings", []))[:200])

# Test cleanup_failed
fake_summary2 = dict(fake_summary)
fake_summary2["data_summary"] = {
    **fake_summary["data_summary"],
    "data_validation_errors": 0,
    "cleanup_failed": 2,
}
r = api("post", "/api/v2/quality-gates/evaluate-summary", json={"suite_summary": fake_summary2, "gate_config": {"cleanup_failure_policy": "fail"}})
gate3 = r.json()
has_cf_rule = any(f.get("rule") == "cleanup_failed" for f in gate3.get("gate_failures", []))
check("Gate cleanup_failed as failure (fail policy)", has_cf_rule, str(gate3.get("gate_failures", []))[:200])

r = api("post", "/api/v2/quality-gates/evaluate-summary", json={"suite_summary": fake_summary2, "gate_config": {"cleanup_failure_policy": "warn"}})
gate4 = r.json()
has_cf_warn = any(w.get("rule") == "cleanup_failed" for w in gate4.get("gate_warnings", []))
check("Gate cleanup_failed as warning (warn policy)", has_cf_warn, str(gate4.get("gate_warnings", []))[:200])

# ── Section 13: 主链路不受影响 ──
print("\n▶ Section 13: 主链路检查")
r = api("get", "/health")
check("Health endpoint", r.status_code == 200)
r = api("get", "/api/v2/test-data/datasets")
check("Test data list", r.status_code == 200)
r = api("get", "/api/v2/test-cases")
check("Test cases list", r.status_code == 200)
r = api("get", "/api/v2/test-suites")
check("Test suites list", r.status_code == 200)
r = api("get", "/api/v2/quality-gates/default-config")
check("Quality gate config", r.status_code == 200)

# ── Section 14: 敏感数据脱敏边界确认 ──
print("\n▶ Section 14: 敏感数据脱敏边界")
r = api("get", f"/api/v2/test-data/datasets/{sens_id}")
detail = r.json().get("data", {})
items = detail.get("items", [])
token_item = next((i for i in items if i["key"] == "api_token"), None)
if token_item:
    check("API response masks sensitive value", "****" in str(token_item.get("value_json", "")))
    check("Sensitive item marked is_sensitive", token_item.get("is_sensitive") is True)
else:
    check("Token item found", False, "api_token item not in response")
normal_item = next((i for i in items if i["key"] == "normal_key"), None)
if normal_item:
    check("Normal value not masked", "hello" in str(normal_item.get("value_json", "")))
else:
    check("Normal item found", False)

# ── Section 15: 非 cleanup_rule 数据集不执行清理 ──
print("\n▶ Section 15: 非 cleanup_rule 不执行清理")
r = api("post", "/api/v2/test-data/cleanup/run", json={"dataset_id": ds_id, "case_id": "", "allow_cleanup": True})
cr = r.json()
check("Non-cleanup_rule skipped", cr.get("status") == "skipped")

# ── Summary ──
print("\n" + "=" * 60)
print(f"P3-3A 测试结果: {PASS} PASS / {FAIL} FAIL (total={PASS + FAIL})")
print("=" * 60)

if FAIL > 0:
    print("\n❌ 失败项:")
    for r in RESULTS:
        if r[0] == "FAIL":
            print(f"  ❌ {r[1]}  {r[2] if len(r) > 2 else ''}")
    sys.exit(1)
else:
    print("\n🎉 All tests passed!")
    sys.exit(0)
