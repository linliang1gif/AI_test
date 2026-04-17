"""
Test Intelligence Agent 完整演示
展示如何使用测试智能决策引擎进行测试用例选择和执行计划优化
"""
from modules.agents import TestIntelligenceAgent, TestCase, LearningAgent
from core import ExecutionResult, TestCaseStatus
from datetime import datetime
import json


def create_realistic_test_cases():
    """创建真实场景的测试用例"""
    test_cases = [
        # 支付模块 - 高优先级
        TestCase("test_payment_create_001", "/api/payment/create", "payment", "P0"),
        TestCase("test_payment_create_002", "/api/payment/create_batch", "payment", "P0"),
        TestCase("test_payment_refund_001", "/api/payment/refund", "payment", "P0"),
        TestCase("test_payment_query_001", "/api/payment/query", "payment", "P1"),
        
        # 用户模块 - 中高优先级
        TestCase("test_user_login_001", "/api/user/login", "user", "P0"),
        TestCase("test_user_register_001", "/api/user/register", "user", "P1"),
        TestCase("test_user_profile_001", "/api/user/profile", "user", "P1"),
        TestCase("test_user_update_001", "/api/user/update", "user", "P1"),
        TestCase("test_user_logout_001", "/api/user/logout", "user", "P2"),
        
        # 订单模块 - 中优先级
        TestCase("test_order_create_001", "/api/order/create", "order", "P1"),
        TestCase("test_order_list_001", "/api/order/list", "order", "P2"),
        TestCase("test_order_detail_001", "/api/order/detail", "order", "P2"),
        TestCase("test_order_cancel_001", "/api/order/cancel", "order", "P1"),
        
        # 商品模块 - 中低优先级
        TestCase("test_product_list_001", "/api/product/list", "product", "P2"),
        TestCase("test_product_detail_001", "/api/product/detail", "product", "P2"),
        TestCase("test_product_search_001", "/api/product/search", "product", "P2"),
        TestCase("test_product_category_001", "/api/product/category", "product", "P3"),
        
        # 搜索模块 - 低优先级
        TestCase("test_search_query_001", "/api/search/query", "search", "P3"),
        TestCase("test_search_suggest_001", "/api/search/suggest", "search", "P3"),
        TestCase("test_search_history_001", "/api/search/history", "search", "P3"),
    ]
    return test_cases


def simulate_historical_data(learning_agent: LearningAgent):
    """模拟历史执行数据"""
    print("\n📚 模拟历史执行数据...")
    
    now = datetime.now()
    
    # 模拟一些失败的支付API
    results = [
        ExecutionResult(
            test_case_id="test_payment_create_001",
            status=TestCaseStatus.FAILED,
            duration=2.0,
            start_time=now,
            end_time=now,
            error="Payment gateway timeout"
        ),
        ExecutionResult(
            test_case_id="test_payment_create_001",
            status=TestCaseStatus.FAILED,
            duration=2.1,
            start_time=now,
            end_time=now,
            error="Payment gateway timeout"
        ),
        ExecutionResult(
            test_case_id="test_payment_refund_001",
            status=TestCaseStatus.FAILED,
            duration=1.5,
            start_time=now,
            end_time=now,
            error="Refund service unavailable"
        ),
        # 一些成功的用例
        ExecutionResult(
            test_case_id="test_user_login_001",
            status=TestCaseStatus.PASSED,
            duration=0.5,
            start_time=now,
            end_time=now,
            error=None
        ),
        ExecutionResult(
            test_case_id="test_product_list_001",
            status=TestCaseStatus.PASSED,
            duration=0.8,
            start_time=now,
            end_time=now,
            error=None
        ),
    ]
    
    # 让LearningAgent学习
    learning_agent.learn(results, [])
    print("  ✅ 历史数据学习完成")


def demo_basic_usage():
    """演示基本使用"""
    print("=" * 80)
    print("演示1: 基本使用 - 无历史数据")
    print("=" * 80)
    
    # 创建agent
    agent = TestIntelligenceAgent()
    
    # 创建测试用例
    test_cases = create_realistic_test_cases()
    print(f"\n📋 总测试用例数: {len(test_cases)}")
    
    # 生成执行计划
    plan = agent.optimize_execution_plan(test_cases)
    
    # 显示结果
    print(f"\n📊 执行计划统计:")
    stats = plan['statistics']
    print(f"  ✅ 选中执行: {stats['selected_tests']}个 ({stats['selection_rate']}%)")
    print(f"  ⏭️  跳过执行: {stats['skipped_tests']}个")
    
    print(f"\n📋 决策分布:")
    for decision, count in stats['decision_breakdown'].items():
        print(f"  {decision}: {count}个")
    
    print(f"\n🔀 并发分组 (按模块):")
    for module, test_ids in plan['parallel_groups'].items():
        print(f"  {module}: {len(test_ids)}个用例")
    
    print(f"\n🎯 执行顺序 (前10个):")
    for i, tc_id in enumerate(plan['execution_order'][:10], 1):
        # 找到对应的风险评分
        risk_score = next((rs for rs in plan['risk_scores'] if rs['test_case_id'] == tc_id), None)
        if risk_score:
            print(f"  {i}. {tc_id} (风险: {risk_score['total_score']:.3f})")


