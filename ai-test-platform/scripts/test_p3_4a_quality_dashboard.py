#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P3-4A: 质量驾驶舱基础指标 — 专项测试脚本
覆盖: overview / test-suite-trend / gate-trend / failure-modules / failure-categories
      defect-summary / data-issues / 参数验证 / 空数据 / 脱敏 / 主链路
"""
import sys, os, json, time, requests

BASE = os.environ.get("TEST_BASE_URL", "http://localhost:8000")
API = f"{BASE}/api/v2/analytics"
HEALTH = f"{BASE}/health"

results = []

def T(name, ok, detail=""):
    results.append((name, ok, detail))
    tag = "PASS" if ok else "FAIL"
    print(f"  [{tag}] {name}" + (f" — {detail}" if detail and not ok else ""))

def section(title):
    print(f"\n{'─'*50}\n  {title}\n{'─'*50}")

def wait_backend(timeout=30):
    for _ in range(timeout):
        try:
            r = requests.get(HEALTH, timeout=2)
            if r.status_code == 200:
                return True
        except:
            pass
        time.sleep(1)
    return False

print("=" * 60)
print("  P3-4A 质量驾驶舱基础指标 — 专项测试")
print("=" * 60)

if not wait_backend():
    print("❌ 后端未就绪"); sys.exit(1)

# ══════════════════════════════════════════════════════════
section("1. overview 正常返回")
r = requests.get(f"{API}/overview")
T("overview 200", r.status_code == 200)
ov = r.json()
T("返回 total_runs", "total_runs" in ov)
T("返回 run_pass_rate", "run_pass_rate" in ov)
T("返回 case_pass_rate", "case_pass_rate" in ov)
T("返回 gate_pass_rate", "gate_pass_rate" in ov)
T("返回 open_defects", "open_defects" in ov)
T("返回 blocker_defects", "blocker_defects" in ov)
T("返回 risk_level", "risk_level" in ov)
T("返回 risk_reasons", "risk_reasons" in ov and isinstance(ov["risk_reasons"], list))
T("返回 data_issue_count", "data_issue_count" in ov)
T("返回 flaky_candidate_count", "flaky_candidate_count" in ov)

section("2. risk_level 计算正确")
T("risk_level 是 low/medium/high", ov.get("risk_level") in ("low", "medium", "high"))
# 验证 pass_rate 在 0-1 之间
T("run_pass_rate 0~1", 0 <= ov.get("run_pass_rate", -1) <= 1)
T("case_pass_rate 0~1", 0 <= ov.get("case_pass_rate", -1) <= 1)
T("gate_pass_rate 0~1", 0 <= ov.get("gate_pass_rate", -1) <= 1)

section("3. test-suite-trend 正常返回")
r = requests.get(f"{API}/test-suite-trend")
T("test-suite-trend 200", r.status_code == 200)
trend = r.json()
T("返回数组", isinstance(trend, list))
if trend:
    T("包含 date", "date" in trend[0])
    T("包含 pass_rate", "pass_rate" in trend[0])
    T("包含 total_suite_runs", "total_suite_runs" in trend[0])
else:
    T("包含 date (空数组)", True, "空数组但不报错")
    T("包含 pass_rate (空数组)", True, "空数组但不报错")
    T("包含 total_suite_runs (空数组)", True, "空数组但不报错")

section("4. gate-trend 正常返回")
r = requests.get(f"{API}/gate-trend")
T("gate-trend 200", r.status_code == 200)
gt = r.json()
T("返回数组", isinstance(gt, list))
if gt:
    T("包含 gate_passed", "gate_passed" in gt[0])
    T("包含 gate_pass_rate", "gate_pass_rate" in gt[0])
else:
    T("包含 gate_passed (空数组)", True, "空数组但不报错")
    T("包含 gate_pass_rate (空数组)", True, "空数组但不报错")

section("5. failure-modules Top 5 返回")
r = requests.get(f"{API}/failure-modules")
T("failure-modules 200", r.status_code == 200)
fm = r.json()
T("返回数组", isinstance(fm, list))
T("最多5项", len(fm) <= 5)
if fm:
    T("包含 module", "module" in fm[0])
    T("包含 failed_count", "failed_count" in fm[0])
    T("包含 failure_rate", "failure_rate" in fm[0])
else:
    T("包含 module (空)", True, "无失败模块")
    T("包含 failed_count (空)", True, "无失败模块")
    T("包含 failure_rate (空)", True, "无失败模块")

section("6. failure-categories 返回")
r = requests.get(f"{API}/failure-categories")
T("failure-categories 200", r.status_code == 200)
fc = r.json()
T("返回数组", isinstance(fc, list))
if fc:
    T("包含 category", "category" in fc[0])
    T("包含 count", "count" in fc[0])
    T("包含 percentage", "percentage" in fc[0])
    total_pct = sum(c.get("percentage", 0) for c in fc)
    T("percentage 总和约 1.0", abs(total_pct - 1.0) < 0.01 or len(fc) == 0, f"实际: {total_pct:.4f}")
else:
    T("包含 category (空)", True, "无失败")
    T("包含 count (空)", True, "无失败")
    T("包含 percentage (空)", True, "无失败")
    T("percentage 总和约 1.0 (空)", True, "无失败")

section("7. defect-summary 返回")
r = requests.get(f"{API}/defect-summary")
T("defect-summary 200", r.status_code == 200)
ds = r.json()
T("返回 total_defects", "total_defects" in ds)
T("返回 open_defects", "open_defects" in ds)
T("返回 blocker_defects", "blocker_defects" in ds)
T("返回 known_issues", "known_issues" in ds)
T("返回 status_distribution", "status_distribution" in ds)
T("返回 severity_distribution", "severity_distribution" in ds)

section("8. data-issues 返回")
r = requests.get(f"{API}/data-issues")
T("data-issues 200", r.status_code == 200)
di = r.json()
T("返回 data_validation_errors", "data_validation_errors" in di)
T("返回 missing_variables", "missing_variables" in di)
T("返回 cleanup_failed", "cleanup_failed" in di)
T("返回 datasets_used", "datasets_used" in di)
T("返回 data_issue_runs", "data_issue_runs" in di)

section("9. project_id 过滤生效")
r = requests.get(f"{API}/overview?project_id=99999")
T("project_id=99999 200", r.status_code == 200)
ov_empty = r.json()
T("total_runs=0 for nonexist project", ov_empty.get("total_runs") == 0)

section("10. days 参数生效")
r7 = requests.get(f"{API}/overview?days=7").json()
r30 = requests.get(f"{API}/overview?days=30").json()
T("days=7 返回", "total_runs" in r7)
T("days=30 返回", "total_runs" in r30)
T("days=30 total_runs >= days=7", r30.get("total_runs", 0) >= r7.get("total_runs", 0))

section("11. days > 90 被限制")
r = requests.get(f"{API}/overview?days=91")
T("days=91 返回 400", r.status_code == 400)
r2 = requests.get(f"{API}/test-suite-trend?days=91")
T("trend days=91 返回 400", r2.status_code == 400)

section("12. 无数据时不报错")
for endpoint in ["overview", "test-suite-trend", "gate-trend", "failure-modules", "failure-categories", "defect-summary", "data-issues"]:
    r = requests.get(f"{API}/{endpoint}?project_id=99999&days=1")
    T(f"{endpoint} 无数据 200", r.status_code == 200)

section("13. API 不返回敏感字段")
ov_text = json.dumps(ov)
T("不含 token", "token" not in ov_text.lower() or "token" in "flaky_candidate_count")
T("不含 password", "password" not in ov_text.lower())
T("不含 cookie", "cookie" not in ov_text.lower())
T("不含 screenshot_path", "screenshot_path" not in ov_text)
T("不含 trace_path", "trace_path" not in ov_text)

section("14. suite_type 过滤")
r = requests.get(f"{API}/test-suite-trend?suite_type=suite")
T("suite_type=suite 200", r.status_code == 200)

section("15. 主链路不受影响")
for path, name in [
    ("/health", "health"),
    ("/api/v2/test-cases?limit=1", "test-cases"),
    ("/api/v2/test-suites", "test-suites"),
    ("/api/v2/quality-gates/default-config", "quality-gates"),
    ("/api/v2/test-data/datasets", "test-data"),
    ("/api/v2/defects", "defects"),
    (f"{API}/overview", "analytics overview"),
]:
    r = requests.get(f"{BASE}{path}" if not path.startswith("http") else path)
    T(f"{name} 200", r.status_code == 200)

# ── 汇总 ──
print("\n" + "=" * 60)
passed = sum(1 for _, ok, _ in results if ok)
failed = sum(1 for _, ok, _ in results if not ok)
print(f"  P3-4A 测试汇总: {passed} PASS / {failed} FAIL / {len(results)} TOTAL")
print("=" * 60)

if failed > 0:
    print("\n  ❌ 失败项:")
    for name, ok, detail in results:
        if not ok:
            print(f"    - {name}: {detail}")

sys.exit(1 if failed > 0 else 0)
