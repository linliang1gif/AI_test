#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P2-10: 测试集管理 MVP 测试脚本
覆盖:
  - CRUD 测试集
  - 添加/移除用例
  - 执行测试集
  - suite_summary 验证
  - 安全控制验证
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import os, json, time, requests

BASE = os.getenv("TEST_BASE_URL", "http://localhost:8000")
API = f"{BASE}/api/v2/test-suites"
CASE_API = f"{BASE}/api/v2/test-cases"

results = []

def log(label, status, detail=""):
    icon = "PASS" if status else "FAIL"
    results.append((label, status))
    print(f"  [{icon}] {label}" + (f" - {detail}" if detail else ""))


def ensure_test_case(db_session=None):
    """Create a simple API test case for suite testing."""
    payload = {
        "title": f"Suite Test Case {int(time.time())}",
        "module": "suite_test",
        "priority": "medium",
        "case_type": "api",
        "steps": ["Send GET /health"],
        "expected": "200 OK",
        "execution_config": {
            "method": "GET",
            "url": f"{BASE}/health",
            "headers": {},
            "timeout": 10
        },
        "assertions": [{"type": "status_code", "expected": 200}]
    }
    r = requests.post(CASE_API, json=payload, timeout=10)
    if r.status_code == 200:
        d = r.json()
        if d.get("success") and d.get("test_case_id"):
            return d["test_case_id"]
    # fallback: try finding existing api case
    r2 = requests.get(f"{CASE_API}?limit=50", timeout=10)
    if r2.status_code == 200:
        data = r2.json()
        items = data if isinstance(data, list) else data.get("data", [])
        for item in items:
            if item.get("case_type") == "api" and item.get("execution_config"):
                return item["id"]
        if items:
            return items[0]["id"]
    return None


def test_create_suite():
    print("\n== 1. Create Suite ==")
    r = requests.post(API, json={
        "name": "P2-10 Smoke Suite",
        "description": "Auto test suite for P2-10",
        "suite_type": "smoke",
        "priority": "high",
    }, timeout=10)
    ok = r.status_code == 200 and r.json().get("success")
    suite_id = r.json().get("suite_id") if ok else None
    log("POST /test-suites -> create", ok, f"suite_id={suite_id}")
    return suite_id


def test_create_suite_invalid():
    print("\n== 1b. Create Suite Invalid ==")
    r = requests.post(API, json={
        "name": "Bad",
        "suite_type": "nonexistent",
    }, timeout=10)
    ok = r.status_code == 400
    log("POST invalid suite_type -> 400", ok, f"status={r.status_code}")


def test_list_suites():
    print("\n== 2. List Suites ==")
    r = requests.get(API, timeout=10)
    ok = r.status_code == 200 and "data" in r.json()
    total = r.json().get("total", 0)
    log("GET /test-suites -> list", ok, f"total={total}")


def test_get_suite(suite_id):
    print("\n== 3. Get Suite Detail ==")
    r = requests.get(f"{API}/{suite_id}", timeout=10)
    ok = r.status_code == 200 and "data" in r.json()
    log("GET /test-suites/{id} -> detail", ok)


def test_update_suite(suite_id):
    print("\n== 4. Update Suite ==")
    r = requests.put(f"{API}/{suite_id}", json={
        "name": "P2-10 Smoke Suite (Updated)",
        "priority": "medium",
    }, timeout=10)
    ok = r.status_code == 200 and r.json().get("success")
    log("PUT /test-suites/{id} -> update", ok)


def test_add_cases(suite_id, case_ids):
    print("\n== 5. Add Cases ==")
    r = requests.post(f"{API}/{suite_id}/cases", json={"case_ids": case_ids}, timeout=10)
    ok = r.status_code == 200 and r.json().get("success")
    added = r.json().get("added", [])
    log("POST /test-suites/{id}/cases -> add", ok, f"added={len(added)}")

    # duplicate add
    r2 = requests.post(f"{API}/{suite_id}/cases", json={"case_ids": case_ids}, timeout=10)
    skipped = r2.json().get("skipped", [])
    log("Duplicate add -> skipped", len(skipped) == len(case_ids), f"skipped={len(skipped)}")


def test_remove_case(suite_id, case_id):
    print("\n== 6. Remove Case ==")
    r = requests.delete(f"{API}/{suite_id}/cases/{case_id}", timeout=10)
    ok = r.status_code == 200 and r.json().get("success")
    log("DELETE /test-suites/{id}/cases/{cid}", ok)

    # re-add for run test
    requests.post(f"{API}/{suite_id}/cases", json={"case_ids": [case_id]}, timeout=10)


