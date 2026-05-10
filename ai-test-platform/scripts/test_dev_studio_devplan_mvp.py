#!/usr/bin/env python3
"""
AI Dev Studio Phase 6 — DevPlan MVP 验收脚本
用法: python scripts/test_dev_studio_devplan_mvp.py http://127.0.0.1:8000
"""

import sys, json, time
import requests

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:8000"
DS_API = f"{BASE}/api/v2/dev-studio"
PS_API = f"{BASE}/api/v2/product-studio"
T = 15
LLM_T = 120

results = []


def check(name, cond, note=""):
    results.append((name, cond))
    tag = "✅" if cond else "❌"
    print(f"  {tag} {name}" + (f"  ({note})" if note else ""))


def llm_post(url, json_body=None, timeout=LLM_T, retries=2):
    for attempt in range(retries):
        try:
            r = requests.post(url, json=json_body or {}, timeout=timeout)
            if r.status_code == 200:
                d = r.json()
                if d.get("error_message") and attempt < retries - 1:
                    time.sleep(3)
                    continue
            return r, True
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(3)
                continue
            return None, False
    return None, False


# ══════════════════════════════════════════════════════════════
#  Phase 0: 健康检查
# ══════════════════════════════════════════════════════════════
print("\n[Phase 0] 健康检查")
try:
    r = requests.get(f"{BASE}/health", timeout=T)
    check("health OK", r.status_code == 200)
except Exception:
    check("health OK", False, "后端不可达")
    # 打印结果并退出
    print("\n" + "=" * 60)
    passed = sum(1 for _, c in results if c)
    print(f"总计: {len(results)}  ✅ PASS: {passed}  ❌ FAIL: {len(results) - passed}")
    sys.exit(1)


# ══════════════════════════════════════════════════════════════
#  Phase 1: Task CRUD
# ══════════════════════════════════════════════════════════════
print("\n[Phase 1] Task CRUD")

# 1.1 创建手动任务
r = requests.post(f"{DS_API}/tasks", json={
    "source_type": "manual",
    "title": "DevPlan MVP 测试任务",
    "description": "用于验收 Phase 6 Dev Studio 功能的测试任务",
}, timeout=T)
check("1.1 创建手动任务 201/200", r.status_code in (200, 201))
d = r.json()
TASK_ID = d.get("dev_task_id", "")
check("1.2 返回 dev_task_id", bool(TASK_ID))
check("1.3 状态为 created", d.get("status") == "created")

# 1.4 列表查询
r = requests.get(f"{DS_API}/tasks", timeout=T)
check("1.4 列表查询 200", r.status_code == 200)
d = r.json()
check("1.5 列表有 items", isinstance(d.get("items"), list) and d["total"] >= 1)

# 1.6 关键字搜索
r = requests.get(f"{DS_API}/tasks?keyword=DevPlan", timeout=T)
check("1.6 关键字搜索", r.status_code == 200 and r.json().get("total", 0) >= 1)

# 1.7 详情查询
r = requests.get(f"{DS_API}/tasks/{TASK_ID}", timeout=T)
check("1.7 详情查询 200", r.status_code == 200)
d = r.json()
check("1.8 详情有 artifacts 字段", "artifacts" in d)
check("1.9 详情有 runs 字段", "runs" in d)

# 1.10 不存在的任务
r = requests.get(f"{DS_API}/tasks/nonexistent_task_id", timeout=T)
check("1.10 不存在的任务 404", r.status_code == 404)


# ══════════════════════════════════════════════════════════════
#  Phase 2: 生成 dev_plan
# ══════════════════════════════════════════════════════════════
print("\n[Phase 2] 生成 dev_plan")

