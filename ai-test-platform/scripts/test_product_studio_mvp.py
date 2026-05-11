#!/usr/bin/env python3
"""
AI Product Studio MVP — 最小验收脚本
用法: python scripts/test_product_studio_mvp.py [BASE_URL]
默认 BASE_URL = http://127.0.0.1:8000
"""

import sys
import json
import requests
import time

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
API = f"{BASE}/api/v2/product-studio"
PASS = 0
FAIL = 0
RESULTS = []


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        RESULTS.append(f"  ✅ {name}")
    else:
        FAIL += 1
        RESULTS.append(f"  ❌ {name} — {detail}")


def main():
    global PASS, FAIL
    print("=" * 60)
    print("AI Product Studio MVP 验收测试")
    print(f"BASE: {API}")
    print("=" * 60)

    # 1. 创建产品想法
    print("\n[1] 创建产品想法")
    r = requests.post(f"{API}/ideas", json={
        "title": "MVP验收测试产品",
        "product_direction": "SaaS内部工具",
        "target_users": "测试工程师",
        "pain_points": "手动回归太慢",
        "existing_assets": "已有CI/CD",
        "current_blockers": "无自动化框架",
        "constraints": "3人团队/2周交付",
    })
    check("创建想法 status=200", r.status_code == 200, f"status={r.status_code}")
    data = r.json()
    idea_id = data.get("idea_id", "")
    check("创建想法返回 idea_id", bool(idea_id), f"data={data}")
    check("创建想法 status=created", data.get("status") == "created")

    # 2. 查询列表
    print("\n[2] 查询想法列表")
    r = requests.get(f"{API}/ideas", params={"keyword": "MVP验收"})
    check("列表 status=200", r.status_code == 200)
    items = r.json().get("items", [])
    check("列表包含刚创建的想法", any(i["idea_id"] == idea_id for i in items))

    # 3. 查询详情
    print("\n[3] 查询想法详情")
    r = requests.get(f"{API}/ideas/{idea_id}")
    check("详情 status=200", r.status_code == 200)
    detail = r.json()
    check("详情包含 title", detail.get("title") == "MVP验收测试产品")
    check("详情包含 artifact_summary", "artifact_summary" in detail)
    check("详情 has_solution=false", detail.get("artifact_summary", {}).get("has_solution") == False)

    # 4-8. 五次生成
    gen_types = [
        ("product_solution", "generate-solution", "产品方案"),
        ("prd", "generate-prd", "PRD"),
        ("prototype", "generate-prototype", "原型说明"),
        ("test_strategy", "generate-test-strategy", "测试策略"),
        ("acceptance_criteria", "generate-acceptance-criteria", "验收标准"),
    ]

    artifact_ids = []
    for run_type, endpoint, label in gen_types:
        print(f"\n[{4 + gen_types.index((run_type, endpoint, label))}] 生成{label}")
        r = requests.post(f"{API}/ideas/{idea_id}/{endpoint}", json={})
        check(f"生成{label} status=200", r.status_code == 200)
        gdata = r.json()
        check(f"生成{label} 有 run_id", bool(gdata.get("run_id")))
        check(f"生成{label} 有 trace_id", bool(gdata.get("trace_id")))
        status = gdata.get("status")
        check(f"生成{label} status=succeeded/failed", status in ("succeeded", "failed"), f"status={status}")
        if status == "succeeded":
            art_id = gdata.get("artifact_id")
            check(f"生成{label} 有 artifact_id", bool(art_id))
            artifact_ids.append(art_id)
        else:
            check(f"生成{label} 失败有 error_message", bool(gdata.get("error_message")))
            print(f"    ⚠️ {label} 生成失败(可能 mock/无 LLM Key): {gdata.get('error_message', '')[:100]}")

    # 9. 查询 Artifact
    print("\n[9] 查询 Artifact")
    if artifact_ids:
        r = requests.get(f"{API}/artifacts/{artifact_ids[0]}")
        check("查询 Artifact status=200", r.status_code == 200)
        art = r.json()
        check("Artifact 有 content_markdown", bool(art.get("content_markdown")))
        check("Artifact 内容不为空", len(art.get("content_markdown", "")) > 10)
    else:
        check("查询 Artifact (跳过: 无成功生成)", False, "所有生成均失败")

    # 10. 更新 Artifact
    print("\n[10] 更新 Artifact")
    if artifact_ids:
        r = requests.put(f"{API}/artifacts/{artifact_ids[0]}", json={
            "title": "更新后的标题",
            "content_markdown": "# 更新后的内容\n\n测试编辑保存功能。",
        })
        check("更新 Artifact status=200", r.status_code == 200)
        check("更新后 title 正确", r.json().get("title") == "更新后的标题")
    else:
        check("更新 Artifact (跳过)", False, "无 artifact")

    # 11. 查询 Run
    print("\n[11] 查询 Run")
    r = requests.get(f"{API}/ideas/{idea_id}")
    runs = r.json().get("runs", [])
    check("详情包含 runs", len(runs) > 0)
    if runs:
        run_id = runs[0]["run_id"]
        r2 = requests.get(f"{API}/runs/{run_id}")
        check("查询 Run status=200", r2.status_code == 200)
        run = r2.json()
        check("Run 有 trace_id", bool(run.get("trace_id")))
        check("Run 有 model_name", run.get("model_name") is not None)

    # 12. LLM 失败不崩溃 — 用不存在的 idea
    print("\n[12] 异常: 不存在的 idea")
    r = requests.post(f"{API}/ideas/nonexistent_id/generate-solution", json={})
    check("不存在 idea 返回 404", r.status_code == 404, f"status={r.status_code}")

    # 12b. 不存在的 artifact / run
    r = requests.get(f"{API}/artifacts/nonexistent_art")
    check("不存在 artifact 返回 404", r.status_code == 404)
    r = requests.get(f"{API}/runs/nonexistent_run")
    check("不存在 run 返回 404", r.status_code == 404)

    # 12c. 空标题创建
    r = requests.post(f"{API}/ideas", json={"title": ""})
    check("空标题返回 400", r.status_code == 400)
    r = requests.post(f"{API}/ideas", json={"title": "   "})
    check("纯空格标题返回 400", r.status_code == 400)

    # 13. artifact_summary 动态计算
    print("\n[13] artifact_summary 正确性")
    r = requests.get(f"{API}/ideas/{idea_id}")
    summary = r.json().get("artifact_summary", {})
    if artifact_ids:
        check("artifact_summary has_solution 正确", summary.get("has_solution") == True)

    # 14. 同一类型多次生成
    print("\n[14] 同类型多次生成")
    r = requests.post(f"{API}/ideas/{idea_id}/generate-solution", json={})
    check("第二次生成 status=200", r.status_code == 200)
    r2 = requests.get(f"{API}/ideas/{idea_id}")
    all_arts = r2.json().get("artifacts", [])
    solution_arts = [a for a in all_arts if a["artifact_type"] == "product_solution"]
    check("同类型可产生多条 Artifact", len(solution_arts) >= 2, f"count={len(solution_arts)}")

    # 15. 不影响现有接口
    print("\n[15] 不影响现有接口")
    r = requests.get(f"{BASE}/health")
    check("健康检查正常", r.status_code == 200)

    # 结果汇总
    print("\n" + "=" * 60)
    print("验收结果汇总")
    print("=" * 60)
    for line in RESULTS:
        print(line)
    print(f"\n总计: {PASS + FAIL} 项 | ✅ 通过: {PASS} | ❌ 失败: {FAIL}")
    if FAIL == 0:
        print("\n🎉 全部通过！")
    else:
        print(f"\n⚠️ {FAIL} 项未通过，请检查。")
    return FAIL


if __name__ == "__main__":
    sys.exit(main())
