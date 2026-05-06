#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A1 验收脚本：TAPD 状态回流

不依赖真实 TAPD 环境，使用 monkeypatch 替换 fetch_tapd_bug_status / load_tapd_config。

覆盖项：
1. sync finding TAPD status 接口存在
2. sync report TAPD status 接口存在
3. 未关联 TAPD Bug 的 Finding 返回 TAPD_BUG_NOT_LINKED
4. 已关联 TAPD Bug 的 Finding 可以更新 tapd_status
5. report 级同步可以跳过未关联 Finding
6. TAPD API 失败时不会破坏 Finding 数据
7. 状态同步后 tapd_last_sync_at 更新
8. api.js 存在 syncFindingTapdStatus
9. api.js 存在 syncReportTapdStatus
10. CodeCompare.jsx 展示 TAPD 状态字段
11. 不输出 TAPD token / password 到日志
"""
from __future__ import annotations

import io
import logging
import sys
import traceback
from pathlib import Path

# stdout 编码兼容（Windows GBK）
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

def check_route_endpoints_present():
    routes_file = ROOT / "routes" / "code_compare_routes.py"
    content = _read(routes_file)
    if not content:
        rec("#1 sync-tapd-status endpoint exists (finding)", "FAIL", "routes file empty")
        rec("#2 sync-tapd-status endpoint exists (report)", "FAIL")
        return
    if "/sync-tapd-status" in content and "sync_finding_tapd_status" in content:
        rec("#1 sync-tapd-status endpoint exists (finding)", "PASS")
    else:
        rec("#1 sync-tapd-status endpoint exists (finding)", "FAIL")
    if "sync_report_tapd_status" in content:
        rec("#2 sync-tapd-status endpoint exists (report)", "PASS")
    else:
        rec("#2 sync-tapd-status endpoint exists (report)", "FAIL")


def check_api_js_functions():
    api_file = ROOT / "frontend" / "src" / "services" / "api.js"
    content = _read(api_file)
    if "syncFindingTapdStatus" in content:
        rec("#8 api.js has syncFindingTapdStatus", "PASS")
    else:
        rec("#8 api.js has syncFindingTapdStatus", "FAIL")
    if "syncReportTapdStatus" in content:
        rec("#9 api.js has syncReportTapdStatus", "PASS")
    else:
        rec("#9 api.js has syncReportTapdStatus", "FAIL")


def check_codecompare_jsx_renders_tapd_status():
    jsx_file = ROOT / "frontend" / "src" / "pages" / "CodeCompare.jsx"
    content = _read(jsx_file)
    has_status_field = "tapd_status" in content and "tapd_status_name" in content
    has_sync_handler = "handleSyncFindingTapd" in content and "handleSyncReportTapd" in content
    has_color_map = "TAPD_STATUS_COLORS" in content
    if has_status_field and has_sync_handler and has_color_map:
        rec("#10 CodeCompare.jsx renders TAPD status badge", "PASS")
    else:
        missing = []
        if not has_status_field:
            missing.append("status fields")
        if not has_sync_handler:
            missing.append("sync handlers")
        if not has_color_map:
            missing.append("color map")
        rec("#10 CodeCompare.jsx renders TAPD status badge", "FAIL", f"missing: {', '.join(missing)}")


def check_no_credential_logged():
    """确保 fetch_tapd_bug_status 不把 api_user / api_password 暴露到日志或返回值"""
    svc_file = ROOT / "services" / "tapd_service.py"
    content = _read(svc_file)
    # 简单静态扫描：确保 api_password / api_user 不出现在日志/返回中
    bad_patterns = [
        r"logger\.info\([^)]*api_password",
        r"logger\.warning\([^)]*api_password",
        r"print\([^)]*api_password",
        r"logger\.info\([^)]*api_user",
        r"print\([^)]*api_user",
    ]
    import re as _re
    leak = False
    for pat in bad_patterns:
        if _re.search(pat, content):
            leak = True
            break
    if not leak:
        rec("#11 TAPD service does not log credentials", "PASS")
    else:
        rec("#11 TAPD service does not log credentials", "FAIL", "credential log pattern found")


# ══════════════════════════════════════════════════════════════════
# 功能检查（mock TAPD client）
# ══════════════════════════════════════════════════════════════════

def _build_test_app():
    """构建仅包含 code_compare_routes 的 minimal FastAPI app（含 mock）

    避免触发 services/__init__.py 对 sqlalchemy 的强依赖：
    使用 importlib 把 services/tapd_service.py 作为顶级 'services' 包注入，
    并 stub 出 services.code_compare_storage_service 等 DB 相关模块。
    """
    import importlib.util
    import types

    # ── stub python-multipart（仅用于让 fastapi UploadFile 路由能初始化）──
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

    # stub DB 相关模块（不被实际调用）
    for stub_name in ("services.code_compare_storage_service",):
        mod = types.ModuleType(stub_name)
        sys.modules[stub_name] = mod

    # stub database 模块（routes/code_compare_routes.py 启动时导入）
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

    def _fake_load_config():
        return {
            "workspace_id": "TEST_WS",
            "api_user": "TEST_USER",
            "api_password": "TEST_PWD",  # nosec: test fixture
        }

    _bug_state = {
        "12345": {"tapd_status": "in_progress", "tapd_status_name": "处理中"},
        "99999": {"error": True, "code": "TAPD_BUG_NOT_FOUND"},
    }

    def _fake_fetch_status(config, bug_id):
        st = _bug_state.get(str(bug_id))
        if not st:
            return {"success": False, "code": "TAPD_BUG_NOT_FOUND", "message": "not found"}
        if st.get("error"):
            return {"success": False, "code": st["code"], "message": "fake error"}
        return {
            "success": True,
            "bug_id": str(bug_id),
            "tapd_status": st["tapd_status"],
            "tapd_status_name": st["tapd_status_name"],
            "tapd_modified": "2026-01-01 00:00:00",
        }

    tapd_service.load_tapd_config = _fake_load_config
    tapd_service.fetch_tapd_bug_status = _fake_fetch_status

    # 导入路由（必须在 monkey patch 之后）
    from routes.code_compare_routes import router, _reports

    app = FastAPI()
    app.include_router(router)

    # 注入测试报告 + finding
    test_report = {
        "report_id": "rpt_test_a1",
        "report_name": "A1 test report",
        "code_snapshot_id": "snap_test",
        "code_snapshot_name": "test snapshot",
        "ai_mode": "rule_based",
        "summary": {"total_req_points": 3, "implemented": 1, "missing": 1, "extra": 0, "uncertain": 0, "risk": 1},
        "findings": [
            {
                "finding_id": "f_linked_ok",
                "type": "missing",
                "requirement": "需求A",
                "tapd_bug_id": "12345",
                "tapd_url": "https://www.tapd.cn/test",
                "tapd_pushed_at": "2026-01-01T00:00:00",
            },
            {
                "finding_id": "f_no_link",
                "type": "missing",
                "requirement": "需求B",
            },
            {
                "finding_id": "f_linked_fail",
                "type": "risk",
                "requirement": "需求C",
                "tapd_bug_id": "99999",
                "tapd_url": "https://www.tapd.cn/notfound",
                "tapd_pushed_at": "2026-01-01T00:00:00",
            },
        ],
        "created_at": "2026-01-01T00:00:00",
    }
    _reports[test_report["report_id"]] = test_report
    return app, test_report, _reports


def check_functional_sync():
    """执行实际接口调用：TestClient + mock"""
    try:
        from fastapi.testclient import TestClient
    except ImportError as e:
        rec("#3-7 functional sync test", "SKIP", f"fastapi.testclient missing: {e}")
        return

    app, test_report, _reports = _build_test_app()
    client = TestClient(app)

    # ── #3: 未关联 TAPD 的 Finding 返回 TAPD_BUG_NOT_LINKED ──
    r = client.post("/api/v2/code-compare/findings/f_no_link/sync-tapd-status")
    if r.status_code == 200 and not r.json().get("success") and r.json().get("code") == "TAPD_BUG_NOT_LINKED":
        rec("#3 unlinked finding returns TAPD_BUG_NOT_LINKED", "PASS")
    else:
        rec("#3 unlinked finding returns TAPD_BUG_NOT_LINKED", "FAIL", f"status={r.status_code} body={r.text[:160]}")

    # ── #4: 已关联 Finding 可以更新 tapd_status ──
    r = client.post("/api/v2/code-compare/findings/f_linked_ok/sync-tapd-status")
    body = r.json() if r.status_code == 200 else {}
    if body.get("success") and body.get("data", {}).get("tapd_status") == "in_progress":
        rec("#4 linked finding can update tapd_status", "PASS")
    else:
        rec("#4 linked finding can update tapd_status", "FAIL", f"body={body}")

    # ── #7: 同步后 tapd_last_sync_at 更新 ──
    finding_now = next((f for f in _reports["rpt_test_a1"]["findings"] if f["finding_id"] == "f_linked_ok"), None)
    if finding_now and finding_now.get("tapd_last_sync_at"):
        rec("#7 tapd_last_sync_at updated after sync", "PASS")
    else:
        rec("#7 tapd_last_sync_at updated after sync", "FAIL", "no last_sync_at")

    # ── #6: TAPD API 失败时不破坏 Finding 数据 ──
    finding_fail = next((f for f in _reports["rpt_test_a1"]["findings"] if f["finding_id"] == "f_linked_fail"), None)
    before_status = finding_fail.get("tapd_status") if finding_fail else None
    r = client.post("/api/v2/code-compare/findings/f_linked_fail/sync-tapd-status")
    after_status = finding_fail.get("tapd_status") if finding_fail else None
    body = r.json() if r.status_code == 200 else {}
    # 失败时不应写入 tapd_status
    if (not body.get("success")) and before_status == after_status:
        rec("#6 TAPD failure does not corrupt finding", "PASS")
    else:
        rec("#6 TAPD failure does not corrupt finding", "FAIL",
            f"before={before_status} after={after_status} body={body}")

    # ── #5: report 级批量同步可以跳过未关联 Finding ──
    r = client.post("/api/v2/code-compare/reports/rpt_test_a1/sync-tapd-status")
    body = r.json() if r.status_code == 200 else {}
    if body.get("success"):
        d = body.get("data", {})
        # total=3, synced>=1 (linked_ok), skipped>=1 (no_link), failed>=1 (linked_fail)
        if d.get("total") == 3 and d.get("skipped") >= 1 and d.get("synced") >= 1 and d.get("failed") >= 1:
            rec("#5 report-level sync skips unlinked findings", "PASS")
        else:
            rec("#5 report-level sync skips unlinked findings", "FAIL", f"data={d}")
    else:
        rec("#5 report-level sync skips unlinked findings", "FAIL", f"body={body}")


def check_no_credential_in_logs_runtime():
    """运行时检查：日志输出不应含 password / TEST_PWD"""
    try:
        from fastapi.testclient import TestClient
    except ImportError:
        rec("#12 runtime log no credential", "SKIP", "fastapi.testclient missing")
        return

    app, _, _ = _build_test_app()
    client = TestClient(app)

    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    handler.setLevel(logging.DEBUG)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    try:
        client.post("/api/v2/code-compare/findings/f_linked_ok/sync-tapd-status")
        client.post("/api/v2/code-compare/findings/f_linked_fail/sync-tapd-status")
        log_output = buf.getvalue()
        bad = ("TEST_PWD" in log_output) or ("api_password" in log_output and "=" in log_output)
        if not bad:
            rec("#12 runtime log no credential leak", "PASS")
        else:
            rec("#12 runtime log no credential leak", "FAIL", "credential keyword in log")
    finally:
        root_logger.removeHandler(handler)


# ══════════════════════════════════════════════════════════════════
# 主入口
# ══════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("A1 - TAPD Status Sync Verification")
    print("=" * 60)

    checks = [
        check_route_endpoints_present,
        check_api_js_functions,
        check_codecompare_jsx_renders_tapd_status,
        check_no_credential_logged,
        check_functional_sync,
        check_no_credential_in_logs_runtime,
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
    print("\n[PASS] A1 TAPD status sync verification PASSED")
    sys.exit(0)


if __name__ == "__main__":
    main()
