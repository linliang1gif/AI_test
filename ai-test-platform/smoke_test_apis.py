import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_api(method, endpoint, data=None, description=""):
    """测试API接口"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n{'='*60}")
    print(f"测试: {description}")
    print(f"请求: {method} {endpoint}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        elif method == "PUT":
            response = requests.put(url, json=data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, timeout=10)
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code < 400:
            try:
                result = response.json()
                print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)[:500]}")
                print(f"✅ 成功")
                return True, result
            except:
                print(f"响应: {response.text[:200]}")
                print(f"✅ 成功")
                return True, response.text
        else:
            print(f"错误: {response.text[:200]}")
            print(f"❌ 失败")
            return False, None
            
    except Exception as e:
        print(f"异常: {str(e)}")
        print(f"❌ 失败")
        return False, None

print("="*60)
print("AI Test Platform - 核心 API 冒烟测试")
print("="*60)

# 1. 项目管理
print("\n\n【1. 项目管理】")
success, projects = test_api("GET", "/api/v2/projects", description="查询项目列表")

# 创建项目
project_data = {
    "name": f"冒烟测试项目_{datetime.now().strftime('%H%M%S')}",
    "description": "P0.5冒烟测试创建的项目"
}
success, new_project = test_api("POST", "/api/v2/projects", project_data, "创建项目")
project_id = new_project.get("id") if success and new_project else None

if project_id:
    test_api("GET", f"/api/v2/projects/{project_id}", description="查询项目详情")

# 2. 环境管理
print("\n\n【2. 环境管理】")
test_api("GET", "/api/v2/environments", description="查询环境列表")

if project_id:
    env_data = {
        "project_id": project_id,
        "name": "测试环境",
        "base_url": "https://api.example.com",
        "description": "冒烟测试环境"
    }
    test_api("POST", "/api/v2/environments", env_data, "创建环境")

# 3. Swagger/OpenAPI 导入
print("\n\n【3. Swagger/OpenAPI 导入】")
test_api("GET", "/api/v2/api-specs", description="查询API规范列表")

# 最小OpenAPI示例
minimal_openapi = {
    "openapi": "3.0.0",
    "info": {
        "title": "冒烟测试API",
        "version": "1.0.0"
    },
    "paths": {
        "/test": {
            "get": {
                "summary": "测试接口",
                "responses": {
                    "200": {
                        "description": "成功"
                    }
                }
            }
        }
    }
}

if project_id:
    swagger_data = {
        "project_id": project_id,
        "name": "冒烟测试API规范",
        "spec_content": json.dumps(minimal_openapi)
    }
    test_api("POST", "/api/v2/api-specs/import", swagger_data, "导入OpenAPI规范")

# 4. 测试用例管理
print("\n\n【4. 测试用例管理】")
test_api("GET", "/api/v2/test-cases", description="查询测试用例列表")

if project_id:
    test_api("GET", f"/api/v2/test-cases?project_id={project_id}", description="查询项目测试用例")

# 5. 用例执行
print("\n\n【5. 用例执行】")
test_api("GET", "/api/v2/test-runs", description="查询执行列表")

# 尝试执行一个简单的测试
if project_id:
    # 先查询是否有可执行的用例
    success, cases = test_api("GET", f"/api/v2/test-cases?project_id={project_id}", description="获取可执行用例")
    
# 6. 执行记录
print("\n\n【6. 执行记录】")
success, runs = test_api("GET", "/api/v2/test-runs", description="查询执行列表")

if success and runs and isinstance(runs, list) and len(runs) > 0:
    run_id = runs[0].get("id")
    if run_id:
        test_api("GET", f"/api/v2/test-runs/{run_id}", description="查询执行详情")
        test_api("GET", f"/api/v2/test-runs/{run_id}/cases", description="查询执行用例")

# 7. 测试报告
print("\n\n【7. 测试报告】")
test_api("GET", "/api/v2/reports", description="查询报告列表")

# 8. AI 分析
print("\n\n【8. AI 分析】")
test_api("GET", "/api/v2/ai/report-analyses", description="查询AI分析列表")

# Dashboard
print("\n\n【9. Dashboard】")
test_api("GET", "/api/v2/dashboard/summary", description="查询Dashboard摘要")

print("\n\n" + "="*60)
print("冒烟测试完成")
print("="*60)
