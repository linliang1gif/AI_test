#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P3-1: CI/CD 质量门禁 MVP — 自动化测试
覆盖: gate_config 加载, gate passed/failed, 各规则生效,
      skip/xfail policy, ci_quality_gate.py exit code, JSON 输出,
      Token 不泄露, 主链路不受影响
"""
import io, sys, os, json, time, subprocess, tempfile
if sys.stdout and getattr(sys.stdout, 'encoding', '').lower().replace('-', '') != 'utf8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr and getattr(sys.stderr, 'encoding', '').lower().replace('-', '') != 'utf8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import requests

BASE = os.getenv("TEST_BASE_URL", os.getenv("API_BASE", "http://localhost:8000"))
TESTING_KEY = os.getenv("TESTING_KEY", "")
PASS = FAIL = 0
results = []

def check(name, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name} — {detail}")
    results.append((name, ok))

def api(method, path, **kw):
    headers = kw.pop("headers", {})
    if TESTING_KEY:
        headers["X-Testing-Key"] = TESTING_KEY
    kw.setdefault("timeout", 30)
    return getattr(requests, method)(f"{BASE}{path}", headers=headers, **kw)

def section(title):
    print(f"\n{'─'*50}")
    print(f"▶ {title}")
    print(f"{'─'*50}")


# ════════════════════════════════════════════════
print("=" * 60)
print("  P3-1 CI/CD 质量门禁 MVP — 自动化测试")
print("=" * 60)
print(f"  Backend: {BASE}")

# Health check
r = api("get", "/health")
check("Backend healthy", r.status_code == 200)

# ════════════════════════════════════════════════
section("1. 默认配置接口")

r = api("get", "/api/v2/quality-gates/default-config")
check("GET default-config 200", r.status_code == 200)
cfg = r.json()
check("default-config has fail_on_any_failed", "fail_on_any_failed" in cfg)
check("default-config has skip_policy", cfg.get("skip_policy") == "warn")

# ════════════════════════════════════════════════
section("2. 准备测试数据 — 创建测试集 + 执行")

# Create a test case
case_payload = {
    "title": f"P3-1 Gate Test Case {int(time.time())}",
    "module": "gate_test",
    "priority": "critical",
    "case_type": "api",
    "steps": [{"action": "GET", "target": f"{BASE}/health"}],
    "expected": "status 200",
    "execution_config": {"method": "GET", "url": f"{BASE}/health"},
}
r = api("post", "/api/v2/test-cases", json=case_payload)
case_id = r.json().get("test_case_id") if r.status_code == 200 else None
check("Create test case for gate", case_id is not None)

# Create a suite
r = api("post", "/api/v2/test-suites", json={"name": "P3-1 Gate Suite", "suite_type": "smoke"})
suite_id = r.json().get("suite_id") if r.status_code == 200 else None
check("Create gate suite", suite_id is not None)

if suite_id and case_id:
    api("post", f"/api/v2/test-suites/{suite_id}/cases", json={"case_ids": [case_id]})

# Run suite
run_id = None
if suite_id:
    r = api("post", f"/api/v2/test-suites/{suite_id}/run", json={})
    check("Suite run 200", r.status_code == 200)
    run_id = r.json().get("run_id")
    check("Got run_id", run_id is not None)

# ════════════════════════════════════════════════
section("3. Gate Passed 场景")

if run_id:
    r = api("post", "/api/v2/quality-gates/evaluate", json={"run_id": run_id})
    check("Evaluate gate 200", r.status_code == 200)
    gate = r.json()
    check("gate_status == passed", gate.get("gate_status") == "passed")
    check("gate_failures empty", len(gate.get("gate_failures", [])) == 0)
    check("total_cases > 0", gate.get("total_cases", 0) > 0)
    check("passed_cases > 0", gate.get("passed_cases", 0) > 0)
    check("gate_config present", "gate_config" in gate)

# ════════════════════════════════════════════════
section("4. Gate Failed 场景 — fail_on_any_failed")

if run_id:
    # Use a custom config that will trigger failure based on existing data
    # First create a failing case - use a bad URL
    fail_payload = {
        "title": f"P3-1 Failing Case {int(time.time())}",
        "module": "gate_test",
        "priority": "critical",
        "case_type": "api",
        "steps": [{"action": "GET", "target": "http://localhost:19999/nonexistent"}],
        "expected": "status 200",
        "execution_config": {"method": "GET", "url": "http://localhost:19999/nonexistent"},
    }
    r = api("post", "/api/v2/test-cases", json=fail_payload)
    fail_case_id = r.json().get("test_case_id") if r.status_code == 200 else None

    # Create failing suite
    r = api("post", "/api/v2/test-suites", json={"name": "P3-1 Fail Suite", "suite_type": "smoke"})
    fail_suite_id = r.json().get("suite_id") if r.status_code == 200 else None
    if fail_suite_id and fail_case_id:
        api("post", f"/api/v2/test-suites/{fail_suite_id}/cases", json={"case_ids": [fail_case_id]})
        r = api("post", f"/api/v2/test-suites/{fail_suite_id}/run", json={})
        fail_run_id = r.json().get("run_id") if r.status_code == 200 else None
        if fail_run_id:
            r = api("post", "/api/v2/quality-gates/evaluate", json={
                "run_id": fail_run_id,
                "gate_config": {"fail_on_any_failed": True}
            })
            gate = r.json()
            check("fail_on_any_failed triggers gate failed", gate.get("gate_status") == "failed")
            rules = [f["rule"] for f in gate.get("gate_failures", [])]
            check("gate_failures contains fail_on_any_failed", "fail_on_any_failed" in rules)
        else:
            check("fail_on_any_failed triggers gate failed", False, "no fail_run_id")
            check("gate_failures contains fail_on_any_failed", False, "skipped")
    else:
        check("fail_on_any_failed triggers gate failed", False, "setup failed")
        check("gate_failures contains fail_on_any_failed", False, "skipped")

# ════════════════════════════════════════════════
section("5. fail_on_p0_failed 生效")

if run_id:
    # The failing case has priority=critical, so fail_on_p0_failed should fire
    if fail_run_id:
        r = api("post", "/api/v2/quality-gates/evaluate", json={
            "run_id": fail_run_id,
            "gate_config": {"fail_on_any_failed": False, "fail_on_p0_failed": True}
        })
        gate = r.json()
        rules = [f["rule"] for f in gate.get("gate_failures", [])]
        check("fail_on_p0_failed in failures", "fail_on_p0_failed" in rules)
    else:
        check("fail_on_p0_failed in failures", False, "no fail_run_id")

# ════════════════════════════════════════════════
section("6. performance_must_pass 生效")

if run_id:
    # With passing run, performance_must_pass should not trigger
    r = api("post", "/api/v2/quality-gates/evaluate", json={
        "run_id": run_id,
        "gate_config": {"fail_on_any_failed": False, "performance_must_pass": True}
    })
    gate = r.json()
    check("performance_must_pass no false positive", gate.get("gate_status") == "passed")

# ════════════════════════════════════════════════
section("7. skip_policy=warn 不阻断")

if run_id:
    r = api("post", "/api/v2/quality-gates/evaluate", json={
        "run_id": run_id,
        "gate_config": {"fail_on_any_failed": False, "skip_policy": "warn"}
    })
    gate = r.json()
    check("skip_policy=warn -> still passed", gate.get("gate_status") == "passed")

# ════════════════════════════════════════════════
section("8. skip_policy=fail 阻断 (需要有 skipped 用例)")

# Create a suite with a functional (manual/skipped) case
func_payload = {
    "title": f"P3-1 Manual Case {int(time.time())}",
    "module": "gate_test",
    "priority": "medium",
    "case_type": "functional",
    "steps": ["Manual step"],
    "expected": "Manual verification",
}
r = api("post", "/api/v2/test-cases", json=func_payload)
manual_case_id = r.json().get("test_case_id") if r.status_code == 200 else None
if manual_case_id:
    r = api("post", "/api/v2/test-suites", json={"name": "P3-1 Skip Suite", "suite_type": "smoke"})
    skip_suite_id = r.json().get("suite_id") if r.status_code == 200 else None
    if skip_suite_id:
        api("post", f"/api/v2/test-suites/{skip_suite_id}/cases", json={"case_ids": [manual_case_id]})
        r = api("post", f"/api/v2/test-suites/{skip_suite_id}/run", json={})
        skip_run_id = r.json().get("run_id") if r.status_code == 200 else None
        if skip_run_id:
            r = api("post", "/api/v2/quality-gates/evaluate", json={
                "run_id": skip_run_id,
                "gate_config": {"fail_on_any_failed": False, "skip_policy": "fail"}
            })
            gate = r.json()
            rules = [f["rule"] for f in gate.get("gate_failures", [])]
            check("skip_policy=fail blocks on skipped", "skip_policy" in rules)
        else:
            check("skip_policy=fail blocks on skipped", False, "no skip_run_id")
    else:
        check("skip_policy=fail blocks on skipped", False, "no skip_suite_id")
else:
    check("skip_policy=fail blocks on skipped", False, "no manual_case_id")

# ════════════════════════════════════════════════
section("9. xfail_policy=warn 不阻断")

if run_id:
    r = api("post", "/api/v2/quality-gates/evaluate", json={
        "run_id": run_id,
        "gate_config": {"fail_on_any_failed": False, "xfail_policy": "warn"}
    })
    gate = r.json()
    check("xfail_policy=warn -> passed", gate.get("gate_status") == "passed")

# ════════════════════════════════════════════════
section("10. nonexistent run_id -> 404")

r = api("post", "/api/v2/quality-gates/evaluate", json={"run_id": "NONEXISTENT_RUN"})
check("nonexistent run_id -> 404", r.status_code == 404)

# ════════════════════════════════════════════════
section("11. ci_quality_gate.py exit code 验证")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if suite_id:
    # Gate passed -> exit 0
    result = subprocess.run(
        [sys.executable, os.path.join(PROJECT_ROOT, "scripts", "ci_quality_gate.py"),
         "--suite-id", str(suite_id), "--base-url", BASE],
        capture_output=True, timeout=120,
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "TESTING": "true", "TESTING_KEY": TESTING_KEY},
        cwd=PROJECT_ROOT,
    )
    check("ci_quality_gate.py gate passed -> exit 0", result.returncode == 0,
          f"rc={result.returncode}")

if fail_suite_id:
    # Gate failed -> exit 1
    result = subprocess.run(
        [sys.executable, os.path.join(PROJECT_ROOT, "scripts", "ci_quality_gate.py"),
         "--suite-id", str(fail_suite_id), "--base-url", BASE, "--fail-on-gate-failed"],
        capture_output=True, timeout=120,
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "TESTING": "true", "TESTING_KEY": TESTING_KEY},
        cwd=PROJECT_ROOT,
    )
    check("ci_quality_gate.py gate failed -> exit 1", result.returncode == 1,
          f"rc={result.returncode}")

# ════════════════════════════════════════════════
section("12. JSON 输出文件")

if suite_id:
    output_path = os.path.join(PROJECT_ROOT, "data", "reports", "test_gate_result.json")
    result = subprocess.run(
        [sys.executable, os.path.join(PROJECT_ROOT, "scripts", "ci_quality_gate.py"),
         "--suite-id", str(suite_id), "--base-url", BASE,
         "--output", output_path],
        capture_output=True, timeout=120,
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "TESTING": "true", "TESTING_KEY": TESTING_KEY},
        cwd=PROJECT_ROOT,
    )
    check("JSON output file created", os.path.exists(output_path))
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        check("JSON has gate_status", "gate_status" in data)
        check("JSON has run_id", "run_id" in data)
        check("JSON has suite_summary", "suite_summary" in data)
        # Clean up
        os.remove(output_path)

# ════════════════════════════════════════════════
section("13. Token/Cookie 不泄露")

if suite_id:
    result = subprocess.run(
        [sys.executable, os.path.join(PROJECT_ROOT, "scripts", "ci_quality_gate.py"),
         "--suite-id", str(suite_id), "--base-url", BASE],
        capture_output=True, timeout=120,
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "TESTING": "true", "TESTING_KEY": TESTING_KEY},
        cwd=PROJECT_ROOT,
    )
    stdout = result.stdout.decode("utf-8", errors="replace")
    check("No TESTING_KEY in output", TESTING_KEY not in stdout or not TESTING_KEY)
    check("No Authorization in output", "authorization" not in stdout.lower())
    check("No Cookie in output", "cookie" not in stdout.lower() or "Cookie file" in stdout)

# ════════════════════════════════════════════════
section("14. 主链路不受影响")

r = api("get", "/health")
check("health endpoint", r.status_code == 200)

r = api("get", "/api/v2/test-cases", params={"limit": 1})
check("GET /api/v2/test-cases", r.status_code == 200)

r = api("get", "/api/v2/projects")
check("GET /api/v2/projects", r.status_code == 200)

r = api("get", "/api/v2/test-suites")
check("GET /api/v2/test-suites", r.status_code == 200)

# ════════════════════════════════════════════════
section("15. gate_config 文件加载")

config_path = os.path.join(PROJECT_ROOT, "configs", "quality_gate.json")
check("quality_gate.json exists", os.path.exists(config_path))
if os.path.exists(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    check("config has all required keys", all(k in cfg for k in ["fail_on_any_failed", "fail_on_p0_failed", "skip_policy", "xfail_policy"]))


# ════════════════════════════════════════════════
# Cleanup suites
for sid in [suite_id, fail_suite_id]:
    if sid:
        try:
            api("delete", f"/api/v2/test-suites/{sid}")
        except Exception:
            pass
if skip_suite_id:
    try:
        api("delete", f"/api/v2/test-suites/{skip_suite_id}")
    except Exception:
        pass

# ════════════════════════════════════════════════
print(f"\n{'=' * 60}")
print(f"  P3-1 CI Quality Gate: PASS={PASS} FAIL={FAIL} TOTAL={PASS+FAIL}")
print(f"  Pass rate: {round(PASS / max(PASS + FAIL, 1) * 100, 1)}%")
print(f"{'=' * 60}")

sys.exit(0 if FAIL == 0 else 1)
