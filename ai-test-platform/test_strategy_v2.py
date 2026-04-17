"""
测试 Strategy Engine V2 增强功能
验证所有 V2 新增字段和结构
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from strategy.strategy_service import get_strategy_service
from datetime import datetime


def test_v2_module_structure():
    """测试1：验证 module 对象结构"""
    print("\n" + "="*60)
    print("测试1：验证 module 对象结构")
    print("="*60)
    
    service = get_strategy_service()
    
    # 模拟 Agent V2 决策
    agent_decision = {
        "action": "run_tests",
        "need_test": True,
        "modules": ["支付模块", "订单模块"],
        "priority": "P0",
        "risk_level": "高",
        "confidence": 0.9,
        "timestamp": datetime.now().isoformat()
    }
    
    result = service.generate_strategy(agent_decision)
    
    # 验证
    assert "strategy" in result, "❌ 缺少 strategy 字段"
    assert len(result["strategy"]) == 2, f"❌ 应该有2个策略，实际{len(result['strategy'])}"
    
    # 验证第一个模块的结构
    first_strategy = result["strategy"][0]
    
    # V2要求：module 必须是对象
    assert "module" in first_strategy, "❌ 缺少 module 字段"
    assert isinstance(first_strategy["module"], dict), "❌ module 必须是对象"
    assert "name" in first_strategy["module"], "❌ module 缺少 name"
    assert "impact" in first_strategy["module"], "❌ module 缺少 impact"
    
    print(f"✅ module 结构正确:")
    print(f"   - name: {first_strategy['module']['name']}")
    print(f"   - impact: {first_strategy['module']['impact']}")
    
    return True


def test_v2_execution_hint():
    """测试2：验证 execution_hint 字段"""
    print("\n" + "="*60)
    print("测试2：验证 execution_hint 字段")
    print("="*60)
    
    service = get_strategy_service()
    
    # 测试不同优先级的 execution_hint
    test_cases = [
        ("P0", {"parallel": True, "timeout": 60}),
        ("P1", {"parallel": True, "timeout": 90}),
        ("P2", {"parallel": False, "timeout": 120})
    ]
    
    for priority, expected_hint in test_cases:
        agent_decision = {
            "action": "run_tests",
            "modules": ["测试模块"],
            "priority": priority,
            "risk_level": "中",
            "confidence": 0.8,
            "timestamp": datetime.now().isoformat()
        }
        
        result = service.generate_strategy(agent_decision)
        strategy = result["strategy"][0]
        
        # 验证 execution_hint
        assert "execution_hint" in strategy, f"❌ {priority} 缺少 execution_hint"
        assert isinstance(strategy["execution_hint"], dict), f"❌ {priority} execution_hint 必须是对象"
        assert "parallel" in strategy["execution_hint"], f"❌ {priority} 缺少 parallel"
        assert "timeout" in strategy["execution_hint"], f"❌ {priority} 缺少 timeout"
        
        # 验证值
        actual_hint = strategy["execution_hint"]
        assert actual_hint["parallel"] == expected_hint["parallel"], \
            f"❌ {priority} parallel 应为 {expected_hint['parallel']}, 实际 {actual_hint['parallel']}"
        assert actual_hint["timeout"] == expected_hint["timeout"], \
            f"❌ {priority} timeout 应为 {expected_hint['timeout']}, 实际 {actual_hint['timeout']}"
        
        print(f"✅ {priority} execution_hint 正确: parallel={actual_hint['parallel']}, timeout={actual_hint['timeout']}")
    
    return True


def test_v2_summary():
    """测试3：验证 summary 字段"""
    print("\n" + "="*60)
    print("测试3：验证 summary 字段")
    print("="*60)
    
    service = get_strategy_service()
    
    agent_decision = {
        "action": "run_tests",
        "modules": ["模块A", "模块B", "模块C"],
        "priority": "P1",
        "risk_level": "高",
        "confidence": 0.85,
        "timestamp": datetime.now().isoformat()
    }
    
    result = service.generate_strategy(agent_decision)
    
    # 验证 summary 存在
    assert "summary" in result, "❌ 缺少 summary 字段"
    assert isinstance(result["summary"], dict), "❌ summary 必须是对象"
    
    # 验证 summary 子字段
    summary = result["summary"]
    assert "total_modules" in summary, "❌ summary 缺少 total_modules"
    assert "estimated_total_cases" in summary, "❌ summary 缺少 estimated_total_cases"
    assert "risk_level" in summary, "❌ summary 缺少 risk_level"
    
    # 验证值
    assert summary["total_modules"] == 3, f"❌ total_modules 应为3，实际{summary['total_modules']}"
    assert summary["estimated_total_cases"] > 0, "❌ estimated_total_cases 应大于0"
    assert summary["risk_level"] == "高", f"❌ risk_level 应为'高'，实际'{summary['risk_level']}'"
    
    print(f"✅ summary 结构正确:")
    print(f"   - total_modules: {summary['total_modules']}")
    print(f"   - estimated_total_cases: {summary['estimated_total_cases']}")
    print(f"   - risk_level: {summary['risk_level']}")
    
    return True


def test_v2_empty_strategy():
    """测试4：验证空策略也包含 summary"""
    print("\n" + "="*60)
    print("测试4：验证空策略的 summary")
    print("="*60)
    
    service = get_strategy_service()
    
    agent_decision = {
        "action": "skip",
        "modules": [],
        "priority": "P2",
        "risk_level": "低",
        "confidence": 0.6,
        "timestamp": datetime.now().isoformat()
    }
    
    result = service.generate_strategy(agent_decision)
    
    # 验证空策略
    assert result["strategy"] == [], "❌ 空策略的 strategy 应为空列表"
    assert result["total_modules"] == 0, "❌ 空策略的 total_modules 应为0"
    
    # 验证 summary 存在
    assert "summary" in result, "❌ 空策略缺少 summary"
    summary = result["summary"]
    
    assert summary["total_modules"] == 0, "❌ 空策略 summary.total_modules 应为0"
    assert summary["estimated_total_cases"] == 0, "❌ 空策略 summary.estimated_total_cases 应为0"
    assert summary["risk_level"] == "低", f"❌ 空策略 summary.risk_level 应为'低'，实际'{summary['risk_level']}'"
    
    print(f"✅ 空策略 summary 正确:")
    print(f"   - total_modules: {summary['total_modules']}")
    print(f"   - estimated_total_cases: {summary['estimated_total_cases']}")
    print(f"   - risk_level: {summary['risk_level']}")
    
    return True


def test_v2_no_none_values():
    """测试5：验证所有字段都不为 None"""
    print("\n" + "="*60)
    print("测试5：验证无 None 值")
    print("="*60)
    
    service = get_strategy_service()
    
    agent_decision = {
        "action": "run_tests",
        "modules": ["核心模块"],
        "priority": "P0",
        "risk_level": "高",
        "confidence": 0.9,
        "timestamp": datetime.now().isoformat()
    }
    
    result = service.generate_strategy(agent_decision)
    
    # 检查顶层字段
    for key, value in result.items():
        if key == "strategy":
            continue  # strategy 是列表，单独检查
        assert value is not None, f"❌ 字段 {key} 不能为 None"
    
    # 检查 strategy 中的每个模块
    for idx, strategy in enumerate(result["strategy"]):
        for key, value in strategy.items():
            assert value is not None, f"❌ 策略{idx} 的字段 {key} 不能为 None"
            
            # 检查嵌套对象
            if key == "module":
                assert value.get("name") is not None, f"❌ 策略{idx} module.name 不能为 None"
                assert value.get("impact") is not None, f"❌ 策略{idx} module.impact 不能为 None"
            
            if key == "execution_hint":
                assert value.get("parallel") is not None, f"❌ 策略{idx} execution_hint.parallel 不能为 None"
                assert value.get("timeout") is not None, f"❌ 策略{idx} execution_hint.timeout 不能为 None"
    
    # 检查 summary
    summary = result["summary"]
    assert summary["total_modules"] is not None, "❌ summary.total_modules 不能为 None"
    assert summary["estimated_total_cases"] is not None, "❌ summary.estimated_total_cases 不能为 None"
    assert summary["risk_level"] is not None, "❌ summary.risk_level 不能为 None"
    
    print("✅ 所有字段都有值，无 None")
    
    return True


def test_v2_execution_order_stable():
    """测试6：验证排序稳定性"""
    print("\n" + "="*60)
    print("测试6：验证排序稳定性")
    print("="*60)
    
    service = get_strategy_service()
    
    agent_decision = {
        "action": "run_tests",
        "modules": ["模块A", "模块B", "模块C"],
        "priority": "P0",
        "risk_level": "高",
        "confidence": 0.9,
        "timestamp": datetime.now().isoformat()
    }
    
    # 多次生成，验证顺序一致
    results = []
    for i in range(3):
        result = service.generate_strategy(agent_decision)
        orders = [s["execution_order"] for s in result["strategy"]]
        results.append(orders)
    
    # 验证所有结果的顺序一致
    first_order = results[0]
    for idx, order in enumerate(results[1:], 1):
        assert order == first_order, f"❌ 第{idx+1}次生成的顺序不一致"
    
    print(f"✅ 排序稳定，3次生成顺序一致: {first_order}")
    
    return True


def test_v2_complete_output():
    """测试7：完整输出示例"""
    print("\n" + "="*60)
    print("测试7：完整 V2 输出示例")
    print("="*60)
    
    service = get_strategy_service()
    
    agent_decision = {
        "action": "run_tests",
        "modules": ["支付模块", "用户模块"],
        "priority": "P0",
        "risk_level": "高",
        "confidence": 0.92,
        "timestamp": datetime.now().isoformat()
    }
    
    result = service.generate_strategy(agent_decision)
    
    print("\n📋 完整 V2 输出结构:")
    print("-" * 60)
    
    # 显示顶层字段
    print(f"total_modules: {result['total_modules']}")
    print(f"total_cases: {result['total_cases']}")
    print(f"confidence: {result['confidence']}")
    
    # 显示 summary
    print(f"\nsummary:")
    print(f"  - total_modules: {result['summary']['total_modules']}")
    print(f"  - estimated_total_cases: {result['summary']['estimated_total_cases']}")
    print(f"  - risk_level: {result['summary']['risk_level']}")
    
    # 显示策略详情
    print(f"\nstrategy ({len(result['strategy'])} 项):")
    for idx, strategy in enumerate(result["strategy"], 1):
        print(f"\n  [{idx}] {strategy['module']['name']}:")
        print(f"      - module.impact: {strategy['module']['impact']}")
        print(f"      - priority: {strategy['priority']}")
        print(f"      - test_types: {strategy['test_types']}")
        print(f"      - case_count: {strategy['case_count']}")
        print(f"      - execution_order: {strategy['execution_order']}")
        print(f"      - execution_hint:")
        print(f"          * parallel: {strategy['execution_hint']['parallel']}")
        print(f"          * timeout: {strategy['execution_hint']['timeout']}")
    
    print("\n✅ V2 输出结构完整")
    
    return True


def main():
    """运行所有测试"""
    print("\n" + "🚀 " + "="*58)
    print("🚀  Strategy Engine V2 增强功能测试")
    print("🚀 " + "="*58)
    
    tests = [
        ("V2 module 对象结构", test_v2_module_structure),
        ("V2 execution_hint", test_v2_execution_hint),
        ("V2 summary 字段", test_v2_summary),
        ("V2 空策略 summary", test_v2_empty_strategy),
        ("V2 无 None 值", test_v2_no_none_values),
        ("V2 排序稳定性", test_v2_execution_order_stable),
        ("V2 完整输出", test_v2_complete_output)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except AssertionError as e:
            print(f"\n❌ 测试失败: {name}")
            print(f"   错误: {e}")
            failed += 1
        except Exception as e:
            print(f"\n❌ 测试异常: {name}")
            print(f"   错误: {e}")
            failed += 1
    
    # 总结
    print("\n" + "="*60)
    print("📊 测试总结")
    print("="*60)
    print(f"✅ 通过: {passed}/{len(tests)}")
    print(f"❌ 失败: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 所有 V2 增强功能测试通过！")
        print("\n✨ V2 新增功能:")
        print("   1. module 对象结构 (name + impact)")
        print("   2. execution_hint (parallel + timeout)")
        print("   3. summary 统计 (total_modules + estimated_total_cases + risk_level)")
        print("   4. 所有字段非 None")
        print("   5. 排序稳定")
        return True
    else:
        print(f"\n⚠️  有 {failed} 个测试失败")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
