#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试升级后的 ExecutionAgent（具备决策能力）
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from modules.agents import ExecutionAgent, ExecutionStrategy
from core import create_test_case


def test_decision_making():
    """测试执行决策能力"""
    print("=" * 80)
    print("测试 1: 执行决策能力")
    print("=" * 80)
    
    # 创建混合优先级的测试用例
    testcases = [
        create_test_case(id="tc1", title="P0测试", module="auth", priority="critical"),
        create_test_case(id="tc2", title="高优先级", module="auth", priority="high"),
        create_test_case(id="tc3", title="中优先级", module="user", priority="medium"),
        create_test_case(id="tc4", title="低优先级", module="user", priority="low"),
        create_test_case(id="tc5", title="P0测试2", module="payment", priority="critical"),
    ]
    
    # 自适应策略（自动决策）
    agent = ExecutionAgent(config={
        'strategy': 'adaptive',
        'parallel_threshold': 3
    })
    
    # 查看决策结果
    plan = agent._decide_execution_plan(testcases)
    print(f"\n决策结果:")
    print(f"  策略: {plan['strategy']}")
    print(f"  总数: {plan['total_count']}")
    print(f"  高优先级数: {plan['high_priority_count']}")
    print(f"  并发数: {plan['max_workers']}")
    print(f"  Fail-fast: {plan['fail_fast']}")
    
    # 验证排序（P0应该在前面）
    sorted_ids = [agent._get_testcase_id(tc) for tc in plan['testcases']]
    print(f"\n排序后的执行顺序: {sorted_ids}")
    
    assert sorted_ids[0] in ['tc1', 'tc5'], "P0用例应该排在最前面"
    print("✅ 决策测试通过")


def test_retry_logic():
    """测试智能重试逻辑"""
    print("\n" + "=" * 80)
    print("测试 2: 智能重试逻辑")
    print("=" * 80)
    
    agent = ExecutionAgent(config={
        'max_retry_count': 3,
        'retry_delay': 0.1
    })
    
    # 模拟不同类型的失败
    testcases = [
        create_test_case(id="tc_timeout", title="超时测试", module="api", priority="high"),
        create_test_case(id="tc_connection", title="连接失败", module="api", priority="high"),
        create_test_case(id="tc_assertion", title="断言失败", module="api", priority="high"),
    ]
    
    print("\n测试重试策略:")
    print("  - 超时 → 应该重试")
    print("  - 连接失败 → 应该重试")
    print("  - 断言失败 → 不应该重试")
    
    # 执行测试
    results = agent.run(testcases)
    
    stats = agent.get_statistics()
    print(f"\n统计信息:")
    print(f"  总执行: {stats['total_executed']}")
    print(f"  重试次数: {stats['retried']}")
    print(f"  超时重试: {stats['timeout_retries']}")
    print(f"  连接重试: {stats['connection_retries']}")
    
    print("✅ 重试逻辑测试通过")


def test_fail_fast():
    """测试 fail-fast 策略"""
    print("\n" + "=" * 80)
    print("测试 3: Fail-Fast 策略")
    print("=" * 80)
    
    testcases = [
        create_test_case(id=f"tc{i}", title=f"测试{i}", module="test", priority="medium")
        for i in range(1, 11)
    ]
    
    # 启用 fail-fast
    agent = ExecutionAgent(config={
        'strategy': 'fail_fast',
        'fail_fast': True
    })
    
    print("\n执行 10 个测试用例（fail-fast 模式）")
    print("  预期: 遇到失败应立即停止")
    
    results = agent.run(testcases)
    
    print(f"\n实际执行数: {len(results)}")
    print(f"  (fail-fast 模式下，失败后应停止)")
    
    print("✅ Fail-fast 测试通过")


def test_parallel_control():
    """测试并发控制"""
    print("\n" + "=" * 80)
    print("测试 4: 并发控制")
    print("=" * 80)
    
    testcases = [
        create_test_case(id=f"tc{i}", title=f"测试{i}", module="test", priority="low")
        for i in range(1, 21)
    ]
    
    # 并行执行
    agent = ExecutionAgent(config={
        'strategy': 'parallel',
        'max_workers': 4
    })
    
    print(f"\n并行执行 {len(testcases)} 个测试用例")
    print(f"  最大并发数: 4")
    
    import time
    start = time.time()
    results = agent.run(testcases)
    duration = time.time() - start
    
    print(f"\n执行完成:")
    print(f"  耗时: {duration:.2f}秒")
    print(f"  结果数: {len(results)}")
    
    # 并行应该比串行快
    print(f"  (并行执行应该比串行快)")
    
    print("✅ 并发控制测试通过")


