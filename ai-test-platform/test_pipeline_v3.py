#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Pipeline V3 - 使用 TestContext 统一数据模型
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.pipeline_service import get_pipeline_service


def test_pipeline_v3_with_context():
    """测试 Pipeline V3 - 使用 TestContext"""
    
    print("=" * 80)
    print("测试 Pipeline V3 - TestContext 模式")
    print("=" * 80)
    
    pipeline = get_pipeline_service()
    
    # 准备输入数据
    input_data = {
        "requirement": """
需求：电商系统核心功能
1. 商品管理模块
   - 商品列表查询
   - 商品详情查询
2. 订单管理模块
   - 创建订单
   - 查询订单
""",
        "git_diff": """
+ def create_order(user_id, product_id):
+     return {"order_id": "123"}
""",
        "priority": "P0",
        "use_case_generator": True
    }
    
    # 执行 Pipeline
    result = pipeline.run_pipeline(input_data)
    
    print(f"\n✅ Pipeline V3 执行完成:")
    print(f"   - Trace ID: {result.get('trace_id', 'N/A')}")
    print(f"   - 阶段数: {len(result.get('timeline', []))}")
    
    # 验证 TestContext 结构
    assert 'trace_id' in result, "应该包含 trace_id"
    assert 'requirement' in result, "应该包含 requirement"
    assert 'decision' in result, "应该包含 decision"
    assert 'strategy' in result, "应该包含 strategy"
    assert 'cases' in result, "应该包含 cases"
    assert 'execution' in result, "应该包含 execution"
    assert 'report' in result, "应该包含 report"
    assert 'timeline' in result, "应该包含 timeline"
    
    # 验证各阶段数据
    print(f"\n✅ 各阶段数据验证:")
    print(f"   - Decision: {result['decision'] is not None}")
    print(f"   - Strategy: {result['strategy'] is not None}")
    print(f"   - Cases: {result['cases'] is not None}")
    print(f"   - Execution: {result['execution'] is not None}")
    print(f"   - Report: {result['report'] is not None}")
    
    # 验证 Report V2 数据
    report = result.get('report', {})
    assert 'coverage' in report, "Report 应该包含 coverage"
    assert 'traditional_coverage' in report, "Report 应该包含 traditional_coverage"
    assert 'ai_analysis' in report, "Report 应该包含 ai_analysis"
    
    coverage = report.get('coverage', {})
    print(f"\n✅ Report V2 覆盖率数据:")
    print(f"   - 模式: {coverage.get('mode', 'N/A')}")
    print(f"   - 覆盖率: {coverage.get('coverage_rate', 0)}%")
    
    print("\n" + "=" * 80)


def test_pipeline_v3_strategy_mode():
    """测试 Pipeline V3 - 策略模式（不使用 Case Generator）"""
    
    print("\n" + "=" * 80)
    print("测试 Pipeline V3 - 策略模式")
    print("=" * 80)
    
    pipeline = get_pipeline_service()
    
    input_data = {
        "requirement": "用户登录功能优化",
        "git_diff": "+ def login(username): pass",
        "priority": "P1",
        "use_case_generator": False  # 禁用 Case Generator
    }
    
    result = pipeline.run_pipeline(input_data)
    
    print(f"\n✅ Pipeline V3 执行完成:")
    print(f"   - Trace ID: {result.get('trace_id', 'N/A')}")
    
    # 验证策略模式
    assert result.get('cases') is None, "策略模式下 cases 应该是 None"
    
    execution = result.get('execution', {})
    assert execution.get('mode') == 'strategy', "执行模式应该是 strategy"
    
    # 验证覆盖率模式
    report = result.get('report', {})
    coverage = report.get('coverage', {})
    
    print(f"\n✅ 覆盖率数据:")
    print(f"   - 模式: {coverage.get('mode', 'N/A')}")
    print(f"   - 覆盖率: {coverage.get('coverage_rate', 0)}%")
    
    assert coverage.get('mode') == 'strategy_based', "覆盖率模式应该是 strategy_based"
    
    print("\n" + "=" * 80)


def test_pipeline_v3_timeline():
    """测试 Pipeline V3 - 时间线记录"""
    
    print("\n" + "=" * 80)
    print("测试 Pipeline V3 - 时间线记录")
    print("=" * 80)
    
    pipeline = get_pipeline_service()
    
    input_data = {
        "requirement": "测试时间线",
        "git_diff": "+ def test(): pass",
        "priority": "P2",
        "use_case_generator": True
    }
    
    result = pipeline.run_pipeline(input_data)
    
    timeline = result.get('timeline', [])
    
    print(f"\n✅ 时间线事件: {len(timeline)} 个")
    
    for event in timeline:
        print(f"   📍 {event['stage']}: {event['status']} ({event.get('duration', 0)}s)")
    
    # 验证时间线
    assert len(timeline) > 0, "应该有时间线事件"
    
    # 验证必要阶段
    stages = [e['stage'] for e in timeline]
    assert 'agent' in stages, "应该包含 agent 阶段"
    assert 'strategy' in stages, "应该包含 strategy 阶段"
    assert 'report' in stages, "应该包含 report 阶段"
    
    print(f"\n✅ 时间线验证通过")
    print("=" * 80)


if __name__ == "__main__":
    print("\n🚀 开始测试 Pipeline V3\n")
    
    # 测试1: TestContext 模式
    test_pipeline_v3_with_context()
    
    # 测试2: 策略模式
    test_pipeline_v3_strategy_mode()
    
    # 测试3: 时间线记录
    test_pipeline_v3_timeline()
    
    print("\n🎉 所有测试完成！Pipeline V3 已就绪\n")
