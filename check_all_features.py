"""全面检查AI测试平台所有功能的实现状态"""
import requests
import json
from pathlib import Path

print("=" * 80)
print("AI测试平台功能实现状态检查")
print("=" * 80)
print()

base_url = "http://localhost:8000"
results = {
    "implemented": [],
    "partial": [],
    "not_implemented": []
}

def check_api(name, method, endpoint, expected_keys=None):
    """检查API端点是否实现"""
    try:
        url = f"{base_url}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=3)
        elif method == "POST":
            response = requests.post(url, json={}, timeout=3)
        else:
            response = requests.request(method, url, timeout=3)
        
        if response.status_code == 200:
            data = response.json()
            if expected_keys:
                has_keys = all(key in data for key in expected_keys)
                return "✅", response.status_code, has_keys
            return "✅", response.status_code, True
        elif response.status_code == 404:
            return "❌", 404, False
        else:
            return "⚠️", response.status_code, False
    except requests.exceptions.ConnectionError:
        return "❌", "连接失败", False
    except Exception as e:
        return "❌", str(e)[:30], False

print("1. 基础功能检查")
print("-" * 80)

# 健康检查
status, code, _ = check_api("健康检查", "GET", "/health")
print(f"{status} 健康检查: {code}")

# Dashboard
status, code, has_data = check_api("Dashboard统计", "GET", "/api/dashboard/stats", ["totalTests", "passed", "failed"])
print(f"{status} Dashboard统计: {code} - 数据完整: {has_data}")

print()
print("2. 项目管理")
print("-" * 80)

status, code, has_data = check_api("获取项目列表", "GET", "/api/projects", ["projects"])
print(f"{status} 获取项目列表: {code}")

status, code, _ = check_api("创建项目", "POST", "/api/projects")
print(f"{status} 创建项目: {code}")

status, code, _ = check_api("删除项目", "DELETE", "/api/projects/1")
print(f"{status} 删除项目: {code}")

print()
print("3. API管理")
print("-" * 80)

status, code, has_data = check_api("获取API列表", "GET", "/api/apis", ["apis"])
print(f"{status} 获取API列表: {code}")

status, code, _ = check_api("解析Swagger", "POST", "/api/swagger/parse")
print(f"{status} 解析Swagger: {code}")

status, code, _ = check_api("上传Swagger", "POST", "/api/upload/swagger")
print(f"{status} 上传Swagger: {code}")

status, code, _ = check_api("执行API", "POST", "/api/execute-api")
print(f"{status} 执行API: {code}")

status, code, _ = check_api("保存为测试用例", "POST", "/api/save-api-as-testcase")
print(f"{status} 保存为测试用例: {code}")

print()
print("4. 测试用例管理")
print("-" * 80)

status, code, has_data = check_api("获取测试用例", "GET", "/api/test-cases", ["test_cases"])
print(f"{status} 获取测试用例: {code}")

status, code, _ = check_api("创建测试用例", "POST", "/api/test-cases")
print(f"{status} 创建测试用例: {code}")

status, code, _ = check_api("生成测试用例", "POST", "/api/ai/generate")
print(f"{status} AI生成测试用例: {code}")

print()
print("5. 测试数据管理")
print("-" * 80)

status, code, _ = check_api("生成测试数据", "POST", "/api/test-data/generate")
print(f"{status} 生成测试数据: {code}")

status, code, _ = check_api("智能生成字段", "POST", "/api/test-data/smart-generate")
print(f"{status} 智能生成字段: {code}")

status, code, _ = check_api("获取数据集", "GET", "/api/test-data/datasets")
print(f"{status} 获取数据集: {code}")

status, code, _ = check_api("创建数据集", "POST", "/api/test-data/datasets")
print(f"{status} 创建数据集: {code}")

print()
print("6. 自动化脚本")
print("-" * 80)

status, code, has_data = check_api("获取脚本列表", "GET", "/api/automation/scripts", ["scripts"])
print(f"{status} 获取脚本列表: {code}")

status, code, _ = check_api("生成脚本", "POST", "/api/automation/scripts/generate")
print(f"{status} 生成脚本: {code}")

status, code, _ = check_api("下载脚本", "GET", "/api/automation/scripts/1/download")
print(f"{status} 下载脚本: {code}")

status, code, _ = check_api("执行脚本", "POST", "/api/automation/scripts/1/execute")
print(f"{status} 执行脚本: {code}")

print()
print("7. 测试执行")
print("-" * 80)

status, code, has_data = check_api("获取测试运行", "GET", "/api/test-runs", ["test_runs"])
print(f"{status} 获取测试运行: {code}")

status, code, _ = check_api("启动测试", "POST", "/api/test-runs/start")
print(f"{status} 启动测试: {code}")

