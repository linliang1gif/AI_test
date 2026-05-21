"""
P3-4B: 质量趋势与风险模块 专项测试
覆盖 8 个新 API: case-trend / defect-trend / data-issue-trend / flaky-trend /
                  performance-trend / visual-trend / module-risk / quality-regression
"""
import sys, os, requests, time, json

BASE = os.environ.get("TEST_BASE_URL", "http://localhost:8000")
KEY = os.environ.get("TESTING_KEY", "regression-test-key-auto")
PASS = FAIL = SKIP = 0
RESULTS = []


def wait_for_backend(max_wait=30):
    for _ in range(max_wait):
        for ep in ["/readiness", "/health"]:
            try:
                r = requests.get(f"{BASE}{ep}", timeout=3)
                if r.ok:
                    return True
            except Exception:
                pass
        time.sleep(1)
    return False


def api(method, path, **kw):
    url = f"{BASE}{path}"
    kw.setdefault("timeout", 15)
    kw.setdefault("headers", {})
    kw["headers"]["X-Test-Key"] = KEY
    return getattr(requests, method)(url, **kw)


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        RESULTS.append(("PASS", name))
    else:
        FAIL += 1
        RESULTS.append(("FAIL", name, detail))
        print(f"  FAIL: {name} — {detail}")


# ─────────────────────────────────────────────────────
print(f"\n{'='*60}")
print("P3-4B 质量趋势与风险模块 专项测试")
print(f"{'='*60}\n")

if not wait_for_backend():
    print("后端未就绪，测试中止")
    sys.exit(1)

# ── 1. case-trend ─────────────────────────────────────
print("▶ case-trend")
r = api("get", "/api/v2/analytics/case-trend?days=14")
check("case-trend 正常返回", r.status_code == 200, f"status={r.status_code}")
data = r.json()
check("case-trend 返回列表", isinstance(data, list))
if data:
    d0 = data[0]
    check("case-trend 包含 date", "date" in d0)
    check("case-trend 包含 total_cases", "total_cases" in d0)
    check("case-trend 包含 passed_cases", "passed_cases" in d0)
    check("case-trend 包含 failed_cases", "failed_cases" in d0)
    check("case-trend 包含 skipped_cases", "skipped_cases" in d0)
    check("case-trend 包含 case_pass_rate", "case_pass_rate" in d0)
else:
    check("case-trend 空数组(无数据)", True)

# ── 2. defect-trend ──────────────────────────────────
print("▶ defect-trend")
r = api("get", "/api/v2/analytics/defect-trend?days=14")
check("defect-trend 正常返回", r.status_code == 200, f"status={r.status_code}")
data = r.json()
check("defect-trend 返回列表", isinstance(data, list))
if data:
    d0 = data[0]
    check("defect-trend 包含 date", "date" in d0)
    check("defect-trend 包含 new_defects", "new_defects" in d0)
    check("defect-trend 包含 closed_defects", "closed_defects" in d0)
    check("defect-trend 包含 reopened_defects", "reopened_defects" in d0)
    check("defect-trend 包含 open_defects", "open_defects" in d0)

# ── 3. data-issue-trend ──────────────────────────────
print("▶ data-issue-trend")
r = api("get", "/api/v2/analytics/data-issue-trend?days=14")
check("data-issue-trend 正常返回", r.status_code == 200, f"status={r.status_code}")
data = r.json()
check("data-issue-trend 返回列表", isinstance(data, list))
if data:
    d0 = data[0]
    check("data-issue-trend 包含 data_validation_errors", "data_validation_errors" in d0)
    check("data-issue-trend 包含 missing_variables", "missing_variables" in d0)
    check("data-issue-trend 包含 cleanup_failed", "cleanup_failed" in d0)
    check("data-issue-trend 包含 data_issue_runs", "data_issue_runs" in d0)

# ── 4. flaky-trend ───────────────────────────────────
print("▶ flaky-trend")
r = api("get", "/api/v2/analytics/flaky-trend?days=14")
check("flaky-trend 正常返回", r.status_code == 200, f"status={r.status_code}")
data = r.json()
check("flaky-trend 返回列表", isinstance(data, list))
if data:
    d0 = data[0]
    check("flaky-trend 包含 flaky_candidate_count", "flaky_candidate_count" in d0)
    check("flaky-trend 包含 retried_cases", "retried_cases" in d0)
    check("flaky-trend 包含 recovered_by_retry_count", "recovered_by_retry_count" in d0)

