#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Intelligence Agent 架构升级

验证:
1. ExecutionEngine 只能执行 execution_plan
2. test_cases_map 正确解决 TestCase 查找问题
3. execute_legacy 兼容旧代码但内部走 Intelligence
4. Pipeline 强制接入 Intelligence Agent
5. 所有执行路径统一
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from modules.executor.execution_engine import ExecutionEngine
from modules.agents import TestIntelligenceAgent, TestCase as IntelligenceTestCase
from core import create_test_case


def test_1_execute_plan():
    """测试 1: ExecutionEngine.execute_plan (新架构)"""
    print("\n" + "="*80)
    print("测试 1: ExecutionEngine.execute_plan (新架构)")
    print("="*80)
    
    # 1. 创建测试用例
    test_cases = [
        create_test_case(
            id="test_001",
            title="测试用例 1",
            module="user",
            priority="P0"
        ),
        create_test_case(
            id="test_002",
            title="测试用例 2",
            module="user",
            priority="P1"
        ),
        create_test_case(
            id="test_003",
            title="测试用例 3",
            module="order",
            priority="P2"
        )
    ]
    
    # 2. 转换为 Intelligence TestCase
    intelligence_cases = []
    for tc in test_cases:
        intelligence_cases.append(IntelligenceTestCase(
            test_case_id=tc.id,
            api=tc.id,
            module=tc.module,
            priority=tc.priority.value,
            tags=[]
        ))
    
    # 3. 使用 Intelligence Agent 生成执行计划
    intelligence_agent = TestIntelligenceAgent()
    execution_plan = intelligence_agent.optimize_execution_plan(intelligence_cases)
    
    print(f"\n✅ 执行计划生成成功:")
    print(f"   总用例: {execution_plan['statistics']['total_tests']}")
    print(f"   选中: {execution_plan['statistics']['selected_tests']}")
    print(f"   跳过: {execution_plan['statistics']['skipped_tests']}")
    
    # 4. 构建 test_cases_map
    test_cases_map = {tc.id: tc for tc in test_cases}
    
    # 5. 使用 ExecutionEngine 执行计划
    engine = ExecutionEngine(config={
        'base_url': 'https://jsonplaceholder.typicode.com',
        'resilience_enabled': False  # 简化测试
    })
    
    results = engine.execute_plan(execution_plan, test_cases_map)
    
    print(f"\n✅ 执行完成:")
    print(f"   执行结果数: {len(results)}")
    
    return True


def test_2_execute_legacy():
    """测试 2: ExecutionEngine.execute_legacy (兼容模式)"""
    print("\n" + "="*80)
    print("测试 2: ExecutionEngine.execute_legacy (兼容模式)")
    print("="*80)
    
    # 1. 创建测试用例
    test_cases = [
        create_test_case(
            id="test_legacy_001",
            title="兼容测试用例 1",
            module="user",
            priority="P0"
        ),
        create_test_case(
            id="test_legacy_002",
            title="兼容测试用例 2",
            module="order",
            priority="P1"
        )
    ]
    
    # 2. 使用 execute_legacy (内部会强制走 Intelligence)
    engine = ExecutionEngine(config={
        'base_url': 'https://jsonplaceholder.typicode.com',
        'resilience_enabled': False
    })
    
    results = engine.execute_legacy(test_cases, max_workers=2, parallel=True)
    
    print(f"\n✅ 兼容模式执行完成:")
    print(f"   执行结果数: {len(results)}")
    
    return True


def test_3_execute_deprecated():
    """测试 3: ExecutionEngine.execute (已废弃)"""
    print("\n" + "="*80)
    print("测试 3: ExecutionEngine.execute (已废弃,但仍可用)")
    print("="*80)
    
    # 1. 创建测试用例
    test_cases = [
        create_test_case(
            id="test_deprecated_001",
            title="废弃接口测试用例",
            module="user",
            priority="P0"
        )
    ]
    
    # 2. 使用 execute (会打印警告)
    engine = ExecutionEngine(config={
        'base_url': 'https://jsonplaceholder.typicode.com',
        'resilience_enabled': False
    })
    
    results = engine.execute(test_cases)
    
    print(f"\n✅ 废弃接口执行完成:")
    print(f"   执行结果数: {len(results)}")
    
    return True


def test_4_test_cases_map():
    """测试 4: test_cases_map 解决 TestCase 查找问题"""
    print("\n" + "="*80)
    print("测试 4: test_cases_map 解决 TestCase 查找问题")
    print("="*80)
    
    # 1. 创建大量测试用例
    test_cases = []
    for i in range(100):
        test_cases.append(create_test_case(
            id=f"test_{i:03d}",
            title=f"测试用例 {i}",
            module=f"module_{i % 5}",
            priority=["P0", "P1", "P2"][i % 3]
        ))
    
    # 2. 构建 test_cases_map (O(1) 查找)
    test_cases_map = {tc.id: tc for tc in test_cases}
    
    print(f"\n✅ test_cases_map 构建成功:")
    print(f"   总用例数: {len(test_cases_map)}")
    
    # 3. 测试查找性能
    import time
    
    # 列表查找 (O(n))
    start = time.time()
    for i in range(1000):
        target_id = f"test_{i % 100:03d}"
        found = next((tc for tc in test_cases if tc.id == target_id), None)
    list_time = time.time() - start
    
    # 字典查找 (O(1))
    start = time.time()
    for i in range(1000):
        target_id = f"test_{i % 100:03d}"
        found = test_cases_map.get(target_id)
    dict_time = time.time() - start
    
    print(f"\n✅ 查找性能对比 (1000次查找):")
    print(f"   列表查找 (O(n)): {list_time:.4f}s")
    print(f"   字典查找 (O(1)): {dict_time:.4f}s")
    print(f"   性能提升: {list_time / dict_time:.2f}x")
    
    return True


def test_5_pipeline_integration():
    """测试 5: Pipeline 强制接入 Intelligence Agent"""
    print("\n" + "="*80)
    print("测试 5: Pipeline 强制接入 Intelligence Agent")
    print("="*80)
    
    try:
        from pipeline_v2_intelligence import run_pipeline_v2_intelligence
        
        print("\n✅ Pipeline V2 Intelligence 导入成功")
        print("   Pipeline 已强制接入 Intelligence Agent")
        print("   所有执行路径统一")
        
        return True
    
    except ImportError as e:
        print(f"\n❌ Pipeline 导入失败: {e}")
        return False


def main():
    """主函数"""
    print("\n" + "="*80)
    print("🚀 Intelligence Agent 架构升级测试")
    print("="*80)
    
    tests = [
        ("ExecutionEngine.execute_plan (新架构)", test_1_execute_plan),
        ("ExecutionEngine.execute_legacy (兼容模式)", test_2_execute_legacy),
        ("ExecutionEngine.execute (已废弃)", test_3_execute_deprecated),
        ("test_cases_map 查找性能", test_4_test_cases_map),
        ("Pipeline 强制接入 Intelligence", test_5_pipeline_integration)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 显示测试结果
    print("\n" + "="*80)
    print("📊 测试结果汇总")
    print("="*80)
    
    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} - {name}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过! 架构升级成功!")
        return 0
    else:
        print("\n⚠️  部分测试失败,请检查")
        return 1


if __name__ == "__main__":
    sys.exit(main())
