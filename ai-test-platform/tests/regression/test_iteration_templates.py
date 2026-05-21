#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Acceptance checks for iteration templates MVP.

Assumes backend is running at BASE_URL, default http://127.0.0.1:8001.
"""
from __future__ import annotations

import os
import sys
import time
import uuid
import requests


BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8001")
BASE = f"{BASE_URL}/api/v2"


def _assert(condition, message):
    if not condition:
        raise AssertionError(message)


def request(method, path, **kwargs):
    headers = kwargs.pop("headers", {})
    headers.setdefault("X-Trace-Id", f"iter-template-{uuid.uuid4().hex[:8]}")
    resp = requests.request(method, f"{BASE_URL}{path}", headers=headers, timeout=180, **kwargs)
    return resp


def get_or_create_project():
    resp = request("GET", "/api/v2/projects")
    _assert(resp.status_code == 200, f"list projects failed: {resp.status_code} {resp.text[:200]}")
    projects = resp.json().get("projects", [])
    if projects:
        return projects[0]["id"]

    resp = request("POST", "/api/v2/projects", json={
        "name": "iteration-template-acceptance",
        "description": "created by scripts/test_iteration_templates.py",
        "owner": "qa",
        "team": "qa",
    })
    _assert(resp.status_code in (200, 201), f"create project failed: {resp.status_code} {resp.text[:200]}")
    return resp.json()["id"]


def main():
    checks = []

    # 1-2 templates contract
    print("CHECK templates list")
    resp = request("GET", "/api/v2/iteration-templates")
    _assert(resp.status_code == 200, f"templates failed: {resp.status_code} {resp.text[:200]}")
    _assert(resp.headers.get("X-Trace-Id"), "templates response missing X-Trace-Id")
    data = resp.json()
    templates = data.get("templates", [])
    _assert(len(templates) == 5, f"expected 5 templates, got {len(templates)}")
    keys = {t.get("template_key") for t in templates}
    _assert({"general_feature", "payment_amount", "erp_sync", "video_attachment", "api_contract"} <= keys, f"template keys mismatch: {keys}")
    for t in templates:
        _assert(t.get("template_key"), "template missing template_key")
        _assert(t.get("template_name"), "template missing template_name")
        _assert(isinstance(t.get("default_test_points"), list) and t["default_test_points"], f"{t.get('template_key')} missing default_test_points")
    checks.append("templates list contract")

    project_id = get_or_create_project()

    # 3 create with payment_amount
    print("CHECK create iteration with payment_amount")
    marker = uuid.uuid4().hex[:8]
    resp = request("POST", "/api/v2/iterations", json={
        "project_id": project_id,
        "name": f"payment template acceptance {marker}",
        "version": f"v.accept.{marker}",
        "description": "acceptance iteration created by template script",
        "template_key": "payment_amount",
    })
    _assert(resp.status_code == 200, f"create iteration failed: {resp.status_code} {resp.text[:500]}")
    _assert(resp.headers.get("X-Trace-Id"), "create iteration response missing X-Trace-Id")
    created = resp.json()
    iteration_id = created["id"]
    _assert(created.get("template_key") == "payment_amount", "created iteration missing template metadata")
    checks.append("create iteration with payment_amount")

    # 4-6 template points generated, unconfirmed, not AI
    print("CHECK template test points")
    resp = request("GET", f"/api/v2/iterations/{iteration_id}/test-points")
    _assert(resp.status_code == 200, f"list test points failed: {resp.status_code} {resp.text[:200]}")
    points = resp.json().get("test_points", [])
    _assert(len(points) >= 12, f"expected at least 12 payment points, got {len(points)}")
    _assert(all(p.get("confirmed") is False for p in points), "template test point should be confirmed=false")
    _assert(all(p.get("ai_generated") is False for p in points), "template test point should be ai_generated=false")
    _assert(all(str(p.get("test_type", "")).startswith("template_payment_amount_") for p in points), "template source marker missing in test_type")
    checks.append("template test points generated")

    # 7 no test cases auto-generated
    print("CHECK no auto test cases")
    resp = request("GET", f"/api/v2/iterations/{iteration_id}/test-cases")
    _assert(resp.status_code == 200, f"list test cases failed: {resp.status_code} {resp.text[:200]}")
    cases_payload = resp.json()
    cases = cases_payload.get("test_cases", cases_payload.get("cases", []))
    _assert(len(cases) == 0, f"test cases should not be auto-generated, got {len(cases)}")
    checks.append("no auto test cases")

    # 8 no defects auto-created: use timestamp keyword to ensure no title hit
    print("CHECK no auto defects")
    resp = request("GET", f"/api/v2/defects?keyword={marker}")
    _assert(resp.status_code == 200, f"list defects failed: {resp.status_code} {resp.text[:200]}")
    _assert(resp.json().get("total", 0) == 0, "defects should not be auto-created")
    checks.append("no auto defects")

    # 9 AI flow can continue: no requirements should produce standard 400, then add requirement and analyze.
    print("CHECK AI analyze flow")
    resp = request("POST", f"/api/v2/iterations/{iteration_id}/ai/analyze-requirements")
    _assert(resp.status_code == 400, f"empty requirements should return 400, got {resp.status_code}")
    _assert(resp.json().get("trace_id"), "error response missing trace_id")
    resp = request("POST", f"/api/v2/iterations/{iteration_id}/requirements", json={
        "title": "付款金额规则",
        "content": "新增付款单金额、个税、服务费、实付金额联动规则。",
        "source_type": "manual",
        "risk_level": "P0",
    })
    _assert(resp.status_code == 200, f"create requirement failed: {resp.status_code} {resp.text[:200]}")
    resp = request("POST", f"/api/v2/iterations/{iteration_id}/ai/analyze-requirements")
    _assert(resp.status_code == 200, f"AI analyze failed: {resp.status_code} {resp.text[:500]}")
    checks.append("AI analyze flow continues")

    # 10 all checked successful responses include trace header already sampled above
    # 11 standard error structure
    print("CHECK standard error")
    resp = request("POST", "/api/v2/iterations", json={
        "project_id": project_id,
        "name": f"bad template {marker}",
        "template_key": "not_exists",
    })
    _assert(resp.status_code == 400, f"bad template should return 400, got {resp.status_code}")
    err = resp.json()
    _assert(err.get("code") == "BAD_REQUEST", f"error code not standardized: {err}")
    _assert(err.get("trace_id"), "standard error missing trace_id")
    checks.append("standard error response")

    print("PASS iteration template acceptance")
    for item in checks:
        print(f" - {item}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
