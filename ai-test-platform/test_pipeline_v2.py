#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Pipeline V2
验证基于 context 的流程编排
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.pipeline_service import get_pipeline_service


def test_pipeline_v2_with_case_generator():
    """测试 Pipeline V2 - 启用 Case Generator"""
    
    print("=" * 80)
    print("测试 Pipeline V2 - 启用 Case Generator")
    print("=" * 80)
    
    input_data = {
        "requirement": """
需求：用户管理模块升级
1. 新增用户批量导入功能
2. 优化用户查询性能
3. 增加用户操作日志
""",
        "git_diff": """
diff --git a/user/service.py b/user/service.py
+ def batch_import_users(file_path):
+     # 批量导入用户
""",
        "use_case_generator": True  # 启用 Case Generator
    }
    
    pipeline_service = get_pipeline_service()
    result = pipeline_service.run_pipeline(input_data)
    
    print(f"\n✅ Pipeline V2 执行完成:")
    print(f"   - Trace ID: {result['trace_id']}")
    print(f"   - 总耗时: {result.get('total_duration', 0)}秒")
    print(f"   - 阶段数: {len(result['timeline'])}")
    
    # 验证各阶段
    print(f"\n📊 各阶段执行情况:")
    for stage in result['timeline']:
        status_icon = "✅" if stage['status'] == 'completed' else "❌"
        print(f"   {status_icon} {stage['stage']}: {stage['duration']}秒 ({stage['status']})")
    
    # 验证 context 数据
    print(f"\n📦 Context 数据:")
    print(f"   - decision: {'✅' if result.get('decision') else '❌'}")
    print(f"   - strategy: {'✅' if result.get('strategy') else '❌'}")
    print(f"   - cases: {'✅' if result.get('cases') else '❌'}")
    print(f"   - execution: {'✅' if result.get('execution') else '❌'}")
    print(f"   - healing: {'✅' if result.get('healing') else '⏭️  (跳过)'}")
    print(f"   - report: {'✅' if result.get('report') else '❌'}")
    
    # 验证 Case Generator 被调用
    if result.get('cases'):
        print(f"\n✅ Case Generator 已执行:")
        print(f"   - 模块数: {len(result['cases'].get('cases', []))}")
        print(f"   - 总用例数: {result['cases'].get('total_cases', 0)}")
    
    # 验证 Orchestrator 使用了 cases
    if result.get('execution'):
        exec_mode = result['execution'].get('mode', 'unknown')
        print(f"\n✅ Orchestrator 执行模式: {exec_mode}")
        if exec_mode == 'cases':
            print(f"   ✅ 使用了 Case Generator 的用例")
    
    print("\n" + "=" * 80)


def test_pipeline_v2_without_case_generator():
    """测试 Pipeline V2 - 禁用 Case Generator"""
    
    print("\n" + "=" * 80)
    print("测试 Pipeline V2 - 禁用 Case Generator")
    print("=" * 80)
    
    input_data = {
        "requirement": """
需求：订单模块优化
1. 优化订单查询性能
""",
        "git_diff": """
diff --git a/order/service.py b/order/service.py
+ def optimize_query():
+     # 优化查询
""",
        "use_case_generator": False  # 禁用 Case Generator
    }
    
    pipeline_service = get_pipeline_service()
    result = pipeline_service.run_pipeline(input_data)
    
    print(f"\n✅ Pipeline V2 执行完成:")
    print(f"   - Trace ID: {result['trace_id']}")
    print(f"   - 总耗时: {result.get('total_duration', 0)}秒")
    
    # 验证 Case Generator 被跳过
    case_stage = next((s for s in result['timeline'] if s['stage'] == 'case_generator'), None)
    
    if case_stage is None:
        print(f"\n✅ Case Generator 已跳过（符合预期）")
    else:
        print(f"\n❌ Case Generator 不应该执行")
    
    # 验证 Orchestrator 使用了 strategy
    if result.get('execution'):
        exec_mode = result['execution'].get('mode', 'unknown')
        print(f"\n✅ Orchestrator 执行模式: {exec_mode}")
        if exec_mode == 'strategy':
            print(f"   ✅ 使用了 Strategy 模式（符合预期）")
    
    print("\n" + "=" * 80)


def test_pipeline_v2_skip_scenario():
    """测试 Pipeline V2 - 跳过场景"""
    
    print("\n" + "=" * 80)
    print("测试 Pipeline V2 - 跳过场景")
    print("=" * 80)
    
    input_data = {
        "requirement": "修改注释",
        "git_diff": """
diff --git a/utils.py b/utils.py
- # old comment
+ # new comment
""",
        "use_case_generator": True
    }
    
    pipeline_service = get_pipeline_service()
    result = pipeline_service.run_pipeline(input_data)
    
    print(f"\n✅ Pipeline V2 执行完成:")
    print(f"   - Trace ID: {result['trace_id']}")
    
    # 验证提前退出
    decision = result.get('decision', {})
    if not decision.get('need_test', True):
        print(f"\n✅ 提前退出（符合预期）:")
        print(f"   - 原因: {decision.get('reason', '无需测试')}")
        
        # 验证后续阶段被跳过
        stage_names = [s['stage'] for s in result['timeline']]
        print(f"\n✅ 执行的阶段: {', '.join(stage_names)}")
        
        if 'orchestrator' not in stage_names:
            print(f"   ✅ Orchestrator 已跳过（符合预期）")
    
    print("\n" + "=" * 80)


def test_pipeline_v2_statistics():
    """测试 Pipeline V2 - 统计信息"""
    
    print("\n" + "=" * 80)
    print("测试 Pipeline V2 - 统计信息")
    print("=" * 80)
    
    pipeline_service = get_pipeline_service()
    stats = pipeline_service.get_statistics()
    
    print(f"\n✅ 统计信息:")
    print(f"   - 总执行次数: {stats['total_pipelines']}")
    print(f"   - 跳过次数: {stats['skipped']}")
    print(f"   - 实际执行: {stats['executed']}")
    print(f"   - 平均耗时: {stats['avg_duration']}秒")
    print(f"   - 成功率: {stats['success_rate']}%")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    # 测试1: 启用 Case Generator
    test_pipeline_v2_with_case_generator()
    
    # 测试2: 禁用 Case Generator
    test_pipeline_v2_without_case_generator()
    
    # 测试3: 跳过场景
    test_pipeline_v2_skip_scenario()
    
    # 测试4: 统计信息
    test_pipeline_v2_statistics()
    
    print("\n🎉 所有测试完成！")
