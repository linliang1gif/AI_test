#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
前端问题诊断脚本
"""

import requests
import json
import time
from pathlib import Path

def test_backend_api():
    """测试后端API"""
    print("🔧 测试后端API...")
    try:
        response = requests.get("http://127.0.0.1:8081/api/dashboard/stats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("   ✅ 后端API正常")
            print(f"   📊 数据: 总测试{data['totalTests']}, 通过{data['passed']}, 失败{data['failed']}")
            return True
        else:
            print(f"   ❌ 后端API返回错误: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 后端API连接失败: {e}")
        return False

def test_frontend_proxy():
    """测试前端代理"""
    print("🌐 测试前端代理...")
    try:
        response = requests.get("http://localhost:3000/api/dashboard/stats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("   ✅ 前端代理正常")
            print(f"   📊 代理数据: 总测试{data['totalTests']}, 通过{data['passed']}, 失败{data['failed']}")
            return True
        else:
            print(f"   ❌ 前端代理返回错误: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 前端代理连接失败: {e}")
        return False

def test_frontend_page():
    """测试前端页面"""
    print("📱 测试前端页面...")
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            content = response.text
            if "<!doctype html>" in content.lower():
                print("   ✅ 前端页面可访问")
                if "root" in content:
                    print("   ✅ React根元素存在")
                else:
                    print("   ⚠️  React根元素可能缺失")
                return True
            else:
                print("   ❌ 前端页面内容异常")
                return False
        else:
            print(f"   ❌ 前端页面返回错误: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 前端页面连接失败: {e}")
        return False

def check_frontend_files():
    """检查前端文件"""
    print("📁 检查前端文件...")
    frontend_dir = Path("ai-test-platform/frontend")
    
    files_to_check = [
        "index.html",
        "src/main.jsx",
        "src/App.jsx",
        "src/index.css",
        "package.json",
        "vite.config.js"
    ]
    
    all_exist = True
    for file_path in files_to_check:
        full_path = frontend_dir / file_path
        if full_path.exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} 缺失")
            all_exist = False
    
    return all_exist

def test_all_apis():
    """测试所有API端点"""
    print("🔍 测试所有API端点...")
    
    endpoints = [
        "/api/dashboard/stats",
        "/api/projects",
        "/api/test-cases",
        "/api/apis",
        "/api/test-runs",
        "/api/reports"
    ]
    
    working_endpoints = 0
    for endpoint in endpoints:
        try:
            response = requests.get(f"http://localhost:3000{endpoint}", timeout=3)
            if response.status_code == 200:
                print(f"   ✅ {endpoint}")
                working_endpoints += 1
            else:
                print(f"   ❌ {endpoint} - {response.status_code}")
        except Exception as e:
            print(f"   ❌ {endpoint} - {str(e)[:50]}...")
    
    print(f"   📊 工作正常的端点: {working_endpoints}/{len(endpoints)}")
    return working_endpoints == len(endpoints)

def main():
    """主函数"""
    print("=" * 60)
    print("🚀 AI测试平台 - 前端问题诊断")
    print("=" * 60)
    
    # 测试步骤
    tests = [
        ("后端API", test_backend_api),
        ("前端代理", test_frontend_proxy),
        ("前端页面", test_frontend_page),
        ("前端文件", check_frontend_files),
        ("所有API", test_all_apis)
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        results[test_name] = test_func()
        time.sleep(1)
    
    # 总结
    print("\n" + "=" * 60)
    print("📋 诊断结果总结:")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")
    
    print(f"\n📊 总体状态: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！前端应该正常工作。")
        print("💡 如果页面仍然没有数据，请检查浏览器控制台错误。")
    else:
        print("⚠️  发现问题，请根据上述结果进行修复。")
    
    print("\n🌐 访问地址:")
    print("   前端: http://localhost:3000")
    print("   后端: http://127.0.0.1:8081")
    print("   API文档: http://127.0.0.1:8081/docs")

if __name__ == "__main__":
    main()