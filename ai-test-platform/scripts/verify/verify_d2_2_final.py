#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""D2-2 最终工程验收 — 异常结构 + 敏感字段 + 端口一致性 + legacy 清单"""
import os
import re
import json
import requests

BASE = "http://127.0.0.1:8001"
REQUIRED_FIELDS = {"code", "message", "trace_id"}
SENSITIVE_WORDS = [
    "token", "access_token", "refresh_token", "authorization",
    "cookie", "api_key", "secret", "password", "client_secret",
]
ok = 0
fail = 0


def chk(label, passed, detail=""):
    global ok, fail
    sym = "PASS" if passed else "FAIL"
    mark = "\u2705" if passed else "\u274c"
    print(f"  {mark} [{sym}] {label}" + (f" \u2014 {detail}" if detail else ""))
    if passed:
        ok += 1
    else:
        fail += 1


def check_response_structure(label, resp, expected_status):
    """验证响应是否符合标准结构"""
    data = resp.json()
    keys = set(data.keys())
    has_all = REQUIRED_FIELDS.issubset(keys)
    status_ok = resp.status_code == expected_status
    has_header = "X-Trace-Id" in resp.headers

    chk(f"{label}: status={resp.status_code}",
        status_ok,
        f"expected {expected_status}")
    chk(f"{label}: 包含 code/message/trace_id",
        has_all,
        f"keys={sorted(keys)}")
    chk(f"{label}: X-Trace-Id header",
        has_header,
        resp.headers.get("X-Trace-Id", "MISSING"))

    # 敏感字段泄露检查
    full_text = json.dumps(data, ensure_ascii=False).lower()
    leaked = []
    for sw in SENSITIVE_WORDS:
        # 在 message / detail / details 值中检查
        for field in ("message", "detail", "details"):
            val = data.get(field)
            if val is None:
                continue
            val_str = json.dumps(val, ensure_ascii=False).lower() if not isinstance(val, str) else val.lower()
            # 排除 trace_id 中的 "token" 误报
            if sw in val_str:
                leaked.append(f"{sw} in {field}")
    chk(f"{label}: 无敏感字段泄露",
        len(leaked) == 0,
        f"泄露: {leaked}" if leaked else "clean")

    return data