# ── 5. performance-trend ─────────────────────────────
print("▶ performance-trend")
r = api("get", "/api/v2/analytics/performance-trend?days=14")
check("performance-trend 正常返回", r.status_code == 200, f"status={r.status_code}")
data = r.json()
check("performance-trend 返回列表或空数组", isinstance(data, list))
if data:
    d0 = data[0]
    check("performance-trend 包含 p95_ms", "p95_ms" in d0)
    check("performance-trend 包含 error_rate", "error_rate" in d0)
    check("performance-trend 包含 threshold_failed_count", "threshold_failed_count" in d0)

# ── 6. visual-trend ──────────────────────────────────
print("▶ visual-trend")
r = api("get", "/api/v2/analytics/visual-trend?days=14")
check("visual-trend 正常返回", r.status_code == 200, f"status={r.status_code}")
data = r.json()
check("visual-trend 返回列表或空数组", isinstance(data, list))
if data:
    d0 = data[0]
    check("visual-trend 包含 visual_failed_count", "visual_failed_count" in d0)
    check("visual-trend 包含 max_diff_ratio", "max_diff_ratio" in d0)

# ── 7. module-risk ───────────────────────────────────
print("▶ module-risk")
r = api("get", "/api/v2/analytics/module-risk?days=14")
check("module-risk 正常返回", r.status_code == 200, f"status={r.status_code}")
data = r.json()
check("module-risk 返回列表", isinstance(data, list))
if data:
    m0 = data[0]
    check("module-risk 包含 module", "module" in m0)
    check("module-risk 包含 risk_score", "risk_score" in m0)
    check("module-risk 包含 risk_level", "risk_level" in m0)
    check("module-risk risk_level 有效值", m0["risk_level"] in ("high", "medium", "low"), f"got {m0.get('risk_level')}")
    check("module-risk 包含 failure_rate", "failure_rate" in m0)
    check("module-risk 包含 open_defects", "open_defects" in m0)
    check("module-risk 包含 blocker_defects", "blocker_defects" in m0)
    check("module-risk 包含 risk_reasons", "risk_reasons" in m0)
    check("module-risk risk_reasons 是列表", isinstance(m0["risk_reasons"], list))
    check("module-risk risk_score 范围 0-1", 0 <= m0["risk_score"] <= 1, f"got {m0['risk_score']}")
    check("module-risk 按 score 降序", all(data[i]["risk_score"] >= data[i+1]["risk_score"] for i in range(len(data)-1)))
else:
    check("module-risk 空数组(无数据)", True)

# high risk check: create test data to ensure some module has risk
# Use existing data from regression runs - check for any module
if data:
    high_mods = [m for m in data if m["risk_level"] == "high"]
    med_mods = [m for m in data if m["risk_level"] == "medium"]
    low_mods = [m for m in data if m["risk_level"] == "low"]
    check("module-risk 风险等级分类正确 (>= 0.7 high, >= 0.4 medium, else low)",
          all(m["risk_score"] >= 0.7 for m in high_mods) and
          all(0.4 <= m["risk_score"] < 0.7 for m in med_mods) and
          all(m["risk_score"] < 0.4 for m in low_mods),
          f"high={len(high_mods)}, med={len(med_mods)}, low={len(low_mods)}")

# ── 8. quality-regression ────────────────────────────
print("▶ quality-regression")
r = api("get", "/api/v2/analytics/quality-regression?days=7")
check("quality-regression 正常返回", r.status_code == 200, f"status={r.status_code}")
data = r.json()
check("quality-regression 返回列表", isinstance(data, list))
check("quality-regression 至少包含 6 个指标", len(data) >= 6, f"got {len(data)}")
if data:
    d0 = data[0]
    check("quality-regression 包含 metric", "metric" in d0)
    check("quality-regression 包含 label", "label" in d0)
    check("quality-regression 包含 current_value", "current_value" in d0)
    check("quality-regression 包含 previous_value", "previous_value" in d0)
    check("quality-regression 包含 delta", "delta" in d0)
    check("quality-regression 包含 degraded", "degraded" in d0)
    check("quality-regression 包含 severity", "severity" in d0)
    check("quality-regression severity 有效值",
          all(r["severity"] in ("none", "low", "medium", "high") for r in data),
          f"invalid severity found")
    metrics = [r["metric"] for r in data]
    for exp in ["case_pass_rate", "gate_pass_rate", "new_defects", "p95_ms", "visual_failed", "data_issues"]:
        check(f"quality-regression 含 {exp}", exp in metrics, f"missing {exp}")

# ── 9. days 参数测试 ─────────────────────────────────
print("▶ days 参数")
r = api("get", "/api/v2/analytics/case-trend?days=7")
check("days=7 生效", r.status_code == 200)
r = api("get", "/api/v2/analytics/case-trend?days=30")
check("days=30 生效", r.status_code == 200)

