#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""D2-3A.2 offline contract check.

This is a fast in-process companion to test_d2_3a_2_real_iteration_validation.py.
It uses FastAPI TestClient, so it does not require port 8001 to be running.
The real validation script is still the source of truth for end-to-end HTTP
execution.
"""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def check(condition, message):
    if not condition:
        raise AssertionError(message)
    print(f"[PASS] {message}")


def json_ok(resp, label, expected=(200, 201)):
    if resp.status_code not in expected:
        raise AssertionError(f"{label} failed: HTTP {resp.status_code} {resp.text[:500]}")
    check(resp.headers.get("X-Trace-Id"), f"X-Trace-Id exists: {label}")
    return resp.json()


def assert_standard_error(resp, label, code):
    check(resp.status_code >= 400, f"{label} returns HTTP error")
    check(resp.headers.get("X-Trace-Id"), f"X-Trace-Id exists: {label}")
    data = resp.json()
    for key in ("code", "message", "trace_id", "details"):
        check(key in data, f"{label} standard error has {key}")
    check(data.get("code") == code, f"{label} code={code}")
    return data


def main():
    import sys

    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    from backend.app import create_app

    marker = uuid.uuid4().hex[:8]
    client = TestClient(create_app())

    project = json_ok(client.post("/api/v2/projects", json={
        "name": f"D2-3A.2离线契约验证项目-{marker}",
        "description": "offline contract check",
        "owner": "qa",
        "team": "qa",
    }), "create project")
    project_id = project["id"]

    env = json_ok(client.post("/api/v2/environments", json={
        "project_id": project_id,
        "name": "test",
        "base_url": "http://127.0.0.1:8001",
        "is_protected": False,
        "allow_write": True,
        "timeout_seconds": 10,
        "retry_count": 0,
    }), "create environment")
    env_id = env["id"]

    iteration = json_ok(client.post("/api/v2/iterations", json={
        "project_id": project_id,
        "name": f"D2-3A.2离线契约验证迭代-{marker}",
        "version": f"offline-{marker}",
        "status": "testing",
        "owner": "qa",
        "test_owner": "qa",
    }), "create iteration")
    iteration_id = iteration["id"]

    empty_report = json_ok(client.get(f"/api/v2/iterations/{iteration_id}/report"), "get empty report")
    check(empty_report.get("data_source") == "real_run_case", "empty report keeps real_run_case source")
    check(empty_report.get("has_real_result") is False, "empty report has_real_result=false")
    check(empty_report.get("total_cases") == 0, "empty report total_cases=0")
    check(empty_report.get("executed_cases") == 0, "empty report executed_cases=0")

    def create_case(title, execution_config):
        data = json_ok(client.post("/api/v2/test-cases", json={
            "title": title,
            "case_type": "api",
            "priority": "high",
            "module": "D2-3A.2",
            "expected": "真实执行结果写入 RunCase",
            "execution_config": execution_config,
            "assertions": [{"type": "status_code", "expected": 200}],
            "project_id": project_id,
            "tags": ["d2-3a2-offline-contract"],
        }), f"create case {title}")
        check(data.get("test_case_id"), f"create case returns test_case_id: {title}")
        return data["test_case_id"]

    valid_case = create_case(
        "D2-3A.2 offline valid - GET /health",
        {"method": "GET", "url": "/health", "timeout": 5},
    )
    invalid_case = create_case(
        "D2-3A.2 offline invalid - missing execution_config",
        {},
    )

    assigned = json_ok(client.post(f"/api/v2/iterations/{iteration_id}/assign-cases", json={
        "case_ids": [valid_case, invalid_case],
    }), "assign cases")
    check(assigned.get("updated") == 2, "assign cases updates both cases")

    smoke = json_ok(client.post(f"/api/v2/iterations/{iteration_id}/execution-sets", json={
        "type": "smoke",
        "name": "D2-3A.2 offline smoke set",
    }), "create smoke execution set")
    check(smoke.get("case_count") == 2, "smoke execution set records selected cases")
    check(set(smoke.get("case_ids", [])) == {valid_case, invalid_case}, "smoke execution set returns case_ids")
    smoke_id = smoke["id"]

    invalid_base = client.post(f"/api/v2/iterations/{iteration_id}/run", json={
        "execution_set_id": smoke_id,
        "base_url": "ftp://invalid.example?api_key=abc123SECRET999",
    })
    assert_standard_error(invalid_base, "invalid base_url", "INVALID_BASE_URL")
    check("abc123SECRET999" not in invalid_base.text, "invalid base_url response redacts probe secret")

    invalid_config = client.post(f"/api/v2/iterations/{iteration_id}/run", json={
        "execution_set_id": smoke_id,
        "environment_id": env_id,
    })
    assert_standard_error(invalid_config, "invalid execution config", "TEST_CASE_EXECUTION_CONFIG_INVALID")

    no_env_project = json_ok(client.post("/api/v2/projects", json={
        "name": f"D2-3A.2离线无环境项目-{marker}",
        "description": "offline no env",
        "owner": "qa",
        "team": "qa",
    }), "create no-env project")
    no_env_iter = json_ok(client.post("/api/v2/iterations", json={
        "project_id": no_env_project["id"],
        "name": f"D2-3A.2离线无环境迭代-{marker}",
        "status": "testing",
    }), "create no-env iteration")
    no_env_case = create_case(
        "D2-3A.2 offline valid without environment",
        {"method": "GET", "url": "/health", "timeout": 5},
    )
    json_ok(client.post(f"/api/v2/iterations/{no_env_iter['id']}/assign-cases", json={
        "case_ids": [no_env_case],
    }), "assign no-env case")
    no_env_set = json_ok(client.post(f"/api/v2/iterations/{no_env_iter['id']}/execution-sets", json={
        "type": "smoke",
    }), "create no-env smoke set")
    no_env_resp = client.post(f"/api/v2/iterations/{no_env_iter['id']}/run", json={
        "execution_set_id": no_env_set["id"],
    })
    assert_standard_error(no_env_resp, "missing environment", "ENVIRONMENT_REQUIRED")

    print("\nD2-3A.2 offline contract check passed.")


if __name__ == "__main__":
    main()
