#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 TestOptimizationAgent

演示优化前后的对比
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from modules.agents.optimization_agent import TestOptimizationAgent
from modules.agents.learning_agent import LearningAgent
from core import create_test_case


def create_sample_testcases():
    """创建示例测试用例（包含冗余）"""
    testcases = []
    
    # 1. Payment API - 5个测试（有冗余）
    testcases.append(create_test_case(
        id="tc_payment_create_001",
        title="POST /payment/create - 正常场景",
        module="payment",
        priority="high"
    ))
    
    testcases.append(create_test_case(
        id="tc_payment_create_002",
        title="POST /payment/create - 正常场景2",  # 冗余
        module="payment",
        priority="medium"
    ))
    
    testcases.append(create_test_case(
        id="tc_payment_create_003",
        title="POST /payment/create - 边界值测试",
        module="payment",
        priority="medium"
    ))
    
    testcases.append(create_test_case(
        id="tc_payment_create_004",
        title="POST /payment/create - 异常场景",
        module="payment",
        priority="high"
    ))
    
    testcases.append(create_test_case(
        id="tc_payment_create_005",
        title="POST /payment/create - 正常场景3",  # 冗余
        module="payment",
        priority="low"
    ))
    
    # 2. Order API - 4个测试
    testcases.append(create_test_case(
        id="tc_order_query_001",
        title="GET /order/query - 正常场景",
        module="order",
        priority="medium"
    ))
    
    testcases.append(create_test_case(
        id="tc_order_query_002",
        title="GET /order/query - 边界值测试",
        module="order",
        priority="medium"
    ))
    
    testcases.append(create_test_case(
        id="tc_order_query_003",
        title="GET /order/query - 异常场景",
        module="order",
        priority="high"
    ))
    
    testcases.append(create_test_case(
        id="tc_order_query_004",
        title="GET /order/query - 正常场景2",  # 冗余
        module="order",
        priority="low"
    ))
    
    # 3. User API - 3个测试
    testcases.append(create_test_case(
        id="tc_user_login_001",
        title="POST /user/login - 正常场景",
        module="user",
        priority="critical"
    ))
    
    testcases.append(create_test_case(
        id="tc_user_login_002",
        title="POST /user/login - 异常场景",
        module="user",
        priority="high"
    ))
    
    testcases.append(create_test_case(
        id="tc_user_login_003",
        title="POST /user/login - 边界值测试",
        module="user",
        priority="medium"
    ))
    
    return testcases


def setup_learning_agent():
    """设置 LearningAgent（模拟历史数据）"""
    learning_agent = LearningAgent(knowledge_dir="knowledge_test")
    
    # 模拟一些高风险 API
    learning_agent.api_stats = {
        "POST /payment/create": {
            "total_executions": 50,
            "total_failures": 15,
            "failure_rate": 0.3,
            "risk_score": 0.6
        },
        "POST /user/login": {
            "total_executions": 100,
            "total_failures": 5,
            "failure_rate": 0.05,
            "risk_score": 0.2
        },
        "GET /order/query": {
            "total_executions": 30,
            "total_failures": 3,
            "failure_rate": 0.1,
            "risk_score": 0.3
        }
    }
    
    return learning_agent


def print_testcases(testcases, title="测试用例"):
    """打印测试用例列表"""
    print(f"\n{title} ({len(testcases)} 个):")
    print("-" * 80)
    
    for i, tc in enumerate(testcases, 1):
        priority = tc.priority.value if hasattr(tc.priority, 'value') else str(tc.priority)
        print(f"{i:2d}. [{priority:8s}] {tc.id:30s} | {tc.title}")


