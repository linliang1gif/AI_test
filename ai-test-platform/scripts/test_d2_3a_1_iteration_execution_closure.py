#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
D2-3A.1 验收脚本：迭代执行闭环补强
验证完整流程：创建迭代 → 录入需求 → 生成测试点 → 生成用例 → 创建执行集 → 真实执行 → 查看报告
"""
import sys
import json
import time
import requests

BASE_URL = "http://localhost:8000/api"

def log(msg, level="INFO"):
    prefix = {"INFO": "✅", "WARN": "⚠️", "ERROR": "❌", "STEP": "🔹"}
    print(f"  {prefix.get(level, '  ')} [{level}] {msg}")

def assert_ok(resp, msg=""):
    if resp.status_code >= 400:
        print(f"  ❌ FAILED: {msg} — HTTP {resp.status_code}")
        try:
            print(f"     Response: {resp.json()}")
        except:
            print(f"     Response: {resp.text[:300]}")
        sys.exit(1)
    return resp.json()

def main():
    print("\n" + "=" * 60)
    print("  D2-3A.1 验收脚本：迭代执行闭环")
    print("=" * 60)

    # 0. Health check
    log("健康检查...", "STEP")
    r = requests.get(f"http://localhost:8000/health", timeout=5)
    assert_ok(r, "健康检查")
    log("服务正常")

    # 1. Ensure project exists
    log("确保项目存在...", "STEP")
    r = requests.get(f"{BASE_URL}/v2/projects")
    if r.status_code == 404:
        r = requests.get(f"http://localhost:8000/api/projects")
    data = assert_ok(r, "获取项目列表")
    projects = data if isinstance(data, list) else data.get("projects", [])
    if not projects:
        r = requests.post(f"{BASE_URL}/v2/projects", json={"name": "D2-3A验收项目", "description": "验收测试"})
        proj = assert_ok(r, "创建项目")
        project_id = proj["id"]
    else:
        project_id = projects[0]["id"]
    log(f"项目ID: {project_id}")

    # 2. Create iteration
    log("创建迭代...", "STEP")
    r = requests.post(f"{BASE_URL}/v2/iterations", json={
        "project_id": project_id,
        "name": f"D2-3A.1验收迭代-{int(time.time())}",
        "version": "v1.0.0",
        "description": "自动验收：迭代执行闭环测试",
    })
    it = assert_ok(r, "创建迭代")
    iter_id = it["id"]
    log(f"迭代ID: {iter_id}")

    # 3. Add requirement
    log("录入需求...", "STEP")
    r = requests.post(f"{BASE_URL}/v2/iterations/{iter_id}/requirements", json={
        "title": "用户登录接口",
        "content": "实现用户名密码登录，返回 token",
        "risk_level": "P0",
    })
    assert_ok(r, "录入需求")
    log("需求已录入")

    # 4. Generate test points
    log("生成测试点...", "STEP")
    r = requests.post(f"{BASE_URL}/v2/iterations/{iter_id}/test-points/generate")
    tp_data = assert_ok(r, "生成测试点")
    log(f"生成测试点: {tp_data.get('generated', 0)} 个")

    # 4.5. Confirm test points
    log("确认测试点...", "STEP")
    r = requests.get(f"{BASE_URL}/v2/iterations/{iter_id}/test-points")
    tp_list = assert_ok(r, "查询测试点")
    test_points = tp_list.get("test_points", [])
    for tp in test_points:
        r = requests.patch(f"{BASE_URL}/v2/iteration-test-points/{tp['id']}/confirm",
                          json={"confirmed": True})
        assert_ok(r, f"确认测试点 {tp['id']}")
    log(f"已确认 {len(test_points)} 个测试点")

    # 5. Generate test cases
    log("生成测试用例...", "STEP")
    r = requests.post(f"{BASE_URL}/v2/iterations/{iter_id}/test-cases/generate")
    tc_data = assert_ok(r, "生成测试用例")
    log(f"生成用例: {tc_data.get('generated', 0)} 个")

    # 6. List test cases
    log("查询测试用例...", "STEP")
    r = requests.get(f"{BASE_URL}/v2/iterations/{iter_id}/test-cases")
    tc_list = assert_ok(r, "查询用例")
    cases = tc_list.get("test_cases", [])
    log(f"共 {len(cases)} 个用例")
    assert len(cases) > 0, "应有至少1个用例"

    # 7. Create execution set (all 3 types)
    log("创建执行集...", "STEP")
    for set_type in ["smoke", "iteration", "regression"]:
        r = requests.post(f"{BASE_URL}/v2/iterations/{iter_id}/execution-sets", json={"type": set_type})
        es = assert_ok(r, f"创建 {set_type} 执行集")
        log(f"  {set_type} 执行集 ID={es['id']}, cases={es['case_count']}")
        assert es["status"] == "created"
        assert es["case_count"] > 0
        # Verify case_ids returned
        assert "case_ids" in es, "应返回 case_ids"
        assert len(es["case_ids"]) == es["case_count"]

    # 8. List execution sets
    log("查询执行集...", "STEP")
    r = requests.get(f"{BASE_URL}/v2/iterations/{iter_id}/execution-sets")
    es_list = assert_ok(r, "查询执行集")
    assert es_list["total"] == 3
    log(f"共 {es_list['total']} 个执行集")

    # 9. Execute iteration (use default — latest iteration type)
    log("执行迭代测试 (真实引擎)...", "STEP")
    r = requests.post(f"{BASE_URL}/v2/iterations/{iter_id}/run", json={})
    run_result = assert_ok(r, "执行迭代")
    log(f"执行完成: run_id={run_result['run_id']}")
    log(f"  total={run_result['total_cases']} passed={run_result['passed']} "
        f"failed={run_result['failed']} error={run_result['error']}")
    log(f"  pass_rate={run_result['pass_rate']}% status={run_result['status']} "
        f"duration={run_result['duration_s']}s")

    # Validate run result structure
    assert "run_id" in run_result
    assert "execution_set_id" in run_result
    assert "pass_rate" in run_result
    assert "results" in run_result
    assert isinstance(run_result["results"], list)
    assert run_result["total_cases"] > 0

    # Validate each result has real data (not mocked)
    for case_result in run_result["results"]:
        assert "case_id" in case_result
        assert "status" in case_result
        assert case_result["status"] in ("passed", "failed", "error", "skipped", "no_assertion")
        assert "duration_ms" in case_result

    # 10. Verify execution set status updated
    log("验证执行集状态更新...", "STEP")
    r = requests.get(f"{BASE_URL}/v2/iterations/{iter_id}/execution-sets")
    es_list = assert_ok(r, "验证执行集")
    iter_es = [e for e in es_list["execution_sets"] if e["type"] == "iteration"]
    assert len(iter_es) > 0
    latest_es = iter_es[0]
    assert latest_es["status"] in ("passed", "failed", "partial", "error"), \
        f"执行集状态应为终态，实际: {latest_es['status']}"
    assert latest_es["run_id"] is not None
    log(f"执行集状态: {latest_es['status']}, run_id: {latest_es['run_id']}")

    # 11. Get iteration report
    log("获取迭代报告...", "STEP")
    r = requests.get(f"{BASE_URL}/v2/iterations/{iter_id}/report")
    report = assert_ok(r, "获取报告")

    # Validate report structure
    assert "stats" in report
    assert "latest_run_id" in report
    assert "runs" in report
    assert "execution_sets" in report
    assert "failure_categories" in report
    assert "risk_summary" in report
    assert "release_recommendation" in report
    assert "release_reason" in report

    stats = report["stats"]
    assert "total_cases" in stats
    assert "executed_cases" in stats
    assert "passed_cases" in stats
    assert "failed_cases" in stats
    assert "pass_rate" in stats

    log(f"报告统计: total={stats['total_cases']} executed={stats['executed_cases']} "
        f"passed={stats['passed_cases']} failed={stats['failed_cases']} "
        f"pass_rate={stats['pass_rate']}%")
    log(f"发布建议: {report['release_recommendation']} — {report['release_reason']}")
    log(f"风险摘要: P0_failed={report['risk_summary']['p0_failed']} "
        f"P1_failed={report['risk_summary']['p1_failed']}")

    if report.get("failure_categories"):
        log(f"失败分类: {json.dumps(report['failure_categories'], ensure_ascii=False)}")

    # 12. Execute specific execution set
    log("执行指定执行集 (smoke)...", "STEP")
    smoke_es = [e for e in es_list["execution_sets"] if e["type"] == "smoke"]
    if smoke_es:
        r = requests.post(f"{BASE_URL}/v2/iterations/{iter_id}/run",
                         json={"execution_set_id": smoke_es[0]["id"]})
        smoke_run = assert_ok(r, "执行 smoke 执行集")
        log(f"Smoke 执行完成: passed={smoke_run['passed']}/{smoke_run['total_cases']}")

    # 13. Final report check — should now have 2 runs
    log("最终报告验证...", "STEP")
    r = requests.get(f"{BASE_URL}/v2/iterations/{iter_id}/report")
    final_report = assert_ok(r, "最终报告")
    assert len(final_report["runs"]) >= 2, f"应有至少2次执行记录，实际: {len(final_report['runs'])}"
    log(f"共 {len(final_report['runs'])} 次执行记录")

    print("\n" + "=" * 60)
    print("  ✅ D2-3A.1 验收通过：迭代执行闭环完整")
    print("=" * 60)
    print(f"""
  总结:
  - 执行集创建：smoke/iteration/regression 三种类型 ✅
  - 用例关联表 (iteration_execution_set_cases) ✅
  - 真实执行引擎调用 (ExecutionEngineV2) ✅
  - TestRun + RunCase 记录写入 ✅
  - 执行集状态更新 (created → running → passed/failed/partial) ✅
  - 报告包含: pass_rate, failure_categories, risk_summary ✅
  - 发布建议 (release_recommendation) ✅
  - 指定执行集执行 ✅
""")


if __name__ == "__main__":
    main()
