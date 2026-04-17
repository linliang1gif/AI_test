#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统就绪测试 - 验证前后端和 AI 功能
"""

import requests
import time

def test_system():
    """测试系统是否就绪"""
    
    print("=" * 60)
    print("🚀 AI 测试平台系统就绪检查")
    print("=" * 60)
    
    results = []
    
    # 1. 后端健康检查
    print("\n1. 后端服务检查...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ 后端服务正常运行")
            results.append(("后端服务", True))
        else:
            print(f"   ❌ 后端服务异常: {response.status_code}")
            results.append(("后端服务", False))
    except Exception as e:
        print(f"   ❌ 后端服务无法访问: {e}")
        results.append(("后端服务", False))
    
    # 2. 前端服务检查
    print("\n2. 前端服务检查...")
    try:
        response = requests.get("http://localhost:5173", timeout=5)
        if response.status_code == 200:
            print("   ✅ 前端服务正常运行")
            results.append(("前端服务", True))
        else:
            print(f"   ❌ 前端服务异常: {response.status_code}")
            results.append(("前端服务", False))
    except Exception as e:
        print(f"   ❌ 前端服务无法访问: {e}")
        results.append(("前端服务", False))
    
    # 3. AI 提供商检查
    print("\n3. AI 提供商检查...")
    try:
        response = requests.get("http://localhost:8000/api/ai/providers", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ AI 提供商接口正常")
            print(f"   默认提供商: {data.get('default')}")
            for provider in data.get('providers', []):
                status_icon = "✅" if provider['status'] == 'available' else "❌"
                print(f"   {status_icon} {provider['name']}: {provider['status']}")
            results.append(("AI 提供商", True))
        else:
            print(f"   ❌ AI 提供商接口异常: {response.status_code}")
            results.append(("AI 提供商", False))
    except Exception as e:
        print(f"   ❌ AI 提供商接口无法访问: {e}")
        results.append(("AI 提供商", False))
    
    # 4. AI 生成测试用例（快速测试）
    print("\n4. AI 生成功能检查...")
    try:
        payload = {
            "requirement": "测试登录功能",
            "module": "测试",
            "count": 1
        }
        response = requests.post(
            "http://localhost:8000/api/ai/generate-testcases",
            json=payload,
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   ✅ AI 生成测试用例成功")
                print(f"   生成了 {data.get('count')} 个测试用例")
                results.append(("AI 生成功能", True))
            else:
                print(f"   ❌ AI 生成失败: {data.get('error')}")
                results.append(("AI 生成功能", False))
        else:
            print(f"   ❌ AI 生成接口异常: {response.status_code}")
            results.append(("AI 生成功能", False))
    except Exception as e:
        print(f"   ❌ AI 生成功能测试失败: {e}")
        results.append(("AI 生成功能", False))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("检查结果汇总")
    print("=" * 60)
    
    for name, status in results:
        icon = "✅" if status else "❌"
        print(f"{icon} {name}")
    
    passed = sum(1 for _, status in results if status)
    total = len(results)
    
    print("=" * 60)
    print(f"通过: {passed}/{total}")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 系统完全就绪！")
        print("\n📋 可用功能:")
        print("  ✅ AI 生成测试用例")
        print("  ✅ AI 生成测试脚本")
        print("  ✅ 测试用例管理")
        print("  ✅ 测试执行")
        print("  ✅ 测试报告")
        print("\n🌐 访问地址:")
        print("  前端: http://localhost:5173")
        print("  后端: http://localhost:8000")
        print("  API 文档: http://localhost:8000/docs")
        return True
    else:
        print(f"\n⚠️  {total - passed} 项检查失败")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("AI 测试平台 - 系统就绪检查")
    print("=" * 60)
    print()
    
    success = test_system()
    
    if not success:
        print("\n💡 故障排查:")
        print("  1. 确认后端服务正在运行")
        print("  2. 确认前端服务正在运行")
        print("  3. 确认 Ollama 服务正在运行")
        print("  4. 检查端口 8000 和 5173 是否被占用")
