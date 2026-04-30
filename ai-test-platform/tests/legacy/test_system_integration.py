#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试系统各模块联动性
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8081"

def test_integration():
    print("=" * 70)
    print("AI测试平台 - 系统联动性测试")
    print("=" * 70)
    
    results = {
        "前后端连接": False,
        "数据持久化": False,
        "项目-测试用例关联": False,
        "API-测试用例关联": False,
        "测试执行流程": False,
        "AI生成功能": False,
        "报告生成": False
    }
    
    # 1. 测试前后端连接
    print("\n1️⃣  测试前后端连接...")
    try:
        r = requests.get(f"{BASE_URL}/api/projects")
        if r.status_code == 200:
            results["前后端连接"] = True
            print("   ✅ 前后端连接正常")
        else:
            print(f"   ❌ 前后端连接失败: {r.status_code}")
    except Exception as e:
        print(f"   ❌ 前后端连接失败: {e}")
    
    # 2. 测试数据持久化
    print("\n2️⃣  测试数据持久化...")
    try:
        # 创建测试项目
        project_data = {
            "name": "联动测试项目",
            "description": "测试系统联动性",
            "environment": "development",
            "baseUrl": "http://localhost:8080"
        }
        r = requests.post(f"{BASE_URL}/api/projects", json=project_data)
        if r.status_code == 200:
            project_id = r.json().get("project", {}).get("id")
            
            # 验证项目是否保存
            r2 = requests.get(f"{BASE_URL}/api/projects")
            projects = r2.json().get("projects", [])
            if any(p["id"] == project_id for p in projects):
                results["数据持久化"] = True
                print(f"   ✅ 数据持久化正常 (项目ID: {project_id})")
            else:
                print("   ❌ 数据持久化失败: 项目未保存")
        else:
            print(f"   ❌ 创建项目失败: {r.status_code}")
    except Exception as e:
        print(f"   ❌ 数据持久化测试失败: {e}")
    
    # 3. 测试项目-测试用例关联
    print("\n3️⃣  测试项目-测试用例关联...")
    try:
        # 获取项目列表
        r = requests.get(f"{BASE_URL}/api/projects")
        projects = r.json().get("projects", [])
        
        # 获取测试用例列表
        r2 = requests.get(f"{BASE_URL}/api/test-cases")
        test_cases = r2.json().get("testCases", [])
        
        # 检查是否有关联字段
        if projects and test_cases:
            has_project_field = any("project_id" in tc or "projectId" in tc for tc in test_cases)
            if has_project_field:
                results["项目-测试用例关联"] = True
                print("   ✅ 项目-测试用例关联字段存在")
            else:
                print("   ⚠️  项目-测试用例关联字段缺失 (需要添加)")
        else:
            print("   ⚠️  暂无数据，无法测试关联")
    except Exception as e:
        print(f"   ❌ 关联测试失败: {e}")
    
    # 4. 测试API-测试用例关联
    print("\n4️⃣  测试API-测试用例关联...")
    try:
        r = requests.get(f"{BASE_URL}/api/apis")
        apis = r.json().get("apis", [])
        
        r2 = requests.get(f"{BASE_URL}/api/test-cases")
        test_cases = r2.json().get("testCases", [])
        
        # 检查是否有API关联字段
        if test_cases:
            has_api_field = any("api_id" in tc or "apiId" in tc for tc in test_cases)
            if has_api_field:
                results["API-测试用例关联"] = True
                print("   ✅ API-测试用例关联字段存在")
            else:
                print("   ⚠️  API-测试用例关联字段缺失 (需要添加)")
        else:
            print("   ⚠️  暂无测试用例数据")
    except Exception as e:
        print(f"   ❌ API关联测试失败: {e}")
    
    # 5. 测试测试执行流程
    print("\n5️⃣  测试测试执行流程...")
    try:
        # 检查测试运行API
        r = requests.get(f"{BASE_URL}/api/test-runs")
        if r.status_code == 200:
            test_runs = r.json().get("testRuns", [])
            
            # 检查是否有执行API
            r2 = requests.post(f"{BASE_URL}/api/test-runs", json={
                "project_id": 1,
                "environment": "development"
            })
            if r2.status_code == 200:
                results["测试执行流程"] = True
                print("   ✅ 测试执行流程正常")
            else:
                print(f"   ⚠️  测试执行API响应异常: {r2.status_code}")
        else:
            print(f"   ❌ 测试运行API失败: {r.status_code}")
    except Exception as e:
        print(f"   ❌ 测试执行流程测试失败: {e}")
    
    # 6. 测试AI生成功能
    print("\n6️⃣  测试AI生成功能...")
    try:
        # 检查AI提供商状态
        r = requests.get(f"{BASE_URL}/api/ai/current")
        if r.status_code == 200:
            ai_info = r.json()
            print(f"   ℹ️  当前AI提供商: {ai_info.get('provider', 'unknown')}")
            
            # 检查Ollama状态
            r2 = requests.get(f"{BASE_URL}/api/ai/ollama/status")
            if r2.status_code == 200:
                ollama_status = r2.json()
                if ollama_status.get("available"):
                    results["AI生成功能"] = True
                    print(f"   ✅ AI生成功能可用 (模型: {ollama_status.get('model', 'unknown')})")
                else:
                    print("   ⚠️  Ollama服务不可用")
            else:
                print("   ⚠️  无法检查Ollama状态")
        else:
            print(f"   ❌ AI API失败: {r.status_code}")
    except Exception as e:
        print(f"   ❌ AI功能测试失败: {e}")
    
    # 7. 测试报告生成
    print("\n7️⃣  测试报告生成...")
    try:
        r = requests.get(f"{BASE_URL}/api/reports")
        if r.status_code == 200:
            reports = r.json().get("reports", [])
            results["报告生成"] = True
            print(f"   ✅ 报告API正常 (当前报告数: {len(reports)})")
        else:
            print(f"   ❌ 报告API失败: {r.status_code}")
    except Exception as e:
        print(f"   ❌ 报告测试失败: {e}")
    
    # 总结
    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 70)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for name, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {name}")
    
    print("\n" + "=" * 70)
    print(f"总体评分: {passed}/{total} ({passed*100//total}%)")
    print("=" * 70)
    
    # 联动性评估
    print("\n📊 联动性评估:")
    if passed >= 6:
        print("   🌟 优秀 - 系统各模块联动良好")
    elif passed >= 4:
        print("   👍 良好 - 核心功能联动正常，部分功能需完善")
    elif passed >= 2:
        print("   ⚠️  一般 - 基础功能可用，需要加强模块间联动")
    else:
        print("   ❌ 较差 - 系统联动存在较多问题")
    
    print("\n💡 改进建议:")
    if not results["项目-测试用例关联"]:
        print("   • 添加项目与测试用例的关联字段")
    if not results["API-测试用例关联"]:
        print("   • 添加API与测试用例的关联字段")
    if not results["AI生成功能"]:
        print("   • 检查Ollama服务是否正常运行")
    if not results["测试执行流程"]:
        print("   • 完善测试执行流程的实现")

if __name__ == "__main__":
    test_integration()