def test_run_suite(suite_id):
    print("\n== 7. Run Suite ==")
    r = requests.post(f"{API}/{suite_id}/run", json={}, timeout=30)
    ok = r.status_code == 200 and r.json().get("success")
    d = r.json()
    run_id = d.get("run_id")
    ss = d.get("suite_summary", {})
    log("POST /test-suites/{id}/run -> execute", ok, f"run_id={run_id}")
    log("suite_summary.suite_id present", ss.get("suite_id") == suite_id)
    log("suite_summary.total_cases > 0", ss.get("total_cases", 0) > 0, f"total={ss.get('total_cases')}")
    log("suite_summary has duration_ms", "duration_ms" in ss, f"duration={ss.get('duration_ms')}ms")
    return run_id


def test_run_empty_suite():
    print("\n== 7b. Run Empty Suite ==")
    r = requests.post(API, json={"name": "Empty Suite", "suite_type": "api"}, timeout=10)
    sid = r.json().get("suite_id")
    if not sid:
        log("Create empty suite for run test", False)
        return
    r2 = requests.post(f"{API}/{sid}/run", json={}, timeout=10)
    ok = r2.status_code == 400
    log("Run empty suite -> 400", ok, f"status={r2.status_code}")
    # cleanup
    requests.delete(f"{API}/{sid}", timeout=10)


def test_delete_suite(suite_id):
    print("\n== 8. Delete Suite ==")
    r = requests.delete(f"{API}/{suite_id}", timeout=10)
    ok = r.status_code == 200 and r.json().get("success")
    log("DELETE /test-suites/{id} -> soft delete", ok)

    # verify not in list
    r2 = requests.get(API, timeout=10)
    ids = [s["id"] for s in r2.json().get("data", [])]
    log("Deleted suite not in list", suite_id not in ids)


def test_suite_run_creates_test_run(run_id):
    print("\n== 9. Verify TestRun Record ==")
    if not run_id:
        log("TestRun check (no run_id)", False)
        return
    r = requests.get(f"{BASE}/api/v2/test-runs/{run_id}", timeout=10)
    if r.status_code == 200:
        data = r.json()
        trigger = data.get("trigger_type", "")
        log("TestRun trigger_type == suite", trigger == "suite", f"got={trigger}")
        summary = data.get("summary", "") or ""
        try:
            sj = json.loads(summary) if isinstance(summary, str) and summary else (summary if isinstance(summary, dict) else {})
            has_ss = "suite_summary" in (sj or {})
            log("TestRun.summary contains suite_summary", has_ss)
        except Exception as e:
            log("TestRun.summary JSON parse", False, str(e)[:100])
    else:
        log("TestRun fetch", False, f"status={r.status_code} body={r.text[:200]}")


def test_filter_by_type():
    print("\n== 10. Filter by suite_type ==")
    # create a regression suite
    requests.post(API, json={"name": "Regression Filter Test", "suite_type": "regression"}, timeout=10)
    r = requests.get(f"{API}?suite_type=regression", timeout=10)
    ok = r.status_code == 200
    data = r.json().get("data", [])
    all_reg = all(s["suite_type"] == "regression" for s in data) if data else True
    log("Filter suite_type=regression", ok and all_reg, f"count={len(data)}")


def test_suite_run_no_app_mode_pollution(suite_id):
    """Coverage item 1: mixed suite execution does NOT modify APP_MODE."""
    print("\n== 11. Suite run does not pollute APP_MODE ==")
    r1 = requests.get(f"{BASE}/health", timeout=5)
    mode_before = r1.json().get("app_mode", "mock")
    # run the suite
    requests.post(f"{API}/{suite_id}/run", json={}, timeout=30)
    r2 = requests.get(f"{BASE}/health", timeout=5)
    mode_after = r2.json().get("app_mode", "mock")
    log("APP_MODE unchanged after suite run", mode_before == mode_after, f"before={mode_before} after={mode_after}")


