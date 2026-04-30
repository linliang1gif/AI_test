#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终系统演示
展示六阶段流程的完整工作流程
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.pipeline_service import get_pipeline_service


def demo_complete_mode():
    """演示完整模式 - 启用 Case Generator"""
    
    print("=" * 80)
    print("演示：完整模式 (Agent → Strategy → Case Generator → Orchestrator → Healing → Report)")
    print("=" * 80)
    
    pipeline = get_pipeline_service()
    
    input_data = {
        "requirement": """
需求：电商平台支付功能升级
1. 支付模块
   - 支持微信支付
   - 支持支付宝支付
   - 支付结果通知
2. 退款模块
   - 全额退款
   - 部分退款
   - 退款审核
""",
        "git_diff": """
+ def wechat_pay(order_id, amount):
+     # 微信支付逻辑
+     return {"status": "success", "transaction_id": "WX123"}
+ 
+ def alipay(order_id, amount):
+     # 支付宝支付逻辑
+     return {"status": "success", "transaction_id": "ALI456"}
""",
        "priority": "P0",
        "use_case_generator": True  # 启用 Case Generator
    }
    
    result = pipeline.run_pipeline(input_data)
    
    print(f"\n📊 执行结果:")
    print(f"   Trace ID: {result['trace_id']}")
    print(f"   优先级: {result['priority']}")
    
    print(f"\n【阶段1】Agent 决策:")
    decision = result['decision']
    print(f"   需要测试: {decision['need_test']}")
    print(f"   风险等级: {decision['risk_level']}")
    print(f"   解析模块: {len(decision.get('parsed_modules', []))} 个")
    
    print(f"\n【阶段2】Strategy 策略:")
    strategy = result['strategy']
    print(f"   策略数: {len(strategy.get('strategy', []))}")
    print(f"   估算用例: {strategy.get('total_cases', 0)} 个")
    
    print(f"\n【阶段3】Case Generator 用例:")
    cases = result.get('cases')
    if cases:
        print(f"   生成模块: {len(cases.get('cases', []))}")
        print(f"   生成用例: {cases.get('total_cases', 0)} 个")
    
    print(f"\n【阶段4】Orchestrator 执行:")
    execution = result['execution']
    exec_summary = execution.get('summary', {})
    print(f"   执行模式: {execution.get('mode', 'N/A')}")
    print(f"   总数: {exec_summary.get('total', 0)}")
    print(f"   通过: {exec_summary.get('passed', 0)}")
    print(f"   失败: {exec_summary.get('failed', 0)}")
    
    print(f"\n【阶段5】Self-Healing 修复:")
    healing = result.get('healing')
    if healing:
        stats = healing.get('statistics', {})
        print(f"   修复次数: {stats.get('total_healings', 0)}")
        print(f"   成功修复: {stats.get('successful_fixes', 0)}")
    else:
        print(f"   ⏭️  跳过（无失败）")
    
    print(f"\n【阶段6】Report 报告:")
    report = result['report']
    coverage = report.get('coverage', {})
    print(f"   状态: {report['summary']['status']}")
    print(f"   覆盖率模式: {coverage.get('mode', 'N/A')}")
    print(f"   覆盖率: {coverage.get('coverage_rate', 0)}%")
    
    print(f"\n⏱️  总耗时: {sum(e.get('duration', 0) for e in result['timeline'])}s")
    
    print("\n" + "=" * 80)


def demo_fast_mode():
    """演示快速模式 - 禁用 Case Generator"""
    
    print("\n" + "=" * 80)
    print("演示：快速模式 (Agent → Strategy → Orchestrator → Healing → Report)")
    print("=" * 80)
    
    pipeline = get_pipeline_service()
    
    input_data = {
        "requirement": "用户登录功能优化",
        "git_diff": "+ def login_with_captcha(): pass",
        "priority": "P1",
        "use_case_generator": False  # 禁用 Case Generator
    }
    
    result = pipeline.run_pipeline(input_data)
    
    print(f"\n📊 执行结果:")
    print(f"   Trace ID: {result['trace_id']}")
    
    print(f"\n【阶段3】Case Generator:")
    print(f"   ⏭️  跳过（配置禁用）")
    
    print(f"\n【阶段4】Orchestrator 执行:")
    execution = result['execution']
    print(f"   执行模式: {execution.get('mode', 'N/A')}")
    print(f"   通过率: {execution.get('summary', {}).get('pass_rate', 0)}%")
    
    print(f"\n【阶段6】Report 报告:")
    report = result['report']
    coverage = report.get('coverage', {})
    print(f"   覆盖率模式: {coverage.get('mode', 'N/A')}")
    print(f"   覆盖率: {coverage.get('coverage_rate', 0)}%")
    
    print("\n" + "=" * 80)


def demo_system_features():
    """演示系统特性"""
    
    print("\n" + "=" * 80)
    print("系统核心特性")
    print("=" * 80)
    
    print(f"\n✅ 统一数据模型:")
    print(f"   • TestContext 类")
    print(f"   • 所有模块只接收 context")
    print(f"   • 不再传多个 JSON")
    
    print(f"\n✅ 传统能力重用:")
    print(f"   • Agent: RequirementParser + ModuleSplitter")
    print(f"   • Case Generator: ScenarioBuilder + CaseBuilder")
    print(f"   • Report: CoverageAnalyzer")
    
    print(f"\n✅ AI 能力增强:")
    print(f"   • Agent: LLM 决策分析")
    print(f"   • Report: AI 总结生成")
    
    print(f"\n✅ 流程可插拔:")
    print(f"   • Case Generator 可启用/禁用")
    print(f"   • Self-Healing 按需触发")
    print(f"   • 支持提前退出")
    
    print(f"\n✅ 覆盖率分析:")
    print(f"   • case_based: 基于用例执行统计")
    print(f"   • strategy_based: 基于策略估算")
    print(f"   • 模块级覆盖率")
    
    print(f"\n✅ 可追溯性:")
    print(f"   • trace_id 全局唯一")
    print(f"   • timeline 记录所有阶段")
    print(f"   • 完整执行历史")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    print("\n🚀 AI 测试平台最终系统演示\n")
    
    # 演示1: 完整模式
    demo_complete_mode()
    
    # 演示2: 快速模式
    demo_fast_mode()
    
    # 演示3: 系统特性
    demo_system_features()
    
    print("\n🎉 演示完成！\n")
