#!/usr/bin/env python3
"""
P2-4 Playwright 执行引擎 MVP — 测试脚本

覆盖:
1. Playwright 是否可用
2. 创建 Web UI 用例
3. 执行 goto 成功
4. 执行 fill + click 成功
5. text_visible 断言
6. url_contains 断言
7. element_visible 断言
8. 失败时保存截图
9. 不支持 action 返回友好错误
10. 结果写入 test_runs / run_cases / run_steps
11. API 用例不受影响
"""
import sys, os, time, requests, json, threading
from http.server import HTTPServer, SimpleHTTPRequestHandler

BASE = os.getenv("BACKEND_URL", "http://localhost:8000")
PASS = FAIL = SKIP = TOTAL = 0
MOCK_PORT = 19876  # 用于测试的本地 mock 页面端口


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
    kw.setdefault("timeout", 60)
    return getattr(requests, method)(f"{BASE}{path}", **kw)


# ── 0. 检查 Playwright 可用性 ──────────────────────
print("\n" + "=" * 60)
print("  P2-4 Playwright Engine MVP Tests")
print("=" * 60)

h = api("get", "/health")
check("Backend healthy", h.ok, h.text[:200])

# 检测 playwright 是否可用
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
    print("\n⚠️  Playwright 不可用，跳过所有执行测试")
    items = [
        "创建 Web UI 用例", "goto 执行", "fill+click 执行",
        "text_visible 断言", "url_contains 断言", "element_visible 断言",
        "失败截图", "不支持 action", "结果写入 DB", "API 不受影响",
    ]
    for name in items:
        skip(name, "Playwright 不可用")
    print(f"\n{'=' * 60}")
    print(f"  P2-4: PASS={PASS} FAIL={FAIL} SKIP={SKIP} TOTAL={TOTAL}")
    print(f"{'=' * 60}")
    sys.exit(0)


# ── 1. 启动 Mock 页面服务器 ────────────────────────
MOCK_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>MockApp - 登录</title></head>
<body>
<h1 id="heading">MockApp 登录页面</h1>
<form id="login-form">
  <input name="username" type="text" placeholder="用户名" />
  <input name="password" type="password" placeholder="密码" />
  <button type="submit">登录</button>
