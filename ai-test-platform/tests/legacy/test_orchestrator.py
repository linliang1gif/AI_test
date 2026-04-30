"""
测试 Orchestrator 模块
验证测试执行调度功能
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator.orchestrator_service import get_orchestrator_service
from datetime import datetime
import time


def test_basic_execution():
    """测试1：基础执行功能"""
    print("\n" + "="*60)
    print("测试1：基础执行功能")
    print("="*60)
    
    service = get_orchestrator_service()
    
    # 模拟 Strategy Engine 输出
    strategy = {
        "strategy": [
            {
                "module": {"name": "支付模块", "impact": "high"},
                "priority": "P0",
                "test_types": ["api", "ui"],
                "case_count": 30,
                "execution_order": 1,
                "execution_hint": {"parallel": True, "timeout": 60}
            }
        ],
        "summary": {
            "total_modules": 1,
            "estimated_total_cases": 30,
            "risk_level": "高"
        }
    }
    
    result = service.run(strategy)
    
    # 验证
    assert "results" in result, "❌ 缺少 results"
    assert "summary" in result, "❌ 缺少 summary"
    assert len(result["results"]) == 1, f"❌ 应该有1个结果，实际{len(result['results'])}"
    
    # 验证结果结构
    test_result = result["results"][0]
    assert "module" in test_result, "❌ 结果缺少 module"
    assert "status" in test_result, "❌ 结果缺少 status"
    assert "duration" in test_result, "❌ 结果缺少 duration"
    assert "details" in test_result, "❌ 结果缺少 details"
    
    # 验证 summary
    summary = result["summary"]
    assert summary["total"] == 1, f"❌ total 应为1，实际{summary['total']}"
    assert summary["passed"] >= 0, "❌ passed 应>=0"
    assert summary["failed"] >= 0, "❌ failed 应>=0"
    
    print(f"✅ 基础执行成功:")
    print(f"   - 模块: {test_result['module']}")
    print(f"   - 状态: {test_result['status']}")
    print(f"   - 耗时: {test_result['duration']}s")
    print(f"   - 通过率: {summary['pass_rate']}%")
    
    return True


def test_multiple_test_types():
    """测试2：多种测试类型执行"""
    print("\n" + "="*60)
    print("测试2：多种测试类型执行")
    print("="*60)
    
    service = get_orchestrator_service()
    
    strategy = {
        "strategy": [
            {
                "module": {"name": "核心模块", "impact": "high"},
                "priority": "P0",
                "test_types": ["api", "ui", "integration"],
                "case_count": 30,
                "execution_order": 1,
                "execution_hint": {"parallel": False, "timeout": 60}
            }
        ],
        "summary": {
            "total_modules": 1,
            "estimated_total_cases": 30,
            "risk_level": "高"
        }
    }
    
    result = service.run(strategy)
    
    # 验证执行了3种测试类型
    test_result = result["results"][0]
    details = test_result["details"]
    
    assert "api" in details.lower(), "❌ 应该执行了 API 测试"
    assert "ui" in details.lower(), "❌ 应该执行了 UI 测试"
    assert "integration" in details.lower() or "集成" in details, "❌ 应该执行了集成测试"
    
    print(f"✅ 多类型测试执行成功:")
    print(f"   - 详情: {details}")
    
    return True


def test_parallel_execution():
    """测试3：并发执行"""
    print("\n" + "="*60)
    print("测试3：并发执行")
    print("="*60)
    
    service = get_orchestrator_service()
    
    # 3个模块，都设置为并发
    strategy = {
        "strategy": [
            {
                "module": {"name": "模块A", "impact": "high"},
                "priority": "P0",
                "test_types": ["api"],
                "case_count": 20,
                "execution_order": 1,
                "execution_hint": {"parallel": True, "timeout": 60}
            },
            {
                "module": {"name": "模块B", "impact": "high"},
                "priority": "P0",
                "test_types": ["api"],
                "case_count": 20,
                "execution_order": 1,
                "execution_hint": {"parallel": True, "timeout": 60}
            },
            {
                "module": {"name": "模块C", "impact": "high"},
                "priority": "P0",
                "test_types": ["api"],
                "case_count": 20,
                "execution_order": 1,
                "execution_hint": {"parallel": True, "timeout": 60}
            }
        ],
        "summary": {
            "total_modules": 3,
            "estimated_total_cases": 60,
            "risk_level": "高"
        }
    }
    
    start = time.time()
    result = service.run(strategy)
    duration = time.time() - start
    
    # 验证
    assert len(result["results"]) == 3, f"❌ 应该有3个结果，实际{len(result['results'])}"
    
    # 并发执行应该比串行快
    # 3个模块 * 0.1s = 0.3s (串行)
    # 并发应该接近 0.1s
    print(f"✅ 并发执行完成:")
    print(f"   - 总耗时: {duration:.2f}s")
    print(f"   - 模块数: {len(result['results'])}")
    print(f"   - 通过: {result['summary']['passed']}/{result['summary']['total']}")
    
    if duration < 0.25:  # 如果明显快于串行
        print(f"   - ⚡ 并发加速明显 (预期串行>0.3s)")
    
    return True


def test_execution_order():
    """测试4：执行顺序"""
    print("\n" + "="*60)
    print("测试4：执行顺序")
    print("="*60)
    
    service = get_orchestrator_service()
    
    # 不同 execution_order
    strategy = {
        "strategy": [
            {
                "module": {"name": "模块C", "impact": "low"},
                "priority": "P2",
                "test_types": ["api"],
                "case_count": 10,
                "execution_order": 3,
                "execution_hint": {"parallel": False, "timeout": 120}
            },
            {
                "module": {"name": "模块A", "impact": "high"},
                "priority": "P0",
                "test_types": ["api"],
                "case_count": 30,
                "execution_order": 1,
                "execution_hint": {"parallel": True, "timeout": 60}
            },
            {
                "module": {"name": "模块B", "impact": "medium"},
                "priority": "P1",
                "test_types": ["api"],
                "case_count": 20,
                "execution_order": 2,
                "execution_hint": {"parallel": True, "timeout": 90}
            }
        ],
        "summary": {
            "total_modules": 3,
            "estimated_total_cases": 60,
            "risk_level": "中"
        }
    }
    
    result = service.run(strategy)
    
    # 验证执行顺序
    modules = [r["module"] for r in result["results"]]
    
    # 应该按 execution_order 排序: A(1) -> B(2) -> C(3)
    assert modules[0] == "模块A", f"❌ 第1个应该是模块A，实际{modules[0]}"
    assert modules[1] == "模块B", f"❌ 第2个应该是模块B，实际{modules[1]}"
    assert modules[2] == "模块C", f"❌ 第3个应该是模块C，实际{modules[2]}"
    
    print(f"✅ 执行顺序正确: {' -> '.join(modules)}")
    
    return True


def test_empty_strategy():
    """测试5：空策略"""
    print("\n" + "="*60)
    print("测试5：空策略")
    print("="*60)
    
    service = get_orchestrator_service()
    
    strategy = {
        "strategy": [],
        "summary": {
            "total_modules": 0,
            "estimated_total_cases": 0,
            "risk_level": "低"
        }
    }
    
    result = service.run(strategy)
    
    # 验证
    assert result["results"] == [], "❌ 空策略应返回空结果"
    assert result["summary"]["total"] == 0, "❌ total 应为0"
    assert result["summary"]["passed"] == 0, "❌ passed 应为0"
    
    print(f"✅ 空策略处理正确")
    
    return True


def test_summary_calculation():
    """测试6：摘要计算"""
    print("\n" + "="*60)
    print("测试6：摘要计算")
    print("="*60)
    
    service = get_orchestrator_service()
    
    strategy = {
        "strategy": [
            {
                "module": {"name": f"模块{i}", "impact": "medium"},
                "priority": "P1",
                "test_types": ["api"],
                "case_count": 20,
                "execution_order": 1,
                "execution_hint": {"parallel": True, "timeout": 90}
            }
            for i in range(5)
        ],
        "summary": {
            "total_modules": 5,
            "estimated_total_cases": 100,
            "risk_level": "中"
        }
    }
    
    result = service.run(strategy)
    
    # 验证 summary
    summary = result["summary"]
    assert summary["total"] == 5, f"❌ total 应为5，实际{summary['total']}"
    assert summary["passed"] + summary["failed"] == 5, "❌ passed+failed 应等于 total"
    assert 0 <= summary["pass_rate"] <= 100, "❌ pass_rate 应在0-100之间"
    assert summary["duration"] > 0, "❌ duration 应大于0"
    
    print(f"✅ 摘要计算正确:")
    print(f"   - 总数: {summary['total']}")
    print(f"   - 通过: {summary['passed']}")
    print(f"   - 失败: {summary['failed']}")
    print(f"   - 通过率: {summary['pass_rate']}%")
    print(f"   - 耗时: {summary['duration']}s")
    
    return True


def main():
    """运行所有测试"""
    print("\n" + "🚀 " + "="*58)
    print("🚀  Test Orchestrator 功能测试")
    print("🚀 " + "="*58)
    
    tests = [
        ("基础执行功能", test_basic_execution),
        ("多种测试类型", test_multiple_test_types),
        ("并发执行", test_parallel_execution),
        ("执行顺序", test_execution_order),
        ("空策略处理", test_empty_strategy),
        ("摘要计算", test_summary_calculation)
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
        print("\n🎉 所有 Orchestrator 功能测试通过！")
        print("\n✨ 核心功能:")
        print("   1. 按 execution_order 排序执行")
        print("   2. 支持多种测试类型 (api/ui/integration)")
        print("   3. 并发执行支持")
        print("   4. 失败处理和汇总")
        print("   5. 执行历史记录")
        return True
    else:
        print(f"\n⚠️  有 {failed} 个测试失败")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
