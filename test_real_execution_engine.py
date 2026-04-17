#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试真实执行引擎
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from modules.executor.real_execution_engine import (
    ExecutionEngine,
    execute_api_test,
    execute_script_test,
    execute_command_test
)


def print_result(title: str, result):
    """打印执行结果"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print('='*60)
    print(f"Trace ID: {result.trace_id}")
    print(f"Status: {result.status}")
    print(f"Success: {result.success}")
    print(f"Duration: {result.duration:.3f}s")
    
    if result.status_code is not None:
        print(f"Status Code: {result.status_code}")
    
    if result.response:
        print(f"Response: {str(result.response)[:200]}...")
    
    if result.error_message:
        print(f"Error: {result.error_message}")
    
    print()


def test_api_execution():
    """测试API执行"""
    print("\n" + "="*60)
    print("测试1: API执行 - 成功案例")
    print("="*60)
    
    # 测试成功的API调用
    result = execute_api_test(
        url='https://jsonplaceholder.typicode.com/posts/1',
        method='GET'
    )
    
    print_result("✅ GET请求成功", result)
    assert result.success == True
    assert result.status_code == 200
    assert result.response is not None
    
    # 测试POST请求
    result = execute_api_test(
        url='https://jsonplaceholder.typicode.com/posts',
        method='POST',
        body={'title': 'Test', 'body': 'Test body', 'userId': 1}
    )
    
    print_result("✅ POST请求成功", result)
    assert result.success == True
    assert result.status_code == 201


def test_api_errors():
    """测试API错误处理"""
    print("\n" + "="*60)
    print("测试2: API执行 - 错误处理")
    print("="*60)
    
    # 测试404错误
    result = execute_api_test(
        url='https://jsonplaceholder.typicode.com/posts/99999',
        method='GET'
    )
    
    print_result("⚠️  404错误", result)
    assert result.success == False
    assert result.status_code == 404
    
    # 测试连接错误
    result = execute_api_test(
        url='http://invalid-domain-that-does-not-exist-12345.com',
        method='GET',
        timeout=5
    )
    
    print_result("❌ 连接错误", result)
    assert result.success == False
    assert result.error_type == 'connection_error'
    
    # 测试超时
    result = execute_api_test(
        url='https://httpbin.org/delay/10',
        method='GET',
        timeout=2
    )
    
    print_result("⏱️  超时错误", result)
    assert result.success == False
    assert result.error_type == 'timeout'


def test_script_execution():
    """测试脚本执行"""
    print("\n" + "="*60)
    print("测试3: 脚本执行")
    print("="*60)
    
    # 测试成功的脚本
    script = """
print("Hello from script!")
print("Script executed successfully")
"""
    
    result = execute_script_test(script)
    print_result("✅ 脚本执行成功", result)
    assert result.success == True
    assert result.status_code == 0
    assert 'Hello from script!' in result.response['stdout']
    
    # 测试失败的脚本
    script = """
print("This will fail")
raise Exception("Test error")
"""
    
    result = execute_script_test(script)
    print_result("❌ 脚本执行失败", result)
    assert result.success == False
    assert result.status_code != 0


def test_command_execution():
    """测试命令执行"""
    print("\n" + "="*60)
    print("测试4: 命令执行")
    print("="*60)
    
    # 测试成功的命令
    result = execute_command_test('echo "Hello from command!"')
    print_result("✅ 命令执行成功", result)
    assert result.success == True
    assert result.status_code == 0
    
    # 测试失败的命令
    result = execute_command_test('exit 1')
    print_result("❌ 命令执行失败", result)
    assert result.success == False
    assert result.status_code == 1


def test_engine_with_testcase():
    """测试使用TestCase对象"""
    print("\n" + "="*60)
    print("测试5: 使用TestCase对象")
    print("="*60)
    
    engine = ExecutionEngine()
    
    # API测试用例
    test_case = {
        'id': 'TC_001',
        'name': '获取用户信息',
        'execution_type': 'api',
        'config': {
            'url': 'https://jsonplaceholder.typicode.com/users/1',
            'method': 'GET',
            'headers': {'Accept': 'application/json'}
        },
        'timeout': 10
    }
    
    result = engine.execute(test_case)
    print_result("✅ TestCase执行成功", result)
    assert result.success == True
    assert result.metadata['method'] == 'GET'


def test_observability():
    """测试可观测性数据"""
    print("\n" + "="*60)
    print("测试6: 可观测性数据")
    print("="*60)
    
    result = execute_api_test(
        url='https://jsonplaceholder.typicode.com/posts/1',
        method='GET'
    )
    
    print("观测数据:")
    print(f"  Trace ID: {result.trace_id}")
    print(f"  Start Time: {result.start_time}")
    print(f"  End Time: {result.end_time}")
    print(f"  Duration: {result.duration:.3f}s")
    print(f"  Metadata: {result.metadata}")
    
    # 验证所有观测数据都存在
    assert result.trace_id is not None
    assert result.start_time is not None
    assert result.end_time is not None
    assert result.duration > 0
    assert result.metadata is not None


def main():
    """运行所有测试"""
    print("="*60)
    print("真实执行引擎 - 完整测试")
    print("="*60)
    
    try:
        test_api_execution()
        test_api_errors()
        test_script_execution()
        test_command_execution()
        test_engine_with_testcase()
        test_observability()
        
        print("\n" + "="*60)
        print("🎉 所有测试通过！")
        print("="*60)
        print("\n测试总结:")
        print("  ✅ API执行 - 成功")
        print("  ✅ API错误处理 - 成功")
        print("  ✅ 脚本执行 - 成功")
        print("  ✅ 命令执行 - 成功")
        print("  ✅ TestCase对象 - 成功")
        print("  ✅ 可观测性 - 成功")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ 测试错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
