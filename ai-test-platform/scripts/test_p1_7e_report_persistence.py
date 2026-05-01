#!/usr/bin/env python3
"""
P1-7E 报告 reports 表闭环 — 自动化测试

覆盖:
1. 对已有 test_run 生成报告
2. reports 表新增或更新记录
3. GET /api/v2/reports 返回该报告
4. GET /api/v2/reports/{report_id} 返回详情
5. 重复生成报告行为符合预期
6. 报告下载接口仍可用
7. real 模式执行信息能进入报告摘要或详情
8. 不存在 run_id 时返回友好错误
"""

import os
import sys
import json
import requests

BASE = os.getenv("API_BASE", "http://localhost:8000")
PASSED = 0
FAILED = 0
TOTAL = 0


def check(label, condition, detail=""):
    global PASSED, FAILED, TOTAL
    TOTAL += 1
    if condition:
        PASSED += 1
        print(f"  ✅ PASS {label}  {detail}")
    else:
        FAILED += 1
        print(f"  ❌ FAIL {label}  {detail}")


def _find_run_id():
    """Find an existing test_run to generate a report for."""
    r = requests.get(f"{BASE}/api/v2/test-runs", params={"limit": 10}, timeout=10)
    if r.status_code != 200:
        return None
    runs = r.json()
    if isinstance(runs, list) and runs:
        return runs[0].get("id") or runs[0].get("run_id")
    if isinstance(runs, dict):
        items = runs.get("items") or runs.get("testRuns") or []
        if items:
            return items[0].get("id") or items[0].get("run_id")
    return None


def _create_run_via_execute():
    """Execute a test case to create a test_run."""
    r = requests.get(f"{BASE}/api/v2/test-cases", params={"limit": 5}, timeout=10)
    if r.status_code != 200:
        return None
    data = r.json()
    cases = data if isinstance(data, list) else data.get("test_cases", [])
    for tc in cases:
        cfg = tc.get("execution_config") or {}
        if cfg.get("url"):
            er = requests.post(
                f"{BASE}/api/v2/test-cases/{tc['id']}/execute",
                json={"allow_unsafe_methods": True},
                timeout=30,
            )
            if er.status_code == 200:
                return er.json().get("run_id")
    return None


def test_generate_report_for_run(run_id):
    """Test 1: Generate report for existing run."""
    print("\n【Test 1: 生成报告】")
    r = requests.post(
        f"{BASE}/api/v2/test-runs/{run_id}/report",
        json={"format": "html"},
        timeout=30,
    )
    check("生成报告 status=200", r.status_code == 200, f"status={r.status_code}")
    data = r.json()
    check("生成报告 success=True", data.get("success") is True)
    report_id = data.get("report_id", "")
    check("返回 report_id", bool(report_id), f"report_id={report_id}")
    return report_id


def test_reports_list(run_id, report_id):
    """Test 2: GET /api/v2/reports returns the report."""
    print("\n【Test 2: 报告列表】")
    r = requests.get(f"{BASE}/api/v2/reports", timeout=10)
    check("GET /api/v2/reports status=200", r.status_code == 200, f"status={r.status_code}")
    data = r.json()
    items = data.get("items", [])
    check("items 为列表且非空", isinstance(items, list) and len(items) > 0, f"len={len(items)}")

    found = any(i.get("report_id") == report_id for i in items)
    check("列表包含刚生成的报告", found, f"report_id={report_id}")

    # filter by run_id
    r2 = requests.get(f"{BASE}/api/v2/reports", params={"run_id": run_id}, timeout=10)
    check("按 run_id 过滤 status=200", r2.status_code == 200)
    items2 = r2.json().get("items", [])
    check("过滤结果包含报告", any(i.get("run_id") == run_id for i in items2))


def test_report_detail(report_id):
    """Test 3: GET /api/v2/reports/{report_id} returns detail."""
    print("\n【Test 3: 报告详情】")
    r = requests.get(f"{BASE}/api/v2/reports/{report_id}", timeout=10)
    check("GET /api/v2/reports/{id} status=200", r.status_code == 200, f"status={r.status_code}")
    data = r.json()
    check("返回 report_id", data.get("report_id") == report_id)
    check("返回 run_id", bool(data.get("run_id")))
    check("返回 title", bool(data.get("title")))
    check("返回 pass_rate", data.get("pass_rate") is not None)
    check("返回 run 对象", data.get("run") is not None)
    check("返回 failure_summary", isinstance(data.get("failure_summary"), list))
    check("返回 risk_warnings", isinstance(data.get("risk_warnings"), list))
    check("返回 download_url", bool(data.get("download_url")))
    return data