r, ok = llm_post(f"{DS_API}/tasks/{TASK_ID}/generate-dev-plan")
if ok and r and r.status_code == 200:
    d = r.json()
    check("2.1 生成 dev_plan 200", True)
    check("2.2 有 run_id", bool(d.get("run_id")))
    check("2.3 有 trace_id", bool(d.get("trace_id")))
    DEV_PLAN_ART_ID = d.get("dev_artifact_id", "")
    is_mock = d.get("is_mock", False)

    if d.get("status") == "succeeded":
        check("2.4 状态 succeeded", True)
        check("2.5 有 dev_artifact_id", bool(DEV_PLAN_ART_ID))
    elif d.get("status") == "failed":
        check("2.4 状态 succeeded", False, f"LLM 失败: {d.get('error_message', '')[:80]}")
        check("2.5 有 dev_artifact_id", False, "LLM 失败跳过")
        DEV_PLAN_ART_ID = ""
    else:
        check("2.4 状态 succeeded", False, f"未知状态: {d.get('status')}")
        check("2.5 有 dev_artifact_id", False)
        DEV_PLAN_ART_ID = ""
else:
    check("2.1 生成 dev_plan 200", False, "请求失败")
    check("2.2 有 run_id", False)
    check("2.3 有 trace_id", False)
    check("2.4 状态 succeeded", False)
    check("2.5 有 dev_artifact_id", False)
    DEV_PLAN_ART_ID = ""
    is_mock = False


# ══════════════════════════════════════════════════════════════
#  Phase 3: 生成其他 4 种产物
# ══════════════════════════════════════════════════════════════
print("\n[Phase 3] 生成 api_design / db_design / file_impact / test_plan")

OTHER_TYPES = ["api_design", "db_design", "file_impact", "test_plan"]
OTHER_ENDPOINTS = {
    "api_design": "generate-api-design",
    "db_design": "generate-db-design",
    "file_impact": "generate-file-impact",
    "test_plan": "generate-test-plan",
}
GEN_ART_IDS = {}

for rt in OTHER_TYPES:
    ep = OTHER_ENDPOINTS[rt]
    r, ok = llm_post(f"{DS_API}/tasks/{TASK_ID}/{ep}")
    if ok and r and r.status_code == 200:
        d = r.json()
        check(f"3.{rt} 200", True)
        check(f"3.{rt} run_id", bool(d.get("run_id")))
        if d.get("status") == "succeeded":
            check(f"3.{rt} succeeded", True)
            GEN_ART_IDS[rt] = d.get("dev_artifact_id", "")
        else:
            check(f"3.{rt} succeeded", False, f"LLM 失败: {d.get('error_message', '')[:60]}")
            GEN_ART_IDS[rt] = ""
    else:
        check(f"3.{rt} 200", False)
        check(f"3.{rt} run_id", False)
        check(f"3.{rt} succeeded", False, "请求失败")
        GEN_ART_IDS[rt] = ""


# ══════════════════════════════════════════════════════════════
#  Phase 4: Artifact CRUD
# ══════════════════════════════════════════════════════════════
print("\n[Phase 4] Artifact CRUD")

# 选一个已有的 artifact
ART_ID = DEV_PLAN_ART_ID or next((v for v in GEN_ART_IDS.values() if v), "")

if ART_ID:
    # 4.1 查询 artifact
    r = requests.get(f"{DS_API}/artifacts/{ART_ID}", timeout=T)
    check("4.1 查询 artifact 200", r.status_code == 200)
    d = r.json()
    check("4.2 有 content_markdown", bool(d.get("content_markdown")))
    check("4.3 artifact_type 正确", d.get("artifact_type") in ["dev_plan", "api_design", "db_design", "file_impact", "test_plan"])

    # 4.4 更新 artifact
    r = requests.put(f"{DS_API}/artifacts/{ART_ID}", json={
        "title": "更新后的标题",
        "status": "confirmed",
    }, timeout=T)
    check("4.4 更新 artifact 200", r.status_code == 200)
    d = r.json()
    check("4.5 标题已更新", d.get("title") == "更新后的标题")
    check("4.6 状态已更新", d.get("status") == "confirmed")

    # 4.7 导出 artifact
    r = requests.post(f"{DS_API}/artifacts/{ART_ID}/export", timeout=T)
    check("4.7 导出 artifact 200", r.status_code == 200)
    check("4.8 导出内容非空", len(r.content) > 0)
