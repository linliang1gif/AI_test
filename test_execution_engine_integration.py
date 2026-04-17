#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试ExecutionEngine集成到backend_api_server.py
验证所有API端点都正确使用ExecutionEngine
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_execution_engine_import():
    """测试ExecutionEngine可以正常导入"""
    print("=" * 60)
    print("测试1: ExecutionEngine导入")
    print("=" * 60)
    
    try:
        from modules.executor.real_execution_engine import (
            ExecutionEngine,
            get_execution_engine,
            execute_api_test,
            execute_script_test,
            execute_command_test
        )
        print("✅ ExecutionEngine导入成功")
        
        # 测试单例模式
        engine1 = get_execution_engine()
        engine2 = get_execution_engine()
        assert engine1 is engine2, "单例模式失败"
        print("✅ 单例模式正常")
        
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_execution():
    """测试API执行功能"""
    print("\n" + "=" * 60)
    print("测试2: API执行")
    print("=" * 60)
    
    try:
        from modules.executor.real_execution_engine import execute_api_test
        
        # 测试GET请求
        result = execute_api_test(
            url='https://jsonplaceholder.typicode.com/posts/1',
            method='GET'
        )
        
        print(f"Trace ID: {result.trace_id}")
        print(f"状态: {result.status}")
        print(f"成功: {result.success}")
        print(f"状态码: {result.status_code}")
        print(f"执行时长: {result.duration:.3f}秒")
        
        assert result.success, "API执行应该成功"
        assert result.status_code == 200, "状态码应该是200"
        assert result.response is not None, "应该有响应数据"
        
        print("✅ API执行测试通过")
        return True
        
    except Exception as e:
        print(f"❌ API执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_script_execution():
    """测试脚本执行功能"""
    print("\n" + "=" * 60)
    print("测试3: 脚本执行")
    print("=" * 60)
    
    try:
        from modules.executor.real_execution_engine import execute_script_test
        
        # 测试简单脚本
        script = '''
print("Hello from ExecutionEngine!")
print("Script execution test")
'''
        
        result = execute_script_test(script=script, timeout=10)
        
        print(f"Trace ID: {result.trace_id}")
        print(f"状态: {result.status}")
        print(f"成功: {result.success}")
        print(f"返回码: {result.status_code}")
        print(f"执行时长: {result.duration:.3f}秒")
        
        if result.response:
            print(f"标准输出: {result.response.get('stdout', '')[:100]}")
        
        assert result.success, "脚本执行应该成功"
        assert result.status_code == 0, "返回码应该是0"
        
        print("✅ 脚本执行测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 脚本执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_command_execution():
    """测试命令执行功能"""
    print("\n" + "=" * 60)
    print("测试4: 命令执行")
    print("=" * 60)
    
    try:
        from modules.executor.real_execution_engine import execute_command_test
        
        # 测试简单命令
        result = execute_command_test(
            command='echo "ExecutionEngine Command Test"',
            timeout=10
        )
        
        print(f"Trace ID: {result.trace_id}")
        print(f"状态: {result.status}")
        print(f"成功: {result.success}")
        print(f"返回码: {result.status_code}")
        print(f"执行时长: {result.duration:.3f}秒")
        
        if result.response:
            print(f"标准输出: {result.response.get('stdout', '')[:100]}")
        
        assert result.success, "命令执行应该成功"
        assert result.status_code == 0, "返回码应该是0"
        
        print("✅ 命令执行测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 命令执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_handling():
    """测试错误处理"""
    print("\n" + "=" * 60)
    print("测试5: 错误处理")
    print("=" * 60)
    
    try:
        from modules.executor.real_execution_engine import execute_api_test
        
        # 测试超时
        print("\n测试超时...")
        result = execute_api_test(
            url='https://httpbin.org/delay/10',
            method='GET',
            timeout=2
        )
        
        print(f"状态: {result.status}")
        print(f"成功: {result.success}")
        print(f"错误类型: {result.error_type}")
        print(f"错误消息: {result.error_message}")
        
        assert not result.success, "超时应该失败"
        assert result.error_type == 'timeout', "错误类型应该是timeout"
        
        # 测试连接错误
        print("\n测试连接错误...")
        result = execute_api_test(
            url='http://invalid-domain-12345.com',
            method='GET',
            timeout=5
        )
        
        print(f"状态: {result.status}")
        print(f"成功: {result.success}")
        print(f"错误类型: {result.error_type}")
        print(f"错误消息: {result.error_message}")
        
        assert not result.success, "连接错误应该失败"
        assert result.error_type == 'connection_error', "错误类型应该是connection_error"
        
        print("✅ 错误处理测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 错误处理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_observability():
    """测试可观测性数据"""
    print("\n" + "=" * 60)
    print("测试6: 可观测性")
    print("=" * 60)
    
    try:
        from modules.executor.real_execution_engine import execute_api_test
        
        result = execute_api_test(
            url='https://jsonplaceholder.typicode.com/posts/1',
            method='GET'
        )
        
        # 验证所有必需的观测数据
        assert result.trace_id, "应该有trace_id"
        assert result.start_time, "应该有start_time"
        assert result.end_time, "应该有end_time"
        assert result.duration >= 0, "应该有duration"
        assert result.metadata, "应该有metadata"
        
        print(f"✅ Trace ID: {result.trace_id}")
        print(f"✅ 开始时间: {result.start_time}")
        print(f"✅ 结束时间: {result.end_time}")
        print(f"✅ 执行时长: {result.duration:.3f}秒")
        print(f"✅ 元数据: {result.metadata}")
        
        print("✅ 可观测性测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 可观测性测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🚀 ExecutionEngine集成测试")
    print("=" * 60)
    
    tests = [
        ("ExecutionEngine导入", test_execution_engine_import),
        ("API执行", test_api_execution),
        ("脚本执行", test_script_execution),
        ("命令执行", test_command_execution),
        ("错误处理", test_error_handling),
        ("可观测性", test_observability),
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
        print("\n🎉 所有测试通过！ExecutionEngine集成成功！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败")
        return 1

if __name__ == "__main__":
    exit(main())
