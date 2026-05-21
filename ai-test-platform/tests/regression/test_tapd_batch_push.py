#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A2 验收脚本：TAPD 批量推送

不依赖真实 TAPD 环境，使用 monkey-patch 替换 push_bug_to_tapd / load_tapd_config。

覆盖项：
1. 后端接口 batch-push-to-tapd 存在
2. BatchPushToTapdRequest 模型定义
3. api.js 包含 batchPushFindingsToTapd
4. CodeCompare.jsx 包含批量模式 / handleBatchPushTapd
5. 空 finding_ids 返回 400
6. 超过 100 条返回 400
7. 推送成功的 finding 写回 tapd_bug_id
8. 已推送的 finding 默认被 skip
9. type=implemented 的 finding 被 skip
10. manual_status=false_positive 的 finding 被 skip
11. 不存在的 finding 标记为 not_found
12. 推送失败时仍返回成功并标记单条 failed
13. 多个 report 中的 finding 都能正确持久化
14. 不泄漏 api_password 到日志
"""
from __future__ import annotations

import io
import logging
import sys
import traceback
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

R: list = []


def rec(name: str, status: str, reason: str = ""):
    R.append((name, status, reason))
    icon = {"PASS": "OK", "FAIL": "XX", "WARN": "!!", "SKIP": "--"}.get(status, "??")
    print(f"  [{icon}] {status:4s} {name}" + (f" | {reason}" if reason else ""))


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


# ══════════════════════════════════════════════════════════════════
# 静态检查
# ══════════════════════════════════════════════════════════════════

def check_backend_endpoint_exists():
    routes_file = ROOT / "routes" / "code_compare_routes.py"
    content = _read(routes_file)
    if "/batch-push-to-tapd" in content and "batch_push_findings_to_tapd" in content:
        rec("#1 batch-push endpoint exists", "PASS")
    else:
        rec("#1 batch-push endpoint exists", "FAIL")

    if "class BatchPushToTapdRequest" in content and "finding_ids" in content:
        rec("#2 BatchPushToTapdRequest model defined", "PASS")
    else:
        rec("#2 BatchPushToTapdRequest model defined", "FAIL")


def check_api_js():
    api_file = ROOT / "frontend" / "src" / "services" / "api.js"
    content = _read(api_file)
    if "batchPushFindingsToTapd" in content:
        rec("#3 api.js has batchPushFindingsToTapd", "PASS")
    else:
        rec("#3 api.js has batchPushFindingsToTapd", "FAIL")


def check_frontend_jsx():
    jsx_file = ROOT / "frontend" / "src" / "pages" / "CodeCompare.jsx"
    content = _read(jsx_file)
    has_batch_mode = "batchMode" in content and "selectedIds" in content
    has_handler = "handleBatchPushTapd" in content
    has_modal = "BatchPushResultModal" in content
    has_checkbox = "Checkbox" in content
    if has_batch_mode and has_handler and has_modal and has_checkbox:
        rec("#4 CodeCompare.jsx batch UI complete", "PASS")
    else:
        missing = []
        if not has_batch_mode: missing.append("batchMode/selectedIds")
        if not has_handler: missing.append("handler")
        if not has_modal: missing.append("BatchPushResultModal")
        if not has_checkbox: missing.append("Checkbox")
        rec("#4 CodeCompare.jsx batch UI complete", "FAIL", f"missing: {', '.join(missing)}")


# ══════════════════════════════════════════════════════════════════
# 功能测试（mock TAPD client）
# ══════════════════════════════════════════════════════════════════

def _build_test_app():
    """构建 minimal FastAPI app，stub TAPD"""
    import importlib.util
    import types

    # ── stub python-multipart ──
    if "multipart" not in sys.modules:
        mp = types.ModuleType("multipart")
        mp.__version__ = "0.0.0-stub"
        sys.modules["multipart"] = mp
        mp_mp = types.ModuleType("multipart.multipart")
        mp_mp.parse_options_header = lambda h: (b"", {})
        sys.modules["multipart.multipart"] = mp_mp

    from fastapi import FastAPI

    # ── stub services 包 ──
    services_pkg = types.ModuleType("services")
    services_pkg.__path__ = [str(ROOT / "services")]
    sys.modules["services"] = services_pkg
    sys.modules["services.code_compare_storage_service"] = types.ModuleType(
        "services.code_compare_storage_service"
    )

    db_pkg = types.ModuleType("database")
    db_pkg.__path__ = [str(ROOT / "database")]
    sys.modules.setdefault("database", db_pkg)

    # ── 直接加载 services/tapd_service.py ──
    spec = importlib.util.spec_from_file_location(
        "services.tapd_service", ROOT / "services" / "tapd_service.py"
    )
    tapd_service = importlib.util.module_from_spec(spec)
    sys.modules["services.tapd_service"] = tapd_service
    spec.loader.exec_module(tapd_service)

    # ── 注入 fake config 和 fake push 行为 ──
    push_log: list = []

    def _fake_load_config():
        return {
            "workspace_id": "TEST_WS",
            "api_user": "TEST_USER",
            "api_password": "TEST_PWD",  # nosec: test fixture
            "default_reporter": "tester",
        }

    # bug counter
    next_bug_id = [10000]
    fail_for_finding: set = set()  # finding 标记为推送失败

    def _fake_push(config, title, description, severity="major", priority="P2",
                   module="", reporter="", extra_fields=None):
        # 记录调用
        push_log.append({"title": title, "severity": severity, "priority": priority, "module": module})
        # 是否需要模拟失败：根据 title 中的 "[FAIL_FOR_TEST]"
        if "[FAIL_FOR_TEST]" in title:
            return {"success": False, "message": "fake push failure"}
        bug_id = str(next_bug_id[0])
        next_bug_id[0] += 1
        return {
            "success": True,
            "bug_id": bug_id,
            "url": f"https://www.tapd.cn/TEST_WS/bugtrace/bugs/view?bug_id={bug_id}",
            "title": title,
        }

    tapd_service.load_tapd_config = _fake_load_config
    tapd_service.push_bug_to_tapd = _fake_push

    # ── 加载 routes ──
    from routes.code_compare_routes import router, _reports
    # stub _resolve_tapd_iteration to avoid network
    import routes.code_compare_routes as cc_routes
    cc_routes._resolve_tapd_iteration = lambda config, name: None

    app = FastAPI()
    app.include_router(router)

    # ── 准备测试数据 ──
    _reports.clear()

    report_a = {
        "report_id": "rpt_a2_a",
        "report_name": "A2 test report A",
        "code_snapshot_id": "snap_a",
        "code_snapshot_name": "snapshot A",
        "ai_mode": "rule_based",
        "summary": {"total_req_points": 5, "implemented": 1, "missing": 2, "extra": 1, "uncertain": 0, "risk": 1},
        "findings": [
            {"finding_id": "f_normal_1", "type": "missing", "requirement_point": "需求A1"},
            {"finding_id": "f_normal_2", "type": "risk", "requirement_point": "需求A2"},
            {"finding_id": "f_already", "type": "missing", "requirement_point": "需求已推送",
             "tapd_bug_id": "999", "tapd_url": "https://www.tapd.cn/exists"},
            {"finding_id": "f_implemented", "type": "implemented", "requirement_point": "需求已实现"},
            {"finding_id": "f_false_positive", "type": "missing", "requirement_point": "[FAIL_FOR_TEST]误报已标记",
             "manual_status": "false_positive"},
            {"finding_id": "f_will_fail", "type": "uncertain",
             "requirement_point": "[FAIL_FOR_TEST] 推送会失败的"},
        ],
        "created_at": "2026-01-01T00:00:00",
    }
    report_b = {
        "report_id": "rpt_a2_b",
        "report_name": "A2 test report B",
        "code_snapshot_id": "snap_b",
        "code_snapshot_name": "snapshot B",
        "ai_mode": "rule_based",
        "summary": {"total_req_points": 1, "implemented": 0, "missing": 1, "extra": 0, "uncertain": 0, "risk": 0},
        "findings": [
            {"finding_id": "f_in_b", "type": "missing", "requirement_point": "需求B"},
        ],
        "created_at": "2026-01-01T00:00:00",
    }
    _reports[report_a["report_id"]] = report_a
    _reports[report_b["report_id"]] = report_b
    return app, _reports, push_log


def check_functional():
    try:
        from fastapi.testclient import TestClient
    except ImportError as e:
        rec("#5-13 functional batch push", "SKIP", f"testclient missing: {e}")
        return

    app, _reports, push_log = _build_test_app()
    client = TestClient(app)

    # ── #5: 空 finding_ids ──
    r = client.post("/api/v2/code-compare/findings/batch-push-to-tapd", json={"finding_ids": []})
    if r.status_code == 400:
        rec("#5 empty finding_ids returns 400", "PASS")
    else:
        rec("#5 empty finding_ids returns 400", "FAIL", f"status={r.status_code}")

    # ── #6: 超过 100 条 ──
    over_limit = [f"f{i}" for i in range(101)]
    r = client.post("/api/v2/code-compare/findings/batch-push-to-tapd", json={"finding_ids": over_limit})
    if r.status_code == 400:
        rec("#6 >100 finding_ids returns 400", "PASS")
    else:
        rec("#6 >100 finding_ids returns 400", "FAIL", f"status={r.status_code}")

    # ── 主测试: 同时含成功/已推送/已实现/误报/失败/跨report ──
    payload = {
        "finding_ids": [
            "f_normal_1", "f_normal_2",  # 应推送成功
            "f_already",                  # 跳过（已推送）
            "f_implemented",              # 跳过（已实现）
            "f_false_positive",           # 跳过（误报）
            "f_will_fail",                # 失败
            "f_in_b",                     # 跨 report 也能推送
            "f_does_not_exist",           # not_found
        ],
        "skip_already_pushed": True,
    }
    r = client.post("/api/v2/code-compare/findings/batch-push-to-tapd", json=payload)
    if r.status_code != 200:
        rec("#7-13 main batch push call", "FAIL", f"status={r.status_code} text={r.text[:200]}")
        return

    body = r.json()
    if not body.get("success"):
        rec("#7-13 main batch push call", "FAIL", f"body={body}")
        return

    data = body.get("data", {})
    results_by_id = {row["finding_id"]: row for row in data.get("results", [])}

    # ── #7: 推送成功的 finding 写回 tapd_bug_id ──
    f_normal_1 = next(f for f in _reports["rpt_a2_a"]["findings"] if f["finding_id"] == "f_normal_1")
    if f_normal_1.get("tapd_bug_id") and results_by_id.get("f_normal_1", {}).get("status") == "pushed":
        rec("#7 successful push writes back tapd_bug_id", "PASS")
    else:
        rec("#7 successful push writes back tapd_bug_id", "FAIL",
            f"finding={f_normal_1.get('tapd_bug_id')} result={results_by_id.get('f_normal_1')}")

    # ── #8: 已推送 skip ──
    if results_by_id.get("f_already", {}).get("status") == "already_pushed" and \
       results_by_id["f_already"].get("bug_id") == "999":
        rec("#8 already-pushed finding is skipped", "PASS")
    else:
        rec("#8 already-pushed finding is skipped", "FAIL", f"result={results_by_id.get('f_already')}")

    # ── #9: type=implemented skip ──
    if results_by_id.get("f_implemented", {}).get("status") == "skipped_implemented":
        rec("#9 implemented finding skipped", "PASS")
    else:
        rec("#9 implemented finding skipped", "FAIL", f"result={results_by_id.get('f_implemented')}")

    # ── #10: false_positive skip ──
    if results_by_id.get("f_false_positive", {}).get("status") == "skipped_false_positive":
        rec("#10 false_positive finding skipped", "PASS")
    else:
        rec("#10 false_positive finding skipped", "FAIL", f"result={results_by_id.get('f_false_positive')}")

    # ── #11: not_found ──
    if results_by_id.get("f_does_not_exist", {}).get("status") == "not_found":
        rec("#11 unknown finding -> not_found", "PASS")
    else:
        rec("#11 unknown finding -> not_found", "FAIL", f"result={results_by_id.get('f_does_not_exist')}")

    # ── #12: failed but interface still 200 ──
    if results_by_id.get("f_will_fail", {}).get("status") == "failed" and r.status_code == 200:
        rec("#12 push failure returns failed item, not 5xx", "PASS")
    else:
        rec("#12 push failure returns failed item, not 5xx", "FAIL",
            f"status={r.status_code} result={results_by_id.get('f_will_fail')}")

    # ── #13: 跨 report 持久化 ──
    f_in_b = next(f for f in _reports["rpt_a2_b"]["findings"] if f["finding_id"] == "f_in_b")
    if f_in_b.get("tapd_bug_id"):
        rec("#13 cross-report finding pushed and saved", "PASS")
    else:
        rec("#13 cross-report finding pushed and saved", "FAIL", f"finding={f_in_b}")


def check_no_credential_leaked():
    """运行时检查日志不泄漏 api_password / TEST_PWD"""
    try:
        from fastapi.testclient import TestClient
    except ImportError:
        rec("#14 runtime log no credential leak", "SKIP")
        return

    app, _reports, _ = _build_test_app()
    client = TestClient(app)

    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    handler.setLevel(logging.DEBUG)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    try:
        client.post("/api/v2/code-compare/findings/batch-push-to-tapd",
                    json={"finding_ids": ["f_normal_1", "f_will_fail"]})
        log_output = buf.getvalue()
        bad = ("TEST_PWD" in log_output) or ("api_password=" in log_output)
        if not bad:
            rec("#14 runtime log no credential leak", "PASS")
        else:
            rec("#14 runtime log no credential leak", "FAIL")
    finally:
        root_logger.removeHandler(handler)


# ══════════════════════════════════════════════════════════════════
# 主入口
# ══════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("A2 - TAPD Batch Push Verification")
    print("=" * 60)

    checks = [
        check_backend_endpoint_exists,
        check_api_js,
        check_frontend_jsx,
        check_functional,
        check_no_credential_leaked,
    ]

    for fn in checks:
        try:
            fn()
        except Exception as e:
            rec(fn.__name__, "FAIL", f"Unexpected: {type(e).__name__}: {e}")
            traceback.print_exc()

    print()
    print("=" * 60)
    t = len(R)
    pcnt = sum(1 for _, s, _ in R if s == "PASS")
    fcnt = sum(1 for _, s, _ in R if s == "FAIL")
    wcnt = sum(1 for _, s, _ in R if s == "WARN")
    skcnt = sum(1 for _, s, _ in R if s == "SKIP")
    print(f"Total: {t}  PASS: {pcnt}  FAIL: {fcnt}  WARN: {wcnt}  SKIP: {skcnt}")

    if fcnt > 0:
        print("\nFAILED items:")
        for n, s, r in R:
            if s == "FAIL":
                print(f"  - {n}: {r}")
        sys.exit(1)
    print("\n[PASS] A2 TAPD batch push verification PASSED")
    sys.exit(0)


if __name__ == "__main__":
    main()
