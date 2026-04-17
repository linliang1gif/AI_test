#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OptimizationAgent 演示 - 展示优化前后对比
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from modules.agents import TestOptimizationAgent, LearningAgent
from core import create_test_case


def main():
    print("=" * 80)
    print("🎯 TestOptimizationAgent 演示")
    print("=" * 80)
    
    # 创建测试用例（模拟 Design Agent 的输出）
    print("\n[1] 模拟 Design Agent 输出...")
    testcases = []
    
    # Payment API - 5个测试（包含冗余）
    for i in range(1, 6):
        testcases.append(create_test_case(
            id=f"tc_payment_{i:03d}",
            title=f"POST /payment - 测试{i}",
            module="payment",
            priority="high" if i <= 2 else "medium" if i <= 4 else "low"
        ))
    
    # Order API - 4个测试
    for i in range(1, 5):
        testcases.append(create_test_case(
            id=f"tc_order_{i:03d}",
            title=f"GET /order - 测试{i}",
            module="order",
            priority="high" if i == 1 else "medium"
        ))
    
    # User API - 3个测试
    for i in range(1, 4):
        testcases.append(create_test_case(
            id=f"tc_user_{i:03d}",
            title=f"POST /user/login - 测试{i}",
            module="user",
            priority="critical" if i == 1 else "high"
        ))
    
    print(f"  ✅ 生成了 {len(testcases)} 个测试用例")
    
    # 创建 LearningAgent（模拟历史数据）
    print("\n[2] 创建 LearningAgent...")
    learning_agent = LearningAgent(knowledge_dir="knowledge_demo")
    learning_agent.api_stats = {
        "POST /payment": {"risk_score": 0.7, "failure_rate": 0.4},
        "GET /order": {"risk_score": 0.3, "failure_rate": 0.1},
        "POST /user/login": {"risk_score": 0.5, "failure_rate": 0.2}
    }
    print(f"  ✅ 设置了 3 个 API 的风险数据")
    
    # 创建 OptimizationAgent
    print("\n[3] 创建 OptimizationAgent...")
    optimization_agent = TestOptimizationAgent()
    print(f"  ✅ OptimizationAgent 已创建")
    
    # 执行优化
    print("\n[4] 执行优化...")
    result = optimization_agent.optimize(testcases, learning_agent)
    
    # 显示结果
    print("\n" + "=" * 80)
    print("📊 优化结果")
    print("=" * 80)
    
    stats = result['statistics']
    print(f"\n原始用例: {stats['original_count']} 个")
    print(f"优化后: {stats['optimized_count']} 个")
    print(f"移除: {stats['dropped_count']} 个")
    print(f"减少比例: {stats['reduction_rate']:.1%}")
    
    plan = result['execution_plan']
    print(f"\n预计耗时: {plan['estimated_time']}")
    print(f"节省时间: {plan['estimated_time_saved']}")
    
    print(f"\n执行顺序（前5个）:")
    for item in result['execution_plan']['execution_order'][:5]:
        print(f"  {item['sequence']}. [{item['priority']:8s}] {item['test_case_id']}")
    
    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80)
    
    print("\n💡 关键点:")
    print("  1. 去重: 移除了低优先级的冗余测试")
    print("  2. 排序: 高风险 API + 高优先级优先执行")
    print("  3. 效率: 减少了测试数量，节省了执行时间")


if __name__ == "__main__":
    main()
