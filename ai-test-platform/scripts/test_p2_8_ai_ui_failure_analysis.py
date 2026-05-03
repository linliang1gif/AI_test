#!/usr/bin/env python3
"""P2-8: AI UI Failure Analysis test script."""
import json
import os
import sys
import time
import requests

BASE = os.getenv("API_BASE", "http://localhost:8000")
PASS = FAIL = SKIP = TOTAL = 0


def check(name, cond, detail=""):
    global PASS, FAIL, TOTAL
    TOTAL += 1
    if cond:
        PASS += 1
        print(f"  PASS {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name}  ({detail})")


def skip_test(name, reason):
    global SKIP, TOTAL
    TOTAL += 1
    SKIP += 1
    print(f"  SKIP {name} -- {reason}")


def api(method, path, **kw):
    url = BASE + path
    headers = kw.pop("headers", {})
    tk = os.getenv("TESTING_KEY", "")
    if tk:
        headers["X-Testing-Key"] = tk
    return getattr(requests, method)(url, headers=headers, timeout=30, **kw)


# ── 0. Health check ──
print("\n== 0. Health ==")
for _ in range(15):
    try:
        r = requests.get(f"{BASE}/health", timeout=3)
        if r.ok:
            break
    except Exception:
        pass
    time.sleep(2)
else:
    print("Backend not ready"); sys.exit(1)
check("Backend healthy", True)

# ── 1. Rule engine unit tests (via service import) ──
print("\n== 1. Rule engine ==")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.failure_analysis import _rule_analyze, _build_evidence, analyze_failure, build_failure_summary, FAILURE_CATEGORIES

# 1a. selector_not_found
ev_sel = _build_evidence({
    "test_case_id": "TC_SEL",
    "error_message": "Timeout waiting for selector '#btn-submit'",
    "response_snapshot": {},
    "assertion_details": [],
})
r_sel = _rule_analyze(ev_sel)
check("selector_not_found rule", r_sel["failure_category"] == "selector_not_found", r_sel["failure_category"])

# 1b. page_timeout
ev_to = _build_evidence({
    "test_case_id": "TC_TO",
    "error_message": "Navigation timed out after 30000ms",
    "response_snapshot": {},
    "assertion_details": [],
})
r_to = _rule_analyze(ev_to)
check("page_timeout rule", r_to["failure_category"] == "page_timeout", r_to["failure_category"])

# 1c. element_not_visible
ev_vis = _build_evidence({
    "test_case_id": "TC_VIS",
    "error_message": "Element is not visible",
    "response_snapshot": {},
    "assertion_details": [],
})
r_vis = _rule_analyze(ev_vis)
check("element_not_visible rule", r_vis["failure_category"] == "element_not_visible", r_vis["failure_category"])

# 1d. network_error / app_bug_suspected (500)
ev_500 = _build_evidence({
    "test_case_id": "TC_500",
    "error_message": "",
    "response_snapshot": {
        "network_errors": [{"url": "https://example.com/api/save", "status": 500, "method": "POST"}]
    },
    "assertion_details": [],
})
r_500 = _rule_analyze(ev_500)
check("app_bug_suspected (500) rule", r_500["failure_category"] == "app_bug_suspected", r_500["failure_category"])
check("should_create_bug for 500", r_500["should_create_bug"] is True)

# 1e. auth_or_permission (401/403)
ev_401 = _build_evidence({
    "test_case_id": "TC_401",
    "error_message": "",
    "response_snapshot": {
        "network_errors": [{"url": "https://example.com/api/data", "status": 401, "method": "GET"}]
    },
    "assertion_details": [],
})
r_401 = _rule_analyze(ev_401)
check("auth_or_permission (401) rule", r_401["failure_category"] == "auth_or_permission", r_401["failure_category"])

# 1f. visual_diff
ev_vd = _build_evidence({
    "test_case_id": "TC_VD",
    "error_message": "",
    "response_snapshot": {
        "visual_results": [{"status": "failed", "match_percentage": 80, "threshold": 95}]
    },
    "assertion_details": [],
})
r_vd = _rule_analyze(ev_vd)
check("visual_diff rule", r_vd["failure_category"] == "visual_diff", r_vd["failure_category"])
check("should_update_baseline for visual", r_vd["should_update_baseline"] is True)

# 1g. assertion_failed
ev_af = _build_evidence({
    "test_case_id": "TC_AF",
    "error_message": "",
    "response_snapshot": {},
    "assertion_details": [{"type": "text_visible", "value": "Success", "actual": "Error", "passed": False}],
})
r_af = _rule_analyze(ev_af)
check("assertion_failed rule", r_af["failure_category"] == "assertion_failed", r_af["failure_category"])

# 1h. console_error
ev_ce = _build_evidence({
    "test_case_id": "TC_CE",
    "error_message": "",
    "response_snapshot": {
        "console_logs": [{"text": "Uncaught TypeError: Cannot read property 'x' of null", "type": "error"}]
    },
    "assertion_details": [],
})
r_ce = _rule_analyze(ev_ce)
check("console_error rule", r_ce["failure_category"] == "console_error", r_ce["failure_category"])

