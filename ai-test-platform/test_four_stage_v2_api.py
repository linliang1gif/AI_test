#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试四阶段流程 V2 - 通过 API
Agent V3 → Strategy → Case Generator → Orchestrator V2

验证完整的 API 集成
"""

import requests
import json

BASE_URL = "http://localhost:8000/api"


def test_four_stage_v2_via_api():
    """通过 API 测试四阶段 V2 流程"""
    
    print("=" * 80)
    print("测试四阶段流程 V2 (通过 API)")
    print("=" * 80)
    
    # ==================== 阶段1: Test Agent V3 ====================
    print("\n【阶段1】Test Agent V3 - AI决策分析")
    print("-" * 80)
    
    agent_payload = {
        "requirement": """
需求：订单管理模块升级
1. 新增订单批量导入功能
2. 优化订单查询性能
3. 增加订单状态流转日志
""",
        "git_diff": """
diff --git a/order/service.py b/order/service.py
+ def batch_import_orders(file_path):
+     # 批量导入订单
"""
    }
    
    response = requests.post(f"{BASE_URL}/agent/analyze", json=agent_payload)
    
    print(f"   状态码: {response.status_code}")
    
    if response.status_code != 200:
        print(f"   ❌ Agent 分析失败: {response.text}")
        return
    
    agent_result = response.json()
    
    print(f"   ✅ Agent 分析完成:")
    print(f"      - 是否需要测试: {agent_result['need_test']}")
    print(f"      - 风险等级: {agent_result['risk_level']}")
    print(f"      - 测试类型: {', '.join(agent_result['test_types'])}")
    print(f"      - 决策动作: {agent_result.get('action', 'N/A')}")
    print(f"      - 解析模块数: {len(agent_result.get('parsed_modules', []))}")
    
    if not agent_result['need_test']:
        print("   ⏭️  无需测试，流程结束")
        return
    
    # ==================== 阶段2: Strategy Engine ====================
    print("\n【阶段2】Strategy Engine - 测试策略生成")
    print("-" * 80)
    
    strategy_payload = {
        "agent_decision": agent_result
    }
    
    response = requests.post(f"{BASE_URL}/strategy/generate", json=strategy_payload)
    
    print(f"   状态码: {response.status_code}")
    
    if response.status_code != 200:
        print(f"   ❌ 策略生成失败: {response.text}")
        return
    
    strategy_result = response.json()
    
    print(f"   ✅ 策略生成完成:")
    print(f"      - 策略数: {len(strategy_result['strategy'])}")
    print(f"      - 总用例数: {strategy_result.get('total_cases', 0)}")
    
    for strategy in strategy_result['strategy'][:3]:
        module_name = strategy['module']['name']
        test_types = ', '.join(strategy['test_types'])
        case_count = strategy['case_count']
        print(f"      📦 {module_name}: {test_types} ({case_count}个用例)")
    
    # ==================== 阶段3: Case Generator ====================
    print("\n【阶段3】Case Generator - 测试用例生成")
    print("-" * 80)
    
    case_payload = {
        "strategy": strategy_result
    }
    
    response = requests.post(f"{BASE_URL}/case/generate", json=case_payload)
    
    print(f"   状态码: {response.status_code}")
    
    if response.status_code != 200:
        print(f"   ❌ 用例生成失败: {response.text}")
        return
    
    case_result = response.json()
    
    print(f"   ✅ 用例生成完成:")
    print(f"      - 模块数: {len(case_result['cases'])}")
    print(f"      - 总用例数: {case_result['total_cases']}")
    
    for module_cases in case_result['cases'][:3]:
        module_name = module_cases['module']
        cases = module_cases['cases']
        print(f"      📦 {module_name}: {len(cases)}个用例")
    
    # ==================== 阶段4: Orchestrator V2 ====================
    print("\n【阶段4】Orchestrator V2 - 测试执行调度")
    print("-" * 80)
    
    orchestrator_payload = {
        "strategy": strategy_result,
        "cases": case_result  # 传入用例
    }
    
    response = requests.post(f"{BASE_URL}/orchestrator/run", json=orchestrator_payload)
    
    print(f"   状态码: {response.status_code}")
    
    if response.status_code != 200:
        print(f"   ❌ 执行失败: {response.text}")
        return
    
    execution_result = response.json()
    
    print(f"   ✅ 执行完成:")
    print(f"      - 执行模式: {execution_result.get('mode', 'unknown')}")
    print(f"      - 模块数: {len(execution_result['results'])}")
    print(f"      - 总测试数: {execution_result['summary']['total']}")
    print(f"      - 通过: {execution_result['summary']['passed']}")
    print(f"      - 失败: {execution_result['summary']['failed']}")
    print(f"      - 通过率: {execution_result['summary']['pass_rate']}%")
    print(f"      - 总耗时: {execution_result['summary']['duration']}秒")
    
    # 显示用例级别结果
    for module_result in execution_result['results'][:3]:
        module_name = module_result['module']
        status = module_result['status']
        case_results = module_result.get('case_results', [])
        
        if case_results:
            passed = sum(1 for cr in case_results if cr['status'] == 'passed')
            print(f"      📦 {module_name}: {status} ({passed}/{len(case_results)} 通过)")
    
    # ==================== 总结 ====================
    print("\n" + "=" * 80)
    print("✅ 四阶段流程 V2 (API) 测试完成")
    print("=" * 80)
    print(f"   阶段1: Agent V3 ✅")
    print(f"   阶段2: Strategy ✅")
    print(f"   阶段3: Case Generator ✅")
    print(f"   阶段4: Orchestrator V2 ✅ (模式: {execution_result.get('mode', 'unknown')})")
    print(f"\n   最终结果: {execution_result['summary']['passed']}/{execution_result['summary']['total']} 通过")
    print("=" * 80)


if __name__ == "__main__":
    try:
        test_four_stage_v2_via_api()
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务器")
        print("   请确保后端服务器正在运行: python backend_api_server.py")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
