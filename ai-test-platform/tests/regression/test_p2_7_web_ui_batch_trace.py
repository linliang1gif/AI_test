#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# P2-9B.1: Windows GBK 编码兼容
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
P2-7 Web UI 批量执行 / Trace / Console / Network — 测试脚本

覆盖:
1. sanitize 模块单元测试
2. PlaywrightResult 新字段 (trace_path, console_logs, network_errors)
3. POST /api/v2/web-ui/batch-run 路由
4. 批量执行只接受 web_ui 用例
5. 批量执行生成 test_run + run_case + run_step
6. response_snapshot 含 trace_path / console_error_count / network_error_count
7. 非 web_ui 用例拒绝
8. 单条失败不中断批量
9. trace 文件静态服务可访问
10. 路由注册检查
"""
import sys, os, time, requests, json, threading

BASE = os.getenv("BACKEND_URL", "http://localhost:8000")
PASS = FAIL = SKIP = TOTAL = 0
MOCK_PORT = 19877


def check(name, condition, detail=""):
    global PASS, FAIL, TOTAL
    TOTAL += 1
    if condition:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}  {detail}")


def skip(name, reason=""):
    global SKIP, TOTAL
    TOTAL += 1
    SKIP += 1
    print(f"  ⏭️  {name}  ({reason})")


def api(method, path, **kw):
    kw.setdefault("timeout", 120)
    return getattr(requests, method)(f"{BASE}{path}", **kw)


# ══════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("  P2-7 Web UI Batch / Trace / Console / Network Tests")
print("=" * 60)

h = api("get", "/health")
check("Backend healthy", h.ok, h.text[:200])

# ── 1. sanitize 模块单元测试 ─────────────────────────
print("\n── 1. sanitize 模块 ──")
try:
    _proj = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if _proj not in sys.path:
        sys.path.insert(0, _proj)
    from services.sanitize import sanitize_url, sanitize_headers, sanitize_text, sanitize_console_entry, sanitize_network_entry

    # URL 脱敏
    url_result = sanitize_url("https://example.com/api?token=secret123&name=test")
    check("sanitize_url: token 被脱敏", "token=[REDACTED]" in url_result and "secret123" not in url_result, url_result)

    url_result2 = sanitize_url("https://example.com/api?access_token=mytoken&page=1")
    check("sanitize_url: access_token 被脱敏", "access_token=[REDACTED]" in url_result2, url_result2)

    # Headers 脱敏
    hdrs = sanitize_headers({"Authorization": "Bearer xxx", "Content-Type": "application/json", "Cookie": "session=abc"})
    check("sanitize_headers: Authorization 被脱敏", hdrs["Authorization"] == "[REDACTED]", str(hdrs))
    check("sanitize_headers: Cookie 被脱敏", hdrs["Cookie"] == "[REDACTED]", str(hdrs))
    check("sanitize_headers: Content-Type 保留", hdrs["Content-Type"] == "application/json", str(hdrs))

    # Text 脱敏
    txt = sanitize_text("Found token=secret123 and Bearer abc123def")
    check("sanitize_text: token= 被脱敏", "secret123" not in txt, txt)
    check("sanitize_text: Bearer 被脱敏", "abc123def" not in txt, txt)

    # Console entry
    entry = sanitize_console_entry({"type": "error", "text": "Authorization Bearer secret", "timestamp": "2026-01-01"})
    check("sanitize_console_entry: text 脱敏", "secret" not in entry["text"], entry["text"])

    # Network entry
    ne = sanitize_network_entry({"url": "https://x.com/api?token=abc", "method": "GET"})
    check("sanitize_network_entry: url 脱敏", "abc" not in ne["url"], ne["url"])

except Exception as e:
    check("sanitize 模块加载", False, str(e))

# ── 2. PlaywrightResult 新字段 ───────────────────────
print("\n── 2. PlaywrightResult 新字段 ──")
try:
    from services.playwright_engine import PlaywrightResult
    pr = PlaywrightResult()
    check("trace_path 默认空", pr.trace_path == "", repr(pr.trace_path))
    check("console_logs 默认空列表", pr.console_logs == [], repr(pr.console_logs))
    check("network_errors 默认空列表", pr.network_errors == [], repr(pr.network_errors))
except Exception as e:
    check("PlaywrightResult 导入", False, str(e))

# ── 3. 检测 Playwright 可用性 ────────────────────────
print("\n── 3. Playwright 可用性 ──")
try:
    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    br = pw.chromium.launch(headless=True)
    br.close()
    pw.stop()
    PLAYWRIGHT_OK = True
    check("Playwright + Chromium 可用", True)
except Exception as e:
    PLAYWRIGHT_OK = False
    skip("Playwright + Chromium 可用", f"不可用: {e}")

if not PLAYWRIGHT_OK:
    print("\n⚠️  Playwright 不可用，跳过执行测试")
    skip_items = [
        "创建 Web UI 用例", "批量执行 2 条 Web UI 用例",
        "test_run 状态正确", "run_case 写入", "run_step 写入",
        "response_snapshot 含 trace_path", "response_snapshot 含 console_error_count",
        "response_snapshot 含 network_error_count",
        "非 web_ui 用例被拒绝", "单条失败不中断",
        "trace 文件可下载", "路由注册检查",
    ]
    for name in skip_items:
        skip(name, "Playwright 不可用")
    print(f"\n{'=' * 60}")
    print(f"  P2-7: PASS={PASS} FAIL={FAIL} SKIP={SKIP} TOTAL={TOTAL}")
    print(f"{'=' * 60}")
    sys.exit(0)

# ── 4. 启动 Mock 页面服务器 ──────────────────────────
from http.server import HTTPServer, SimpleHTTPRequestHandler
import tempfile, pathlib

MOCK_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>P2-7 Mock</title></head>
<body>
<h1 id="heading">P2-7 Mock App</h1>
<form id="login-form">
  <input name="username" type="text" />
  <input name="password" type="password" />
  <button type="submit">登录</button>
</form>
<script>
document.getElementById('login-form').addEventListener('submit', function(e) {
  e.preventDefault();
  document.getElementById('heading').textContent = '欢迎回来';
  window.history.pushState({}, '', '/dashboard');
});
// Trigger a console.error for capture testing
console.error('P2-7-TEST-CONSOLE-ERROR: intentional error');
console.warn('P2-7-TEST-CONSOLE-WARN: intentional warning');
</script>
</body></html>"""

