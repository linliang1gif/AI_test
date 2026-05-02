#!/usr/bin/env python3
"""
P2-3 Web UI 用例模型 — 回归测试脚本

覆盖:
1. 创建 Web UI 用例成功
2. Web UI steps 保存成功
3. Web UI assertions 保存成功
4. execution_config.engine=playwright 保存成功
5. 查询列表能看到 case_type=web_ui
6. case_type 筛选可用
7. 编辑 Web UI 用例成功
8. deleted Web UI 用例不可编辑
9. API 用例不受影响
10. functional 用例不受影响
11. Web UI 用例执行时返回友好提示
"""
import sys, os, requests, json

BASE = os.getenv("BACKEND_URL", "http://localhost:8000")
PASS = FAIL = SKIP = TOTAL = 0


def check(name, condition, detail=""):
    global PASS, FAIL, TOTAL
    TOTAL += 1
    if condition:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}  {detail}")


def api(method, path, **kw):
    kw.setdefault("timeout", 10)
    r = getattr(requests, method)(f"{BASE}{path}", **kw)
    return r


# ── 0. Health ───────────────────────────────────────
print("\n" + "=" * 60)
print("  P2-3 Web UI Case Model Tests")
print("=" * 60)

h = api("get", "/health")
check("Backend healthy", h.ok, h.text[:200])

# ── 1. 创建 Web UI 用例 ────────────────────────────
print("\n── 创建 Web UI 用例 ──")
webui_payload = {
    "title": "P2-3 登录流程测试",
    "module": "用户管理",
    "priority": "high",
    "case_type": "web_ui",
    "expected": "登录成功跳转首页",
    "steps": [
        {"action": "goto", "target": "/login", "value": "", "description": "打开登录页"},
        {"action": "fill", "target": "input[name=username]", "value": "admin", "description": "输入用户名"},
        {"action": "fill", "target": "input[name=password]", "value": "pass123", "description": "输入密码"},
        {"action": "click", "target": "button[type=submit]", "value": "", "description": "点击登录"},
    ],
    "assertions": [
        {"type": "url_contains", "target": "", "value": "/dashboard", "description": "跳转到首页"},
        {"type": "text_visible", "target": "", "value": "首页", "description": "展示首页文字"},
    ],
    "execution_config": {
        "engine": "playwright",
        "browser": "chromium",
        "base_url": "http://localhost:3000",
        "viewport": {"width": 1366, "height": 768},
        "headless": True,
    },
}
r = api("post", "/api/v2/test-cases", json=webui_payload)
check("创建 Web UI 用例 status=200", r.status_code in (200, 201), f"status={r.status_code}")
data = r.json()
check("创建 Web UI 用例 success=true", data.get("success"), json.dumps(data, ensure_ascii=False)[:200])
webui_id = data.get("test_case_id", "")
check("返回 test_case_id", bool(webui_id), f"id={webui_id}")

# ── 2. 查询详情验证字段 ────────────────────────────
print("\n── 验证字段保存 ──")
r2 = api("get", f"/api/v2/test-cases/{webui_id}")
check("查询 Web UI 用例详情", r2.ok, f"status={r2.status_code}")
tc = r2.json()
check("case_type=web_ui", tc.get("case_type") == "web_ui", f"got {tc.get('case_type')}")
steps = tc.get("steps") or []
check("steps 保存 4 步", len(steps) == 4, f"got {len(steps)}")
if steps:
    check("step[0].action=goto", steps[0].get("action") == "goto", f"got {steps[0]}")
assertions = tc.get("assertions") or []
check("assertions 保存 2 条", len(assertions) == 2, f"got {len(assertions)}")
if assertions:
    check("assertion[0].type=url_contains", assertions[0].get("type") == "url_contains", f"got {assertions[0]}")
ec = tc.get("execution_config") or {}
check("execution_config.engine=playwright", ec.get("engine") == "playwright", f"got {ec}")
check("execution_config.browser=chromium", ec.get("browser") == "chromium", f"got {ec}")
check("execution_config.base_url 保存", ec.get("base_url") == "http://localhost:3000", f"got {ec}")

# ── 3. 列表和筛选 ──────────────────────────────────
print("\n── 列表和筛选 ──")
r3 = api("get", "/api/v2/test-cases", params={"case_type": "web_ui", "limit": 500})
check("列表查询成功", r3.ok)
all_cases = r3.json().get("test_cases", [])
webui_found = any(c["id"] == webui_id for c in all_cases)
check("列表中能找到 Web UI 用例", webui_found)

r4 = api("get", "/api/v2/test-cases", params={"case_type": "web_ui", "limit": 500})
check("case_type=web_ui 筛选成功", r4.ok)
filtered = r4.json().get("test_cases", [])
check("筛选结果包含刚创建的用例", any(c["id"] == webui_id for c in filtered))
check("筛选结果全部为 web_ui", all(c.get("case_type") == "web_ui" for c in filtered), f"got {[c.get('case_type') for c in filtered[:5]]}")