else:
    check("4.1 查询 artifact 200", False, "无可用 artifact")
    check("4.2 有 content_markdown", False)
    check("4.3 artifact_type 正确", False)
    check("4.4 更新 artifact 200", False)
    check("4.5 标题已更新", False)
    check("4.6 状态已更新", False)
    check("4.7 导出 artifact 200", False)
    check("4.8 导出内容非空", False)

# 4.9 不存在的 artifact
r = requests.get(f"{DS_API}/artifacts/nonexistent_art_id", timeout=T)
check("4.9 不存在的 artifact 404", r.status_code == 404)


# ══════════════════════════════════════════════════════════════
#  Phase 5: Run 查询
# ══════════════════════════════════════════════════════════════
print("\n[Phase 5] Run 查询")

# 获取任务详情中的 runs
r = requests.get(f"{DS_API}/tasks/{TASK_ID}", timeout=T)
d = r.json()
task_runs = d.get("runs", [])
check("5.1 任务有 runs", len(task_runs) >= 1)

if task_runs:
    run_id = task_runs[0].get("run_id", "")
    r = requests.get(f"{DS_API}/runs/{run_id}", timeout=T)
    check("5.2 查询 run 200", r.status_code == 200)
    d = r.json()
    check("5.3 run 有 trace_id", bool(d.get("trace_id")))
    check("5.4 run 有 model_name", bool(d.get("model_name")))
    check("5.5 run 有 dev_task_id", d.get("dev_task_id") == TASK_ID)
else:
    check("5.2 查询 run 200", False)
    check("5.3 run 有 trace_id", False)
    check("5.4 run 有 model_name", False)
    check("5.5 run 有 dev_task_id", False)

# 5.6 不存在的 run
r = requests.get(f"{DS_API}/runs/nonexistent_run_id", timeout=T)
check("5.6 不存在的 run 404", r.status_code == 404)


# ══════════════════════════════════════════════════════════════
#  Phase 6: 与 Product Studio 集成
# ══════════════════════════════════════════════════════════════
print("\n[Phase 6] Product Studio 集成")