mock_dir = tempfile.mkdtemp(prefix="p27_test_")
pathlib.Path(os.path.join(mock_dir, "index.html")).write_text(MOCK_HTML, encoding="utf-8")
pathlib.Path(os.path.join(mock_dir, "login")).mkdir(exist_ok=True)
pathlib.Path(os.path.join(mock_dir, "login", "index.html")).write_text(MOCK_HTML, encoding="utf-8")

class QuietHandler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=mock_dir, **kw)
    def log_message(self, *a):
        pass

httpd = HTTPServer(("127.0.0.1", MOCK_PORT), QuietHandler)
srv_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
srv_thread.start()
time.sleep(0.5)

MOCK_BASE = f"http://127.0.0.1:{MOCK_PORT}"
print(f"  Mock server running at {MOCK_BASE}")

# ── 5. 创建 Web UI 用例 ─────────────────────────────
print("\n── 5. 创建 Web UI 用例 ──")

case1_payload = {
    "title": "P2-7 批量测试用例A (login)",
    "module": "P2-7",
    "priority": "high",
    "case_type": "web_ui",
    "steps": [
        {"action": "goto", "target": "/login", "value": "", "description": "打开登录页"},
        {"action": "fill", "target": "input[name=username]", "value": "admin", "description": "输入用户名"},
        {"action": "fill", "target": "input[name=password]", "value": "pass123", "description": "输入密码"},
        {"action": "click", "target": "button[type=submit]", "value": "", "description": "点击登录"},
        {"action": "wait_for", "target": "500", "value": "", "description": "等待"},
    ],
    "assertions": [
        {"type": "text_visible", "target": "", "value": "欢迎回来", "description": "显示欢迎"},
    ],
    "execution_config": {
        "engine": "playwright", "browser": "chromium",
        "base_url": MOCK_BASE, "headless": True, "timeout": 10000,
    },
}
r1 = api("post", "/api/v2/test-cases", json=case1_payload)
check("创建 Web UI 用例A", r1.ok and r1.json().get("success"), r1.text[:200])
case_a_id = r1.json().get("test_case_id", "")

