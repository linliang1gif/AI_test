#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证backend_api_server.py中的ExecutionEngine集成
需要先启动后端服务器: cd ai-test-platform && py backend_api_server.py
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """测试健康检查"""
    print("=" * 60)
    print("测试1: 健康检查")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        assert response.status_code == 200
        print("✅ 健康检查通过")
        return True
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False

def test_execute_api():
    """测试API执行端点（使用ExecutionEngine）"""
    print("\n" + "=" * 60)
    print("测试2: API执行端点")
    print("=" * 60)
    
    try:
        # 测试数据
        payload = {
            "method": "GET",
            "base_url": "https://jsonplaceholder.typicode.com",
            "path": "/posts/1",
            "data": {},
            "timeout": 30
        }
        
        print(f"请求: POST {BASE_URL}/api/execute-api")
        print(f"数据: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            f"{BASE_URL}/api/execute-api",
            json=payload,
            timeout=30
        )
        
        print(f"\n状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        # 验证ExecutionEngine特有字段
        assert "trace_id" in result, "应该包含trace_id"
        assert "success" in result, "应该包含success"
        assert "status_code" in result, "应该包含status_code"
        assert "response_time" in result, "应该包含response_time"
        
        print(f"\n✅ trace_id: {result.get('trace_id')}")
        print(f"✅ 执行成功: {result.get('success')}")
        print(f"✅ 状态码: {result.get('status_code')}")
        print(f"✅ 响应时间: {result.get('response_time')}ms")
        
        print("✅ API执行端点测试通过")
        return True
        
    except Exception as e:
        print(f"❌ API执行端点测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_save_and_execute_testcase():
    """测试保存并执行测试用例"""
    print("\n" + "=" * 60)
    print("测试3: 保存并执行测试用例")
    print("=" * 60)
    
    try:
        # 步骤1: 执行API并保存为测试用例
        print("\n步骤1: 执行API...")
        api_payload = {
            "method": "GET",
            "base_url": "https://jsonplaceholder.typicode.com",
            "path": "/posts/1",
            "data": {}
        }
        
        api_response = requests.post(
            f"{BASE_URL}/api/execute-api",
            json=api_payload,
            timeout=30
        )
        
        api_result = api_response.json()
        print(f"API执行结果: success={api_result.get('success')}, trace_id={api_result.get('trace_id')}")
        
        # 步骤2: 保存为测试用例
        print("\n步骤2: 保存为测试用例...")
        save_payload = {
            "api_info": {
                "name": "获取文章详情",
                "method": "GET",
                "path": "/posts/1",
                "tags": ["文章管理"]
            },
            "execution_result": api_result,
            "request_data": {}
        }
        
        save_response = requests.post(
            f"{BASE_URL}/api/save-api-as-testcase",
            json=save_payload,
            timeout=30
        )
        
        save_result = save_response.json()
        print(f"保存结果: {json.dumps(save_result, indent=2, ensure_ascii=False)}")
        
        assert save_result.get('success'), "保存应该成功"
        test_case_id = save_result.get('test_case_id')
        print(f"✅ 测试用例ID: {test_case_id}")
        
        # 步骤3: 执行测试用例
        print(f"\n步骤3: 执行测试用例 {test_case_id}...")
        time.sleep(1)  # 等待数据保存
        
        execute_response = requests.post(
            f"{BASE_URL}/api/testcases/{test_case_id}/execute",
            timeout=30
        )
        
        execute_result = execute_response.json()
        print(f"执行结果: {json.dumps(execute_result, indent=2, ensure_ascii=False)}")
        
        # 验证ExecutionEngine特有字段
        assert "trace_id" in execute_result, "应该包含trace_id"
        assert execute_result.get('success'), "执行应该成功"
        
        print(f"\n✅ trace_id: {execute_result.get('trace_id')}")
        print(f"✅ 执行状态: {execute_result.get('result', {}).get('status')}")
        print(f"✅ 响应时间: {execute_result.get('result', {}).get('response_time')}ms")
        
        print("✅ 保存并执行测试用例通过")
        return True
        
    except Exception as e:
        print(f"❌ 保存并执行测试用例失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_script_generation_and_execution():
    """测试脚本生成和执行"""
    print("\n" + "=" * 60)
    print("测试4: 脚本生成和执行")
    print("=" * 60)
    
    try:
        # 步骤1: 获取测试用例列表
        print("\n步骤1: 获取测试用例...")
        response = requests.get(f"{BASE_URL}/api/test-cases", timeout=10)
        test_cases = response.json().get('data', [])
        
        if not test_cases:
            print("⚠️  没有测试用例，跳过此测试")
            return True
        
        test_case_id = test_cases[0].get('id')
        print(f"使用测试用例: {test_case_id}")
        
        # 步骤2: 生成脚本
        print("\n步骤2: 生成脚本...")
        gen_response = requests.post(
            f"{BASE_URL}/api/automation/scripts/generate",
            json={"test_case_id": test_case_id},
            timeout=30
        )
        
        gen_result = gen_response.json()
        
        if not gen_result.get('success'):
            print(f"⚠️  脚本生成失败: {gen_result.get('error')}")
            return True
        
        script_id = gen_result.get('script_id')
        print(f"✅ 脚本ID: {script_id}")
        
        # 步骤3: 执行脚本
        print(f"\n步骤3: 执行脚本 {script_id}...")
        time.sleep(1)
        
        exec_response = requests.post(
            f"{BASE_URL}/api/automation/scripts/{script_id}/execute",
            timeout=60
        )
        
        exec_result = exec_response.json()
        print(f"执行结果: {json.dumps(exec_result, indent=2, ensure_ascii=False)}")
        
        # 验证ExecutionEngine特有字段
        assert "trace_id" in exec_result, "应该包含trace_id"
        
        print(f"\n✅ trace_id: {exec_result.get('trace_id')}")
        print(f"✅ 执行状态: {exec_result.get('status')}")
        print(f"✅ 执行时间: {exec_result.get('execution_time')}ms")
        
        print("✅ 脚本生成和执行测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 脚本生成和执行测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🚀 Backend ExecutionEngine集成验证")
    print("=" * 60)
    print("\n⚠️  请确保后端服务器已启动:")
    print("   cd ai-test-platform && py backend_api_server.py")
    print()
    
    # 等待用户确认
    input("按Enter键开始测试...")
    
    tests = [
        ("健康检查", test_health),
        ("API执行端点", test_execute_api),
        ("保存并执行测试用例", test_save_and_execute_testcase),
        ("脚本生成和执行", test_script_generation_and_execution),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ 测试 '{name}' 异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 打印总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} - {name}")
    
    print("\n" + "=" * 60)
    print(f"通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 所有测试通过！Backend ExecutionEngine集成验证成功！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败")
        return 1

if __name__ == "__main__":
    exit(main())