# ── 4. 编辑 Web UI 用例 ────────────────────────────
print("\n── 编辑 Web UI 用例 ──")
r5 = api("put", f"/api/v2/test-cases/{webui_id}", json={
    "title": "P2-3 登录流程测试（已编辑）",
    "steps": [
        {"action": "goto", "target": "/login", "value": "", "description": "打开登录页"},
        {"action": "fill", "target": "#username", "value": "admin2", "description": "输入新用户名"},
        {"action": "click", "target": "#login-btn", "value": "", "description": "点击登录"},
    ],
})
check("编辑 Web UI 用例成功", r5.ok and r5.json().get("success"), f"status={r5.status_code} {r5.text[:200]}")
r5b = api("get", f"/api/v2/test-cases/{webui_id}")
tc2 = r5b.json()
check("编辑后标题更新", "已编辑" in tc2.get("title", ""), f"title={tc2.get('title')}")
check("编辑后 steps 变为 3 步", len(tc2.get("steps", [])) == 3, f"got {len(tc2.get('steps', []))}")

# ── 5. deleted 用例不可编辑 ─────────────────────────
print("\n── deleted 用例不可编辑 ──")
api("put", f"/api/v2/test-cases/{webui_id}", json={"status": "deleted"})
r6 = api("get", f"/api/v2/test-cases/{webui_id}")
check("deleted 用例查询返回 404", r6.status_code == 404, f"status={r6.status_code}")

# ── 6. API 用例不受影响 ────────────────────────────
print("\n── API 用例不受影响 ──")
api_payload = {
    "title": "P2-3 API 用例兼容测试",
    "module": "兼容",
    "priority": "medium",
    "case_type": "api",
    "steps": ["发送 GET 请求"],
    "expected": "返回 200",
}
r7 = api("post", "/api/v2/test-cases", json=api_payload)
check("创建 API 用例成功", r7.ok and r7.json().get("success"))
api_id = r7.json().get("test_case_id", "")
r7b = api("get", f"/api/v2/test-cases/{api_id}")
check("API 用例 case_type 正确", r7b.json().get("case_type") in ("api", None))

# ── 7. functional 用例不受影响 ─────────────────────
print("\n── functional 用例不受影响 ──")
func_payload = {
    "title": "P2-3 功能用例兼容测试",
    "module": "兼容",
    "priority": "low",
    "steps": ["打开页面", "验证功能"],
    "expected": "功能正常",
}
r8 = api("post", "/api/v2/test-cases", json=func_payload)
check("创建 functional 用例成功", r8.ok and r8.json().get("success"))
func_id = r8.json().get("test_case_id", "")
r8b = api("get", f"/api/v2/test-cases/{func_id}")
check("functional 用例 case_type 正确", r8b.json().get("case_type") == "functional")

# ── 8. Web UI 用例执行分发 ─────────────────────────
print("\n── Web UI 执行分发 ──")
# P2-4: web_ui 用例现在走 PlaywrightEngine，不再阻止
r9_c = api("post", "/api/v2/test-cases", json={
    "title": "P2-3 执行分发测试",
    "case_type": "web_ui",
    "steps": [{"action": "goto", "target": "/test", "value": "", "description": "测试"}],
    "execution_config": {"engine": "playwright"},
})
exec_id = r9_c.json().get("test_case_id", "")
r9 = api("post", f"/api/v2/test-cases/{exec_id}/execute", json={})
check("Web UI 用例执行返回 200", r9.status_code == 200, f"status={r9.status_code}")
check("Web UI 执行有 run_id", bool(r9.json().get("run_id")), f"body={r9.text[:200]}")

# ── 9. case_type 校验 ─────────────────────────────
print("\n── case_type 校验 ──")
r10 = api("post", "/api/v2/test-cases", json={
    "title": "P2-3 非法 case_type",
    "case_type": "invalid_type",
})
check("非法 case_type 返回 400", r10.status_code == 400, f"status={r10.status_code}")

# ── 清理 ──────────────────────────────────────────
for cid in [api_id, func_id, exec_id]:
    if cid:
        api("put", f"/api/v2/test-cases/{cid}", json={"status": "deleted"})

# ── 汇总 ──────────────────────────────────────────
print(f"\n{'=' * 60}")
print(f"  P2-3 Web UI Case Model: PASS={PASS} FAIL={FAIL} SKIP={SKIP} TOTAL={TOTAL}")
rate = round(PASS / max(PASS + FAIL, 1) * 100, 1)
print(f"  通过率: {rate}%")
print(f"{'=' * 60}")

sys.exit(0 if FAIL == 0 else 1)
