import requests
import json

# 获取后端OpenAPI规范
response = requests.get("http://localhost:8000/openapi.json")
openapi_spec = response.json()

# 提取所有后端路径
backend_paths = set(openapi_spec["paths"].keys())

print("="*80)
print("后端实际API路径清单")
print("="*80)

# 按路径前缀分组
api_groups = {}
for path in sorted(backend_paths):
    # 提取第一级路径作为分组
    parts = path.strip('/').split('/')
    if len(parts) >= 2:
        group = f"/{parts[0]}/{parts[1]}"
    else:
        group = f"/{parts[0]}" if parts else "/"
    
    if group not in api_groups:
        api_groups[group] = []
    api_groups[group].append(path)

for group in sorted(api_groups.keys()):
    print(f"\n【{group}】")
    for path in sorted(api_groups[group]):
        methods = list(openapi_spec["paths"][path].keys())
        methods_str = ", ".join([m.upper() for m in methods if m != 'parameters'])
        print(f"  {methods_str:20} {path}")

print("\n" + "="*80)
print(f"总计: {len(backend_paths)} 个API路径")
print("="*80)

# 前端调用的关键路径（从api.js提取）
frontend_paths = {
    # V2 API
    "/api/v2/projects": "GET, POST",
    "/api/v2/projects/{id}": "GET, PUT, DELETE",
    "/api/v2/environments": "POST",
    "/api/v2/environments/{id}": "GET, PUT, DELETE",
    "/api/v2/test-cases": "GET",
    "/api/v2/test-cases/{id}": "GET",
    "/api/v2/test-cases/{id}/execute": "POST",
    "/api/v2/test-cases/batch-execute": "POST",
    "/api/v2/test-runs": "GET, POST",
    "/api/v2/test-runs/{id}": "GET",
    "/api/v2/test-runs/{id}/cases": "GET",
    "/api/v2/dashboard/summary": "GET",
    "/api/v2/swagger/import-file": "POST",
    "/api/v2/swagger/api-specs": "GET",
    "/api/v2/execution/trigger": "POST",
    "/api/v2/execute": "POST",
    "/api/v2/execute/batch": "POST",
    
    # Pilot API
    "/api/pilot/projects": "GET, POST",
    "/api/pilot/projects/{id}": "GET, PUT, DELETE",
    "/api/pilot/environments": "POST",
    "/api/pilot/test-cases": "GET",
    "/api/pilot/test-runs": "GET, POST",
    "/api/pilot/test-runs/{id}": "GET",
    "/api/pilot/reports": "GET",
    "/api/pilot/reports/{id}": "GET",
    
    # 其他API
    "/api/ai/providers/list": "GET",
    "/api/upload/swagger": "POST",
    "/health": "GET",
}

print("\n\n" + "="*80)
print("前后端接口一致性检查")
print("="*80)

missing_in_backend = []
for fe_path, methods in sorted(frontend_paths.items()):
    # 将{id}替换为{project_id}等进行模糊匹配
    path_pattern = fe_path.replace("{id}", "{")
    
    # 检查是否存在
    found = False
    for be_path in backend_paths:
        if be_path == fe_path or be_path.startswith(path_pattern):
            found = True
            break
    
    status = "✅" if found else "❌"
    print(f"{status} {methods:20} {fe_path}")
    
    if not found:
        missing_in_backend.append(fe_path)

if missing_in_backend:
    print("\n" + "="*80)
    print("⚠️ 前端调用但后端不存在的接口:")
    print("="*80)
    for path in missing_in_backend:
        print(f"  ❌ {path}")
else:
    print("\n✅ 所有前端调用的接口在后端都存在")

print("\n" + "="*80)
