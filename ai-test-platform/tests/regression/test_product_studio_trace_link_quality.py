#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Product Studio TraceLink and quality score acceptance test.

The script assumes the backend is running and validates the public
/api/v2/product-studio APIs end to end.
"""
from __future__ import annotations

import os
import sys
import uuid

import requests


BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8001").rstrip("/")
SECRET_PROBE = "ps-secret-token-123456"


def check(condition, message):
    if not condition:
        raise AssertionError(message)
    print(f"[PASS] {message}")


def request(method, path, **kwargs):
    headers = kwargs.pop("headers", {})
    headers.setdefault("X-Trace-Id", f"ps-quality-{uuid.uuid4().hex[:10]}")
    resp = requests.request(method, f"{BASE_URL}{path}", headers=headers, timeout=240, **kwargs)
    check(resp.headers.get("X-Trace-Id"), f"X-Trace-Id exists: {method} {path}")
    return resp


def json_ok(resp, label, expected=(200, 201)):
    if resp.status_code not in expected:
        raise AssertionError(f"{label} failed: HTTP {resp.status_code} {resp.text[:800]}")
    return resp.json()


def assert_no_sensitive_leak(resp, label):
    text = resp.text.lower()
    for key in ("authorization", "cookie", "password", "api_key", "secret", SECRET_PROBE.lower()):
        check(key not in text, f"{label} does not leak {key}")


def create_idea(marker):
    resp = request("POST", "/api/v2/product-studio/ideas", json={
        "title": f"Product Studio TraceLink 质量验证 {marker}",
        "product_direction": "验证 AI 需求生成链路中的 PRD、需求点、测试用例和 TraceLink",
        "target_users": "测试工程师、产品经理",
        "pain_points": "生成测试用例后质量分偏低，缺少需求到用例的追踪关系",
        "existing_assets": "已有 Product Studio、RequirementPoint、TestCase、TraceLink 表",
        "current_blockers": "需要证明每条测试用例可追溯到需求点",
        "constraints": "不新增重复模块，不破坏迭代中心",
    })
    data = json_ok(resp, "create product idea")
    check(data.get("idea_id"), "创建 ProductIdea 成功")
    return data["idea_id"]


def generate_prd(idea_id):
    provider = os.getenv("PRODUCT_STUDIO_PROVIDER")
    model = os.getenv("PRODUCT_STUDIO_MODEL")
    payload = {}
    if provider:
        payload["provider"] = provider
    if model:
        payload["model"] = model
    resp = request("POST", f"/api/v2/product-studio/ideas/{idea_id}/generate-prd", json=payload)
    data = json_ok(resp, "generate prd")
    check(data.get("artifact_id"), "生成 PRD 成功")
    return data["artifact_id"]


def get_quality_summary(artifact_id):
    resp = request("GET", f"/api/v2/product-studio/artifacts/{artifact_id}/quality-summary")
    data = json_ok(resp, "get quality summary")
    check("quality_score" in data or "average_quality_score" in data, "质量分返回 score")
    return data


def get_quality_dashboard(idea_id):
    resp = request("GET", f"/api/v2/product-studio/ideas/{idea_id}/quality-dashboard")
    return json_ok(resp, "get quality dashboard")


def generate_requirement_points(artifact_id):
    resp = request("POST", f"/api/v2/product-studio/artifacts/{artifact_id}/generate-requirement-points")
    data = json_ok(resp, "generate requirement points")
    if data.get("error_message"):
        raise AssertionError(f"generate requirement points returned error: {data['error_message']}")
    check(data.get("generated_count", 0) > 0, "生成 RequirementPoint 成功")
    for rp in data.get("requirement_points", []):
        check(rp.get("source_id") == artifact_id, "RequirementPoint 记录来源 artifact_id")
    return data


def generate_test_cases(artifact_id):
    resp = request("POST", f"/api/v2/product-studio/artifacts/{artifact_id}/generate-test-cases")
    data = json_ok(resp, "generate test cases")
    if data.get("error_message"):
        raise AssertionError(f"generate test cases returned error: {data['error_message']}")
    check(data.get("generated_count", 0) > 0, "生成 TestCase 成功")
    for tc in data.get("test_cases", []):
        check(tc.get("requirement_point_id"), "生成的 TestCase 关联 requirement_point_id")
    return data


def get_trace_links(artifact_id):
    resp = request("GET", f"/api/v2/product-studio/artifacts/{artifact_id}/trace-links")
    data = json_ok(resp, "get trace links")
    check("trace_links" in data, "TraceLink 查询接口返回 trace_links")
    return data


def score_links(artifact_id):
    resp = request("POST", f"/api/v2/product-studio/artifacts/{artifact_id}/score-trace-links")
    data = json_ok(resp, "score trace links")
    check(data.get("scored_count", 0) > 0, "TraceLink 批量评分成功")
    return data


def verify_error_response():
    resp = request(
        "POST",
        "/api/v2/product-studio/artifacts/not-found/generate-test-cases",
        headers={"Authorization": f"Bearer {SECRET_PROBE}", "Cookie": f"sid={SECRET_PROBE}"},
    )
    check(resp.status_code >= 400, "错误响应返回 HTTP error")
    data = resp.json()
    for key in ("code", "message", "trace_id", "details"):
        check(key in data, f"错误响应结构包含 {key}")
    assert_no_sensitive_leak(resp, "Product Studio error response")


def main():
    marker = uuid.uuid4().hex[:8]
    print(f"Product Studio TraceLink quality validation against {BASE_URL}")

    idea_id = create_idea(marker)
    artifact_id = generate_prd(idea_id)

    before_summary = get_quality_summary(artifact_id)
    before_score = before_summary.get("quality_score", before_summary.get("average_quality_score", 0))
    check(before_summary.get("warnings") or before_summary.get("total_links") == 0, "缺少 TraceLink 时返回明确 warning")

    dashboard_before = get_quality_dashboard(idea_id)
    check(
        "TRACE_LINK_MISSING" in dashboard_before.get("risk_flags", [])
        or any("追踪关系" in item for item in dashboard_before.get("recommendations", [])),
        "缺少 TraceLink 时 Dashboard 有明确提示",
    )

    rp_result = generate_requirement_points(artifact_id)
    rp_ids = {rp["id"] for rp in rp_result.get("requirement_points", [])}
    trace_after_rp = get_trace_links(artifact_id)
    check(len(trace_after_rp.get("requirement_points", [])) >= len(rp_ids), "RequirementPoint TraceLink 生成成功")

    tc_result = generate_test_cases(artifact_id)
    tc_ids = {tc["id"] for tc in tc_result.get("test_cases", [])}
    trace_after_tc = get_trace_links(artifact_id)
    tc_links = [l for l in trace_after_tc.get("trace_links", []) if l.get("target_type") == "test_case"]
    check(len(tc_links) >= len(tc_ids), "ProductArtifactTraceLink 生成成功")
    for link in tc_links:
        check(link.get("source_type") == "requirement_point", "TestCase TraceLink source_type 指向 requirement_point")
        check(link.get("source_id") in rp_ids, "每个 TestCase 能追溯到 RequirementPoint")
        check(link.get("relation_type") == "requirement_point_to_test_case", "TraceLink relation_type 正确")

    score_links(artifact_id)
    after_summary = get_quality_summary(artifact_id)
    after_score = after_summary.get("quality_score", after_summary.get("average_quality_score", 0))
    check(after_score > before_score, "有 TraceLink 后质量分明显提升")
    check(after_summary.get("trace_link_count", after_summary.get("total_links", 0)) > 0, "质量分基于真实 TraceLink")

    verify_error_response()

    print("PASS Product Studio TraceLink quality validation")
    print(f"idea_id={idea_id} artifact_id={artifact_id} before_score={before_score} after_score={after_score}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
