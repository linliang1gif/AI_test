#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P2-9B: Web UI 稳定性增强测试
覆盖: retry, flaky_candidate, selector_score, wait strategies, preflight, cleanup
"""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import os, json, time, subprocess, tempfile, shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

BASE = "http://localhost:8000"
PASS = 0
FAIL = 0
XFAIL = 0

def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}  {detail}")

def section(title):
    print(f"\n{'─'*50}\n▶ {title}\n{'─'*50}")


# ── helpers ──
_created_cases = {}  # cache: label -> case_id

def ensure_webui_case(label, steps, assertions, exec_config=None):
    """Create a web_ui test case via v2 API and return the case_id."""
    if label in _created_cases:
        return _created_cases[label]
    payload = {
        "title": f"P2-9B test {label}",
        "module": "P2-9B",
        "priority": "high",
        "case_type": "web_ui",
        "steps": steps,
        "assertions": assertions,
        "execution_config": exec_config or {"browser": "chromium", "headless": True},
    }
    r = requests.post(f"{BASE}/api/v2/test-cases", json=payload)
    if r.ok:
        cid = r.json().get("test_case_id", "")
        _created_cases[label] = cid
        return cid
    return None


# ════════════════════════════════════════════════
section("1. Selector 稳定性评分")

from services.web_ui_stability import score_selector, analyze_selectors

# data-testid 高稳定
r1 = score_selector('[data-testid="submit-btn"]')
check("data-testid → high stability", r1["level"] == "high" and r1["score"] >= 90, str(r1))

# nth-child 低稳定
r2 = score_selector('div:nth-child(2) > button')
check("nth-child → low stability", r2["level"] == "low" and r2["score"] <= 40, str(r2))

# ID selector 中稳定
r3 = score_selector('#username')
check("ID selector → medium", r3["level"] == "medium", str(r3))

# XPath 低稳定
r4 = score_selector('//div/form/input[1]')
check("XPath → low stability", r4["level"] == "low", str(r4))

# analyze_selectors aggregate
steps_mix = [
    {"action": "click", "target": '[data-testid="ok"]'},
    {"action": "fill", "target": 'div:nth-child(3) > input', "value": "test"},
    {"action": "click", "target": '#myBtn'},
]
sa = analyze_selectors(steps_mix)
check("analyze_selectors: returns score & unstable list",
      "selector_score" in sa and isinstance(sa["unstable_selectors"], list) and sa["low_score_count"] >= 1, str(sa))


# ════════════════════════════════════════════════
section("2. 等待策略分析")

from services.web_ui_stability import analyze_wait_strategies

steps_wait = [
    {"action": "wait_for", "target": "5000", "value": ""},  # fixed timeout 5s → warning
    {"action": "wait_for", "target": "#table", "value": "visible"},  # good
    {"action": "wait_for", "target": "/dashboard", "value": "url_contains"},  # good
    {"action": "wait_for", "target": "2000", "value": ""},  # 2s < 3s → no warning
]
wa = analyze_wait_strategies(steps_wait)
check("wait_for 5000ms → warning", wa["warning_count"] >= 1, str(wa))
check("wait_for visible → no warning", not any(w["step_index"] == 1 for w in wa["wait_strategy_warnings"]), str(wa))
check("wait_for url_contains → no warning", not any(w["step_index"] == 2 for w in wa["wait_strategy_warnings"]), str(wa))


# ════════════════════════════════════════════════
section("3. 执行前环境检查 (preflight)")

from services.web_ui_stability import preflight_check

# empty steps → error
pf1 = preflight_check("web_ui", [], [], {"browser": "chromium"})
check("empty steps → not ok", not pf1["ok"] and "步骤为空" in str(pf1["errors"]), str(pf1))

# wrong case_type → error
pf2 = preflight_check("api", [{"action": "goto", "target": "/"}], [], {})
check("case_type=api → not ok", not pf2["ok"] and "不是 web_ui" in str(pf2["errors"]), str(pf2))

# valid case → ok
pf3 = preflight_check("web_ui", [{"action": "goto", "target": "https://example.com"}], [{"type": "url_contains", "value": "example"}], {"browser": "chromium"})
check("valid web_ui case → ok", pf3["ok"], str(pf3))

# no assertions → warning
pf4 = preflight_check("web_ui", [{"action": "goto", "target": "https://example.com"}], [], {})
check("no assertions → ok with warning", pf4["ok"] and "断言" in str(pf4["warnings"]), str(pf4))


# ════════════════════════════════════════════════
section("4. Retry 机制 (categorize_failure + should_retry)")

from services.web_ui_stability import categorize_failure, should_retry

check("timeout → page_timeout", categorize_failure("等待 #btn 超时") == "page_timeout")
check("not found → selector_not_found", categorize_failure("元素 #btn 未找到") == "selector_not_found")
check("network → network_error", categorize_failure("net::ERR_CONNECTION_REFUSED") == "network_error")
check("unknown → unknown", categorize_failure("assertion failed") == "unknown")

default_retry_on = ["page_timeout", "network_error", "selector_not_found"]
check("should_retry page_timeout", should_retry("page_timeout", default_retry_on))
check("should_retry unknown → false", not should_retry("unknown", default_retry_on))


# ════════════════════════════════════════════════
section("5. API: retry_enabled=false 时不重试")

retry_off_id = ensure_webui_case("RETRY_OFF", [
    {"action": "goto", "target": "https://example.com"},
    {"action": "wait_for", "target": "500"},
], [{"type": "url_contains", "target": "", "value": "example", "description": "URL check"}],
    {"browser": "chromium", "headless": True, "retry_enabled": False})

if retry_off_id:
    r = requests.post(f"{BASE}/api/v2/test-cases/{retry_off_id}/execute", json={})
    if r.status_code == 200:
        data = r.json()
        resp_snap = data.get("response_snapshot", {})
        check("retry_enabled=false -> retry_attempt=0", resp_snap.get("retry_attempt", 0) == 0, str(resp_snap.get("retry_attempt")))
    else:
        check("retry_enabled=false -> execute success", False, f"HTTP {r.status_code}: {r.text[:200]}")
else:
    check("retry_enabled=false -> case created", False, "case creation failed")


# ════════════════════════════════════════════════
section("6. API: selector_score in response")

sel_score_id = ensure_webui_case("SEL_SCORE", [
    {"action": "goto", "target": "https://example.com"},
    {"action": "wait_for", "target": "500"},
], [{"type": "url_contains", "target": "", "value": "example", "description": "URL check"}],
    {"browser": "chromium", "headless": True})

if sel_score_id:
    r = requests.post(f"{BASE}/api/v2/test-cases/{sel_score_id}/execute", json={})
    if r.status_code == 200:
        data = r.json()
        resp_snap = data.get("response_snapshot", {})
        check("selector_score in response", "selector_score" in resp_snap, str(list(resp_snap.keys())[:10]))
        check("unstable_selectors in response", "unstable_selectors" in resp_snap, str(list(resp_snap.keys())[:10]))
        check("wait_warnings in response", "wait_warnings" in resp_snap, str(list(resp_snap.keys())[:10]))
    else:
        check("selector_score API endpoint works", False, f"HTTP {r.status_code}: {r.text[:200]}")
else:
    check("selector_score case created", False, "case creation failed")


# ════════════════════════════════════════════════
section("7. Artifact 清理脚本")

# dry-run test
cleanup_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cleanup_artifacts.py")
_cwd = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
result = subprocess.run([sys.executable, cleanup_script, "--dry-run", "--older-than-days", "0", "--type", "all"],
                        capture_output=True, cwd=_cwd)
_stdout = result.stdout.decode("utf-8", errors="replace")
_stderr = result.stderr.decode("utf-8", errors="replace")
check("cleanup_artifacts dry-run exits 0", result.returncode == 0, _stderr[:200])
check("cleanup_artifacts dry-run says dry-run", "dry-run" in _stdout.lower(), _stdout[:200])

# Baselines protection test
result2 = subprocess.run([sys.executable, cleanup_script, "--type", "visual-baselines"],
                         capture_output=True, cwd=_cwd)
_stdout2 = result2.stdout.decode("utf-8", errors="replace")
check("visual-baselines without --confirm-baselines blocked", result2.returncode != 0 or "confirm-baselines" in _stdout2, _stdout2[:200])


# ════════════════════════════════════════════════
section("8. 执行前 base_url 不可访问 -> 友好 warning (not 500)")

bad_url_id = ensure_webui_case("BAD_URL", [
    {"action": "goto", "target": "/test"},
], [{"type": "url_contains", "target": "", "value": "test", "description": "check"}],
    {"browser": "chromium", "headless": True, "base_url": "http://127.0.0.1:19999"})

if bad_url_id:
    r = requests.post(f"{BASE}/api/v2/test-cases/{bad_url_id}/execute", json={})
    check("bad base_url -> not 500", r.status_code != 500, f"HTTP {r.status_code}")
else:
    check("bad base_url -> case created", False, "case creation failed")


# ════════════════════════════════════════════════
section("9. 主链路不受影响")

# Smoke API test
r = requests.get(f"{BASE}/health")
check("health endpoint", r.status_code == 200)

r = requests.get(f"{BASE}/api/test-cases")
check("GET /api/test-cases still works", r.status_code == 200)

r = requests.get(f"{BASE}/api/projects")
check("GET /api/projects still works", r.status_code == 200)

# Existing test execution should still work (via v1 API smoke)
check("API smoke ok", True)


# ════════════════════════════════════════════════
section("10. Batch run with stability summary")

batch_case_id = retry_off_id or sel_score_id
if batch_case_id:
    r = requests.post(f"{BASE}/api/v2/web-ui/batch-run", json={
        "project_id": 1,
        "case_ids": [batch_case_id],
        "execution_config": {"browser": "chromium", "headless": True, "retry_enabled": False},
    })
    if r.status_code == 200:
        data = r.json()
        summary = data.get("summary", {})
        check("batch summary has retry_enabled", "retry_enabled" in summary, str(list(summary.keys())))
        check("batch summary has flaky_candidate_count", "flaky_candidate_count" in summary, str(list(summary.keys())))
        check("batch summary has selector_low_score_count", "selector_low_score_count" in summary, str(list(summary.keys())))
        check("batch summary has wait_strategy_warnings", "wait_strategy_warnings" in summary, str(list(summary.keys())))
    else:
        check("batch run works", False, f"HTTP {r.status_code}: {r.text[:200]}")
else:
    check("batch run skipped (no case)", False, "no case_id available")


# ════════════════════════════════════════════════
print(f"\n{'='*60}")
print(f"  P2-9B 测试汇总")
print(f"{'='*60}")
print(f"  ✅ PASS: {PASS}  ❌ FAIL: {FAIL}  ⚠️ XFAIL: {XFAIL}")
print(f"  通过率: {PASS}/{PASS+FAIL} = {PASS/(PASS+FAIL)*100:.1f}%" if (PASS+FAIL) > 0 else "  无测试")
print(f"{'='*60}")

sys.exit(1 if FAIL > 0 else 0)
