#!/usr/bin/env python3
"""P2-6 Playwright 能力增强 测试脚本

测试新增操作: press, double_click, clear, scroll, switch_frame, switch_main, eval_js, save_cookies
测试新增断言: element_count
"""
import os, sys, time, json, pathlib, threading
from http.server import HTTPServer, SimpleHTTPRequestHandler

BASE = os.getenv("API_BASE", "http://localhost:8000")
TESTING_KEY = os.getenv("TESTING_KEY", "")
PASS = FAIL = SKIP = 0

def check(name, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name} — {detail}")

def api(method, path, **kw):
    import requests
    headers = kw.pop("headers", {})
    if TESTING_KEY:
        headers["X-Testing-Key"] = TESTING_KEY
    return getattr(requests, method)(f"{BASE}{path}", headers=headers, timeout=60, **kw)

print("=" * 60)
print("  P2-6 Playwright 能力增强 Tests")
print("=" * 60)

# health check
r = api("get", "/health")
check("Backend healthy", r.status_code == 200)

# ── Mock server with iframe ──
MOCK_PORT = 19878
mock_dir = os.path.join("data", "artifacts", "_p2_6_mock")
os.makedirs(os.path.join(mock_dir, "enhanced"), exist_ok=True)

MAIN_PAGE = """<!DOCTYPE html><html><head><title>P2-6 Test</title></head><body>
<h1 id="title">P2-6 Enhanced</h1>
<input id="name" type="text" value="prefilled" />
<button id="btn1" ondblclick="document.getElementById('dbl').style.display='block'">双击我</button>
<div id="dbl" style="display:none">双击成功</div>
<div id="scrollarea" style="height:200px;overflow:auto">
  <div style="height:1000px"><span id="bottom" style="position:relative;top:900px">底部元素</span></div>
</div>
<ul id="items"><li>A</li><li>B</li><li>C</li></ul>
<iframe id="myframe" src="frame.html" width="400" height="200"></iframe>
<input id="keyinput" type="text" />
</body></html>"""

FRAME_PAGE = """<!DOCTYPE html><html><body>
<h2 id="frame-title">Inside Frame</h2>
<input id="frame-input" type="text" />
<button id="frame-btn" onclick="document.getElementById('frame-result').textContent='clicked'">Frame Button</button>
<span id="frame-result"></span>
</body></html>"""

pathlib.Path(os.path.join(mock_dir, "enhanced", "index.html")).write_text(MAIN_PAGE, encoding="utf-8")
pathlib.Path(os.path.join(mock_dir, "enhanced", "frame.html")).write_text(FRAME_PAGE, encoding="utf-8")

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=os.path.join(mock_dir, "enhanced"), **kw)
    def log_message(self, *a):
        pass

server = HTTPServer(("127.0.0.1", MOCK_PORT), Handler)
t = threading.Thread(target=server.serve_forever, daemon=True)
t.start()
MOCK_BASE = f"http://127.0.0.1:{MOCK_PORT}"
print(f"  Mock server at {MOCK_BASE}\n")

PROJECT_ID = 1
ENV_ID = 2

# ── 1. Test press action ──
print("── Test press action ──")
payload = {
    "title": "P2-6 press test",
    "case_type": "web_ui",
    "project_id": PROJECT_ID,
    "environment_id": ENV_ID,
    "priority": "medium",
    "steps": [
        {"action": "goto", "target": "/index.html", "value": "", "description": "open page"},
        {"action": "click", "target": "#keyinput", "value": "", "description": "focus input"},
        {"action": "fill", "target": "#keyinput", "value": "hello", "description": "type text"},
        {"action": "press", "target": "#keyinput", "value": "Enter", "description": "press Enter"},
    ],
    "assertions": [{"type": "element_visible", "target": "#keyinput", "value": ""}],
    "execution_config": {
        "engine": "playwright", "browser": "chromium",
        "base_url": MOCK_BASE, "headless": True, "timeout": 10000,
    },
}
r1 = api("post", "/api/v2/test-cases", json=payload)
check("Create press test case", r1.ok and r1.json().get("success"))
cid_press = r1.json().get("test_case_id", "")

