#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试四阶段流程 V2
Agent V3 → Strategy → Case Generator → Orchestrator V2

验证完整的集成流程
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from agent.test_agent_service import get_test_agent_service
from strategy.strategy_service import get_strategy_service
from case_generator.case_service import get_case_service
from orchestrator.orchestrator_service import get_orchestrator_service


def test_four_stage_v2_pipeline():
    """测试四阶段 V2 流程"""
    
    print("=" * 80)
    print("测试四阶段流程 V2: Agent V3 → Strategy → Case Generator → Orchestrator V2")
    print("=" * 80)
    
    # ==================== 阶段1: Test Agent V3 ====================
    print("\n【阶段1】Test Agent V3 - AI决策分析")
    print("-" * 80)
    
    requirement = """
需求：支付模块优化
1. 支付接口性能优化
2. 增加支付超时重试机制
3. 优化支付结果通知
"""
    
    git_diff = """
diff --git a/payment/service.py b/payment/service.py
+ def retry_payment(order_id):
+     # 支付重试逻辑
"""
    
    agent_service = get_test_agent_service()
    agent_result = agent_service.analyze(requirement, git_diff)
    
    print(f"✅ Agent 分析完成:")
    print(f"   - 是否需要测试: {agent_result['need_test']}")
    print(f"   - 风险等级: {agent_result['risk_level']}")
    print(f"   - 测试类型: {', '.join(agent_result['test_types'])}")
    print(f"   - 决策动作: {agent_result.get('action', 'N/A')}")
    print(f"   - 置信度: {agent_result.get('confidence', 'N/A')}")
    print(f"   - 解析模块数: {len(agent_result.get('parsed_modules', []))}")
    
    if not agent_result['need_test']:
        print("⏭️  无需测试，流程结束")
        return
    
    # ==================== 阶段2: Strategy Engine ====================
    print("\n【阶段2】Strategy Engine - 测试策略生成")
    print("-" * 80)
    
    strategy_service = get_strategy_service()
    strategy_result = strategy_service.generate_strategy(agent_result)
    
    print(f"✅ 策略生成完成:")
    print(f"   - 策略数: {len(strategy_result['strategy'])}")
    print(f"   - 总用例数: {strategy_result.get('total_cases', strategy_result.get('summary', {}).get('total_cases', 0))}")
    
    for strategy in strategy_result['strategy']:
        module_name = strategy['module']['name']
        test_types = ', '.join(strategy['test_types'])
        case_count = strategy['case_count']
        print(f"   📦 {module_name}: {test_types} ({case_count}个用例)")
    
    # ==================== 阶段3: Case Generator ====================
    print("\n【阶段3】Case Generator - 测试用例生成")
    print("-" * 80)
    
    case_service = get_case_service()
    case_result = case_service.generate_cases(strategy_result)
    
    print(f"✅ 用例生成完成:")
    print(f"   - 模块数: {len(case_result['cases'])}")
    print(f"   - 总用例数: {case_result['total_cases']}")
    
    for module_cases in case_result['cases']:
        module_name = module_cases['module']
        cases = module_cases['cases']
        print(f"   📦 {module_name}: {len(cases)}个用例")
        
        # 显示前3个用例
        for case in cases[:3]:
            print(f"      • {case['id']}: {case['title']} [{case['type']}]")
    
    # ==================== 阶段4: Orchestrator V2 ====================
    print("\n【阶段4】Orchestrator V2 - 测试执行调度")
    print("-" * 80)
    
    orchestrator_service = get_orchestrator_service()
    
    # 使用新模式：传入 cases
    execution_result = orchestrator_service.run(strategy_result, cases=case_result)
    
    print(f"✅ 执行完成:")
    print(f"   - 执行模式: {execution_result.get('mode', 'unknown')}")
    print(f"   - 模块数: {len(execution_result['results'])}")
    print(f"   - 总测试数: {execution_result['summary']['total']}")
    print(f"   - 通过: {execution_result['summary']['passed']}")
    print(f"   - 失败: {execution_result['summary']['failed']}")
    print(f"   - 通过率: {execution_result['summary']['pass_rate']}%")
    print(f"   - 总耗时: {execution_result['summary']['duration']}秒")
    
    # 显示每个模块的执行结果
    for module_result in execution_result['results']:
        module_name = module_result['module']
        status = module_result['status']
        duration = module_result['duration']
        case_results = module_result.get('case_results', [])
        
        print(f"\n   📦 {module_name}: {status} ({duration}秒)")
        print(f"      {module_result['details']}")
        
        if case_results:
            passed = sum(1 for cr in case_results if cr['status'] == 'passed')
            print(f"      用例结果: {passed}/{len(case_results)} 通过")
    
    # ==================== 总结 ====================
    print("\n" + "=" * 80)
    print("✅ 四阶段流程 V2 测试完成")
    print("=" * 80)
    print(f"   阶段1: Agent V3 ✅ (解析{len(agent_result.get('parsed_modules', []))}个模块)")
    print(f"   阶段2: Strategy ✅ (生成{len(strategy_result['strategy'])}个策略)")
    print(f"   阶段3: Case Generator ✅ (生成{case_result['total_cases']}个用例)")
    print(f"   阶段4: Orchestrator V2 ✅ (执行{execution_result['summary']['total']}个模块)")
    print(f"\n   最终结果: {execution_result['summary']['passed']}/{execution_result['summary']['total']} 通过")
    print("=" * 80)


def test_compatibility_mode():
    """测试兼容模式：不传 cases 参数"""
    
    print("\n" + "=" * 80)
    print("测试兼容模式: 不传 cases 参数（使用策略模式）")
    print("=" * 80)
    
    # 准备测试策略
    test_strategy = {
        "strategy": [
            {
                "module": {"name": "兼容测试模块", "impact": "high"},
                "priority": "P1",
                "test_types": ["api", "ui"],
                "case_count": 8,
                "execution_order": 1,
                "execution_hint": {"parallel": False, "timeout": 60}
            }
        ],
        "total_modules": 1,
        "total_cases": 8
    }
    
    orchestrator_service = get_orchestrator_service()
    
    # 不传 cases 参数
    result = orchestrator_service.run(test_strategy, cases=None)
    
    print(f"✅ 兼容模式执行完成:")
    print(f"   - 执行模式: {result.get('mode', 'unknown')}")
    print(f"   - 通过: {result['summary']['passed']}/{result['summary']['total']}")
    
    assert result.get('mode') == 'strategy', "应该使用策略模式"
    
    print("=" * 80)


if __name__ == "__main__":
    # 测试1: 完整四阶段流程
    test_four_stage_v2_pipeline()
    
    # 测试2: 兼容模式
    test_compatibility_mode()
    
    print("\n🎉 所有测试通过！")