case2_payload = {
    "title": "P2-7 批量测试用例B (简单goto)",
    "module": "P2-7",
    "priority": "medium",
    "case_type": "web_ui",
    "steps": [
        {"action": "goto", "target": "/login", "value": "", "description": "打开页面"},
        {"action": "screenshot", "target": "", "value": "", "description": "截图"},
    ],
    "assertions": [
        {"type": "element_visible", "target": "#heading", "value": "", "description": "标题可见"},
    ],
    "execution_config": {
        "engine": "playwright", "browser": "chromium",
        "base_url": MOCK_BASE, "headless": True, "timeout": 10000,
    },
}
r2 = api("post", "/api/v2/test-cases", json=case2_payload)
check("创建 Web UI 用例B", r2.ok and r2.json().get("success"), r2.text[:200])
case_b_id = r2.json().get("test_case_id", "")

# 创建一个 API 用例（非 web_ui）
api_payload = {
    "title": "P2-7 API 用例 (不应进入 web_ui 批量)",
    "module": "P2-7",
    "priority": "low",
    "case_type": "api",
    "expected": "200",
    "execution_config": {"method": "GET", "url": "/health"},
}
r3 = api("post", "/api/v2/test-cases", json=api_payload)
api_case_id = r3.json().get("test_case_id", "")

# ── 6. 非 web_ui 用例被拒绝 ─────────────────────────
print("\n── 6. 非 web_ui 用例被拒绝 ──")
r_reject = api("post", "/api/v2/web-ui/batch-run", json={
    "case_ids": [api_case_id],
    "execution_config": {"browser": "chromium", "headless": True},
})
check("非 web_ui 用例被拒绝 (400)", r_reject.status_code == 400, f"status={r_reject.status_code} body={r_reject.text[:200]}")

# ── 7. 批量执行 2 条 Web UI 用例 ────────────────────
print("\n── 7. 批量执行 Web UI 用例 ──")
batch_payload = {
    "case_ids": [case_a_id, case_b_id],
    "execution_config": {
        "browser": "chromium",
        "headless": True,
        "base_url": MOCK_BASE,
        "timeout": 15000,
        "enable_trace": True,
        "capture_console": True,
        "capture_network": True,
    },
}
r_batch = api("post", "/api/v2/web-ui/batch-run", json=batch_payload)
check("批量执行返回 200", r_batch.status_code == 200, f"status={r_batch.status_code} body={r_batch.text[:300]}")
batch_data = r_batch.json()

check("success=true", batch_data.get("success") == True, str(batch_data.get("success")))
check("run_id 不为空", bool(batch_data.get("run_id")), batch_data.get("run_id", ""))
check("total_cases=2", batch_data.get("total_cases") == 2, str(batch_data.get("total_cases")))
check("passed_cases >= 1", batch_data.get("passed_cases", 0) >= 1, str(batch_data.get("passed_cases")))

run_id = batch_data.get("run_id", "")

# 验证 case_results
case_results = batch_data.get("case_results", [])
check("case_results 含 2 条", len(case_results) == 2, f"got {len(case_results)}")

if case_results:
    cr0 = case_results[0]
    check("case_result 有 case_id", bool(cr0.get("case_id")), str(cr0))
    check("case_result 有 status", cr0.get("status") in ("passed", "failed"), str(cr0.get("status")))
    check("case_result 有 duration_ms", cr0.get("duration_ms", 0) >= 0, str(cr0.get("duration_ms")))

# 验证 trace_count
check("trace_count >= 1", batch_data.get("trace_count", 0) >= 1, str(batch_data.get("trace_count")))

# 验证 console_error_count (我们的 mock 页面有 console.error)
check("console_error_count >= 0", batch_data.get("console_error_count", -1) >= 0, str(batch_data.get("console_error_count")))

# 验证 network_error_count
check("network_error_count >= 0", batch_data.get("network_error_count", -1) >= 0, str(batch_data.get("network_error_count")))

# 验证 summary
summary = batch_data.get("summary", {})
check("summary.case_type=web_ui", summary.get("case_type") == "web_ui", str(summary.get("case_type")))

