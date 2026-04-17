#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 LearningAgent（学习型代理）
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from modules.agents.learning_agent import LearningAgent


def create_mock_result(testcase_id: str, status: str, error: str = None):
    """创建模拟执行结果"""
    return {
        'test_case_id': testcase_id,
        'status': status,
        'error': error
    }


def create_mock_healing_record(testcase_id: str, healing_level: str, 
                               strategy: str, success: bool):
    """创建模拟修复记录"""
    return {
        'testcase_id': testcase_id,
        'healing_level': healing_level,
        'strategy': strategy,
        'success': success
    }


def test_failure_pattern_learning():
    """测试失败模式学习"""
    print("=" * 80)
    print("测试 1: 失败模式学习")
    print("=" * 80)
    
    agent = LearningAgent(knowledge_dir="test_knowledge")
    agent.reset_knowledge()
    
    # 模拟执行结果（多次失败）
    results = [
        create_mock_result('tc_payment_create_001', 'FAILED', 'Connection timeout'),
        create_mock_result('tc_payment_create_002', 'FAILED', 'Connection timeout'),
        create_mock_result('tc_payment_create_003', 'FAILED', 'Connection timeout'),
        create_mock_result('tc_order_cancel_001', 'FAILED', 'Assertion failed: expected 200 but got 404'),
        create_mock_result('tc_user_login_001', 'PASSED', None),
    ]
    
    # 学习
    agent.learn(results, [])
    
    # 获取失败模式
    patterns = agent.get_failure_patterns()
    
    print(f"\n学习到的失败模式:")
    for pattern in patterns:
        print(f"  API: {pattern['api']}")
        print(f"    错误类型: {pattern['error_type']}")
        print(f"    频率: {pattern['frequency']}")
        print(f"    严重度: {pattern['severity']:.2f}")
        print()
    
    assert len(patterns) >= 2, "应该学习到至少2个失败模式"
    print("✅ 失败模式学习测试通过")


def test_healing_strategy_learning():
    """测试修复策略学习"""
    print("\n" + "=" * 80)
    print("测试 2: 修复策略学习")
    print("=" * 80)
    
    agent = LearningAgent(knowledge_dir="test_knowledge")
    agent.reset_knowledge()
    
    # 模拟执行结果
    results = [
        create_mock_result('tc1', 'FAILED', 'Timeout'),
        create_mock_result('tc2', 'FAILED', 'Timeout'),
        create_mock_result('tc3', 'FAILED', 'Timeout'),
        create_mock_result('tc4', 'FAILED', 'Connection refused'),
        create_mock_result('tc5', 'FAILED', 'Connection refused'),
    ]
    
    # 模拟修复记录
    healing_records = [
        create_mock_healing_record('tc1', 'L1_RETRY', 'retry', True),
        create_mock_healing_record('tc2', 'L1_RETRY', 'retry', True),
        create_mock_healing_record('tc3', 'L2_DATA', 'regenerate', False),
        create_mock_healing_record('tc4', 'L1_RETRY', 'retry', True),
        create_mock_healing_record('tc5', 'L1_RETRY', 'retry', False),
    ]
    
    # 学习
    agent.learn(results, healing_records)
    
    # 获取最优策略
    best_timeout = agent.get_best_healing_strategy('timeout')
    best_connection = agent.get_best_healing_strategy('connection')
    
    print(f"\n学习到的最优策略:")
    print(f"  timeout → {best_timeout}")
    print(f"  connection → {best_connection}")
    
    # 查看详细统计
    print(f"\n修复统计:")
    print(json.dumps(agent.healing_stats, indent=2, ensure_ascii=False))
    
    assert best_timeout == 'L1_RETRY', "timeout 的最优策略应该是 L1_RETRY"
    print("✅ 修复策略学习测试通过")


def test_coverage_gap_analysis():
    """测试覆盖缺口分析"""
    print("\n" + "=" * 80)
    print("测试 3: 覆盖缺口分析")
    print("=" * 80)
    
    agent = LearningAgent(knowledge_dir="test_knowledge")
    agent.reset_knowledge()
    
    # 模拟执行结果（某些 API 失败率高但测试少）
    results = [
        # payment_refund: 2次测试，2次失败（失败率100%，测试少）
        create_mock_result('tc_payment_refund_001', 'FAILED', 'Error'),
        create_mock_result('tc_payment_refund_002', 'FAILED', 'Error'),
        
        # order_cancel: 3次测试，2次失败（失败率67%，测试少）
        create_mock_result('tc_order_cancel_001', 'FAILED', 'Error'),
        create_mock_result('tc_order_cancel_002', 'FAILED', 'Error'),
        create_mock_result('tc_order_cancel_003', 'PASSED', None),
        
        # user_login: 10次测试，1次失败（失败率10%，测试多）
        *[create_mock_result(f'tc_user_login_{i:03d}', 'PASSED', None) for i in range(1, 10)],
        create_mock_result('tc_user_login_010', 'FAILED', 'Error'),
    ]
    
    # 学习
    agent.learn(results, [])
    
    # 获取覆盖缺口
    gaps = agent.get_coverage_gaps()
    
    print(f"\n识别到的覆盖缺口:")
    for gap in gaps:
        print(f"  API: {gap['api']}")
        print(f"    测试次数: {gap['test_count']}")
        print(f"    失败率: {gap['failure_rate']:.1%}")
        print(f"    优先级: {gap['priority']}")
        print()
    
    assert len(gaps) >= 2, "应该识别到至少2个覆盖缺口"
    print("✅ 覆盖缺口分析测试通过")


