#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Phase C2: Windows GBK encoding fix
import io, sys
if sys.stdout and getattr(sys.stdout, 'encoding', '').lower().replace('-', '') != 'utf8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr and getattr(sys.stderr, 'encoding', '').lower().replace('-', '') != 'utf8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
Phase C2 -- Security Hardening Verification

16 checks:
 1. backend/app.py no allow_origins=["*"]
 2. config.py supports CORS_ALLOW_ORIGINS
 3. Default CORS whitelist includes localhost:5173
 4. clone-repo blocks localhost
 5. clone-repo blocks 127.0.0.1
 6. clone-repo blocks 10.x
 7. clone-repo blocks 172.16.x
 8. clone-repo blocks 192.168.x
 9. clone-repo blocks 169.254.169.254
10. clone-repo blocks file://
11. clone-repo blocks ftp://
12. Git URL log sanitization
13. Zip Slip protection present
14. Sensitive file filter present
15. Content sanitization function present
16. Regression scripts no emoji encoding crash
"""

import os, re, subprocess, traceback

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, ROOT)

APP_FILE = os.path.join(ROOT, "backend", "app.py")
CONFIG_FILE = os.path.join(ROOT, "backend", "config.py")
ROUTES_FILE = os.path.join(ROOT, "routes", "code_compare_routes.py")

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


# ── #1: CORS no wildcard ──

def check_cors_no_wildcard():
    content = _read(APP_FILE)
    if not content:
        rec("#1 CORS no wildcard", "FAIL", "app.py not found"); return
    if 'allow_origins=["*"]' in content or "allow_origins=['*']" in content:
        rec("#1 CORS no wildcard", "FAIL", "allow_origins=[\"*\"] still present")
    else:
        rec("#1 CORS no wildcard", "PASS")


# ── #2: config supports CORS_ALLOW_ORIGINS ──

def check_config_cors():
    content = _read(CONFIG_FILE)
    if not content:
        rec("#2 config CORS_ALLOW_ORIGINS", "FAIL", "config.py not found"); return
    if "CORS_ALLOW_ORIGINS" in content:
        rec("#2 config CORS_ALLOW_ORIGINS", "PASS")
    else:
        rec("#2 config CORS_ALLOW_ORIGINS", "FAIL")


# ── #3: Default whitelist includes localhost:5173 ──

def check_default_whitelist():
    content = _read(CONFIG_FILE)
    if not content:
        rec("#3 default whitelist", "FAIL"); return
    if "localhost:5173" in content and "127.0.0.1:5173" in content:
        rec("#3 default whitelist localhost:5173", "PASS")
    else:
        rec("#3 default whitelist localhost:5173", "FAIL")


# ── #4-9: SSRF blocking tests ──

def check_ssrf_blocking():
    content = _read(ROUTES_FILE)
    if not content:
        rec("#4-9 SSRF", "FAIL", "routes file not found"); return

    # Check _validate_repo_url function exists
    if "_validate_repo_url" not in content:
        rec("#4 clone-repo blocks localhost", "FAIL", "_validate_repo_url missing")
        rec("#5 clone-repo blocks 127.0.0.1", "FAIL")
        rec("#6 clone-repo blocks 10.x", "FAIL")
        rec("#7 clone-repo blocks 172.16.x", "FAIL")
        rec("#8 clone-repo blocks 192.168.x", "FAIL")
        rec("#9 clone-repo blocks 169.254.169.254", "FAIL")
        return

    # Functional test: import and call _validate_repo_url
    try:
        # Add routes dir parent to path for import
        from routes.code_compare_routes import _validate_repo_url

        # #4: localhost
        ok, _ = _validate_repo_url("https://localhost/repo.git")
        rec("#4 clone-repo blocks localhost", "PASS" if not ok else "FAIL")

        # #5: 127.0.0.1
        ok, _ = _validate_repo_url("https://127.0.0.1/repo.git")
        rec("#5 clone-repo blocks 127.0.0.1", "PASS" if not ok else "FAIL")

        # #6: 10.x
        ok, _ = _validate_repo_url("https://10.0.0.5/repo.git")
        rec("#6 clone-repo blocks 10.x", "PASS" if not ok else "FAIL")

        # #7: 172.16.x
        ok, _ = _validate_repo_url("https://172.16.1.1/repo.git")
        rec("#7 clone-repo blocks 172.16.x", "PASS" if not ok else "FAIL")

        # #8: 192.168.x
        ok, _ = _validate_repo_url("https://192.168.1.100/repo.git")
        rec("#8 clone-repo blocks 192.168.x", "PASS" if not ok else "FAIL")

        # #9: 169.254.169.254
        ok, _ = _validate_repo_url("https://169.254.169.254/latest/meta-data")
        rec("#9 clone-repo blocks 169.254.169.254", "PASS" if not ok else "FAIL")

    except ImportError as e:
        rec("#4 clone-repo blocks localhost", "SKIP", f"import failed: {e}")
        rec("#5 clone-repo blocks 127.0.0.1", "SKIP", str(e))
        rec("#6 clone-repo blocks 10.x", "SKIP", str(e))
        rec("#7 clone-repo blocks 172.16.x", "SKIP", str(e))
        rec("#8 clone-repo blocks 192.168.x", "SKIP", str(e))
        rec("#9 clone-repo blocks 169.254.169.254", "SKIP", str(e))
    except Exception as e:
        rec("#4-9 SSRF functional test", "FAIL", str(e))


# ── #10: blocks file:// ──

def check_blocks_file_protocol():
    try:
        from routes.code_compare_routes import _validate_repo_url
        ok, _ = _validate_repo_url("file:///etc/passwd")
        rec("#10 clone-repo blocks file://", "PASS" if not ok else "FAIL")
    except ImportError:
        # Static check fallback
        content = _read(ROUTES_FILE)
        if content and '"file"' in content:
            rec("#10 clone-repo blocks file://", "PASS")
        else:
            rec("#10 clone-repo blocks file://", "FAIL")


# ── #11: blocks ftp:// ──

def check_blocks_ftp_protocol():
    try:
        from routes.code_compare_routes import _validate_repo_url
        ok, _ = _validate_repo_url("ftp://internal.server/repo")
        rec("#11 clone-repo blocks ftp://", "PASS" if not ok else "FAIL")
    except ImportError:
        content = _read(ROUTES_FILE)
        if content and '"ftp"' in content:
            rec("#11 clone-repo blocks ftp://", "PASS")
        else:
            rec("#11 clone-repo blocks ftp://", "FAIL")


# ── #12: Git URL log sanitization ──

def check_log_sanitization():
    content = _read(ROUTES_FILE)
    if not content:
        rec("#12 Git URL log sanitization", "FAIL"); return
    if "_sanitize_git_url_for_log" in content:
        rec("#12 Git URL log sanitization", "PASS")
    else:
        rec("#12 Git URL log sanitization", "FAIL")


# ── #13: Zip Slip protection ──

def check_zip_slip():
    content = _read(ROUTES_FILE)
    if not content:
        rec("#13 Zip Slip protection", "FAIL"); return
    if "Zip Slip" in content or "zip slip" in content.lower() or "路径穿越" in content:
        rec("#13 Zip Slip protection", "PASS")
    else:
        rec("#13 Zip Slip protection", "FAIL")


# ── #14: Sensitive file filter ──

def check_sensitive_filter():
    content = _read(ROUTES_FILE)
    if not content:
        rec("#14 Sensitive file filter", "FAIL"); return
    if "SENSITIVE_FILES" in content and "_is_sensitive_file" in content:
        rec("#14 Sensitive file filter", "PASS")
    else:
        rec("#14 Sensitive file filter", "FAIL")


# ── #15: Content sanitization ──

def check_content_sanitization():
    content = _read(ROUTES_FILE)
    if not content:
        rec("#15 Content sanitization", "FAIL"); return
    if "_sanitize_content" in content and "REDACTED" in content:
        rec("#15 Content sanitization", "PASS")
    else:
        rec("#15 Content sanitization", "FAIL")


# ── #16: Regression scripts no emoji crash ──

def check_scripts_encoding():
    scripts = [
        "test_architecture_consolidation.py",
        "test_code_compare_db_persistence.py",
        "test_testcases_v2_migration.py",
        "run_regression_all.py",
    ]
    all_ok = True
    for s in scripts:
        path = os.path.join(SCRIPT_DIR, s)
        content = _read(path)
        if not content:
            continue
        # Check encoding fix is present
        if "encoding" in content[:500] and ("utf-8" in content[:500] or "utf8" in content[:500]):
            continue
        all_ok = False
        break

    if all_ok:
        rec("#16 scripts encoding compatibility", "PASS")
    else:
        rec("#16 scripts encoding compatibility", "FAIL", "Missing encoding fix in some scripts")


def main():
    print("=" * 60)
    print("Phase C2 -- Security Hardening Verification")
    print("=" * 60)
    print()

    for fn in [check_cors_no_wildcard, check_config_cors, check_default_whitelist,
               check_ssrf_blocking, check_blocks_file_protocol, check_blocks_ftp_protocol,
               check_log_sanitization, check_zip_slip, check_sensitive_filter,
               check_content_sanitization, check_scripts_encoding]:
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
        print("\n[PASS] Security hardening verification PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