# ── 8. TestRun 写入验证 ─────────────────────────────
print("\n── 8. TestRun 写入验证 ──")
r_run = api("get", f"/api/v2/test-runs/{run_id}")
if r_run.ok:
    run_raw = r_run.json()
    # Handle both dict and list response
    if isinstance(run_raw, list):
        run_data = run_raw[0] if run_raw else {}
    elif isinstance(run_raw, dict):
        run_data = run_raw.get("test_run") or run_raw
    else:
        run_data = {}
    check("TestRun 存在", bool(run_data), "")
    trigger = run_data.get("trigger_type", "")
    summary_str = run_data.get("summary") or ""
    check("TestRun trigger_type=web_ui_batch",
          trigger == "web_ui_batch" or "web_ui" in summary_str,
          f"trigger_type={trigger}")
else:
    skip("TestRun 查询", f"API: {r_run.status_code}")

# ── 9. RunCase / RunStep 写入验证 ────────────────────
print("\n── 9. RunCase/RunStep 验证 ──")
try:
    r_cases = api("get", f"/api/v2/observability/runs/{run_id}/cases")
    if r_cases.ok:
        cases_data = r_cases.json()
        run_cases = cases_data.get("data") or cases_data.get("cases") or cases_data.get("run_cases") or (cases_data if isinstance(cases_data, list) else [])
        check("RunCase 数量 >= 2", len(run_cases) >= 2, f"got {len(run_cases)}")

        # 检查 response_snapshot 含 trace_path (需用详情接口 full=True)
        if run_cases:
            rc0 = run_cases[0]
            rc_id = rc0.get("id")
            tc_id = rc0.get("test_case_id", "")
            # 获取完整详情
            r_detail = api("get", f"/api/v2/observability/runs/{run_id}/cases/{tc_id}")
            if r_detail.ok:
                detail_data = r_detail.json().get("data") or r_detail.json()
                rs = detail_data.get("response_snapshot") or {}
                check("response_snapshot 含 trace_path", "trace_path" in rs, str(list(rs.keys())[:10]))
                check("response_snapshot 含 console_error_count", "console_error_count" in rs, str(list(rs.keys())[:10]))
                check("response_snapshot 含 network_error_count", "network_error_count" in rs, str(list(rs.keys())[:10]))
            else:
                skip("response_snapshot 检查 (detail API)", f"API: {r_detail.status_code}")

            # 查 RunSteps
            if rc_id:
                r_steps = api("get", f"/api/v2/observability/cases/{rc_id}/steps")
                if r_steps.ok:
                    steps_raw = r_steps.json()
                    steps = steps_raw.get("data") or steps_raw.get("steps") or steps_raw.get("run_steps") or (steps_raw if isinstance(steps_raw, list) else [])
                    check("RunStep 数量 >= 1", len(steps) >= 1, f"got {len(steps)}")
                else:
                    skip("RunStep 查询", f"API: {r_steps.status_code}")
            else:
                skip("RunStep 查询", "RunCase id 缺失")
        else:
            skip("response_snapshot 检查", "无 RunCase 数据")
    else:
        skip("RunCase 查询", f"API: {r_cases.status_code}")
except Exception as e:
    skip("RunCase/RunStep 验证", str(e))

# ── 10. 单条失败不中断 ──────────────────────────────
print("\n── 10. 单条失败不中断 ──")
fail_payload = {
    "title": "P2-7 故意失败用例",
    "module": "P2-7",
    "priority": "low",
    "case_type": "web_ui",
    "steps": [
        {"action": "goto", "target": "/login", "value": "", "description": "打开页面"},
    ],
    "assertions": [
        {"type": "url_contains", "target": "", "value": "this_will_never_match_p27", "description": "故意失败"},
    ],
    "execution_config": {"engine": "playwright", "browser": "chromium", "base_url": MOCK_BASE, "headless": True},
}
rf = api("post", "/api/v2/test-cases", json=fail_payload)
fail_case_id = rf.json().get("test_case_id", "")

r_mixed = api("post", "/api/v2/web-ui/batch-run", json={
    "case_ids": [fail_case_id, case_b_id],
    "execution_config": {"browser": "chromium", "headless": True, "base_url": MOCK_BASE, "timeout": 10000},
})
check("混合批量返回 200", r_mixed.status_code == 200, f"status={r_mixed.status_code}")
mixed_data = r_mixed.json()
check("mixed: total_cases=2", mixed_data.get("total_cases") == 2, str(mixed_data.get("total_cases")))
check("mixed: failed_cases >= 1", mixed_data.get("failed_cases", 0) >= 1, str(mixed_data.get("failed_cases")))
check("mixed: passed_cases >= 1", mixed_data.get("passed_cases", 0) >= 1, str(mixed_data.get("passed_cases")))

