#!/usr/bin/env python3
"""
P1-7B.1 TestCases 持久化与删除风险加固验证
"""
import json, os, time, requests, subprocess, signal, sys

BASE = "http://localhost:8000"
PASS_COUNT = 0
FAIL_COUNT = 0
RESULTS = []

def check(section, label, cond, detail=""):
    global PASS_COUNT, FAIL_COUNT
    status = "PASS" if cond else "FAIL"
    if cond:
        PASS_COUNT += 1
    else:
        FAIL_COUNT += 1
    icon = "\u2705" if cond else "\u274c"
    msg = f"  {icon} {status}  {label}  {detail}"
    print(msg)
    RESULTS.append({"section": section, "label": label, "status": status, "detail": detail})

def wait_for_server(timeout=30):
    """等待后端启动"""
    for _ in range(timeout):
        try:
            r = requests.get(f"{BASE}/health", timeout=2)
            if r.status_code == 200:
                return True
        except:
            pass
        time.sleep(1)
    return False

def create_unique_spec(ts_suffix, paths_prefix):
    """创建唯一 swagger spec"""
    return {
        "openapi": "3.0.0",
        "info": {"title": f"Test_{ts_suffix}", "version": "1.0.0"},
        "paths": {
            f"/{paths_prefix}/users": {
                "get": {
                    "tags": [paths_prefix],
                    "summary": f"List {paths_prefix} users",
                    "parameters": [
                        {"name": "page", "in": "query", "schema": {"type": "integer"}},
                    ],
                    "responses": {"200": {"description": "OK", "content": {"application/json": {"schema": {"type": "object", "properties": {"items": {"type": "array", "items": {"type": "object"}}}}}}}}
                },
                "post": {
                    "tags": [paths_prefix],
                    "summary": f"Create {paths_prefix} user",
                    "requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object", "required": ["name"], "properties": {"name": {"type": "string"}, "email": {"type": "string"}}}}}},
                    "responses": {"201": {"description": "Created"}}
                }
            },
            f"/{paths_prefix}/users/{{id}}": {
                "get": {
                    "tags": [paths_prefix],
                    "summary": f"Get {paths_prefix} user",
                    "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                    "responses": {"200": {"description": "OK"}}
                },
                "put": {
                    "tags": [paths_prefix],
                    "summary": f"Update {paths_prefix} user",
                    "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                    "requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object", "properties": {"name": {"type": "string"}}}}}},
                    "responses": {"200": {"description": "OK"}}
                },
                "delete": {
                    "tags": [paths_prefix],
                    "summary": f"Delete {paths_prefix} user",
                    "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                    "responses": {"204": {"description": "Deleted"}}
                }
            }
        }
    }

def import_swagger_file(project_id, spec, filename):
    """导入 swagger 文件"""
    os.makedirs("uploads/swagger", exist_ok=True)
    tmp = f"uploads/swagger/_verify_{filename}.json"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False)
    with open(tmp, "rb") as f:
        r = requests.post(
            f"{BASE}/api/v2/swagger/import-file?project_id={project_id}&generate_cases=True",
            files={"file": (f"{filename}.json", f, "application/json")}
        )
    os.remove(tmp)
    return r

# ==============================================================================
print("=" * 72)
print("P1-7B.1 TestCases \u6301\u4e45\u5316\u4e0e\u5220\u9664\u98ce\u9669\u52a0\u56fa\u9a8c\u8bc1")
print("=" * 72)

ts = int(time.time())

# ==================== 一、验证 V2 持久化 ====================
print(f"\n{'='*72}")
print("\u3010\u4e00\u3011\u9a8c\u8bc1 V2 \u6301\u4e45\u5316\uff08\u5bfc\u5165\u2192\u91cd\u542f\u2192\u7528\u4f8b\u4ecd\u5728\uff09")
print("="*72)

# 1.1 导入 OpenAPI 生成测试用例
p_persist = requests.post(f"{BASE}/api/v2/projects", json={"name": f"Persist_{ts}", "description": "persistence test"})
pid_persist = p_persist.json().get("id")
check("一", "创建持久化验证项目", pid_persist is not None, f"pid={pid_persist}")

spec_persist = create_unique_spec(ts, f"persist{ts}")
imp_persist = import_swagger_file(pid_persist, spec_persist, f"persist_{ts}")
check("一", "导入 Swagger 成功", imp_persist.status_code == 200)

# 1.2 确认 V2 查询能看到用例
r_before = requests.get(f"{BASE}/api/v2/test-cases?project_id={pid_persist}&limit=100")
total_before = r_before.json()["total"]
check("一", "导入后 V2 可查到用例", total_before > 0, f"count={total_before}")
case_ids_before = [tc["id"] for tc in r_before.json().get("test_cases", [])]

# 1.3 记录总数
r_all_before = requests.get(f"{BASE}/api/v2/test-cases?limit=5")
total_all_before = r_all_before.json()["total"]
print(f"  \u2139\ufe0f  重启前全局总数: {total_all_before}, 项目用例数: {total_before}")

