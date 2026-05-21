#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""D2-3A.2 acceptance: real iteration execution and report trust hardening.

The script assumes backend is running at BASE_URL, default http://127.0.0.1:8001.
It creates a disposable iteration, real executable API cases, runs a smoke set
through ExecutionEngineV2, and verifies report data against RunCase rows.
"""
from __future__ import annotations

import os
import sys
import time
import uuid
import sqlite3
from datetime import datetime
from pathlib import Path

import requests


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8001").rstrip("/")
BASE = f"{BASE_URL}/api/v2"
SECRET_PROBE = "abc123SECRET999"
SECRET_QUERY = (
    f"token={SECRET_PROBE}&authorization={SECRET_PROBE}"
    f"&cookie={SECRET_PROBE}&api_key={SECRET_PROBE}"
    f"&password={SECRET_PROBE}&secret={SECRET_PROBE}"
)


def check(condition, message):
    if not condition:
        raise AssertionError(message)
    print(f"[PASS] {message}")


def request(method, path, **kwargs):
    headers = kwargs.pop("headers", {})
    headers.setdefault("X-Trace-Id", f"d2-3a2-{uuid.uuid4().hex[:10]}")
    resp = requests.request(method, f"{BASE_URL}{path}", headers=headers, timeout=180, **kwargs)
    check(resp.headers.get("X-Trace-Id"), f"X-Trace-Id exists: {method} {path}")
    return resp


def json_ok(resp, label, expected=(200, 201)):
    if resp.status_code not in expected:
        raise AssertionError(f"{label} failed: HTTP {resp.status_code} {resp.text[:500]}")
    return resp.json()


def assert_standard_error(resp, label):
    check(resp.status_code >= 400, f"{label} returns HTTP error")
    data = resp.json()
    for key in ("code", "message", "trace_id", "details"):
        check(key in data, f"{label} standard error has {key}")
    body_text = resp.text.lower()
    for sensitive in ("authorization", "cookie", "password", "api_key", "secret", "token", SECRET_PROBE.lower()):
        check(sensitive not in body_text, f"{label} does not leak {sensitive}")
    return data


def local_db_path() -> Path:
    raw = Path(os.getenv("DB_PATH", "data/test_platform.db"))
    return raw if raw.is_absolute() else PROJECT_ROOT / raw


def insert_empty_execution_set(iteration_id, marker):
    db_path = local_db_path()
    check(db_path.exists(), f"本地 SQLite 数据库存在: {db_path}")
    now = datetime.now().isoformat(sep=" ", timespec="seconds")
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO iteration_execution_sets
                (iteration_id, name, type, status, case_count, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                iteration_id,
                f"D2-3A.2 empty set {marker}",
                "smoke",
                "created",
                0,
                now,
                now,
            ),
        )
        conn.commit()
        return cur.lastrowid


def create_project(marker):
    resp = request("POST", "/api/v2/projects", json={
        "name": f"D2-3A.2真实执行验证项目-{marker}",
        "description": "created by test_d2_3a_2_real_iteration_validation.py",
        "owner": "qa",
        "team": "qa",
    })
    data = json_ok(resp, "create project")
    check(data.get("id"), "创建迭代验证项目成功")
    return data["id"]


def create_environment(project_id):
    resp = request("POST", "/api/v2/environments", json={
        "project_id": project_id,
        "name": "test",
        "base_url": BASE_URL,
        "is_protected": False,
        "allow_write": True,
        "timeout_seconds": 10,
        "retry_count": 0,
    })
    data = json_ok(resp, "create environment")
    check(data.get("id"), "创建真实执行测试环境成功")
    return data["id"]


def create_iteration(project_id, marker):
    resp = request("POST", "/api/v2/iterations", json={
        "project_id": project_id,
        "name": f"D2-3A.2真实执行验证迭代-{marker}",
        "version": f"d2-3a2-{marker}",
        "description": "验证报告是否来自真实 TestRun/RunCase 聚合",
        "status": "testing",
        "owner": "qa",
        "test_owner": "qa",
    })
    data = json_ok(resp, "create iteration")
    check(data.get("id"), "创建迭代成功")
    return data["id"]


def create_requirement(iteration_id):
    resp = request("POST", f"/api/v2/iterations/{iteration_id}/requirements", json={
        "title": "D2-3A.2 报告可信度验证",
        "content": "需要通过真实执行结果证明迭代报告统计来自 TestRun、RunCase、ExecutionSet 聚合。",
        "source_type": "manual",
        "risk_level": "P1",
    })
    json_ok(resp, "create requirement")
    check(True, "录入需求成功")


def analyze_and_confirm_points(iteration_id):
    resp = request("POST", f"/api/v2/iterations/{iteration_id}/ai/analyze-requirements")
    json_ok(resp, "analyze requirements")
    check(True, "AI 解析需求成功")

    resp = request("POST", f"/api/v2/iterations/{iteration_id}/test-points/generate")
    data = json_ok(resp, "generate test points")
    check(data.get("generated", 0) >= 3, "生成至少 3 个测试点成功")

    resp = request("GET", f"/api/v2/iterations/{iteration_id}/test-points")
    data = json_ok(resp, "list test points")
    points = data.get("test_points", [])
    check(points, "查询测试点成功")
    check(len(points) >= 3, "查询到至少 3 个测试点")
    for tp in points[:3]:
        resp = request("PATCH", f"/api/v2/iteration-test-points/{tp['id']}/confirm", json={"confirmed": True})
        json_ok(resp, f"confirm test point {tp['id']}")
    check(True, "确认至少 3 个测试点成功")


def create_case(title, execution_config, assertions, project_id):
    resp = request("POST", "/api/v2/test-cases", json={
        "title": title,
        "case_type": "api",
        "priority": "high",
        "module": "D2-3A.2",
        "expected": "真实执行结果写入 RunCase",
        "execution_config": execution_config,
        "assertions": assertions,
        "project_id": project_id,
        "tags": ["d2-3a2-real-validation"],
    })
    data = json_ok(resp, f"create case {title}")
    case_id = data.get("test_case_id")
    check(case_id, f"补充真实可执行 TestCase: {title}")
    return case_id


def create_invalid_case(project_id):
    return create_case(
        "D2-3A.2 invalid - missing execution_config",
        {},
        [{"type": "status_code", "expected": 200}],
        project_id,
    )


def create_real_cases(project_id):
    passed_case = create_case(
        "D2-3A.2 passed - GET /health status 200",
        {"method": "GET", "url": "/health", "timeout": 5},
        [{"type": "status_code", "expected": 200}],
        project_id,
    )
    failed_case = create_case(
        "D2-3A.2 failed - GET /health impossible code",
        {"method": "GET", "url": "/health", "timeout": 5},
        [
            {"type": "status_code", "expected": 200},
            {"type": "json_path_equals", "path": "code", "expected": 999999},
        ],
        project_id,
    )
    error_case = create_case(
        "D2-3A.2 error - unreachable per-case base_url",
        {"method": "GET", "url": "/health", "base_url": "http://127.0.0.1:9", "timeout": 1},
        [{"type": "status_code", "expected": 200}],
        project_id,
    )
    return [passed_case, failed_case, error_case]


def assign_cases(iteration_id, case_ids):
    resp = request("POST", f"/api/v2/iterations/{iteration_id}/assign-cases", json={"case_ids": case_ids})
    data = json_ok(resp, "assign cases")
    check(data.get("updated") == len(case_ids), "测试用例已分配到迭代")


def create_smoke_set(iteration_id):
    resp = request("POST", f"/api/v2/iterations/{iteration_id}/execution-sets", json={
        "type": "smoke",
        "name": "D2-3A.2 real smoke set",
    })
    data = json_ok(resp, "create smoke execution set")
    check(data.get("case_count", 0) >= 3, "创建 smoke 执行集成功")
    return data["id"], data.get("case_ids", [])


def run_smoke(iteration_id, execution_set_id, environment_id):
    resp = request("POST", f"/api/v2/iterations/{iteration_id}/run", json={
        "execution_set_id": execution_set_id,
        "environment_id": environment_id,
    })
    data = json_ok(resp, "run smoke execution set")
    check(data.get("run_id"), "执行 smoke 执行集成功")
    check(data.get("total_cases", 0) >= 3, "真实执行返回用例统计")
    return data


def load_run_cases(run_id):
    resp = request("GET", f"/api/v2/test-runs/{run_id}/cases")
    rows = json_ok(resp, "load run cases")
    check(rows, "RunCase 可通过接口读取，证明已真实落库")

    details = []
    for row in rows:
        resp = request("GET", f"/api/v2/test-runs/{run_id}/cases/{row['id']}")
        detail = json_ok(resp, f"load run case detail {row['id']}")
        details.append({
            "id": detail["id"],
            "case_id": detail["test_case_id"],
            "status": detail["status"],
            "error_type": detail.get("error_type"),
            "request_snapshot": detail.get("request_snapshot"),
            "response_snapshot": detail.get("response_snapshot"),
        })
    return details


def verify_empty_report(iteration_id):
    resp = request("GET", f"/api/v2/iterations/{iteration_id}/report")
    report = json_ok(resp, "get empty report")
    check(report.get("data_source") == "real_run_case", "空态 report.data_source 仍标记真实来源")
    check(report.get("has_real_result") is False, "没执行过时返回明确空态")
    check(report.get("latest_run_id") is None, "空态 latest_run_id 为空")
    check(report.get("total_cases") == 0, "空态 total_cases 不伪造")
    check(report.get("executed_cases") == 0, "空态 executed_cases 不伪造")
    check(report.get("pass_rate") == 0.0, "空态 pass_rate 为 0")
    check(report.get("empty") is True, "空态 empty=true")
    check(report.get("message") == "暂无真实执行结果，请先创建执行集并执行测试", "空态提示明确")
    check(report.get("failure_categories") == {}, "空态 failure_categories 为空对象")
    check(report.get("risk_summary") == {}, "空态 risk_summary 为空对象")


def verify_report(iteration_id, run_id, execution_set_id, run_cases, set_case_count):
    resp = request("GET", f"/api/v2/iterations/{iteration_id}/report")
    report = json_ok(resp, "get report")

    passed = sum(1 for rc in run_cases if rc["status"] == "passed")
    failed = sum(1 for rc in run_cases if rc["status"] == "failed")
    error = sum(1 for rc in run_cases if rc["status"] == "error")
    executed = len(run_cases)
    expected_pass_rate = round(passed / executed * 100, 1) if executed else 0.0
    expected_categories = {}
    for rc in run_cases:
        if rc["status"] in ("failed", "error"):
            category = rc["error_type"] or ("assertion_error" if rc["status"] == "failed" else "unknown_error")
            expected_categories[category] = expected_categories.get(category, 0) + 1

    check(report.get("data_source") == "real_run_case", "report.data_source 标记真实 RunCase")
    check(report.get("latest_run_id") == run_id, "report.latest_run_id 来自最新 TestRun")
    check(report.get("latest_execution_set_id") == execution_set_id, "report.latest_execution_set_id 来自 ExecutionSet")
    check(report.get("generated_at"), "report.generated_at 不为空")
    check(report.get("total_cases") == set_case_count, "report.total_cases 与执行集用例数一致")
    check(report.get("executed_cases") == executed, "report.executed_cases 与 RunCase 数一致")
    check(report.get("passed_cases") == passed, "report.passed_cases 与 RunCase 聚合一致")
    check(report.get("failed_cases") == failed, "report.failed_cases 与 RunCase 聚合一致")
    check(report.get("error_cases") == error, "report.error_cases 与 RunCase 聚合一致")
    check(report.get("pass_rate") == expected_pass_rate, "report.pass_rate 计算正确")
    check(report.get("failure_categories") == expected_categories, "report.failure_categories 来自真实 RunCase 聚合")
    check(report.get("release_recommendation"), "report.release_recommendation 不为空")
    check(report.get("release_reason"), "report.release_reason 不为空")
    return report


def verify_invalid_base_url_error(iteration_id, execution_set_id):
    resp = request("POST", f"/api/v2/iterations/{iteration_id}/run", json={
        "execution_set_id": execution_set_id,
        "base_url": f"ftp://invalid.example?{SECRET_QUERY}",
    })
    err = assert_standard_error(resp, "run invalid base_url")
    check(err.get("code") == "INVALID_BASE_URL", "错误响应 code 明确")


def verify_422_error_shape():
    resp = request("POST", "/api/v2/iterations", json={
        "project_id": "not-an-int",
        "name": "D2-3A.2 422 标准错误验证",
    })
    err = assert_standard_error(resp, "422 validation error")
    check(err.get("code") == "VALIDATION_ERROR", "422 错误响应 code 标准化")


def verify_run_prechecks(env_project_id, environment_id, marker):
    resp = request("POST", "/api/v2/iterations/999999999/run", json={
        "base_url": BASE_URL,
    })
    err = assert_standard_error(resp, "run iteration not found")
    check(err.get("code") == "ITERATION_NOT_FOUND", "iteration 不存在错误明确")

    iter_for_missing_set = create_iteration(env_project_id, f"{marker}-missing-set")
    resp = request("POST", f"/api/v2/iterations/{iter_for_missing_set}/run", json={
        "execution_set_id": 999999999,
        "environment_id": environment_id,
    })
    err = assert_standard_error(resp, "run execution set not found")
    check(err.get("code") == "EXECUTION_SET_NOT_FOUND", "execution_set 不存在错误明确")

    empty_set_id = insert_empty_execution_set(iter_for_missing_set, marker)
    resp = request("POST", f"/api/v2/iterations/{iter_for_missing_set}/run", json={
        "execution_set_id": empty_set_id,
        "environment_id": environment_id,
    })
    err = assert_standard_error(resp, "run empty execution set")
    check(err.get("code") == "EXECUTION_SET_EMPTY", "execution_set 无用例错误明确")

    missing_env_project = create_project(f"{marker}-no-env")
    iter_without_env = create_iteration(missing_env_project, f"{marker}-no-env")
    valid_case = create_case(
        "D2-3A.2 precheck - valid case without environment",
        {"method": "GET", "url": "/health", "timeout": 5},
        [{"type": "status_code", "expected": 200}],
        missing_env_project,
    )
    assign_cases(iter_without_env, [valid_case])
    set_without_env, _ = create_smoke_set(iter_without_env)
    resp = request("POST", f"/api/v2/iterations/{iter_without_env}/run", json={
        "execution_set_id": set_without_env,
    })
    err = assert_standard_error(resp, "run environment missing")
    check(err.get("code") == "ENVIRONMENT_REQUIRED", "环境配置缺失错误明确")

    invalid_iter = create_iteration(env_project_id, f"{marker}-invalid-case")
    invalid_case = create_invalid_case(env_project_id)
    assign_cases(invalid_iter, [invalid_case])
    invalid_set_id, _ = create_smoke_set(invalid_iter)
    resp = request("POST", f"/api/v2/iterations/{invalid_iter}/run", json={
        "execution_set_id": invalid_set_id,
        "environment_id": environment_id,
    })
    err = assert_standard_error(resp, "run case missing execution fields")
    check(err.get("code") == "TEST_CASE_EXECUTION_CONFIG_INVALID", "用例缺执行字段错误明确")


def main():
    marker = uuid.uuid4().hex[:8]
    print(f"D2-3A.2 real iteration validation against {BASE_URL}")

    resp = request("GET", "/api/v2/health/full")
    json_ok(resp, "health/full")
    check(True, "health/full 健康检查通过")
    verify_422_error_shape()

    project_id = create_project(marker)
    environment_id = create_environment(project_id)
    iteration_id = create_iteration(project_id, marker)
    verify_empty_report(iteration_id)
    create_requirement(iteration_id)
    analyze_and_confirm_points(iteration_id)

    verify_run_prechecks(project_id, environment_id, marker)

    case_ids = create_real_cases(project_id)
    assign_cases(iteration_id, case_ids)
    execution_set_id, set_case_ids = create_smoke_set(iteration_id)
    check(set(case_ids).issubset(set(set_case_ids)), "smoke 执行集包含本次补充的真实用例")

    verify_invalid_base_url_error(iteration_id, execution_set_id)

    run_result = run_smoke(iteration_id, execution_set_id, environment_id)
    run_id = run_result["run_id"]
    run_cases = load_run_cases(run_id)
    set_case_count = len(set_case_ids)
    check(len(run_cases) == len(case_ids), "RunCase 已真实写入")
    check(any(rc["status"] == "passed" for rc in run_cases), "至少产生 1 条 passed RunCase")
    check(any(rc["status"] in ("failed", "error") for rc in run_cases), "至少产生 1 条 failed 或 error RunCase")
    check(any(rc["status"] == "error" and rc["error_type"] for rc in run_cases), "error 用例产生明确错误分类")
    check(any(rc["response_snapshot"] for rc in run_cases if rc["status"] in ("passed", "failed")), "RunCase 包含真实响应快照")

    verify_report(iteration_id, run_id, execution_set_id, run_cases, set_case_count)

    print("PASS D2-3A.2 real iteration validation")
    print(f"iteration_id={iteration_id} execution_set_id={execution_set_id} run_id={run_id}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