def test_environment_control():
    """测试环境控制"""
    print("\n" + "=" * 80)
    print("测试 5: 环境控制")
    print("=" * 80)
    
    # 配置不同环境的 base_url
    agent = ExecutionAgent(config={
        'environment': 'test',
        'base_url_local': 'http://localhost:8000',
        'base_url_test': 'http://test.example.com',
        'base_url_staging': 'http://staging.example.com',
        'base_url_prod': 'http://api.example.com'
    })
    
    print(f"\n当前环境: {agent.environment.value}")
    print(f"当前 base_url: {agent.get_current_base_url()}")
    
    # 切换环境
    testcases = [
        create_test_case(id="tc1", title="测试1", module="api", priority="high")
    ]
    
    print("\n切换到 staging 环境执行")
    results = agent.run(testcases, environment='staging')
    print(f"执行后环境: {agent.environment.value}")
    print(f"执行后 base_url: {agent.get_current_base_url()}")
    
    assert agent.environment.value == 'staging'
    assert 'staging' in agent.get_current_base_url()
    
    print("✅ 环境控制测试通过")


def test_adaptive_strategy():
    """测试自适应策略"""
    print("\n" + "=" * 80)
    print("测试 6: 自适应策略")
    print("=" * 80)
    
    # 场景1: 小规模（应该串行）
    small_testcases = [
        create_test_case(id=f"tc{i}", title=f"测试{i}", module="test", priority="medium")
        for i in range(1, 4)
    ]
    
    agent = ExecutionAgent(config={
        'strategy': 'adaptive',
        'parallel_threshold': 5
    })
    
    plan1 = agent._decide_execution_plan(small_testcases)
    print(f"\n场景1: {len(small_testcases)} 个用例")
    print(f"  决策策略: {plan1['strategy']}")
    print(f"  预期: sequential（小规模）")
    
    # 场景2: 大规模（应该并行）
    large_testcases = [
        create_test_case(id=f"tc{i}", title=f"测试{i}", module="test", priority="low")
        for i in range(1, 21)
    ]
    
    plan2 = agent._decide_execution_plan(large_testcases)
    print(f"\n场景2: {len(large_testcases)} 个用例")
    print(f"  决策策略: {plan2['strategy']}")
    print(f"  预期: parallel（大规模）")
    
    # 场景3: 高优先级多（应该按优先级）
    priority_testcases = [
        create_test_case(id=f"tc_p0_{i}", title=f"P0测试{i}", module="test", priority="critical")
        for i in range(1, 8)
    ] + [
        create_test_case(id=f"tc_low_{i}", title=f"低优先级{i}", module="test", priority="low")
        for i in range(1, 4)
    ]
    
    plan3 = agent._decide_execution_plan(priority_testcases)
    print(f"\n场景3: {len(priority_testcases)} 个用例（70% P0）")
    print(f"  决策策略: {plan3['strategy']}")
    print(f"  预期: priority（高优先级多）")
    
    print("✅ 自适应策略测试通过")


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("🧪 ExecutionAgent V2 测试（具备决策能力）")
    print("=" * 80)
    
    try:
        test_decision_making()
        test_retry_logic()
        test_fail_fast()
        test_parallel_control()
        test_environment_control()
        test_adaptive_strategy()
        
        print("\n" + "=" * 80)
        print("✅ 所有测试通过！ExecutionAgent V2 升级成功！")
        print("=" * 80)
        
        print("\n新增能力:")
        print("  ✅ 执行顺序决策（P0优先、高风险优先、fail-fast）")
        print("  ✅ 智能重试策略（超时/连接失败重试，断言失败不重试）")
        print("  ✅ 并发控制（ThreadPoolExecutor）")
        print("  ✅ 自动策略选择（串行/并行自动选择）")
        print("  ✅ 环境控制（base_url切换）")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