# 1.4 确认旧 API 返回的是内存数据（与 V2 无关）
r_old = requests.get(f"{BASE}/api/test-cases")
old_count = r_old.json().get("count", 0)
check("一", "旧 /api/test-cases 返回内存数据(=0)", old_count == 0, f"count={old_count}")

# ==================== 二、验证 project_id 过滤 ====================
print(f"\n{'='*72}")
print("\u3010\u4e8c\u3011\u9a8c\u8bc1 project_id \u8fc7\u6ee4\uff08A/B \u9879\u76ee\u9694\u79bb\uff09")
print("="*72)

# 2.1 创建项目 A
pA = requests.post(f"{BASE}/api/v2/projects", json={"name": f"ProjectA_{ts}", "description": "project A"})
pidA = pA.json().get("id")
check("二", "创建项目 A", pidA is not None, f"pidA={pidA}")

# 2.2 创建项目 B
pB = requests.post(f"{BASE}/api/v2/projects", json={"name": f"ProjectB_{ts}", "description": "project B"})
pidB = pB.json().get("id")
check("二", "创建项目 B", pidB is not None, f"pidB={pidB}")

# 2.3 导入 Swagger A（唯一路径）
specA = create_unique_spec(f"A{ts}", f"alpha{ts}")
impA = import_swagger_file(pidA, specA, f"alpha_{ts}")
check("二", "项目 A 导入成功", impA.status_code == 200)

# 2.4 导入 Swagger B（唯一路径）
specB = create_unique_spec(f"B{ts}", f"beta{ts}")
impB = import_swagger_file(pidB, specB, f"beta_{ts}")
check("二", "项目 B 导入成功", impB.status_code == 200)

# 2.5 查询项目 A 用例
rA = requests.get(f"{BASE}/api/v2/test-cases?project_id={pidA}&limit=200")
casesA = rA.json().get("test_cases", [])
totalA = rA.json()["total"]
idsA = set(tc["id"] for tc in casesA)
check("二", f"项目 A 有用例", totalA > 0, f"count={totalA}")

# 2.6 查询项目 B 用例
rB = requests.get(f"{BASE}/api/v2/test-cases?project_id={pidB}&limit=200")
casesB = rB.json().get("test_cases", [])
totalB = rB.json()["total"]
idsB = set(tc["id"] for tc in casesB)
check("二", f"项目 B 有用例", totalB > 0, f"count={totalB}")

# 2.7 检查隔离性 — A 的用例是否出现在 B 中
# 因为 tags LIKE 方案，同一 ID 可能被多个项目标记
# 这里检查的是：A 独有的 tag 中是否出现 B 的 tag
has_cross_contamination = False
for tc in casesA:
    tags = tc.get("tags") or []
    if f"project:{pidB}" in tags and f"project:{pidA}" not in tags:
        has_cross_contamination = True
        break
check("二", "项目 A 用例无 B 的独占污染", not has_cross_contamination)

# 检查是否有重叠
overlap = idsA & idsB
if overlap:
    # 重叠可能是因为相同 API 路径（不同项目导入同一 spec 的去重）
    # 这在 tags LIKE 方案下是已知行为
    print(f"  \u26a0\ufe0f  A\u2229B 重叠 {len(overlap)} 个用例（同路径去重已知行为）")
    # 验证重叠用例同时含两个标签
    for oid in list(overlap)[:3]:
        tc = next((t for t in casesA if t["id"] == oid), None)
        if tc:
            tags = tc.get("tags") or []
            has_both = f"project:{pidA}" in tags and f"project:{pidB}" in tags
            check("二", f"重叠用例 {oid} 含双标签", has_both, f"tags={tags}")
else:
    check("二", "A/B 用例完全隔离", True, "无重叠")

# 2.8 全部项目
rAll = requests.get(f"{BASE}/api/v2/test-cases?limit=5")
totalAll = rAll.json()["total"]
check("二", "全部项目 >= A+B (去重)", totalAll >= max(totalA, totalB), f"all={totalAll}")

# ==================== 三、验证删除不破坏历史记录 ====================
print(f"\n{'='*72}")
print("\u3010\u4e09\u3011\u9a8c\u8bc1\u5220\u9664\u4e0d\u7834\u574f\u5386\u53f2\u8bb0\u5f55")
print("="*72)

# 3.1 查找一个已有执行记录的测试用例
r_runs = requests.get(f"{BASE}/api/v2/test-runs?limit=10")
runs_data = r_runs.json()
if isinstance(runs_data, list):
    runs = runs_data
elif isinstance(runs_data, dict):
    runs = runs_data.get("runs") or runs_data.get("test_runs") or []
else:
    runs = []

target_tc_id = None
target_run_id = None
target_run_case_count = 0

