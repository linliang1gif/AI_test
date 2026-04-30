"""
测试完整流程：Agent → Strategy → Orchestrator
验证三个模块的端到端集成
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from agent.test_agent_service import get_test_agent_service
from strategy.strategy_service import get_strategy_service
from orchestrator.orchestrator_service import get_orchestrator_service


def test_full_pipeline():
    """完整流程测试"""
    print("\n" + "🔗 " + "="*58)
    print("🔗  完整流程测试: Agent → Strategy → Orchestrator")
    print("🔗 " + "="*58)
    
    # ==================== 阶段1: Test Agent ====================
    print("\n📍 阶段1: Test Agent 分析")
    print("-" * 60)
    
    agent_service = get_test_agent_service()
    
    # 模拟需求和 git diff
    requirement = "新增支付功能，支持微信支付和支付宝支付"
    git_diff = """
    diff --git a/payment/wechat_pay.py b/payment/wechat_pay.py
    new file mode 100644
    index 0000000..1234567
    --- /dev/null
    +++ b/payment/wechat_pay.py
    @@ -0,0 +1,50 @@
    +def process_wechat_payment(order_id, amount):
    +    # 处理微信支付
    +    pass
    """
    
    agent_result = agent_service.analyze(requirement, git_diff)
    
    print(f"✅ Agent 决策:")
    print(f"   - action: {agent_result['action']}")
    print(f"   - priority: {agent_result['priority']}")
    print(f"   - modules: {agent_result['modules']}")
    print(f"   - confidence: {agent_result['confidence']}")
    print(f"   - risk_level: {agent_result['risk_level']}")
    
    # ==================== 阶段2: Strategy Engine ====================
    print("\n📍 阶段2: Strategy Engine 生成策略")
    print("-" * 60)
    
    strategy_service = get_strategy_service()
    strategy_result = strategy_service.generate_strategy(agent_result)
    
    print(f"✅ Strategy 生成:")
    print(f"   - 模块数: {strategy_result['summary']['total_modules']}")
    print(f"   - 预估用例: {strategy_result['summary']['estimated_total_cases']}")
    print(f"   - 风险等级: {strategy_result['summary']['risk_level']}")
    
    for idx, s in enumerate(strategy_result['strategy'], 1):
        print(f"\n   [{idx}] {s['module']['name']}:")
        print(f"       - impact: {s['module']['impact']}")
        print(f"       - test_types: {s['test_types']}")
        print(f"       - case_count: {s['case_count']}")
        print(f"       - execution_hint: parallel={s['execution_hint']['parallel']}, timeout={s['execution_hint']['timeout']}")
    
    # ==================== 阶段3: Orchestrator ====================
    print("\n📍 阶段3: Orchestrator 执行测试")
    print("-" * 60)
    
    orchestrator_service = get_orchestrator_service()
    execution_result = orchestrator_service.run(strategy_result)
    
    print(f"✅ Orchestrator 执行:")
    print(f"   - 总数: {execution_result['summary']['total']}")
    print(f"   - 通过: {execution_result['summary']['passed']}")
    print(f"   - 失败: {execution_result['summary']['failed']}")
    print(f"   - 通过率: {execution_result['summary']['pass_rate']}%")
    print(f"   - 总耗时: {execution_result['summary']['duration']}s")
    
    print("\n   执行详情:")
    for idx, r in enumerate(execution_result['results'], 1):
        status_icon = "✅" if r['status'] == 'passed' else "❌"
        print(f"   {status_icon} [{idx}] {r['module']}: {r['status']} ({r['duration']}s)")
    
    # ==================== 验证完整流程 ====================
    print("\n" + "="*60)
    print("🔍 验证完整流程")
    print("="*60)
    
    # 验证数据流转
    assert agent_result['action'] == 'run_tests', "❌ Agent 应该决定执行测试"
    assert len(strategy_result['strategy']) > 0, "❌ Strategy 应该生成策略"
    assert len(execution_result['results']) > 0, "❌ Orchestrator 应该有执行结果"
    
    # 验证数量一致性
    agent_modules = len(agent_result['modules'])
    strategy_modules = strategy_result['summary']['total_modules']
    execution_modules = execution_result['summary']['total']
    
    assert agent_modules == strategy_modules, \
        f"❌ Agent模块数({agent_modules}) != Strategy模块数({strategy_modules})"
    assert strategy_modules == execution_modules, \
        f"❌ Strategy模块数({strategy_modules}) != Execution模块数({execution_modules})"
    
    print(f"✅ 数据流转正确:")
    print(f"   - Agent识别: {agent_modules}个模块")
    print(f"   - Strategy生成: {strategy_modules}个策略")
    print(f"   - Orchestrator执行: {execution_modules}个测试")
    
    # 验证 V2 字段传递
    assert 'summary' in strategy_result, "❌ Strategy 应该有 summary"
    assert 'summary' in execution_result, "❌ Execution 应该有 summary"
    
    print(f"\n✅ V2 字段传递正确")
    
    print("\n" + "🎉 " + "="*58)
    print("🎉  完整流程测试通过！")
    print("🎉 " + "="*58)
    print("\n流程链路:")
    print("  需求/Diff → Agent决策 → Strategy策略 → Orchestrator执行 → 结果汇总")
    
    return True


if __name__ == "__main__":
    try:
        success = test_full_pipeline()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 流程测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
