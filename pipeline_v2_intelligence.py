#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整测试 Pipeline V2 - Intelligence Agent 接管版

🔥 架构升级:
- Intelligence Agent 完全接管执行层
- ExecutionEngine 只能执行 execution_plan
- 引入 test_cases_map 解决 TestCase 查找问题
- 所有执行路径统一

流程:
Discovery Agent → Design Agent → Optimization Agent → Intelligence Agent → ExecutionEngine → Healing Agent → Report
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# 导入新的 Agent 架构
from modules.agents import (
    DesignAgent, HealingAgent, LearningAgent, 
    TestOptimizationAgent, TestIntelligenceAgent, TestCase as IntelligenceTestCase
)
from modules.discovery import TestDiscoveryAgent
from modules.report import ReportGenerator
from modules.executor.execution_engine import ExecutionEngine


def run_pipeline_v2_intelligence(
    old_swagger: str = None,
    new_swagger: str = None,
    requirement: str = None,
    base_url: str = "https://api.example.com",
    environment: str = "test",
    output_dir: str = "output"
):
    """
    运行完整测试 Pipeline V2 (Intelligence Agent 接管版)
    
    Args:
        old_swagger: 旧版 Swagger 文件(用于变更发现)
        new_swagger: 新版 Swagger 文件
        requirement: 需求文档(可选,用于从需求生成测试)
        base_url: API 基础 URL
        environment: 执行环境(test/staging/production)
        output_dir: 输出目录
    
    Returns:
        执行结果列表
    """
    print("=" * 80)
    print("🚀 开始执行测试 Pipeline V2 (Intelligence Agent 接管版)")
    print("=" * 80)
    
    pipeline_start = datetime.now()
    
    # ========== 阶段 1: Discovery Agent(发现测试点)==========
    print("\n[1/7] 🔍 Discovery Agent - 发现测试点...")
    
    test_points = []
    
    try:
        if old_swagger and new_swagger:
            # 从 Swagger 变更发现测试点
            discovery_agent = TestDiscoveryAgent()
            test_points = discovery_agent.discover_from_swagger_changes(
                old_swagger=old_swagger,
                new_swagger=new_swagger
            )
            
            print(f"  ✅ 发现了 {len(test_points)} 个高风险测试点")
            
            # 显示测试点统计
            risk_stats = {}
            for tp in test_points:
                risk = tp.risk_level.value if hasattr(tp.risk_level, 'value') else str(tp.risk_level)
                risk_stats[risk] = risk_stats.get(risk, 0) + 1
            
            print(f"  按风险等级:")
            for risk, count in sorted(risk_stats.items()):
                print(f"    {risk}: {count}")
        
        elif new_swagger:
            # 从单个 Swagger 发现所有 API
            print(f"  ℹ️  从 Swagger 发现所有 API")
            test_points = []
        
        else:
            print(f"  ℹ️  跳过 Discovery(将从需求生成测试)")
    
    except Exception as e:
        print(f"  ⚠️  Discovery 失败: {e}")
        import traceback
        traceback.print_exc()
    
    # ========== 阶段 2: Design Agent(设计测试用例)==========
    print(f"\n[2/7] 🎨 Design Agent - 设计测试用例...")
    
    try:
        # 创建 Design Agent
        design_agent = DesignAgent(config={
            'max_testcases_per_api': 5,
            'include_edge_cases': True,
            'include_error_cases': True,
            'priority_threshold': 'medium'
        })
        
        # 根据不同来源设计测试用例
        if test_points:
            # 从 Discovery 结果设计
            testcases = design_agent.design_from_discovery(test_points)
            print(f"  ✅ 从 Discovery 设计了 {len(testcases)} 个测试用例")
        
        elif requirement:
            # 从需求文档设计
            testcases = design_agent.design_from_requirement(requirement)
            print(f"  ✅ 从需求设计了 {len(testcases)} 个测试用例")
        
        elif new_swagger:
            # 从 Swagger 设计
            with open(new_swagger, 'r', encoding='utf-8') as f:
                swagger_data = json.load(f)
            
            testcases = design_agent.design_from_swagger(swagger_data)
            print(f"  ✅ 从 Swagger 设计了 {len(testcases)} 个测试用例")
        
        else:
            print(f"  ❌ 错误: 需要提供 Swagger 或需求文档")
            return None
        
        # 显示设计统计
        stats = design_agent.get_design_statistics()
        print(f"  设计统计:")
        print(f"    总设计次数: {stats['total_designs']}")
        print(f"    总测试用例: {stats['total_testcases']}")
        print(f"    平均每次: {stats['avg_testcases_per_design']:.1f}")
        
        # 按优先级统计
        priority_stats = {}
        for tc in testcases:
            p = tc.priority.value if hasattr(tc.priority, 'value') else str(tc.priority)
            priority_stats[p] = priority_stats.get(p, 0) + 1
        
        print(f"  按优先级:")
        for priority, count in sorted(priority_stats.items()):
            print(f"    {priority}: {count}")
    
    except Exception as e:
        print(f"  ❌ Design Agent 失败: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # ========== 阶段 3: Optimization Agent(优化测试用例)==========
    print(f"\n[3/7] ⚡ Optimization Agent - 优化测试用例...")
    
    try:
        # 创建 Learning Agent(用于获取高风险 API)
        learning_agent = LearningAgent(knowledge_dir="knowledge")
        
        # 创建 Optimization Agent
        optimization_agent = TestOptimizationAgent(config={
            'dedup_threshold': 0.9,
            'keep_boundary': True,
            'keep_negative': True,
            'keep_high_priority': True
        })
        
        print(f"  ⏳ 正在优化 {len(testcases)} 个测试用例...")
        
        # 执行优化
        optimization_result = optimization_agent.optimize(testcases, learning_agent)
        
        # 使用优化后的用例
        testcases = optimization_result['optimized_cases']
        
        # 显示优化统计
        opt_stats = optimization_result['statistics']
        print(f"  ✅ 优化完成")
        print(f"     原始用例: {opt_stats['original_count']}")
        print(f"     优化后: {opt_stats['optimized_count']}")
        print(f"     移除: {opt_stats['dropped_count']}")
        print(f"     减少比例: {opt_stats['reduction_rate']:.1%}")
        print(f"     预计节省时间: {optimization_result['execution_plan']['estimated_time_saved']}")
        
        # 显示覆盖率信息
        coverage = optimization_result['coverage_report']
        print(f"  覆盖率:")
        print(f"     总 API: {coverage['total_apis']}")
        print(f"     平均测试数/API: {coverage['avg_tests_per_api']:.1f}")
    
    except Exception as e:
        print(f"  ⚠️  Optimization Agent 失败: {e}")
        import traceback
        traceback.print_exc()
        # 继续使用未优化的用例
        learning_agent = LearningAgent(knowledge_dir="knowledge")
    
    # ========== 阶段 4: Intelligence Agent(智能决策执行计划)==========
    print(f"\n[4/7] 🧠 Intelligence Agent - 智能决策执行计划...")
    
    try:
        # 1. 转换为 Intelligence TestCase
        intelligence_cases = []
        for tc in testcases:
            intelligence_cases.append(IntelligenceTestCase(
                test_case_id=tc.id,
                api=getattr(tc, 'api_id', tc.id),
                module=tc.module,
                priority=tc.priority.value if hasattr(tc.priority, 'value') else str(tc.priority),
                tags=getattr(tc, 'tags', [])
            ))
        
        # 2. 使用 Intelligence Agent 生成执行计划
        intelligence_agent = TestIntelligenceAgent(learning_agent=learning_agent)
        execution_plan = intelligence_agent.optimize_execution_plan(intelligence_cases)
        
        # 显示执行计划统计
        plan_stats = execution_plan['statistics']
        print(f"  ✅ 执行计划生成完成")
        print(f"     总用例: {plan_stats['total_tests']}")
        print(f"     选中: {plan_stats['selected_tests']}")
        print(f"     跳过: {plan_stats['skipped_tests']}")
        print(f"     选择率: {plan_stats['selection_rate']}%")
        
        # 显示决策分布
        decision_breakdown = plan_stats['decision_breakdown']
        print(f"  决策分布:")
        for decision, count in decision_breakdown.items():
            print(f"    {decision}: {count}")
        
        # 保存执行计划
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        plan_file = output_path / "execution_plan.json"
        intelligence_agent.save_execution_plan(execution_plan, str(plan_file))
        print(f"  💾 执行计划已保存: {plan_file}")
    
    except Exception as e:
        print(f"  ❌ Intelligence Agent 失败: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # ========== 阶段 5: ExecutionEngine(执行测试 - 使用 execution_plan)==========
    print(f"\n[5/7] 🧪 ExecutionEngine - 执行测试(基于 execution_plan)...")
    
    try:
        # 创建 ExecutionEngine
        execution_engine = ExecutionEngine(config={
            'base_url': base_url,
            'timeout': 30,
            'max_retries': 3,
            'retry_delay': 1.0,
            'resilience_enabled': True
        })
        
        # 构建 test_cases_map
        test_cases_map = {tc.id: tc for tc in testcases}
        
        print(f"  ⏳ 正在执行测试...")
        print(f"     环境: {environment}")
        print(f"     Base URL: {base_url}")
        print(f"     🔥 执行模式: Intelligence Agent 接管")
        
        # 🔥 执行计划(由 Intelligence Agent 生成)
        results = execution_engine.execute_plan(execution_plan, test_cases_map)
        
        # 获取执行统计
        exec_stats = execution_engine.get_statistics(results)
        
        print(f"  ✅ 执行完成")
        print(f"     总执行: {exec_stats['total']}")
        print(f"     通过: {exec_stats['passed']}")
        print(f"     失败: {exec_stats['failed']}")
        print(f"     跳过: {exec_stats['skipped']}")
        print(f"     通过率: {exec_stats['pass_rate']}")
        print(f"     总耗时: {exec_stats['total_duration']}s")
        print(f"     平均耗时: {exec_stats['avg_duration']}s")
        
        # 🔥 收集所有 trace_id
        trace_ids = []
        failures_with_trace = []
        
        for result in results:
            if hasattr(result, 'trace_id') and result.trace_id:
                trace_ids.append(result.trace_id)
            
            # 收集失败用例的 trace_id
            status = result.status.value if hasattr(result.status, 'value') else str(result.status)
            if status.upper() in ['FAILED', 'ERROR']:
                failure_info = {
                    'test_case_id': result.test_case_id if hasattr(result, 'test_case_id') else 'unknown',
                    'trace_id': result.trace_id if hasattr(result, 'trace_id') else None,
                    'error_type': result.error_type if hasattr(result, 'error_type') else None,
                    'error_message': result.error if hasattr(result, 'error') else None
                }
                failures_with_trace.append(failure_info)
        
        print(f"     🔥 Trace IDs: {len(trace_ids)} 个")
        
        # 保存执行信息到统计中
        exec_stats['execution'] = {
            'engine': 'intelligence',
            'trace_ids': trace_ids,
            'failures': failures_with_trace
        }
    
    except Exception as e:
        print(f"  ❌ ExecutionEngine 失败: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # ========== 阶段 6: Healing Agent(智能自愈)==========
    print(f"\n[6/7] 🔧 Healing Agent - 智能自愈...")
    
    try:
        # 创建 Healing Agent
        healing_agent = HealingAgent(config={
            'enable_l1': True,               # L1: 重试
            'enable_l2': True,               # L2: 数据修复
            'enable_l3': True,               # L3: 断言修复
            'enable_l4': True,               # L4: 代码修复建议
            'healing_threshold': 0.3,        # 修复价值阈值
            'max_retry_count': 3,
            'auto_upgrade': True             # 失败后自动升级层级
        })
        
        # 执行智能修复(带决策能力)
        healing_records = healing_agent.heal(results)
        
        # 获取修复统计
        healing_stats = healing_agent.get_statistics()
        healing_report = healing_agent.get_healing_report()
        
        print(f"  ✅ 修复完成")
        print(f"     总用例: {healing_stats['total']}")
        print(f"     修复: {healing_stats['healed']}")
        print(f"     跳过: {healing_stats['skipped']}")
        print(f"     修复率: {healing_stats['healing_rate']:.1%}")
        print(f"     升级次数: {healing_stats['upgraded']}")
        
        # 按层级统计
        if healing_stats['healed'] > 0:
            print(f"  按修复层级:")
            for level, count in healing_stats['by_level'].items():
                if count > 0:
                    level_info = healing_report['by_level'].get(f'{level}_RETRY') or \
                                 healing_report['by_level'].get(f'{level}_DATA') or \
                                 healing_report['by_level'].get(f'{level}_TOLERANCE') or \
                                 healing_report['by_level'].get(f'{level}_MANUAL')
                    if level_info:
                        print(f"    {level}: {count} - {level_info['description']}")
        
        # 按策略统计
        if any(healing_stats['by_strategy'].values()):
            print(f"  按修复策略:")
            for strategy, count in healing_stats['by_strategy'].items():
                if count > 0:
                    print(f"    {strategy}: {count}")
    
    except Exception as e:
        print(f"  ⚠️  Healing Agent 失败: {e}")
        import traceback
        traceback.print_exc()
        healing_records = []
        healing_stats = {}
    
    # ========== 阶段 7: Report Generator(生成报告)==========
    print(f"\n[7/7] 📊 Report Generator - 生成报告...")
    
    try:
        report_generator = ReportGenerator()
        report = report_generator.generate(results)
        
        # 显示报告摘要
        print(f"\n  {'='*60}")
        print(f"  📈 测试报告摘要")
        print(f"  {'='*60}")
        print(f"  总用例: {report['summary']['total']}")
        print(f"  ✅ 通过: {report['summary']['passed']}")
        print(f"  ❌ 失败: {report['summary']['failed']}")
        print(f"  ⚠️  错误: {report['summary']['error']}")
        print(f"  通过率: {report['summary']['pass_rate']}")
        print(f"  总耗时: {report['summary']['total_duration']}s")
        print(f"  平均耗时: {report['summary']['avg_duration']}s")
        print(f"  {'='*60}")
        
        # 显示失败用例(前5个)
        if report["failures"]:
            print(f"\n  ❌ 失败用例 (前5个):")
            for f in report["failures"][:5]:
                print(f"     - {f['test_case_id']} | {f['error'][:60]}...")
            if len(report["failures"]) > 5:
                print(f"     ... 还有 {len(report['failures']) - 5} 个失败用例")
    
    except Exception as e:
        print(f"  ⚠️  报告生成失败: {e}")
        report = None
    
    # ========== 保存结果 ==========
    print(f"\n[保存] 💾 保存结果...")
    
    try:
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # 保存测试用例
        testcases_file = output_path / "testcases_intelligence.json"
        testcases_data = [
            {
                'id': tc.id,
                'title': tc.title,
                'module': tc.module,
                'priority': tc.priority.value if hasattr(tc.priority, 'value') else str(tc.priority),
                'status': tc.status.value if hasattr(tc.status, 'value') else str(tc.status)
            }
            for tc in testcases
        ]
        with open(testcases_file, 'w', encoding='utf-8') as f:
            json.dump(testcases_data, f, ensure_ascii=False, indent=2)
        
        # 保存执行结果
        if report:
            report_json_file = output_path / "report_intelligence.json"
            report_generator.save_report(results, str(report_json_file), format="json")
            
            report_html_file = output_path / "report_intelligence.html"
            report_generator.save_report(results, str(report_html_file), format="html")
        
        # 保存 Healing 记录
        if healing_records:
            healing_file = output_path / "healing_records_intelligence.json"
            with open(healing_file, 'w', encoding='utf-8') as f:
                json.dump(healing_records, f, ensure_ascii=False, indent=2)
        
        # 保存 Pipeline 摘要
        pipeline_end = datetime.now()
        pipeline_duration = (pipeline_end - pipeline_start).total_seconds()
        
        summary = {
            'pipeline_version': 'V2 Intelligence (Intelligence Agent 接管版)',
            'start_time': pipeline_start.isoformat(),
            'end_time': pipeline_end.isoformat(),
            'duration': pipeline_duration,
            'stages': {
                'discovery': {
                    'test_points': len(test_points)
                },
                'design': {
                    'testcases': len(testcases),
                    'statistics': stats
                },
                'optimization': {
                    'original_count': opt_stats.get('original_count', len(testcases)),
                    'optimized_count': opt_stats.get('optimized_count', len(testcases)),
                    'reduction_rate': opt_stats.get('reduction_rate', 0)
                } if 'opt_stats' in locals() else None,
                'intelligence': {
                    'execution_plan': execution_plan,
                    'statistics': plan_stats
                },
                'execution': {
                    'engine': 'intelligence',
                    'trace_ids': exec_stats.get('execution', {}).get('trace_ids', []),
                    'failures': exec_stats.get('execution', {}).get('failures', []),
                    'statistics': {
                        'total': exec_stats['total'],
                        'passed': exec_stats['passed'],
                        'failed': exec_stats['failed'],
                        'skipped': exec_stats['skipped'],
                        'pass_rate': exec_stats['pass_rate'],
                        'total_duration': exec_stats['total_duration'],
                        'avg_duration': exec_stats['avg_duration']
                    }
                },
                'healing': {
                    'records': len(healing_records),
                    'statistics': healing_stats
                } if healing_stats else None,
                'report': {
                    'summary': report['summary'] if report else None
                }
            }
        }
        
        summary_file = output_path / "pipeline_summary_intelligence.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"  ✅ 结果已保存到: {output_dir}/")
        print(f"     - testcases_intelligence.json")
        print(f"     - execution_plan.json")
        print(f"     - report_intelligence.json")
        print(f"     - report_intelligence.html")
        print(f"     - healing_records_intelligence.json")
        print(f"     - pipeline_summary_intelligence.json")
    
    except Exception as e:
        print(f"  ⚠️  保存结果失败: {e}")
        import traceback
        traceback.print_exc()
    
    # ========== 完成 ==========
    print(f"\n{'='*80}")
    
    if report:
        pass_rate_value = float(report['summary']['pass_rate'].rstrip('%'))
        if pass_rate_value >= 80:
            print(f"✅ Pipeline V2 Intelligence 执行成功!")
        else:
            print(f"⚠️  Pipeline V2 Intelligence 执行完成,但通过率较低")
        
        print(f"   通过率: {report['summary']['pass_rate']}")
        print(f"   总耗时: {pipeline_duration:.2f}s")
    
    if healing_stats and healing_stats.get('healed', 0) > 0:
        print(f"🔧 Healing Agent: 修复了 {healing_stats['healed']} 个用例")
    
    print(f"{'='*80}\n")
    
    return results


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='运行测试 Pipeline V2 (Intelligence Agent 接管版)')
    parser.add_argument('--old-swagger', help='旧版 Swagger 文件(用于变更发现)')
    parser.add_argument('--new-swagger', help='新版 Swagger 文件')
    parser.add_argument('--requirement', help='需求文档')
    parser.add_argument('--base-url', default='https://api.example.com', help='API 基础 URL')
    parser.add_argument('--environment', default='test', choices=['test', 'staging', 'production'], help='执行环境')
    parser.add_argument('--output', default='output', help='输出目录')
    
    args = parser.parse_args()
    
    # 验证输入
    if not (args.old_swagger or args.new_swagger or args.requirement):
        print("❌ 错误: 需要提供 --old-swagger + --new-swagger 或 --new-swagger 或 --requirement")
        sys.exit(1)
    
    # 运行 Pipeline
    results = run_pipeline_v2_intelligence(
        old_swagger=args.old_swagger,
        new_swagger=args.new_swagger,
        requirement=args.requirement,
        base_url=args.base_url,
        environment=args.environment,
        output_dir=args.output
    )
    
    if results is None:
        sys.exit(1)
    
    # 根据通过率决定退出码
    passed = sum(1 for r in results if hasattr(r, 'status') and 
                 (r.status.value if hasattr(r.status, 'value') else str(r.status)).upper() == 'PASSED')
    pass_rate = (passed / len(results) * 100) if results else 0
    
    sys.exit(0 if pass_rate >= 80 else 1)


if __name__ == "__main__":
    # 如果没有参数,使用示例运行
    if len(sys.argv) == 1:
        print("💡 使用示例运行 Pipeline V2 Intelligence\n")
        
        # 示例: 从需求生成测试
        results = run_pipeline_v2_intelligence(
            requirement="用户登录功能:支持用户名密码登录,登录成功返回token",
            base_url="https://jsonplaceholder.typicode.com",
            environment="test",
            output_dir="output"
        )
    else:
        main()
