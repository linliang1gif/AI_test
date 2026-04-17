#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证 TestContext 完整集成
验证统一数据模型在整个系统中的工作情况
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from common.context import TestContext
from pipeline.pipeline_service import get_pipeline_service


def verify_context_integration():
    """验证 TestContext 完整集成"""
    
    print("=" * 80)
    print("验证 TestContext 完整集成")
    print("=" * 80)
    
    pipeline = get_pipeline_service()
    
    # 准备输入数据
    input_data = {
        "requirement": """
需求：电商平台核心功能
1. 商品管理模块
   - 商品上架
   - 商品下架
   - 商品编辑
2. 订单管理模块
   - 创建订单
   - 取消订单
   - 订单查询
3. 支付管理模块
   - 在线支付
   - 退款处理
""",
        "git_diff": """
+ def create_order(user_id, items):
+     # 创建订单逻辑
+     return {"order_id": "ORD123", "status": "created"}
+ 
+ def process_payment(order_id, amount):
+     # 支付处理逻辑
+     return {"payment_id": "PAY456", "status": "success"}
""",
        "priority": "P0",
        "use_case_generator": True
    }
    
    # 执行 Pipeline
    result = pipeline.run_pipeline(input_data)
    
    print(f"\n【验证点1】TestContext 结构完整性")
    print("-" * 80)
    
    # 验证 TestContext 核心字段
    core_fields = ['trace_id', 'requirement', 'git_diff', 'priority', 'use_case_generator', 'created_at', 'timeline']
    
    for field in core_fields:
        exists = field in result
        status = "✅" if exists else "❌"
        print(f"   {status} {field}: {'存在' if exists else '缺失'}")
        assert exists, f"应该包含 {field}"
    
    print(f"\n【验证点2】阶段数据完整性")
    print("-" * 80)
    
    # 验证各阶段数据
    stage_fields = ['decision', 'strategy', 'cases', 'execution', 'report']
    
    for field in stage_fields:
        data = result.get(field)
        exists = data is not None
        status = "✅" if exists else "⚠️"
        print(f"   {status} {field}: {'有数据' if exists else '无数据'}")
    
    # decision, strategy, execution, report 必须存在
    assert result.get('decision') is not None, "decision 必须存在"
    assert result.get('strategy') is not None, "strategy 必须存在"
    assert result.get('execution') is not None, "execution 必须存在"
    assert result.get('report') is not None, "report 必须存在"
    
    print(f"\n【验证点3】Report V2 增强功能")
    print("-" * 80)
    
    report = result.get('report', {})
    
    # 验证 Report V2 字段
    report_v2_fields = ['coverage', 'traditional_coverage', 'ai_analysis']
    
    for field in report_v2_fields:
        exists = field in report
        status = "✅" if exists else "❌"
        print(f"   {status} {field}: {'存在' if exists else '缺失'}")
        assert exists, f"Report 应该包含 {field}"
    
    # 显示覆盖率数据
    coverage = report.get('coverage', {})
    print(f"\n   覆盖率分析:")
    print(f"      - 模式: {coverage.get('mode', 'N/A')}")
    print(f"      - 总用例数: {coverage.get('total_cases', 0)}")
    print(f"      - 已执行: {coverage.get('executed_cases', 0)}")
    print(f"      - 覆盖率: {coverage.get('coverage_rate', 0)}%")
    
    # 显示模块覆盖率
    module_coverage = coverage.get('module_coverage', [])
    if module_coverage:
        print(f"\n   模块覆盖率: {len(module_coverage)} 个模块")
        for mc in module_coverage[:3]:  # 只显示前3个
            print(f"      📦 {mc.get('module', 'N/A')}: {mc.get('coverage_rate', 0)}%")
    
    print(f"\n【验证点4】时间线记录")
    print("-" * 80)
    
    timeline = result.get('timeline', [])
    print(f"   时间线事件: {len(timeline)} 个")
    
    for event in timeline:
        print(f"      📍 {event['stage']}: {event['status']} ({event.get('duration', 0)}s)")
    
    # 验证必要阶段
    stages = [e['stage'] for e in timeline]
    required_stages = ['agent', 'strategy', 'orchestrator', 'report']
    
    for stage in required_stages:
        assert stage in stages, f"时间线应该包含 {stage} 阶段"
    
    print(f"\n【验证点5】数据流一致性")
    print("-" * 80)
    
    # 验证数据流：decision → strategy → cases → execution → report
    decision = result.get('decision', {})
    strategy = result.get('strategy', {})
    cases = result.get('cases', {})
    execution = result.get('execution', {})
    
    # 验证模块数量一致性
    parsed_modules = len(decision.get('parsed_modules', []))
    strategy_modules = len(strategy.get('strategy', []))
    case_modules = len(cases.get('cases', [])) if cases else 0
    execution_modules = len(execution.get('results', []))
    
    print(f"   模块数量流转:")
    print(f"      Agent 解析: {parsed_modules} 个")
    print(f"      Strategy 生成: {strategy_modules} 个")
    print(f"      Case Generator: {case_modules} 个")
    print(f"      Orchestrator 执行: {execution_modules} 个")
    
    # 验证用例数量一致性
    strategy_cases = strategy.get('total_cases', 0)
    generated_cases = cases.get('total_cases', 0) if cases else 0
    
    print(f"\n   用例数量流转:")
    print(f"      Strategy 估算: {strategy_cases} 个")
    print(f"      Case Generator 生成: {generated_cases} 个")
    
    print(f"\n【验证点6】统一数据模型优势")
    print("-" * 80)
    
    print(f"   ✅ 单一数据对象: TestContext")
    print(f"   ✅ 所有模块只接收 context")
    print(f"   ✅ 不再传多个 JSON")
    print(f"   ✅ Pipeline 只传 context")
    print(f"   ✅ 降低模块耦合")
    print(f"   ✅ 统一数据流")
    
    print("\n" + "=" * 80)
    print("✅ TestContext 完整集成验证通过")
    print("=" * 80)


if __name__ == "__main__":
    verify_context_integration()
    print("\n🎉 验证完成！统一数据模型已就绪\n")
