"""
演示完整三阶段流程
Agent → Strategy → Orchestrator
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from agent.test_agent_service import get_test_agent_service
from strategy.strategy_service import get_strategy_service
from orchestrator.orchestrator_service import get_orchestrator_service
import json


def demo_payment_feature():
    """演示场景1：支付功能开发"""
    print("\n" + "💳 " + "="*58)
    print("💳  演示场景1：支付功能开发")
    print("💳 " + "="*58)
    
    # 输入
    requirement = """
    需求：新增支付功能
    - 支持微信支付
    - 支持支付宝支付
    - 支持退款功能
    - 需要支付回调处理
    """
    
    git_diff = """
    diff --git a/payment/wechat_pay.py b/payment/wechat_pay.py
    new file mode 100644
    +++ b/payment/wechat_pay.py
    @@ -0,0 +1,80 @@
    +class WechatPayment:
    +    def process_payment(self, order_id, amount):
    +        # 处理微信支付
    +    def handle_callback(self, data):
    +        # 处理支付回调
    """
    
    print("\n📄 输入:")
    print(f"  需求: {requirement.strip()[:50]}...")
    print(f"  Diff: 新增支付模块，约80行代码")
    
    # 阶段1: Agent
    print("\n" + "─"*60)
    print("🤖 阶段1: Test Agent 决策")
    print("─"*60)
    
    agent_service = get_test_agent_service()
    agent_result = agent_service.analyze(requirement, git_diff)
    
    print(f"✅ 决策结果:")
    print(f"   action: {agent_result['action']}")
    print(f"   priority: {agent_result['priority']}")
    print(f"   modules: {agent_result['modules']}")
    print(f"   risk_level: {agent_result['risk_level']}")
    print(f"   confidence: {agent_result['confidence']}")
    
    # 阶段2: Strategy
    print("\n" + "─"*60)
    print("📋 阶段2: Strategy Engine 生成策略")
    print("─"*60)
    
    strategy_service = get_strategy_service()
    strategy_result = strategy_service.generate_strategy(agent_result)
    
    print(f"✅ 策略生成:")
    print(f"   模块数: {strategy_result['summary']['total_modules']}")
    print(f"   预估用例: {strategy_result['summary']['estimated_total_cases']}")
    print(f"   风险等级: {strategy_result['summary']['risk_level']}")
    
    for s in strategy_result['strategy']:
        print(f"\n   📦 {s['module']['name']}:")
        print(f"      - impact: {s['module']['impact']}")
        print(f"      - test_types: {', '.join(s['test_types'])}")
        print(f"      - case_count: {s['case_count']}")
        print(f"      - parallel: {s['execution_hint']['parallel']}")
    
    # 阶段3: Orchestrator
    print("\n" + "─"*60)
    print("⚡ 阶段3: Orchestrator 执行测试")
    print("─"*60)
    
    orchestrator_service = get_orchestrator_service()
    execution_result = orchestrator_service.run(strategy_result)
    
    print(f"✅ 执行完成:")
    print(f"   总数: {execution_result['summary']['total']}")
    print(f"   通过: {execution_result['summary']['passed']}")
    print(f"   失败: {execution_result['summary']['failed']}")
    print(f"   通过率: {execution_result['summary']['pass_rate']}%")
    print(f"   总耗时: {execution_result['summary']['duration']}s")
    
    print(f"\n   详细结果:")
    for r in execution_result['results']:
        status_icon = "✅" if r['status'] == 'passed' else "❌"
        print(f"   {status_icon} {r['module']}: {r['status']} ({r['duration']}s)")
    
    return True


def demo_readme_update():
    """演示场景2：README 更新（应跳过测试）"""
    print("\n" + "📝 " + "="*58)
    print("📝  演示场景2：README 更新")
    print("📝 " + "="*58)
    
    requirement = "更新 README 文档，添加安装说明"
    git_diff = """
    diff --git a/README.md b/README.md
    @@ -10,0 +11,5 @@
    +## 安装
    +pip install -r requirements.txt
    """
    
    print("\n📄 输入:")
    print(f"  需求: {requirement}")
    print(f"  Diff: 修改 README.md")
    
    # 阶段1: Agent
    print("\n" + "─"*60)
    print("🤖 阶段1: Test Agent 决策")
    print("─"*60)
    
    agent_service = get_test_agent_service()
    agent_result = agent_service.analyze(requirement, git_diff)
    
    print(f"✅ 决策结果:")
    print(f"   action: {agent_result['action']}")
    print(f"   reason: {agent_result['reason']}")
    
    if agent_result['action'] == 'skip':
        print(f"\n⏭️  决策为跳过，流程结束")
        return True
    
    # 如果需要测试，继续后续流程
    strategy_service = get_strategy_service()
    strategy_result = strategy_service.generate_strategy(agent_result)
    
    orchestrator_service = get_orchestrator_service()
    execution_result = orchestrator_service.run(strategy_result)
    
    print(f"✅ 执行完成: {execution_result['summary']['total']} 个测试")
    
    return True


def demo_multi_module():
    """演示场景3：多模块开发"""
    print("\n" + "🏗️  " + "="*58)
    print("🏗️  演示场景3：多模块开发")
    print("🏗️  " + "="*58)
    
    requirement = """
    需求：用户系统重构
    - 用户注册功能
    - 用户登录功能
    - 权限管理功能
    - 用户资料管理
    """
    
    git_diff = """
    diff --git a/user/register.py b/user/register.py
    +++ 新增 150 行
    diff --git a/user/login.py b/user/login.py
    +++ 新增 120 行
    diff --git a/user/permission.py b/user/permission.py
    +++ 新增 200 行
    """
    
    print("\n📄 输入:")
    print(f"  需求: 用户系统重构（4个子功能）")
    print(f"  Diff: 3个文件，约470行代码")
    
    # 完整流程
    agent_service = get_test_agent_service()
    strategy_service = get_strategy_service()
    orchestrator_service = get_orchestrator_service()
    
    # 阶段1
    print("\n" + "─"*60)
    print("🤖 阶段1: Test Agent 决策")
    agent_result = agent_service.analyze(requirement, git_diff)
    print(f"✅ 识别 {len(agent_result['modules'])} 个模块，优先级 {agent_result['priority']}")
    
    # 阶段2
    print("\n" + "─"*60)
    print("📋 阶段2: Strategy Engine 生成策略")
    strategy_result = strategy_service.generate_strategy(agent_result)
    print(f"✅ 生成 {strategy_result['summary']['total_modules']} 个策略，预估 {strategy_result['summary']['estimated_total_cases']} 个用例")
    
    # 阶段3
    print("\n" + "─"*60)
    print("⚡ 阶段3: Orchestrator 执行测试")
    execution_result = orchestrator_service.run(strategy_result)
    
    print(f"✅ 执行完成:")
    print(f"   - 通过率: {execution_result['summary']['pass_rate']}%")
    print(f"   - 总耗时: {execution_result['summary']['duration']}s")
    
    # 显示详细结果
    print(f"\n   模块执行结果:")
    for idx, r in enumerate(execution_result['results'], 1):
        status_icon = "✅" if r['status'] == 'passed' else "❌"
        print(f"   {status_icon} [{idx}] {r['module']}: {r['status']} ({r['duration']}s)")
    
    return True


def main():
    """运行所有演示"""
    print("\n" + "🎬 " + "="*58)
    print("🎬  AI 测试决策系统 - 完整流程演示")
    print("🎬 " + "="*58)
    print("\n系统架构:")
    print("  Test Agent (AI决策) → Strategy Engine (策略生成) → Orchestrator (执行调度)")
    
    demos = [
        ("支付功能开发", demo_payment_feature),
        ("README 更新", demo_readme_update),
        ("多模块开发", demo_multi_module)
    ]
    
    for name, demo_func in demos:
        try:
            demo_func()
        except Exception as e:
            print(f"\n❌ 演示失败: {name}")
            print(f"   错误: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "🎉 " + "="*58)
    print("🎉  演示完成！")
    print("🎉 " + "="*58)
    print("\n核心价值:")
    print("  ✨ AI 自动决策是否需要测试")
    print("  ✨ 自动生成测试策略")
    print("  ✨ 自动调度并执行测试")
    print("  ✨ 支持并发执行，提升效率")
    print("  ✨ 完整的结果汇总和统计")


if __name__ == "__main__":
    main()
