"""
Phase 18 验收脚本 - 执行稳定性与演示闭环加固
测试内容:
  1. 批量执行 summary 增强 (pass_rate, failure_categories, skipped_reasons, skipped_cases)
  2. destructive 跳过机制 (skipped_reason, skipped_message)
  3. failure_category 分类逻辑增强
  4. HTML 报告增强 (概览/失败分类/风险/skipped/失败详情)
  5. 向后兼容: Demo Init / Preset 批量执行 / 报告生成下载
"""
import requests
import json
import time

BASE = 'http://localhost:8000'
H = {'Authorization': 'Bearer demo-token', 'Content-Type': 'application/json'}
TIMEOUT = 120  # 批量执行可能较慢
SHORT = 15
results = []


def check(name, cond):
    results.append((name, cond))
    status = "PASS" if cond else "FAIL"
    print(f"  {'✅' if cond else '❌'} {status}: {name}")


print("=" * 60)
print("  Phase 18 Acceptance Tests")
print("=" * 60)

# ──────────────────────────────────────────────────────────────
# 1. 向后兼容: Demo 系统状态
# ──────────────────────────────────────────────────────────────
print("\n── 1. Demo 系统向后兼容 ──")
r = requests.get(f"{BASE}/api/v2/demo/status", timeout=SHORT)
d = r.json()
check("1.1 Demo status API 200", r.status_code == 200)
check("1.2 Demo initialized", d.get("data", {}).get("initialized") is True)
tc_count = d.get("data", {}).get("test_case_count", 0)
check("1.3 Demo has >=100 test cases", tc_count >= 100)

# ──────────────────────────────────────────────────────────────
# 2. 向后兼容: Mock API 连通
# ──────────────────────────────────────────────────────────────
print("\n── 2. Mock API 连通 ──")
r = requests.post(f"{BASE}/api/mock/login", json={"username": "admin", "password": "123456"}, timeout=SHORT)
check("2.1 Mock login OK", r.status_code == 200 and r.json().get("code") == 0)

r = requests.get(f"{BASE}/api/mock/products", headers=H, timeout=SHORT)
check("2.2 Mock products list OK", r.status_code == 200 and r.json().get("code") == 0)

# ──────────────────────────────────────────────────────────────
# 3. 向后兼容: 治理概况
# ──────────────────────────────────────────────────────────────
print("\n── 3. 治理概况 ──")
r = requests.get(f"{BASE}/api/v2/test-cases/governance-summary", timeout=SHORT)
check("3.1 Governance summary 200", r.status_code == 200)
gs = r.json()
# governance summary 可能用 total 或 total_cases
tc_val = gs.get("total_cases") or gs.get("total") or gs.get("data", {}).get("total_cases", 0) or gs.get("data", {}).get("total", 0)
check("3.2 Has total_cases", (tc_val or 0) > 0)
if not tc_val:
    print(f"    [DEBUG] governance response: {str(gs)[:300]}")

# ──────────────────────────────────────────────────────────────
# 4. Phase 18: Preset 批量执行 (smoke) + summary 增强
# ──────────────────────────────────────────────────────────────
print("\n── 4. Preset 批量执行 + Summary 增强 ──")
batch = {}
run_id = ""
try:
    print("    [INFO] smoke 批量执行中，请等待(最长60s)...")
    r = requests.post(
        f"{BASE}/api/v2/test-cases/batch-execute",
        headers=H,
        json={"preset": "smoke", "environment_id": 1, "skip_destructive": True},
        timeout=60
    )
    check("4.1 Smoke preset execute 200", r.status_code == 200)
    batch = r.json()
    run_id = batch.get("run_id", "")

    check("4.2 Response has pass_rate", "pass_rate" in batch)
    check("4.3 Response has failure_categories", "failure_categories" in batch)
    check("4.4 Response has skipped_reasons", "skipped_reasons" in batch)
    check("4.5 Response has skipped_cases", "skipped_cases" in batch)
    check("4.6 pass_rate is number", isinstance(batch.get("pass_rate"), (int, float)))
    check("4.7 failure_categories is dict", isinstance(batch.get("failure_categories"), dict))
    check("4.8 skipped_reasons is dict", isinstance(batch.get("skipped_reasons"), dict))

    total = batch.get("total_cases", 0)
    passed = batch.get("passed_cases", 0)
    failed = batch.get("failed_cases", 0)
    skipped = batch.get("skipped_cases", 0)
    check("4.9 total >= passed+failed+skipped", total >= passed + failed + skipped or total >= passed + skipped)
    check("4.10 pass_rate > 0", batch.get("pass_rate", 0) > 0)
    check("4.11 run_id not empty", len(run_id) > 0)
