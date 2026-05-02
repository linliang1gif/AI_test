#!/usr/bin/env python3
"""
P2-1 统一回归脚本
运行所有回归测试并输出汇总结果。
任何关键测试失败时返回非 0 退出码。
"""
import subprocess
import sys
import time
import os
import requests

# ── 配置 ──────────────────────────────────────────────
BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
TIMEOUT_PER_SCRIPT = 120  # 每个脚本最大运行秒数

# 回归脚本列表: (名称, 路径, 是否关键, 是否依赖AI)
REGRESSION_SCRIPTS = [
    ("P0-7 Smoke 冒烟测试",           "scripts/smoke_p0_7_local.py",            True,  False),
    ("API Contract 契约检查",          "scripts/check_api_contract.py",          True,  False),
    ("P1-7A Import Pipeline",          "scripts/test_p1_7a_import_pipeline.py",  True,  False),
    ("P1-7D Real Mode Safety",         "scripts/test_p1_7d_real_mode_safety.py", True,  False),
    ("P1-7E Report Persistence",       "scripts/test_p1_7e_report_persistence.py", True,  False),
    ("P2-3 Web UI Case Model",          "scripts/test_p2_3_web_ui_case_model.py", True,  False),
    ("P2-4 Playwright Engine MVP",     "scripts/test_p2_4_playwright_engine_mvp.py", True, False),
    ("P2-5 Visual Regression MVP",     "scripts/test_p2_5_visual_regression_mvp.py", True, False),
    ("P1-8A AI Heal Guard",            "scripts/test_p1_8a_ai_heal_guard.py",   False, True),
    ("P1-8 AI Case Review",            "scripts/test_p1_8_ai_case_review.py",   False, True),
]

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


# ── 运行单个脚本 ──────────────────────────────────────
def run_script(name: str, path: str) -> dict:
    """运行脚本并返回 {status, name, duration, output}"""
    abs_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), path)
    if not os.path.exists(abs_path):
        return {"status": "SKIP", "name": name, "duration": 0, "reason": f"文件不存在: {path}"}

    start = time.time()
    try:
        result = subprocess.run(
            [sys.executable, abs_path],
            capture_output=True, timeout=TIMEOUT_PER_SCRIPT,
            env={**os.environ, "PYTHONIOENCODING": "utf-8", "TESTING": "true", "TESTING_KEY": os.getenv("TESTING_KEY", "")},
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
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

    # 1. 等待后端
    if not wait_for_backend(BASE_URL):
        print("\n❌ 后端未启动，回归测试中止")
        sys.exit(1)

    # 2. 运行回归脚本
    ai_provider = os.getenv("AI_PROVIDER", "none")
    results = []
    for name, path, _critical, needs_ai in REGRESSION_SCRIPTS:
        if needs_ai and ai_provider == "none":
            results.append({"status": "SKIP", "name": name, "duration": 0, "reason": f"AI_PROVIDER=none, 跳过AI依赖测试"})
            print(f"\n{'\u2500'*50}")
            print(f"\u25b6 {name}")
            print(f"  \u23ed\ufe0f SKIP (AI_PROVIDER=none)")
            continue
        print(f"\n{'─'*50}")
        print(f"▶ {name}")
        print(f"  {path}")
        print(f"{'─'*50}")
        r = run_script(name, path)
        results.append(r)
        icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️"}.get(r["status"], "?")
        print(f"  {icon} {r['status']}  ({r['duration']}s)")
        if r.get("reason"):
            print(f"  原因: {r['reason']}")

    # 3. 汇总
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    skipped = sum(1 for r in results if r["status"] == "SKIP")

    print(f"\n{'=' * 70}")
    print(f"  回归测试汇总")
    print(f"{'=' * 70}")
    print(f"  总计: {total}  ✅ PASS: {passed}  ❌ FAIL: {failed}  ⏭️ SKIP: {skipped}")
    print(f"  通过率: {passed}/{total - skipped} = {round(passed / max(total - skipped, 1) * 100, 1)}%")
    print(f"{'=' * 70}")

    # 逐条列表
    for r in results:
        icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️"}.get(r["status"], "?")
        print(f"  {icon} {r['name']:40} {r['status']:6} {r['duration']}s")

    # 4. 关键失败判定
    critical_failures = []
    for i, (name, path, critical, _ai) in enumerate(REGRESSION_SCRIPTS):
        if critical and results[i]["status"] == "FAIL":
            critical_failures.append(name)

    if critical_failures:
        print(f"\n🚨 关键测试失败 ({len(critical_failures)} 个):")
        for cf in critical_failures:
            print(f"  ❌ {cf}")
        sys.exit(1)

    if failed > 0:
        print(f"\n⚠️  有 {failed} 个非关键测试失败，但不阻塞 CI")

    if skipped > 0:
        skip_reasons = [r.get('reason', '未知') for r in results if r['status'] == 'SKIP']
        print(f"\n🎉 回归测试通过! (SKIP: {skipped} 个)")
        for sr in skip_reasons:
            print(f"  ⏭️  {sr}")
    else:
        print(f"\n🎉 回归测试全部通过!")
    sys.exit(0)


if __name__ == "__main__":
    main()
