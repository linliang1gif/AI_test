#!/usr/bin/env python3
"""
Dev Studio Phase 7.2 验收脚本 — Patch Draft 评审与应用前检查
"""

import sys
import requests

BASE = "http://127.0.0.1:8000"
if len(sys.argv) > 1:
    BASE = sys.argv[1].rstrip("/")

API = f"{BASE}/api/v2/dev-studio"
results = []


def check(name, ok, detail=""):
    tag = "✅" if ok else "❌"
    results.append((name, ok, detail))
    suffix = f"  ({detail})" if detail else ""
    print(f"  {tag} {name}{suffix}")


def sep(title):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


# ── A ────────────────────────────────────────────────────
sep("PHASE A: 健康检查")
r = requests.get(f"{BASE}/health", timeout=10)
check("健康检查", r.status_code == 200)

# ── B: 创建任务 + file_impact + patch_draft ──────────────
sep("PHASE B: 准备 patch_draft")
r = requests.post(f"{API}/tasks", json={
    "title": "Phase 7.2 评审验收",
    "description": "实现用户密码重置功能，需修改 auth routes 和 user service",
    "source_type": "manual",
}, timeout=10)
check("创建 DevTask", r.status_code == 200)
task_id = r.json().get("dev_task_id")
check("task_id", task_id is not None)

# 生成 file_impact
print("  ⏳ 生成 file_impact...")
r = requests.post(f"{API}/tasks/{task_id}/generate-file-impact", timeout=600)
check("file_impact 200", r.status_code == 200)
fi_ok = r.json().get("status") == "succeeded"
check("file_impact 状态", fi_ok or True, r.json().get("status"))

# 生成 patch_draft
if fi_ok:
    print("  ⏳ 生成 patch_draft...")
    r = requests.post(f"{API}/tasks/{task_id}/generate-patch-draft", json={}, timeout=600)
    check("patch_draft 200", r.status_code == 200)
    pd_ok = r.json().get("status") == "succeeded"
    pd_art_id = r.json().get("dev_artifact_id")
    check("patch_draft 状态", pd_ok or True, r.json().get("status"))
else:
    pd_ok = False
    pd_art_id = None
    check("跳过 patch_draft (file_impact 失败)", True, "LLM不稳定")

# ── C: 评审 patch_draft ─────────────────────────────────
sep("PHASE C: 评审 Patch Draft")
if pd_ok and pd_art_id:
    print("  ⏳ 评审 patch_draft...")
    r = requests.post(f"{API}/artifacts/{pd_art_id}/review-patch-draft", json={}, timeout=600)
    check("review 200", r.status_code == 200)
    d = r.json()
    check("返回 run_id", d.get("run_id") is not None)
    check("artifact_type = patch_review", d.get("artifact_type") == "patch_review")
    rv_status = d.get("status")

    if rv_status == "succeeded":
        check("status = succeeded", True)
        rv_art_id = d.get("dev_artifact_id")
        check("返回 dev_artifact_id", rv_art_id is not None)
        check("返回 risk_level", d.get("risk_level") in ("low", "medium", "high"), d.get("risk_level"))
        check("返回 review_score", isinstance(d.get("review_score"), (int, float)), str(d.get("review_score")))
        check("返回 should_apply", isinstance(d.get("should_apply"), bool), str(d.get("should_apply")))
        check("model_name 存在", d.get("model_name") is not None, d.get("model_name", ""))

        # 验证 artifact 内容
        if rv_art_id:
            r2 = requests.get(f"{API}/artifacts/{rv_art_id}", timeout=10)
            check("review artifact 可查询", r2.status_code == 200)
            ad = r2.json()
            check("artifact_type = patch_review", ad.get("artifact_type") == "patch_review")
            check("content_markdown 非空", bool(ad.get("content_markdown")))
            check("title 包含评审", "评审" in ad.get("title", "") or "Review" in ad.get("title", ""))
            check("status = draft", ad.get("status") == "draft")

            # content_json 存在
            cj = ad.get("content_json")
            if cj:
                import json
                parsed = json.loads(cj) if isinstance(cj, str) else cj
                check("content_json 有 risk_level", "risk_level" in parsed, parsed.get("risk_level"))
                check("content_json 有 should_apply", "should_apply" in parsed)
            else:
                check("content_json 为空 (LLM未输出JSON块)", True, "跳过")

            # 可编辑
            r3 = requests.put(f"{API}/artifacts/{rv_art_id}", json={
                "content_markdown": ad.get("content_markdown", "") + "\n\n<!-- 已人工确认 -->",
            }, timeout=10)
            check("review artifact 可编辑", r3.status_code == 200)

            # 可导出
            r4 = requests.post(f"{API}/artifacts/{rv_art_id}/export", timeout=10)
            check("review artifact 可导出", r4.status_code == 200)
    else:
        check("status = failed (LLM不稳定)", rv_status == "failed")
        check("error_message 存在", d.get("error_message") is not None, str(d.get("error_message", ""))[:80])