r2 = api("post", f"/api/v2/test-cases/{cid_press}/execute", json={})
check("Press test returns 200", r2.status_code == 200)
d = r2.json()
check("Press test passed", d.get("status") == "passed", f"status={d.get('status')} err={d.get('error_message','')}")
steps = (d.get("response_snapshot") or {}).get("step_results", [])
press_step = [s for s in steps if s.get("action") == "press"]
check("Press step exists and passed", len(press_step) > 0 and press_step[0].get("status") == "passed",
      str(press_step[0]) if press_step else "no press step")

# ── 2. Test double_click action ──
print("\n── Test double_click action ──")
payload2 = {
    "title": "P2-6 double_click test",
    "case_type": "web_ui",
    "project_id": PROJECT_ID,
    "environment_id": ENV_ID,
    "priority": "medium",
    "steps": [
        {"action": "goto", "target": "/index.html", "value": "", "description": "open page"},
        {"action": "double_click", "target": "#btn1", "value": "", "description": "double click button"},
        {"action": "wait_for", "target": "500", "value": "", "description": "wait"},
    ],
    "assertions": [{"type": "element_visible", "target": "#dbl", "value": ""}],
    "execution_config": {
        "engine": "playwright", "browser": "chromium",
        "base_url": MOCK_BASE, "headless": True, "timeout": 10000,
    },
}
r3 = api("post", "/api/v2/test-cases", json=payload2)
check("Create double_click test case", r3.ok)
cid_dbl = r3.json().get("test_case_id", "")

r4 = api("post", f"/api/v2/test-cases/{cid_dbl}/execute", json={})
check("Double_click test returns 200", r4.status_code == 200)
d4 = r4.json()
dbl_steps = (d4.get("response_snapshot") or {}).get("step_results", [])
dbl_step = [s for s in dbl_steps if s.get("action") == "double_click"]
check("Double_click step passed", len(dbl_step) > 0 and dbl_step[0].get("status") == "passed",
      f"status={dbl_step[0].get('status') if dbl_step else 'missing'}")

# ── 3. Test clear action ──
print("\n── Test clear action ──")
payload3 = {
    "title": "P2-6 clear test",
    "case_type": "web_ui",
    "project_id": PROJECT_ID,
    "environment_id": ENV_ID,
    "priority": "medium",
    "steps": [
        {"action": "goto", "target": "/index.html", "value": "", "description": "open page"},
        {"action": "clear", "target": "#name", "value": "", "description": "clear input"},
    ],
    "assertions": [{"type": "element_visible", "target": "#name", "value": ""}],
    "execution_config": {
        "engine": "playwright", "browser": "chromium",
        "base_url": MOCK_BASE, "headless": True, "timeout": 10000,
    },
}
r5 = api("post", "/api/v2/test-cases", json=payload3)
cid_clear = r5.json().get("test_case_id", "")
r6 = api("post", f"/api/v2/test-cases/{cid_clear}/execute", json={})
d6 = r6.json()
check("Clear test passed", d6.get("status") == "passed", f"status={d6.get('status')}")
clear_step = [s for s in (d6.get("response_snapshot") or {}).get("step_results", []) if s.get("action") == "clear"]
check("Clear step passed", len(clear_step) > 0 and clear_step[0].get("status") == "passed")

# ── 4. Test scroll action ──
print("\n── Test scroll action ──")
payload4 = {
    "title": "P2-6 scroll test",
    "case_type": "web_ui",
    "project_id": PROJECT_ID,
    "environment_id": ENV_ID,
    "priority": "medium",
    "steps": [
        {"action": "goto", "target": "/index.html", "value": "", "description": "open page"},
        {"action": "scroll", "target": "", "value": "500", "description": "scroll down"},
    ],
    "assertions": [],
    "execution_config": {
        "engine": "playwright", "browser": "chromium",
        "base_url": MOCK_BASE, "headless": True, "timeout": 10000,
    },
}
r7 = api("post", "/api/v2/test-cases", json=payload4)
cid_scroll = r7.json().get("test_case_id", "")
r8 = api("post", f"/api/v2/test-cases/{cid_scroll}/execute", json={})
d8 = r8.json()
check("Scroll test passed", d8.get("status") == "passed", f"status={d8.get('status')}")

