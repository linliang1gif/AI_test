#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试后端 AI 功能
"""

import requests
import json

def test_ai_generate_testcases():
    """测试 AI 生成测试用例接口"""
    
    base_url = "http://localhost:8000"
    
    print("=" * 60)
    print("测试后端 AI 生成测试用例")
    print("=" * 60)
    
    # 测试数据
    requirement = """
    用户登录功能需求：
    1. 用户可以使用用户名和密码登录
    2. 登录成功后返回 JWT token
    3. 登录失败返回错误信息
    4. 支持记住密码功能
    """
    
    payload = {
        "requirement": requirement,
        "module": "用户管理",
        "count": 3
    }
    
    print(f"\n📝 需求文档:\n{requirement}")
    print(f"\n🤖 正在调用后端 AI 接口...")
    
    try:
        response = requests.post(
            f"{base_url}/api/ai/generate-testcases",
            json=payload,
            timeout=60
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n✅ AI 生成成功!")
            print(f"📊 生成了 {len(result.get('testcases', []))} 个测试用例:")
            
            for i, tc in enumerate(result.get('testcases', []), 1):
                print(f"\n  {i}. {tc.get('title', '未命名')}")
                print(f"     模块: {tc.get('module', '-')}")
                print(f"     优先级: {tc.get('priority', '-')}")
                print(f"     步骤数: {len(tc.get('steps', []))}")
                if tc.get('steps'):
                    print(f"     步骤: {', '.join(tc['steps'][:2])}...")
            
            return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"响应: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_generate_script():
    """测试 AI 生成测试脚本接口"""
    
    base_url = "http://localhost:8000"
    
    print("\n\n" + "=" * 60)
    print("测试后端 AI 生成测试脚本")
    print("=" * 60)
    
    # 测试用例数据
    testcase = {
        "title": "用户登录-正常场景",
        "module": "用户管理",
        "priority": "high",
        "steps": [
            "打开登录页面",
            "输入用户名: admin",
            "输入密码: 123456",
            "点击登录按钮"
        ],
        "expected": "登录成功，跳转到首页"
    }
    
    payload = {
        "testcase": testcase,
        "framework": "pytest"
    }
    
    print(f"\n📝 测试用例: {testcase['title']}")
    print(f"🤖 正在调用后端 AI 接口...")
    
    try:
        response = requests.post(
            f"{base_url}/api/ai/generate-script",
            json=payload,
            timeout=60
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n✅ AI 生成成功!")
            print(f"📄 生成的脚本:")
            print("-" * 60)
            script = result.get('script', '')
            print(script[:500] + "..." if len(script) > 500 else script)
            print("-" * 60)
            
            return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"响应: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_health():
    """测试健康检查"""
    
    base_url = "http://localhost:8000"
    
    print("\n\n" + "=" * 60)
    print("测试健康检查")
    print("=" * 60)
    
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 后端服务正常")
            print(f"状态: {result.get('status')}")
            print(f"AI 提供商: {result.get('ai_provider')}")
            print(f"AI 模型: {result.get('ai_model')}")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False


if __name__ == "__main__":
    print("\n🚀 后端 AI 功能测试\n")
    
    tests = [
        ("健康检查", test_health),
        ("AI 生成测试用例", test_ai_generate_testcases),
        ("AI 生成测试脚本", test_ai_generate_script),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} 测试异常: {e}")
            results.append((name, False))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print("=" * 60)
    print(f"总计: {passed}/{total} 通过")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 所有测试通过！后端 AI 功能正常工作！")
        print("\n💡 现在可以:")
        print("  1. 访问前端: http://localhost:5173")
        print("  2. 访问 API 文档: http://localhost:8000/docs")
        print("  3. 在前端使用 AI 生成功能")
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
