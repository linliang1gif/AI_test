"""
HealingEngine验证脚本
验证Self-Healing引擎的功能
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from modules.healing import HealingEngine, HealingLevel
from modules.executor.execution_engine import ExecutionResult


def verify_l1_detection():
    """验证1: L1错误检测"""
    print("=" * 80)
    print("验证1: L1错误检测（环境问题）")
    print("=" * 80)
    
    results = [
        ExecutionResult("TC_001", "failed", 0.5, "Connection timeout"),
        ExecutionResult("TC_002", "failed", 0.3, "Network error"),
        ExecutionResult("TC_003", "error", 0.2, "503 Service Unavailable"),
    ]
    
    engine = HealingEngine()
    healed_results = engine.heal(results)
    
    # 验证所有用例都被识别为L1
    for r in healed_results:
        assert hasattr(r, 'healing_info'), f"{r.test_case_id} 应有healing_info"
        assert r.healing_info['level'] == HealingLevel.L1_RETRY.value, \
            f"{r.test_case_id} 应被识别为L1"
        assert r.healing_info['action'] == 'retry', \
            f"{r.test_case_id} 的action应为retry"
    
    print("✅ L1错误检测正常")
    print(f"   检测到 {len(healed_results)} 个L1错误")
    print()
    
    return True


def verify_l2_detection():
    """验证2: L2错误检测"""
    print("=" * 80)
    print("验证2: L2错误检测（数据问题）")
    print("=" * 80)
    
    results = [
        ExecutionResult("TC_001", "failed", 0.5, "Invalid data format"),
        ExecutionResult("TC_002", "failed", 0.3, "Null pointer exception"),
        ExecutionResult("TC_003", "failed", 0.4, "400 Bad Request"),
    ]
    
    engine = HealingEngine()
    healed_results = engine.heal(results)
    
    # 验证所有用例都被识别为L2
    for r in healed_results:
        assert hasattr(r, 'healing_info'), f"{r.test_case_id} 应有healing_info"
        assert r.healing_info['level'] == HealingLevel.L2_DATA.value, \
            f"{r.test_case_id} 应被识别为L2"
        assert r.healing_info['action'] == 'regenerate_data', \
            f"{r.test_case_id} 的action应为regenerate_data"
    
    print("✅ L2错误检测正常")
    print(f"   检测到 {len(healed_results)} 个L2错误")
    print()
    
    return True


def verify_l3_detection():
    """验证3: L3错误检测"""
    print("=" * 80)
    print("验证3: L3错误检测（不稳定）")
    print("=" * 80)
    
    results = [
        ExecutionResult("TC_001", "failed", 0.5, "Flaky test"),
        ExecutionResult("TC_002", "failed", 0.3, "Intermittent failure"),
        ExecutionResult("TC_003", "failed", 0.4, "Race condition"),
    ]
    
    engine = HealingEngine()
    healed_results = engine.heal(results)
    
    # 验证所有用例都被识别为L3
    for r in healed_results:
        assert hasattr(r, 'healing_info'), f"{r.test_case_id} 应有healing_info"
        assert r.healing_info['level'] == HealingLevel.L3_FLAKY.value, \
            f"{r.test_case_id} 应被识别为L3"
        assert r.healing_info['action'] == 'tolerate', \
            f"{r.test_case_id} 的action应为tolerate"
        assert r.status == 'passed_with_warning', \
            f"{r.test_case_id} 的状态应为passed_with_warning"
    
    print("✅ L3错误检测正常")
    print(f"   检测到 {len(healed_results)} 个L3错误")
    print(f"   状态已改为: passed_with_warning")
    print()
    
    return True


def verify_l4_detection():
    """验证4: L4错误检测"""
    print("=" * 80)
    print("验证4: L4错误检测（断言失败）")
    print("=" * 80)
    
    results = [
        ExecutionResult("TC_001", "failed", 0.5, "Assertion failed: expected 200, got 404"),
        ExecutionResult("TC_002", "failed", 0.3, "JSON path not found"),
        ExecutionResult("TC_003", "failed", 0.4, "Response mismatch"),
    ]
    
    engine = HealingEngine()
    healed_results = engine.heal(results)
    
    # 验证所有用例都被识别为L4
    for r in healed_results:
        assert hasattr(r, 'healing_info'), f"{r.test_case_id} 应有healing_info"
        assert r.healing_info['level'] == HealingLevel.L4_MANUAL.value, \
            f"{r.test_case_id} 应被识别为L4"
        assert r.healing_info['action'] == 'manual_review', \
            f"{r.test_case_id} 的action应为manual_review"
    
    print("✅ L4错误检测正常")
    print(f"   检测到 {len(healed_results)} 个L4错误")
    print()
    
    return True


def verify_healing_report():
    """验证5: 修复报告"""
    print("=" * 80)
    print("验证5: 修复报告")
    print("=" * 80)
    
    results = [
        ExecutionResult("TC_001", "passed", 0.5, None),
        ExecutionResult("TC_002", "failed", 0.3, "Connection timeout"),  # L1
        ExecutionResult("TC_003", "failed", 0.4, "Invalid data"),  # L2
        ExecutionResult("TC_004", "failed", 0.5, "Flaky test"),  # L3
        ExecutionResult("TC_005", "failed", 0.6, "Assertion failed"),  # L4
    ]
    
    engine = HealingEngine()
    healed_results = engine.heal(results)
    report = engine.get_healing_report()
    
    # 验证报告内容
    assert report['total_cases'] == 5, "总用例数应为5"
    assert report['healed_cases'] == 4, "修复用例数应为4"
    assert report['by_level']['L1_RETRY']['count'] == 1, "L1应为1"
    assert report['by_level']['L2_DATA']['count'] == 1, "L2应为1"
    assert report['by_level']['L3_FLAKY']['count'] == 1, "L3应为1"
    assert report['by_level']['L4_MANUAL']['count'] == 1, "L4应为1"
    
    print("✅ 修复报告正常")
    print(f"   总用例: {report['total_cases']}")
    print(f"   修复用例: {report['healed_cases']}")
    print(f"   修复率: {report['healing_rate']}")
    print()
    
    return True


def verify_helper_methods():
    """验证6: 辅助方法"""
    print("=" * 80)
    print("验证6: 辅助方法")
    print("=" * 80)
    
    results = [
        ExecutionResult("TC_001", "failed", 0.3, "Connection timeout"),  # L1
        ExecutionResult("TC_002", "failed", 0.4, "Invalid data"),  # L2
        ExecutionResult("TC_003", "failed", 0.5, "Assertion failed"),  # L4
    ]
    
    engine = HealingEngine()
    healed_results = engine.heal(results)
    
    # 验证get_retry_cases
    retry_cases = engine.get_retry_cases(healed_results)
    assert len(retry_cases) == 2, "应有2个需要重试的用例（L1+L2）"
    
    # 验证get_manual_review_cases
    manual_cases = engine.get_manual_review_cases(healed_results)
    assert len(manual_cases) == 1, "应有1个需要人工审查的用例（L4）"
    
    print("✅ 辅助方法正常")
    print(f"   需要重试: {len(retry_cases)}个")
    print(f"   需要人工审查: {len(manual_cases)}个")
    print()
    
    return True


def verify_custom_config():
    """验证7: 自定义配置"""
    print("=" * 80)
    print("验证7: 自定义配置")
    print("=" * 80)
    
    results = [
        ExecutionResult("TC_001", "failed", 0.3, "Connection timeout"),
        ExecutionResult("TC_002", "failed", 0.4, "Flaky test"),
    ]
    
    # 禁用L3修复
    config = {'enable_l3': False}
    engine = HealingEngine(config)
    healed_results = engine.heal(results)
    
    # TC_001应被识别为L1
    assert healed_results[0].healing_info['level'] == HealingLevel.L1_RETRY.value
    
    # TC_002应被识别为L4（因为L3被禁用）
    assert healed_results[1].healing_info['level'] == HealingLevel.L4_MANUAL.value
    
    print("✅ 自定义配置正常")
    print(f"   L3禁用后，flaky错误被识别为L4")
    print()
    
    return True


def main():
    """运行所有验证"""
    print("\n" + "=" * 80)
    print("🚀 开始验证HealingEngine")
    print("=" * 80 + "\n")
    
    results = []
    
    try:
        results.append(("L1检测", verify_l1_detection()))
    except Exception as e:
        print(f"❌ L1检测验证失败: {e}\n")
        results.append(("L1检测", False))
    
    try:
        results.append(("L2检测", verify_l2_detection()))
    except Exception as e:
        print(f"❌ L2检测验证失败: {e}\n")
        results.append(("L2检测", False))
    
    try:
        results.append(("L3检测", verify_l3_detection()))
    except Exception as e:
        print(f"❌ L3检测验证失败: {e}\n")
        results.append(("L3检测", False))
    
    try:
        results.append(("L4检测", verify_l4_detection()))
    except Exception as e:
        print(f"❌ L4检测验证失败: {e}\n")
        results.append(("L4检测", False))
    
    try:
        results.append(("修复报告", verify_healing_report()))
    except Exception as e:
        print(f"❌ 修复报告验证失败: {e}\n")
        results.append(("修复报告", False))
    
    try:
        results.append(("辅助方法", verify_helper_methods()))
    except Exception as e:
        print(f"❌ 辅助方法验证失败: {e}\n")
        results.append(("辅助方法", False))
    
    try:
        results.append(("自定义配置", verify_custom_config()))
    except Exception as e:
        print(f"❌ 自定义配置验证失败: {e}\n")
        results.append(("自定义配置", False))
    
    # 汇总结果
    print("=" * 80)
    print("验证结果汇总")
    print("=" * 80)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status} - {name}")
    
    total = len(results)
    passed_count = sum(1 for _, p in results if p)
    failed_count = total - passed_count
    pass_rate = (passed_count / total * 100) if total > 0 else 0
    
    print(f"\n总计: {total}, 通过: {passed_count}, 失败: {failed_count}")
    print(f"通过率: {pass_rate:.1f}%")
    
    if passed_count == total:
        print("\n🎉 所有验证通过！HealingEngine工作正常！")
        return 0
    else:
        print(f"\n⚠️  有 {failed_count} 个验证失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