def test_optimization_agent():
    """测试 OptimizationAgent"""
    print("=" * 80)
    print("🧪 测试 TestOptimizationAgent")
    print("=" * 80)
    
    # 1. 创建示例测试用例
    print("\n[1] 创建示例测试用例...")
    testcases = create_sample_testcases()
    print(f"  ✅ 创建了 {len(testcases)} 个测试用例")
    
    # 显示原始用例
    print_testcases(testcases, "原始测试用例")
    
    # 2. 设置 LearningAgent
    print("\n[2] 设置 LearningAgent...")
    learning_agent = setup_learning_agent()
    high_risk_apis = learning_agent.get_high_risk_apis()
    print(f"  ✅ 识别了 {len(high_risk_apis)} 个高风险 API:")
    for api_info in high_risk_apis:
        print(f"     - {api_info['api']}: 风险分数 {api_info['risk_score']:.2f}")
    
    # 3. 创建 OptimizationAgent
    print("\n[3] 创建 OptimizationAgent...")
    optimization_agent = TestOptimizationAgent(config={
        'dedup_threshold': 0.9,
        'keep_boundary': True,
        'keep_negative': True,
        'keep_high_priority': True
    })
    print(f"  ✅ OptimizationAgent 已创建")
    
    # 4. 执行优化
    print("\n[4] 执行优化...")
    result = optimization_agent.optimize(testcases, learning_agent)
    
    # 5. 显示优化结果
    print("\n" + "=" * 80)
    print("📊 优化结果")
    print("=" * 80)
    
    # 统计信息
    stats = result['statistics']
    print(f"\n统计信息:")
    print(f"  原始用例数: {stats['original_count']}")
    print(f"  优化后用例数: {stats['optimized_count']}")
    print(f"  移除用例数: {stats['dropped_count']}")
    print(f"  减少比例: {stats['reduction_rate']:.1%}")
    print(f"  优化耗时: {stats['optimization_duration']:.3f}s")
    
    # 显示优化后的用例
    print_testcases(result['optimized_cases'], "优化后的测试用例（按优先级排序）")
    
    # 显示被移除的用例
    if result['dropped_cases']:
        print_testcases(result['dropped_cases'], "被移除的测试用例（冗余）")
    
    # 执行计划
    print("\n执行计划:")
    plan = result['execution_plan']
    print(f"  总用例: {plan['total_cases']}")
    print(f"  优化后: {plan['optimized_cases']}")
    print(f"  移除: {plan['dropped_cases']}")
    print(f"  减少比例: {plan['reduction_rate']}")
    print(f"  预计耗时: {plan['estimated_time']}")
    print(f"  节省时间: {plan['estimated_time_saved']}")
    
    print(f"\n  执行顺序（前10个）:")
    for item in plan['execution_order']:
        print(f"    {item['sequence']:2d}. [{item['priority']:8s}] {item['test_case_id']:30s} | {item['api']}")
    
    # 覆盖率报告
    print("\n覆盖率报告:")
    coverage = result['coverage_report']
    print(f"  总 API 数: {coverage['total_apis']}")
    print(f"  平均每个 API 的测试数: {coverage['avg_tests_per_api']:.1f}")
    
    if coverage['duplicate_coverage']:
        print(f"\n  ⚠️  重复覆盖 ({len(coverage['duplicate_coverage'])} 个):")
        for dup in coverage['duplicate_coverage']:
            print(f"     - {dup['api']}: {dup['test_count']} 个测试 - {dup['suggestion']}")
    
    # 6. 对比分析
    print("\n" + "=" * 80)
    print("📈 优化前后对比")
    print("=" * 80)
    
    print("\n优化前:")
    print(f"  - Payment API: 5 个测试（包含 3 个冗余的正常场景）")
    print(f"  - Order API: 4 个测试（包含 1 个冗余的正常场景）")
    print(f"  - User API: 3 个测试（无冗余）")
    print(f"  - 总计: {len(testcases)} 个测试")
    print(f"  - 预计耗时: {len(testcases) * 2}s")
    
    print("\n优化后:")
    print(f"  - Payment API: 保留边界、异常、高优先级测试")
    print(f"  - Order API: 保留边界、异常测试")
    print(f"  - User API: 全部保留（critical 优先级）")
    print(f"  - 总计: {len(result['optimized_cases'])} 个测试")
    print(f"  - 预计耗时: {len(result['optimized_cases']) * 2}s")
    print(f"  - 节省时间: {len(result['dropped_cases']) * 2}s ({stats['reduction_rate']:.1%})")
    
    print("\n优化策略:")
    print(f"  ✅ 去重: 移除了 {len(result['dropped_cases'])} 个冗余测试")
    print(f"  ✅ 排序: 按 P0 + 高风险优先")
    print(f"  ✅ 保留: 边界测试、异常测试、高优先级测试")
    
    print("\n" + "=" * 80)
    print("✅ 测试完成")
    print("=" * 80)
    
    return result


def test_optimization_statistics():
    """测试优化统计"""
    print("\n" + "=" * 80)
    print("📊 测试优化统计")
    print("=" * 80)
    
    optimization_agent = TestOptimizationAgent()
    
    # 执行多次优化
    for i in range(3):
        testcases = create_sample_testcases()
        learning_agent = setup_learning_agent()
        result = optimization_agent.optimize(testcases, learning_agent)
        print(f"\n第 {i+1} 次优化: {result['statistics']['original_count']} → "
              f"{result['statistics']['optimized_count']} 用例")
    
    # 获取统计信息
    stats = optimization_agent.get_optimization_statistics()
    
    print("\n总体统计:")
    print(f"  总优化次数: {stats['total_optimizations']}")
    print(f"  总原始用例: {stats['total_original_cases']}")
    print(f"  总优化用例: {stats['total_optimized_cases']}")
    print(f"  总移除用例: {stats['total_dropped_cases']}")
    print(f"  平均减少比例: {stats['avg_reduction_rate']:.1%}")
    
    print("\n✅ 统计测试完成")


if __name__ == "__main__":
    # 测试1: 基本优化功能
    result = test_optimization_agent()
    
    # 测试2: 优化统计
    test_optimization_statistics()
