"""Phase 10A 验收脚本（综合）

覆盖：
  T1  trace_id middleware：请求/响应/异常链路
  T2  全局异常处理：未知异常 → INTERNAL_ERROR + 不泄露内部
  T3  sanitize.py：路径/SQL/Traceback/敏感字段脱敏
  T4  危险操作 confirm_text：缺失/错误/正确三态
  T5  裸 except 清零（grep 校验）
  T6  silent except 已补日志（analytics/code_compare/test_selection）
  T7  启动入口：corrupted.bak 已迁移、业务无引用
  T8  日志记录含 trace_id

不依赖网络服务器，直接用 FastAPI TestClient。
"""
from __future__ import annotations
import json
import logging
import os
import re
import subprocess
import sys
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# T4 用：模块级 BaseModel，避免 pydantic v2 ForwardRef 解析错误
from backend.danger_guard import ConfirmRequest as _ConfirmRequest


class _DangerBody(_ConfirmRequest):
    pass


def _h(title: str):
    print("\n" + "=" * 64)
    print(f"  {title}")
    print("=" * 64)


def _ok(name: str):
    print(f"  [PASS] {name}")


def _fail(name: str, detail: str = ""):
    print(f"  [FAIL] {name}  {detail}")


# ────────────────────── T1+T2+T8: middleware + handler + log ──────────────────────
def t1_t2_t8_middleware():
    _h("T1+T2+T8 trace_id middleware + 全局异常处理 + 日志含 trace_id")
    from fastapi import FastAPI, HTTPException
    from fastapi.testclient import TestClient
    from backend.trace_middleware import TraceIdMiddleware, TRACE_HEADER, current_trace_id
    from backend.exception_handlers import register_exception_handlers
    from backend.logging_config import setup_logging

    setup_logging("DEBUG")
    app = FastAPI()
    app.add_middleware(TraceIdMiddleware)
    register_exception_handlers(app)

    @app.get("/ok")
    def _ok_route():
        return {"trace_id": current_trace_id(), "ok": True}

    @app.get("/biz-fail")
    def _biz_fail():
        raise HTTPException(status_code=400, detail="参数无效")

    @app.get("/leak")
    def _leak():
        raise RuntimeError(
            "DB error at C:\\Users\\admin\\app\\db.sqlite "
            "SELECT * FROM users WHERE token=Bearer abc12345 "
            "password=secret123"
        )

    client = TestClient(app, raise_server_exceptions=False)
    score = 0

    # 1) ok 路由 → 响应头有 X-Trace-Id
    r = client.get("/ok")
    assert r.status_code == 200, r.text
    tid = r.headers.get(TRACE_HEADER)
    if tid and len(tid) >= 8:
        _ok("响应头含 X-Trace-Id")
        score += 1
    else:
        _fail("响应头缺 X-Trace-Id", str(r.headers))

    # 2) 客户端透传 X-Trace-Id
    r = client.get("/ok", headers={TRACE_HEADER: "test-tid-001"})
    if r.headers.get(TRACE_HEADER) == "test-tid-001":
        _ok("客户端透传 X-Trace-Id 生效")
        score += 1
    else:
        _fail("客户端透传 X-Trace-Id 失败", r.headers.get(TRACE_HEADER, ""))

    # 3) 业务异常含 trace_id
    r = client.get("/biz-fail")
    body = r.json()
    if r.status_code == 400 and "trace_id" in body and body.get("detail") == "参数无效":
        _ok("HTTPException 响应含 trace_id 且 detail 透传")
        score += 1
    else:
        _fail("业务异常结构错误", json.dumps(body, ensure_ascii=False))

    # 4) 未知异常 → INTERNAL_ERROR 标准结构
    r = client.get("/leak")
    body = r.json()
    if (r.status_code == 500
            and body.get("code") == "INTERNAL_ERROR"
            and "trace_id" in body
            and "message" in body):
        _ok("未知异常返回 INTERNAL_ERROR 标准结构")
        score += 1
    else:
        _fail("未知异常结构不符", json.dumps(body, ensure_ascii=False))

    # 5) 未知异常响应 不得 含 内部细节
    text = json.dumps(body, ensure_ascii=False)
    leak_keywords = ["Traceback", "SELECT", "sqlite", "C:\\Users", "/Users/", "/home/",
                     "Bearer abc", "secret123", "RuntimeError"]
    leaks = [kw for kw in leak_keywords if kw.lower() in text.lower()]
    if not leaks:
        _ok("未知异常响应不含敏感/内部信息")
        score += 1
    else:
        _fail(f"响应泄露关键字 {leaks}", text[:200])

    return score, 5