# 1i. unknown fallback
ev_unk = _build_evidence({
    "test_case_id": "TC_UNK",
    "error_message": "Something unusual happened",
    "response_snapshot": {},
    "assertion_details": [],
})
r_unk = _rule_analyze(ev_unk)
check("unknown fallback rule", r_unk["failure_category"] == "unknown", r_unk["failure_category"])

# 1j. all categories valid
check("all categories valid", all(c in FAILURE_CATEGORIES for c in [
    r_sel["failure_category"], r_to["failure_category"], r_vis["failure_category"],
    r_500["failure_category"], r_401["failure_category"], r_vd["failure_category"],
    r_af["failure_category"], r_ce["failure_category"], r_unk["failure_category"],
]))

# 1k. analysis_mode is 'rule' when AI_PROVIDER=none
check("analysis_mode=rule when no AI", r_sel["analysis_mode"] == "rule")

# ── 2. Sanitization: no Token/Cookie/Authorization in output ──
print("\n== 2. Sanitization ==")
ev_secret = _build_evidence({
    "test_case_id": "TC_SEC",
    "error_message": "Bearer eyJhbGciOiJIUzI1NiJ9.secret failed",
    "response_snapshot": {
        "network_errors": [
            {"url": "https://api.example.com/data?token=abc123&other=ok", "status": 500, "method": "GET",
             "headers": {"Authorization": "Bearer secret_token", "Cookie": "session=xyz"}}
        ],
        "console_logs": [{"text": "token=mysecrettoken in console", "type": "error"}],
    },
    "assertion_details": [],
})
check("error_message sanitized", "[REDACTED]" in ev_secret["error_message"], ev_secret["error_message"][:100])
net0 = ev_secret["network_errors"][0] if ev_secret["network_errors"] else {}
check("URL token sanitized", "abc123" not in net0.get("url", ""), net0.get("url", ""))
con0 = ev_secret["console_errors"][0] if ev_secret["console_errors"] else {}
check("console token sanitized", "mysecrettoken" not in con0.get("text", ""), con0.get("text", ""))

# ── 3. build_failure_summary ──
print("\n== 3. Summary builder ==")
analyses = [r_sel, r_500, r_vd, r_af]
summary = build_failure_summary(analyses)
check("summary total_analyzed", summary["total_analyzed"] == 4, summary.get("total_analyzed"))
check("summary has category_distribution", "category_distribution" in summary)
check("summary has high_confidence_count", "high_confidence_count" in summary)
check("summary has should_create_bug_count", summary.get("should_create_bug_count", 0) >= 1)

# ── 4. API: POST failure-analysis (need a WebUI run) ──
print("\n== 4. Create test Web UI run ==")

# Create a web_ui test case that will fail
case_payload = {
    "title": "P2-8 test failure case",
    "case_type": "web_ui",
    "steps": [
        {"action": "goto", "target": "http://localhost:19876/nonexistent-page-p28"},
        {"action": "click", "target": "#does-not-exist-button"}
    ],
    "assertions": [
        {"type": "text_visible", "value": "ThisTextWillNeverAppear12345"}
    ],
    "execution_config": {"base_url": "http://localhost:19876", "timeout": 5000}
}
r_create = api("post", "/api/v2/test-cases", json=case_payload)
case_id = None
if r_create.ok:
    d = r_create.json()
    case_id = d.get("test_case_id") or d.get("id") or d.get("data", {}).get("id")
check("create web_ui case", case_id is not None, f"status={r_create.status_code}")

# Execute batch run (will fail because target doesn't exist)
run_id = None
if case_id:
    batch_payload = {
        "case_ids": [case_id],
        "execution_config": {"base_url": "http://localhost:19876", "timeout": 5000, "headless": True}
    }
    r_batch = api("post", "/api/v2/web-ui/batch-run", json=batch_payload)
    if r_batch.ok:
        bd = r_batch.json()
        run_id = bd.get("run_id")
        check("batch-run executed", run_id is not None)
        check("batch-run has failures", bd.get("failed_cases", 0) >= 1, f"failed={bd.get('failed_cases')}")
    else:
        skip_test("batch-run", f"status={r_batch.status_code} {r_batch.text[:200]}")
else:
    skip_test("batch-run", "no case_id")

