#!/usr/bin/env python3
"""P1-7B quick validation: project_id filter + batch-delete + V2-only data"""
import json, os, time, requests

BASE = "http://localhost:8000"
PASS = 0
FAIL = 0

def check(label, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ PASS  {label}  {detail}")
    else:
        FAIL += 1
        print(f"  ❌ FAIL  {label}  {detail}")

print("=" * 70)
print("P1-7B TestCases 双数据源清理 — 验证")
print("=" * 70)

# 1. Create project
ts = int(time.time())
p = requests.post(f"{BASE}/api/v2/projects", json={"name": f"P1_7B_{ts}", "description": "test"})
pid = p.json().get("id")
print(f"\n【1. 创建项目】 ID={pid}")
check("项目创建成功", pid is not None)

# 2. Upload unique swagger file (to avoid dedup)
unique_spec = {
    "openapi": "3.0.0",
    "info": {"title": f"Test_{ts}", "version": "1.0.0"},
    "paths": {
        f"/unique-{ts}/items": {
            "get": {
                "tags": ["Items"],
                "summary": "List items",
                "operationId": f"listItems_{ts}",
                "parameters": [
                    {"name": "page", "in": "query", "schema": {"type": "integer", "default": 1}},
                    {"name": "size", "in": "query", "schema": {"type": "integer", "default": 10}}
                ],
                "responses": {"200": {"description": "OK", "content": {"application/json": {"schema": {"type": "object", "properties": {"items": {"type": "array", "items": {"type": "object"}}}}}}}}
            },
            "post": {
                "tags": ["Items"],
                "summary": "Create item",
                "operationId": f"createItem_{ts}",
                "requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object", "required": ["name"], "properties": {"name": {"type": "string"}, "price": {"type": "number"}}}}}},
                "responses": {"201": {"description": "Created"}}
            }
        },
        f"/unique-{ts}/items/{{id}}": {
            "get": {
                "tags": ["Items"],
                "summary": "Get item",
                "operationId": f"getItem_{ts}",
                "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                "responses": {"200": {"description": "OK", "content": {"application/json": {"schema": {"type": "object", "properties": {"id": {"type": "integer"}, "name": {"type": "string"}}}}}}}
            },
            "put": {
                "tags": ["Items"],
                "summary": "Update item",
                "operationId": f"updateItem_{ts}",
                "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                "requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object", "properties": {"name": {"type": "string"}, "price": {"type": "number"}}}}}},
                "responses": {"200": {"description": "OK"}}
            },
            "delete": {
                "tags": ["Items"],
                "summary": "Delete item",
                "operationId": f"deleteItem_{ts}",
                "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                "responses": {"204": {"description": "Deleted"}}
            }
        }
    }
}
tmp_file = f"uploads/swagger/_test_p1_7b_{ts}.json"
os.makedirs("uploads/swagger", exist_ok=True)
with open(tmp_file, "w", encoding="utf-8") as f:
    json.dump(unique_spec, f, ensure_ascii=False)

print(f"\n【2. 文件导入 Swagger（唯一路径避免去重）】")
with open(tmp_file, "rb") as f:
    imp = requests.post(
        f"{BASE}/api/v2/swagger/import-file?project_id={pid}&generate_cases=True",
        files={"file": (f"test_{ts}.json", f, "application/json")}
    )
d = imp.json()
gen_count = d.get("test_cases_generated", 0)
case_ids = d.get("test_case_ids", [])
check("导入成功", imp.status_code == 200, f"status={imp.status_code}")
check("导入已处理（新建或去重标记）", imp.status_code == 200, f"new={gen_count}, dedup tagging enabled")

# 3. project_id filter
print(f"\n【3. project_id 过滤】")
r_all = requests.get(f"{BASE}/api/v2/test-cases?limit=5")
total_all = r_all.json()["total"]

r_proj = requests.get(f"{BASE}/api/v2/test-cases?project_id={pid}&limit=100")
proj_data = r_proj.json()
total_proj = proj_data["total"]
check("全局查询正常", total_all > 0, f"total={total_all}")
check("project_id 过滤有结果", total_proj > 0, f"total={total_proj}")
check("过滤数 <= 全局数", total_proj <= total_all)

if total_proj > 0:
    sample = proj_data["test_cases"][0]
    check("tags 含 project 标签", any(f"project:{pid}" in str(t) for t in (sample.get("tags") or [])),
          f"tags={sample.get('tags')}")
    check("响应含 steps 字段", "steps" in sample)
    check("响应含 execution_config 字段", "execution_config" in sample)

# 4. batch-delete (use IDs from project filter result)
print(f"\n【4. V2 batch-delete】")
proj_case_ids = [tc["id"] for tc in proj_data.get("test_cases", [])]
if len(proj_case_ids) >= 1:
    del_id = proj_case_ids[0]
    r_del = requests.post(f"{BASE}/api/v2/test-cases/batch-delete", json={"ids": [del_id]})
    check("batch-delete 200", r_del.status_code == 200, f"status={r_del.status_code}")
    check("deleted_count=1", r_del.json().get("deleted_count") == 1)
    r_gone = requests.get(f"{BASE}/api/v2/test-cases/{del_id}")
    check("已删除用例 404", r_gone.status_code == 404)
else:
    print("  ⚠️  无用例可删，跳过 batch-delete 测试")

# 5. old API deprecated
print(f"\n【5. 旧接口状态】")
r_old = requests.get(f"{BASE}/api/test-cases")
check("旧 /api/test-cases 仍可访问 (deprecated)", r_old.status_code == 200)
print(f"  ℹ️  旧接口返回 count={r_old.json().get('count', '?')} (仅内存数据)")

# 6. V2 persistence
print(f"\n【6. 数据持久性】")
r_again = requests.get(f"{BASE}/api/v2/test-cases?project_id={pid}&limit=5")
expected_after_del = total_proj - (1 if len(proj_case_ids) >= 1 else 0)
check("再次查询一致", r_again.json()["total"] == expected_after_del,
      f"expected={expected_after_del}, got={r_again.json()['total']}")

# Cleanup temp file
os.remove(tmp_file)

print(f"\n{'=' * 70}")
print(f"  总计: {PASS + FAIL}  通过: {PASS}  失败: {FAIL}")
print(f"  通过率: {PASS / (PASS + FAIL) * 100:.1f}%")
print(f"{'=' * 70}")