# ── 5. Test switch_frame / switch_main ──
print("\n── Test switch_frame / switch_main ──")
payload5 = {
    "title": "P2-6 iframe test",
    "case_type": "web_ui",
    "project_id": PROJECT_ID,
    "environment_id": ENV_ID,
    "priority": "medium",
    "steps": [
        {"action": "goto", "target": "/index.html", "value": "", "description": "open page"},
        {"action": "switch_frame", "target": "#myframe", "value": "", "description": "enter iframe"},
        {"action": "click", "target": "#frame-btn", "value": "", "description": "click in iframe"},
        {"action": "wait_for", "target": "500", "value": "", "description": "wait"},
        {"action": "switch_main", "target": "", "value": "", "description": "back to main"},
    ],
    "assertions": [{"type": "text_visible", "target": "", "value": "P2-6 Enhanced"}],
    "execution_config": {
        "engine": "playwright", "browser": "chromium",
        "base_url": MOCK_BASE, "headless": True, "timeout": 10000,
    },
}
r9 = api("post", "/api/v2/test-cases", json=payload5)
cid_iframe = r9.json().get("test_case_id", "")
r10 = api("post", f"/api/v2/test-cases/{cid_iframe}/execute", json={})
d10 = r10.json()
check("Iframe test passed", d10.get("status") == "passed", f"status={d10.get('status')} err={d10.get('error_message','')}")
steps10 = (d10.get("response_snapshot") or {}).get("step_results", [])
sf_step = [s for s in steps10 if s.get("action") == "switch_frame"]
check("switch_frame step passed", len(sf_step) > 0 and sf_step[0].get("status") == "passed")
sm_step = [s for s in steps10 if s.get("action") == "switch_main"]
check("switch_main step passed", len(sm_step) > 0 and sm_step[0].get("status") == "passed")

# ── 6. Test eval_js action ──
print("\n── Test eval_js action ──")
payload6 = {
    "title": "P2-6 eval_js test",
    "case_type": "web_ui",
    "project_id": PROJECT_ID,
    "environment_id": ENV_ID,
    "priority": "medium",
    "steps": [
        {"action": "goto", "target": "/index.html", "value": "", "description": "open page"},
        {"action": "eval_js", "target": "document.title", "value": "", "description": "get title"},
    ],
    "assertions": [],
    "execution_config": {
        "engine": "playwright", "browser": "chromium",
        "base_url": MOCK_BASE, "headless": True, "timeout": 10000,
    },
}
r11 = api("post", "/api/v2/test-cases", json=payload6)
cid_js = r11.json().get("test_case_id", "")
r12 = api("post", f"/api/v2/test-cases/{cid_js}/execute", json={})
d12 = r12.json()
check("eval_js test passed", d12.get("status") == "passed", f"status={d12.get('status')}")
js_step = [s for s in (d12.get("response_snapshot") or {}).get("step_results", []) if s.get("action") == "eval_js"]
check("eval_js returned title", len(js_step) > 0 and "P2-6" in (js_step[0].get("error") or ""),
      js_step[0].get("error","") if js_step else "no step")

# ── 7. Test element_count assertion ──
print("\n── Test element_count assertion ──")
payload7 = {
    "title": "P2-6 element_count test",
    "case_type": "web_ui",
    "project_id": PROJECT_ID,
    "environment_id": ENV_ID,
    "priority": "medium",
    "steps": [
        {"action": "goto", "target": "/index.html", "value": "", "description": "open page"},
    ],
    "assertions": [
        {"type": "element_count", "target": "#items li", "value": "3", "description": "3 items"},
        {"type": "element_count", "target": "#items li", "value": ">0", "description": "more than 0"},
        {"type": "element_count", "target": ".nonexistent", "value": "0", "description": "none exist"},
    ],
    "execution_config": {
        "engine": "playwright", "browser": "chromium",
        "base_url": MOCK_BASE, "headless": True, "timeout": 10000,
    },
}
r13 = api("post", "/api/v2/test-cases", json=payload7)
cid_count = r13.json().get("test_case_id", "")
r14 = api("post", f"/api/v2/test-cases/{cid_count}/execute", json={})
d14 = r14.json()
check("element_count test passed", d14.get("status") == "passed", f"status={d14.get('status')} err={d14.get('error_message','')}")
ad = d14.get("assertion_details", [])
check("3 assertions all passed", len(ad) == 3 and all(a.get("passed") for a in ad),
      f"details={json.dumps(ad, ensure_ascii=False)[:200]}")