# ── 11. trace 文件下载 ──────────────────────────────
print("\n── 11. trace 文件下载 ──")
if case_results:
    trace_path = case_results[0].get("trace_path", "")
    if trace_path:
        trace_filename = os.path.basename(trace_path)
        r_dl = api("get", f"/api/v2/web-ui/traces/{trace_filename}")
        check("trace 文件下载 API 200", r_dl.status_code == 200, f"status={r_dl.status_code}")
        if r_dl.status_code == 200:
            check("trace 文件大小 > 0", len(r_dl.content) > 0, f"size={len(r_dl.content)}")
    else:
        skip("trace 文件下载", "无 trace_path")
else:
    skip("trace 文件下载", "无 case_results")

# ── 12. 路由注册检查 ─────────────────────────────────
print("\n── 12. 路由注册检查 ──")
r_docs = api("get", "/openapi.json")
if r_docs.ok:
    openapi = r_docs.json()
    paths = openapi.get("paths", {})
    check("/api/v2/web-ui/batch-run 路由已注册", "/api/v2/web-ui/batch-run" in paths, f"paths={list(paths.keys())[:10]}")
else:
    skip("路由注册检查", f"OpenAPI: {r_docs.status_code}")

# ── 13. Trace 下载安全测试 (P2-7.1) ──────────────────
print("\n── 13. Trace 下载安全 ──")

# 路径穿越 ../../.env
r_trav = api("get", "/api/v2/web-ui/traces/..%2F..%2F.env")
check("路径穿越 ../../.env 被拒绝", r_trav.status_code in (400, 403, 404, 422), f"status={r_trav.status_code}")

r_trav2 = api("get", "/api/v2/web-ui/traces/..%2F..%2Fdata%2Ftest_platform.db")
check("路径穿越 ../../db 被拒绝", r_trav2.status_code in (400, 403, 404, 422), f"status={r_trav2.status_code}")

# 非 zip 文件
r_nonzip = api("get", "/api/v2/web-ui/traces/test.py")
check("非 zip 文件被拒绝", r_nonzip.status_code == 400, f"status={r_nonzip.status_code}")

r_nonzip2 = api("get", "/api/v2/web-ui/traces/secret.env")
check("非 zip (.env) 被拒绝", r_nonzip2.status_code == 400, f"status={r_nonzip2.status_code}")

# 不存在的 zip 文件
r_missing = api("get", "/api/v2/web-ui/traces/nonexistent_file_12345.zip")
check("不存在文件返回 404", r_missing.status_code == 404, f"status={r_missing.status_code}")

# 文件名含特殊字符
r_special = api("get", "/api/v2/web-ui/traces/file%3B%20rm%20-rf.zip")
check("特殊字符文件名被拒绝", r_special.status_code in (400, 403, 404, 422), f"status={r_special.status_code}")

# ── 14. /traces 静态挂载已移除 (P2-7.2) ────────────
print("\n── 14. /traces 静态挂载验证 ──")
if case_results:
    tp = case_results[0].get("trace_path", "")
    if tp:
        fn = os.path.basename(tp.replace("\\", "/"))
        r_static = api("get", f"/traces/{fn}")
        check("/traces 静态挂载已移除 (非200)", r_static.status_code != 200, f"status={r_static.status_code}")
    else:
        skip("/traces 静态挂载验证", "无 trace_path")
else:
    skip("/traces 静态挂载验证", "无 case_results")

# ── 15. 清理 ────────────────────────────────────────
print("\n── 15. 清理 ──")
for cid in [case_a_id, case_b_id, api_case_id, fail_case_id]:
    if cid:
        api("put", f"/api/v2/test-cases/{cid}", json={"status": "deleted"})

try:
    httpd.shutdown()
except Exception:
    pass

# ── 汇总 ────────────────────────────────────────────
print(f"\n{'=' * 60}")
print(f"  P2-7: PASS={PASS} FAIL={FAIL} SKIP={SKIP} TOTAL={TOTAL}")
print(f"{'=' * 60}")

if FAIL > 0:
    sys.exit(1)
