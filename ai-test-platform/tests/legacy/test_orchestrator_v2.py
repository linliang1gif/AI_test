#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Orchestrator V2 - 重构后的执行调度器
验证基于用例的执行模式
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator.orchestrator_service import get_orchestrator_service


def test_orchestrator_v2():
    """测试 Orchestrator V2"""
    
    print("=" * 70)
    print("测试 Orchestrator V2 - 基于用例的执行模式")
    print("=" * 70)
    
    # 准备测试用例（来自 Case Generator 的输出）
    test_cases = {
        "cases": [
            {
                "module": "支付模块",
                "cases": [
                    {
                        "id": "TC_01_01",
                        "title": "验证支付模块功能_正常",
                        "type": "功能测试",
                        "priority": "高",
                        "steps": ["步骤1", "步骤2"],
                        "expected_result": "支付成功"
                    },
                    {
                        "id": "TC_01_02",
                        "title": "验证支付模块功能_异常",
                        "type": "异常测试",
                        "priority": "高",
                        "steps": ["步骤1", "步骤2"],
                        "expected_result": "提示错误"
                    },
                    {
                        "id": "TC_01_03",
                        "title": "验证支付模块UI",
                        "type": "UI测试",
                        "priority": "中",
                        "steps": ["步骤1", "步骤2"],
                        "expected_result": "界面正常"
                    }
                ]
            },
            {
                "module": "订单模块",
                "cases": [
                    {
                        "id": "TC_02_01",
                        "title": "验证订单创建",
                        "type": "功能测试",
                        "priority": "高",
                        "steps": ["步骤1", "步骤2"],
                        "expected_result": "订单创建成功"
                    },
                    {
                        "id": "TC_02_02",
                        "title": "验证订单集成",
                        "type": "集成测试",
                        "priority": "中",
                        "steps": ["步骤1", "步骤2"],
                        "expected_result": "集成成功"
                    }
                ]
            }
        ],
        "total_cases": 5,
        "generated_at": "2024-03-21T10:00:00"
    }
    
    # 测试1: 基于用例执行
    print("\n【测试1】基于用例执行")
    print("-" * 70)
    
    service = get_orchestrator_service()
    result = service.run_by_cases(test_cases)
    
    print(f"\n✅ 执行结果:")
    print(f"   - 执行模式: {result.get('mode', 'unknown')}")
    print(f"   - 模块数: {len(result['results'])}")
    print(f"   - 总测试数: {result['summary']['total']}")
    print(f"   - 通过: {result['summary']['passed']}")
    print(f"   - 失败: {result['summary']['failed']}")
    print(f"   - 通过率: {result['summary']['pass_rate']}%")
    print(f"   - 总耗时: {result['summary']['duration']}秒")
    
    # 显示每个模块的结果
    for module_result in result['results']:
        module_name = module_result['module']
        status = module_result['status']
        duration = module_result['duration']
        case_results = module_result.get('case_results', [])
        
        print(f"\n   📦 {module_name}: {status} ({duration}秒)")
        print(f"      {module_result['details']}")
        
        if case_results:
            print(f"      用例结果: {len(case_results)}个")
            for cr in case_results[:3]:
                print(f"         • {cr['title']}: {cr['status']}")
    
    # 测试2: 验证用例类型分组
    print("\n【测试2】验证用例类型分组")
    print("-" * 70)
    
    # 检查是否正确分组
    for module_result in result['results']:
        case_results = module_result.get('case_results', [])
        if case_results:
            print(f"   {module_result['module']}: {len(case_results)} 个用例执行")
    
    # 测试3: 兼容模式 - 基于策略执行
    print("\n【测试3】兼容模式 - 基于策略执行")
    print("-" * 70)
    
    test_strategy = {
        "strategy": [
            {
                "module": {"name": "测试模块", "impact": "high"},
                "priority": "P0",
                "test_types": ["api"],
                "case_count": 5,
                "execution_order": 1,
                "execution_hint": {"parallel": False, "timeout": 60}
            }
        ],
        "total_modules": 1,
        "total_cases": 5
    }
    
    strategy_result = service.run(test_strategy, cases=None)
    
    print(f"   ✅ 策略模式执行:")
    print(f"      - 模式: {strategy_result.get('mode', 'unknown')}")
    print(f"      - 通过: {strategy_result['summary']['passed']}/{strategy_result['summary']['total']}")
    
    # 测试4: 获取统计
    print("\n【测试4】获取统计信息")
    print("-" * 70)
    
    stats = service.get_statistics()
    print(f"   ✅ 统计信息:")
    print(f"      - 总执行次数: {stats['total_executions']}")
    print(f"      - 总测试数: {stats['total_tests']}")
    print(f"      - 平均通过率: {stats['avg_pass_rate']}%")
    
    print("\n" + "=" * 70)
    print("✅ Orchestrator V2 测试完成")
    print("=" * 70)


if __name__ == "__main__":
    test_orchestrator_v2()
