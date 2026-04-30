#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证完整集成
测试传统流程能力层完全集成到五阶段 AI 系统

验证点：
1. Agent V3：需求解析 ✅
2. Strategy：策略生成 ✅
3. Case Generator：用例生成 ✅
4. Orchestrator V2：基于用例执行 ✅
5. Pipeline V2：统一编排 ✅
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.pipeline_service import get_pipeline_service


def test_complete_integration():
    """测试完整集成"""
    
    print("=" * 80)
    print("验证完整集成：传统流程能力层 → 五阶段 AI 系统")
    print("=" * 80)
    
    # 准备测试数据
    input_data = {
        "requirement": """
需求：电商平台核心功能升级

一、商品管理模块
1. 商品批量导入功能
2. 商品分类管理优化
3. 商品库存预警

二、订单管理模块
1. 订单批量处理
2. 订单状态流转优化
3. 订单超时自动取消

三、支付管理模块
1. 支付接口性能优化
2. 支付重试机制
3. 支付结果通知
""",
        "git_diff": """
diff --git a/product/service.py b/product/service.py
+ def batch_import_products(file_path):
+     # 批量导入商品

diff --git a/order/service.py b/order/service.py
+ def batch_process_orders(order_ids):
+     # 批量处理订单

diff --git a/payment/service.py b/payment/service.py
+ def retry_payment(order_id):
+     # 支付重试
""",
        "use_case_generator": True
    }
    
    # 执行 Pipeline
    pipeline_service = get_pipeline_service()
    result = pipeline_service.run_pipeline(input_data)
    
    # ==================== 验证点1: Agent V3 需求解析 ====================
    print(f"\n【验证点1】Agent V3 - 需求解析")
    print("-" * 80)
    
    decision = result.get('decision', {})
    parsed_modules = decision.get('parsed_modules', [])
    
    print(f"   ✅ 需求解析:")
    print(f"      - 解析模块数: {len(parsed_modules)}")
    
    for module in parsed_modules[:5]:
        print(f"      • {module.get('name', '未知')}")
    
    assert len(parsed_modules) > 0, "应该解析出模块"
    
    # ==================== 验证点2: Strategy 策略生成 ====================
    print(f"\n【验证点2】Strategy Engine - 策略生成")
    print("-" * 80)
    
    strategy = result.get('strategy', {})
    strategy_list = strategy.get('strategy', [])
    
    print(f"   ✅ 策略生成:")
    print(f"      - 策略数: {len(strategy_list)}")
    print(f"      - 总用例数: {strategy.get('total_cases', 0)}")
    
    assert len(strategy_list) > 0, "应该生成策略"
    
    # ==================== 验证点3: Case Generator 用例生成 ====================
    print(f"\n【验证点3】Case Generator - 用例生成")
    print("-" * 80)
    
    cases = result.get('cases', {})
    case_list = cases.get('cases', [])
    
    print(f"   ✅ 用例生成:")
    print(f"      - 模块数: {len(case_list)}")
    print(f"      - 总用例数: {cases.get('total_cases', 0)}")
    
    # 显示用例详情
    for module_cases in case_list[:3]:
        module_name = module_cases.get('module', '未知')
        module_case_list = module_cases.get('cases', [])
        print(f"      📦 {module_name}: {len(module_case_list)}个用例")
    
    assert len(case_list) > 0, "应该生成用例"
    assert cases.get('total_cases', 0) > 0, "总用例数应该大于0"
    
    # ==================== 验证点4: Orchestrator V2 基于用例执行 ====================
    print(f"\n【验证点4】Orchestrator V2 - 基于用例执行")
    print("-" * 80)
    
    execution = result.get('execution', {})
    exec_mode = execution.get('mode', 'unknown')
    exec_results = execution.get('results', [])
    
    print(f"   ✅ 执行调度:")
    print(f"      - 执行模式: {exec_mode}")
    print(f"      - 模块数: {len(exec_results)}")
    
    # 验证用例级别结果
    has_case_results = False
    for module_result in exec_results:
        case_results = module_result.get('case_results', [])
        if case_results:
            has_case_results = True
            print(f"      📦 {module_result['module']}: {len(case_results)}个用例执行")
    
    assert exec_mode == 'cases', "应该使用 cases 模式"
    assert has_case_results, "应该有用例级别的结果"
    
    # ==================== 验证点5: Pipeline V2 统一编排 ====================
    print(f"\n【验证点5】Pipeline V2 - 统一编排")
    print("-" * 80)
    
    timeline = result.get('timeline', [])
    stage_names = [s['stage'] for s in timeline]
    
    print(f"   ✅ 流程编排:")
    print(f"      - 阶段数: {len(timeline)}")
    print(f"      - 阶段列表: {' → '.join(stage_names)}")
    
    # 验证必要阶段
    required_stages = ['agent', 'strategy', 'case_generator', 'orchestrator', 'report']
    for stage in required_stages:
        if stage in stage_names:
            print(f"      ✅ {stage}")
        else:
            print(f"      ❌ {stage} (缺失)")
    
    assert 'agent' in stage_names, "应该有 agent 阶段"
    assert 'strategy' in stage_names, "应该有 strategy 阶段"
    assert 'case_generator' in stage_names, "应该有 case_generator 阶段"
    assert 'orchestrator' in stage_names, "应该有 orchestrator 阶段"
    assert 'report' in stage_names, "应该有 report 阶段"
    
    # ==================== 总结 ====================
    print(f"\n" + "=" * 80)
    print(f"✅ 完整集成验证通过")
    print(f"=" * 80)
    print(f"   ✅ Agent V3：需求解析 + AI 决策")
    print(f"   ✅ Strategy：策略生成")
    print(f"   ✅ Case Generator：用例生成")
    print(f"   ✅ Orchestrator V2：基于用例执行")
    print(f"   ✅ Pipeline V2：统一编排")
    print(f"\n   🎯 传统流程能力层已完全集成到五阶段 AI 系统")
    print(f"=" * 80)


if __name__ == "__main__":
    test_complete_integration()
    print("\n🎉 验证完成！")