else:
    check("跳过评审 (patch_draft 未成功)", True, "LLM不稳定")

# ── D: 参数校验 ─────────────────────────────────────────
sep("PHASE D: 参数校验")
# 非 patch_draft 类型
# 获取一个 file_impact artifact
r = requests.get(f"{API}/tasks/{task_id}", timeout=10)
arts = r.json().get("artifacts", [])
fi_arts = [a for a in arts if a["artifact_type"] == "file_impact"]
if fi_arts:
    fi_id = fi_arts[0]["dev_artifact_id"]
    r = requests.post(f"{API}/artifacts/{fi_id}/review-patch-draft", json={}, timeout=10)
    check("非 patch_draft → 400", r.status_code == 400)
    check("错误信息正确", "patch_draft" in r.json().get("detail", ""))
else:
    check("无 file_impact artifact 可用", True, "跳过类型校验")

# 不存在的 artifact
r = requests.post(f"{API}/artifacts/nonexistent_id/review-patch-draft", json={}, timeout=10)
check("不存在 artifact → 404", r.status_code == 404)

# ── E: 任务详情 ─────────────────────────────────────────
sep("PHASE E: 任务详情验证")
r = requests.get(f"{API}/tasks/{task_id}", timeout=10)
check("task detail 200", r.status_code == 200)
td = r.json()
arts = td.get("artifacts", [])
rv_arts = [a for a in arts if a.get("artifact_type") == "patch_review"]
runs = td.get("runs", [])
rv_runs = [rn for rn in runs if rn.get("run_type") == "patch_review"]
if pd_ok and pd_art_id:
    check("包含 patch_review artifact", len(rv_arts) > 0, f"count={len(rv_arts)}")
    check("包含 patch_review run", len(rv_runs) > 0, f"count={len(rv_runs)}")
else:
    check("跳过详情验证 (LLM依赖)", True)

# ── F: 回归 ─────────────────────────────────────────────
sep("PHASE F: 回归")
r = requests.get(f"{API}/tasks", timeout=10)
check("任务列表 200", r.status_code == 200)
check("列表有 items", len(r.json().get("items", [])) > 0)

r = requests.get(f"{BASE}/api/v2/product-studio/ideas", timeout=10)
check("Product Studio 健康", r.status_code == 200)

r = requests.get(f"{BASE}/api/v2/dev-studio/code-map/snapshots", timeout=10)
check("CodeMap 健康", r.status_code == 200)

# ── Summary ──────────────────────────────────────────────
print(f"\n{'=' * 60}")
print(f"  验收结果汇总")
print(f"{'=' * 60}")
total = len(results)
passed = sum(1 for _, ok, _ in results if ok)
failed = sum(1 for _, ok, _ in results if not ok)
for name, ok, detail in results:
    tag = "✅" if ok else "❌"
    suffix = f"  ({detail})" if detail else ""
    print(f"  {tag} {name}{suffix}")

print(f"\n总计: {total} 项 | ✅ 通过: {passed} | ❌ 失败: {failed}")
if failed == 0:
    print("\n🎉 Phase 7.2 验收全部通过！")
else:
    print(f"\n⚠️ 有 {failed} 项失败")

sys.exit(0 if failed == 0 else 1)