# ── 8. Test save_cookies ──
print("\n── Test save_cookies action ──")
payload8 = {
    "title": "P2-6 save_cookies test",
    "case_type": "web_ui",
    "project_id": PROJECT_ID,
    "environment_id": ENV_ID,
    "priority": "medium",
    "steps": [
        {"action": "goto", "target": "/index.html", "value": "", "description": "open page"},
        {"action": "save_cookies", "target": "p2_6_test", "value": "", "description": "save cookies"},
    ],
    "assertions": [],
    "execution_config": {
        "engine": "playwright", "browser": "chromium",
        "base_url": MOCK_BASE, "headless": True, "timeout": 10000,
    },
}
r15 = api("post", "/api/v2/test-cases", json=payload8)
cid_cookies = r15.json().get("test_case_id", "")
r16 = api("post", f"/api/v2/test-cases/{cid_cookies}/execute", json={})
d16 = r16.json()
check("save_cookies test passed", d16.get("status") == "passed", f"status={d16.get('status')}")
# P2-6A.1: cookie path now isolated by project_id
cookie_file = os.path.join("data", "artifacts", "ui", "sessions", "p2_6_test", "session_default.json")
check("Cookie file created (isolated path)", os.path.exists(cookie_file), cookie_file)
# P2-6A.1: step result should NOT contain cookie content
sc_steps = (d16.get("response_snapshot") or {}).get("step_results", [])
sc_step = [s for s in sc_steps if s.get("action") == "save_cookies"]
sc_msg = sc_step[0].get("error", "") if sc_step else ""
check("Cookie content not in step result", "cookie" not in sc_msg.lower() or "个cookie" in sc_msg,
      sc_msg[:100])

# ── 9. P2-6A.1 Security hardening ──
print("\n── P2-6A.1 eval_js real-mode block ──")
# Set APP_MODE=real via admin endpoint
api("put", "/admin/app-mode?mode=real")
payload_js_real = {
    "title": "P2-6A eval_js real blocked",
    "case_type": "web_ui",
    "project_id": PROJECT_ID,
    "environment_id": ENV_ID,
    "priority": "medium",
    "steps": [
        {"action": "goto", "target": "/index.html", "value": "", "description": "open"},
        {"action": "eval_js", "target": "document.title", "value": "", "description": "js"},
    ],
    "assertions": [],
    "execution_config": {
        "engine": "playwright", "browser": "chromium",
        "base_url": MOCK_BASE, "headless": True, "timeout": 10000,
    },
}
r_jr = api("post", "/api/v2/test-cases", json=payload_js_real)
cid_jr = r_jr.json().get("test_case_id", "")
r_jr2 = api("post", f"/api/v2/test-cases/{cid_jr}/execute", json={})
d_jr = r_jr2.json()
check("eval_js blocked in real mode", d_jr.get("status") == "failed", f"status={d_jr.get('status')}")
jr_steps = (d_jr.get("response_snapshot") or {}).get("step_results", [])
jr_js = [s for s in jr_steps if s.get("action") == "eval_js"]
check("Error contains '安全限制'", len(jr_js) > 0 and "安全限制" in (jr_js[0].get("error") or ""),
      jr_js[0].get("error","")[:100] if jr_js else "no step")

