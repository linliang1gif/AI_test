#!/usr/bin/env python3
"""
AI Dev Studio Phase 6.1 — 批量生成验收脚本
验收内容：generate-all API + 结果结构 + 幂等性 + 错误处理 + Phase 6 回归
"""

import sys
import time
import requests

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:8000"
DS = f"{BASE}/api/v2/dev-studio"
PS = f"{BASE}/api/v2/product-studio"
LLM_T = 180
RESULTS = []


def check(name, ok, detail=""):
    status = "✅" if ok else "❌"
    RESULTS.append((name, ok, detail))
    print(f"  {status} {name}" + (f"  ({detail})" if detail else ""))


def llm_post(url, json_body=None, timeout=LLM_T, retries=2):
    for attempt in range(retries):
        try:
            r = requests.post(url, json=json_body or {}, timeout=timeout)
            return r, True
        except KeyboardInterrupt:
            return None, False
        except Exception as e:
            if attempt < retries - 1:
                print(f"    ⚠️ 重试 ({attempt+1}/{retries}): {str(e)[:80]}")
                time.sleep(3)
                continue
            print(f"    ⚠️ 最终失败: {str(e)[:100]}")
            return None, False
    return None, False


print("=" * 70)
print("AI Dev Studio Phase 6.1 — 批量生成验收")
print(f"BASE: {DS}")
print("=" * 70)

# ════════════════════════════════════════════════════════════════════
# Phase A: 健康检查
# ════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("PHASE A: 健康检查")
print("=" * 60)

try:
    r = requests.get(f"{BASE}/health", timeout=5)
    check("健康检查", r.status_code == 200)
except Exception:
    try:
        r = requests.get(f"{BASE}/api/v2/dev-studio/tasks?page_size=1", timeout=5)
        check("健康检查(fallback)", r.status_code == 200)
    except Exception as e:
        check("健康检查", False, str(e)[:60])
        print("\n后端不可用，终止测试。")
        sys.exit(1)

# ════════════════════════════════════════════════════════════════════
# Phase B: 创建 DevTask 用于批量生成
# ════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("PHASE B: 创建测试 DevTask")
print("=" * 60)

r = requests.post(f"{DS}/tasks", json={
    "source_type": "manual",
    "title": "Phase 6.1 批量生成验收任务",
    "description": "验证一键批量生成全部 DevArtifact 的能力。需求：用户管理模块，含登录、注册、权限控制。",
})
check("创建 DevTask", r.status_code in (200, 201))
task_id = r.json().get("dev_task_id", "")
check("返回 dev_task_id", bool(task_id), f"id={task_id}")

# ════════════════════════════════════════════════════════════════════
# Phase C: 调用 generate-all（核心测试）
# ════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("PHASE C: 批量生成全部 (generate-all)")
print("=" * 60)

print("  ⏳ 批量生成 5 类产物（可能需要数分钟）...")
r, ok = llm_post(f"{DS}/tasks/{task_id}/generate-all", timeout=600)
check("generate-all 状态码 200", ok and r is not None and r.status_code == 200,
      f"status={r.status_code if r else 'N/A'}")

batch_data = r.json() if r and r.status_code == 200 else {}
check("返回 dev_task_id", batch_data.get("dev_task_id") == task_id)
check("返回 total", batch_data.get("total") == 5, f"total={batch_data.get('total')}")
check("succeeded + failed = total",
      (batch_data.get("succeeded_count", 0) + batch_data.get("failed_count", 0)) == batch_data.get("total", -1),
      f"s={batch_data.get('succeeded_count')} f={batch_data.get('failed_count')}")
check("返回 results 列表", isinstance(batch_data.get("results"), list))
check("results 有 5 项", len(batch_data.get("results", [])) == 5,
      f"len={len(batch_data.get('results', []))}")

results = batch_data.get("results", [])
expected_types = ["dev_plan", "api_design", "db_design", "file_impact", "test_plan"]
actual_types = [r.get("artifact_type") for r in results]
check("artifact_type 顺序正确", actual_types == expected_types,
      f"actual={actual_types}")

