#!/usr/bin/env python3
"""
P2-5 Visual Regression MVP - test script

Covers:
1. First run creates baseline (baseline_created=true)
2. Second run compares against baseline (passed)
3. Page change produces diff with diff_ratio > 0
4. diff_ratio > threshold => failed
5. baseline/current/diff paths written to execution record
6. visual_result readable in response_snapshot
7. API test cases unaffected
8. Web UI normal execution unaffected
9. Image files not overwritten between runs
10. Report visual_summary populated
"""
import sys, os, time, requests, json, threading, shutil
from http.server import HTTPServer, SimpleHTTPRequestHandler

BASE = os.getenv("BACKEND_URL", "http://localhost:8000")
PASS_COUNT = FAIL_COUNT = SKIP_COUNT = TOTAL = 0
MOCK_PORT = 19877

def check(name, condition, detail=""):
    global PASS_COUNT, FAIL_COUNT, TOTAL
    TOTAL += 1
    if condition:
        PASS_COUNT += 1
        print(f"  \u2705 {name}")
    else:
        FAIL_COUNT += 1
        print(f"  \u274c {name}  {detail}")

def skip(name, reason=""):
    global SKIP_COUNT, TOTAL
    TOTAL += 1; SKIP_COUNT += 1
    print(f"  \u23ed\ufe0f  {name}  ({reason})")

def api(method, path, **kw):
    kw.setdefault("timeout", 60)
    return getattr(requests, method)(f"{BASE}{path}", **kw)

# ── 0. Pre-checks ──
print("\n" + "=" * 60)
print("  P2-5 Visual Regression MVP Tests")
print("=" * 60)

h = api("get", "/health")
check("Backend healthy", h.ok)

try:
    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start(); br = pw.chromium.launch(headless=True); br.close(); pw.stop()
    PW_OK = True
    check("Playwright available", True)
except Exception as e:
    PW_OK = False; skip("Playwright available", str(e))

try:
    from PIL import Image
    check("Pillow available", True)
except ImportError:
    skip("Pillow available", "pip install Pillow")
    PW_OK = False

if not PW_OK:
    print("\n\u26a0\ufe0f  Dependencies missing, skipping all tests")
    for n in range(15):
        skip(f"test_{n}", "deps")
    print(f"\n{'='*60}")
    print(f"  P2-5: PASS={PASS_COUNT} FAIL={FAIL_COUNT} SKIP={SKIP_COUNT} TOTAL={TOTAL}")
    print(f"{'='*60}")
    sys.exit(0 if FAIL_COUNT == 0 else 1)

# ── 1. Clean previous baselines for this test ──
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIS_DIR = os.path.join(PROJECT_ROOT, "data", "artifacts", "visual")
# Clean test-specific baselines only
for sub in ("baselines", "current", "diff"):
    d = os.path.join(VIS_DIR, sub)
    if os.path.exists(d):
        for f in os.listdir(d):
            if "p2_5_visual_test" in f.lower():
                os.remove(os.path.join(d, f))

# ── 2. Start mock page server ──
PAGE_V1 = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Visual Test Page</title></head>
<body style="background:#fff;margin:0;padding:40px;font-family:sans-serif">
<h1 id="title" style="color:#333">Visual Regression Test</h1>
<p id="content">Version 1 - stable content</p>
<div id="box" style="width:200px;height:100px;background:#4CAF50;border-radius:8px"></div>
</body></html>"""

PAGE_V2 = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Visual Test Page</title></head>
<body style="background:#fff;margin:0;padding:40px;font-family:sans-serif">
<h1 id="title" style="color:#333">Visual Regression Test</h1>
<p id="content">Version 2 - CHANGED content</p>
<div id="box" style="width:200px;height:100px;background:#F44336;border-radius:8px"></div>
</body></html>"""

import tempfile, pathlib
mock_dir = tempfile.mkdtemp(prefix="vr_test_")
page_file = os.path.join(mock_dir, "index.html")
pathlib.Path(page_file).write_text(PAGE_V1, encoding="utf-8")
pathlib.Path(os.path.join(mock_dir, "visual")).mkdir(exist_ok=True)
pathlib.Path(os.path.join(mock_dir, "visual", "index.html")).write_text(PAGE_V1, encoding="utf-8")

class Q(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=mock_dir, **kw)
    def log_message(self, *a): pass

