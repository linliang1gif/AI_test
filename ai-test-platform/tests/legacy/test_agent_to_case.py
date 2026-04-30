#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试完整流程: Agent V3 → Strategy → Case Generator
验证三阶段集成是否正常工作
"""

import requests
import json

BASE_URL = "http://localhost:8000/api"


def test_agent_to_case_pipeline():
    """测试 Agent → Strategy → Case Generator 完整流程"""
    
    print("=" * 70)
    print("测试完整流程: Agent V3 → Strategy → Case Generator")
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
    +     # 处理支付逻辑
    +     return {"status": "success"}
    """
    
    # 阶段1: Agent 分析
    print("\n【阶段1】Agent 分析需求")
    print("-" * 70)
    
    try:
        response = requests.post(
            f"{BASE_URL}/agent/analyze",
            json={
                "requirement": requirement,
                "git_diff": git_diff,
                "priority": "P0"
            },
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ Agent 分析失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return
        
        agent_result = response.json()
        print(f"✅ Agent 分析完成:")
        print(f"   - 决策: {agent_result['action']}")
        print(f"   - 影响模块: {agent_result['modules']}")
        print(f"   - 风险等级: {agent_result['risk_level']}")
        print(f"   - 置信度: {agent_result['confidence']}")
        
        # 显示解析的模块
        if 'parsed_modules' in agent_result:
            print(f"   - 解析模块数: {len(agent_result['parsed_modules'])}")
            for mod in agent_result['parsed_modules'][:2]:
                print(f"      • {mod['name']}: {len(mod.get('functions', []))} 个功能")
        
    except Exception as e:
        print(f"❌ Agent 分析异常: {e}")
        return
    
    # 阶段2: Strategy 生成
    print("\n【阶段2】Strategy 生成测试策略")
    print("-" * 70)
    
    try:
        response = requests.post(
            f"{BASE_URL}/strategy/generate",
            json={"agent_decision": agent_result},
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Strategy 生成失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return
        
        strategy_result = response.json()
        print(f"✅ Strategy 生成完成:")
        print(f"   - 模块数: {strategy_result['total_modules']}")
        print(f"   - 预估用例数: {strategy_result['total_cases']}")
        
        for mod_strategy in strategy_result['strategy']:
            module_name = mod_strategy['module']['name']
            test_types = mod_strategy['test_types']
            case_count = mod_strategy['case_count']
            print(f"      • {module_name}: {test_types} → {case_count}个用例")
        
    except Exception as e:
        print(f"❌ Strategy 生成异常: {e}")
        return
    
    # 阶段3: Case Generator 生成用例
    print("\n【阶段3】Case Generator 生成测试用例")
    print("-" * 70)
    
    try:
        response = requests.post(
            f"{BASE_URL}/case/generate",
            json={"strategy": strategy_result},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Case Generator 失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return
        
        case_result = response.json()
        print(f"✅ Case Generator 完成:")
        print(f"   - 模块数: {len(case_result['cases'])}")
        print(f"   - 总用例数: {case_result['total_cases']}")
        
        for module_cases in case_result['cases']:
            module_name = module_cases['module']
            cases = module_cases['cases']
            print(f"\n   📦 {module_name}: {len(cases)} 个用例")
            
            # 显示前3个用例
            for i, case in enumerate(cases[:3], 1):
                print(f"      {i}. {case['title']}")
                print(f"         • 类型: {case['type']}")
                print(f"         • 优先级: {case['priority']}")
                print(f"         • 步骤数: {len(case['steps'])}")
                print(f"         • 自动化: {case['automation_feasible']['feasibility']}")
        
    except Exception as e:
        print(f"❌ Case Generator 异常: {e}")
        return
    
    # 总结
    print("\n" + "=" * 70)
    print("✅ 三阶段流程测试完成")
    print("=" * 70)
    print(f"📊 流程总结:")
    print(f"   Agent → {len(agent_result['modules'])} 个影响模块")
    print(f"   Strategy → {strategy_result['total_modules']} 个测试模块")
    print(f"   Case Generator → {case_result['total_cases']} 个测试用例")
    print("=" * 70)


if __name__ == "__main__":
    test_agent_to_case_pipeline()
