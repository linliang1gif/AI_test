#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试三阶段流程: Agent → Strategy → Case Generator
使用 Mock 数据避免 AI 调用延迟
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from agent.test_agent_service import get_test_agent_service
from strategy.strategy_service import get_strategy_service
from case_generator.case_service import get_case_service


def test_three_stage_quick():
    """快速测试三阶段流程"""
    
    print("=" * 70)
    print("快速测试: Agent V3 → Strategy → Case Generator")
    print("=" * 70)
    
    # 准备测试数据
    requirement = """
    需求文档：电商平台支付模块升级
    
    1. 支付模块
    - 支持微信支付
    - 支持支付宝支付
    - 支持银行卡支付
    
    2. 订单模块
    - 创建订单
    - 查询订单
    - 取消订单
    """
    
    git_diff = """
    + def process_payment(amount, method):
    +     return {"status": "success"}
    """
    
    # 阶段1: Agent 分析（使用 Mock）
    print("\n【阶段1】Agent V3 分析")
    print("-" * 70)
    
    # 直接构造 Agent 输出（跳过 AI 调用）
    agent_result = {
        "action": "test",
        "modules": ["支付模块", "订单模块"],
        "priority": "P0",
        "risk_level": "高",
        "test_types": ["api", "integration"],
        "estimated_effort": "中等",
        "confidence": 0.85,
        "test_scope": {
            "modules": ["支付模块", "订单模块"],
            "test_types": ["api", "integration"]
        },
        "execution_hint": {
            "parallel": True,
            "timeout": 60
        },
        "timestamp": "2024-03-21T10:00:00",
        "parsed_modules": [
            {
                "id": "mod_001",
                "name": "支付模块",
                "description": "支付功能模块",
                "functions": ["微信支付", "支付宝支付", "银行卡支付"],
                "priority": "高",
                "complexity": "中等",
                "dependencies": []
            },
            {
                "id": "mod_002",
                "name": "订单模块",
                "description": "订单管理模块",
                "functions": ["创建订单", "查询订单", "取消订单"],
                "priority": "高",
                "complexity": "中等",
                "dependencies": ["支付模块"]
            }
        ],
        "parsed_sections": [
            {"title": "支付模块", "content": "支持微信支付、支付宝支付、银行卡支付"},
            {"title": "订单模块", "content": "创建订单、查询订单、取消订单"}
        ]
    }
    
    print(f"✅ Agent 分析完成:")
    print(f"   - 决策: {agent_result['action']}")
    print(f"   - 影响模块: {agent_result['modules']}")
    print(f"   - 解析模块数: {len(agent_result['parsed_modules'])}")
    
    # 阶段2: Strategy 生成
    print("\n【阶段2】Strategy 生成测试策略")
    print("-" * 70)
    
    strategy_service = get_strategy_service()
    strategy_result = strategy_service.generate_strategy(agent_result)
    
    print(f"✅ Strategy 生成完成:")
    print(f"   - 模块数: {strategy_result['total_modules']}")
    print(f"   - 预估用例数: {strategy_result['total_cases']}")
    
    for mod_strategy in strategy_result['strategy']:
        module_name = mod_strategy['module']['name']
        test_types = mod_strategy['test_types']
        case_count = mod_strategy['case_count']
        print(f"      • {module_name}: {test_types} → {case_count}个用例")
    
    # 阶段3: Case Generator 生成用例
    print("\n【阶段3】Case Generator 生成测试用例")
    print("-" * 70)
    
    case_service = get_case_service()
    case_result = case_service.generate_cases(strategy_result)
    
    print(f"✅ Case Generator 完成:")
    print(f"   - 模块数: {len(case_result['cases'])}")
    print(f"   - 总用例数: {case_result['total_cases']}")
    
    for module_cases in case_result['cases']:
        module_name = module_cases['module']
        cases = module_cases['cases']
        print(f"\n   📦 {module_name}: {len(cases)} 个用例")
        
        # 统计用例类型
        type_counts = {}
        for case in cases:
            case_type = case['type']
            type_counts[case_type] = type_counts.get(case_type, 0) + 1
        
        print(f"      类型分布: {type_counts}")
        
        # 显示前3个用例
        for i, case in enumerate(cases[:3], 1):
            print(f"      {i}. {case['title']}")
            print(f"         • 类型: {case['type']}, 优先级: {case['priority']}")
            print(f"         • 步骤数: {len(case['steps'])}")
            print(f"         • 自动化: {case['automation_feasible']['feasibility']}")
    
    # 验证优先级过滤规则
    print("\n【验证】优先级过滤规则")
    print("-" * 70)
    
    # P0 应该有 正常+异常+边界
    p0_module = case_result['cases'][0]
    p0_types = set(case['type'] for case in p0_module['cases'])
    print(f"✅ P0 模块({p0_module['module']})用例类型: {p0_types}")
    
    expected_p0 = {'功能测试', '异常测试', '边界测试'}
    if p0_types == expected_p0:
        print(f"   ✅ 符合 P0 规则: 正常+异常+边界")
    else:
        print(f"   ⚠️  不完全符合 P0 规则,期望: {expected_p0}")
    
    # 总结
    print("\n" + "=" * 70)
    print("✅ 三阶段流程验证完成")
    print("=" * 70)
    print(f"📊 数据流转:")
    print(f"   1. Agent: 解析 {len(agent_result['parsed_modules'])} 个模块")
    print(f"   2. Strategy: 生成 {strategy_result['total_modules']} 个策略")
    print(f"   3. Case Generator: 生成 {case_result['total_cases']} 个用例")
    print("=" * 70)


if __name__ == "__main__":
    test_three_stage_quick()