except Exception as e:
    print(f"    ⚠️ SKIP: 批量执行超时或异常 ({e.__class__.__name__})")
    for i in range(1, 12):
        check(f"4.{i} Skipped (timeout)", False)

# ──────────────────────────────────────────────────────────────
# 5. Phase 18: destructive 跳过机制
# ──────────────────────────────────────────────────────────────
print("\n── 5. Destructive 跳过机制 ──")
batch2 = {}
run_id2 = ""
try:
    # 先获取包含 destructive 的用例 ID (DEMO_OK_007=DELETE产品, DEMO_OK_011=取消订单)
    destructive_ids = ["DEMO_OK_007", "DEMO_OK_011"]
    safe_ids = ["DEMO_OK_001", "DEMO_OK_002", "DEMO_OK_003"]
    all_ids = safe_ids + destructive_ids
    print(f"    [INFO] 指定 {len(all_ids)} 个用例(含 destructive)执行中...")
    r2 = requests.post(
        f"{BASE}/api/v2/test-cases/batch-execute",
        headers=H,
        json={"case_ids": all_ids, "environment_id": 1, "skip_destructive": True},
        timeout=60
    )
    check("5.1 Batch with skip_destructive 200", r2.status_code == 200)
    batch2 = r2.json()
    run_id2 = batch2.get("run_id", "")

    skipped_results = [r for r in batch2.get("results", []) if r.get("status") == "skipped"]
    destructive_skipped = [r for r in skipped_results if r.get("skipped_reason") == "destructive"]
    check("5.2 Has skipped results", len(skipped_results) > 0)
    check("5.3 Has destructive skipped entries", len(destructive_skipped) > 0)

    if destructive_skipped:
        first = destructive_skipped[0]
        check("5.4 skipped_reason = destructive", first.get("skipped_reason") == "destructive")
        check("5.5 skipped_message not empty", len(first.get("skipped_message", "")) > 0)
        check("5.6 Skipped entry has case_name", len(first.get("case_name", "")) > 0)
    else:
        check("5.4 skipped_reason = destructive", False)
        check("5.5 skipped_message not empty", False)
        check("5.6 Skipped entry has case_name", False)

    sk_reasons = batch2.get("skipped_reasons", {})
    check("5.7 skipped_reasons has destructive key", "destructive" in sk_reasons)
    check("5.8 skipped_cases count matches", batch2.get("skipped_cases", 0) == sum(sk_reasons.values()))
except Exception as e:
    print(f"    ⚠️ SKIP: 批量执行超时或异常 ({e.__class__.__name__})")
    for i in range(1, 9):
        check(f"5.{i} Skipped (timeout)", False)

# ──────────────────────────────────────────────────────────────
# 6. Phase 18: failure_category 分类逻辑增强
# ──────────────────────────────────────────────────────────────
print("\n── 6. Failure Category 分类 ──")
valid_cats = {'auth_error', 'env_error', 'request_error', 'response_error',
              'assertion_error', 'dependency_error', 'timeout_error', 'unknown_error'}
fc = batch2.get("failure_categories", {})
all_valid = all(k in valid_cats for k in fc.keys())
check("6.1 All failure_categories are valid", all_valid or len(fc) == 0)

failed_results = [r for r in batch2.get("results", []) if r.get("status") in ("failed", "error")]
if failed_results:
    has_cat = all(r.get("failure_category") in valid_cats for r in failed_results)
    check("6.2 All failed results have valid failure_category", has_cat)
else:
    check("6.2 No failed results (all passed or skipped)", True)

# ──────────────────────────────────────────────────────────────
# 7. Phase 18: HTML 报告增强
# ──────────────────────────────────────────────────────────────
print("\n── 7. HTML 报告增强 ──")
if run_id2:
    try:
        r = requests.post(f"{BASE}/api/v2/test-runs/{run_id2}/report", json={"format": "html"}, timeout=SHORT)
        check("7.1 Report generation 200", r.status_code == 200)
        rpt = r.json()
        check("7.2 Report has report_url", "report_url" in rpt)

        r = requests.get(f"{BASE}/api/v2/test-runs/{run_id2}/report/download?format=html", timeout=SHORT)
        check("7.3 Report download 200", r.status_code == 200)
        html = r.text

        check("7.4 Report has '执行概览'", "执行概览" in html)
        check("7.5 Report has '失败分类统计'", "失败分类统计" in html)
        check("7.6 Report has '风险等级统计'", "风险等级统计" in html)
        check("7.7 Report has '跳过详情'", "跳过详情" in html)
        check("7.8 Report has '失败详情'", "失败详情" in html)
        check("7.9 Report has '通过率'", "通过率" in html)
        check("7.10 Report has '实际执行'", "实际执行" in html)
        check("7.11 Report has 'destructive'", "destructive" in html)
        check("7.12 Report has '排查建议'", "排查建议" in html)
        check("7.13 Report has project info", "项目:" in html or "Project" in html or "ERP" in html)
    except Exception as e:
        print(f"    ⚠️ SKIP: 报告生成异常 ({e.__class__.__name__})")
        for i in range(1, 14):
            check(f"7.{i} Skipped (error)", False)