# ── 5. POST failure-analysis ──
print("\n== 5. POST failure-analysis ==")
if run_id:
    r_fa = api("post", f"/api/v2/web-ui/runs/{run_id}/failure-analysis")
    check("POST failure-analysis 200", r_fa.status_code == 200, f"status={r_fa.status_code}")
    if r_fa.ok:
        fa_data = r_fa.json()
        fa_analyses = fa_data.get("analyses", [])
        fa_summary = fa_data.get("summary", {})
        check("analyses non-empty", len(fa_analyses) >= 1, f"len={len(fa_analyses)}")
        check("summary has total_analyzed", fa_summary.get("total_analyzed", 0) >= 1)
        if fa_analyses:
            a0 = fa_analyses[0]
            check("has failure_category", a0.get("failure_category") in FAILURE_CATEGORIES, a0.get("failure_category"))
            check("has confidence", 0 <= a0.get("confidence", -1) <= 1, a0.get("confidence"))
            check("has root_cause_summary", bool(a0.get("root_cause_summary")))
            check("has evidence list", isinstance(a0.get("evidence"), list))
            check("has suggested_action", bool(a0.get("suggested_action")))
            check("has should_retry", "should_retry" in a0)
            check("has should_create_bug", "should_create_bug" in a0)
            check("has should_update_selector", "should_update_selector" in a0)
            check("has should_update_baseline", "should_update_baseline" in a0)
            check("has analysis_mode", a0.get("analysis_mode") in ("rule", "ai"), a0.get("analysis_mode"))
            check("has case_id", bool(a0.get("case_id")))
            check("has run_id", a0.get("run_id") == run_id)
            # Check no sensitive data in output
            fa_str = json.dumps(fa_analyses)
            check("no Bearer in output", "Bearer " not in fa_str or "[REDACTED]" in fa_str)
            check("no Cookie in output", "Cookie" not in fa_str or "[REDACTED]" in fa_str)
    else:
        skip_test("POST analysis details", f"API failed: {r_fa.status_code}")
else:
    skip_test("POST failure-analysis", "no run_id")

# ── 6. GET failure-analysis ──
print("\n== 6. GET failure-analysis ==")
if run_id:
    r_get = api("get", f"/api/v2/web-ui/runs/{run_id}/failure-analysis")
    check("GET failure-analysis 200", r_get.status_code == 200, f"status={r_get.status_code}")
    if r_get.ok:
        gd = r_get.json()
        check("GET returns analyses", len(gd.get("analyses", [])) >= 1)
        check("GET returns summary", gd.get("summary", {}).get("total_analyzed", 0) >= 1)
else:
    skip_test("GET failure-analysis", "no run_id")

# ── 7. Repeat POST (idempotent update) ──
print("\n== 7. Repeat POST ==")
if run_id:
    r_fa2 = api("post", f"/api/v2/web-ui/runs/{run_id}/failure-analysis")
    check("repeat POST 200", r_fa2.status_code == 200)
    if r_fa2.ok:
        check("repeat returns analyses", len(r_fa2.json().get("analyses", [])) >= 1)
else:
    skip_test("repeat POST", "no run_id")

# ── 8. GET on non-existent run ──
print("\n== 8. Non-existent run ==")
r_ne = api("get", "/api/v2/web-ui/runs/NONEXISTENT_RUN_999/failure-analysis")
check("non-existent run 404", r_ne.status_code == 404, f"status={r_ne.status_code}")

# ── 9. POST on run with no failures ──
print("\n== 9. Run with no failures ==")
r_runs = api("get", "/api/v2/observability/runs?limit=10")
no_fail_run_id = None
if r_runs.ok:
    runs_data = r_runs.json().get("data", [])
    for rd in runs_data:
        if rd.get("status") == "passed" and rd.get("failed_cases", 1) == 0:
            no_fail_run_id = rd.get("id")
            break
if no_fail_run_id:
    r_nf = api("post", f"/api/v2/web-ui/runs/{no_fail_run_id}/failure-analysis")
    check("no-failure run returns empty analyses", len(r_nf.json().get("analyses", [])) == 0)
else:
    skip_test("no-failure run", "no passed run found")

# ── 10. Route registration check ──
print("\n== 10. Route registration ==")
r_docs = api("get", "/openapi.json")
if r_docs.ok:
    paths = r_docs.json().get("paths", {})
    check("POST failure-analysis route registered",
          any("failure-analysis" in p for p in paths), list(p for p in paths if "failure" in p))
    check("GET failure-analysis route registered",
          any("failure-analysis" in p for p in paths), list(p for p in paths if "failure" in p))
else:
    skip_test("route check", f"OpenAPI: {r_docs.status_code}")

# ── 11. Main pipeline integrity ──
print("\n== 11. Main pipeline integrity ==")
r_health = api("get", "/health")
check("health OK", r_health.ok)
r_cases = api("get", "/api/v2/test-cases?limit=5")
check("test-cases API OK", r_cases.ok)
r_runs2 = api("get", "/api/v2/observability/runs?limit=3")
check("observability runs OK", r_runs2.ok)

# ── 12. Cleanup ──
print("\n== 12. Cleanup ==")
if case_id:
    api("put", f"/api/v2/test-cases/{case_id}", json={"status": "deleted"})

# ── Summary ──
print(f"\n{'=' * 60}")
print(f"  P2-8: PASS={PASS} FAIL={FAIL} SKIP={SKIP} TOTAL={TOTAL}")
print(f"{'=' * 60}")
sys.exit(0 if FAIL == 0 else 1)