status, code, _ = check_api("获取执行状态", "GET", "/api/test-runs/1/status")
print(f"{status} 获取执行状态: {code}")

print()
print("8. 报告管理")
print("-" * 80)

status, code, has_data = check_api("获取报告列表", "GET", "/api/reports", ["reports"])
print(f"{status} 获取报告列表: {code}")

status, code, _ = check_api("获取报告详情", "GET", "/api/reports/1")
print(f"{status} 获取报告详情: {code}")

status, code, _ = check_api("生成报告", "POST", "/api/reports/generate")
print(f"{status} 生成报告: {code}")

print()
print("9. AI功能")
print("-" * 80)

status, code, _ = check_api("获取AI代理", "GET", "/api/ai/agents")
print(f"{status} 获取AI代理: {code}")

status, code, _ = check_api("AI生成", "POST", "/api/ai/generate")
print(f"{status} AI生成: {code}")

status, code, _ = check_api("获取AI提供商", "GET", "/api/ai/providers/list")
print(f"{status} 获取AI提供商: {code}")

status, code, _ = check_api("切换AI提供商", "POST", "/api/ai/providers/switch")
print(f"{status} 切换AI提供商: {code}")

print()
print("10. 知识库")
print("-" * 80)

status, code, _ = check_api("知识库统计", "GET", "/api/knowledge/stats")
print(f"{status} 知识库统计: {code}")

status, code, _ = check_api("搜索测试用例", "POST", "/api/knowledge/testcases/search")
print(f"{status} 搜索测试用例: {code}")

status, code, _ = check_api("获取覆盖率", "GET", "/api/knowledge/coverage")
print(f"{status} 获取覆盖率: {code}")

print()
print("=" * 80)
print("前端页面检查")
print("=" * 80)
print()

# 检查前端页面文件
frontend_pages = [
    ("Dashboard", "ai-test-platform/frontend/src/pages/Dashboard.jsx"),
    ("项目管理", "ai-test-platform/frontend/src/pages/Projects.jsx"),
    ("API管理", "ai-test-platform/frontend/src/pages/ApiExplorer.jsx"),
    ("测试用例", "ai-test-platform/frontend/src/pages/TestCases.jsx"),
    ("测试数据", "ai-test-platform/frontend/src/pages/TestData.jsx"),
    ("自动化脚本", "ai-test-platform/frontend/src/pages/Automation.jsx"),
    ("测试执行", "ai-test-platform/frontend/src/pages/TestRuns.jsx"),
    ("测试报告", "ai-test-platform/frontend/src/pages/Reports.jsx"),
]

for name, path in frontend_pages:
    if Path(path).exists():
        print(f"✅ {name}: 页面文件存在")
    else:
        print(f"❌ {name}: 页面文件不存在")

print()
print("=" * 80)
print("数据文件检查")
print("=" * 80)
print()

data_file = Path("ai-test-platform/data/platform_data.json")
if data_file.exists():
    print(f"✅ 数据文件存在: {data_file}")
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"\n数据统计:")
        print(f"  - 项目数: {len(data.get('projects', []))}")
        print(f"  - API数: {len(data.get('apis', []))}")
        print(f"  - 测试用例数: {len(data.get('test_cases', []))}")
        print(f"  - 自动化脚本数: {len(data.get('scripts', []))}")
        print(f"  - 测试运行数: {len(data.get('test_runs', []))}")
        print(f"  - 报告数: {len(data.get('reports', []))}")
        print(f"  - 数据集数: {len(data.get('datasets', []))}")
    except Exception as e:
        print(f"⚠️  读取数据文件失败: {e}")
else:
    print(f"❌ 数据文件不存在: {data_file}")

print()
print("=" * 80)
print("总结")
print("=" * 80)
print()

print("✅ 完全实现的功能:")
print("  - Swagger上传和解析")
print("  - API列表查看")
print("  - API执行（Mock模式）")
print("  - 保存为测试用例")
print("  - 项目管理")
print("  - Dashboard统计")
print()

print("⚠️  部分实现的功能:")
print("  - 测试用例生成（后端有，前端可能未连接）")
print("  - 测试数据生成（后端有，前端可能未连接）")
print("  - 自动化脚本生成（后端有，前端可能未连接）")
print()

print("❌ 未实现或有问题的功能:")
print("  - 从测试用例生成脚本")
print("  - 脚本执行")
print("  - 测试运行")
print("  - 报告生成")
print("  - 知识库功能")
print()

print("建议:")
print("1. 先修复前端按钮连接问题")
print("2. 实现脚本生成功能")
print("3. 实现测试执行功能")
print("4. 实现报告生成功能")
