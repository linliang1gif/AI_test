#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Case Generator 模块
验证用例生成功能是否正常工作
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from case_generator.case_service import get_case_service


def test_case_generator():
    """测试用例生成器"""
    
    print("=" * 60)
    print("测试 Case Generator 模块")
    print("=" * 60)
    
    # 准备测试策略（来自 Strategy Engine 的输出）
    test_strategy = {
        "strategy": [
            {
                "module": {
                    "name": "支付模块",
                    "impact": "high"
                },
                "priority": "P0",
                "test_types": ["api", "integration"],
                "case_count": 8,
                "execution_order": 1,
                "risk_level": "高",
                "execution_hint": {
                    "parallel": True,
                    "timeout": 60
                }
            },
            {
                "module": {
                    "name": "订单模块",
                    "impact": "medium"
                },
                "priority": "P1",
                "test_types": ["api"],
                "case_count": 5,
                "execution_order": 2,
                "risk_level": "中",
                "execution_hint": {
                    "parallel": True,
                    "timeout": 90
                }
            }
        ],
        "total_modules": 2,
        "total_cases": 13,
        "generated_at": "2024-03-21T10:00:00"
    }
    
    # 测试1: 生成用例
    print("\n【测试1】生成测试用例")
    print("-" * 60)
    
    service = get_case_service()
    result = service.generate_cases(test_strategy)
    
    print(f"✅ 生成结果:")
    print(f"   - 模块数: {len(result['cases'])}")
    print(f"   - 总用例数: {result['total_cases']}")
    print(f"   - 生成时间: {result['generated_at']}")
    
    # 显示每个模块的用例
    for module_cases in result['cases']:
        module_name = module_cases['module']
        cases = module_cases['cases']
        print(f"\n   📦 {module_name}: {len(cases)} 个用例")
        
        # 显示前3个用例
        for i, case in enumerate(cases[:3], 1):
            print(f"      {i}. {case['title']}")
            print(f"         类型: {case['type']}, 优先级: {case['priority']}")
    
    # 测试2: 验证用例结构
    print("\n【测试2】验证用例结构")
    print("-" * 60)
    
    required_fields = [
        'id', 'title', 'module', 'testpoint', 'scenario_id',
        'precondition', 'steps', 'test_data', 'expected_result',
        'priority', 'type', 'complexity', 'estimated_time',
        'automation_feasible', 'risk_level', 'tags'
    ]
    
    all_valid = True
    for module_cases in result['cases']:
        for case in module_cases['cases']:
            for field in required_fields:
                if field not in case:
                    print(f"   ❌ 缺少字段: {field}")
                    all_valid = False
    
    if all_valid:
        print("   ✅ 所有用例结构完整")
    
    # 测试3: 验证优先级过滤
    print("\n【测试3】验证优先级过滤")
    print("-" * 60)
    
    # P0 应该有正常+异常+边界
    p0_module = result['cases'][0]
    p0_types = set(case['type'] for case in p0_module['cases'])
    print(f"   P0 模块用例类型: {p0_types}")
    
    # P1 应该有正常+异常
    if len(result['cases']) > 1:
        p1_module = result['cases'][1]
        p1_types = set(case['type'] for case in p1_module['cases'])
        print(f"   P1 模块用例类型: {p1_types}")
    
    # 测试4: 获取历史
    print("\n【测试4】获取用例历史")
    print("-" * 60)
    
    history = service.get_case_history(limit=5)
    print(f"   ✅ 历史记录数: {len(history)}")
    
    # 测试5: 获取统计
    print("\n【测试5】获取统计信息")
    print("-" * 60)
    
    stats = service.get_statistics()
    print(f"   ✅ 统计信息:")
    print(f"      - 总生成次数: {stats['total_generations']}")
    print(f"      - 总用例数: {stats['total_cases']}")
    print(f"      - 平均每次生成: {stats['avg_cases_per_generation']}")
    
    # 测试6: 空策略处理
    print("\n【测试6】空策略处理")
    print("-" * 60)
    
    empty_strategy = {
        "strategy": [],
        "total_modules": 0,
        "total_cases": 0
    }
    
    empty_result = service.generate_cases(empty_strategy)
    print(f"   ✅ 空策略处理: {empty_result['total_cases']} 个用例")
    
    print("\n" + "=" * 60)
    print("✅ Case Generator 模块测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_case_generator()
