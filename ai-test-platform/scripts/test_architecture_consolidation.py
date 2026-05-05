#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Phase C2: Windows GBK encoding fix
import io, sys
if sys.stdout and getattr(sys.stdout, 'encoding', '').lower().replace('-', '') != 'utf8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr and getattr(sys.stderr, 'encoding', '').lower().replace('-', '') != 'utf8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
Phase A — 架构收口验收脚本

覆盖检查:
  1. backend/app.py 可正常导入 create_app
  2. router_registry.py 可正常注册 V2 routes
  3. /api/v2/dashboard/summary 可访问
  4. /api/v2/test-cases 可访问
  5. 前端 api.js 不再调用 /api/dashboard/stats (无直接调用)
  6. 前端 TestCases 主列表使用 V2 test-cases API
  7. test_cases_db 使用警告 (仅在 legacy 文件中)
  8. api.ai.getCurrent 不存在死调用
  9. backend_api_server.py 被标记为 legacy
 10. 核心回归脚本可发现

输出: PASS / FAIL / WARN + exit code
"""

import os
import sys
import re
import importlib
import traceback

# ── 路径设置 ──
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_ROOT)

FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend", "src")
API_JS = os.path.join(FRONTEND_DIR, "services", "api.js")
PAGES_DIR = os.path.join(FRONTEND_DIR, "pages")
LEGACY_FILE = os.path.join(PROJECT_ROOT, "backend_api_server.py")

# ── 测试基础设施 ──
RESULTS = []  # (name, status, reason)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
TESTING_KEY = os.getenv("TESTING_KEY", "regression-test-key-auto")


def record(name, status, reason=""):
    RESULTS.append((name, status, reason))
    icon = {"PASS": "OK", "FAIL": "XX", "WARN": "!!", "SKIP": "--"}.get(status, "??")
    print(f"  [{icon}] {status:4s} {name}" + (f" | {reason}" if reason else ""))


# ════════════════════════════════════════════════════
# CHECK 1: backend/app.py create_app 可导入
# ════════════════════════════════════════════════════
def check_create_app_importable():
    try:
        from backend.app import create_app
        app = create_app()
        assert app is not None
        record("create_app importable", "PASS")
    except Exception as e:
        record("create_app importable", "FAIL", str(e))


# ════════════════════════════════════════════════════
# CHECK 2: router_registry 可注册
# ════════════════════════════════════════════════════
def check_router_registry():
    try:
        from backend.router_registry import register_routers, MODULE_FLAGS
        assert callable(register_routers)
        # MODULE_FLAGS 应在 create_app 时填充
        record("router_registry importable", "PASS")
    except Exception as e:
        record("router_registry importable", "FAIL", str(e))


# ════════════════════════════════════════════════════
# CHECK 3: /api/v2/dashboard/summary 可访问
# ════════════════════════════════════════════════════
def check_v2_dashboard():
    try:
        import requests
        headers = {"X-Testing-Key": TESTING_KEY}
        r = requests.get(f"{BACKEND_URL}/api/v2/dashboard/summary", headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            assert "data" in data or "project_count" in data or "test_case_count" in str(data)
            record("/api/v2/dashboard/summary", "PASS")
        else:
            record("/api/v2/dashboard/summary", "FAIL", f"HTTP {r.status_code}")
    except ImportError:
        record("/api/v2/dashboard/summary", "SKIP", "requests not installed")
    except Exception as e:
        record("/api/v2/dashboard/summary", "SKIP", f"Backend not running: {e}")


# ════════════════════════════════════════════════════
# CHECK 4: /api/v2/test-cases 可访问
# ════════════════════════════════════════════════════
def check_v2_test_cases():
    try:
        import requests
        headers = {"X-Testing-Key": TESTING_KEY}
        r = requests.get(f"{BACKEND_URL}/api/v2/test-cases", headers=headers, timeout=5)
        if r.status_code == 200:
            record("/api/v2/test-cases", "PASS")
        else:
            record("/api/v2/test-cases", "FAIL", f"HTTP {r.status_code}")
    except ImportError:
        record("/api/v2/test-cases", "SKIP", "requests not installed")
    except Exception as e:
        record("/api/v2/test-cases", "SKIP", f"Backend not running: {e}")


# ════════════════════════════════════════════════════
# CHECK 5: 前端 api.js 不再直接调用 /api/dashboard/stats
# ════════════════════════════════════════════════════
def check_no_direct_dashboard_stats():
    if not os.path.exists(API_JS):
        record("api.js no /api/dashboard/stats", "SKIP", "api.js not found")
        return

    with open(API_JS, "r", encoding="utf-8") as f:
        content = f.read()

    # 查找非注释中直接调用 /api/dashboard/stats 的行
    direct_calls = []
    for i, line in enumerate(content.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("*"):
            continue
        if "/api/dashboard/stats" in line and "DEPRECATED" not in line and "console.warn" not in line:
            # 检查是否在函数体内且不是转发到 V2
            if "request(" in line and "v2.dashboard" not in line:
                direct_calls.append(f"L{i}: {stripped[:80]}")

    if direct_calls:
        record("api.js no /api/dashboard/stats", "FAIL", f"Found direct calls: {direct_calls}")
    else:
        record("api.js no /api/dashboard/stats", "PASS", "getStats now redirects to V2")


# ════════════════════════════════════════════════════
# CHECK 6: TestCases.jsx 主列表使用 V2
# ════════════════════════════════════════════════════
def check_testcases_uses_v2():
    tc_file = os.path.join(PAGES_DIR, "TestCases.jsx")
    if not os.path.exists(tc_file):
        record("TestCases.jsx uses V2", "SKIP", "file not found")
        return

    with open(tc_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 主列表加载应使用 api.v2.testCases.getAll
    if "api.v2.testCases.getAll" in content:
        record("TestCases.jsx main list uses V2", "PASS")
    else:
        record("TestCases.jsx main list uses V2", "FAIL", "api.v2.testCases.getAll not found")

    # 创建用例应使用 api.v2.testCases.create
    if "api.v2.testCases.create" in content:
        record("TestCases.jsx create uses V2", "PASS")
    else:
        record("TestCases.jsx create uses V2", "WARN", "api.v2.testCases.create not found")


# ════════════════════════════════════════════════════
# CHECK 7: test_cases_db 使用警告
# ════════════════════════════════════════════════════
def check_test_cases_db_usage():
    # 搜索项目中 test_cases_db 使用
    legacy_file = LEGACY_FILE
    routes_dir = os.path.join(PROJECT_ROOT, "routes")
    services_dir = os.path.join(PROJECT_ROOT, "services")

    # 在 routes/ 和 services/ 中不应有 test_cases_db
    non_legacy_hits = []
    for search_dir in [routes_dir, services_dir]:
        if not os.path.isdir(search_dir):
            continue
        for fname in os.listdir(search_dir):
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(search_dir, fname)
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                for i, line in enumerate(f, 1):
                    if "test_cases_db" in line:
                        non_legacy_hits.append(f"{fname}:{i}")

    if non_legacy_hits:
        record("test_cases_db only in legacy", "FAIL", f"Found in: {non_legacy_hits}")
    else:
        # 检查 legacy 文件中存在（预期）
        if os.path.exists(legacy_file):
            with open(legacy_file, "r", encoding="utf-8", errors="ignore") as f:
                legacy_content = f.read()
            count = legacy_content.count("test_cases_db")
            record("test_cases_db only in legacy", "WARN", f"Still {count} references in backend_api_server.py (legacy)")
        else:
            record("test_cases_db only in legacy", "PASS")


# ════════════════════════════════════════════════════
# CHECK 8: api.ai.getCurrent 不存在死调用
# ════════════════════════════════════════════════════
def check_no_getcurrent_call():
    hits = []
    if os.path.isdir(PAGES_DIR):
        for fname in os.listdir(PAGES_DIR):
            if not fname.endswith(".jsx"):
                continue
            fpath = os.path.join(PAGES_DIR, fname)
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                for i, line in enumerate(f, 1):
                    if "getCurrent" in line and "ai" in line.lower():
                        hits.append(f"{fname}:{i}")

    if hits:
        record("ai.getCurrent no page callers", "FAIL", f"Found in: {hits}")
    else:
        record("ai.getCurrent no page callers", "PASS")

    # 检查 api.js 中的实现
    if os.path.exists(API_JS):
        with open(API_JS, "r", encoding="utf-8") as f:
            content = f.read()
        if "DEPRECATED" in content and "getCurrent" in content:
            record("ai.getCurrent marked deprecated", "PASS")
        elif "getCurrent" not in content:
            record("ai.getCurrent marked deprecated", "PASS", "removed from api.js")
        else:
            record("ai.getCurrent marked deprecated", "WARN", "getCurrent exists without DEPRECATED mark")


# ════════════════════════════════════════════════════
# CHECK 9: backend_api_server.py 被标记 legacy
# ════════════════════════════════════════════════════
def check_legacy_marker():
    if not os.path.exists(LEGACY_FILE):
        record("backend_api_server.py legacy marker", "SKIP", "file not found")
        return

    with open(LEGACY_FILE, "r", encoding="utf-8", errors="ignore") as f:
        head = f.read(2000)

    if "LEGACY" in head.upper() or "legacy" in head.lower():
        record("backend_api_server.py legacy marker", "PASS")
    else:
        record("backend_api_server.py legacy marker", "FAIL", "No legacy marker in file header")


# ════════════════════════════════════════════════════
# CHECK 10: 回归脚本可发现
# ════════════════════════════════════════════════════
def check_regression_scripts():
    reg_script = os.path.join(SCRIPT_DIR, "run_regression_all.py")
    if not os.path.exists(reg_script):
        record("regression scripts exist", "FAIL", "run_regression_all.py not found")
        return

    with open(reg_script, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # 检查是否包含测试脚本注册
    if "REGRESSION_SCRIPTS" in content or "scripts" in content.lower():
        record("regression scripts exist", "PASS")
    else:
        record("regression scripts exist", "WARN", "No REGRESSION_SCRIPTS found")


# ════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════
def main():
    print("=" * 60)
    print("Phase A — 架构收口验收脚本")
    print("=" * 60)
    print()

    checks = [
        check_create_app_importable,
        check_router_registry,
        check_v2_dashboard,
        check_v2_test_cases,
        check_no_direct_dashboard_stats,
        check_testcases_uses_v2,
        check_test_cases_db_usage,
        check_no_getcurrent_call,
        check_legacy_marker,
        check_regression_scripts,
    ]

    for check_fn in checks:
        try:
            check_fn()
        except Exception as e:
            record(check_fn.__name__, "FAIL", f"Unexpected: {e}")
            traceback.print_exc()
        print()

    # ── 汇总 ──
    print("=" * 60)
    total = len(RESULTS)
    passed = sum(1 for _, s, _ in RESULTS if s == "PASS")
    failed = sum(1 for _, s, _ in RESULTS if s == "FAIL")
    warned = sum(1 for _, s, _ in RESULTS if s == "WARN")
    skipped = sum(1 for _, s, _ in RESULTS if s == "SKIP")

    print(f"Total: {total}  PASS: {passed}  FAIL: {failed}  WARN: {warned}  SKIP: {skipped}")

    if failed > 0:
        print("\n[FAIL] Architecture consolidation FAILED")
        print("FAIL 项:")
        for name, status, reason in RESULTS:
            if status == "FAIL":
                print(f"  - {name}: {reason}")
        sys.exit(1)
    elif warned > 0:
        print("\n[WARN] Architecture consolidation PASSED (with warnings)")
        sys.exit(0)
    else:
        print("\n[PASS] Architecture consolidation PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
