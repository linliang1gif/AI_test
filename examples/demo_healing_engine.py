"""
HealingEngine演示脚本
展示Self-Healing的四层修复策略
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.healing import HealingEngine, HealingLevel
from modules.executor.execution_engine import ExecutionResult


def demo_l1_retry():
    """演示1: L1修复 - 环境问题（重试）"""
    print("=" * 80)
    print("演示1: L1修复 - 环境问题（重试）")
    print("=" * 80)
    
    # 模拟环境问题的失败用例
    results = [
        ExecutionResult("TC_001", "failed", 0.5, "Connection timeout"),
        ExecutionResult("TC_002", "failed", 0.3, "Network error: connection refused"),
        ExecutionResult("TC_003", "error", 0.2, "Socket error: connection reset"),
        ExecutionResult("TC_004", "failed", 1.0, "503 Service Unavailable"),
    ]
    
    # 应用修复
    engine = HealingEngine()
    healed_results = engine.heal(results)
    
    print("\n修复结果:")
    for r in healed_results:
        if hasattr(r, 'healing_info'):
            print(f"  {r.test_case_id}:")
            print(f"    级别: {r.healing_info['level']}")
            print(f"    原因: {r.healing_info['reason']}")
            print(f"    建议: {r.healing_info['suggestion']}")
    
    print("\n✅ 演示完成\n")


def demo_l2_data():
    """演示2: L2修复 - 数据问题（重建数据）"""
    print("=" * 80)
    print("演示2: L2修复 - 数据问题（重建数据）")
    print("=" * 80)
    
    # 模拟数据问题的失败用例
    results = [
        ExecutionResult("TC_001", "failed", 0.5, "Invalid data format"),
        ExecutionResult("TC_002", "failed", 0.3, "Null pointer exception"),
        ExecutionResult("TC_003", "failed", 0.4, "Missing required field: email"),
        ExecutionResult("TC_004", "failed", 0.6, "400 Bad Request: validation error"),
    ]
    
    # 应用修复
    engine = HealingEngine()
    healed_results = engine.heal(results)
    
    print("\n修复结果:")
    for r in healed_results:
        if hasattr(r, 'healing_info'):
            print(f"  {r.test_case_id}:")
            print(f"    级别: {r.healing_info['level']}")
            print(f"    原因: {r.healing_info['reason']}")
            print(f"    建议: {r.healing_info['suggestion']}")
    
    print("\n✅ 演示完成\n")


def demo_l3_flaky():
    """演示3: L3修复 - 不稳定（容错）"""
    print("=" * 80)
    print("演示3: L3修复 - 不稳定（容错）")
    print("=" * 80)
    
    # 模拟不稳定的失败用例
    results = [
        ExecutionResult("TC_001", "failed", 0.5, "Flaky test: sometimes passes"),
        ExecutionResult("TC_002", "failed", 0.3, "Intermittent failure detected"),
        ExecutionResult("TC_003", "failed", 0.4, "Race condition in async operation"),
    ]
    
    # 应用修复
    engine = HealingEngine()
    healed_results = engine.heal(results)
    
    print("\n修复结果:")
    for r in healed_results:
        if hasattr(r, 'healing_info'):
            print(f"  {r.test_case_id}:")
            print(f"    原状态: {r.healing_info['original_status']}")
            print(f"    新状态: {r.status}")
            print(f"    级别: {r.healing_info['level']}")
            print(f"    原因: {r.healing_info['reason']}")
            print(f"    建议: {r.healing_info['suggestion']}")
    
    print("\n✅ 演示完成\n")


def demo_l4_manual():
    """演示4: L4修复 - 断言失败（人工审查）"""
    print("=" * 80)
    print("演示4: L4修复 - 断言失败（人工审查）")
    print("=" * 80)
    
    # 模拟断言失败的用例
    results = [
        ExecutionResult("TC_001", "failed", 0.5, "Assertion failed: status_code expected 200, got 404"),
        ExecutionResult("TC_002", "failed", 0.3, "JSON path data.id not found"),
        ExecutionResult("TC_003", "failed", 0.4, "Response mismatch: expected 'success', got 'error'"),
    ]
    
    # 应用修复
    engine = HealingEngine()
    healed_results = engine.heal(results)
    
    print("\n修复结果:")
    for r in healed_results:
        if hasattr(r, 'healing_info'):
            print(f"  {r.test_case_id}:")
            print(f"    级别: {r.healing_info['level']}")
            print(f"    原因: {r.healing_info['reason']}")
            print(f"    建议: {r.healing_info['suggestion']}")
    
    # 获取需要人工审查的用例
    manual_cases = engine.get_manual_review_cases(healed_results)
    print(f"\n需要人工审查的用例: {len(manual_cases)}个")
    
    print("\n✅ 演示完成\n")


def demo_mixed_errors():
    """演示5: 混合错误场景"""
    print("=" * 80)
    print("演示5: 混合错误场景")
    print("=" * 80)
    
    # 模拟各种类型的失败用例
    results = [
        ExecutionResult("TC_001", "passed", 0.5, None),
        ExecutionResult("TC_002", "failed", 0.3, "Connection timeout"),  # L1
        ExecutionResult("TC_003", "failed", 0.4, "Invalid data format"),  # L2
        ExecutionResult("TC_004", "failed", 0.5, "Flaky test"),  # L3
        ExecutionResult("TC_005", "failed", 0.6, "Assertion failed: expected 200, got 404"),  # L4
        ExecutionResult("TC_006", "passed", 0.7, None),
        ExecutionResult("TC_007", "error", 0.2, "Network error"),  # L1
        ExecutionResult("TC_008", "failed", 0.4, "Missing required field"),  # L2
    ]
    
    # 应用修复
    engine = HealingEngine()
    healed_results = engine.heal(results)
    
    # 获取修复报告
    report = engine.get_healing_report()
    
    print("\n修复报告:")
    print(f"  总用例数: {report['total_cases']}")
    print(f"  修复用例数: {report['healed_cases']}")
    print(f"  修复率: {report['healing_rate']}")
    
    print("\n  按级别统计:")
    for level, info in report['by_level'].items():
        if info['count'] > 0:
            print(f"    {level}: {info['count']}个 - {info['description']}")
    
    # 获取需要重试的用例
    retry_cases = engine.get_retry_cases(healed_results)
    print(f"\n  需要重试的用例: {len(retry_cases)}个")
    for r in retry_cases:
        print(f"    - {r.test_case_id}: {r.healing_info['reason']}")
    
    # 获取需要人工审查的用例
    manual_cases = engine.get_manual_review_cases(healed_results)
    print(f"\n  需要人工审查的用例: {len(manual_cases)}个")
    for r in manual_cases:
        print(f"    - {r.test_case_id}: {r.error_message}")
    
    print("\n✅ 演示完成\n")


def demo_custom_config():
    """演示6: 自定义配置"""
    print("=" * 80)
    print("演示6: 自定义配置")
    print("=" * 80)
    
    results = [
        ExecutionResult("TC_001", "failed", 0.3, "Connection timeout"),
        ExecutionResult("TC_002", "failed", 0.4, "Invalid data"),
        ExecutionResult("TC_003", "failed", 0.5, "Flaky test"),
    ]
    
    # 只启用L1和L2修复
    config = {
        'enable_l1': True,
        'enable_l2': True,
        'enable_l3': False,  # 禁用L3
        'enable_l4': False,  # 禁用L4
        'max_retry': 5
    }
    
    engine = HealingEngine(config)
    healed_results = engine.heal(results)
    
    print("\n配置:")
    print(f"  L1修复: {'启用' if config['enable_l1'] else '禁用'}")
    print(f"  L2修复: {'启用' if config['enable_l2'] else '禁用'}")
    print(f"  L3修复: {'启用' if config['enable_l3'] else '禁用'}")
    print(f"  L4修复: {'启用' if config['enable_l4'] else '禁用'}")
    print(f"  最大重试: {config['max_retry']}次")
    
    print("\n修复结果:")
    for r in healed_results:
        if hasattr(r, 'healing_info'):
            print(f"  {r.test_case_id}: {r.healing_info['level']}")
        else:
            print(f"  {r.test_case_id}: 未修复（L3/L4已禁用）")
    
    print("\n✅ 演示完成\n")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("HealingEngine 完整演示")
    print("=" * 80 + "\n")
    
    demo_l1_retry()
    demo_l2_data()
    demo_l3_flaky()
    demo_l4_manual()
    demo_mixed_errors()
    demo_custom_config()
    
    print("=" * 80)
    print("🎉 所有演示完成！")
    print("=" * 80)