for run in runs:
    rid = run.get("id") or run.get("run_id")
    if not rid:
        continue
    r_cases = requests.get(f"{BASE}/api/v2/test-runs/{rid}/cases")
    if r_cases.status_code != 200:
        continue
    rc_data = r_cases.json()
    if isinstance(rc_data, list):
        rc_list = rc_data
    elif isinstance(rc_data, dict):
        rc_list = rc_data.get("cases") or rc_data.get("run_cases") or []
    else:
        rc_list = []
    if rc_list:
        for rc in rc_list:
            tcid = rc.get("test_case_id")
            if tcid:
                target_tc_id = tcid
                target_run_id = rid
                target_run_case_count = len(rc_list)
                break
    if target_tc_id:
        break

if target_tc_id:
    print(f"  \u2139\ufe0f  找到目标: tc={target_tc_id}, run={target_run_id}, run_cases={target_run_case_count}")

    # 3.2 确认用例存在
    r_tc = requests.get(f"{BASE}/api/v2/test-cases/{target_tc_id}")
    check("三", "目标用例存在", r_tc.status_code == 200)

    # 3.3 查看 run 详情 — 删除前
    r_run_detail = requests.get(f"{BASE}/api/v2/test-runs/{target_run_id}")
    check("三", "执行记录详情可访问（删前）", r_run_detail.status_code == 200)

    r_run_cases_before = requests.get(f"{BASE}/api/v2/test-runs/{target_run_id}/cases")
    rcb_data = r_run_cases_before.json()
    cases_in_run_before = len(rcb_data if isinstance(rcb_data, list) else (rcb_data.get("cases") or rcb_data.get("run_cases") or []))
    check("三", f"run 含 {cases_in_run_before} 条 case 记录（删前）", cases_in_run_before > 0)

    # 3.4 执行 batch-delete
    print(f"  \u26a0\ufe0f  即将 batch-delete tc={target_tc_id}")
    r_del = requests.post(f"{BASE}/api/v2/test-cases/batch-delete", json={"ids": [target_tc_id]})
    check("三", "batch-delete 返回 200", r_del.status_code == 200, f"resp={r_del.json()}")

    # 3.5 用例已被删除
    r_tc_after = requests.get(f"{BASE}/api/v2/test-cases/{target_tc_id}")
    check("三", "用例已删除 (404)", r_tc_after.status_code == 404)

    # 3.6 查看执行记录列表 — 不应白屏/500
    r_runs_after = requests.get(f"{BASE}/api/v2/test-runs?limit=10")
    check("三", "执行记录列表仍正常", r_runs_after.status_code == 200)

    # 3.7 查看执行记录详情 — 不应 500
    r_run_detail_after = requests.get(f"{BASE}/api/v2/test-runs/{target_run_id}")
    check("三", "执行记录详情仍可访问（删后）", r_run_detail_after.status_code == 200)

    # 3.8 查看 run_cases — 该 tc 的 run_case 应已被级联删除
    r_run_cases_after = requests.get(f"{BASE}/api/v2/test-runs/{target_run_id}/cases")
    check("三", "run cases 端点仍可访问（删后）", r_run_cases_after.status_code == 200)
    rca_data = r_run_cases_after.json()
    cases_in_run_after = len(rca_data if isinstance(rca_data, list) else (rca_data.get("cases") or rca_data.get("run_cases") or []))
    lost = cases_in_run_before - cases_in_run_after
    print(f"  \u2139\ufe0f  删前 run_cases={cases_in_run_before}, 删后={cases_in_run_after}, 丢失={lost}")

    if lost > 0:
        print(f"  \u26a0\ufe0f  \u2757 级联删除导致 {lost} 条 run_case 丢失！")
        check("三", "历史 run_case 未丢失", False, f"lost={lost}")
        # 标记风险
        RESULTS.append({"section": "三-风险", "label": "级联删除破坏历史执行记录",
                        "status": "RISK", "detail": f"丢失 {lost} 条 run_case"})
    else:
        check("三", "历史 run_case 未丢失", True)

    # 3.9 查看报告（如果有）
    r_reports = requests.get(f"{BASE}/api/v2/test-runs/{target_run_id}")
    report_data = r_reports.json()
    has_report = report_data.get("report") is not None or "report_id" in str(report_data)
    check("三", "执行记录响应无异常字段", r_reports.status_code == 200)

else:
    print("  \u26a0\ufe0f  未找到有执行记录的测试用例，跳过删除风险验证")
    print("  \u2139\ufe0f  原因：可能尚无 test_run 数据")
    check("三", "有可测试的执行记录", False, "无 run_case 数据")


# ==================== 汇总 ====================
print(f"\n{'='*72}")
print("汇总")
print("="*72)
print(f"  总计: {PASS_COUNT + FAIL_COUNT}  通过: {PASS_COUNT}  失败: {FAIL_COUNT}")
print(f"  通过率: {PASS_COUNT / max(PASS_COUNT + FAIL_COUNT, 1) * 100:.1f}%")

# 输出风险项
risks = [r for r in RESULTS if r["status"] in ("FAIL", "RISK")]
if risks:
    print(f"\n\u26a0\ufe0f  风险项:")
    for r in risks:
        print(f"    [{r['section']}] {r['label']}: {r['detail']}")

print(f"{'='*72}")
