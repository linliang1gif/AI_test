#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试完整工作流API
验证脚本生成和测试执行功能
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_generate_script():
    """测试脚本生成API"""
    print("\n" + "="*60)
    print("测试1: 生成自动化脚本")
    print("="*60)
    
    # 首先创建一个测试用例
    test_case = {
        "title": "验证用户登录功能",
        "module": "用户管理",
        "priority": "high",
        "status": "pending",
        "steps": [
            "打开登录页面",
            "输入用户名和密码",
            "点击登录按钮",
            "验证登录成功"
        ],
        "expected": "用户成功登录,跳转到首页",
        "source": "test"
    }
    
    # 创建测试用例
    response = requests.post(f"{BASE_URL}/api/test-cases", json=test_case)
    if response.status_code == 200:
        created_case = response.json()['data']
        testcase_id = created_case['id']
        print(f"✅ 测试用例创建成功, ID: {testcase_id}")
        
        # 生成脚本
        print(f"\n生成脚本...")
        response = requests.post(f"{BASE_URL}/api/testcases/{testcase_id}/generate-script")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                script = result.get('script', '')
                print(f"✅ 脚本生成成功!")
                print(f"\n生成的脚本预览 (前500字符):")
                print("-" * 60)
                print(script[:500])
                print("-" * 60)
                return testcase_id
            else:
                print(f"❌ 脚本生成失败: {result.get('message')}")
        else:
            print(f"❌ API请求失败: {response.status_code}")
    else:
        print(f"❌ 创建测试用例失败: {response.status_code}")
    
    return None

def test_execute_testcase(testcase_id: int):
    """测试执行测试用例API"""
    print("\n" + "="*60)
    print("测试2: 执行测试用例")
    print("="*60)
    
    print(f"执行测试用例 ID: {testcase_id}...")
    response = requests.post(f"{BASE_URL}/api/testcases/{testcase_id}/execute")
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            exec_result = result.get('result', {})
            print(f"✅ 测试执行完成!")
            print(f"\n执行结果:")
            print(f"  状态: {exec_result.get('status')}")
            print(f"  消息: {exec_result.get('message')}")
            print(f"  详情: {exec_result.get('details')}")
            print(f"  响应时间: {exec_result.get('response_time')}")
            
            if 'assertions' in exec_result:
                assertions = exec_result['assertions']
                print(f"\n断言结果:")
                print(f"  总计: {assertions.get('total', 0)}")
                print(f"  通过: {assertions.get('passed', 0)}")
                print(f"  失败: {assertions.get('failed', 0)}")
        else:
            print(f"❌ 测试执行失败: {result.get('message')}")
    else:
        print(f"❌ API请求失败: {response.status_code}")

def test_get_test_runs():
    """测试获取测试执行记录"""
    print("\n" + "="*60)
    print("测试3: 获取测试执行记录")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/api/test-runs")
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            runs = result.get('data', [])
            print(f"✅ 获取到 {len(runs)} 条执行记录")
            
            if runs:
                print(f"\n最新执行记录:")
                latest = runs[-1]
                print(f"  ID: {latest.get('id')}")
                print(f"  测试用例: {latest.get('testcase_title', 'N/A')}")
                print(f"  状态: {latest.get('status')}")
                print(f"  执行时间: {latest.get('executed_at')}")
        else:
            print(f"❌ 获取失败: {result.get('message')}")
    else:
        print(f"❌ API请求失败: {response.status_code}")

if __name__ == "__main__":
    print("\n🧪 开始测试完整工作流API...")
    
    # 测试1: 生成脚本
    testcase_id = test_generate_script()
    
    if testcase_id:
        # 等待一下
        time.sleep(1)
        
        # 测试2: 执行测试
        test_execute_testcase(testcase_id)
        
        # 等待一下
        time.sleep(1)
        
        # 测试3: 查看执行记录
        test_get_test_runs()
    
    print("\n" + "="*60)
    print("✅ 测试完成!")
    print("="*60)
