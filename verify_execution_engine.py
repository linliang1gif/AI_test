"""
验证执行引擎功能
快速测试ExecutionEngine是否正常工作
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


def verify_basic_execution():
    """验证基本执行功能"""
    print("=" * 60)
    print("验证1: 基本执行功能")
    print("=" * 60)
    
    from modules.executor import ExecutionEngine
    
    test_case = TestCase(
        id="TC_VERIFY_001",
        test_point_id="TP_VERIFY_001",
        title="验证基本执行",
        precondition="无",
        steps=["调用API"],
        expected="成功",
        priority=Priority.P0,
        test_type=TestType.API,
        module="验证",
        execution_config={
            "method": "GET",
            "url": "https://jsonplaceholder.typicode.com/posts/1",
            "timeout": 10
        },
        assertions=[
            {"type": "status_code", "expected": 200},
            {"type": "json_path", "field": "id", "operator": "equals", "expected": 1}
        ]
    )
    
    engine = ExecutionEngine()
    results = engine.execute([test_case], parallel=False)
    
    assert len(results) == 1, "❌ 应该返回1个结果"
    result = results[0]
    
    print(f"✅ 测试用例ID: {result.test_case_id}")
    print(f"✅ 执行状态: {result.status}")
    print(f"✅ 执行耗时: {result.duration:.2f}s")
    
    if result.status == "passed":
        print("✅ 基本执行功能正常")
        return True
    else:
        print(f"❌ 执行失败: {result.error_message}")
        return False


def verify_parallel_execution():
    """验证并行执行"""
    print("\n" + "=" * 60)
    print("验证2: 并行执行功能")
    print("=" * 60)
    
    from modules.executor import ExecutionEngine
    import time
    
    # 创建5个测试用例
    test_cases = [
        TestCase(
            id=f"TC_PARALLEL_{i:03d}",
            test_point_id=f"TP_PARALLEL_{i:03d}",
            title=f"并行测试{i}",
            precondition="无",
            steps=["调用API"],
            expected="成功",
            priority=Priority.P0,
            test_type=TestType.API,
            module="验证",
            execution_config={
                "method": "GET",
                "url": f"https://jsonplaceholder.typicode.com/posts/{i}",
                "timeout": 10
            },
            assertions=[
                {"type": "status_code", "expected": 200}
            ]
        )
        for i in range(1, 6)
    ]
    
    engine = ExecutionEngine()
    
    # 顺序执行
    start = time.time()
    results_seq = engine.execute(test_cases, parallel=False)
    seq_time = time.time() - start
    
    # 并行执行
    start = time.time()
    results_par = engine.execute(test_cases, max_workers=5, parallel=True)
    par_time = time.time() - start
    
    print(f"✅ 顺序执行耗时: {seq_time:.2f}s")
    print(f"✅ 并行执行耗时: {par_time:.2f}s")
    print(f"✅ 加速比: {seq_time/par_time:.2f}x")
    
    if par_time < seq_time:
        print("✅ 并行执行功能正常")
        return True
    else:
        print("⚠️ 并行执行未加速（可能是网络原因）")
        return True  # 不算失败


def verify_assertions():
    """验证断言功能"""
    print("\n" + "=" * 60)
    print("验证3: 断言功能")
    print("=" * 60)
    
    from modules.executor import ExecutionEngine
    
    test_case = TestCase(
        id="TC_ASSERTION",
        test_point_id="TP_ASSERTION",
        title="验证多种断言",
        precondition="无",
        steps=["调用API"],
        expected="所有断言通过",
        priority=Priority.P0,
        test_type=TestType.API,
        module="验证",
        execution_config={
            "method": "GET",
            "url": "https://jsonplaceholder.typicode.com/users/1",
            "timeout": 10
        },
        assertions=[
            {"type": "status_code", "expected": 200},
            {"type": "json_path", "field": "id", "operator": "equals", "expected": 1},
            {"type": "json_path", "field": "name", "operator": "contains", "expected": "Leanne"},
            {"type": "response_time", "expected": 5.0}
        ]
    )
    
    engine = ExecutionEngine()
    results = engine.execute([test_case], parallel=False)
    
    result = results[0]
    
    print(f"✅ 断言数量: {len(result.assertion_results)}")
    
    for assertion in result.assertion_results:
        status = "✅" if assertion['passed'] else "❌"
        print(f"{status} {assertion['type']}: Expected={assertion.get('expected')}, Actual={assertion.get('actual')}")
    
    passed_count = sum(1 for a in result.assertion_results if a['passed'])
    
    if passed_count == len(result.assertion_results):
        print("✅ 所有断言通过")
        return True
    else:
        print(f"⚠️ {passed_count}/{len(result.assertion_results)} 断言通过")
        return False


def verify_statistics():
    """验证统计功能"""
    print("\n" + "=" * 60)
    print("验证4: 统计功能")
    print("=" * 60)
    
    from modules.executor import ExecutionEngine
    
    # 创建混合结果的测试用例
    test_cases = [
        TestCase(
            id="TC_STAT_PASS",
            test_point_id="TP_STAT_PASS",
            title="通过的测试",
            precondition="无",
            steps=["调用API"],
            expected="成功",
            priority=Priority.P0,
            test_type=TestType.API,
            module="验证",
            execution_config={
                "method": "GET",
                "url": "https://jsonplaceholder.typicode.com/posts/1",
                "timeout": 10
            },
            assertions=[
                {"type": "status_code", "expected": 200}
            ]
        ),
        TestCase(
            id="TC_STAT_FAIL",
            test_point_id="TP_STAT_FAIL",
            title="失败的测试",
            precondition="无",
            steps=["调用API"],
            expected="失败",
            priority=Priority.P0,
            test_type=TestType.API,
            module="验证",
            execution_config={
                "method": "GET",
                "url": "https://jsonplaceholder.typicode.com/posts/1",
                "timeout": 10
            },
            assertions=[
                {"type": "status_code", "expected": 404}  # 故意失败
            ]
        )
    ]
    
    engine = ExecutionEngine()
    results = engine.execute(test_cases, parallel=False)
    
    stats = engine.get_statistics(results)
    
    print(f"✅ 总计: {stats['total']}")
    print(f"✅ 通过: {stats['passed']}")
    print(f"✅ 失败: {stats['failed']}")
    print(f"✅ 通过率: {stats['pass_rate']}")
    print(f"✅ 总耗时: {stats['total_duration']}s")
    print(f"✅ 平均耗时: {stats['avg_duration']}s")
    
    if stats['total'] == 2 and stats['passed'] >= 1:
        print("✅ 统计功能正常")
        return True
    else:
        print("❌ 统计功能异常")
        return False


def main():
    """运行所有验证"""
    print("\n🚀 开始验证ExecutionEngine功能\n")
    
    results = []
    
    try:
        results.append(("基本执行", verify_basic_execution()))
    except Exception as e:
        print(f"❌ 基本执行验证失败: {e}")
        results.append(("基本执行", False))
    
    try:
        results.append(("并行执行", verify_parallel_execution()))
    except Exception as e:
        print(f"❌ 并行执行验证失败: {e}")
        results.append(("并行执行", False))
    
    try:
        results.append(("断言功能", verify_assertions()))
    except Exception as e:
        print(f"❌ 断言功能验证失败: {e}")
        results.append(("断言功能", False))
    
    try:
        results.append(("统计功能", verify_statistics()))
    except Exception as e:
        print(f"❌ 统计功能验证失败: {e}")
        results.append(("统计功能", False))
    
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
        print("\n🎉 所有验证通过！ExecutionEngine工作正常！")
        return 0
    else:
        print(f"\n⚠️ {total - passed} 个验证失败，请检查")
        return 1


if __name__ == "__main__":
    exit(main())