# ────────────────────── T3 sanitize 函数级 ──────────────────────
def t3_sanitize():
    _h("T3 sanitize 函数级测试")
    from services.sanitize import (
        sanitize_path, sanitize_exception_message, sanitize_value,
        sanitize_text, sanitize_headers, sanitize_url,
    )
    score = 0; total = 0

    cases = [
        ("Win 路径", lambda: sanitize_path("打开 C:\\Users\\admin\\secret\\db.sqlite 时失败"),
         lambda r: "C:\\Users" not in r and "<path:db.sqlite>" in r),
        ("Linux 路径", lambda: sanitize_path("read /home/user/.ssh/id_rsa fail"),
         lambda r: "/home/user" not in r and "<path:" in r),
        ("Traceback", lambda: sanitize_exception_message(
            'Traceback (most recent call last):\n  File "x.py", line 1\nNameError: x\n'),
         lambda r: "Traceback" not in r and "<traceback redacted>" in r),
        ("SQL", lambda: sanitize_exception_message("DB error: SELECT id FROM users WHERE x=1 LIMIT 5"),
         lambda r: "SELECT" not in r and "<sql redacted>" in r),
        ("Bearer", lambda: sanitize_text("Authorization: Bearer abc123def456"),
         lambda r: "abc123def456" not in r),
        ("URL token", lambda: sanitize_url("https://api.x.com/?token=secret123&id=1"),
         lambda r: "secret123" not in r and "[REDACTED]" in r),
        ("Headers", lambda: sanitize_headers({"Cookie": "x", "Content-Type": "json"}),
         lambda r: r["Cookie"] == "[REDACTED]" and r["Content-Type"] == "json"),
        ("Dict 递归", lambda: sanitize_value({"name": "u", "password": "secretXY"}),
         lambda r: r["password"] != "secretXY" and r["name"] == "u"),
    ]
    for name, fn, check in cases:
        total += 1
        try:
            r = fn()
            if check(r):
                _ok(f"{name}  → {r if not isinstance(r, dict) else r}")
                score += 1
            else:
                _fail(f"{name} 校验失败", str(r))
        except Exception as e:
            _fail(f"{name} 异常", str(e))
    return score, total


# ────────────────────── T4 confirm_text 守卫 ──────────────────────
def t4_confirm():
    _h("T4 危险操作 confirm_text 守卫")
    from typing import Optional
    from fastapi import FastAPI, Body
    from fastapi.testclient import TestClient
    from backend.trace_middleware import TraceIdMiddleware
    from backend.exception_handlers import register_exception_handlers
    from backend.danger_guard import check_confirm, CONFIRM_ERROR_CODE

    app = FastAPI()
    app.add_middleware(TraceIdMiddleware)
    register_exception_handlers(app)

    @app.post("/danger")
    def _danger(body: _DangerBody):
        check_confirm("DANGER_OP", body.confirm, body.confirm_text)
        return {"ok": True}

    client = TestClient(app, raise_server_exceptions=False)
    score = 0

    # 1) 缺少 confirm（提供空 body，使用默认 confirm=False）
    r = client.post("/danger", json={"confirm": False, "confirm_text": ""})
    body = r.json()
    if r.status_code == 400 and body.get("detail", {}).get("code") == CONFIRM_ERROR_CODE:
        _ok("缺少 confirm 返回 400 + DANGEROUS_OPERATION_CONFIRM_REQUIRED")
        score += 1
    else:
        _fail("缺 confirm 校验异常", json.dumps(body, ensure_ascii=False))

    # 2) confirm_text 错误
    r = client.post("/danger", json={"confirm": True, "confirm_text": "WRONG"})
    body = r.json()
    if r.status_code == 400 and body.get("detail", {}).get("code") == CONFIRM_ERROR_CODE:
        _ok("confirm_text 错误返回 400")
        score += 1
    else:
        _fail("错 confirm_text 校验异常", json.dumps(body, ensure_ascii=False))

    # 3) confirm_text 正确
    r = client.post("/danger", json={"confirm": True, "confirm_text": "DANGER_OP"})
    if r.status_code == 200 and r.json().get("ok"):
        _ok("confirm_text 正确进入业务逻辑")
        score += 1
    else:
        _fail("正确 confirm 失败", r.text)

    # 4) detail 含 required_confirm_text 提示
    r = client.post("/danger", json={})
    body = r.json()
    detail = body.get("detail", {}) if isinstance(body.get("detail"), dict) else {}
    if detail.get("required_confirm_text") == "DANGER_OP":
        _ok("错误响应含 required_confirm_text 提示")
        score += 1
    else:
        _fail("缺 required_confirm_text", json.dumps(body, ensure_ascii=False))

    return score, 4


