"""
测试Test Intelligence Agent
"""
from modules.agents.test_intelligence_agent import (
    TestIntelligenceAgent, TestCase, ExecutionDecision
)
from modules.agents.learning_agent import LearningAgent
import json


def create_test_cases():
    """创建测试用例"""
    test_cases = [
        # 高风险用例 (P0, 高失败率)
        TestCase(
            test_case_id="test_payment_001",
            api="/api/payment/create",
            module="payment",
            priority="P0"
        ),
        TestCase(
            test_case_id="test_payment_002",
            api="/api/payment/refund",
            module="payment",
            priority="P0"
        ),
        # 中风险用例 (P1)
        TestCase(
            test_case_id="test_user_001",
            api="/api/user/login",
            module="user",
            priority="P1"
        ),
        TestCase(
            test_case_id="test_user_002",
            api="/api/user/register",
            module="user",
            priority="P1"
        ),
        TestCase(
            test_case_id="test_user_003",
            api="/api/user/profile",
            module="user",
            priority="P1"
        ),
        # 低风险用例 (P2, P3)
        TestCase(
            test_case_id="test_product_001",
            api="/api/product/list",
            module="product",
            priority="P2"
        ),
        TestCase(
            test_case_id="test_product_002",
            api="/api/product/detail",
            module="product",
            priority="P2"
        ),
        TestCase(
            test_case_id="test_order_001",
            api="/api/order/list",
            module="order",
            priority="P3"
        ),
        TestCase(
            test_case_id="test_order_002",
            api="/api/order/detail",
            module="order",
            priority="P3"
        ),
        TestCase(
            test_case_id="test_search_001",
            api="/api/search/query",
            module="search",
            priority="P3"
        )
    ]
    return test_cases


def test_select_tests():
    """测试用例选择"""
    print("=" * 80)
    print("测试用例选择")
    print("=" * 80)
    
    # 创建agent
    agent = TestIntelligenceAgent()
    
    # 创建测试用例
    test_cases = create_test_cases()
    print(f"\n总测试用例数: {len(test_cases)}")
    
    # 选择测试用例
    result = agent.select_tests(test_cases)
    
    print(f"\n✅ 选中执行: {len(result['selected_tests'])}个")
    for tc_id in result['selected_tests'][:5]:
        print(f"  - {tc_id}")
    
    print(f"\n⏭️  跳过执行: {len(result['skipped_tests'])}个")
    for tc_id in result['skipped_tests'][:5]:
        print(f"  - {tc_id}")
    
    print(f"\n📊 优先级顺序 (前5个):")
    for i, tc_id in enumerate(result['priority_order'][:5], 1):
        print(f"  {i}. {tc_id}")
    
    print("\n✅ 用例选择测试通过")


def test_calculate_risk_score():
    """测试风险评分"""
    print("\n" + "=" * 80)
    print("测试风险评分")
    print("=" * 80)
    
    agent = TestIntelligenceAgent()
    
    # 测试不同优先级的用例
    test_cases = [
        TestCase("test_p0", "/api/test", "test", "P0"),
        TestCase("test_p1", "/api/test", "test", "P1"),
        TestCase("test_p2", "/api/test", "test", "P2"),
        TestCase("test_p3", "/api/test", "test", "P3"),
    ]
    
    print("\n风险评分结果:")
    for tc in test_cases:
        risk_score = agent.calculate_risk_score(tc)
        print(f"\n{tc.test_case_id} ({tc.priority}):")
        print(f"  总分: {risk_score.total_score:.3f}")
        print(f"  决策: {risk_score.decision.value}")
        print(f"  明细: 失败率={risk_score.failure_rate:.3f}, "
              f"变更频率={risk_score.change_frequency:.3f}, "
              f"优先级={risk_score.priority_weight:.3f}, "
              f"覆盖缺口={risk_score.coverage_gap:.3f}")
    
    print("\n✅ 风险评分测试通过")


def test_optimize_execution_plan():
    """测试执行计划优化"""
    print("\n" + "=" * 80)
    print("测试执行计划优化")
    print("=" * 80)
    
    agent = TestIntelligenceAgent()
    test_cases = create_test_cases()
    
    # 生成执行计划
    plan = agent.optimize_execution_plan(test_cases)
    
    print(f"\n📊 执行统计:")
    stats = plan['statistics']
    print(f"  总用例数: {stats['total_tests']}")
    print(f"  选中执行: {stats['selected_tests']}")
    print(f"  跳过执行: {stats['skipped_tests']}")
    print(f"  选择率: {stats['selection_rate']}%")
    
    print(f"\n📋 决策分布:")
    for decision, count in stats['decision_breakdown'].items():
        print(f"  {decision}: {count}个")
    
    print(f"\n🔀 并发分组:")
    for module, test_ids in plan['parallel_groups'].items():
        print(f"  {module}: {len(test_ids)}个用例")
        for tc_id in test_ids[:3]:
            print(f"    - {tc_id}")
    
    # 保存执行计划
    output_path = "execution_plan_example.json"
    agent.save_execution_plan(plan, output_path)
    print(f"\n💾 执行计划已保存到: {output_path}")
    
    print("\n✅ 执行计划优化测试通过")


def test_explain_decision():
    """测试决策解释"""
    print("\n" + "=" * 80)
    print("测试决策解释")
    print("=" * 80)
    
    agent = TestIntelligenceAgent()
    
    # 测试不同优先级的决策解释
    test_cases = [
        TestCase("test_high_priority", "/api/payment", "payment", "P0"),
        TestCase("test_low_priority", "/api/search", "search", "P3"),
    ]
    
    for tc in test_cases:
        print(f"\n{'-' * 80}")
        explanation = agent.explain_decision(tc)
        print(explanation)
    
    print("\n✅ 决策解释测试通过")


def test_with_learning_agent():
    """测试与LearningAgent集成"""
    print("\n" + "=" * 80)
    print("测试与LearningAgent集成")
    print("=" * 80)
    
    # 创建LearningAgent
    learning_agent = LearningAgent(knowledge_dir="test_knowledge_temp")
    
    # 创建TestIntelligenceAgent并集成LearningAgent
    agent = TestIntelligenceAgent(learning_agent=learning_agent)
    
    test_cases = create_test_cases()
    
    # 生成执行计划
    plan = agent.optimize_execution_plan(test_cases)
    
    print(f"\n📊 集成LearningAgent后的执行计划:")
    print(f"  选中执行: {len(plan['selected_tests'])}个")
    print(f"  跳过执行: {len(plan['skipped_tests'])}个")
    
    # 显示风险评分
    print(f"\n🎯 风险评分 (前5个):")
    for risk_score in plan['risk_scores'][:5]:
        print(f"  {risk_score['test_case_id']}: "
              f"总分={risk_score['total_score']:.3f}, "
              f"决策={risk_score['decision']}")
    
    # 清理测试数据
    import shutil
    import os
    if os.path.exists("test_knowledge_temp"):
        shutil.rmtree("test_knowledge_temp")
    
    print("\n✅ LearningAgent集成测试通过")


def main():
    """主测试函数"""
    print("\n🚀 Test Intelligence Agent 测试")
    print("=" * 80)
    
    try:
        test_select_tests()
        test_calculate_risk_score()
        test_optimize_execution_plan()
        test_explain_decision()
        test_with_learning_agent()
        
        print("\n" + "=" * 80)
        print("✅ 所有测试通过!")
        print("=" * 80)
        
        # 显示生成的执行计划示例
        print("\n📄 查看生成的执行计划: execution_plan_example.json")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
