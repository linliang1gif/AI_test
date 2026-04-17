#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DesignAgent 和 ExecutionAgent 演示

展示如何使用新的 Agent 架构
"""

import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.agents import DesignAgent, ExecutionAgent, ExecutionStrategy


def demo_design_agent():
    """演示 DesignAgent"""
    print("=" * 80)
    print("DesignAgent 演示")
    print("=" * 80)
    
    # 1. 创建 DesignAgent
    design_agent = DesignAgent(config={
        'max_testcases_per_api': 3,
        'include_edge_cases': True,
        'include_error_cases': True
    })
    
    print("\n✅ DesignAgent 已创建")
    print(f"   配置: max_testcases_per_api=3, include_edge_cases=True")
    
    # 2. 从需求设计测试用例
    print("\n" + "-" * 80)
    print("场景 1: 从需求文档设计测试用例")
    print("-" * 80)
    
    requirement = """
    用户登录功能需求：
    1. 用户可以使用用户名和密码登录
    2. 登录成功后返回 JWT token
    3. 登录失败返回错误信息
    4. 支持记住密码功能
    5. 支持第三方登录（微信、QQ）
    """
    
    testcases = design_agent.design_from_requirement(requirement)
    
    print(f"\n✅ 生成了 {len(testcases)} 个测试用例:")
    for i, tc in enumerate(testcases, 1):
        title = tc.get('title') if isinstance(tc, dict) else getattr(tc, 'title', 'Unknown')
        priority = tc.get('priority') if isinstance(tc, dict) else getattr(tc, 'priority', 'Unknown')
        print(f"   {i}. {title} (优先级: {priority})")
    
    # 3. 从 Discovery 结果设计测试用例
    print("\n" + "-" * 80)
    print("场景 2: 从 Discovery 结果设计测试用例")
    print("-" * 80)
    
    discovery_results = [
        {
            "path": "/api/users",
            "method": "POST",
            "change_type": "new_endpoint",
            "risk_level": "high",
            "description": "新增用户创建接口"
        },
        {
            "path": "/api/users/{id}",
            "method": "DELETE",
            "change_type": "modified",
            "risk_level": "critical",
            "description": "删除用户接口参数变更"
        }
    ]
    
    testcases = design_agent.design_from_discovery(discovery_results)
    
    print(f"\n✅ 生成了 {len(testcases)} 个测试用例:")
    for i, tc in enumerate(testcases, 1):
        title = tc.get('title') if isinstance(tc, dict) else getattr(tc, 'title', 'Unknown')
        priority = tc.get('priority') if isinstance(tc, dict) else getattr(tc, 'priority', 'Unknown')
        print(f"   {i}. {title} (优先级: {priority})")
    
    # 4. 优化测试用例
    print("\n" + "-" * 80)
    print("场景 3: 优化测试用例集合")
    print("-" * 80)
    
    # 创建一些重复的测试用例
    all_testcases = testcases + testcases[:2]  # 添加重复
    print(f"\n原始测试用例数: {len(all_testcases)}")
    
    optimized = design_agent.optimize_testcases(all_testcases, max_count=10)
    print(f"优化后测试用例数: {len(optimized)}")
    
    # 5. 获取统计信息
    print("\n" + "-" * 80)
    print("设计统计信息")
    print("-" * 80)
    
    stats = design_agent.get_design_statistics()
    print(f"\n总设计次数: {stats['total_designs']}")
    print(f"总测试用例数: {stats['total_testcases']}")
    print(f"平均每次设计用例数: {stats['avg_testcases_per_design']:.1f}")
    print(f"设计来源: {stats['sources']}")
    
    return testcases


def demo_execution_agent(testcases):
    """演示 ExecutionAgent"""
    print("\n\n" + "=" * 80)
    print("ExecutionAgent 演示")
    print("=" * 80)
    
    # 1. 创建 ExecutionAgent - 顺序执行
    print("\n" + "-" * 80)
    print("场景 1: 顺序执行")
    print("-" * 80)
    
    execution_agent = ExecutionAgent(config={
        'environment': 'test',
        'strategy': 'sequential',
        'retry_count': 2
    })
    
    print("\n✅ ExecutionAgent 已创建")
    print(f"   环境: test, 策略: sequential, 重试次数: 2")
    
    print(f"\n开始执行 {len(testcases[:3])} 个测试用例...")
    results = execution_agent.execute(testcases[:3])
    
    print(f"\n✅ 执行完成，结果:")
    for i, result in enumerate(results, 1):
        status = result.get('status') if isinstance(result, dict) else getattr(result, 'status', 'Unknown')
        print(f"   {i}. 状态: {status}")
    
    # 2. 并行执行
    print("\n" + "-" * 80)
    print("场景 2: 并行执行")
    print("-" * 80)
    
    execution_agent = ExecutionAgent(config={
        'environment': 'test',
        'strategy': 'parallel',
        'max_workers': 3
    })
    
    print("\n✅ ExecutionAgent 已创建")
    print(f"   环境: test, 策略: parallel, 并发数: 3")
    
    print(f"\n开始并行执行 {len(testcases[:5])} 个测试用例...")
    results = execution_agent.execute(testcases[:5])
    
    print(f"\n✅ 执行完成")
    
    # 3. 按优先级执行
    print("\n" + "-" * 80)
    print("场景 3: 按优先级执行")
    print("-" * 80)
    
    execution_agent = ExecutionAgent(config={
        'environment': 'test',
        'strategy': 'priority'
    })
    
    print("\n✅ ExecutionAgent 已创建")
    print(f"   环境: test, 策略: priority")
    
    print(f"\n开始按优先级执行 {len(testcases)} 个测试用例...")
    results = execution_agent.execute(testcases)
    
    print(f"\n✅ 执行完成")
    
    # 4. 自适应执行
    print("\n" + "-" * 80)
    print("场景 4: 自适应执行")
    print("-" * 80)
    
    execution_agent = ExecutionAgent(config={
        'environment': 'test',
        'strategy': 'adaptive',
        'max_workers': 2
    })
    
    print("\n✅ ExecutionAgent 已创建")
    print(f"   环境: test, 策略: adaptive")
    print(f"   (高优先级顺序执行，低优先级并行执行)")
    
    print(f"\n开始自适应执行 {len(testcases)} 个测试用例...")
    results = execution_agent.execute(testcases)
    
    print(f"\n✅ 执行完成")
    
    # 5. 获取统计信息
    print("\n" + "-" * 80)
    print("执行统计信息")
    print("-" * 80)
    
    stats = execution_agent.get_statistics()
    print(f"\n总执行数: {stats['total_executed']}")
    print(f"通过: {stats['passed']}")
    print(f"失败: {stats['failed']}")
    print(f"跳过: {stats['skipped']}")
    print(f"重试: {stats['retried']}")
    print(f"通过率: {stats['pass_rate']:.1%}")
    
    return results


def demo_complete_workflow():
    """演示完整工作流"""
    print("\n\n" + "=" * 80)
    print("完整工作流演示")
    print("=" * 80)
    
    print("\n这是一个完整的测试流程:")
    print("  Discovery → Design → Execution → Report")
    
    # 1. 模拟 Discovery 结果
    print("\n" + "-" * 80)
    print("步骤 1: Test Discovery")
    print("-" * 80)
    
    discovery_results = [
        {
            "path": "/api/orders",
            "method": "POST",
            "change_type": "new_endpoint",
            "risk_level": "high"
        },
        {
            "path": "/api/payments",
            "method": "POST",
            "change_type": "modified",
            "risk_level": "critical"
        }
    ]
    
    print(f"✅ 发现了 {len(discovery_results)} 个高风险变更点")
    
    # 2. 设计测试用例
    print("\n" + "-" * 80)
    print("步骤 2: Design Test Cases")
    print("-" * 80)
    
    design_agent = DesignAgent(config={
        'max_testcases_per_api': 5
    })
    
    testcases = design_agent.design_from_discovery(discovery_results)
    print(f"✅ 设计了 {len(testcases)} 个测试用例")
    
    # 3. 执行测试用例
    print("\n" + "-" * 80)
    print("步骤 3: Execute Test Cases")
    print("-" * 80)
    
    execution_agent = ExecutionAgent(config={
        'environment': 'test',
        'strategy': 'priority',
        'retry_count': 3
    })
    
    results = execution_agent.execute(testcases)
    print(f"✅ 执行了 {len(results)} 个测试用例")
    
    # 4. 统计结果
    print("\n" + "-" * 80)
    print("步骤 4: Summary")
    print("-" * 80)
    
    stats = execution_agent.get_statistics()
    print(f"\n📊 执行结果:")
    print(f"   通过: {stats['passed']}")
    print(f"   失败: {stats['failed']}")
    print(f"   通过率: {stats['pass_rate']:.1%}")
    
    print("\n✅ 完整工作流执行成功！")


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("🤖 DesignAgent & ExecutionAgent 演示")
    print("=" * 80)
    
    # 1. 演示 DesignAgent
    testcases = demo_design_agent()
    
    # 2. 演示 ExecutionAgent
    demo_execution_agent(testcases)
    
    # 3. 演示完整工作流
    demo_complete_workflow()
    
    print("\n" + "=" * 80)
    print("✅ 所有演示完成！")
    print("=" * 80)
    
    print("\n💡 关键要点:")
    print("  1. DesignAgent 专注于测试用例设计")
    print("  2. ExecutionAgent 专注于测试用例执行")
    print("  3. 两者职责清晰，互不依赖")
    print("  4. 可以灵活组合使用")
    print("  5. 支持多种执行策略")


if __name__ == "__main__":
    main()
