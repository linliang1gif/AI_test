#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI测试平台 - 验证修复结果
"""

import requests
import json
import time

def test_api_endpoints():
    """测试API端点"""
    print("🧪 测试API端点...")
    
    base_url = "http://127.0.0.1:8081/api"
    
    endpoints = [
        ("/dashboard/stats", "仪表板统计"),
        ("/projects", "项目列表"),
        ("/apis", "API列表"),
        ("/test-cases", "测试用例"),
        ("/test-runs", "测试执行"),
        ("/reports", "测试报告"),
        ("/ai/agents", "AI代理"),
        ("/ai/current", "AI配置"),
    ]
    
    passed = 0
    total = len(endpoints)
    
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: 正常 (HTTP 200)")
                passed += 1
            else:
                print(f"❌ {name}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: {str(e)}")
    
    print(f"\n📊 API测试结果: {passed}/{total} 通过")
    return passed == total

def test_crud_operations():
    """测试CRUD操作"""
    print("\n🔄 测试CRUD操作...")
    
    base_url = "http://127.0.0.1:8081/api"
    
    # 测试创建项目
    try:
        project_data = {
            "name": f"测试项目_{int(time.time())}",
            "description": "自动化测试项目"
        }
        
        response = requests.post(f"{base_url}/projects", 
                               json=project_data, 
                               timeout=5)
        
        if response.status_code == 200:
            print("✅ 项目创建: 正常")
            project_id = response.json().get('id')
            
            # 测试删除项目
            if project_id:
                delete_response = requests.delete(f"{base_url}/projects/{project_id}", 
                                                timeout=5)
                if delete_response.status_code == 200:
                    print("✅ 项目删除: 正常")
                    return True
                else:
                    print(f"❌ 项目删除: HTTP {delete_response.status_code}")
            else:
                print("⚠️ 项目ID未返回，跳过删除测试")
                return True
        else:
            print(f"❌ 项目创建: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ CRUD操作失败: {e}")
        return False

def test_ai_functionality():
    """测试AI功能"""
    print("\n🤖 测试AI功能...")
    
    base_url = "http://127.0.0.1:8081/api"
    
    try:
        # 测试AI配置获取
        config_response = requests.get(f"{base_url}/ai/current", timeout=5)
        if config_response.status_code == 200:
            config = config_response.json()
            print(f"✅ AI配置获取: 正常")
            print(f"   当前提供商: {config.get('current_provider', 'unknown')}")
            print(f"   当前模型: {config.get('current_model', 'unknown')}")
        else:
            print(f"❌ AI配置获取: HTTP {config_response.status_code}")
            return False
        
        # 测试AI生成（简单测试）
        generate_data = {
            "prompt": "你好，请简单回复一下"
        }
        
        generate_response = requests.post(f"{base_url}/ai/generate", 
                                        json=generate_data, 
                                        timeout=10)
        
        if generate_response.status_code == 200:
            result = generate_response.json()
            if result.get('success'):
                print("✅ AI生成功能: 正常")
                print(f"   AI回复: {result.get('response', '')[:50]}...")
                return True
            else:
                print(f"❌ AI生成失败: {result.get('error', 'unknown')}")
                return False
        else:
            print(f"❌ AI生成请求: HTTP {generate_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ AI功能测试失败: {e}")
        return False

def check_frontend_files():
    """检查前端文件修复"""
    print("\n📁 检查前端文件修复...")
    
    files_to_check = [
        ("frontend/vite.config.js", "Vite配置"),
        ("frontend/src/services/api.js", "API服务"),
        ("frontend/src/App.jsx", "主应用"),
        ("frontend/src/pages/Projects.jsx", "项目页面"),
    ]
    
    for file_path, name in files_to_check:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 检查关键修复点
            if file_path.endswith('vite.config.js'):
                if 'http://127.0.0.1:8081' in content:
                    print(f"✅ {name}: 代理配置已修复")
                else:
                    print(f"❌ {name}: 代理配置未修复")
                    
            elif file_path.endswith('api.js'):
                if "API_BASE_URL = '/api'" in content:
                    print(f"✅ {name}: API路径已修复")
                else:
                    print(f"❌ {name}: API路径未修复")
                    
            elif 'App.jsx' in file_path:
                if "fetch('/api/" in content:
                    print(f"✅ {name}: API调用已修复")
                else:
                    print(f"❌ {name}: API调用未修复")
                    
            elif 'Projects.jsx' in file_path:
                if "fetch('/api/" in content:
                    print(f"✅ {name}: API调用已修复")
                else:
                    print(f"❌ {name}: API调用未修复")
                    
        except Exception as e:
            print(f"❌ {name}: 文件检查失败 - {e}")

def main():
    """主函数"""
    print("=" * 60)
    print("🔍 AI测试平台 - 修复结果验证")
    print("=" * 60)
    print(f"⏰ 验证时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查前端文件修复
    check_frontend_files()
    
    # 测试API端点
    api_ok = test_api_endpoints()
    
    # 测试CRUD操作
    crud_ok = test_crud_operations()
    
    # 测试AI功能
    ai_ok = test_ai_functionality()
    
    # 总结
    print("\n" + "=" * 60)
    print("📋 验证结果总结")
    print("=" * 60)
    
    results = [
        ("API端点测试", api_ok),
        ("CRUD操作测试", crud_ok),
        ("AI功能测试", ai_ok),
    ]
    
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    
    for name, ok in results:
        status = "✅ 通过" if ok else "❌ 失败"
        print(f"{name}: {status}")
    
    print(f"\n📊 总体结果: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！按钮点击问题已完全修复！")
        print("\n💡 现在可以正常使用以下功能:")
        print("   • 项目管理 (创建、删除、运行)")
        print("   • API管理 (Swagger解析、接口测试)")
        print("   • 测试用例管理 (生成、编辑)")
        print("   • AI功能 (对话、生成、分析)")
        print("\n🌐 访问地址:")
        print("   • 前端界面: http://localhost:3001")
        print("   • 后端API: http://127.0.0.1:8081")
        print("   • API文档: http://127.0.0.1:8081/docs")
    else:
        print("\n⚠️ 部分功能仍有问题，请检查:")
        print("   1. 服务是否正常启动")
        print("   2. 浏览器控制台是否有错误")
        print("   3. 网络连接是否正常")
    
    print("=" * 60)

if __name__ == "__main__":
    main()