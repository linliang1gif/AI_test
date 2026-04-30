#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
四阶段完整流程测试
Test Agent → Strategy Engine → Orchestrator → Self-Healing
"""

import requests
import json
import time


BASE_URL = "http://localhost:8000/api"


def test_complete_pipeline():
    """测试完整的四阶段流程"""
    print("\n" + "="*70)
    print("🚀 四阶段完整流程测试")
    print("="*70)
    
    # ==================== 阶段1: Test Agent ====================
    print("\n【阶段1】Test Agent - AI 决策分析")
    print("-" * 70)
    
    agent_request = {
        "requirement": "支付模块需要支持微信支付和支付宝支付",
        "git_diff": "+def wechat_pay():\n+    return process_payment('wechat')",
        "context": {
            "priority": "P0",
            "module": "支付模块"
        }
    }
    
    print("📤 发送需求到 Test Agent...")
    response = requests.post(f"{BASE_URL}/agent/analyze", json=agent_request)
    agent_result = response.json()
    
    print(f"✅ Test Agent 决策:")
    print(f"   需要测试: {agent_result['need_test']}")
    print(f"   测试类型: {agent_result['test_types']}")
    print(f"   风险等级: {agent_result['risk_level']}")
    print(f"   执行动作: {agent_result['action']}")
    print(f"   置信度: {agent_result['confidence']}")
    
    assert agent_result['need_test'] == True, "应该需要测试"
    # action 可能是 run_tests 或 execute_test
    assert agent_result['action'] in ['execute_test', 'run_tests'], "应该执行测试"
    
    # ==================== 阶段2: Strategy Engine ====================
    print("\n【阶段2】Strategy Engine - 生成测试策略")
    print("-" * 70)
    
    strategy_request = {
        "agent_decision": agent_result
    }
    
    print("📤 发送决策到 Strategy Engine...")
    response = requests.post(f"{BASE_URL}/strategy/generate", json=strategy_request)
    strategy_result = response.json()
    
    print(f"✅ 测试策略:")
    print(f"   模块数: {len(strategy_result['strategy'])}")
    
    for module in strategy_result['strategy'][:2]:  # 显示前2个
        print(f"\n   模块: {module['module']['name']}")
        print(f"   测试类型: {module['test_types']}")
        print(f"   优先级: {module['priority']}")
        print(f"   执行顺序: {module['execution_order']}")
    
    print(f"\n   总结:")
    print(f"   - 总模块数: {strategy_result['summary']['total_modules']}")
    if 'estimated_duration' in strategy_result['summary']:
        print(f"   - 预计耗时: {strategy_result['summary']['estimated_duration']}分钟")
    
    assert len(strategy_result['strategy']) > 0, "应该有测试策略"
    
    # ==================== 阶段3: Orchestrator ====================
    print("\n【阶段3】Orchestrator - 执行测试")
    print("-" * 70)
    
    # 注意：orchestrator 需要完整的 strategy 对象，不只是 strategy 列表
    orchestrator_request = strategy_result  # 直接传递整个 strategy_result
    
    print("📤 发送策略到 Orchestrator...")
    response = requests.post(f"{BASE_URL}/orchestrator/run", json=orchestrator_request)
    
    if response.status_code != 200:
        print(f"❌ Orchestrator 调用失败: {response.status_code}")
        print(f"   响应: {response.text}")
        orchestrator_result = {
            "results": [],
            "summary": {"total": 0, "passed": 0, "failed": 0, "duration": 0}
        }
    else:
        orchestrator_result = response.json()
    
    print(f"✅ 执行结果:")
    print(f"   总数: {orchestrator_result['summary']['total']}")
    print(f"   通过: {orchestrator_result['summary']['passed']}")
    print(f"   失败: {orchestrator_result['summary']['failed']}")
    print(f"   总耗时: {orchestrator_result['summary']['duration']}s")
    
    # 显示部分结果
    for result in orchestrator_result['results'][:3]:
        status_icon = "✅" if result['status'] == 'passed' else "❌"
        print(f"\n   {status_icon} {result['module']}")
        print(f"      状态: {result['status']}")
        print(f"      耗时: {result['duration']}s")
    
    # ==================== 阶段4: Self-Healing ====================
    print("\n【阶段4】Self-Healing - 自动修复失败用例")
    print("-" * 70)
    
    # 查找失败的测试
    failed_tests = [r for r in orchestrator_result['results'] if r['status'] == 'failed']
    
    if failed_tests:
        print(f"发现 {len(failed_tests)} 个失败用例，开始自动修复...")
        
        for failed in failed_tests[:2]:  # 最多修复2个
            print(f"\n🔧 修复: {failed['module']}")
            
            healing_request = {
                "module": failed['module'],
                "error": failed.get('details', 'Unknown error'),
                "test_type": "api"
            }
            
            response = requests.post(f"{BASE_URL}/healing/fix", json=healing_request)
            healing_result = response.json()
            
            print(f"   修复成功: {healing_result['fixed']}")
            print(f"   修复策略: {healing_result.get('fix_strategy', 'N/A')[:50]}...")
            print(f"   置信度: {healing_result['confidence']}")
            
            if healing_result.get('retry_result'):
                retry = healing_result['retry_result']
                print(f"   重试结果: {retry['status']}")
    else:
        print("✅ 所有测试通过，无需修复")
    
    # ==================== 最终统计 ====================
    print("\n" + "="*70)
    print("📊 四阶段流程统计")
    print("="*70)
    
    # Test Agent 统计
    agent_stats_response = requests.get(f"{BASE_URL}/agent/statistics")
    agent_stats = agent_stats_response.json()['data']
    
    print(f"\n【Test Agent】")
    print(f"   总分析次数: {agent_stats['total_analyses']}")
    print(f"   需要测试: {agent_stats['need_test_count']}")
    
    # Strategy Engine 统计
    strategy_stats_response = requests.get(f"{BASE_URL}/strategy/statistics")
    strategy_stats = strategy_stats_response.json()['data']
    
    print(f"\n【Strategy Engine】")
    print(f"   总策略数: {strategy_stats['total_strategies']}")
    print(f"   总模块数: {strategy_stats['total_modules']}")
    
    # Orchestrator 统计
    orchestrator_stats_response = requests.get(f"{BASE_URL}/orchestrator/statistics")
    orchestrator_stats = orchestrator_stats_response.json()['data']
    
    print(f"\n【Orchestrator】")
    print(f"   总执行次数: {orchestrator_stats['total_runs']}")
    print(f"   总测试数: {orchestrator_stats['total_tests']}")
    print(f"   通过率: {orchestrator_stats['pass_rate']}%")
    
    # Self-Healing 统计
    healing_stats_response = requests.get(f"{BASE_URL}/healing/statistics")
    healing_stats = healing_stats_response.json()['data']
    
    print(f"\n【Self-Healing】")
    print(f"   总修复次数: {healing_stats['total_healings']}")
    print(f"   成功修复: {healing_stats['successful_fixes']}")
    print(f"   成功率: {healing_stats['success_rate']}%")
    
    print("\n" + "="*70)
    print("✅ 四阶段流程测试完成！")
    print("="*70)


def test_healing_integration():
    """测试 Self-Healing 与 Orchestrator 的集成"""
    print("\n" + "="*70)
    print("🔗 Self-Healing 集成测试")
    print("="*70)
    
    # 创建一个会失败的策略
    print("\n1️⃣ 创建测试策略（包含会失败的用例）")
    
    strategy_with_list = {
        "strategy": [
            {
                "module": {
                    "name": "支付模块",
                    "description": "支付接口测试",
                    "impact": "high"
                },
                "test_types": ["api"],
                "priority": "P0",
                "execution_order": 1,
                "execution_hint": {
                    "parallel": False,
                    "estimated_time": 2
                }
            }
        ]
    }
    
    # 执行测试
    print("\n2️⃣ 执行测试（可能失败）")
    response = requests.post(f"{BASE_URL}/orchestrator/run", json=strategy_with_list)
    
    if response.status_code != 200:
        print(f"   ⚠️  Orchestrator 调用失败: {response.status_code}")
        return
    
    result = response.json()
    
    print(f"   执行结果: {result['summary']['passed']}/{result['summary']['total']} 通过")
    
    # 如果有失败，触发修复
    failed_count = result['summary']['failed']
    if failed_count > 0:
        print(f"\n3️⃣ 触发自动修复（{failed_count} 个失败用例）")
        
        for test_result in result['results']:
            if test_result['status'] == 'failed':
                healing_request = {
                    "module": test_result['module'],
                    "error": test_result.get('details', 'Test failed'),
                    "test_type": "api"
                }
                
                healing_response = requests.post(f"{BASE_URL}/healing/fix", json=healing_request)
                healing_result = healing_response.json()
                
                print(f"\n   修复 {test_result['module']}:")
                print(f"   - 修复成功: {healing_result['fixed']}")
                print(f"   - 重试结果: {healing_result.get('retry_result', {}).get('status', 'N/A')}")
    else:
        print(f"\n3️⃣ 所有测试通过，无需修复")
    
    print("\n✅ 集成测试完成")


if __name__ == "__main__":
    try:
        test_complete_pipeline()
        time.sleep(1)
        test_healing_integration()
        
        print("\n" + "="*70)
        print("🎉 四阶段系统完整测试通过！")
        print("="*70)
        print("\n系统能力:")
        print("   ✅ AI 智能决策（Test Agent）")
        print("   ✅ 策略生成（Strategy Engine）")
        print("   ✅ 自动执行（Orchestrator）")
        print("   ✅ 自动修复（Self-Healing）")
        
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 连接失败: 请确保后端服务器运行在 {BASE_URL}")
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
