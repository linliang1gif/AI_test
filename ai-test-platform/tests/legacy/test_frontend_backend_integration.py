#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
前后端API联调测试脚本
测试所有前端页面调用的后端API接口
"""

import requests
import json
from typing import Dict, Any, List
from datetime import datetime

class FrontendBackendIntegrationTest:
    """前后端集成测试"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8081"):
        self.base_url = base_url
        self.test_results = []
        
    def test_api(self, name: str, method: str, endpoint: str, data: Dict = None, files: Dict = None) -> bool:
        """测试单个API接口"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, timeout=10)
            elif method == "POST":
                if files:
                    response = requests.post(url, files=files, timeout=10)
                else:
                    response = requests.post(url, json=data, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, timeout=10)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            success = response.status_code in [200, 201]
            result = {
                "name": name,
                "endpoint": endpoint,
                "method": method,
                "status_code": response.status_code,
                "success": success,
                "response_time": response.elapsed.total_seconds(),
                "error": None if success else response.text[:200]
            }
            
            if success:
                try:
                    result["response_data"] = response.json()
                except:
                    result["response_data"] = response.text[:100]
            
            self.test_results.append(result)
            
            status = "✅" if success else "❌"
            print(f"{status} {name}: {endpoint} - {response.status_code} ({response.elapsed.total_seconds():.3f}s)")
            
            return success
            
        except Exception as e:
            result = {
                "name": name,
                "endpoint": endpoint,
                "method": method,
                "status_code": 0,
                "success": False,
                "response_time": 0,
                "error": str(e)
            }
            self.test_results.append(result)
            print(f"❌ {name}: {endpoint} - 错误: {str(e)}")
            return False
    
    def run_all_tests(self):
        """运行所有API测试"""
        print("\n" + "="*80)
        print("🚀 开始前后端API联调测试")
        print("="*80 + "\n")
        
        # 1. Dashboard API测试
        print("\n📊 Dashboard API测试:")
        print("-" * 80)
        self.test_api("获取仪表板统计", "GET", "/api/dashboard/stats")
        
        # 2. Projects API测试
        print("\n📁 Projects API测试:")
        print("-" * 80)
        self.test_api("获取项目列表", "GET", "/api/projects")
        self.test_api("创建项目", "POST", "/api/projects", {
            "name": "测试项目",
            "description": "API测试创建的项目",
            "environment": "development",
            "baseUrl": "http://test.example.com"
        })
        
        # 3. API Explorer测试
        print("\n🌐 API Explorer测试:")
        print("-" * 80)
        self.test_api("获取API列表", "GET", "/api/apis")
        self.test_api("解析Swagger", "POST", "/api/swagger/parse", {
            "url": "https://petstore.swagger.io/v2/swagger.json"
        })
        
        # 4. Test Cases API测试
        print("\n📝 Test Cases API测试:")
        print("-" * 80)
        self.test_api("获取测试用例", "GET", "/api/test-cases")
        self.test_api("创建测试用例", "POST", "/api/test-cases", {
            "title": "API测试用例",
            "steps": ["步骤1", "步骤2"],
            "expected": "预期结果",
            "priority": "High",
            "module": "测试模块"
        })
        
        # 注意: /api/testcases/generate 需要文件上传,这里跳过
        print("⚠️  跳过 /api/testcases/generate (需要文件上传)")
        
        # 5. Test Runs API测试
        print("\n▶️  Test Runs API测试:")
        print("-" * 80)
        self.test_api("获取测试执行列表", "GET", "/api/test-runs")
        self.test_api("启动测试执行", "POST", "/api/test-runs", {
            "test_type": "all",
            "environment": "staging"
        })
        
        # 6. Reports API测试
        print("\n📈 Reports API测试:")
        print("-" * 80)
        self.test_api("获取报告列表", "GET", "/api/reports")
        
        # 7. Automation API测试
        print("\n🤖 Automation API测试:")
        print("-" * 80)
        self.test_api("获取自动化脚本", "GET", "/api/automation/scripts")
        
        # 8. AI Insights API测试
        print("\n🧠 AI Insights API测试:")
        print("-" * 80)
        self.test_api("获取AI代理状态", "GET", "/api/ai/agents")
        self.test_api("获取当前AI配置", "GET", "/api/ai/current")
        self.test_api("获取AI提供商列表", "GET", "/api/ai/providers/list")
        
        # 9. 文件上传API测试
        print("\n📤 文件上传API测试:")
        print("-" * 80)
        # 创建测试文件
        test_content = "这是一个测试需求文档\n\n功能需求:\n1. 用户登录\n2. 商品管理\n3. 订单处理"
        files = {'file': ('test_requirement.txt', test_content, 'text/plain')}
        self.test_api("上传需求文档", "POST", "/api/upload/requirement", files=files)
        
        # 10. 知识库API测试
        print("\n📚 知识库API测试:")
        print("-" * 80)
        self.test_api("获取知识库统计", "GET", "/api/knowledge/stats")
        self.test_api("获取覆盖率报告", "GET", "/api/knowledge/coverage")
        
        # 生成测试报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*80)
        print("📋 测试报告")
        print("="*80 + "\n")
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["success"])
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"总测试数: {total}")
        print(f"通过: {passed} ✅")
        print(f"失败: {failed} ❌")
        print(f"通过率: {pass_rate:.1f}%")
        
        if failed > 0:
            print("\n失败的测试:")
            print("-" * 80)
            for result in self.test_results:
                if not result["success"]:
                    print(f"❌ {result['name']}")
                    print(f"   接口: {result['method']} {result['endpoint']}")
                    print(f"   状态码: {result['status_code']}")
                    print(f"   错误: {result['error']}")
                    print()
        
        # 保存详细报告到文件
        report_file = f"frontend_backend_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "test_time": datetime.now().isoformat(),
                "summary": {
                    "total": total,
                    "passed": passed,
                    "failed": failed,
                    "pass_rate": pass_rate
                },
                "results": self.test_results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n详细报告已保存到: {report_file}")
        
        # API对接情况总结
        print("\n" + "="*80)
        print("🔗 前后端API对接情况总结")
        print("="*80 + "\n")
        
        api_groups = {
            "Dashboard": ["dashboard"],
            "Projects": ["projects"],
            "API Explorer": ["apis", "swagger"],
            "Test Cases": ["test-cases", "testcases"],
            "Test Runs": ["test-runs"],
            "Reports": ["reports"],
            "Automation": ["automation"],
            "AI Insights": ["ai"],
            "File Upload": ["upload"],
            "Knowledge Base": ["knowledge"]
        }
        
        for group_name, keywords in api_groups.items():
            group_results = [r for r in self.test_results if any(k in r["endpoint"] for k in keywords)]
            if group_results:
                group_passed = sum(1 for r in group_results if r["success"])
                group_total = len(group_results)
                status = "✅" if group_passed == group_total else "⚠️"
                print(f"{status} {group_name}: {group_passed}/{group_total} 接口正常")
        
        print("\n" + "="*80)
        if pass_rate >= 90:
            print("🎉 前后端对接良好!")
        elif pass_rate >= 70:
            print("⚠️  前后端对接基本正常,部分接口需要修复")
        else:
            print("❌ 前后端对接存在较多问题,需要修复")
        print("="*80 + "\n")


def main():
    """主函数"""
    print("\n🔍 检查后端服务...")
    try:
        response = requests.get("http://127.0.0.1:8081/api/dashboard/stats", timeout=5)
        print("✅ 后端服务运行正常\n")
    except Exception as e:
        print(f"❌ 后端服务未启动或无法访问: {e}")
        print("\n请先启动后端服务:")
        print("  cd ai-test-platform")
        print("  py backend_api_server.py")
        return
    
    # 运行测试
    tester = FrontendBackendIntegrationTest()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
