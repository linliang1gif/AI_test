#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# P2-9B.1: Windows GBK 编码兼容
import io, sys
if sys.stdout and getattr(sys.stdout, 'encoding', '').lower().replace('-', '') != 'utf8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr and getattr(sys.stderr, 'encoding', '').lower().replace('-', '') != 'utf8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
P2-1 统一回归脚本
运行所有回归测试并输出汇总结果。
任何关键测试失败时返回非 0 退出码。
"""
import subprocess
import time
import os
import shutil
import signal
import requests

# ── 配置 ──────────────────────────────────────────────
BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
TIMEOUT_PER_SCRIPT = 180  # 每个脚本最大运行秒数
DEFAULT_TESTING_KEY = "regression-test-key-auto"
MANAGE_BACKEND = os.getenv("REGRESSION_MANAGE_BACKEND", "true").lower() == "true"

# 回归脚本列表: (名称, 路径, 是否关键, 是否依赖AI, 外部依赖标记)
# 外部依赖标记: None=无, "external_api"=外部API, "browser"=浏览器
REGRESSION_SCRIPTS = [
    ("P0-7 Smoke 冒烟测试",           "scripts/smoke_p0_7_local.py",            True,  False, None),
    ("API Contract 契约检查",          "scripts/check_api_contract.py",          True,  False, None),
    ("P1-7A Import Pipeline",          "scripts/test_p1_7a_import_pipeline.py",  True,  False, None),
    ("P1-7D Real Mode Safety",         "scripts/test_p1_7d_real_mode_safety.py", True,  False, None),
    ("P1-7E Report Persistence",       "scripts/test_p1_7e_report_persistence.py", True,  False, None),
    ("Phase 18 执行稳定性",            "scripts/test_phase18.py",                False, False, "external_api"),
    ("P2-3 Web UI Case Model",          "scripts/test_p2_3_web_ui_case_model.py", True,  False, None),
    ("P2-4 Playwright Engine MVP",     "scripts/test_p2_4_playwright_engine_mvp.py", True, False, "browser"),
    ("P2-5 Visual Regression MVP",     "scripts/test_p2_5_visual_regression_mvp.py", True, False, "browser"),
    ("P2-6 Playwright Enhanced",       "scripts/test_p2_6_playwright_enhanced.py",  True, False, "browser"),
    ("P2-6B API Performance MVP",      "scripts/test_p2_6b_api_performance_mvp.py", True, False, None),
    ("P2-7 Web UI Batch/Trace",        "scripts/test_p2_7_web_ui_batch_trace.py",   True, False, "browser"),
    ("P2-8 AI UI Failure Analysis",   "scripts/test_p2_8_ai_ui_failure_analysis.py", True, False, "browser"),
    ("P2-9B Web UI Stability",        "scripts/test_p2_9b_web_ui_stability.py",  True, False, "browser"),
    ("P2-10 Test Suite Management",    "scripts/test_p2_10_test_suite_management.py", True, False, None),
    ("P3-1 CI Quality Gate",           "scripts/test_p3_1_ci_quality_gate.py",  True, False, None),
    ("P3-2 Test Data Management",      "scripts/test_p3_2_test_data_management.py", True, False, None),
    ("P3-3A Test Data Enhancement",    "scripts/test_p3_3a_test_data_enhancement.py", True, False, None),
    ("P3-3B Defect Management",        "scripts/test_p3_3b_defect_management.py", True, False, None),
    ("P3-4A Quality Dashboard",        "scripts/test_p3_4a_quality_dashboard.py", True, False, None),
    ("P1-8A AI Heal Guard",            "scripts/test_p1_8a_ai_heal_guard.py",   False, True,  None),
    ("P1-8 AI Case Review",            "scripts/test_p1_8_ai_case_review.py",   False, True,  None),
]


# ── 浏览器可用性检测 ─────────────────────────────────────
def check_browser_available() -> bool:
    """Detect if Playwright + Chromium browser are installed and usable."""
    try:
        r = subprocess.run(
            [sys.executable, "-c",
             "from playwright.sync_api import sync_playwright; "
             "p = sync_playwright().start(); "
             "b = p.chromium.launch(headless=True); "
             "b.close(); p.stop(); "
             "print('BROWSER_OK')"],
            capture_output=True, timeout=15,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        stdout = r.stdout.decode("utf-8", errors="replace")
        return "BROWSER_OK" in stdout
    except Exception:
        return False

# ── 等待后端就绪 ──────────────────────────────────────
def wait_for_backend(url: str, max_wait: int = 60) -> bool:
    print(f"\n⏳ 等待后端就绪: {url}/health ...")
    for i in range(max_wait):
        try:
            r = requests.get(f"{url}/health", timeout=3)
            if r.ok:
                print(f"✅ 后端就绪 ({i+1}s)")
                return True
        except Exception:
            pass
        time.sleep(1)
    print(f"❌ 后端未就绪 ({max_wait}s 超时)")
    return False


def ensure_backend_ready(url: str, max_wait: int = 30, label: str = "") -> bool:
    """每个脚本执行前确认后端可用: 优先 /readiness, 回退 /health, 最多重试 max_wait 秒."""
    for i in range(max_wait):
        # 优先 /readiness
        try:
            r = requests.get(f"{url}/readiness", timeout=3)
            if r.ok:
                return True
        except Exception:
            pass
        # 回退 /health
        try:
            r = requests.get(f"{url}/health", timeout=3)
            if r.ok:
                return True
        except Exception:
            pass
        time.sleep(1)
    tag = f" ({label})" if label else ""
    print(f"  ⚠️ Backend readiness timeout ({max_wait}s){tag}")
    return False


# ── 后端生命周期管理 ──────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_backend_proc = None

def _testing_key():
    return os.getenv("TESTING_KEY", "") or DEFAULT_TESTING_KEY

def start_managed_backend():
    """启动一个带 TESTING=true + TESTING_KEY 的后端进程."""
    global _backend_proc
    # 先检查是否已有后端在运行
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=3)
        if r.ok:
            print("  ⚠️ 已检测到运行中的后端, 先关闭...")
            stop_managed_backend(force_kill_port=True)
            time.sleep(2)
    except Exception:
        pass

    env = {
        **os.environ,
        "TESTING": "true",
        "TESTING_KEY": _testing_key(),
        "PYTHONIOENCODING": "utf-8",
    }
    log_dir = os.path.join(PROJECT_ROOT, "data")
    os.makedirs(log_dir, exist_ok=True)
    _backend_log = open(os.path.join(log_dir, "regression_backend.log"), "w", encoding="utf-8")
    _backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app:create_app",
         "--host", "0.0.0.0", "--port", "8000", "--factory"],
        cwd=PROJECT_ROOT, env=env,
        stdout=_backend_log, stderr=subprocess.STDOUT,
    )
    print(f"  🚀 已启动后端进程 PID={_backend_proc.pid}")


def stop_managed_backend(force_kill_port=False):
    global _backend_proc
    if _backend_proc:
        try:
            _backend_proc.terminate()
            _backend_proc.wait(timeout=10)
        except Exception:
            _backend_proc.kill()
        _backend_proc = None
    if force_kill_port:
        # Windows: kill process on port 8000
        try:
            out = subprocess.check_output("netstat -ano | findstr :8000 | findstr LISTEN", shell=True, text=True)
            for line in out.strip().split("\n"):
                pid = line.strip().split()[-1]
                if pid.isdigit():
                    subprocess.run(["taskkill", "/PID", pid, "/F"], capture_output=True)
        except Exception:
            pass


# ── 运行单个脚本 ──────────────────────────────────────
def run_script(name: str, path: str) -> dict:
    """运行脚本并返回 {status, name, duration, output}"""
    abs_path = os.path.join(PROJECT_ROOT, path)
    if not os.path.exists(abs_path):
        return {"status": "SKIP", "name": name, "duration": 0, "reason": f"文件不存在: {path}"}

    start = time.time()
    try:
        result = subprocess.run(
            [sys.executable, abs_path],
            capture_output=True, timeout=TIMEOUT_PER_SCRIPT,
            env={**os.environ, "PYTHONIOENCODING": "utf-8", "TESTING": "true", "TESTING_KEY": _testing_key()},
            cwd=PROJECT_ROOT,
        )
        duration = round(time.time() - start, 1)
        status = "PASS" if result.returncode == 0 else "FAIL"
        stdout = result.stdout.decode("utf-8", errors="replace") if isinstance(result.stdout, bytes) else (result.stdout or "")
        stderr = result.stderr.decode("utf-8", errors="replace") if isinstance(result.stderr, bytes) else (result.stderr or "")
        output = stdout + stderr
        return {"status": status, "name": name, "duration": duration, "output": output[-500:]}
    except subprocess.TimeoutExpired:
        duration = round(time.time() - start, 1)
        return {"status": "FAIL", "name": name, "duration": duration, "reason": f"超时 ({TIMEOUT_PER_SCRIPT}s)"}
    except Exception as e:
        duration = round(time.time() - start, 1)
        return {"status": "FAIL", "name": name, "duration": duration, "reason": str(e)}


# ── 主流程 ──────────────────────────────────────────
def main():
    print("=" * 70)
    print("  AI Test Platform — 统一回归测试")
    print("=" * 70)

    # 1. 启动/等待后端（带 TESTING=true + TESTING_KEY）
    if MANAGE_BACKEND:
        print(f"\n🔧 回归管理模式: 自动启动后端 (TESTING=true, TESTING_KEY={_testing_key()[:8]}...)")
        start_managed_backend()
    if not wait_for_backend(BASE_URL):
        print("\n❌ 后端未启动，回归测试中止")
        if MANAGE_BACKEND:
            stop_managed_backend()
        sys.exit(1)

    # 2. 检测浏览器可用性
    print(f"\n🔍 检测 Playwright/Chromium 浏览器环境...")
    browser_available = check_browser_available()
    if browser_available:
        print(f"  ✅ Chromium 浏览器可用")
    else:
        print(f"  ⚠️ Chromium 浏览器不可用 — 浏览器依赖测试将标记 XFAIL")

    # 3. 运行回归脚本
    ai_provider = os.getenv("AI_PROVIDER", "none")
    results = []
    for entry in REGRESSION_SCRIPTS:
        name, path, _critical, needs_ai = entry[:4]
        ext_dep = entry[4] if len(entry) > 4 else None

        if needs_ai and ai_provider == "none":
            results.append({"status": "SKIP", "name": name, "duration": 0, "reason": f"AI_PROVIDER=none, 跳过AI依赖测试", "ext_dep": None})
            print(f"\n{'─'*50}")
            print(f"▶ {name}")
            print(f"  ⏭️ SKIP (AI_PROVIDER=none)")
            continue

        # 浏览器不可用时，浏览器依赖测试直接 XFAIL，不执行
        if ext_dep == "browser" and not browser_available:
            results.append({"status": "XFAIL", "name": name, "duration": 0,
                            "reason": "Chromium 浏览器不可用", "ext_dep": ext_dep})
            print(f"\n{'─'*50}")
            print(f"▶ {name}")
            print(f"  ⚠️ XFAIL (Chromium 浏览器不可用)")
            continue

        print(f"\n{'─'*50}")
        print(f"▶ {name}")
        print(f"  {path}")
        print(f"{'─'*50}")
        # P3-4A.1: 每个脚本执行前确认后端 readiness
        if not ensure_backend_ready(BASE_URL, max_wait=30, label=name):
            results.append({"status": "FAIL", "name": name, "duration": 0,
                            "reason": "Backend readiness timeout", "ext_dep": ext_dep})
            icon = "❌"
            print(f"  {icon} FAIL  (Backend readiness timeout)")
            continue
        r = run_script(name, path)
        r["ext_dep"] = ext_dep
        # 外部 API 依赖失败 -> XFAIL（仅限 external_api，浏览器可用时不自动 XFAIL）
        if r["status"] == "FAIL" and ext_dep == "external_api":
            r["status"] = "XFAIL"
            r["reason"] = r.get("reason", "") or f"外部依赖({ext_dep})失败, 标记为 XFAIL"
        results.append(r)
        icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️", "XFAIL": "⚠️"}.get(r["status"], "?")
        print(f"  {icon} {r['status']}  ({r['duration']}s)")
        if r.get("reason"):
            print(f"  原因: {r['reason']}")

    # 4. 汇总
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    skipped = sum(1 for r in results if r["status"] == "SKIP")
    xfail = sum(1 for r in results if r["status"] == "XFAIL")

    print(f"\n{'=' * 70}")
    print(f"  回归测试汇总")
    print(f"{'=' * 70}")
    print(f"  总计: {total}  ✅ PASS: {passed}  ❌ FAIL: {failed}  ⚠️ XFAIL: {xfail}  ⏭️ SKIP: {skipped}")
    effective = total - skipped - xfail
    print(f"  核心通过率: {passed}/{effective} = {round(passed / max(effective, 1) * 100, 1)}%")
    print(f"{'=' * 70}")

    # 逐条列表
    for r in results:
        icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️", "XFAIL": "⚠️"}.get(r["status"], "?")
        dep_tag = f" [{r.get('ext_dep')}]" if r.get('ext_dep') else ""
        print(f"  {icon} {r['name']:40} {r['status']:6} {r['duration']}s{dep_tag}")

    # 外部依赖失败明细
    xfail_items = [r for r in results if r["status"] == "XFAIL"]
    if xfail_items:
        print(f"\n⚠️  外部依赖失败 ({len(xfail_items)} 个), 不影响核心链路:")
        for r in xfail_items:
            print(f"  ⚠️  {r['name']} — {r.get('ext_dep', '?')}")

    # 5. 关键失败判定
    critical_failures = []
    for i, entry in enumerate(REGRESSION_SCRIPTS):
        name, path, critical = entry[0], entry[1], entry[2]
        if critical and results[i]["status"] == "FAIL":
            critical_failures.append(name)

    if MANAGE_BACKEND:
        print("\n🛑 关闭回归管理的后端进程...")
        stop_managed_backend()

    if critical_failures:
        print(f"\n🚨 关键测试失败 ({len(critical_failures)} 个):")
        for cf in critical_failures:
            print(f"  ❌ {cf}")
        sys.exit(1)

    if failed > 0:
        print(f"\n⚠️  有 {failed} 个非关键测试失败，但不阻塞 CI")

    summary_msg = []
    if skipped > 0:
        summary_msg.append(f"SKIP: {skipped}")
    if xfail > 0:
        summary_msg.append(f"XFAIL: {xfail}")

    suffix = f" ({', '.join(summary_msg)})" if summary_msg else ""
    print(f"\n🎉 回归测试通过!{suffix}")
    sys.exit(0)


if __name__ == "__main__":
    main()
