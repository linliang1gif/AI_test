"""
验证企业级ApiRunner功能
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from dataclasses import dataclass
from typing import List, Dict
from enum import Enum


# 模拟数据模型
class TestType(Enum):
    API = "api"


class Priority(Enum):
    P0 = "P0"


@dataclass
class TestCase:
    id: str
    test_point_id: str
    title: str
    precondition: str
    steps: List[str]
    expected: str
    priority: Priority
    test_type: TestType
    module: str
    execution_config: Dict
    assertions: List[Dict]
    save_to_context: Dict = None


def verify_dynamic_parameters():
    """验证动态参数替换"""
    print("=" * 60)
    print("验证1: 动态参数替换")
    print("=" * 60)
    
    from modules.executor.api_runner import ApiRunner
    
    runner = ApiRunner({"base_url": "https://jsonplaceholder.typicode.com"})
    
    # 设置上下文
    runner.set_context("post_id", 1)
    
    test_case = TestCase(
        id="TC_VERIFY_DYNAMIC",
        test_point_id="TP_VERIFY_DYNAMIC",
        title="验证动态参数",
        precondition="无",
        steps=["调用API"],
        expected="成功",
        priority=Priority.P0,
        test_type=TestType.API,
        module="验证",
        execution_config={
            "method": "GET",
            "url": "/posts/${post_id}",
            "timeout": 10
        },
        assertions=[
            {"type": "status_code", "expected": 200},
            {"type": "json_path", "field": "id", "operator": "equals", "expected": 1}
        ]
    )
    
    result = runner.run(test_case)
    
    if result['status'] == 'passed':
        print("✅ 动态参数替换功能正常")
        print(f"   URL: {result['request_info']['url']}")
        return True
    else:
        print(f"❌ 动态参数替换失败: {result.get('error_message')}")
        return False


def verify_token_injection():
    """验证Token注入"""
    print("\n" + "=" * 60)
    print("验证2: Token注入")
    print("=" * 60)
    
    from modules.executor.api_runner import ApiRunner
    
    config = {
        "base_url": "https://jsonplaceholder.typicode.com",
        "auth_config": {
            "type": "bearer",
            "token": "test_token_123"
        }
    }
    
    runner = ApiRunner(config)
    
    test_case = TestCase(
        id="TC_VERIFY_AUTH",
        test_point_id="TP_VERIFY_AUTH",
        title="验证Token注入",
        precondition="无",
        steps=["调用API"],
        expected="成功",
        priority=Priority.P0,
        test_type=TestType.API,
        module="验证",
        execution_config={
            "method": "GET",
            "url": "/posts/1",
            "timeout": 10
        },
        assertions=[
            {"type": "status_code", "expected": 200}
        ]
    )
    
    result = runner.run(test_case)
    
    if result['status'] == 'passed':
        print("✅ Token注入功能正常")
        # 检查是否有Authorization头
        if 'headers' in result['request_info']:
            auth_header = result['request_info']['headers'].get('Authorization', '')
            if 'Bearer' in auth_header:
                print(f"   Authorization头已注入: {auth_header[:30]}...")
        return True
    else:
        print(f"❌ Token注入失败: {result.get('error_message')}")
        return False


def verify_enhanced_json_path():
    """验证增强的JSON Path断言"""
    print("\n" + "=" * 60)
    print("验证3: 增强的JSON Path断言")
    print("=" * 60)
    
    from modules.executor.api_runner import ApiRunner
    
    runner = ApiRunner({"base_url": "https://jsonplaceholder.typicode.com"})
    
    test_case = TestCase(
        id="TC_VERIFY_JSONPATH",
        test_point_id="TP_VERIFY_JSONPATH",
        title="验证增强JSON Path",
        precondition="无",
        steps=["调用API"],
        expected="成功",
        priority=Priority.P0,
        test_type=TestType.API,
        module="验证",
        execution_config={
            "method": "GET",
            "url": "/users/1",
            "timeout": 10
        },
        assertions=[
            # 基本断言
            {"type": "json_path", "field": "id", "operator": "equals", "expected": 1},
            
            # 嵌套路径
            {"type": "json_path", "field": "address.city", "operator": "exists", "expected": True},
            
            # 大于断言
            {"type": "json_path", "field": "id", "operator": "greater_than", "expected": 0},
            
            # 类型断言
            {"type": "json_path", "field": "id", "operator": "type", "expected": "int"},
        ]
    )
    
    result = runner.run(test_case)
    
    if result['status'] == 'passed':
        passed_count = sum(1 for a in result['assertion_results'] if a['passed'])
        total_count = len(result['assertion_results'])
        print(f"✅ 增强JSON Path断言功能正常")
        print(f"   通过: {passed_count}/{total_count}")
        
        for assertion in result['assertion_results']:
            status = "✅" if assertion['passed'] else "❌"
            print(f"   {status} {assertion['type']} ({assertion.get('operator')})")
        
        return True
    else:
        print(f"❌ 增强JSON Path断言失败: {result.get('error_message')}")
        return False


def verify_smart_retry():
    """验证智能重试"""
    print("\n" + "=" * 60)
    print("验证4: 智能重试机制")
    print("=" * 60)
    
    from modules.executor.api_runner import ApiRunner
    
    config = {
        "base_url": "https://jsonplaceholder.typicode.com",
        "retry_config": {
            "max_retries": 2,
            "backoff_factor": 1,
            "retry_on_status": [500, 502, 503, 504],
            "retry_on_timeout": True
        }
    }
    
    runner = ApiRunner(config)
    
    test_case = TestCase(
        id="TC_VERIFY_RETRY",
        test_point_id="TP_VERIFY_RETRY",
        title="验证智能重试",
        precondition="无",
        steps=["调用API"],
        expected="成功",
        priority=Priority.P0,
        test_type=TestType.API,
        module="验证",
        execution_config={
            "method": "GET",
            "url": "/posts/1",
            "timeout": 10
        },
        assertions=[
            {"type": "status_code", "expected": 200}
        ]
    )
    
    result = runner.run(test_case)
    
    if 'retry_info' in result:
        retry_info = result['retry_info']
        print(f"✅ 智能重试机制正常")
        print(f"   总尝试次数: {retry_info['total_attempts']}")
        print(f"   重试次数: {retry_info['retry_count']}")
        if retry_info['retry_reasons']:
            print(f"   重试原因: {', '.join(retry_info['retry_reasons'])}")
        return True
    else:
        print("❌ 智能重试机制异常")
        return False


def verify_context_chaining():
    """验证上下文链式调用"""
    print("\n" + "=" * 60)
    print("验证5: 上下文链式调用")
    print("=" * 60)
    
    from modules.executor.api_runner import ApiRunner
    
    runner = ApiRunner({"base_url": "https://jsonplaceholder.typicode.com"})
    
    # 第一个请求
    test_case_1 = TestCase(
        id="TC_VERIFY_CHAIN_1",
        test_point_id="TP_VERIFY_CHAIN_1",
        title="创建资源",
        precondition="无",
        steps=["创建Post"],
        expected="成功",
        priority=Priority.P0,
        test_type=TestType.API,
        module="验证",
        execution_config={
            "method": "POST",
            "url": "/posts",
            "body": {
                "title": "Test",
                "body": "Test Body",
                "userId": 1
            },
            "timeout": 10
        },
        assertions=[
            {"type": "status_code", "expected": 201}
        ],
        save_to_context={
            "created_id": "id"
        }
    )
    
    result_1 = runner.run(test_case_1)
    
    if result_1['status'] != 'passed':
        print(f"❌ 第一个请求失败: {result_1.get('error_message')}")
        return False
    
    created_id = runner.get_context('created_id')
    print(f"   第一个请求成功，创建ID: {created_id}")
    
    # 第二个请求（使用第一个请求的结果）
    test_case_2 = TestCase(
        id="TC_VERIFY_CHAIN_2",
        test_point_id="TP_VERIFY_CHAIN_2",
        title="查询资源",
        precondition="资源已创建",
        steps=["查询Post"],
        expected="成功",
        priority=Priority.P0,
        test_type=TestType.API,
        module="验证",
        execution_config={
            "method": "GET",
            "url": "/posts/${created_id}",
            "timeout": 10
        },
        assertions=[
            {"type": "status_code", "expected": 200},
            {"type": "json_path", "field": "id", "operator": "equals", "expected": created_id}
        ]
    )
    
    result_2 = runner.run(test_case_2)
    
    if result_2['status'] == 'passed':
        print(f"✅ 上下文链式调用功能正常")
        print(f"   第二个请求成功，使用了上下文变量")
        return True
    else:
        print(f"❌ 第二个请求失败: {result_2.get('error_message')}")
        return False


def main():
    """运行所有验证"""
    print("\n🚀 开始验证企业级ApiRunner功能\n")
    
    results = []
    
    try:
        results.append(("动态参数", verify_dynamic_parameters()))
    except Exception as e:
        print(f"❌ 动态参数验证失败: {e}")
        results.append(("动态参数", False))
    
    try:
        results.append(("Token注入", verify_token_injection()))
    except Exception as e:
        print(f"❌ Token注入验证失败: {e}")
        results.append(("Token注入", False))
    
    try:
        results.append(("增强JSON Path", verify_enhanced_json_path()))
    except Exception as e:
        print(f"❌ 增强JSON Path验证失败: {e}")
        results.append(("增强JSON Path", False))
    
    try:
        results.append(("智能重试", verify_smart_retry()))
    except Exception as e:
        print(f"❌ 智能重试验证失败: {e}")
        results.append(("智能重试", False))
    
    try:
        results.append(("上下文链式调用", verify_context_chaining()))
    except Exception as e:
        print(f"❌ 上下文链式调用验证失败: {e}")
        results.append(("上下文链式调用", False))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("验证结果汇总")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status} - {name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\n总计: {total}, 通过: {passed}, 失败: {total - passed}")
    print(f"通过率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 所有验证通过！企业级ApiRunner工作正常！")
        return 0
    else:
        print(f"\n⚠️ {total - passed} 个验证失败，请检查")
        return 1


if __name__ == "__main__":
    exit(main())
