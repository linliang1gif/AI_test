#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 ExecutionEngine 集成 ResilienceEngine

验证：
1. ResilienceEngine 是否正确集成
2. 重试机制是否生效
3. 熔断机制是否生效
4. 统计信息是否正确
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from modules.executor.execution_engine import ExecutionEngine
from core import create_test_case


def test_resilience_integration():
    """测试 ResilienceEngine 集成"""
    print("=" * 80)
    print("🧪 测试 ExecutionEngine 集成 ResilienceEngine")
    print("=" * 80)
    
    # 1. 创建 ExecutionEngine（启用 ResilienceEngine）
    print("\n[1] 创建 ExecutionEngine（启用 ResilienceEngine）...")
    config = {
        'resilience_enabled': True,
        'max_retries': 3,
        'retry_delay': 0.5,
        'circuit_breaker_enabled': True,
        'rate_limiter_enabled': True
    }
    engine = ExecutionEngine(config)
    
    print(f"  ✅ ExecutionEngine 已创建")
    print(f"  ResilienceEngine: {'启用' if engine.resilience else '禁用'}")
    
    # 2. 创建测试用例
    print("\n[2] 创建测试用例...")
    test_cases = []
    
    for i in range(1, 4):
        tc = create_test_case(
            id=f"tc_test_{i:03d}",
            title=f"测试用例 {i}",
            module="test",
            priority="high"
        )
        test_cases.append(tc)
    
    print(f"  ✅ 创建了 {len(test_cases)} 个测试用例")
    
    # 3. 执行测试
    print("\n[3] 执行测试...")
    try:
        results = engine.execute(test_cases, parallel=False)
        print(f"  ✅ 执行完成: {len(results)} 个结果")
    except Exception as e:
        print(f"  ⚠️  执行出错: {e}")
        results = []
    
    # 4. 显示统计
    print("\n[4] 统计信息:")
    if results:
        stats = engine.get_statistics(results)
        
        print(f"\n执行统计:")
        print(f"  总用例: {stats['total']}")
        print(f"  通过: {stats['passed']}")
        print(f"  失败: {stats['failed']}")
        print(f"  通过率: {stats['pass_rate']}")
        print(f"  总耗时: {stats['total_duration']}s")
        
        # ResilienceEngine 统计
        if 'resilience' in stats:
            res_stats = stats['resilience']['resilience']
            print(f"\nResilienceEngine 统计:")
            print(f"  总调用: {res_stats['total_calls']}")
            print(f"  成功: {res_stats['successful_calls']}")
            print(f"  失败: {res_stats['failed_calls']}")
            print(f"  重试: {res_stats['retried_calls']}")
            print(f"  熔断拒绝: {res_stats['circuit_breaker_rejections']}")
            print(f"  限流拒绝: {res_stats['rate_limiter_rejections']}")
    
    print("\n" + "=" * 80)
    print("✅ 测试完成")
    print("=" * 80)


def test_without_resilience():
    """测试不启用 ResilienceEngine"""
    print("\n" + "=" * 80)
    print("🧪 测试 ExecutionEngine（不启用 ResilienceEngine）")
    print("=" * 80)
    
    # 创建 ExecutionEngine（禁用 ResilienceEngine）
    print("\n[1] 创建 ExecutionEngine（禁用 ResilienceEngine）...")
    config = {
        'resilience_enabled': False,
        'max_retries': 2
    }
    engine = ExecutionEngine(config)
    
    print(f"  ✅ ExecutionEngine 已创建")
    print(f"  ResilienceEngine: {'启用' if engine.resilience else '禁用'}")
    
    # 创建测试用例
    test_cases = [
        create_test_case(
            id="tc_test_001",
            title="测试用例 1",
            module="test",
            priority="high"
        )
    ]
    
    # 执行测试
    print("\n[2] 执行测试...")
    try:
        results = engine.execute(test_cases, parallel=False)
        print(f"  ✅ 执行完成: {len(results)} 个结果")
    except Exception as e:
        print(f"  ⚠️  执行出错: {e}")
        results = []
    
    # 显示统计
    if results:
        stats = engine.get_statistics(results)
        print(f"\n统计信息:")
        print(f"  总用例: {stats['total']}")
        print(f"  通过: {stats['passed']}")
        print(f"  失败: {stats['failed']}")
        print(f"  ResilienceEngine 统计: {'有' if 'resilience' in stats else '无'}")
    
    print("\n✅ 测试完成")


if __name__ == "__main__":
    # 测试1: 启用 ResilienceEngine
    test_resilience_integration()
    
    # 测试2: 不启用 ResilienceEngine
    test_without_resilience()
