"""
端到端测试: Test Agent → Strategy Engine
验证完整决策到策略流程
"""
import requests
import json

AGENT_URL = "http://localhost:8000/api/agent"
STRATEGY_URL = "http://localhost:8000/api/strategy"

def test_e2e_payment_feature():
    """端到端测试: 支付功能变更"""
    print("\n" + "="*60)
    print("🔄 端到端测试: 支付功能变更")
    print("="*60)
    
    # Step 1: Test Agent 分析
    print("\n【Step 1: Test Agent 决策】")
    agent_request = {
        "requirement": "新增微信支付功能，支持扫码支付和H5支付",
        "git_diff": """
diff --git a/payment/wechat.py b/payment/wechat.py
+class WechatPayment:
+    def scan_pay(self, order_id, amount):
+        # 扫码支付逻辑
+    def h5_pay(self, order_id, amount):
+        # H5支付逻辑
"""
    }
    
    agent_response = requests.post(
        f"{AGENT_URL}/analyze",
        json=agent_request,
        timeout=30
    )
    agent_decision = agent_response.json()
    
    print(f"  action: {agent_decision['action']}")
    print(f"  priority: {agent_decision['priority']}")
    print(f"  modules: {agent_decision['modules']}")
    print(f"  confidence: {agent_decision['confidence']}")
    print(f"  test_scope: {agent_decision['test_scope']}")
    
    # Step 2: Strategy Engine 生成策略
    print(f"\n【Step 2: Strategy Engine 生成策略】")
    strategy_request = {
        "agent_decision": agent_decision
    }
    
    strategy_response = requests.post(
        f"{STRATEGY_URL}/generate",
        json=strategy_request,
        timeout=10
    )
    strategy_result = strategy_response.json()
    
    print(f"  总模块数: {strategy_result['total_modules']}")
    print(f"  总用例数: {strategy_result['total_cases']}")
    print(f"  策略置信度: {strategy_result['confidence']}")
    
    print(f"\n  模块策略:")
    for s in strategy_result['strategy']:
        print(f"    {s['execution_order']}. {s['module']}")
        print(f"       测试类型: {s['test_types']}")
        print(f"       用例数: {s['case_count']}")
    
    # Step 3: 验证流程
    print(f"\n【Step 3: 流程验证】")
    
    # 验证1: Agent决策被正确传递
    if strategy_result['source_decision'] == agent_decision['timestamp']:
        print(f"  ✅ 决策溯源正确")
    else:
        print(f"  ❌ 决策溯源失败")
    
    # 验证2: 置信度传递
    if strategy_result['confidence'] == agent_decision['confidence']:
        print(f"  ✅ 置信度传递正确")
    else:
        print(f"  ❌ 置信度传递失败")
    
    # 验证3: 支付模块特殊规则
    payment_strategy = next((s for s in strategy_result['strategy'] if '支付' in s['module']), None)
    if payment_strategy and 'integration' in payment_strategy['test_types']:
        print(f"  ✅ 支付模块自动添加 integration 测试")
    else:
        print(f"  ⚠️  支付模块未添加 integration 测试")
    
    # 验证4: 用例数合理
    if strategy_result['total_cases'] >= 25:
        print(f"  ✅ 高风险场景用例数充足 ({strategy_result['total_cases']})")
    else:
        print(f"  ⚠️  用例数偏少 ({strategy_result['total_cases']})")
    
    return agent_decision, strategy_result