# ────────────────────── T5/T6/T7 静态扫描 ──────────────────────
def _grep_count(pattern: str, paths) -> int:
    count = 0
    for d in paths:
        for p, _, fs in os.walk(ROOT / d):
            if "__pycache__" in p:
                continue
            for f in fs:
                if not f.endswith(".py"):
                    continue
                full = os.path.join(p, f)
                try:
                    src = open(full, "rb").read().decode("utf-8", errors="ignore")
                except Exception:
                    continue
                count += len(re.findall(pattern, src, re.MULTILINE))
    return count


def t5_naked_except():
    _h("T5 裸 except 清零")
    n = _grep_count(r"^\s*except\s*:\s*$", ["routes", "services", "app", "backend"])
    if n == 0:
        _ok("业务目录裸 except = 0")
        return 1, 1
    _fail(f"仍有裸 except: {n} 处")
    return 0, 1


def t6_silent_except_logged():
    _h("T6 静默异常清零（业务热点）")
    n = 0
    for f in ["services/analytics_service.py",
              "services/code_compare_storage_service.py",
              "services/test_selection_service.py"]:
        src = (ROOT / f).read_bytes().decode("utf-8")
        n += len(re.findall(r"except Exception:\s*\n\s*pass", src))
    if n == 0:
        _ok("analytics/code_compare/test_selection 静默 except = 0")
        return 1, 1
    _fail(f"仍有 silent except: {n}")
    return 0, 1


def t7_corrupted_bak():
    _h("T7 启动入口清理")
    score = 0; total = 2
    # 1) 业务目录无 corrupted.bak
    bad = []
    for d in ["routes", "services", "app", "backend"]:
        for p, _, fs in os.walk(ROOT / d):
            for f in fs:
                if "corrupted" in f.lower():
                    bad.append(os.path.join(p, f))
    if not bad:
        _ok("业务目录无 corrupted 残留")
        score += 1
    else:
        _fail(f"残留 corrupted: {bad}")

    # 2) archive 中有归档
    archived = ROOT / "archive" / "legacy_backup"
    if archived.exists() and any(f for f in archived.iterdir() if "corrupted" in f.name):
        _ok("archive/legacy_backup 中有归档备份")
        score += 1
    else:
        _fail("archive 中无归档备份")
    return score, total


# ────────────────────── T8 logging trace_id 注入 ──────────────────────
def t8_log_has_trace():
    _h("T8 日志格式包含 trace_id")
    from backend.logging_config import setup_logging
    from backend.trace_middleware import set_trace_id, reset_trace_id

    buf = StringIO()
    setup_logging("DEBUG")
    root = logging.getLogger()
    sh = logging.StreamHandler(buf)
    fmt = next((h.formatter for h in root.handlers if getattr(h, "_sanitized", False)), None)
    if fmt is None:
        _fail("未找到 sanitized handler")
        return 0, 1
    sh.setFormatter(fmt)
    # 复用 trace filter
    from backend.logging_config import TraceIdFilter
    sh.addFilter(TraceIdFilter())
    root.addHandler(sh)

    token = set_trace_id("trace-xyz-7777")
    try:
        logging.getLogger("p10a.test").info("hello world password=topSecret123")
    finally:
        reset_trace_id(token)
        root.removeHandler(sh)

    out = buf.getvalue()
    has_tid = "trace-xyz-7777" in out
    no_secret = "topSecret123" not in out
    if has_tid and no_secret:
        _ok("日志含 trace_id 且 password 已脱敏")
        return 1, 1
    _fail(f"trace_id={has_tid}, no_secret={no_secret}", out[:300])
    return 0, 1


# ────────────────────── 主入口 ──────────────────────
def main():
    suites = [
        t1_t2_t8_middleware,
        t3_sanitize,
        t4_confirm,
        t5_naked_except,
        t6_silent_except_logged,
        t7_corrupted_bak,
        t8_log_has_trace,
    ]
    total_pass = 0
    total_total = 0
    for s in suites:
        try:
            p, t = s()
        except Exception as e:
            _h(s.__name__)
            _fail("套件异常", str(e))
            p, t = 0, 1
        total_pass += p
        total_total += t

    print("\n" + "=" * 64)
    print(f"  Phase 10A 验收: {total_pass} / {total_total} ")
    print("=" * 64)
    return 0 if total_pass == total_total else 1


if __name__ == "__main__":
    sys.exit(main())
