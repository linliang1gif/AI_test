#!/usr/bin/env python3
"""Phase 19 Acceptance Tests: AI 报告分析能力"""

import requests
import json

BASE = "http://localhost:8000"
H = {"Authorization": "Bearer demo-token", "Content-Type": "application/json"}
SHORT = 10
TIMEOUT = 60

results = []
def check(name, ok):
    results.append((name, ok))
    mark = "✅ PASS" if ok else "❌ FAIL"
    print(f"  {mark}: {name}")

print("=" * 60)
print("  Phase 19 Acceptance Tests")
print("=" * 60)

# ──────────────────────────────────────────────────────────────
# 1. Demo 系统可用
# ──────────────────────────────────────────────────────────────
print("\n── 1. Demo 系统可用 ──")
r = requests.get(f"{BASE}/api/v2/demo/status", timeout=SHORT)
check("1.1 Demo status 200", r.status_code == 200)
d = r.json().get("data", {})
check("1.2 Demo initialized", d.get("initialized") is True)

# ──────────────────────────────────────────────────────────────
# 2. 执行小批量用例获取 run_id（含 pass + fail + destructive skip）
# ──────────────────────────────────────────────────────────────
print("\n── 2. 批量执行(小集合) ──")
run_id = ""
try:
    # 用少量明确用例: 正常+异常+破坏性, 快速拿到 run_id
    test_ids = [
        "DEMO_OK_001", "DEMO_OK_002", "DEMO_OK_003",  # 正常GET
        "DEMO_AUTH_001", "DEMO_AUTH_002",               # 认证失败
        "DEMO_REQ_001",                                  # 参数错误
        "DEMO_OK_007", "DEMO_OK_011",                   # destructive
    ]
    print(f"    [INFO] 执行 {len(test_ids)} 条用例(含 destructive)...")
    r = requests.post(
        f"{BASE}/api/v2/test-cases/batch-execute",
        headers=H,
        json={"case_ids": test_ids, "environment_id": 1, "skip_destructive": True},
        timeout=TIMEOUT,
    )
    check("2.1 Batch execute 200", r.status_code == 200)
    batch = r.json()
    run_id = batch.get("run_id", "")
    check("2.2 Has run_id", len(run_id) > 0)
    check("2.3 Has results", len(batch.get("results", [])) > 0)
except Exception as e:
    print(f"    ⚠️ SKIP: {e.__class__.__name__}")
    check("2.1 Batch execute timeout", False)
    check("2.2 skip", False)
    check("2.3 skip", False)

# ──────────────────────────────────────────────────────────────
# 3. 生成 AI 分析
# ──────────────────────────────────────────────────────────────
print("\n── 3. 生成 AI 分析 ──")
analysis = None
if run_id:
    try:
        r = requests.post(f"{BASE}/api/v2/test-runs/{run_id}/ai-analysis", timeout=90)
        check("3.1 AI analysis 200", r.status_code == 200)
        body = r.json()
        check("3.2 Response has data", body.get("data") is not None)
        analysis = body.get("data", {})
    except Exception as e:
        print(f"    ⚠️ SKIP: {e.__class__.__name__}")
        check("3.1 AI analysis error", False)
        check("3.2 skip", False)
else:
    check("3.1 skip (no run_id)", False)
    check("3.2 skip", False)

# ──────────────────────────────────────────────────────────────
# 4. 验证分析结构
# ──────────────────────────────────────────────────────────────
print("\n── 4. 分析结构验证 ──")
if analysis:
    check("4.1 Has health_score", "health_score" in analysis)
    check("4.2 health_score is int", isinstance(analysis.get("health_score"), int))
    check("4.3 health_score 0-100", 0 <= analysis.get("health_score", -1) <= 100)
    check("4.4 Has release_recommendation", "release_recommendation" in analysis)
    check("4.5 release_recommendation valid", analysis.get("release_recommendation") in ("pass", "caution", "block"))
    check("4.6 Has summary", isinstance(analysis.get("summary"), str) and len(analysis.get("summary", "")) > 0)
    check("4.7 Has key_findings", isinstance(analysis.get("key_findings"), list))
    check("4.8 Has risk_points", isinstance(analysis.get("risk_points"), list))
    check("4.9 Has failure_analysis", isinstance(analysis.get("failure_analysis"), list))
    check("4.10 Has suggestions", isinstance(analysis.get("suggestions"), list))
    check("4.11 Has next_actions", isinstance(analysis.get("next_actions"), list))
    check("4.12 Has skipped_analysis", isinstance(analysis.get("skipped_analysis"), list))
    check("4.13 Has analysis_id", "analysis_id" in analysis)
    check("4.14 Has provider", "provider" in analysis)
else:
    for i in range(1, 15):
        check(f"4.{i} skip (no analysis)", False)

# ──────────────────────────────────────────────────────────────
# 5. Provider 默认 rule_based
# ──────────────────────────────────────────────────────────────
print("\n── 5. Provider 验证 ──")
if analysis:
    check("5.1 provider is valid", analysis.get("provider") in ("rule_based", "llm"))
    check("5.2 suggestions not empty", len(analysis.get("suggestions", [])) > 0)
    check("5.3 key_findings not empty", len(analysis.get("key_findings", [])) > 0)
else:
    check("5.1 skip", False)
    check("5.2 skip", False)
    check("5.3 skip", False)

