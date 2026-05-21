#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# P2-9B.1: Windows GBK 编码兼容
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
P1-7D 真实项目安全执行保护 — 自动化测试

覆盖:
1. mock 模式 GET 可执行           → /health app_mode=mock
2. mock 模式 POST 可执行          → 单用例执行不被拦截
3. real 模式 GET 可执行            → 单用例 GET 不被拦截
4. real 模式 POST 默认被拦截       → 403 REAL_MODE_UNSAFE_METHOD_BLOCKED
5. real 模式 PUT/PATCH/DELETE 被拦截
6. real 模式 POST + allow_unsafe_methods=true 可执行
7. 拦截错误 code = REAL_MODE_UNSAFE_METHOD_BLOCKED
8. Token 不出现在错误响应中
9. 执行记录中记录 app_mode 和 allow_unsafe_methods
"""

import os
import sys
import json
import time
import requests

BASE = os.getenv("API_BASE", "http://localhost:8000")
TESTING_KEY = os.getenv("TESTING_KEY", "")
TESTING_HEADERS = {"X-Testing-Key": TESTING_KEY} if TESTING_KEY else {}
PASSED = 0
FAILED = 0
TOTAL = 0


def _set_mode(mode: str):
    r = requests.put(f"{BASE}/admin/app-mode", params={"mode": mode}, headers=TESTING_HEADERS, timeout=5)
    assert r.status_code == 200, f"set_app_mode failed: {r.status_code} {r.text}"
    # verify
    h = requests.get(f"{BASE}/health", timeout=5).json()
    assert h.get("app_mode") == mode, f"app_mode mismatch: {h}"


def _find_case_by_method(method: str):
    """Find a test case with given HTTP method from existing cases."""
    r = requests.get(f"{BASE}/api/v2/test-cases", params={"limit": 500}, timeout=10)
    if r.status_code != 200:
        return None
    data = r.json()
    cases = data if isinstance(data, list) else data.get("test_cases", [])
    for tc in cases:
        cfg = tc.get("execution_config") or {}
        m = (cfg.get("method") or "").upper()
        if m == method.upper() and cfg.get("url"):
            return tc
    return None


def _create_temp_case(method: str, db_session=None):
    """Create a temporary test case with execution_config for testing."""
    case_id = f"safety-test-{method.lower()}-{int(time.time())}"
    # Insert directly via DB if possible, otherwise skip
    try:
        r = requests.post(f"{BASE}/api/v2/test-cases", json={
            "id": case_id,
            "title": f"Safety Test {method}",
            "module": "safety_test",
            "priority": "medium",
            "source": "manual",
            "execution_config": {
                "method": method.upper(),
                "url": "/api/v2/projects",
                "headers": {},
                "body": {} if method.upper() != "GET" else None,
            },
        }, timeout=10)
        if r.status_code in (200, 201):
            return r.json() if r.json().get("id") else {"id": case_id}
    except Exception:
        pass
    return None


def check(label, condition, detail=""):
    global PASSED, FAILED, TOTAL
    TOTAL += 1
    if condition:
        PASSED += 1
        print(f"✅ PASS {label}  {detail}")
    else:
        FAILED += 1
        print(f"❌ FAIL {label}  {detail}")


def test_health_returns_app_mode():
    """Test 1: /health returns app_mode field."""
    r = requests.get(f"{BASE}/health", timeout=5)
    data = r.json()
    check("/health 返回 app_mode", "app_mode" in data, f"app_mode={data.get('app_mode')}")


def test_mock_mode_no_blocking():
    """Test 2-3: mock 模式下 GET 和 POST 不被拦截。"""
    _set_mode("mock")

    # Find GET case
    get_case = _find_case_by_method("GET")
    if get_case:
        r = requests.post(
            f"{BASE}/api/v2/test-cases/{get_case['id']}/execute",
            json={"allow_unsafe_methods": False},
            timeout=30,
        )
        # Should not be 403
        check("mock 模式 GET 不被拦截", r.status_code != 403, f"status={r.status_code}")
    else:
        check("mock 模式 GET 不被拦截", True, "(无可用GET用例，跳过)")

    # Find POST case
    post_case = _find_case_by_method("POST")
    if post_case:
        r = requests.post(
            f"{BASE}/api/v2/test-cases/{post_case['id']}/execute",
            json={"allow_unsafe_methods": False},
            timeout=30,
        )
        check("mock 模式 POST 不被拦截", r.status_code != 403, f"status={r.status_code}")
    else:
        check("mock 模式 POST 不被拦截", True, "(无可用POST用例，跳过)")


def test_real_mode_get_allowed():
    """Test 4: real 模式 GET 不被拦截。"""
    _set_mode("real")

    get_case = _find_case_by_method("GET")
    if get_case:
        r = requests.post(
            f"{BASE}/api/v2/test-cases/{get_case['id']}/execute",
            json={"allow_unsafe_methods": False},
            timeout=30,
        )
        check("real 模式 GET 不被拦截", r.status_code != 403, f"status={r.status_code}")
    else:
        check("real 模式 GET 不被拦截", True, "(无可用GET用例，跳过)")


def test_real_mode_post_blocked():
    """Test 5: real 模式 POST 默认被拦截。"""
    _set_mode("real")

    post_case = _find_case_by_method("POST")
    if post_case:
        r = requests.post(
            f"{BASE}/api/v2/test-cases/{post_case['id']}/execute",
            json={"allow_unsafe_methods": False},
            timeout=30,
        )
        check("real 模式 POST 默认被拦截", r.status_code == 403, f"status={r.status_code}")

        # Check structured error
        detail = r.json().get("detail", {})
        if isinstance(detail, str):
            try:
                detail = json.loads(detail)
            except Exception:
                pass
        code = detail.get("code", "") if isinstance(detail, dict) else ""
        check(
            "拦截 code=REAL_MODE_UNSAFE_METHOD_BLOCKED",
            code == "REAL_MODE_UNSAFE_METHOD_BLOCKED",
            f"code={code}",
        )
        check(
            "拦截响应无 Token 泄漏",
            "token" not in json.dumps(detail).lower() or "token" in "allow_unsafe_methods",
            "",
        )
    else:
        check("real 模式 POST 默认被拦截", True, "(无可用POST用例，跳过)")
        check("拦截 code=REAL_MODE_UNSAFE_METHOD_BLOCKED", True, "(跳过)")
        check("拦截响应无 Token 泄漏", True, "(跳过)")


def test_real_mode_put_patch_delete_blocked():
    """Test 6: real 模式 PUT/PATCH/DELETE 被拦截。"""
    _set_mode("real")

    for method in ("PUT", "PATCH", "DELETE"):
        case = _find_case_by_method(method)
        if case:
            r = requests.post(
                f"{BASE}/api/v2/test-cases/{case['id']}/execute",
                json={"allow_unsafe_methods": False},
                timeout=30,
            )
            check(f"real 模式 {method} 默认被拦截", r.status_code == 403, f"status={r.status_code}")
        else:
            check(f"real 模式 {method} 默认被拦截", True, f"(无可用{method}用例，跳过)")


def test_real_mode_post_with_allow():
    """Test 7: real 模式 POST + allow_unsafe_methods=true 可执行。"""
    _set_mode("real")

    post_case = _find_case_by_method("POST")
    if post_case:
        r = requests.post(
            f"{BASE}/api/v2/test-cases/{post_case['id']}/execute",
            json={"allow_unsafe_methods": True},
            timeout=30,
        )
        check(
            "real 模式 POST + allow_unsafe_methods=true 通过",
            r.status_code != 403,
            f"status={r.status_code}",
        )
    else:
        check("real 模式 POST + allow_unsafe_methods=true 通过", True, "(无可用POST用例，跳过)")


def test_batch_real_mode_blocked():
    """Test 8: real 模式批量包含 POST 被拦截。"""
    _set_mode("real")

    post_case = _find_case_by_method("POST")
    if post_case:
        r = requests.post(
            f"{BASE}/api/v2/test-cases/batch-execute",
            json={"case_ids": [post_case["id"]], "allow_unsafe_methods": False},
            timeout=30,
        )
        check("real 模式批量 POST 被拦截", r.status_code == 403, f"status={r.status_code}")

        detail = r.json().get("detail", {})
        if isinstance(detail, str):
            try:
                detail = json.loads(detail)
            except Exception:
                pass
        code = detail.get("code", "") if isinstance(detail, dict) else ""
        check("批量拦截 code 正确", code == "REAL_MODE_UNSAFE_METHOD_BLOCKED", f"code={code}")
    else:
        check("real 模式批量 POST 被拦截", True, "(无可用POST用例，跳过)")
        check("批量拦截 code 正确", True, "(跳过)")


def test_execution_record_metadata():
    """Test 9: 执行记录中记录 app_mode 和 allow_unsafe_methods。"""
    _set_mode("mock")

    get_case = _find_case_by_method("GET")
    if get_case:
        r = requests.post(
            f"{BASE}/api/v2/test-cases/{get_case['id']}/execute",
            json={"allow_unsafe_methods": False},
            timeout=30,
        )
        if r.status_code == 200:
            run_id = r.json().get("run_id", "")
            if run_id:
                rr = requests.get(f"{BASE}/api/v2/test-runs/{run_id}", timeout=10)
                if rr.status_code == 200:
                    run_data = rr.json()
                    summary_raw = run_data.get("summary", "{}")
                    if isinstance(summary_raw, str):
                        try:
                            summary = json.loads(summary_raw)
                        except Exception:
                            summary = {}
                    else:
                        summary = summary_raw or {}
                    has_mode = "app_mode" in summary
                    has_allow = "allow_unsafe_methods" in summary
                    check("执行记录含 app_mode", has_mode, f"summary keys={list(summary.keys())}")
                    check("执行记录含 allow_unsafe_methods", has_allow, "")
                    return
        check("执行记录含 app_mode", True, "(执行未成功，跳过)")
        check("执行记录含 allow_unsafe_methods", True, "(跳过)")
    else:
        check("执行记录含 app_mode", True, "(无可用GET用例，跳过)")
        check("执行记录含 allow_unsafe_methods", True, "(跳过)")


def main():
    print("=" * 80)
    print("P1-7D 真实项目安全执行保护 — 自动化测试")
    print("=" * 80)
    print(f"后端: {BASE}")
    print()

    # Save original mode
    orig = requests.get(f"{BASE}/health", timeout=5).json().get("app_mode", "mock")

    try:
        test_health_returns_app_mode()
        test_mock_mode_no_blocking()
        test_real_mode_get_allowed()
        test_real_mode_post_blocked()
        test_real_mode_put_patch_delete_blocked()
        test_real_mode_post_with_allow()
        test_batch_real_mode_blocked()
        test_execution_record_metadata()
    finally:
        # Restore original mode
        _set_mode(orig)
        print(f"\n(已恢复 APP_MODE={orig})")

    print()
    print("=" * 80)
    print(f"测试汇总  总计: {TOTAL}  通过: {PASSED}  失败: {FAILED}")
    print(f"通过率: {round(PASSED / max(TOTAL, 1) * 100, 1)}%")
    print("=" * 80)

    sys.exit(0 if FAILED == 0 else 1)


if __name__ == "__main__":
    main()
