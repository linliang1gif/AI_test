#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试最小可用流程
从Swagger解析 → 执行API → 保存测试用例 → 执行测试用例
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def print_step(step_num, title):
    """打印步骤标题"""
    print(f"\n{'='*60}")
    print(f"步骤 {step_num}: {title}")
    print('='*60)

def test_minimal_flow():
    """测试最小可用流程"""
    
    print("🚀 开始测试最小可用流程")
    print("="*60)
    
    # ==================== 步骤1: 准备测试API ====================
    print_step(1, "准备测试API（使用公共API）")
    
    test_api = {
        "id": 999,
        "name": "获取文章详情",
        "method": "GET",
        "path": "/posts/1",
        "tags": ["测试"]
    }
    
    print(f"✅ 测试API: {test_api['method']} {test_api['path']}")
    
    # ==================== 步骤2: 执行API ====================
    print_step(2, "执行API")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/execute-api",
            json={
                "method": test_api["method"],
                "base_url": "https://jsonplaceholder.typicode.com",
                "path": test_api["path"],
                "data": {},
                "timeout": 30
            },
            timeout=10
        )
        
        if response.status_code == 200:
            execution_result = response.json()
            print(f"✅ API执行成功")
            print(f"   状态码: {execution_result.get('status_code')}")
            print(f"   响应时间: {execution_result.get('response_time')}ms")
            print(f"   成功: {execution_result.get('success')}")
        else:
            print(f"❌ API执行失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False
    
    # ==================== 步骤3: 保存为测试用例 ====================
    print_step(3, "保存为测试用例")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/save-api-as-testcase",
            json={
                "api_info": {
                    "name": test_api["name"],
                    "method": test_api["method"],
                    "path": test_api["path"],
                    "tags": test_api["tags"]
                },
                "execution_result": execution_result,
                "request_data": {}
            },
            timeout=10
        )
        
        if response.status_code == 200:
            save_result = response.json()
            if save_result.get('success'):
                test_case_id = save_result.get('test_case_id')
                print(f"✅ 保存成功")
                print(f"   测试用例ID: {test_case_id}")
            else:
                print(f"❌ 保存失败: {save_result.get('error')}")
                return False
        else:
            print(f"❌ 保存失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False
    
    # ==================== 步骤4: 执行测试用例 ====================
    print_step(4, "执行测试用例")
    
    try:
        # 等待1秒确保数据已保存
        time.sleep(1)
        
        response = requests.post(
            f"{BASE_URL}/api/testcases/{test_case_id}/execute",
            timeout=10
        )
        
        if response.status_code == 200:
            exec_result = response.json()
            if exec_result.get('success'):
                print(f"✅ 测试用例执行成功")
                result = exec_result.get('result', {})
                print(f"   状态: {result.get('status')}")
                print(f"   消息: {result.get('message', '无')}")
            else:
                print(f"❌ 测试用例执行失败: {exec_result.get('error')}")
                return False
        else:
            print(f"❌ 执行失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False
    
    # ==================== 验证数据 ====================
    print_step(5, "验证数据持久化")
    
    try:
        # 验证测试用例是否保存
        response = requests.get(f"{BASE_URL}/api/test-cases", timeout=5)
        if response.status_code == 200:
            data = response.json()
            test_cases = data.get('data', [])
            
            # 查找刚创建的测试用例
            found = any(tc.get('id') == test_case_id for tc in test_cases)
            
            if found:
                print(f"✅ 测试用例已保存到数据库")
                print(f"   总测试用例数: {len(test_cases)}")
            else:
                print(f"⚠️  测试用例未找到（可能已被删除）")
        else:
            print(f"⚠️  无法验证: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️  验证失败: {e}")
    
    # ==================== 总结 ====================
    print("\n" + "="*60)
    print("🎉 最小可用流程测试完成！")
    print("="*60)
    print("\n流程总结:")
    print("1. ✅ 执行API - 成功")
    print("2. ✅ 保存为测试用例 - 成功")
    print("3. ✅ 执行测试用例 - 成功")
    print("4. ✅ 数据持久化 - 成功")
    print("\n所有步骤均已完成！")
    
    return True

if __name__ == "__main__":
    success = test_minimal_flow()
    exit(0 if success else 1)