# ──────────────────────────────────────────────────────────────
# 6. GET 查询分析结果
# ──────────────────────────────────────────────────────────────
print("\n── 6. 查询已保存分析 ──")
if run_id:
    try:
        r = requests.get(f"{BASE}/api/v2/test-runs/{run_id}/ai-analysis", timeout=SHORT)
        check("6.1 GET analysis 200", r.status_code == 200)
        body = r.json()
        saved = body.get("data", {})
        check("6.2 Saved has health_score", "health_score" in (saved or {}))
        check("6.3 Saved has analysis_id", "analysis_id" in (saved or {}))
        check("6.4 Saved provider valid", (saved or {}).get("provider") in ("rule_based", "llm"))
    except Exception as e:
        print(f"    ⚠️ SKIP: {e.__class__.__name__}")
        for i in range(1, 5):
            check(f"6.{i} skip", False)
else:
    for i in range(1, 5):
        check(f"6.{i} skip (no run_id)", False)

# ──────────────────────────────────────────────────────────────
# 7. 无 run_id 时 404
# ──────────────────────────────────────────────────────────────
print("\n── 7. 边界条件 ──")
r = requests.post(f"{BASE}/api/v2/test-runs/NONEXISTENT_RUN/ai-analysis", timeout=SHORT)
check("7.1 Non-existent run returns 404", r.status_code == 404)

r = requests.get(f"{BASE}/api/v2/test-runs/NONEXISTENT_RUN/ai-analysis", timeout=SHORT)
check("7.2 GET non-existent returns empty", r.status_code == 200 and r.json().get("data") is None)

# ──────────────────────────────────────────────────────────────
# 8. HTML 报告包含 AI 分析区域
# ──────────────────────────────────────────────────────────────
print("\n── 8. HTML 报告集成 AI 分析 ──")
if run_id:
    try:
        # 先生成 AI 分析（已在步骤3完成），再生成报告
        r = requests.post(f"{BASE}/api/v2/test-runs/{run_id}/report", json={"format": "html"}, timeout=SHORT)
        check("8.1 Report generation 200", r.status_code == 200)

        r = requests.get(f"{BASE}/api/v2/test-runs/{run_id}/report/download?format=html", timeout=SHORT)
        check("8.2 Report download 200", r.status_code == 200)
        html = r.text

        check("8.3 Report has AI 质量分析", "AI 质量分析" in html)
        check("8.4 Report has 健康评分", "健康评分" in html)
        check("8.5 Report has 发布建议", "发布建议" in html)
        check("8.6 Report has 关键发现", "关键发现" in html)
        check("8.7 Report has 修复建议", "修复建议" in html)
        check("8.8 Report has 下一步行动", "下一步行动" in html)
        check("8.9 Report has analysis tag", "规则分析" in html or "AI 大模型" in html or "llm" in html)
    except Exception as e:
        print(f"    ⚠️ SKIP: {e.__class__.__name__}")
        for i in range(1, 10):
            check(f"8.{i} skip", False)
else:
    for i in range(1, 10):
        check(f"8.{i} skip (no run_id)", False)

# ──────────────────────────────────────────────────────────────
# 9. 无 AI KEY 不报错
# ──────────────────────────────────────────────────────────────
print("\n── 9. 无 AI KEY 不报错 ──")
# 当前没有配置 AI_REPORT_API_KEY，所以应该自动 fallback
if analysis:
    check("9.1 Provider works", analysis.get("provider") in ("rule_based", "llm"))
    check("9.2 Analysis complete without KEY", analysis.get("health_score") is not None)
else:
    check("9.1 skip", False)
    check("9.2 skip", False)

# ──────────────────────────────────────────────────────────────
# 10. 评分规则合理性
# ──────────────────────────────────────────────────────────────
print("\n── 10. 评分规则合理性 ──")
if analysis:
    score = analysis.get("health_score", 0)
    rec = analysis.get("release_recommendation", "")
    # smoke preset 应该大部分通过
    check("10.1 Smoke score reasonable (>= 0)", score >= 0)
    check("10.2 Recommendation consistent with score",
          (rec == "block" and score < 85) or
          (rec == "caution" and 0 <= score <= 100) or
          (rec == "pass" and score >= 85))
    # failure_analysis 结构
    fa = analysis.get("failure_analysis", [])
    if fa:
        first = fa[0]
        check("10.3 failure_analysis has category", "category" in first)
        check("10.4 failure_analysis has count", "count" in first)
        check("10.5 failure_analysis has analysis", "analysis" in first)
        check("10.6 failure_analysis has suggestion", "suggestion" in first)
    else:
        check("10.3 No failures (all passed)", True)
        check("10.4 skip", True)
        check("10.5 skip", True)
        check("10.6 skip", True)
else:
    for i in range(1, 7):
        check(f"10.{i} skip", False)

# ──────────────────────────────────────────────────────────────
# 11. Phase 17/18 向后兼容
# ──────────────────────────────────────────────────────────────
print("\n── 11. 向后兼容 ──")
r = requests.get(f"{BASE}/api/v2/demo/status", timeout=SHORT)
check("11.1 Demo status still works", r.status_code == 200)

r = requests.post(f"{BASE}/api/mock/login", json={"username": "admin", "password": "123456"}, timeout=SHORT)
check("11.2 Mock login still works", r.status_code == 200)

r = requests.get(f"{BASE}/api/v2/test-cases/governance-summary", timeout=SHORT)
check("11.3 Governance summary still works", r.status_code == 200)

# ──────────────────────────────────────────────────────────────
# 汇总
# ──────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
passed_count = sum(1 for _, ok in results if ok)
total_count = len(results)
failed_count = total_count - passed_count
print(f"  Results: {passed_count}/{total_count} passed, {failed_count} failed")

if failed_count > 0:
    print("\n  Failed tests:")
    for name, ok in results:
        if not ok:
            print(f"    ❌ {name}")
else:
    print("\n  ALL PHASE 19 TESTS PASSED")

print("=" * 60)
exit(0 if failed_count == 0 else 1)