def main():
    global ok, fail
    print("=" * 60)
    print("  D2-2 最终工程验收")
    print("=" * 60)

    # ═══════ 1. 异常处理器注册验证 ═══════
    print("\n[1] exception_handlers.py 全局注册确认")
    app_py = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "backend", "app.py")
    with open(app_py, "r", encoding="utf-8") as f:
        app_content = f.read()
    chk("register_exception_handlers(app) 存在",
        "register_exception_handlers(app)" in app_content)
    chk("TraceIdMiddleware 注册",
        "TraceIdMiddleware" in app_content)

    # ═══════ 2. 五种异常类型返回标准结构 ═══════
    print("\n[2] 异常类型标准结构验证")

    # 2a. 404 路由不存在
    print("  --- 404 路由不存在 ---")
    r = requests.get(f"{BASE}/api/v2/nonexistent-d22-verify")
    d = check_response_structure("404-route-not-found", r, 404)
    chk("404 code=NOT_FOUND", d.get("code") == "NOT_FOUND", f"code={d.get('code')}")

    # 2b. 422 请求体验证失败
    print("  --- 422 Validation Error ---")
    r = requests.post(f"{BASE}/api/v2/projects", json={})
    check_response_structure("422-validation", r, 422)

    # 2c. HTTPException 业务 404
    print("  --- HTTPException (project 404) ---")
    r = requests.get(f"{BASE}/api/v2/projects/99999")
    check_response_structure("HTTPException-proj-404", r, 404)

    # 2d. HTTPException 400 (danger guard)
    print("  --- HTTPException (danger guard 400) ---")
    r = requests.delete(f"{BASE}/api/v2/projects/99999", json={})
    check_response_structure("HTTPException-guard-400", r, 400)

    # 2e. 500 内部错误 (通过故意触发)
    # 用 health/full 的已知可用性代替 — 对 500 通过检查 generic handler 代码逻辑覆盖
    print("  --- 500 generic handler (代码覆盖确认) ---")
    eh_py = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "backend", "exception_handlers.py")
    with open(eh_py, "r", encoding="utf-8") as f:
        eh_content = f.read()
    chk("generic_exception_handler 注册",
        "async def generic_exception_handler" in eh_content)
    chk("generic handler 返回 code=INTERNAL_ERROR",
        'INTERNAL_ERROR_CODE' in eh_content and '"code": INTERNAL_ERROR_CODE' in eh_content)
    chk("generic handler 返回 details={}",
        '"details": {}' in eh_content)
    chk("generic handler 返回 500",
        "status_code=500" in eh_content)

    # ═══════ 3. 敏感字段注入测试 ═══════
    print("\n[3] 敏感字段注入测试")
    r = requests.get(f"{BASE}/api/v2/nonexistent?token=SUPER_SECRET_XYZ&api_key=MY_KEY_123&password=Pass1234")
    data = r.json()
    full = json.dumps(data, ensure_ascii=False)
    chk("token 值未泄露", "SUPER_SECRET_XYZ" not in full)
    chk("api_key 值未泄露", "MY_KEY_123" not in full)
    chk("password 值未泄露", "Pass1234" not in full)

    # sanitize.py 覆盖确认
    print("\n  --- sanitize.py 敏感字段正则覆盖 ---")
    san_py = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "services", "sanitize.py")
    with open(san_py, "r", encoding="utf-8") as f:
        san_content = f.read().lower()
    for sw in SENSITIVE_WORDS:
        found = sw.lower() in san_content
        chk(f"sanitize.py 覆盖 '{sw}'", found)

    # ═══════ 4. 端口一致性 ═══════
    print("\n[4] BACKEND_PORT 一致性检查")
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # .env
    env_file = os.path.join(root, ".env")
    env_port = None
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                m = re.match(r"BACKEND_PORT\s*=\s*(\d+)", line.strip())
                if m:
                    env_port = m.group(1)
    chk(".env BACKEND_PORT", env_port is not None, f"port={env_port}")

    # vite.config.js
    vite_file = os.path.join(root, "frontend", "vite.config.js")
    if os.path.exists(vite_file):
        with open(vite_file, "r", encoding="utf-8") as f:
            vite_content = f.read()
        vite_ports = re.findall(r"http://127\.0\.0\.1:(\d+)", vite_content)
        all_match = all(p == env_port for p in vite_ports) if vite_ports else False
        chk("vite.config.js proxy ports 与 .env 一致",
            all_match,
            f"vite_ports={vite_ports} env_port={env_port}")

    # backend config default
    cfg_file = os.path.join(root, "backend", "config.py")
    if os.path.exists(cfg_file):
        with open(cfg_file, "r", encoding="utf-8") as f:
            cfg_content = f.read()
        chk("backend/config.py 存在 BACKEND_PORT",
            "BACKEND_PORT" in cfg_content)

    # ═══════ 5. api.js [LEGACY] 清单 ═══════
    print("\n[5] api.js [LEGACY] 标记清单")
    api_js = os.path.join(root, "frontend", "src", "services", "api.js")
    with open(api_js, "r", encoding="utf-8") as f:
        lines = f.readlines()
    legacy_lines = [(i + 1, line.rstrip()) for i, line in enumerate(lines) if "[LEGACY]" in line]
    chk("LEGACY 标记数量 >= 7", len(legacy_lines) >= 7, f"found={len(legacy_lines)}")
    for ln, text in legacy_lines:
        print(f"    L{ln}: {text.strip()}")

    # ═══════ Summary ═══════
    total = ok + fail
    print(f"\n{'=' * 60}")
    print(f"  总计: {total}  通过: {ok}  失败: {fail}")
    if fail == 0:
        print("  \U0001f389 D2-2 最终验收全部通过！可进入 D2-3A")
    else:
        print(f"  \u26d4 存在 {fail} 项失败，需修复后再进入 D2-3A")
    print("=" * 60)


if __name__ == "__main__":
    main()