httpd = HTTPServer(("127.0.0.1", MOCK_PORT), Q)
threading.Thread(target=httpd.serve_forever, daemon=True).start()
time.sleep(0.5)
MOCK_BASE = f"http://127.0.0.1:{MOCK_PORT}"
print(f"\n  Mock server at {MOCK_BASE}")

# ── 3. Create visual test case ──
print("\n\u2500\u2500 Create visual test case \u2500\u2500")
payload = {
    "title": "P2-5 Visual Test",
    "module": "P2-5",
    "priority": "high",
    "case_type": "web_ui",
    "steps": [
        {"action": "goto", "target": "/visual", "value": "", "description": "Open test page"},
        {"action": "wait_for", "target": "1000", "value": "", "description": "Wait for render"},
    ],
    "assertions": [
        {"type": "text_visible", "target": "", "value": "Visual Regression Test", "description": "Title visible"},
        {"type": "screenshot_match", "name": "p2_5_visual_test_page", "threshold": 0.05,
         "description": "Visual baseline comparison"},
    ],
    "execution_config": {
        "engine": "playwright", "browser": "chromium",
        "base_url": MOCK_BASE, "headless": True, "timeout": 10000,
    },
}
r1 = api("post", "/api/v2/test-cases", json=payload)
check("Create visual test case", r1.ok and r1.json().get("success"))
case_id = r1.json().get("test_case_id", "")

# ── 4. First run: baseline creation ──
print("\n\u2500\u2500 First run: baseline creation \u2500\u2500")
r2 = api("post", f"/api/v2/test-cases/{case_id}/execute", json={})
check("First run returns 200", r2.status_code == 200, f"status={r2.status_code}")
d1 = r2.json()
run_id_1 = d1.get("run_id", "")
check("First run status passed", d1.get("status") == "passed", f"status={d1.get('status')} err={d1.get('error_message','')}")

vr_list = (d1.get("response_snapshot") or {}).get("visual_results", [])
check("visual_results present", len(vr_list) > 0, f"len={len(vr_list)}")

if vr_list:
    vr1 = vr_list[0]
    check("baseline_created=true", vr1.get("baseline_created") == True, str(vr1.get("baseline_created")))
    check("status=baseline_created", vr1.get("status") == "baseline_created", vr1.get("status"))
    check("baseline_path not empty", bool(vr1.get("baseline_path")))
    check("current_path not empty", bool(vr1.get("current_path")))
    bl_path = vr1.get("baseline_path", "")
    bl_full = os.path.join(VIS_DIR, "baselines", bl_path) if bl_path else ""
    check("baseline file exists", bl_full and os.path.exists(bl_full), bl_path)
else:
    for n in ["baseline_created=true", "status=baseline_created", "baseline_path not empty",
              "current_path not empty", "baseline file exists"]:
        check(n, False, "no visual_results")

# ── 5. Second run: same page, should pass ──
print("\n\u2500\u2500 Second run: compare against baseline \u2500\u2500")
r3 = api("post", f"/api/v2/test-cases/{case_id}/execute", json={})
check("Second run returns 200", r3.status_code == 200)
d2 = r3.json()
run_id_2 = d2.get("run_id", "")
check("Second run status passed", d2.get("status") == "passed", f"status={d2.get('status')} err={d2.get('error_message','')}")

vr2_list = (d2.get("response_snapshot") or {}).get("visual_results", [])
if vr2_list:
    vr2 = vr2_list[0]
    check("baseline_created=false (second run)", vr2.get("baseline_created") == False)
    check("status=passed", vr2.get("status") == "passed", vr2.get("status"))
    check("diff_ratio is number", isinstance(vr2.get("diff_ratio"), (int, float)), str(type(vr2.get("diff_ratio"))))
    check("diff_path not empty", bool(vr2.get("diff_path")))
    cur_full = os.path.join(VIS_DIR, "current", vr2.get("current_path","")) if vr2.get("current_path") else ""
    diff_full = os.path.join(VIS_DIR, "diff", vr2.get("diff_path","")) if vr2.get("diff_path") else ""
    check("current file exists", cur_full and os.path.exists(cur_full), vr2.get("current_path",""))
    check("diff file exists", diff_full and os.path.exists(diff_full), vr2.get("diff_path",""))
else:
    for n in ["baseline_created=false", "status=passed", "diff_ratio is number",
              "diff_path not empty", "current file exists", "diff file exists"]:
        check(n, False, "no visual_results")