def demo_with_learning():
    """演示与LearningAgent集成"""
    print("\n" + "=" * 80)
    print("演示2: 与LearningAgent集成 - 基于历史数据决策")
    print("=" * 80)
    
    # 创建LearningAgent
    learning_agent = LearningAgent(knowledge_dir="demo_knowledge")
    
    # 模拟历史数据
    simulate_historical_data(learning_agent)
    
    # 创建TestIntelligenceAgent并集成LearningAgent
    agent = TestIntelligenceAgent(learning_agent=learning_agent)
    
    # 创建测试用例
    test_cases = create_realistic_test_cases()
    
    # 生成执行计划
    plan = agent.optimize_execution_plan(test_cases)
    
    # 显示结果
    print(f"\n📊 基于历史数据的执行计划:")
    stats = plan['statistics']
    print(f"  ✅ 选中执行: {stats['selected_tests']}个 ({stats['selection_rate']}%)")
    print(f"  ⏭️  跳过执行: {stats['skipped_tests']}个")
    
    # 显示高风险用例
    print(f"\n⚠️  高风险用例 (风险评分 > 0.5):")
    high_risk = [rs for rs in plan['risk_scores'] if rs['total_score'] > 0.5]
    for rs in high_risk[:5]:
        print(f"  - {rs['test_case_id']}: {rs['total_score']:.3f}")
        print(f"    失败率={rs['failure_rate']:.3f}, 优先级={rs['priority_weight']:.3f}")
    
    # 清理
    import shutil
    import os
    if os.path.exists("demo_knowledge"):
        shutil.rmtree("demo_knowledge")


def demo_decision_explanation():
    """演示决策解释"""
    print("\n" + "=" * 80)
    print("演示3: 决策解释")
    print("=" * 80)
    
    agent = TestIntelligenceAgent()
    
    # 选择几个代表性的测试用例
    test_cases = [
        TestCase("test_payment_create", "/api/payment/create", "payment", "P0"),
        TestCase("test_user_profile", "/api/user/profile", "user", "P1"),
        TestCase("test_search_query", "/api/search/query", "search", "P3"),
    ]
    
    for tc in test_cases:
        print(f"\n{'-' * 80}")
        explanation = agent.explain_decision(tc)
        print(explanation)


def demo_save_and_load():
    """演示保存和加载执行计划"""
    print("\n" + "=" * 80)
    print("演示4: 保存和加载执行计划")
    print("=" * 80)
    
    agent = TestIntelligenceAgent()
    test_cases = create_realistic_test_cases()
    
    # 生成执行计划
    plan = agent.optimize_execution_plan(test_cases)
    
    # 保存到文件
    output_path = "execution_plan_demo.json"
    agent.save_execution_plan(plan, output_path)
    print(f"\n💾 执行计划已保存到: {output_path}")
    
    # 加载执行计划
    loaded_plan = agent.load_execution_plan(output_path)
    print(f"\n📂 执行计划已加载")
    print(f"  选中用例: {len(loaded_plan['selected_tests'])}个")
    print(f"  跳过用例: {len(loaded_plan['skipped_tests'])}个")
    
    # 显示JSON内容片段
    print(f"\n📄 执行计划JSON片段:")
    print(json.dumps({
        'selected_tests': loaded_plan['selected_tests'][:3],
        'statistics': loaded_plan['statistics']
    }, indent=2, ensure_ascii=False))


def demo_parallel_execution():
    """演示并发执行策略"""
    print("\n" + "=" * 80)
    print("演示5: 并发执行策略")
    print("=" * 80)
    
    agent = TestIntelligenceAgent()
    test_cases = create_realistic_test_cases()
    
    # 生成执行计划
    plan = agent.optimize_execution_plan(test_cases)
    
    print(f"\n🔀 并发执行分组详情:")
    for module, test_ids in plan['parallel_groups'].items():
        print(f"\n模块: {module}")
        print(f"  用例数: {len(test_ids)}")
        print(f"  可并发执行的用例:")
        for tc_id in test_ids:
            print(f"    - {tc_id}")
    
    print(f"\n💡 并发执行建议:")
    print(f"  - 同一模块的用例可以并发执行")
    print(f"  - 不同模块之间也可以并发执行")
    print(f"  - 建议并发度: {len(plan['parallel_groups'])} (模块数)")


def main():
    """主演示函数"""
    print("\n🚀 Test Intelligence Agent 完整演示")
    print("=" * 80)
    
    try:
        demo_basic_usage()
        demo_with_learning()
        demo_decision_explanation()
        demo_save_and_load()
        demo_parallel_execution()
        
        print("\n" + "=" * 80)
        print("✅ 演示完成!")
        print("=" * 80)
        
        print("\n📚 使用场景:")
        print("  1. CI/CD流水线中自动选择测试用例")
        print("  2. 基于历史数据优化测试执行")
        print("  3. 减少测试执行时间")
        print("  4. 提高测试效率")
        print("  5. 智能跳过低风险用例")
        
    except Exception as e:
        print(f"\n❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