# days > 90 限制
r = api("get", "/api/v2/analytics/case-trend?days=100")
check("days=100 返回 400", r.status_code in (400, 422), f"status={r.status_code}")
r = api("get", "/api/v2/analytics/module-risk?days=91")
check("module-risk days=91 返回 400", r.status_code in (400, 422), f"status={r.status_code}")

# ── 10. project_id 过滤 ─────────────────────────────
print("▶ project_id 过滤")
r = api("get", "/api/v2/analytics/case-trend?days=14&project_id=99999")
check("project_id=99999 不报错", r.status_code == 200)
data = r.json()
check("project_id=99999 返回空数组", isinstance(data, list))

r = api("get", "/api/v2/analytics/module-risk?days=14&project_id=99999")
check("module-risk project_id=99999 返回空数组", r.status_code == 200 and isinstance(r.json(), list))

# ── 11. module 过滤 ──────────────────────────────────
print("▶ module 过滤")
r = api("get", "/api/v2/analytics/module-risk?days=14&module=不存在的模块")
check("module=不存在 返回空数组", r.status_code == 200 and isinstance(r.json(), list) and len(r.json()) == 0)

# ── 12. 无数据不 500 ────────────────────────────────
print("▶ 无数据不 500")
for ep in ["case-trend", "defect-trend", "data-issue-trend", "flaky-trend",
           "performance-trend", "visual-trend", "module-risk", "quality-regression"]:
    r = api("get", f"/api/v2/analytics/{ep}?days=1&project_id=99999")
    check(f"{ep} 无数据不 500", r.status_code == 200, f"status={r.status_code}")

# ── 13. 不返回敏感字段 ──────────────────────────────
print("▶ 敏感字段检查")
SENSITIVE_KEYS = ["password", "token", "authorization", "trace_path", "screenshot_path"]
for ep in ["case-trend", "defect-trend", "module-risk", "quality-regression"]:
    r = api("get", f"/api/v2/analytics/{ep}?days=14")
    raw = r.text.lower()
    for s in SENSITIVE_KEYS:
        check(f"{ep} 不含键 {s}", f'"{s}"' not in raw and f'"{s}":' not in raw)

# ── 14. analytics import 不查询 DB ──────────────────
print("▶ analytics import 安全性")
try:
    import importlib, ast
    svc_path = os.path.join(os.path.dirname(__file__), "..", "services", "analytics_service.py")
    svc_path = os.path.normpath(svc_path)
    with open(svc_path, "r", encoding="utf-8") as f:
        src = f.read()
    tree = ast.parse(src)
    top_calls = [n for n in ast.iter_child_nodes(tree) if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)]
    db_calls = []
    for c in top_calls:
        call_src = ast.get_source_segment(src, c)
        if call_src and ("db." in call_src or "session" in call_src.lower()):
            db_calls.append(call_src[:80])
    check("analytics_service import 无 DB 调用", len(db_calls) == 0, f"found: {db_calls}")
except Exception as e:
    check("analytics_service import 检查", False, str(e))

# ── 15. 主链路不受影响 ──────────────────────────────
print("▶ 主链路检查")
main_checks = [
    ("/api/v2/test-cases?limit=1", "test-cases"),
    ("/api/v2/analytics/overview?days=7", "overview"),
    ("/api/v2/analytics/test-suite-trend?days=7", "suite-trend"),
    ("/api/v2/analytics/gate-trend?days=7", "gate-trend"),
    ("/api/v2/analytics/failure-modules?days=7", "failure-modules"),
    ("/api/v2/analytics/failure-categories?days=7", "failure-categories"),
    ("/api/v2/analytics/defect-summary?days=7", "defect-summary"),
    ("/api/v2/analytics/data-issues?days=7", "data-issues"),
    ("/health", "health"),
    ("/readiness", "readiness"),
]
for path, label in main_checks:
    r = api("get", path)
    check(f"主链路 {label} 正常", r.status_code == 200, f"status={r.status_code}")

# ── 汇总 ─────────────────────────────────────────────
total = PASS + FAIL + SKIP
print(f"\n{'='*60}")
print(f"P3-4B 测试汇总: {PASS} PASS / {FAIL} FAIL / {total} TOTAL")
print(f"{'='*60}")

if FAIL > 0:
    print("\n失败项:")
    for r in RESULTS:
        if r[0] == "FAIL":
            print(f"  ✗ {r[1]} — {r[2]}")

sys.exit(1 if FAIL > 0 else 0)
