#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试测试用例生成API - 当前状态验证
"""

import requests
import io

def test_testcase_generate_api():
    """测试测试用例生成API"""
    print("=" * 60)
    print("🧪 测试测试用例生成API")
    print("=" * 60)
    
    # 创建测试文件
    test_content = """
    用户管理模块需求:
    1. 用户可以注册账号
    2. 用户可以登录系统
    3. 用户可以修改个人信息
    4. 用户可以重置密码
    """.encode('utf-8')
    
    files = {
        'file': ('test_requirement.txt', io.BytesIO(test_content), 'text/plain')
    }
    
    try:
        print("\n📤 发送请求到: http://localhost:8000/api/testcases/generate")
        response = requests.post(
            "http://localhost:8000/api/testcases/generate",
            files=files,
            timeout=30
        )
        
        print(f"📥 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 请求成功!")
            print(f"\n📊 生成结果:")
            print(f"  - 成功: {result.get('success')}")
            print(f"  - 数量: {result.get('count')}")
            print(f"  - 消息: {result.get('message')}")
            
            if result.get('testCases'):
                print(f"\n📝 生成的测试用例:")
                for i, tc in enumerate(result['testCases'], 1):
                    print(f"\n  {i}. {tc.get('title')}")
                    print(f"     模块: {tc.get('module')}")
                    print(f"     优先级: {tc.get('priority')}")
                    print(f"     状态: {tc.get('status')}")
            
            return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_via_proxy():
    """通过前端代理测试"""
    print("\n" + "=" * 60)
    print("🧪 通过前端代理测试")
    print("=" * 60)
    
    test_content = b"Test requirement document"
    
    files = {
        'file': ('test.txt', io.BytesIO(test_content), 'text/plain')
    }
    
    try:
        print("\n📤 发送请求到: http://localhost:5174/api/testcases/generate")
        response = requests.post(
            "http://localhost:5174/api/testcases/generate",
            files=files,
            timeout=30
        )
        
        print(f"📥 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 代理请求成功!")
            print(f"  - 生成数量: {result.get('count')}")
            return True
        else:
            print(f"❌ 代理请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 代理测试失败: {e}")
        return False

if __name__ == "__main__":
    print("\n🚀 开始测试...\n")
    
    # 测试1: 直接访问后端
    test1 = test_testcase_generate_api()
    
    # 测试2: 通过前端代理
    test2 = test_via_proxy()
    
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    print(f"直接访问后端: {'✅ 通过' if test1 else '❌ 失败'}")
    print(f"通过前端代理: {'✅ 通过' if test2 else '❌ 失败'}")
    print("=" * 60)
    
    if test1 and test2:
        print("\n🎉 所有测试通过! API工作正常!")
    else:
        print("\n⚠️  部分测试失败,请检查配置")