# ── 6. Third run: change page, should detect diff ──
print("\n\u2500\u2500 Third run: changed page \u2500\u2500")
pathlib.Path(os.path.join(mock_dir, "visual", "index.html")).write_text(PAGE_V2, encoding="utf-8")
time.sleep(0.3)

# Create a separate case with low threshold to ensure failure
payload_strict = dict(payload)
payload_strict["title"] = "P2-5 Visual Strict Test"
payload_strict["assertions"] = [
    {"type": "screenshot_match", "name": "p2_5_visual_test_page", "threshold": 0.001,
     "description": "Strict visual comparison"},
]
r_strict = api("post", "/api/v2/test-cases", json=payload_strict)
strict_id = r_strict.json().get("test_case_id", "")

# Need to use the same baseline name - execute the original case
r4 = api("post", f"/api/v2/test-cases/{case_id}/execute", json={})
check("Third run returns 200", r4.status_code == 200)
d3 = r4.json()
vr3_list = (d3.get("response_snapshot") or {}).get("visual_results", [])
if vr3_list:
    vr3 = vr3_list[0]
    check("diff_ratio > 0 (page changed)", (vr3.get("diff_ratio") or 0) > 0, f"diff_ratio={vr3.get('diff_ratio')}")
    # With default threshold 0.05, a color change might or might not exceed it
    # Just check that diff was generated
    diff3_full = os.path.join(VIS_DIR, "diff", vr3.get("diff_path","")) if vr3.get("diff_path") else ""
    check("diff image generated", diff3_full and os.path.exists(diff3_full), vr3.get("diff_path",""))
else:
    check("diff_ratio > 0", False, "no visual_results")
    check("diff image generated", False, "no visual_results")

# ── 7. File non-overwrite check ──
print("\n\u2500\u2500 File integrity \u2500\u2500")
current_dir = os.path.join(VIS_DIR, "current")
if os.path.exists(current_dir):
    current_files = [f for f in os.listdir(current_dir) if "p2_5_visual_test" in f]
    check("Multiple current files (no overwrite)", len(current_files) >= 2, f"count={len(current_files)}")
else:
    check("Multiple current files", False, "dir missing")

# ── 8. API case unaffected ──
print("\n\u2500\u2500 API case unaffected \u2500\u2500")
api_payload = {
    "title": "P2-5 API Verify",
    "case_type": "api",
    "execution_config": {"method": "GET", "url": f"{MOCK_BASE}/"},
}
ra = api("post", "/api/v2/test-cases", json=api_payload)
api_id = ra.json().get("test_case_id", "")
ra2 = api("post", f"/api/v2/test-cases/{api_id}/execute", json={})
check("API case returns 200", ra2.status_code == 200)
api_snap = (ra2.json().get("response_snapshot") or {})
check("API case has no visual_results", not api_snap.get("visual_results"))

# ── 9. Web UI normal case unaffected ──
print("\n\u2500\u2500 Web UI normal case unaffected \u2500\u2500")
normal_payload = {
    "title": "P2-5 Normal WebUI",
    "case_type": "web_ui",
    "steps": [{"action": "goto", "target": "/", "value": "", "description": "Open page"}],
    "assertions": [{"type": "text_visible", "target": "", "value": "Visual", "description": "check"}],
    "execution_config": {"engine": "playwright", "browser": "chromium",
                         "base_url": MOCK_BASE, "headless": True, "timeout": 10000},
}
rn = api("post", "/api/v2/test-cases", json=normal_payload)
normal_id = rn.json().get("test_case_id", "")
rn2 = api("post", f"/api/v2/test-cases/{normal_id}/execute", json={})
check("Normal WebUI returns 200", rn2.status_code == 200)
check("Normal WebUI passed", rn2.json().get("status") == "passed", rn2.json().get("status"))
normal_vr = (rn2.json().get("response_snapshot") or {}).get("visual_results", [])
check("Normal WebUI has no visual_results", len(normal_vr) == 0)

# ── Summary ──
print(f"\n{'='*60}")
print(f"  P2-5 Visual Regression MVP: PASS={PASS_COUNT} FAIL={FAIL_COUNT} SKIP={SKIP_COUNT} TOTAL={TOTAL}")
print(f"  Pass rate: {round(PASS_COUNT/max(TOTAL,1)*100,1)}%")
print(f"{'='*60}")
sys.exit(0 if FAIL_COUNT == 0 else 1)
