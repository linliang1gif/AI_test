"""
Test Discovery Agent 演示
展示如何自动发现高风险测试点
"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.discovery import TestDiscoveryAgent, RiskLevel


def demo_swagger_changes():
    """演示1: 从Swagger变更发现测试点"""
    print("=" * 80)
    print("演示1: 从Swagger变更发现测试点")
    print("=" * 80)
    
    # 初始化发现代理
    agent = TestDiscoveryAgent()
    
    # Swagger文件路径
    old_swagger = Path(__file__).parent / "old_swagger.json"
    new_swagger = Path(__file__).parent / "new_swagger.json"
    
    print(f"\n📄 对比Swagger文件:")
    print(f"  旧版本: {old_swagger.name}")
    print(f"  新版本: {new_swagger.name}")
    
    # 发现测试点
    print("\n🔍 开始发现测试点...")
    test_points = agent.discover_from_swagger_changes(
        str(old_swagger),
        str(new_swagger)
    )
    
    print(f"\n✅ 发现了 {len(test_points)} 个测试点\n")
    
    # 显示测试点
    for i, tp in enumerate(test_points, 1):
        print(f"📌 测试点 {i}:")
        print(f"  描述: {tp.test_point}")
        print(f"  原因: {tp.reason}")
        print(f"  风险等级: {tp.risk_level}")
        print(f"  测试类型: {tp.suggested_test_type}")
        print(f"  优先级: {tp.priority}")
        if tp.api_path:
            print(f"  API路径: {tp.api_path}")
        if tp.changed_fields:
            print(f"  变更字段: {', '.join(tp.changed_fields)}")
        if tp.suggested_scenarios:
            print(f"  建议场景:")
            for scenario in tp.suggested_scenarios:
                print(f"    - {scenario}")
        print()
    
    return test_points


def demo_risk_filtering(test_points):
    """演示2: 按风险等级过滤"""
    print("\n" + "=" * 80)
    print("演示2: 按风险等级过滤")
    print("=" * 80)
    
    agent = TestDiscoveryAgent()
    agent.discovered_points = test_points
    
    # 只获取高风险和严重风险的测试点
    critical_points = agent.filter_by_risk(RiskLevel.HIGH)
    
    print(f"\n🔴 高风险及以上测试点: {len(critical_points)} 个\n")
    
    for tp in critical_points:
        print(f"  [{tp.risk_level.upper()}] {tp.test_point}")


def demo_statistics(test_points):
    """演示3: 统计信息"""
    print("\n" + "=" * 80)
    print("演示3: 统计信息")
    print("=" * 80)
    
    agent = TestDiscoveryAgent()
    agent.discovered_points = test_points
    
    stats = agent.get_statistics()
    
    print(f"\n📊 统计信息:")
    print(f"  总测试点数: {stats['total']}")
    
    print(f"\n  按风险等级:")
    for risk, count in stats['by_risk_level'].items():
        print(f"    {risk}: {count}")
    
    print(f"\n  按测试类型:")
    for test_type, count in stats['by_test_type'].items():
        print(f"    {test_type}: {count}")
    
    print(f"\n  按优先级:")
    for priority, count in stats['by_priority'].items():
        print(f"    {priority}: {count}")


def demo_export_json(test_points):
    """演示4: 导出为JSON"""
    print("\n" + "=" * 80)
    print("演示4: 导出为JSON")
    print("=" * 80)
    
    agent = TestDiscoveryAgent()
    agent.discovered_points = test_points
    
    # 导出为JSON
    json_data = agent.export_to_json()
    
    print(f"\n📄 JSON格式（前2个测试点）:")
    print(json.dumps(json_data[:2], ensure_ascii=False, indent=2))
    
    # 保存到文件
    output_file = Path(__file__).parent.parent / "output" / "discovered_test_points.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 已保存到: {output_file}")


def demo_git_diff():
    """演示5: 从Git Diff发现测试点"""
    print("\n" + "=" * 80)
    print("演示5: 从Git Diff发现测试点")
    print("=" * 80)
    
    # 模拟Git Diff
    diff_content = """
diff --git a/src/payment/service.py b/src/payment/service.py
index 1234567..abcdefg 100644
--- a/src/payment/service.py
+++ b/src/payment/service.py
@@ -10,6 +10,10 @@ def process_payment(order_id, amount):
     if amount <= 0:
         raise ValueError("Invalid amount")
     