else:
    print("    ⚠️ SKIP: 无 run_id, 跳过报告测试")
    for i in range(1, 14):
        check(f"7.{i} Skipped (no run_id)", False)

# ──────────────────────────────────────────────────────────────
# 8. 向后兼容: query-safe preset
# ──────────────────────────────────────────────────────────────
print("\n── 8. 向后兼容: query-safe Preset ──")
try:
    print("    [INFO] query-safe 批量执行中，请等待(最长60s)...")
    r = requests.post(
        f"{BASE}/api/v2/test-cases/batch-execute",
        headers=H,
        json={"preset": "query-safe", "environment_id": 1},
        timeout=60
    )
    # query-safe 可能没有匹配用例返回 400
    if r.status_code == 200:
        check("8.1 query-safe preset 200", True)
        qs = r.json()
        check("8.2 query-safe has results", len(qs.get("results", [])) > 0)
        check("8.3 query-safe has pass_rate", "pass_rate" in qs)
    elif r.status_code == 400:
        print(f"    [INFO] query-safe 无匹配用例(正常): {r.text[:100]}")
        check("8.1 query-safe returns 400 (no matching cases)", True)
        check("8.2 query-safe expected empty", True)
        check("8.3 query-safe expected empty", True)
    else:
        check("8.1 query-safe preset unexpected", False)
        check("8.2 skip", False)
        check("8.3 skip", False)
except Exception as e:
    print(f"    ⚠️ SKIP: 超时或异常 ({e.__class__.__name__})")
    for i in range(1, 4):
        check(f"8.{i} Skipped (timeout)", False)

# ──────────────────────────────────────────────────────────────
# 9. 单用例执行详情
# ──────────────────────────────────────────────────────────────
print("\n── 9. 单用例执行详情 ──")
try:
    r = requests.get(f"{BASE}/api/v2/test-cases", params={"limit": 1}, timeout=SHORT)
    if r.status_code == 200:
        tc_list = r.json()
        first_tc = None
        if isinstance(tc_list, list) and len(tc_list) > 0:
            first_tc = tc_list[0]
        elif isinstance(tc_list, dict):
            # 可能是 {"test_cases": [...]} 或 {"data": [...]}
            items = tc_list.get("test_cases") or tc_list.get("data") or []
            if isinstance(items, list) and len(items) > 0:
                first_tc = items[0]

        if first_tc:
            tc_id = first_tc.get("id")
            r = requests.post(
                f"{BASE}/api/v2/test-cases/{tc_id}/execute",
                headers=H,
                json={"environment_id": 1},
                timeout=30
            )
            check("9.1 Single execute 200", r.status_code == 200)
            se = r.json()
            check("9.2 Has run_id", "run_id" in se)
            check("9.3 Has status", "status" in se)
            check("9.4 Has duration_ms", "duration_ms" in se)
        else:
            check("9.1 No test case found", False)
            check("9.2 skip", False)
            check("9.3 skip", False)
            check("9.4 skip", False)
    else:
        check("9.1 Test case list failed", False)
        check("9.2 skip", False)
        check("9.3 skip", False)
        check("9.4 skip", False)
except Exception as e:
    print(f"    ⚠️ SKIP: 超时或异常 ({e.__class__.__name__})")
    for i in range(1, 5):
        check(f"9.{i} Skipped (timeout)", False)

# ──────────────────────────────────────────────────────────────
# 10. Demo 重置 向后兼容
# ──────────────────────────────────────────────────────────────
print("\n── 10. Demo 重置 ──")
r = requests.post(f"{BASE}/api/v2/demo/reset", timeout=SHORT)
check("10.1 Demo reset 200", r.status_code == 200)
d = r.json()
# reset 返回 {"code": 0, "data": {"project_id": ..., "test_case_count": ...}}
check("10.2 Reset success", d.get("code") == 0 and d.get("data", {}).get("test_case_count", 0) > 0)

# ──────────────────────────────────────────────────────────────
# 汇总
# ──────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
passed_count = sum(1 for _, ok in results if ok)
total_count = len(results)
failed_count = total_count - passed_count
print(f"  Results: {passed_count}/{total_count} passed, {failed_count} failed")

if failed_count > 0:
    print("\n  Failed tests:")
    for name, ok in results:
        if not ok:
            print(f"    ❌ {name}")

print("=" * 60)
exit(0 if failed_count == 0 else 1)