def test_suite_summary_in_report(run_id):
    """Coverage item 2: suite_summary does not break report persistence."""
    print("\n== 12. suite_summary report persistence ==")
    if not run_id:
        log("Report persistence (no run_id)", False)
        return
    r = requests.post(f"{BASE}/api/v2/test-runs/{run_id}/report", json={}, timeout=15)
    ok = r.status_code == 200
    log("Report generation for suite run", ok, f"status={r.status_code}")
    if ok:
        report_id = r.json().get("report_id")
        if report_id:
            r2 = requests.get(f"{BASE}/api/v2/reports/{report_id}", timeout=10)
            log("Report detail accessible", r2.status_code == 200)
        else:
            log("Report detail accessible", False, "no report_id")


def test_soft_delete_preserves_history(suite_id, run_id):
    """Coverage item 7: soft delete preserves history test_run."""
    print("\n== 13. Soft delete preserves historical test_run ==")
    if not run_id:
        log("Soft delete history (no run_id)", False)
        return
    # delete suite
    requests.delete(f"{API}/{suite_id}", timeout=10)
    # verify test_run still exists
    r = requests.get(f"{BASE}/api/v2/test-runs/{run_id}", timeout=10)
    log("Historical test_run survives suite soft-delete", r.status_code == 200, f"status={r.status_code}")


def test_functional_case_skipped():
    """Coverage item 3: functional cases in suite are marked skipped/manual."""
    print("\n== 14. Functional case marked manual/skipped ==")
    # create functional case
    payload = {
        "title": f"Functional Suite Case {int(time.time())}",
        "module": "suite_test",
        "priority": "medium",
        "case_type": "functional",
        "steps": ["Manual step 1"],
        "expected": "Manual verification",
    }
    r = requests.post(CASE_API, json=payload, timeout=10)
    func_case_id = r.json().get("test_case_id") if r.status_code == 200 else None
    if not func_case_id:
        log("Create functional case", False)
        return
    # create suite with functional case
    r2 = requests.post(API, json={"name": "Functional Test Suite", "suite_type": "mixed"}, timeout=10)
    sid = r2.json().get("suite_id")
    if not sid:
        log("Create suite for functional test", False)
        return
    requests.post(f"{API}/{sid}/cases", json={"case_ids": [func_case_id]}, timeout=10)
    # run suite
    r3 = requests.post(f"{API}/{sid}/run", json={}, timeout=30)
    ss = r3.json().get("suite_summary", {})
    skipped = ss.get("skipped_cases", 0)
    log("Functional case counted as skipped", skipped >= 1, f"skipped={skipped}")
    # cleanup
    requests.delete(f"{API}/{sid}", timeout=10)


def main():
    print("=" * 60)
    print("P2-10: Test Suite Management MVP - Test Script")
    print("=" * 60)
    print(f"Target: {BASE}")

    # health check
    try:
        hr = requests.get(f"{BASE}/health", timeout=5)
        print(f"Health: {hr.status_code}")
    except Exception as e:
        print(f"Health check failed: {e}")
        print("Server not reachable, aborting.")
        sys.exit(1)

    # ensure a test case exists
    case_id = ensure_test_case()
    if not case_id:
        print("FAIL: Could not create or find test case for suite testing")
        sys.exit(1)
    print(f"Using test case: {case_id}")

    # run tests
    suite_id = test_create_suite()
    test_create_suite_invalid()
    test_list_suites()

    if suite_id:
        test_get_suite(suite_id)
        test_update_suite(suite_id)
        test_add_cases(suite_id, [case_id])
        test_remove_case(suite_id, case_id)
        run_id = test_run_suite(suite_id)
        test_run_empty_suite()
        test_suite_run_creates_test_run(run_id)
        test_filter_by_type()
        test_suite_run_no_app_mode_pollution(suite_id)
        test_suite_summary_in_report(run_id)
        test_functional_case_skipped()
        test_soft_delete_preserves_history(suite_id, run_id)
        # Note: test_soft_delete_preserves_history soft-deletes suite_id,
        # so we skip the explicit test_delete_suite call (already done inside)
    else:
        print("SKIP: Suite creation failed, skipping dependent tests")
        for label in ["get", "update", "add_cases", "remove_case", "run", "run_empty", "run_record", "filter", "delete"]:
            log(f"Skipped: {label}", False, "suite_id is None")

    # summary
    print("\n" + "=" * 60)
    passed = sum(1 for _, s in results if s)
    failed = sum(1 for _, s in results if not s)
    print(f"P2-10 Results: {passed} PASS / {failed} FAIL (total {len(results)})")
    print("=" * 60)

    if failed > 0:
        print("\nFailed tests:")
        for label, s in results:
            if not s:
                print(f"  - {label}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
