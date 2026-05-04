#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P3-1: CI 质量门禁执行脚本

用法:
  python scripts/ci_quality_gate.py --suite-id 1
  python scripts/ci_quality_gate.py --suite-type smoke --project-id 1
  python scripts/ci_quality_gate.py --suite-id 1 --gate-config configs/quality_gate.json
  python scripts/ci_quality_gate.py --suite-id 1 --output data/reports/ci_gate_result.json

exit code 0 = gate passed
exit code 1 = gate failed
exit code 2 = execution error
"""
import io, sys
if sys.stdout and getattr(sys.stdout, 'encoding', '').lower().replace('-', '') != 'utf8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr and getattr(sys.stderr, 'encoding', '').lower().replace('-', '') != 'utf8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import argparse
import json
import os
import time
import requests

DEFAULT_BASE = os.getenv("TEST_BASE_URL", "http://localhost:8000")
DEFAULT_GATE_CONFIG = {
    "fail_on_any_failed": True,
    "fail_on_p0_failed": True,
    "max_api_failures": 0,
    "max_web_ui_failures": 0,
    "max_visual_failures": 0,
    "performance_must_pass": True,
    "skip_policy": "warn",
    "xfail_policy": "warn",
}


def load_gate_config(path):
    if not path:
        return DEFAULT_GATE_CONFIG
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def wait_backend(base, timeout=30):
    for i in range(timeout):
        try:
            r = requests.get(f"{base}/health", timeout=3)
            if r.ok:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def find_suite(base, suite_id=None, suite_type=None, project_id=None):
    """Find suite by id or by type+project."""
    if suite_id:
        r = requests.get(f"{base}/api/v2/test-suites/{suite_id}", timeout=10)
        if r.status_code == 200:
            body = r.json()
            return body.get("data", body) if isinstance(body, dict) else body
        return None

    params = {"limit": 100}
    if suite_type:
        params["suite_type"] = suite_type
    r = requests.get(f"{base}/api/v2/test-suites", params=params, timeout=10)
    if r.status_code != 200:
        return None
    suites = r.json().get("data", [])
    if project_id:
        suites = [s for s in suites if s.get("project_id") == project_id]
    if suite_type:
        suites = [s for s in suites if s.get("suite_type") == suite_type]
    return suites[0] if suites else None


def run_suite(base, suite_id, app_mode="mock"):
    """Execute a test suite and return run result."""
    payload = {}
    if app_mode == "real":
        payload["allow_unsafe_methods"] = False
    r = requests.post(f"{base}/api/v2/test-suites/{suite_id}/run", json=payload, timeout=120)
    if r.status_code != 200:
        return None, f"Suite execution failed: {r.status_code} {r.text[:200]}"
    return r.json(), None


def evaluate_gate(base, run_id, gate_config):
    """Call quality gate API."""
    r = requests.post(f"{base}/api/v2/quality-gates/evaluate",
                      json={"run_id": run_id, "gate_config": gate_config}, timeout=30)
    if r.status_code == 200:
        return r.json(), None
    return None, f"Gate evaluation failed: {r.status_code} {r.text[:200]}"


def main():
    parser = argparse.ArgumentParser(description="P3-1 CI Quality Gate")
    parser.add_argument("--suite-id", type=int, help="Test suite ID")
    parser.add_argument("--suite-type", type=str, help="Suite type (smoke/regression/release)")
    parser.add_argument("--project-id", type=int, help="Project ID filter")
    parser.add_argument("--app-mode", default="mock", choices=["mock", "real"])
    parser.add_argument("--gate-config", type=str, help="Path to gate config JSON")
    parser.add_argument("--output", type=str, help="Output JSON result path")
    parser.add_argument("--base-url", type=str, default=DEFAULT_BASE)
    parser.add_argument("--fail-on-gate-failed", action="store_true", default=True)
    args = parser.parse_args()

    base = args.base_url
    print("=" * 60)
    print("  P3-1 CI Quality Gate")
    print("=" * 60)

    # 1. Wait for backend
    print(f"\n[1/5] 检查后端: {base}")
    if not wait_backend(base):
        print("  ❌ 后端不可用")
        sys.exit(2)
    print("  ✅ 后端就绪")

    # 2. Load gate config
    print(f"\n[2/5] 加载门禁配置")
    gate_config = load_gate_config(args.gate_config)
    print(f"  配置: {json.dumps(gate_config, ensure_ascii=False)}")

    # 3. Find suite
    print(f"\n[3/5] 查找测试集")
    if not args.suite_id and not args.suite_type:
        print("  ❌ 必须指定 --suite-id 或 --suite-type")
        sys.exit(2)
    suite = find_suite(base, args.suite_id, args.suite_type, args.project_id)
    if not suite:
        print(f"  ❌ 未找到测试集 (id={args.suite_id}, type={args.suite_type})")
        sys.exit(2)
    suite_id = suite.get("id") or suite.get("suite_id")
    suite_name = suite.get("name", "unknown")
    print(f"  ✅ 测试集: {suite_name} (id={suite_id}, type={suite.get('suite_type')})")

    # 4. Execute suite
    print(f"\n[4/5] 执行测试集 (app_mode={args.app_mode})")
    start = time.time()
    result, err = run_suite(base, suite_id, args.app_mode)
    duration = round(time.time() - start, 1)
    if err:
        print(f"  ❌ {err}")
        sys.exit(2)
    run_id = result.get("run_id")
    suite_summary = result.get("suite_summary", {})
    print(f"  ✅ 执行完成 run_id={run_id} ({duration}s)")
    print(f"  总计: {suite_summary.get('total_cases', 0)}  "
          f"通过: {suite_summary.get('passed_cases', 0)}  "
          f"失败: {suite_summary.get('failed_cases', 0)}  "
          f"跳过: {suite_summary.get('skipped_cases', 0)}")

    # 5. Evaluate gate
    print(f"\n[5/5] 评估质量门禁")
    gate_result, err = evaluate_gate(base, run_id, gate_config)
    if err:
        print(f"  ❌ {err}")
        sys.exit(2)

    gate_status = gate_result.get("gate_status", "error")
    gate_failures = gate_result.get("gate_failures", [])
    gate_warnings = gate_result.get("gate_warnings", [])

    if gate_status == "passed":
        print(f"  ✅ 质量门禁: PASSED")
    else:
        print(f"  ❌ 质量门禁: FAILED")
        for f in gate_failures:
            print(f"    🚫 [{f['rule']}] {f['message']}")

    if gate_warnings:
        for w in gate_warnings:
            print(f"    ⚠️  [{w['rule']}] {w['message']}")

    # Output JSON
    final_result = {
        "gate_status": gate_status,
        "run_id": run_id,
        "suite_id": suite_id,
        "suite_name": suite_name,
        "suite_summary": suite_summary,
        "gate_failures": gate_failures,
        "gate_warnings": gate_warnings,
        "gate_config": gate_config,
        "duration_s": duration,
    }

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(final_result, f, ensure_ascii=False, indent=2)
        print(f"\n📄 结果已保存: {args.output}")

    # Summary
    print(f"\n{'=' * 60}")
    print(f"  Gate: {gate_status.upper()}  |  Run: {run_id}  |  Duration: {duration}s")
    print(f"{'=' * 60}")

    if gate_status == "failed" and args.fail_on_gate_failed:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
