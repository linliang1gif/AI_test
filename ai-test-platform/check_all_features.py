#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整功能检查脚本
检查所有前后端功能是否正常实现
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8081"

def print_section(title):
    print("\n" + "="*60)
    print(title)
    print("="*60)

def test_api(name, method, url, data=None, files=None):
    """测试API接口"""
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            if files:
                response = requests.post(url, files=files)
            else:
                response = requests.post(url, json=data)
        
        status = "✅" if response.status_code == 200 else "❌"
        print(f"{status} {name}: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"   响应: {json.dumps(result, ensure_ascii=False)[:100]}...")
            except:
                print(f"   响应: {response.text[:100]}...")
        else:
            print(f"   错误: {response.text[:100]}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ {name}: 异常 - {str(e)}")
        return False

def main():
    print("\n" + "="*60)
    print("AI测试平台 - 完整功能检查")
    print("="*60)
    
    results = {}
    
    # 1. Dashboard API
    print_section("1. Dashboard (仪表板)")
    results["Dashboard - 统计数据"] = test_api(
        "获取统计数据", "GET", f"{BASE_URL}/api/dashboard/stats"
    )
    
    # 2. Projects API
    print_section("2. Projects (项目管理)")
    results["Projects - 获取列表"] = test_api(
        "获取项目列表", "GET", f"{BASE_URL}/api/projects"
    )
    results["Projects - 创建项目"] = test_api(
        "创建新项目", "POST", f"{BASE_URL}/api/projects",
        data={"name": "测试项目", "description": "测试描述"}
    )
    
    # 3. Test Cases API
    print_section("3. Test Cases (测试用例)")
    results["TestCases - 获取列表"] = test_api(
        "获取测试用例列表", "GET", f"{BASE_URL}/api/test-cases"
    )
    results["TestCases - 生成用例"] = test_api(
        "生成测试用例", "POST", f"{BASE_URL}/api/testcases/generate",
        files={"file": ("test.txt", b"test content", "text/plain")}
    )
    results["TestCases - 导出Excel"] = test_api(
        "导出Excel", "GET", f"{BASE_URL}/api/test-cases/export"
    )
    
    # 4. Test Runs API
    print_section("4. Test Runs (测试运行)")
    results["TestRuns - 获取列表"] = test_api(
        "获取测试运行列表", "GET", f"{BASE_URL}/api/test-runs"
    )
    results["TestRuns - 启动测试"] = test_api(
        "启动新测试", "POST", f"{BASE_URL}/api/test-runs/start",
        data={"environment": "staging"}
    )
    
    # 5. Automation API
    print_section("5. Automation (自动化脚本)")
    results["Automation - 获取脚本"] = test_api(
        "获取自动化脚本", "GET", f"{BASE_URL}/api/automation/scripts"
    )
    results["Automation - 生成脚本"] = test_api(
        "生成新脚本", "POST", f"{BASE_URL}/api/ai/generate",
        data={"type": "automation_script", "framework": "pytest"}
    )
    
    # 6. Reports API
    print_section("6. Reports (测试报告)")
    results["Reports - 获取列表"] = test_api(
        "获取报告列表", "GET", f"{BASE_URL}/api/reports"
    )
    results["Reports - 生成报告"] = test_api(
        "生成新报告", "POST", f"{BASE_URL}/api/reports/generate",
        data={"type": "comprehensive"}
    )
    
    # 7. API Explorer
    print_section("7. API Explorer (API探索)")
    results["APIExplorer - 获取接口"] = test_api(
        "获取API接口", "GET", f"{BASE_URL}/api/api-explorer/endpoints"
    )
    results["APIExplorer - 测试接口"] = test_api(
        "测试API接口", "POST", f"{BASE_URL}/api/api-explorer/test",
        data={"url": "http://example.com", "method": "GET"}
    )
    
    # 8. AI Insights
    print_section("8. AI Insights (AI洞察)")
    results["AIInsights - 获取代理"] = test_api(
        "获取AI代理", "GET", f"{BASE_URL}/api/ai/agents"
    )
    results["AIInsights - AI分析"] = test_api(
        "AI分析", "POST", f"{BASE_URL}/api/ai/analyze",
        data={"type": "bug_analysis", "data": "test"}
    )
    
    # 9. Knowledge Base
    print_section("9. Knowledge Base (知识库)")
    results["KnowledgeBase - 搜索"] = test_api(
        "搜索知识库", "GET", f"{BASE_URL}/api/knowledge/search?q=test"
    )
    
    # 10. Settings
    print_section("10. Settings (设置)")
    results["Settings - 获取配置"] = test_api(
        "获取系统配置", "GET", f"{BASE_URL}/api/settings"
    )
    
    # 汇总结果
    print_section("功能检查汇总")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    print(f"\n总计: {total} 个功能")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"通过率: {passed/total*100:.1f}%")
    
    print("\n详细结果:")
    for name, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {name}")
    
    # 未实现的功能
    print_section("需要实现的功能")
    failed_features = [name for name, result in results.items() if not result]
    if failed_features:
        for feature in failed_features:
            print(f"❌ {feature}")
    else:
        print("🎉 所有功能都已实现!")

if __name__ == "__main__":
    main()