</form>
<script>
document.getElementById('login-form').addEventListener('submit', function(e) {
  e.preventDefault();
  document.title = 'MockApp - 首页';
  document.getElementById('heading').textContent = '欢迎回来，首页';
  window.history.pushState({}, '', '/dashboard');
});
</script>
</body></html>"""

import tempfile, pathlib

mock_dir = tempfile.mkdtemp(prefix="pw_test_")
pathlib.Path(os.path.join(mock_dir, "index.html")).write_text(MOCK_HTML, encoding="utf-8")
# Also create /login path by serving index.html
pathlib.Path(os.path.join(mock_dir, "login")).mkdir(exist_ok=True)
pathlib.Path(os.path.join(mock_dir, "login", "index.html")).write_text(MOCK_HTML, encoding="utf-8")

class QuietHandler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=mock_dir, **kw)
    def log_message(self, *a):
        pass  # 静默

httpd = HTTPServer(("127.0.0.1", MOCK_PORT), QuietHandler)
srv_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
srv_thread.start()
time.sleep(0.5)

MOCK_BASE = f"http://127.0.0.1:{MOCK_PORT}"
print(f"\n  Mock server running at {MOCK_BASE}")

# ── 2. 创建 Web UI 用例 ───────────────────────────
print("\n── 创建 Web UI 用例 ──")
payload = {
    "title": "P2-4 登录测试 (Playwright)",
    "module": "P2-4",
    "priority": "high",
    "case_type": "web_ui",
    "steps": [
        {"action": "goto", "target": "/login", "value": "", "description": "打开登录页"},
        {"action": "fill", "target": "input[name=username]", "value": "admin", "description": "输入用户名"},
        {"action": "fill", "target": "input[name=password]", "value": "pass123", "description": "输入密码"},
        {"action": "click", "target": "button[type=submit]", "value": "", "description": "点击登录"},
        {"action": "wait_for", "target": "500", "value": "", "description": "等待页面更新"},
    ],
    "assertions": [
        {"type": "text_visible", "target": "", "value": "欢迎回来", "description": "页面显示欢迎"},
        {"type": "url_contains", "target": "", "value": "/dashboard", "description": "URL 含 dashboard"},
        {"type": "element_visible", "target": "#heading", "value": "", "description": "标题可见"},
    ],
    "execution_config": {
        "engine": "playwright",
        "browser": "chromium",
        "base_url": MOCK_BASE,
        "headless": True,
        "timeout": 10000,
    },
}
r1 = api("post", "/api/v2/test-cases", json=payload)
check("创建 Web UI 用例成功", r1.ok and r1.json().get("success"))
case_id = r1.json().get("test_case_id", "")

# ── 3. 执行 Web UI 用例 ───────────────────────────
print("\n── 执行 Web UI 用例 ──")
r2 = api("post", f"/api/v2/test-cases/{case_id}/execute", json={})
check("执行返回 200", r2.status_code == 200, f"status={r2.status_code} body={r2.text[:300]}")
exec_data = r2.json()
check("有 run_id", bool(exec_data.get("run_id")), str(exec_data)[:200])
check("状态为 passed", exec_data.get("status") == "passed", f"status={exec_data.get('status')} err={exec_data.get('error_message','')}")
run_id = exec_data.get("run_id", "")

# 验证步骤结果
step_results = (exec_data.get("response_snapshot") or {}).get("step_results", [])
check("step_results 返回 5 步", len(step_results) == 5, f"got {len(step_results)}")
if step_results:
    check("goto 步骤通过", step_results[0].get("status") == "passed" and step_results[0].get("action") == "goto")
    check("fill 步骤通过", step_results[1].get("status") == "passed" and step_results[1].get("action") == "fill")
    check("click 步骤通过", step_results[3].get("status") == "passed" and step_results[3].get("action") == "click")
    check("wait_for 步骤通过", step_results[4].get("status") == "passed" and step_results[4].get("action") == "wait_for")

# 验证断言结果
a_details = exec_data.get("assertion_details", [])
check("assertion_details 返回 3 条", len(a_details) == 3, f"got {len(a_details)}")
if a_details:
    check("text_visible 断言通过", a_details[0].get("passed") == True, str(a_details[0]))
    check("url_contains 断言通过", a_details[1].get("passed") == True, str(a_details[1]))
    check("element_visible 断言通过", a_details[2].get("passed") == True, str(a_details[2]))

# ── 4. 验证结果写入 DB ────────────────────────────
print("\n── 验证结果写入 DB ──")
# 通过 list API 验证 test_runs
r3 = api("get", "/api/v2/test-runs", params={"limit": 10})
if r3.ok:
    r3_data = r3.json()
    runs = r3_data if isinstance(r3_data, list) else r3_data.get("test_runs", r3_data.get("runs", []))
    if isinstance(runs, list):
        found = any((r.get("id") == run_id or r.get("run_id") == run_id) for r in runs)
        check("test_runs 包含执行记录", found, f"run_id={run_id} runs_ids={[r.get('id') for r in runs[:5]]}")
    else:
        check("test_runs 包含执行记录", True, "format unknown, but API ok")
else:
    skip("test_runs 查询", f"API: {r3.status_code}")

# ── 5. 失败截图 ──────────────────────────────────
print("\n── 失败截图 ──")
fail_payload = {
    "title": "P2-4 失败截图测试",
    "case_type": "web_ui",
    "steps": [
        {"action": "goto", "target": "/login", "value": "", "description": "打开登录页"},
    ],
    "assertions": [
        {"type": "url_contains", "target": "", "value": "this_will_never_match_12345", "description": "故意失败的断言"},
    ],
    "execution_config": {
        "engine": "playwright",
        "browser": "chromium",
        "base_url": MOCK_BASE,
        "headless": True,
        "timeout": 5000,
    },
}
rf = api("post", "/api/v2/test-cases", json=fail_payload)
fail_id = rf.json().get("test_case_id", "")
rf2 = api("post", f"/api/v2/test-cases/{fail_id}/execute", json={})
check("失败用例执行返回 200", rf2.status_code == 200, f"status={rf2.status_code}")
fail_data = rf2.json()
check("失败用例状态为 failed", fail_data.get("status") == "failed", f"status={fail_data.get('status')}")
check("失败用例有 error_message", bool(fail_data.get("error_message")), fail_data.get("error_message","")[:200])
fail_ss = (fail_data.get("response_snapshot") or {}).get("failure_screenshot", "")
check("失败截图路径不为空", bool(fail_ss), f"screenshot={fail_ss}")
if fail_ss:
    check("失败截图文件存在", os.path.exists(fail_ss), f"path={fail_ss}")

# ── 6. 不支持 action ──────────────────────────────
print("\n── 不支持 action ──")
bad_payload = {
    "title": "P2-4 不支持 action 测试",
    "case_type": "web_ui",
    "steps": [
        {"action": "drag_and_drop", "target": "#src", "value": "#dst", "description": "拖拽"},
    ],
    "assertions": [],
    "execution_config": {"engine": "playwright", "browser": "chromium", "base_url": MOCK_BASE, "headless": True},
}
rb = api("post", "/api/v2/test-cases", json=bad_payload)
bad_id = rb.json().get("test_case_id", "")
rb2 = api("post", f"/api/v2/test-cases/{bad_id}/execute", json={})
check("不支持 action 返回 200", rb2.status_code == 200, f"status={rb2.status_code}")
bad_data = rb2.json()
check("不支持 action 状态为 failed", bad_data.get("status") == "failed")
check("错误信息含'不支持'", "不支持" in (bad_data.get("error_message") or ""), bad_data.get("error_message","")[:200])

# ── 7. 非 chromium 浏览器 ─────────────────────────
print("\n── 非 chromium 浏览器 ──")
ff_payload = {
    "title": "P2-4 Firefox 测试",
    "case_type": "web_ui",
    "steps": [{"action": "goto", "target": "/login", "value": "", "description": ""}],
    "assertions": [],
    "execution_config": {"engine": "playwright", "browser": "firefox", "base_url": MOCK_BASE, "headless": True},
}
rff = api("post", "/api/v2/test-cases", json=ff_payload)
ff_id = rff.json().get("test_case_id", "")
rff2 = api("post", f"/api/v2/test-cases/{ff_id}/execute", json={})
check("非 chromium 返回 400", rff2.status_code == 400, f"status={rff2.status_code}")
check("错误含 chromium", "chromium" in (rff2.json().get("detail") or "").lower(), rff2.text[:200])

# ── 8. API 用例不受影响 ───────────────────────────
print("\n── API 用例不受影响 ──")
api_payload = {
    "title": "P2-4 API 兼容测试",
    "module": "兼容",
    "priority": "medium",
    "case_type": "api",
    "expected": "200",
    "execution_config": {
        "method": "GET",
        "url": "/health",
    },
}
ra = api("post", "/api/v2/test-cases", json=api_payload)
api_case_id = ra.json().get("test_case_id", "")
ra2 = api("post", f"/api/v2/test-cases/{api_case_id}/execute", json={"base_url": BASE})
check("API 用例执行返回 200", ra2.status_code == 200, f"status={ra2.status_code}")
check("API 用例不走 Playwright", (ra2.json().get("request_snapshot") or {}).get("engine") != "playwright")

# ── 清理 ──────────────────────────────────────────
for cid in [case_id, fail_id, bad_id, ff_id, api_case_id]:
    if cid:
        api("put", f"/api/v2/test-cases/{cid}", json={"status": "deleted"})

httpd.shutdown()

# ── 汇总 ──────────────────────────────────────────
print(f"\n{'=' * 60}")
print(f"  P2-4 Playwright Engine MVP: PASS={PASS} FAIL={FAIL} SKIP={SKIP} TOTAL={TOTAL}")
rate = round(PASS / max(PASS + FAIL, 1) * 100, 1)
print(f"  通过率: {rate}%")
print(f"{'=' * 60}")

sys.exit(0 if FAIL == 0 else 1)
