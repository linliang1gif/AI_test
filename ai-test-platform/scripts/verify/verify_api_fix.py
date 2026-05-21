import requests
import json

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
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code < 400:
            print(f"✅ 成功")
            return True
        else:
            print(f"❌ 失败: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        return False

print("="*60)
print("P0.6 API契约修复验证")
print("="*60)

results = {}

# 1. 项目管理 (v2路由)
print("\n\n【1. 项目管理 - V2路由】")
results['projects_list'] = test_api("GET", "/api/v2/projects", description="查询项目列表")
results['projects_detail'] = test_api("GET", "/api/v2/projects/1", description="查询项目详情")

# 2. 环境管理 (v2路由，使用枚举name)
print("\n\n【2. 环境管理 - V2路由】")
env_data = {
    "project_id": 1,
    "name": "test",  # 使用枚举值
    "base_url": "https://api.example.com",
    "is_protected": False,
    "allow_write": True,
    "timeout_seconds": 30,
    "retry_count": 0
}
results['env_create'] = test_api("POST", "/api/v2/environments", env_data, "创建环境(使用枚举)")

# 3. API Specs (swagger路由)
print("\n\n【3. API Specs - Swagger路由】")
results['api_specs_list'] = test_api("GET", "/api/v2/swagger/api-specs", description="查询API规范列表")
results['api_specs_by_project'] = test_api("GET", "/api/v2/swagger/api-specs?project_id=1", description="按项目查询API规范")

# 4. 测试用例 (v2路由)
print("\n\n【4. 测试用例 - V2路由】")
results['testcases_list'] = test_api("GET", "/api/v2/test-cases", description="查询测试用例列表")
results['testcases_detail'] = test_api("GET", "/api/v2/test-cases/TC_001", description="查询用例详情")

# 5. 执行记录 (v2路由)
print("\n\n【5. 执行记录 - V2路由】")
results['testruns_list'] = test_api("GET", "/api/v2/test-runs", description="查询执行列表")

# 获取第一个run_id
response = requests.get(f"{BASE_URL}/api/v2/test-runs")
if response.status_code == 200:
    runs = response.json()
    if runs and len(runs) > 0:
        run_id = runs[0].get("id")
        results['testruns_detail'] = test_api("GET", f"/api/v2/test-runs/{run_id}", description="查询执行详情")
        results['testruns_cases'] = test_api("GET", f"/api/v2/observability/runs/{run_id}/cases", description="查询执行用例(observability)")

# 6. 报告 (通过test-runs)
print("\n\n【6. 报告 - Test-Runs路由】")
if run_id:
    results['report_generate'] = test_api("POST", f"/api/v2/test-runs/{run_id}/report", 
                                         {"format": "html"}, "生成报告")

# 7. Dashboard
print("\n\n【7. Dashboard - V2路由】")
results['dashboard'] = test_api("GET", "/api/v2/dashboard/summary", description="Dashboard摘要")

# 统计结果
print("\n\n" + "="*60)
print("验证结果统计")
print("="*60)

success_count = sum(1 for v in results.values() if v)
total_count = len(results)
fail_count = total_count - success_count

print(f"\n总计: {total_count} 个接口")
print(f"✅ 成功: {success_count} 个")
print(f"❌ 失败: {fail_count} 个")
print(f"成功率: {success_count/total_count*100:.1f}%")

print("\n详细结果:")
for name, success in results.items():
    status = "✅" if success else "❌"
    print(f"{status} {name}")

if fail_count == 0:
    print("\n🎉 所有接口验证通过！可以进入P1阶段")
else:
    print(f"\n⚠️ 还有 {fail_count} 个接口需要修复")
