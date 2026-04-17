"""
企业级ApiRunner使用示例
演示动态参数、Token注入、智能重试等高级特性
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

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


def demo_dynamic_parameters():
    """演示1: 动态参数替换"""
    print("=" * 60)
    print("演示1: 动态参数替换")
    print("=" * 60)
    
    from modules.executor.api_runner import ApiRunner
    
    # 配置Runner
    config = {
        "base_url": "https://jsonplaceholder.typicode.com",
        "timeout": 10,
        "auth_config": {
            "type": "bearer",
            "token": "test_token_123"
        }
    }
    
    runner = ApiRunner(config)
    
    # 设置上下文变量
    runner.set_context("user_id", 1)
    runner.set_context("post_id", 1)
    
    # 创建测试用例（使用动态参数）
    test_case = TestCase(
        id="TC_DYNAMIC_001",
        test_point_id="TP_DYNAMIC_001",
        title="测试动态参数",
        precondition="无",
        steps=["调用API"],
        expected="成功",
        priority=Priority.P0,
        test_type=TestType.API,
        module="动态参数",
        execution_config={
            "method": "GET",
            "url": "/users/${user_id}/posts/${post_id}",  # 动态参数
            "timeout": 10
        },
        assertions=[
            {"type": "status_code", "expected": 404},  # 这个API不存在，会404
        ]
    )
    
    print("\n🚀 执行测试（使用动态参数）...")
    print(f"  URL模板: /users/${{user_id}}/posts/${{post_id}}")
    print(f"  user_id: {runner.get_context('user_id')}")
    print(f"  post_id: {runner.get_context('post_id')}")
    
    result = runner.run(test_case)
    
    print(f"\n📊 执行结果:")
    print(f"  状态: {result['status']}")
    print(f"  实际URL: {result['request_info']['url']}")
    print(f"  状态码: {result['request_info']['status_code']}")


def demo_token_injection():
    """演示2: Token注入"""
    print("\n" + "=" * 60)
    print("演示2: Token注入")
    print("=" * 60)
    
    from modules.executor.api_runner import ApiRunner
    
    # 配置Bearer Token认证
    config = {
        "base_url": "https://jsonplaceholder.typicode.com",
        "auth_config": {
            "type": "bearer",
            "token": "my_secret_token_123"
        }
    }
    
    runner = ApiRunner(config)
    
    test_case = TestCase(
        id="TC_AUTH_001",
        test_point_id="TP_AUTH_001",
        title="测试Token注入",
        precondition="无",
        steps=["调用API"],
        expected="成功",
        priority=Priority.P0,
        test_type=TestType.API,
        module="认证",
        execution_config={
            "method": "GET",
            "url": "/posts/1",
            "timeout": 10
        },
        assertions=[
            {"type": "status_code", "expected": 200}
        ]
    )
    
    print("\n🚀 执行测试（自动注入Token）...")
    print(f"  认证类型: Bearer Token")
    print(f"  Token: {config['auth_config']['token']}")
    
    result = runner.run(test_case)
    
    print(f"\n📊 执行结果:")
    print(f"  状态: {result['status']}")
    print(f"  请求头包含: Authorization: Bearer ...")
    
    # 查看实际请求头
    if 'headers' in result['request_info']:
        auth_header = result['request_info']['headers'].get('Authorization', 'Not found')
        print(f"  实际Authorization: {auth_header[:30]}...")


def demo_smart_retry():
    """演示3: 智能重试机制"""
    print("\n" + "=" * 60)
    print("演示3: 智能重试机制")
    print("=" * 60)
    
    from modules.executor.api_runner import ApiRunner
    
    # 配置重试策略
    config = {
        "base_url": "https://jsonplaceholder.typicode.com",
        "retry_config": {
            "max_retries": 3,
            "backoff_factor": 2,
            "retry_on_status": [500, 502, 503, 504],
            "retry_on_timeout": True
        }
    }
    
    runner = ApiRunner(config)
    
    test_case = TestCase(
        id="TC_RETRY_001",
        test_point_id="TP_RETRY_001",
        title="测试智能重试",
        precondition="无",
        steps=["调用API"],
        expected="成功",
        priority=Priority.P0,
        test_type=TestType.API,
        module="重试",
        execution_config={
            "method": "GET",
            "url": "/posts/1",
            "timeout": 10
        },
        assertions=[
            {"type": "status_code", "expected": 200}
        ]
    )
    
    print("\n🚀 执行测试（启用智能重试）...")
    print(f"  最大重试次数: {config['retry_config']['max_retries']}")
    print(f"  退避因子: {config['retry_config']['backoff_factor']}")
    print(f"  重试状态码: {config['retry_config']['retry_on_status']}")
    
    result = runner.run(test_case)
    
    print(f"\n📊 执行结果:")
    print(f"  状态: {result['status']}")
    
    if 'retry_info' in result:
        retry_info = result['retry_info']
        print(f"  总尝试次数: {retry_info['total_attempts']}")
        print(f"  重试次数: {retry_info['retry_count']}")
        if retry_info['retry_reasons']:
            print(f"  重试原因: {', '.join(retry_info['retry_reasons'])}")


def demo_enhanced_json_path():
    """演示4: 增强的JSON Path断言"""
    print("\n" + "=" * 60)
    print("演示4: 增强的JSON Path断言")
    print("=" * 60)
    
    from modules.executor.api_runner import ApiRunner
    
    runner = ApiRunner({"base_url": "https://jsonplaceholder.typicode.com"})
    
    test_case = TestCase(
        id="TC_JSONPATH_001",
        test_point_id="TP_JSONPATH_001",
        title="测试增强JSON Path",
        precondition="无",
        steps=["调用API"],
        expected="成功",
        priority=Priority.P0,
        test_type=TestType.API,
        module="JSON Path",
        execution_config={
            "method": "GET",
            "url": "/users/1",
            "timeout": 10
        },
        assertions=[
            # 基本断言
            {"type": "json_path", "field": "id", "operator": "equals", "expected": 1},
            
            # 嵌套路径
            {"type": "json_path", "field": "address.city", "operator": "contains", "expected": "Gwenborough"},
            
            # 存在性断言
            {"type": "json_path", "field": "email", "operator": "exists", "expected": True},
            
            # 类型断言
            {"type": "json_path", "field": "id", "operator": "type", "expected": "int"},
            
            # 大于断言
            {"type": "json_path", "field": "id", "operator": "greater_than", "expected": 0},
        ]
    )
    
    print("\n🚀 执行测试（增强JSON Path断言）...")
    print("  断言类型:")
    print("    1. 基本相等断言")
    print("    2. 嵌套路径断言")
    print("    3. 存在性断言")
    print("    4. 类型断言")
    print("    5. 比较断言")
    
    result = runner.run(test_case)
    
    print(f"\n📊 执行结果:")
    print(f"  状态: {result['status']}")
    print(f"  断言结果:")
    
    for assertion in result['assertion_results']:
        status = "✅" if assertion['passed'] else "❌"
        print(f"    {status} {assertion['type']} ({assertion.get('operator', 'equals')}): {assertion.get('expected')} vs {assertion.get('actual')}")


def demo_context_chaining():
    """演示5: 上下文链式调用"""
    print("\n" + "=" * 60)
    print("演示5: 上下文链式调用")
    print("=" * 60)
    
    from modules.executor.api_runner import ApiRunner
    
    runner = ApiRunner({"base_url": "https://jsonplaceholder.typicode.com"})
    
    # 第一个请求：创建资源
    test_case_1 = TestCase(
        id="TC_CHAIN_001",
        test_point_id="TP_CHAIN_001",
        title="创建资源",
        precondition="无",
        steps=["创建Post"],
        expected="成功",
        priority=Priority.P0,
        test_type=TestType.API,
        module="链式调用",
        execution_config={
            "method": "POST",
            "url": "/posts",
            "body": {
                "title": "Test Post",
                "body": "Test Body",
                "userId": 1
            },
            "timeout": 10
        },
        assertions=[
            {"type": "status_code", "expected": 201},
            {"type": "json_path", "field": "id", "operator": "exists", "expected": True}
        ],
        save_to_context={
            "created_post_id": "id",  # 保存id到上下文
            "created_post_title": "title"
        }
    )
    
    print("\n🚀 步骤1: 创建资源...")
    result_1 = runner.run(test_case_1)
    
    print(f"  状态: {result_1['status']}")
    print(f"  创建的Post ID: {runner.get_context('created_post_id')}")
    print(f"  创建的Post标题: {runner.get_context('created_post_title')}")
    
    # 第二个请求：使用第一个请求的结果
    test_case_2 = TestCase(
        id="TC_CHAIN_002",
        test_point_id="TP_CHAIN_002",
        title="查询创建的资源",
        precondition="资源已创建",
        steps=["查询Post"],
        expected="成功",
        priority=Priority.P0,
        test_type=TestType.API,
        module="链式调用",
        execution_config={
            "method": "GET",
            "url": "/posts/${created_post_id}",  # 使用上下文变量
            "timeout": 10
        },
        assertions=[
            {"type": "status_code", "expected": 200},
            {"type": "json_path", "field": "id", "operator": "equals", "expected": runner.get_context('created_post_id')}
        ]
    )
    
    print("\n🚀 步骤2: 查询创建的资源...")
    print(f"  使用上下文变量: created_post_id = {runner.get_context('created_post_id')}")
    
    result_2 = runner.run(test_case_2)
    
    print(f"  状态: {result_2['status']}")
    print(f"  查询URL: {result_2['request_info']['url']}")


def demo_interceptors():
    """演示6: 请求/响应拦截器"""
    print("\n" + "=" * 60)
    print("演示6: 请求/响应拦截器")
    print("=" * 60)
    
    from modules.executor.api_runner import ApiRunner
    
    runner = ApiRunner({"base_url": "https://jsonplaceholder.typicode.com"})
    
    # 添加请求拦截器（记录请求）
    def request_logger(config):
        print(f"  📤 发送请求: {config['method']} {config['url']}")
        return config
    
    # 添加响应拦截器（记录响应）
    def response_logger(response):
        print(f"  📥 收到响应: {response.status_code} ({response.elapsed.total_seconds():.2f}s)")
        return response
    
    runner.add_request_interceptor(request_logger)
    runner.add_response_interceptor(response_logger)
    
    test_case = TestCase(
        id="TC_INTERCEPTOR_001",
        test_point_id="TP_INTERCEPTOR_001",
        title="测试拦截器",
        precondition="无",
        steps=["调用API"],
        expected="成功",
        priority=Priority.P0,
        test_type=TestType.API,
        module="拦截器",
        execution_config={
            "method": "GET",
            "url": "/posts/1",
            "timeout": 10
        },
        assertions=[
            {"type": "status_code", "expected": 200}
        ]
    )
    
    print("\n🚀 执行测试（启用拦截器）...")
    result = runner.run(test_case)
    
    print(f"\n📊 执行结果:")
    print(f"  状态: {result['status']}")


if __name__ == "__main__":
    # 运行所有演示
    demo_dynamic_parameters()
    demo_token_injection()
    demo_smart_retry()
    demo_enhanced_json_path()
    demo_context_chaining()
    demo_interceptors()
    
    print("\n" + "=" * 60)
    print("✅ 所有演示完成！")
    print("=" * 60)