+    # 新增：金额上限检查
+    if amount > 100000:
+        raise ValueError("Amount exceeds limit")
+    
     # 处理支付
     return payment_gateway.charge(order_id, amount)
"""
    
    agent = TestDiscoveryAgent()
    
    print("\n📝 Git Diff内容:")
    print(diff_content)
    
    print("\n🔍 开始分析代码变更...")
    test_points = agent.discover_from_git_diff(diff_content)
    
    print(f"\n✅ 发现了 {len(test_points)} 个测试点\n")
    
    for tp in test_points:
        print(f"📌 {tp.test_point}")
        print(f"   原因: {tp.reason}")
        print(f"   风险: {tp.risk_level}")
        print()


def demo_failure_logs():
    """演示6: 从失败日志发现测试点"""
    print("\n" + "=" * 80)
    print("演示6: 从失败日志发现测试点")
    print("=" * 80)
    
    # 模拟失败日志
    log_content = """
[2024-03-23 10:15:32] ERROR: POST /api/orders - 500 Internal Server Error
[2024-03-23 10:16:45] FAILED: GET /api/users/123 - Timeout after 30s
[2024-03-23 10:17:12] ERROR: PUT /api/payments/456 - Invalid amount: -100
"""
    
    agent = TestDiscoveryAgent()
    
    print("\n📋 失败日志:")
    print(log_content)
    
    print("\n🔍 开始分析失败日志...")
    test_points = agent.discover_from_failure_logs(log_content)
    
    print(f"\n✅ 发现了 {len(test_points)} 个测试点\n")
    
    for tp in test_points:
        print(f"📌 {tp.test_point}")
        print(f"   原因: {tp.reason}")
        print(f"   API: {tp.api_path}")
        print()


def demo_integration_with_swagger_generator():
    """演示7: 与Swagger生成器集成"""
    print("\n" + "=" * 80)
    print("演示7: 与Swagger生成器集成")
    print("=" * 80)
    
    from modules.swagger import SwaggerTestCaseGenerator
    
    # 1. 发现测试点
    agent = TestDiscoveryAgent()
    old_swagger = Path(__file__).parent / "old_swagger.json"
    new_swagger = Path(__file__).parent / "new_swagger.json"
    
    test_points = agent.discover_from_swagger_changes(
        str(old_swagger),
        str(new_swagger)
    )
    
    print(f"\n🔍 发现了 {len(test_points)} 个测试点")
    
    # 2. 为高风险API生成测试用例
    print("\n🚀 为高风险API生成测试用例...")
    
    generator = SwaggerTestCaseGenerator(str(new_swagger))
    
    # 找到支付API（新增的高风险API）
    payment_api = None
    for api in generator.loader.get_all_apis():
        if '/payments' in api['path']:
            payment_api = api
            break
    
    if payment_api:
        test_cases = generator.generate_testcases_for_api(payment_api)
        
        print(f"\n✅ 为 {payment_api['path']} 生成了 {len(test_cases)} 个测试用例:")
        for tc in test_cases:
            print(f"  - {tc.id}: {tc.title}")
    
    print("\n💡 完整流程:")
    print("  1. Test Discovery Agent 发现高风险测试点")
    print("  2. Swagger Generator 生成详细测试用例")
    print("  3. Execution Engine 执行测试用例")
    print("  4. Self-Healing 自动修复失败")


if __name__ == "__main__":
    print("\n🎉 Test Discovery Agent 演示\n")
    
    # 演示1: Swagger变更
    test_points = demo_swagger_changes()
    
    # 演示2: 风险过滤
    demo_risk_filtering(test_points)
    
    # 演示3: 统计信息
    demo_statistics(test_points)
    
    # 演示4: 导出JSON
    demo_export_json(test_points)
    
    # 演示5: Git Diff
    demo_git_diff()
    
    # 演示6: 失败日志
    demo_failure_logs()
    
    # 演示7: 集成
    demo_integration_with_swagger_generator()
    
    print("\n" + "=" * 80)
    print("✅ 所有演示完成！")
    print("=" * 80)
    print("\n💡 下一步:")
    print("  1. 查看发现的测试点: output/discovered_test_points.json")
    print("  2. 使用Swagger Generator生成测试用例")
    print("  3. 使用Execution Engine执行测试")
    print()
