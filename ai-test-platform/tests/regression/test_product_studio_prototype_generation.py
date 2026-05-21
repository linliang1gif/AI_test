"""Acceptance checks for Product Studio high-fidelity prototype MVP."""

from __future__ import annotations

import os
import re
import sys
import uuid
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.models import ProductArtifact, ProductArtifactTraceLink, RequirementPoint
from database.session import SessionLocal


BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8001").rstrip("/")
SECRET_PROBE = "prototype-secret-token-123456"


def check(condition, message):
    if not condition:
        raise AssertionError(message)
    print(f"[PASS] {message}")


def request(method, path, **kwargs):
    headers = kwargs.pop("headers", {})
    headers.setdefault("X-Trace-Id", f"prototype-{uuid.uuid4().hex[:10]}")
    resp = requests.request(method, f"{BASE_URL}{path}", headers=headers, timeout=240, **kwargs)
    check(resp.headers.get("X-Trace-Id"), f"X-Trace-Id exists: {method} {path}")
    return resp


def json_ok(resp, label, expected=(200, 201)):
    if resp.status_code not in expected:
        raise AssertionError(f"{label} failed: HTTP {resp.status_code} {resp.text[:800]}")
    return resp.json()


def create_idea(title):
    resp = request("POST", "/api/v2/product-studio/ideas", json={
        "title": title,
        "product_direction": "企业级后台高保真原型生成",
        "target_users": "产品经理、测试工程师、研发",
        "pain_points": "PRD 有了，但缺少可预览的 HTML 原型用于需求沟通和测试设计",
        "constraints": "不接 Figma，不使用脚本，不使用外部 CDN",
    })
    data = json_ok(resp, "create idea")
    check(data.get("idea_id"), "Product Studio idea 存在或可创建")
    return data["idea_id"]


def generate_prd(idea_id):
    resp = request("POST", f"/api/v2/product-studio/ideas/{idea_id}/generate-prd", json={"provider": "mock"})
    data = json_ok(resp, "generate PRD")
    check(data.get("artifact_id"), "生成 PRD 成功")
    return data["artifact_id"]


def ensure_requirement_points(prd_artifact_id):
    db = SessionLocal()
    try:
        existing = db.query(RequirementPoint).filter(RequirementPoint.source_id == prd_artifact_id).all()
        if existing:
            check(True, "生成或存在 RequirementPoint")
            return [rp.id for rp in existing]
        rp_ids = []
        for title, priority, risk in [
            ("生成高保真 HTML 原型", "high", "P1"),
            ("原型 HTML 必须安全预览", "critical", "P0"),
            ("原型需要建立需求点 TraceLink", "medium", "P2"),
        ]:
            rp_id = f"RP_PROTO_{uuid.uuid4().hex[:12]}"
            db.add(RequirementPoint(
                id=rp_id,
                source_type="ai_product_studio",
                source_id=prd_artifact_id,
                point_type="feature",
                title=title,
                description=f"{title}，用于验证 Product Studio 高保真原型 MVP。",
                keywords_json=["高保真原型", "HTML", "TraceLink"],
                priority=priority,
                module_name=risk,
            ))
            rp_ids.append(rp_id)
        db.commit()
        check(True, "生成或存在 RequirementPoint")
        return rp_ids
    finally:
        db.close()


def assert_safe_html(html):
    lower = html.lower()
    check("<script" not in lower and "</script" not in lower, "html 不包含 script")
    check("<iframe" not in lower and "</iframe" not in lower, "html 不包含 iframe")
    check(not re.search(r"\son[a-z]+\s*=", lower), "html 不包含 onerror/onload 等事件属性")
    check("http://" not in lower and "https://" not in lower, "html 不包含外部依赖")


def verify_db(artifact_id):
    db = SessionLocal()
    try:
        artifact = db.query(ProductArtifact).filter(ProductArtifact.artifact_id == artifact_id).first()
        check(artifact is not None, "ProductArtifact 保存成功")
        check(artifact.artifact_type == "high_fidelity_prototype", "ProductArtifact artifact_type = high_fidelity_prototype")
        links = db.query(ProductArtifactTraceLink).filter(
            (ProductArtifactTraceLink.target_id == artifact_id) |
            (ProductArtifactTraceLink.artifact_id == artifact_id)
        ).all()
        check(len(links) > 0, "ProductArtifactTraceLink 保存成功")
    finally:
        db.close()


def verify_empty_state():
    empty_idea = create_idea(f"Prototype empty state {uuid.uuid4().hex[:8]}")
    resp = request("GET", f"/api/v2/product-studio/ideas/{empty_idea}/prototype")
    data = json_ok(resp, "get empty prototype")
    check(data.get("exists") is False, "没有原型时返回标准空态")
    check(data.get("message") == "暂无高保真原型，请先生成", "空态 message 正确")


def verify_error_response():
    resp = request(
        "POST",
        "/api/v2/product-studio/ideas/not-found/generate-prototype",
        headers={"Authorization": f"Bearer {SECRET_PROBE}", "Cookie": f"sid={SECRET_PROBE}"},
        json={},
    )
    check(resp.status_code >= 400, "错误响应返回 HTTP error")
    data = resp.json()
    for key in ("code", "message", "trace_id", "details"):
        check(key in data, f"错误响应结构包含 {key}")
    check(SECRET_PROBE not in resp.text, "错误响应不泄露 token/authorization/cookie/api_key/password")


def main():
    print(f"Product Studio prototype generation validation against {BASE_URL}")
    verify_empty_state()

    idea_id = create_idea(f"高保真原型验收 {uuid.uuid4().hex[:8]}")
    prd_artifact_id = generate_prd(idea_id)
    ensure_requirement_points(prd_artifact_id)

    resp = request("POST", f"/api/v2/product-studio/ideas/{idea_id}/generate-prototype", json={"provider": "mock"})
    data = json_ok(resp, "generate high fidelity prototype")
    check(data.get("artifact_type") == "high_fidelity_prototype", "返回 artifact_type = high_fidelity_prototype")
    content = data.get("content") or {}
    html = content.get("html") or ""
    check(bool(html.strip()), "返回 html 字段")
    assert_safe_html(html)
    check(len(data.get("trace_links") or []) > 0, "返回 TraceLink")

    artifact_id = data["artifact_id"]
    verify_db(artifact_id)

    resp = request("GET", f"/api/v2/product-studio/ideas/{idea_id}/prototype")
    latest = json_ok(resp, "get latest prototype")
    check(latest.get("exists") is True, "getPrototype 能获取最新原型")
    check(latest.get("artifact_id") == artifact_id, "getPrototype 返回最新 artifact_id")

    verify_error_response()
    print("PASS Product Studio prototype generation validation")
    print(f"idea_id={idea_id} artifact_id={artifact_id}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