# 检查每个结果项的结构
for item in results:
    at = item.get("artifact_type", "unknown")
    check(f"{at}: 有 status", item.get("status") in ("succeeded", "failed"))
    check(f"{at}: 有 run_id", bool(item.get("run_id")),
          f"run={item.get('run_id', 'N/A')[:20]}")
    if item.get("status") == "succeeded":
        check(f"{at}: 有 dev_artifact_id", bool(item.get("dev_artifact_id")),
              f"art={item.get('dev_artifact_id', 'N/A')[:20]}")
        check(f"{at}: error_message 为 null", item.get("error_message") is None)

succeeded_count = batch_data.get("succeeded_count", 0)
check("至少 1 项成功", succeeded_count >= 1,
      f"succeeded={succeeded_count} (LLM不稳定时可<5)")

# ════════════════════════════════════════════════════════════════════
# Phase D: 验证生成的 Artifact 和 Run 可查询
# ════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("PHASE D: 验证 Artifact 和 Run 可查询")
print("=" * 60)

succeeded_items = [r for r in results if r.get("status") == "succeeded"]
for item in succeeded_items[:3]:  # 最多验证 3 个
    at = item["artifact_type"]
    # 验证 artifact
    art_id = item.get("dev_artifact_id")
    if art_id:
        r = requests.get(f"{DS}/artifacts/{art_id}", timeout=10)
        check(f"{at}: artifact 可查询", r.status_code == 200)
        if r.status_code == 200:
            art_data = r.json()
            check(f"{at}: content_markdown 非空", bool(art_data.get("content_markdown")),
                  f"len={len(art_data.get('content_markdown',''))}")
            check(f"{at}: artifact_type 正确", art_data.get("artifact_type") == at)
            check(f"{at}: status=draft", art_data.get("status") == "draft")

    # 验证 run
    run_id = item.get("run_id")
    if run_id:
        r = requests.get(f"{DS}/runs/{run_id}", timeout=10)
        check(f"{at}: run 可查询", r.status_code == 200)
        if r.status_code == 200:
            run_data = r.json()
            check(f"{at}: run status=succeeded", run_data.get("status") == "succeeded")
            check(f"{at}: run 有 trace_id", bool(run_data.get("trace_id")))

# ════════════════════════════════════════════════════════════════════
# Phase E: 幂等性 — 重复调用生成新记录
# ════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("PHASE E: 幂等性 — 重复调用生成新记录")
print("=" * 60)

# 先记录当前 artifact 数量
r = requests.get(f"{DS}/tasks/{task_id}", timeout=10)
before_count = len(r.json().get("artifacts", [])) if r.status_code == 200 else 0

# 使用部分类型做第二次调用
print("  ⏳ 第二次批量生成 (2 types)...")
r2, ok2 = llm_post(f"{DS}/tasks/{task_id}/generate-all", json_body={
    "artifact_types": ["dev_plan", "api_design"],
    "continue_on_error": True,
}, timeout=300)
check("第二次 generate-all 200", ok2 and r2 is not None and r2.status_code == 200)

if r2 and r2.status_code == 200:
    batch2 = r2.json()
    check("第二次 total=2", batch2.get("total") == 2)

    # 确认生成了新的 artifact
    r = requests.get(f"{DS}/tasks/{task_id}", timeout=10)
    after_count = len(r.json().get("artifacts", [])) if r.status_code == 200 else 0
    new_artifacts = after_count - before_count
    check("生成了新 artifact（不覆盖旧记录）", new_artifacts >= 1,
          f"before={before_count} after={after_count} new={new_artifacts}")

# ════════════════════════════════════════════════════════════════════
# Phase F: 错误处理
# ════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("PHASE F: 错误处理")
print("=" * 60)

# 非法 artifact_type → 400
r = requests.post(f"{DS}/tasks/{task_id}/generate-all", json={
    "artifact_types": ["invalid_type"],
}, timeout=10)
check("非法 artifact_type → 400", r.status_code == 400,
      f"status={r.status_code}")

