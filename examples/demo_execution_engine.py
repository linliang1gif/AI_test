"""
执行引擎使用示例
演示如何使用ExecutionEngine直接执行测试用例（无pytest）
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dataclasses import dataclass
from typing import List, Dict
from enum import Enum


# 模拟数据模型（实际使用时从core/models.py导入）
class TestType(Enum):
    API = "api"
    UI = "ui"
    INTEGRATION = "integration"


class Priority(Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"


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


def demo_api_test():
    """演示API测试执行"""
    print("=" * 60)
    print("演示1: API测试执行")
    print("=" * 60)
    
    # 创建测试用例
    test_cases = [
        TestCase(
            id="TC_001",
            test_point_id="TP_001",
            title="验证用户登录接口",
            precondition="用户已注册",
            steps=["调用POST /api/login接口", "传入用户名和密码"],
            expected="返回200状态码和token",
            priority=Priority.P0,
            test_type=TestType.API,
            module="用户管理",
            execution_config={
                "method": "POST",
                "url": "https://jsonplaceholder.typicode.com/posts",
                "body": {
                    "title": "test",
                    "body": "test body",
                    "userId": 1
                },
                "timeout": 10
            },
            assertions=[
                {
                    "type": "status_code",
                    "expected": 201
                },
                {
                    "type": "json_path",
                    "field": "id",
                    "operator": "greater_than",
                    "expected": 0
                },
                {
                    "type": "response_time",
                    "expected": 5.0
                }
            ]
        ),
        TestCase(
            id="TC_002",
            test_point_id="TP_002",
            title="验证获取用户信息接口",
            precondition="用户已登录",
            steps=["调用GET /api/users/1接口"],
            expected="返回用户详细信息",
            priority=Priority.P1,
            test_type=TestType.API,
            module="用户管理",
            execution_config={
                "method": "GET",
                "url": "https://jsonplaceholder.typicode.com/users/1",
                "timeout": 10
            },
            assertions=[
                {
                    "type": "status_code",
                    "expected": 200
                },
                {
                    "type": "json_path",
                    "field": "id",
                    "operator": "equals",
                    "expected": 1
                },
                {
                    "type": "json_path",
                    "field": "name",
                    "operator": "contains",
                    "expected": "Leanne"
                }
            ]
        )
    ]
    
    # 初始化执行引擎
    from modules.executor import ExecutionEngine
    
    config = {
        "base_url": "https://jsonplaceholder.typicode.com",
        "timeout": 30,
        "retry_on_failure": False,
        "max_retries": 0
    }
    
    engine = ExecutionEngine(config)
    
    # 执行测试（并行）
    print("\n🚀 开始执行测试（并行模式）...")
    results = engine.execute(test_cases, max_workers=2, parallel=True)
    
    # 打印结果
    print("\n📊 执行结果:")
    for result in results:
        print(f"\n测试用例: {result.test_case_id}")
        print(f"  状态: {result.status}")
        print(f"  耗时: {result.duration:.2f}s")
        
        if result.assertion_results:
            print(f"  断言结果:")
            for assertion in result.assertion_results:
                status = "✅" if assertion['passed'] else "❌"
                print(f"    {status} {assertion['type']}: Expected={assertion.get('expected')}, Actual={assertion.get('actual')}")
        
        if result.error_message:
            print(f"  错误: {result.error_message}")
    
    # 统计信息
    stats = engine.get_statistics(results)
    print("\n📈 统计信息:")
    print(f"  总计: {stats['total']}")
    print(f"  通过: {stats['passed']}")
    print(f"  失败: {stats['failed']}")
    print(f"  错误: {stats['error']}")
    print(f"  通过率: {stats['pass_rate']}")
    print(f"  总耗时: {stats['total_duration']}s")
    print(f"  平均耗时: {stats['avg_duration']}s")


def demo_sequential_execution():
    """演示顺序执行"""
    print("\n" + "=" * 60)
    print("演示2: 顺序执行模式")
    print("=" * 60)
    
    # 创建简单测试用例
    test_cases = [
        TestCase(
            id=f"TC_{i:03d}",
            test_point_id=f"TP_{i:03d}",
            title=f"测试用例 {i}",
            precondition="无",
            steps=["执行测试"],
            expected="成功",
            priority=Priority.P2,
            test_type=TestType.API,
            module="测试模块",
            execution_config={
                "method": "GET",
                "url": f"https://jsonplaceholder.typicode.com/posts/{i}",
                "timeout": 10
            },
            assertions=[
                {
                    "type": "status_code",
                    "expected": 200
                }
            ]
        )
        for i in range(1, 4)
    ]
    
    from modules.executor import ExecutionEngine
    
    engine = ExecutionEngine()
    
    # 顺序执行
    print("\n🚀 开始执行测试（顺序模式）...")
    results = engine.execute(test_cases, parallel=False)
    
    # 打印结果
    print("\n📊 执行结果:")
    for result in results:
        status_icon = "✅" if result.status == "passed" else "❌"
        print(f"{status_icon} {result.test_case_id}: {result.status} ({result.duration:.2f}s)")
    
    stats = engine.get_statistics(results)
    print(f"\n通过率: {stats['pass_rate']}, 总耗时: {stats['total_duration']}s")


def demo_retry_mechanism():
    """演示重试机制"""
    print("\n" + "=" * 60)
    print("演示3: 失败重试机制")
    print("=" * 60)
    
    # 创建一个会失败的测试用例
    test_case = TestCase(
        id="TC_RETRY",
        test_point_id="TP_RETRY",
        title="测试重试机制",
        precondition="无",
        steps=["调用不存在的接口"],
        expected="失败后重试",
        priority=Priority.P1,
        test_type=TestType.API,
        module="测试模块",
        execution_config={
            "method": "GET",
            "url": "https://jsonplaceholder.typicode.com/invalid-endpoint",
            "timeout": 5
        },
        assertions=[
            {
                "type": "status_code",
                "expected": 200
            }
        ]
    )
    
    from modules.executor import ExecutionEngine
    
    # 配置重试
    config = {
        "retry_on_failure": True,
        "max_retries": 2,
        "retry_delay": 1
    }
    
    engine = ExecutionEngine(config)
    
    print("\n🚀 开始执行测试（启用重试）...")
    results = engine.execute([test_case], parallel=False)
    
    result = results[0]
    print(f"\n📊 执行结果:")
    print(f"  状态: {result.status}")
    print(f"  重试次数: {result.retry_count}")
    print(f"  耗时: {result.duration:.2f}s")
    if result.error_message:
        print(f"  错误: {result.error_message}")


def demo_custom_runner():
    """演示自定义Runner"""
    print("\n" + "=" * 60)
    print("演示4: 自定义Runner")
    print("=" * 60)
    
    # 创建自定义Runner
    class CustomRunner:
        def __init__(self, config):
            self.config = config
        
        def run(self, test_case):
            print(f"  执行自定义测试: {test_case.title}")
            return {
                "status": "passed",
                "message": "Custom runner executed successfully"
            }
    
    from modules.executor import ExecutionEngine
    
    engine = ExecutionEngine()
    
    # 注册自定义Runner
    engine.register_runner("custom", CustomRunner({}))
    
    # 创建使用自定义Runner的测试用例
    class CustomTestType(Enum):
        CUSTOM = "custom"
    
    test_case = TestCase(
        id="TC_CUSTOM",
        test_point_id="TP_CUSTOM",
        title="自定义测试用例",
        precondition="无",
        steps=["执行自定义逻辑"],
        expected="成功",
        priority=Priority.P2,
        test_type=CustomTestType.CUSTOM,
        module="自定义模块",
        execution_config={},
        assertions=[]
    )
    
    print("\n🚀 开始执行自定义测试...")
    results = engine.execute([test_case], parallel=False)
    
    result = results[0]
    print(f"\n📊 执行结果:")
    print(f"  状态: {result.status}")
    print(f"  耗时: {result.duration:.2f}s")


if __name__ == "__main__":
    # 运行所有演示
    demo_api_test()
    demo_sequential_execution()
    demo_retry_mechanism()
    demo_custom_runner()
    
    print("\n" + "=" * 60)
    print("✅ 所有演示完成！")
    print("=" * 60)