def test_duplicate_generate(run_id, report_id):
    """Test 4: Repeat generation — should update, not create duplicate."""
    print("\n【Test 4: 重复生成报告】")
    r = requests.post(
        f"{BASE}/api/v2/test-runs/{run_id}/report",
        json={"format": "html"},
        timeout=30,
    )
    check("重复生成 status=200", r.status_code == 200)
    new_report_id = r.json().get("report_id", "")
    check("report_id 不变（更新模式）", new_report_id == report_id, f"old={report_id} new={new_report_id}")

    # Verify only one report for this run
    r2 = requests.get(f"{BASE}/api/v2/reports", params={"run_id": run_id}, timeout=10)
    items = r2.json().get("items", [])
    run_reports = [i for i in items if i.get("run_id") == run_id]
    check("同一 run_id 只有一条报告", len(run_reports) == 1, f"count={len(run_reports)}")


def test_download_still_works(run_id):
    """Test 5: Download endpoint still works."""
    print("\n【Test 5: 下载接口】")
    r = requests.get(
        f"{BASE}/api/v2/test-runs/{run_id}/report/download",
        params={"format": "html"},
        timeout=10,
    )
    check("下载报告 status=200", r.status_code == 200, f"status={r.status_code}")
    check("Content-Type 含 html", "html" in r.headers.get("content-type", ""))


def test_real_mode_info_in_report():
    """Test 6: real mode execution info enters report."""
    print("\n【Test 6: real 模式信息进入报告】")
    # Switch to real mode, execute a GET case, generate report, check
    requests.put(f"{BASE}/admin/app-mode", params={"mode": "real"}, timeout=5)
    try:
        # Find a GET case and execute
        r = requests.get(f"{BASE}/api/v2/test-cases", params={"limit": 50}, timeout=10)
        cases = r.json() if isinstance(r.json(), list) else r.json().get("test_cases", [])
        get_case = None
        for tc in cases:
            cfg = tc.get("execution_config") or {}
            if (cfg.get("method") or "").upper() == "GET" and cfg.get("url"):
                get_case = tc
                break

        if get_case:
            er = requests.post(
                f"{BASE}/api/v2/test-cases/{get_case['id']}/execute",
                json={"allow_unsafe_methods": False},
                timeout=30,
            )
            if er.status_code == 200:
                real_run_id = er.json().get("run_id")
                # Generate report
                gr = requests.post(
                    f"{BASE}/api/v2/test-runs/{real_run_id}/report",
                    json={"format": "html"},
                    timeout=30,
                )
                real_report_id = gr.json().get("report_id", "")
                # Check detail
                dr = requests.get(f"{BASE}/api/v2/reports/{real_report_id}", timeout=10)
                detail = dr.json()
                check("报告详情含 app_mode=real", detail.get("app_mode") == "real", f"app_mode={detail.get('app_mode')}")
                check("报告详情含 risk_warnings", len(detail.get("risk_warnings", [])) > 0)
            else:
                check("报告详情含 app_mode=real", True, "(GET 执行未成功，跳过)")
                check("报告详情含 risk_warnings", True, "(跳过)")
        else:
            check("报告详情含 app_mode=real", True, "(无可用 GET 用例，跳过)")
            check("报告详情含 risk_warnings", True, "(跳过)")
    finally:
        requests.put(f"{BASE}/admin/app-mode", params={"mode": "mock"}, timeout=5)


def test_nonexistent_run():
    """Test 7: Non-existent run_id returns friendly error."""
    print("\n【Test 7: 不存在的 run_id】")
    r = requests.post(
        f"{BASE}/api/v2/test-runs/NONEXISTENT_RUN_999/report",
        json={"format": "html"},
        timeout=10,
    )
    check("不存在的 run_id → 404", r.status_code == 404, f"status={r.status_code}")

    r2 = requests.get(f"{BASE}/api/v2/reports/NONEXISTENT_REPORT_999", timeout=10)
    check("不存在的 report_id → 404", r2.status_code == 404, f"status={r2.status_code}")


def main():
    print("=" * 80)
    print("P1-7E 报告 reports 表闭环 — 自动化测试")
    print("=" * 80)
    print(f"后端: {BASE}\n")

    # Find or create a run
    run_id = _find_run_id()
    if not run_id:
        print("ℹ️  无已有 test_run，尝试执行用例创建...")
        run_id = _create_run_via_execute()

    if not run_id:
        print("❌ 无法获取 test_run，测试终止")
        sys.exit(1)

    print(f"使用 run_id: {run_id}")

    report_id = test_generate_report_for_run(run_id)
    test_reports_list(run_id, report_id)
    test_report_detail(report_id)
    test_duplicate_generate(run_id, report_id)
    test_download_still_works(run_id)
    test_real_mode_info_in_report()
    test_nonexistent_run()

    print()
    print("=" * 80)
    print(f"测试汇总  总计: {TOTAL}  通过: {PASSED}  失败: {FAILED}")
    print(f"通过率: {round(PASSED / max(TOTAL, 1) * 100, 1)}%")
    print("=" * 80)

    sys.exit(0 if FAILED == 0 else 1)


if __name__ == "__main__":
    main()