# 6.1 创建一个 Product Studio Idea
r = requests.post(f"{PS_API}/ideas", json={
    "title": "Dev Studio 集成测试产品",
    "product_direction": "用于验证 Dev Studio 与 Product Studio 的集成",
    "target_users": "测试工程师",
}, timeout=T)
if r.status_code == 200:
    idea_data = r.json()
    IDEA_ID = idea_data.get("idea_id", "")
    check("6.1 创建 idea 200", True)

    # 6.2 生成 PRD
    r2, ok2 = llm_post(f"{PS_API}/ideas/{IDEA_ID}/generate-prd")
    if ok2 and r2 and r2.status_code == 200:
        prd_data = r2.json()
        check("6.2 生成 PRD", True)
        ART_ID_FROM_PS = prd_data.get("artifact_id", "")

        if ART_ID_FROM_PS:
            # 6.3 从 Product Studio artifact 创建 Dev Task
            r3 = requests.post(f"{DS_API}/tasks", json={
                "source_type": "product_artifact",
                "source_id": ART_ID_FROM_PS,
                "idea_id": IDEA_ID,
                "title": f"[PRD] Dev Studio 集成测试产品 开发计划",
                "description": "从 Product Studio PRD 创建的开发任务",
            }, timeout=T)
            check("6.3 从 PS artifact 创建 task 200", r3.status_code in (200, 201))
            d3 = r3.json()
            INTEGRATED_TASK_ID = d3.get("dev_task_id", "")
            check("6.4 集成任务有 dev_task_id", bool(INTEGRATED_TASK_ID))

            if INTEGRATED_TASK_ID:
                # 6.5 查看详情中的 source_summary
                r4 = requests.get(f"{DS_API}/tasks/{INTEGRATED_TASK_ID}", timeout=T)
                d4 = r4.json()
                check("6.5 详情有 source_summary", bool(d4.get("source_summary")))

                # 6.6 生成 dev_plan
                r5, ok5 = llm_post(f"{DS_API}/tasks/{INTEGRATED_TASK_ID}/generate-dev-plan")
                if ok5 and r5 and r5.status_code == 200:
                    d5 = r5.json()
                    check("6.6 集成任务生成 dev_plan", d5.get("status") in ("succeeded", "failed"))
                    if d5.get("status") == "succeeded":
                        check("6.7 集成任务有 artifact", bool(d5.get("dev_artifact_id")))
                    else:
                        check("6.7 集成任务有 artifact", False, "LLM soft-fail")
                else:
                    check("6.6 集成任务生成 dev_plan", False)
                    check("6.7 集成任务有 artifact", False)
            else:
                check("6.5 详情有 source_summary", False)
                check("6.6 集成任务生成 dev_plan", False)
                check("6.7 集成任务有 artifact", False)
        else:
            check("6.3 从 PS artifact 创建 task 200", False, "无 artifact_id")
            check("6.4 集成任务有 dev_task_id", False)
            check("6.5 详情有 source_summary", False)
            check("6.6 集成任务生成 dev_plan", False)
            check("6.7 集成任务有 artifact", False)
    else:
        check("6.2 生成 PRD", False, "LLM 不可用")
        for i in range(3, 8):
            check(f"6.{i} 跳过", False, "前置失败")
else:
    check("6.1 创建 idea 200", False)
    for i in range(2, 8):
        check(f"6.{i} 跳过", False, "前置失败")


# ══════════════════════════════════════════════════════════════
#  Phase 7: 安全验证
# ══════════════════════════════════════════════════════════════
print("\n[Phase 7] 安全验证")

# 7.1 创建任务无 source_id 的 product_artifact 类型
r = requests.post(f"{DS_API}/tasks", json={
    "source_type": "product_artifact",
    "source_id": "nonexistent_artifact_id",
    "title": "安全测试任务",
}, timeout=T)
check("7.1 不存在的 source_id 返回 404", r.status_code == 404)

# 7.2 不支持的 run_type — 直接调用不存在的 endpoint
r = requests.post(f"{DS_API}/tasks/{TASK_ID}/generate-unknown-type", timeout=T)
check("7.2 不存在的 endpoint 404/405/422", r.status_code in (404, 405, 422))

# 7.3 验证无自动代码修改
if ART_ID:
    r = requests.get(f"{DS_API}/artifacts/{ART_ID}", timeout=T)
    d = r.json()
    md = (d.get("content_markdown") or "").lower()
    has_dangerous = any(kw in md for kw in ["git push", "git commit", "rm -rf", "deploy"])
    check("7.3 产物不含自动执行命令", not has_dangerous)
else:
    check("7.3 产物不含自动执行命令", True, "无可用 artifact 跳过")


# ══════════════════════════════════════════════════════════════
#  结果汇总
# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
passed = sum(1 for _, c in results if c)
failed = len(results) - passed
print(f"总计: {len(results)}  ✅ PASS: {passed}  ❌ FAIL: {failed}")

# 区分 LLM soft-fail
llm_fail_count = sum(1 for name, c in results if not c and ("LLM" in name or "soft-fail" in str(name)))
core_fail = failed - llm_fail_count
if core_fail > 0:
    print(f"⚠️ 核心失败: {core_fail} (非 LLM 原因)")
elif failed > 0:
    print(f"ℹ️ 全部失败均为 LLM soft-fail，核心逻辑通过")
else:
    print("🎉 全部通过！")

sys.exit(0 if core_fail == 0 else 1)