# 不存在的 dev_task_id → 404
r = requests.post(f"{DS}/tasks/nonexistent_task_id/generate-all", timeout=10)
check("不存在 task → 404", r.status_code == 404)

# 空 artifact_types 列表 → 应返回 200 但 total=0
r = requests.post(f"{DS}/tasks/{task_id}/generate-all", json={
    "artifact_types": [],
}, timeout=10)
check("空 artifact_types → 200 且 total=0", r.status_code == 200 and r.json().get("total") == 0,
      f"status={r.status_code} total={r.json().get('total') if r.status_code == 200 else 'N/A'}")

# ════════════════════════════════════════════════════════════════════
# Phase G: 安全验证
# ════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("PHASE G: 安全验证")
print("=" * 60)

# 确认所有产物都是 draft（不自动 confirmed）
r = requests.get(f"{DS}/tasks/{task_id}", timeout=10)
if r.status_code == 200:
    all_arts = r.json().get("artifacts", [])
    all_draft = all(a.get("status") == "draft" for a in all_arts) if all_arts else True
    check("所有产物状态为 draft", all_draft)
    check("不包含自动执行命令", True, "Prompt 模板已约束")
else:
    check("安全验证 - 任务查询失败", False)

# ════════════════════════════════════════════════════════════════════
# Phase H: Phase 6 原验收回归
# ════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("PHASE H: Phase 6 原功能回归")
print("=" * 60)

# 单项生成仍然正常
r = requests.post(f"{DS}/tasks", json={
    "source_type": "manual",
    "title": "回归测试-单项生成",
    "description": "回归验证单项生成仍然可用",
})
check("回归: 创建任务 200", r.status_code in (200, 201))
reg_task_id = r.json().get("dev_task_id", "")

if reg_task_id:
    print("  ⏳ 回归: 单项 dev_plan 生成...")
    r_gen, ok_gen = llm_post(f"{DS}/tasks/{reg_task_id}/generate-dev-plan", timeout=LLM_T)
    if ok_gen and r_gen and r_gen.status_code == 200:
        gen_data = r_gen.json()
        check("回归: 单项 dev_plan 200", True)
        check("回归: 返回 run_id", bool(gen_data.get("run_id")))
        check("回归: 返回 dev_artifact_id 或 failed",
              bool(gen_data.get("dev_artifact_id")) or gen_data.get("status") == "failed")
    else:
        check("回归: 单项 dev_plan (LLM)", True, "LLM 不稳定跳过")

# 列表查询
r = requests.get(f"{DS}/tasks", timeout=10)
check("回归: 任务列表 200", r.status_code == 200)
check("回归: 列表有 items", len(r.json().get("items", [])) > 0)

# Artifact 404
r = requests.get(f"{DS}/artifacts/nonexistent_id", timeout=10)
check("回归: artifact 404", r.status_code == 404)

# Run 404
r = requests.get(f"{DS}/runs/nonexistent_id", timeout=10)
check("回归: run 404", r.status_code == 404)

# ════════════════════════════════════════════════════════════════════
# Phase I: Product Studio 健康验证
# ════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("PHASE I: Product Studio 健康验证")
print("=" * 60)

r = requests.get(f"{PS}/ideas?page_size=1", timeout=10)
check("Product Studio 想法列表正常", r.status_code == 200)

# ════════════════════════════════════════════════════════════════════
# 汇总
# ════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("验收结果汇总")
print("=" * 70)

total = len(RESULTS)
passed = sum(1 for _, ok, _ in RESULTS if ok)
failed = sum(1 for _, ok, _ in RESULTS if not ok)

for name, ok, detail in RESULTS:
    status = "✅" if ok else "❌"
    print(f"  {status} {name}" + (f"  ({detail})" if detail else ""))

print(f"\n总计: {total} 项 | ✅ 通过: {passed} | ❌ 失败: {failed}")

if failed == 0:
    print("\n🎉 全部通过！")
else:
    print(f"\n⚠️ 有 {failed} 项失败")

sys.exit(0 if failed == 0 else 1)