def test_high_risk_apis():
    """测试高风险 API 识别"""
    print("\n" + "=" * 80)
    print("测试 4: 高风险 API 识别")
    print("=" * 80)
    
    agent = LearningAgent(knowledge_dir="test_knowledge")
    agent.reset_knowledge()
    
    # 模拟执行结果
    results = [
        # payment API: 高失败率
        *[create_mock_result(f'tc_payment_create_{i:03d}', 'FAILED', 'Error') for i in range(1, 8)],
        *[create_mock_result(f'tc_payment_create_{i:03d}', 'PASSED', None) for i in range(8, 11)],
        
        # order API: 中等失败率
        *[create_mock_result(f'tc_order_create_{i:03d}', 'FAILED', 'Error') for i in range(1, 4)],
        *[create_mock_result(f'tc_order_create_{i:03d}', 'PASSED', None) for i in range(4, 11)],
        
        # user API: 低失败率
        create_mock_result('tc_user_login_001', 'FAILED', 'Error'),
        *[create_mock_result(f'tc_user_login_{i:03d}', 'PASSED', None) for i in range(2, 11)],
    ]
    
    # 学习
    agent.learn(results, [])
    
    # 获取高风险 API
    high_risk = agent.get_high_risk_apis()
    
    print(f"\n高风险 API:")
    for api in high_risk:
        print(f"  {api['api']}")
        print(f"    风险分数: {api['risk_score']:.2f}")
        print(f"    失败率: {api['failure_rate']:.1%}")
        print(f"    失败次数: {api['total_failures']}/{api['total_executions']}")
        print()
    
    assert len(high_risk) >= 1, "应该识别到至少1个高风险 API"
    assert high_risk[0]['api'] == '/payment/create', "payment API 应该是最高风险"
    print("✅ 高风险 API 识别测试通过")


def test_knowledge_persistence():
    """测试知识持久化"""
    print("\n" + "=" * 80)
    print("测试 5: 知识持久化")
    print("=" * 80)
    
    # 第一次：学习并保存
    agent1 = LearningAgent(knowledge_dir="test_knowledge")
    agent1.reset_knowledge()
    
    results = [
        create_mock_result('tc_payment_001', 'FAILED', 'Timeout'),
        create_mock_result('tc_payment_002', 'FAILED', 'Timeout'),
    ]
    
    agent1.learn(results, [])
    
    patterns_before = len(agent1.failure_patterns)
    print(f"\n第一次学习: {patterns_before} 个失败模式")
    
    # 第二次：加载已有知识
    agent2 = LearningAgent(knowledge_dir="test_knowledge")
    patterns_after = len(agent2.failure_patterns)
    
    print(f"重新加载: {patterns_after} 个失败模式")
    
    assert patterns_after == patterns_before, "知识应该被持久化"
    
    # 检查文件是否存在
    knowledge_dir = Path("test_knowledge")
    assert (knowledge_dir / "failures.json").exists(), "failures.json 应该存在"
    assert (knowledge_dir / "healing_stats.json").exists(), "healing_stats.json 应该存在"
    assert (knowledge_dir / "coverage_gaps.json").exists(), "coverage_gaps.json 应该存在"
    assert (knowledge_dir / "api_stats.json").exists(), "api_stats.json 应该存在"
    
    print("✅ 知识持久化测试通过")


def test_learning_summary():
    """测试学习摘要"""
    print("\n" + "=" * 80)
    print("测试 6: 学习摘要")
    print("=" * 80)
    
    agent = LearningAgent(knowledge_dir="test_knowledge")
    agent.reset_knowledge()
    
    # 模拟完整学习过程
    results = [
        create_mock_result('tc_payment_001', 'FAILED', 'Timeout'),
        create_mock_result('tc_payment_002', 'FAILED', 'Timeout'),
        create_mock_result('tc_order_001', 'FAILED', 'Connection refused'),
        create_mock_result('tc_user_001', 'PASSED', None),
    ]
    
    healing_records = [
        create_mock_healing_record('tc_payment_001', 'L1_RETRY', 'retry', True),
        create_mock_healing_record('tc_payment_002', 'L1_RETRY', 'retry', True),
        create_mock_healing_record('tc_order_001', 'L1_RETRY', 'retry', False),
    ]
    
    agent.learn(results, healing_records)
    
    # 获取学习摘要
    summary = agent.get_learning_summary()
    
    print(f"\n学习摘要:")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    
    assert summary['failure_patterns']['total_patterns'] >= 2
    assert summary['healing_strategies']['error_types_learned'] >= 1
    
    print("✅ 学习摘要测试通过")


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("🧪 LearningAgent 测试（学习型代理）")
    print("=" * 80)
    
    try:
        test_failure_pattern_learning()
        test_healing_strategy_learning()
        test_coverage_gap_analysis()
        test_high_risk_apis()
        test_knowledge_persistence()
        test_learning_summary()
        
        print("\n" + "=" * 80)
        print("✅ 所有测试通过！LearningAgent 实现成功！")
        print("=" * 80)
        
        print("\n核心能力:")
        print("  ✅ 失败模式学习 - 识别常见失败模式")
        print("  ✅ 修复策略学习 - 统计最优修复策略")
        print("  ✅ 覆盖缺口分析 - 识别高风险但测试少的API")
        print("  ✅ 高风险API识别 - 基于历史数据计算风险分数")
        print("  ✅ 知识持久化 - 存储和加载学习结果")
        print("  ✅ 学习摘要 - 提供完整的学习报告")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