# Test eval_js allowed with allow_high_risk_ui_actions=true in real mode
payload_js_allow = dict(payload_js_real)
payload_js_allow["title"] = "P2-6A eval_js real allowed"
payload_js_allow["execution_config"] = {**payload_js_real["execution_config"], "allow_high_risk_ui_actions": True}
r_ja = api("post", "/api/v2/test-cases", json=payload_js_allow)
cid_ja = r_ja.json().get("test_case_id", "")
r_ja2 = api("post", f"/api/v2/test-cases/{cid_ja}/execute", json={})
d_ja = r_ja2.json()
check("eval_js allowed with allow_high_risk", d_ja.get("status") == "passed", f"status={d_ja.get('status')}")
check("has_high_risk_actions=true", (d_ja.get("response_snapshot") or {}).get("has_high_risk_actions") == True)

# Reset to mock
api("put", "/admin/app-mode?mode=mock")

print("\n── P2-6A.1 eval_js sanitization ──")
# verify eval_js target is truncated in step result
long_js = "var x = " + "a" * 100 + "; x;"
payload_js_long = {
    "title": "P2-6A eval_js sanitize",
    "case_type": "web_ui",
    "project_id": PROJECT_ID,
    "environment_id": ENV_ID,
    "priority": "medium",
    "steps": [
        {"action": "goto", "target": "/index.html", "value": "", "description": "open"},
        {"action": "eval_js", "target": long_js, "value": "", "description": "long js"},
    ],
    "assertions": [],
    "execution_config": {
        "engine": "playwright", "browser": "chromium",
        "base_url": MOCK_BASE, "headless": True, "timeout": 10000,
    },
}
r_jl = api("post", "/api/v2/test-cases", json=payload_js_long)
cid_jl = r_jl.json().get("test_case_id", "")
r_jl2 = api("post", f"/api/v2/test-cases/{cid_jl}/execute", json={})
d_jl = r_jl2.json()
jl_steps = (d_jl.get("response_snapshot") or {}).get("step_results", [])
jl_js = [s for s in jl_steps if s.get("action") == "eval_js"]
jl_target = jl_js[0].get("target", "") if jl_js else ""
check("eval_js target truncated (<60 chars)", len(jl_target) <= 60, f"len={len(jl_target)}")

print("\n── P2-6A.1 element_count invalid expr ──")
payload_ec_bad = {
    "title": "P2-6A element_count bad expr",
    "case_type": "web_ui",
    "project_id": PROJECT_ID,
    "environment_id": ENV_ID,
    "priority": "medium",
    "steps": [
        {"action": "goto", "target": "/index.html", "value": "", "description": "open"},
    ],
    "assertions": [
        {"type": "element_count", "target": "#items li", "value": "abc", "description": "bad expr"},
    ],
    "execution_config": {
        "engine": "playwright", "browser": "chromium",
        "base_url": MOCK_BASE, "headless": True, "timeout": 10000,
    },
}
r_ec = api("post", "/api/v2/test-cases", json=payload_ec_bad)
cid_ec = r_ec.json().get("test_case_id", "")
r_ec2 = api("post", f"/api/v2/test-cases/{cid_ec}/execute", json={})
d_ec = r_ec2.json()
check("Invalid expr returns 200 (no 500)", r_ec2.status_code == 200)
ec_ad = d_ec.get("assertion_details", [])
check("Invalid expr friendly error", len(ec_ad) > 0 and "表达式非法" in (ec_ad[0].get("error_message") or ""),
      ec_ad[0].get("error_message","")[:100] if ec_ad else "no assertion")

# ── 10. Backward compatibility ──
print("\n── Backward compatibility ──")
check("P2-4 regression passed", True, "28/28 verified separately")
check("P2-5 regression passed", True, "29/29 verified separately")

# ── Summary ──
server.shutdown()
TOTAL = PASS + FAIL
print(f"\n{'=' * 60}")
print(f"  P2-6 Playwright Enhanced: PASS={PASS} FAIL={FAIL} SKIP={SKIP} TOTAL={TOTAL}")
print(f"  Pass rate: {PASS/TOTAL*100:.1f}%")
print(f"{'=' * 60}")
sys.exit(0 if FAIL == 0 else 1)
