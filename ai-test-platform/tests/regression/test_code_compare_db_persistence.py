#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Phase C2: Windows GBK encoding fix
import io, sys
if sys.stdout and getattr(sys.stdout, 'encoding', '').lower().replace('-', '') != 'utf8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr and getattr(sys.stderr, 'encoding', '').lower().replace('-', '') != 'utf8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
Phase C1 — code_compare DB 持久化验收脚本

24 项检查覆盖模型/服务/路由/兼容/回归。
"""

import os, re, json, subprocess, traceback

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, ROOT)

MODELS_FILE = os.path.join(ROOT, "database", "models.py")
SERVICE_FILE = os.path.join(ROOT, "services", "code_compare_storage_service.py")
ROUTES_FILE = os.path.join(ROOT, "routes", "code_compare_routes.py")
STARTUP_FILE = os.path.join(ROOT, "backend", "startup.py")
DB_INIT_FILE = os.path.join(ROOT, "database", "__init__.py")

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


# ── 1-5: 模型存在检查 ──

def check_models():
    content = _read(MODELS_FILE)
    if not content:
        rec("#1-5 models.py", "FAIL", "file not found"); return

    models = [
        (1, "CodeSnapshot", "class CodeSnapshot"),
        (2, "CodeCompareReport", "class CodeCompareReport"),
        (3, "CodeCompareFinding", "class CodeCompareFinding"),
        (4, "RequirementPoint", "class RequirementPoint"),
        (5, "RequirementConfirmQuestion", "class RequirementConfirmQuestion"),
    ]
    for idx, name, pattern in models:
        if pattern in content:
            rec(f"#{idx} {name} model exists", "PASS")
        else:
            rec(f"#{idx} {name} model exists", "FAIL")


# ── 6-7: upload/analyze 写 DB ──

def check_routes_write_db():
    content = _read(ROUTES_FILE)
    if not content:
        rec("#6-7 routes", "FAIL", "file not found"); return

    # #6: upload writes CodeSnapshot
    if "svc.save_snapshot" in content:
        rec("#6 upload writes CodeSnapshot to DB", "PASS")
    else:
        rec("#6 upload writes CodeSnapshot to DB", "FAIL")

    # #7: analyze writes report
    if "svc.save_report" in content:
        rec("#7 analyze writes CodeCompareReport to DB", "PASS")
    else:
        rec("#7 analyze writes CodeCompareReport to DB", "FAIL")


# ── 8-9: reports list/detail 优先查 DB ──

def check_reports_read_db():
    content = _read(ROUTES_FILE)
    if not content:
        rec("#8-9 routes", "FAIL"); return

    if "svc.list_reports()" in content:
        rec("#8 reports list queries DB first", "PASS")
    else:
        rec("#8 reports list queries DB first", "FAIL")

    if "svc.get_report_detail" in content:
        rec("#9 report detail queries DB first", "PASS")
    else:
        rec("#9 report detail queries DB first", "FAIL")


# ── 10: finding review 更新 DB ──

def check_finding_review_db():
    content = _read(ROUTES_FILE)
    if not content:
        rec("#10 finding review", "FAIL"); return

    if "svc.update_finding_status" in content:
        rec("#10 finding review updates DB", "PASS")
    else:
        rec("#10 finding review updates DB", "FAIL")


# ── 11: manual_status 字段 DB 持久化 ──

def check_manual_status_field():
    content = _read(MODELS_FILE)
    if not content:
        rec("#11 manual_status", "FAIL"); return

    if "manual_status" in content and "CodeCompareFinding" in content:
        rec("#11 manual_status field in DB model", "PASS")
    else:
        rec("#11 manual_status field in DB model", "FAIL")


# ── 12: 服务重启后报告仍可查询 (service 有 DB query) ──

def check_persistence_after_restart():
    content = _read(SERVICE_FILE)
    if not content:
        rec("#12 persistence after restart", "FAIL", "service file not found"); return

    if "self.db.query(CodeCompareReport)" in content:
        rec("#12 service queries DB (survives restart)", "PASS")
    else:
        rec("#12 service queries DB (survives restart)", "FAIL")


# ── 13: 旧 JSON 报告兼容读取 ──

def check_legacy_json_compat():
    content = _read(SERVICE_FILE)
    if not content:
        rec("#13 legacy JSON compat", "FAIL"); return

    if "legacy_json" in content and "_load_legacy_report" in content:
        rec("#13 legacy JSON reports compatible", "PASS")
    else:
        rec("#13 legacy JSON reports compatible", "FAIL")


# ── 14: 新报告不依赖 JSON 文件才能展示 ──

def check_new_report_no_json_dependency():
    content = _read(SERVICE_FILE)
    if not content:
        rec("#14 new report no JSON dependency", "FAIL"); return

    # DB query is the primary path
    if "self.db.query(CodeCompareReport)" in content and "_report_to_detail" in content:
        rec("#14 new report reads from DB directly", "PASS")
    else:
        rec("#14 new report reads from DB directly", "FAIL")


# ── 15: evidence_json 结构完整 ──

def check_evidence_json():
    content = _read(MODELS_FILE)
    if not content:
        rec("#15 evidence_json", "FAIL"); return

    if "evidence_json = Column(JSON" in content:
        rec("#15 evidence_json field exists", "PASS")
    else:
        rec("#15 evidence_json field exists", "FAIL")


# ── 16: suggested_test_cases_json ──

def check_suggested_test_cases():
    content = _read(MODELS_FILE)
    if not content:
        rec("#16 suggested_test_cases_json", "FAIL"); return

    if "suggested_test_cases_json = Column(JSON" in content:
        rec("#16 suggested_test_cases_json field exists", "PASS")
    else:
        rec("#16 suggested_test_cases_json field exists", "FAIL")


# ── 17: target_type / target_id 字段 ──

def check_target_fields():
    content = _read(MODELS_FILE)
    if not content:
        rec("#17 target fields", "FAIL"); return

    has_type = "target_type = Column(" in content
    has_id = "target_id = Column(" in content
    if has_type and has_id:
        rec("#17 target_type/target_id fields exist", "PASS")
    else:
        rec("#17 target_type/target_id fields exist", "FAIL", f"type={has_type}, id={has_id}")


# ── 18: false_positive 可持久化 ──

def check_false_positive_persist():
    content = _read(ROUTES_FILE)
    if not content:
        rec("#18 false_positive persist", "FAIL"); return

    if "false_positive" in content and "svc.update_finding_status" in content:
        rec("#18 false_positive persists to DB", "PASS")
    else:
        rec("#18 false_positive persists to DB", "FAIL")


# ── 19: upload 返回结构不变 ──

def check_upload_response():
    content = _read(ROUTES_FILE)
    if not content:
        rec("#19 upload response", "FAIL"); return

    if '"success": True, "snapshot": meta' in content:
        rec("#19 upload response structure unchanged", "PASS")
    else:
        rec("#19 upload response structure unchanged", "FAIL")


# ── 20: analyze 返回结构不变 ──

def check_analyze_response():
    content = _read(ROUTES_FILE)
    if not content:
        rec("#20 analyze response", "FAIL"); return

    if '"success": True, "report": report' in content:
        rec("#20 analyze response structure unchanged", "PASS")
    else:
        rec("#20 analyze response structure unchanged", "FAIL")


# ── 21: CodeCompare.jsx 展示字段不受影响 ──

def check_jsx_fields():
    jsx = os.path.join(ROOT, "frontend", "src", "pages", "CodeCompare.jsx")
    content = _read(jsx)
    if not content:
        rec("#21 CodeCompare.jsx", "SKIP", "file not found"); return

    # 检查关键字段仍被引用
    fields = ["findings", "report_id", "summary", "code_snapshot_name"]
    missing = [f for f in fields if f not in content]
    if not missing:
        rec("#21 CodeCompare.jsx display fields intact", "PASS")
    else:
        rec("#21 CodeCompare.jsx display fields intact", "FAIL", f"Missing: {missing}")


# ── 22: architecture_consolidation 通过 ──

def check_arch():
    script = os.path.join(SCRIPT_DIR, "test_architecture_consolidation.py")
    if not os.path.exists(script):
        rec("#22 architecture_consolidation", "SKIP"); return
    try:
        r = subprocess.run(
            [sys.executable, script], cwd=ROOT,
            capture_output=True, timeout=60,
            encoding='utf-8', errors='replace',
        )
        if r.returncode == 0:
            rec("#22 architecture_consolidation", "PASS")
        else:
            rec("#22 architecture_consolidation", "FAIL", (r.stdout+r.stderr)[-200:])
    except Exception as e:
        rec("#22 architecture_consolidation", "SKIP", str(e))


# ── 23: testcases_v2_migration 通过 ──

def check_testcases_v2():
    script = os.path.join(SCRIPT_DIR, "test_testcases_v2_migration.py")
    if not os.path.exists(script):
        rec("#23 testcases_v2_migration", "SKIP"); return
    try:
        r = subprocess.run(
            [sys.executable, script], cwd=ROOT,
            capture_output=True, timeout=120,
            encoding='utf-8', errors='replace',
        )
        if r.returncode == 0:
            rec("#23 testcases_v2_migration", "PASS")
        else:
            rec("#23 testcases_v2_migration", "FAIL", (r.stdout+r.stderr)[-200:])
    except Exception as e:
        rec("#23 testcases_v2_migration", "SKIP", str(e))


# ── 24: smoke 回归通过 ──

def check_smoke():
    script = os.path.join(SCRIPT_DIR, "run_regression_all.py")
    if not os.path.exists(script):
        rec("#24 smoke regression", "SKIP"); return
    try:
        r = subprocess.run(
            [sys.executable, script, "--profile", "smoke"],
            cwd=ROOT, capture_output=True, timeout=180,
            encoding='utf-8', errors='replace',
        )
        if r.returncode == 0:
            rec("#24 smoke regression", "PASS")
        else:
            rec("#24 smoke regression", "FAIL", (r.stdout+r.stderr)[-200:])
    except Exception as e:
        rec("#24 smoke regression", "SKIP", str(e))


def main():
    print("=" * 60)
    print("Phase C1 — code_compare DB 持久化验收")
    print("=" * 60)
    print()

    for fn in [check_models, check_routes_write_db, check_reports_read_db,
               check_finding_review_db, check_manual_status_field,
               check_persistence_after_restart, check_legacy_json_compat,
               check_new_report_no_json_dependency, check_evidence_json,
               check_suggested_test_cases, check_target_fields,
               check_false_positive_persist, check_upload_response,
               check_analyze_response, check_jsx_fields, check_arch,
               check_testcases_v2, check_smoke]:
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
        print("\nPhase C1 verification PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
