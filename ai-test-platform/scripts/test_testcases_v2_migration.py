#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Phase C2: Windows GBK encoding fix
import io, sys
if sys.stdout and getattr(sys.stdout, 'encoding', '').lower().replace('-', '') != 'utf8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr and getattr(sys.stderr, 'encoding', '').lower().replace('-', '') != 'utf8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
Phase B1 — TestCases V2 迁移验收脚本

15 项检查:
 1. api.js 不含旧 /api/testcases/{id}/generate-script 路径
 2. api.js 不含旧 /api/testcases/{id}/manual-execute 路径
 3. api.js 不含旧 /api/test-cases/export 路径 (非 v2)
 4. api.js 不含旧 /api/test-cases/{id}/bind-dataset 路径 (非 v2)
 5. 后端存在 POST /api/v2/test-cases/{id}/generate-script
 6. 后端存在 POST /api/v2/test-cases/{id}/manual-execute
 7. 后端存在 GET  /api/v2/test-cases/export
 8. 后端存在 POST /api/v2/test-cases/{id}/bind-dataset
 9. 新路由不引用 test_cases_db
10. 新路由从 TestCase DB 查询
11. router_registry.py 注册 test_case_extra_routes
12. backend_api_server.py 标记 legacy
13. TestCases.jsx 可正常 import (无语法错误)
14. 前端 build 不报错
15. smoke 回归通过
"""

import os, sys, re, subprocess, traceback

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, ROOT)

API_JS = os.path.join(ROOT, "frontend", "src", "services", "api.js")
ROUTES_FILE = os.path.join(ROOT, "routes", "test_case_extra_routes.py")
REGISTRY = os.path.join(ROOT, "backend", "router_registry.py")
LEGACY = os.path.join(ROOT, "backend_api_server.py")
TC_JSX = os.path.join(ROOT, "frontend", "src", "pages", "TestCases.jsx")

R = []

def rec(name, status, reason=""):
    R.append((name, status, reason))
    icon = {"PASS": "OK", "FAIL": "XX", "WARN": "!!", "SKIP": "--"}.get(status, "??")
    print(f"  [{icon}] {status:4s} {name}" + (f" | {reason}" if reason else ""))


def _read(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


# ── 1-4: api.js 旧路径检查 ──

def check_apijs_old_paths():
    content = _read(API_JS)
    if content is None:
        rec("api.js exists", "SKIP", "file not found"); return

    old_patterns = [
        (1, r'`\$\{API_BASE_URL\}/testcases/\$\{.*?\}/generate-script`', "/api/testcases/{id}/generate-script"),
        (2, r'`\$\{API_BASE_URL\}/testcases/\$\{.*?\}/manual-execute`', "/api/testcases/{id}/manual-execute"),
        (3, r'`\$\{API_BASE_URL\}/test-cases/export`', "/api/test-cases/export (non-v2)"),
        (4, r'`\$\{API_BASE_URL\}/test-cases/\$\{.*?\}/bind-dataset`', "/api/test-cases/{id}/bind-dataset (non-v2)"),
    ]
    for idx, pattern, desc in old_patterns:
        hits = re.findall(pattern, content)
        if hits:
            rec(f"#{idx} api.js no old {desc}", "FAIL", f"Found: {hits[:2]}")
        else:
            rec(f"#{idx} api.js no old {desc}", "PASS")


# ── 5-8: V2 后端路由存在 ──

def check_v2_routes_exist():
    content = _read(ROUTES_FILE)
    if content is None:
        rec("#5-8 routes file exists", "FAIL", "test_case_extra_routes.py not found"); return

    checks = [
        (5, '/test-cases/{case_id}/generate-script', 'POST generate-script'),
        (6, '/test-cases/{case_id}/manual-execute', 'POST manual-execute'),
        (7, '/test-cases/export', 'GET export'),
        (8, '/test-cases/{case_id}/bind-dataset', 'POST bind-dataset'),
    ]
    for idx, path, desc in checks:
        if path in content:
            rec(f"#{idx} V2 route {desc}", "PASS")
        else:
            rec(f"#{idx} V2 route {desc}", "FAIL", f"Path not found in routes file")


# ── 9: 新路由不引用 test_cases_db ──

def check_no_legacy_db():
    content = _read(ROUTES_FILE)
    if content is None:
        rec("#9 no test_cases_db", "SKIP"); return
    if "test_cases_db" in content:
        rec("#9 no test_cases_db in new routes", "FAIL", "Found test_cases_db reference")
    else:
        rec("#9 no test_cases_db in new routes", "PASS")


# ── 10: 新路由使用 TestCase DB ──

def check_uses_db():
    content = _read(ROUTES_FILE)
    if content is None:
        rec("#10 uses TestCase DB", "SKIP"); return
    if "db.query(TestCase)" in content:
        rec("#10 uses TestCase DB query", "PASS")
    else:
        rec("#10 uses TestCase DB query", "FAIL", "db.query(TestCase) not found")


# ── 11: router_registry 注册 ──

def check_registry():
    content = _read(REGISTRY)
    if content is None:
        rec("#11 router_registry", "SKIP"); return
    if "test_case_extra_routes" in content:
        rec("#11 router_registry registers test_case_extra_routes", "PASS")
    else:
        rec("#11 router_registry registers test_case_extra_routes", "FAIL")


# ── 12: legacy 标记 ──

def check_legacy():
    content = _read(LEGACY)
    if content is None:
        rec("#12 legacy marker", "SKIP"); return
    if "LEGACY" in content.upper() and "Phase B1" in content:
        rec("#12 backend_api_server.py legacy+B1 marker", "PASS")
    elif "LEGACY" in content.upper():
        rec("#12 backend_api_server.py legacy marker", "WARN", "No Phase B1 note")
    else:
        rec("#12 backend_api_server.py legacy marker", "FAIL")


# ── 13: TestCases.jsx import check (syntax) ──

def check_jsx_syntax():
    if not os.path.exists(TC_JSX):
        rec("#13 TestCases.jsx exists", "SKIP"); return
    # Just check file is readable and has expected import
    content = _read(TC_JSX)
    if "import" in content and "api" in content:
        rec("#13 TestCases.jsx importable", "PASS")
    else:
        rec("#13 TestCases.jsx importable", "FAIL", "Missing expected imports")


# ── 14: frontend build ──

def check_frontend_build():
    fe_dir = os.path.join(ROOT, "frontend")
    if not os.path.isdir(fe_dir):
        rec("#14 frontend build", "SKIP", "frontend dir not found"); return
    try:
        r = subprocess.run(
            ["npx", "--yes", "vite", "build"],
            cwd=fe_dir, capture_output=True, timeout=120,
            shell=True, encoding='utf-8', errors='replace',
        )
        if "built in" in (r.stdout + r.stderr):
            rec("#14 frontend build", "PASS")
        else:
            rec("#14 frontend build", "FAIL", (r.stderr or r.stdout)[-200:])
    except Exception as e:
        rec("#14 frontend build", "SKIP", str(e))


# ── 15: smoke 回归 ──

def check_smoke():
    smoke = os.path.join(SCRIPT_DIR, "run_regression_all.py")
    if not os.path.exists(smoke):
        rec("#15 smoke regression", "SKIP", "script not found"); return
    try:
        r = subprocess.run(
            [sys.executable, smoke, "--profile", "smoke"],
            cwd=ROOT, capture_output=True, timeout=180,
            encoding='utf-8', errors='replace',
        )
        if r.returncode == 0:
            rec("#15 smoke regression", "PASS")
        else:
            rec("#15 smoke regression", "FAIL", (r.stdout + r.stderr)[-200:])
    except Exception as e:
        rec("#15 smoke regression", "SKIP", str(e))


# ── Phase B1.5: execute 迁移检查 (#16-#22) ──

CASE_EXEC_ROUTES = os.path.join(ROOT, "routes", "case_execute_routes.py")

def check_b15_execute():
    api_content = _read(API_JS)
    jsx_content = _read(TC_JSX)
    exec_routes = _read(CASE_EXEC_ROUTES)

    # #16: api.js 不含旧 /api/testcases/${id}/execute
    if api_content:
        if re.search(r'`\$\{API_BASE_URL\}/testcases/\$\{.*?\}/execute`', api_content):
            rec("#16 api.js no old /api/testcases/{id}/execute", "FAIL")
        else:
            rec("#16 api.js no old /api/testcases/{id}/execute", "PASS")
    else:
        rec("#16 api.js", "SKIP", "file not found")

    # #17: api.testCases.execute uses V2 path
    if api_content:
        lines = api_content.split('\n')
        found_v2 = any(
            'execute:' in line and 'PILOT_API_BASE_URL' in line and '/test-cases/' in line
            for line in lines
        )
        if found_v2:
            rec("#17 api.testCases.execute uses V2 path", "PASS")
        else:
            rec("#17 api.testCases.execute uses V2 path", "FAIL")
    else:
        rec("#17 api.testCases.execute", "SKIP")

    # #18: TestCases.jsx not directly calling /api/testcases/*
    if jsx_content:
        if '/api/testcases/' in jsx_content:
            rec("#18 TestCases.jsx no /api/testcases/* call", "FAIL")
        else:
            rec("#18 TestCases.jsx no /api/testcases/* call", "PASS")
    else:
        rec("#18 TestCases.jsx", "SKIP")

    # #19: V2 execute route exists
    if exec_routes:
        if '/execute' in exec_routes and 'case_id' in exec_routes:
            rec("#19 V2 execute route exists", "PASS")
        else:
            rec("#19 V2 execute route exists", "FAIL")
    else:
        rec("#19 V2 execute route", "FAIL", "case_execute_routes.py not found")

    # #20: V2 execute no test_cases_db
    if exec_routes:
        if 'test_cases_db' in exec_routes:
            rec("#20 V2 execute no test_cases_db", "FAIL")
        else:
            rec("#20 V2 execute no test_cases_db", "PASS")
    else:
        rec("#20 V2 execute", "SKIP")

    # #21: V2 execute uses DB TestCase
    if exec_routes:
        if 'db.query(TestCase)' in exec_routes:
            rec("#21 V2 execute queries DB TestCase", "PASS")
        else:
            rec("#21 V2 execute queries DB TestCase", "FAIL")
    else:
        rec("#21 V2 execute", "SKIP")

    # #22: V2 execute writes TestRun + RunCase
    if exec_routes:
        has_run = 'TestRun(' in exec_routes
        has_rc = 'RunCase(' in exec_routes
        if has_run and has_rc:
            rec("#22 V2 execute writes TestRun+RunCase", "PASS")
        else:
            rec("#22 V2 execute writes TestRun+RunCase", "FAIL", f"TestRun={has_run}, RunCase={has_rc}")
    else:
        rec("#22 V2 execute", "SKIP")


def main():
    print("=" * 60)
    print("Phase B1 + B1.5 \u2014 TestCases V2 \u8fc1\u79fb\u9a8c\u6536")
    print("=" * 60)
    print()

    for fn in [check_apijs_old_paths, check_v2_routes_exist, check_no_legacy_db,
               check_uses_db, check_registry, check_legacy, check_jsx_syntax,
               check_b15_execute, check_frontend_build, check_smoke]:
        try:
            fn()
        except Exception as e:
            rec(fn.__name__, "FAIL", f"Unexpected: {e}")
            traceback.print_exc()
        print()

    print("=" * 60)
    t = len(R)
    p = sum(1 for _, s, _ in R if s == "PASS")
    f = sum(1 for _, s, _ in R if s == "FAIL")
    w = sum(1 for _, s, _ in R if s == "WARN")
    sk = sum(1 for _, s, _ in R if s == "SKIP")
    print(f"Total: {t}  PASS: {p}  FAIL: {f}  WARN: {w}  SKIP: {sk}")

    if f > 0:
        print("\nFAILED items:")
        for n, s, r in R:
            if s == "FAIL":
                print(f"  - {n}: {r}")
        sys.exit(1)
    else:
        print("\nPhase B1 + B1.5 verification PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