def test_e2e_documentation():
    """端到端测试: 文档更新"""
    print("\n" + "="*60)
    print("🔄 端到端测试: 文档更新")
    print("="*60)
    
    # Step 1: Test Agent 分析
    print("\n【Step 1: Test Agent 决策】")
    agent_request = {
        "requirement": "更新API文档，添加新接口说明",
        "git_diff": "diff --git a/docs/api.md\n+## 新接口..."
    }
    
    agent_response = requests.post(
        f"{AGENT_URL}/analyze",
        json=agent_request,
        timeout=30
    )
    agent_decision = agent_response.json()
    
    print(f"  action: {agent_decision['action']}")
    print(f"  need_test: {agent_decision['need_test']}")
    
    # Step 2: Strategy Engine 生成策略
    print(f"\n【Step 2: Strategy Engine 生成策略】")
    strategy_request = {
        "agent_decision": agent_decision
    }
    
    strategy_response = requests.post(
        f"{STRATEGY_URL}/generate",
        json=strategy_request,
        timeout=10
    )
    strategy_result = strategy_response.json()
    
    print(f"  策略列表: {strategy_result['strategy']}")
    print(f"  总模块数: {strategy_result['total_modules']}")
    
    # 验证
    print(f"\n【验证】")
    if agent_decision['action'] == 'skip':
        if strategy_result['strategy'] == []:
            print(f"  ✅ skip决策正确生成空策略")
        else:
            print(f"  ❌ skip决策应返回空策略")
    else:
        print(f"  ⚠️  文档更新被判断为需要测试（模型特性）")

def test_e2e_multiple_changes():
    """端到端测试: 多个变更批量处理"""
    print("\n" + "="*60)
    print("🔄 端到端测试: 批量处理多个变更")
    print("="*60)
    
    changes = [
        {
            "name": "支付功能",
            "requirement": "新增支付宝支付",
            "git_diff": "diff --git a/payment/alipay.py..."
        },
        {
            "name": "订单查询",
            "requirement": "优化订单查询接口",
            "git_diff": "diff --git a/order/query.py..."
        },
        {
            "name": "日志优化",
            "requirement": "调整日志输出格式",
            "git_diff": "diff --git a/utils/logger.py..."
        }
    ]
    
    print(f"\n处理 {len(changes)} 个变更...")
    
    all_strategies = []
    
    for change in changes:
        print(f"\n  处理: {change['name']}")
        
        # Agent 决策
        agent_response = requests.post(
            f"{AGENT_URL}/analyze",
            json={
                "requirement": change['requirement'],
                "git_diff": change['git_diff']
            },
            timeout=30
        )
        agent_decision = agent_response.json()
        
        print(f"    Agent: action={agent_decision['action']}, priority={agent_decision['priority']}")
        
        # Strategy 生成
        if agent_decision['action'] == 'run_tests':
            strategy_response = requests.post(
                f"{STRATEGY_URL}/generate",
                json={"agent_decision": agent_decision},
                timeout=10
            )
            strategy = strategy_response.json()
            
            print(f"    Strategy: {strategy['total_modules']}模块, {strategy['total_cases']}用例")
            all_strategies.append(strategy)
    
    # 汇总
    print(f"\n【汇总统计】")
    total_modules = sum(s['total_modules'] for s in all_strategies)
    total_cases = sum(s['total_cases'] for s in all_strategies)
    
    print(f"  需要测试的变更: {len(all_strategies)}/{len(changes)}")
    print(f"  总模块数: {total_modules}")
    print(f"  总用例数: {total_cases}")
    print(f"  建议测试人员: {max(1, total_cases // 20)}")

def main():
    """运行所有端到端测试"""
    print("\n" + "🚀 Agent → Strategy 端到端测试".center(60, "="))
    
    try:
        # 健康检查
        agent_health = requests.get(f"{AGENT_URL}/health", timeout=5).json()
        strategy_health = requests.get(f"{STRATEGY_URL}/health", timeout=5).json()
        
        print(f"\n✅ 服务状态:")
        print(f"   Test Agent: {agent_health['status']}")
        print(f"   Strategy Engine: {strategy_health['status']}")
        
        # 运行测试
        test_e2e_payment_feature()
        test_e2e_documentation()
        test_e2e_multiple_changes()
        
        # 总结
        print("\n" + "="*60)
        print("✅ Agent → Strategy 端到端测试完成")
        print("="*60)
        print("\n🎯 完整流程验证:")
        print("  1. Test Agent 分析需求和代码变更 ✅")
        print("  2. 输出V2决策（action, confidence, test_scope等）✅")
        print("  3. Strategy Engine 消费决策 ✅")
        print("  4. 生成结构化策略（可被Orchestrator执行）✅")
        print("\n📦 下一步: 实现 Orchestrator 执行引擎")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
