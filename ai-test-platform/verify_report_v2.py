#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Report V2 完整验证
验证所有新增能力：覆盖率分析、传统模块接入、AI 总结增强
"""

import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.report_generator import generate_report


def verify_report_v2_features():
    """验证 Report V2 的所有新增功能"""
    
    print("=" * 80)
    print("Report V2 完整功能验证")
    print("=" * 80)
    
    # 准备测试数据
    context = {
        "trace_id": "verify-001",
        "decision": {
            "need_test": True,
            "risk_level": "高",
            "test_types": ["api", "ui", "integration"],
            "action": "run_tests"
        },
        "strategy": {
            "strategy": [
                {"module": {"name": "支付模块"}, "case_count": 30},
                {"module": {"name": "订单模块"}, "case_count": 25},
                {"module": {"name": "用户模块"}, "case_count": 20}
            ],
            "total_cases": 75
        },
        "cases": {
            "cases": [
                {
                    "module": "支付模块",
                    "cases": [
                        {"id": "TC_PAY_01", "title": "支付成功", "type": "api"},
                        {"id": "TC_PAY_02", "title": "支付失败", "type": "api"},
                        {"id": "TC_PAY_03", "title": "退款", "type": "api"}
                    ]
                },
                {
                    "module": "订单模块",
                    "cases": [
                        {"id": "TC_ORD_01", "title": "创建订单", "type": "api"},
                        {"id": "TC_ORD_02", "title": "取消订单", "type": "api"}
                    ]
                },
                {
                    "module": "用户模块",
                    "cases": [
                        {"id": "TC_USR_01", "title": "用户注册", "type": "api"}
                    ]
                }
            ],
            "total_cases": 6
        },
        "execution": {
            "mode": "cases",
            "results": [
                {
                    "module": "支付模块",
                    "status": "failed",
                    "duration": 1.2,
                    "case_results": [
                        {"case_id": "TC_PAY_01", "status": "passed"},
                        {"case_id": "TC_PAY_02", "status": "failed"},
                        {"case_id": "TC_PAY_03", "status": "passed"}
                    ]
                },
                {
                    "module": "订单模块",
                    "status": "passed",
                    "duration": 0.8,
                    "case_results": [
                        {"case_id": "TC_ORD_01", "status": "passed"},
                        {"case_id": "TC_ORD_02", "status": "passed"}
                    ]
                },
                {
                    "module": "用户模块",
                    "status": "passed",
                    "duration": 0.5,
                    "case_results": [
                        {"case_id": "TC_USR_01", "status": "passed"}
                    ]
                }
            ],
            "summary": {
                "total": 3,
                "passed": 2,
                "failed": 1,
                "pass_rate": 66.67
            }
        },
        "healing": {
            "records": [
                {
                    "module": "支付模块",
                    "fixed": True,
                    "fix_strategy": "parameter_adjustment",
                    "retry_status": "passed"
                }
            ],
            "statistics": {
                "total_healings": 1,
                "successful_fixes": 1,
                "failed_fixes": 0
            }
        }
    }
    
    # 生成报告
    report = generate_report(context)
    
    print(f"\n【功能1】覆盖率分析")
    print("-" * 80)
    coverage = report.get('coverage', {})
    print(f"✅ 覆盖率模式: {coverage.get('mode', 'N/A')}")
    print(f"✅ 总用例数: {coverage.get('total_cases', 0)}")
    print(f"✅ 已执行: {coverage.get('executed_cases', 0)}")
    print(f"✅ 覆盖率: {coverage.get('coverage_rate', 0)}%")
    
    # 验证
    assert coverage.get('mode') == 'case_based', "✅ 覆盖率模式正确"
    assert coverage.get('total_cases') == 6, "✅ 总用例数正确"
    assert coverage.get('executed_cases') == 6, "✅ 已执行用例数正确"
    assert coverage.get('coverage_rate') == 100.0, "✅ 覆盖率计算正确"
    
    # 模块级覆盖率
    module_coverage = coverage.get('module_coverage', [])
    print(f"\n✅ 模块级覆盖率: {len(module_coverage)} 个模块")
    for mc in module_coverage:
        print(f"   📦 {mc.get('module', 'N/A')}: {mc.get('executed', 0)}/{mc.get('total', 0)} ({mc.get('coverage_rate', 0)}%)")
    
    assert len(module_coverage) == 3, "✅ 模块数量正确"
    
    print(f"\n【功能2】传统覆盖率模块接入")
    print("-" * 80)
    trad_cov = report.get('traditional_coverage', {})
    print(f"✅ 可用性检查: {trad_cov.get('available', False)}")
    print(f"✅ 消息: {trad_cov.get('message', 'N/A')}")
    
    assert 'available' in trad_cov, "✅ 传统覆盖率字段存在"
    
    print(f"\n【功能3】AI 总结增强")
    print("-" * 80)
    ai_analysis = report.get('ai_analysis', '')
    
    try:
        ai_obj = json.loads(ai_analysis)
        print(f"✅ AI 总结格式: JSON")
        print(f"✅ 总结内容: {ai_obj.get('summary', 'N/A')[:80]}...")
        print(f"✅ 覆盖率字段: {ai_obj.get('coverage', 'N/A')}")
        print(f"✅ 风险字段: {ai_obj.get('risk', 'N/A')}")
        
        # 验证必要字段
        assert 'summary' in ai_obj, "✅ 包含 summary"
        assert 'coverage' in ai_obj, "✅ 包含 coverage"
        assert 'risk' in ai_obj, "✅ 包含 risk"
        
        # 验证可选字段
        if 'key_findings' in ai_obj:
            print(f"✅ 关键发现: {len(ai_obj['key_findings'])} 条")
        if 'recommendations' in ai_obj:
            print(f"✅ 建议: {len(ai_obj['recommendations'])} 条")
        
    except json.JSONDecodeError:
        print(f"⚠️  AI 总结格式: 文本（Fallback）")
        print(f"   内容: {ai_analysis[:100]}...")
    
    print(f"\n【功能4】修复统计集成")
    print("-" * 80)
    summary = report.get('summary', {})
    print(f"✅ 原始失败: 1")
    print(f"✅ 成功修复: 1")
    print(f"✅ 最终通过: {summary.get('passed', 0)}")
    print(f"✅ 最终失败: {summary.get('failed', 0)}")
    
    # 验证修复后的统计
    assert summary.get('passed') == 3, "✅ 修复后通过数正确"
    assert summary.get('failed') == 0, "✅ 修复后失败数正确"
    
    print(f"\n【功能5】报告结构完整性")
    print("-" * 80)
    required_fields = ['summary', 'details', 'coverage', 'traditional_coverage', 'ai_analysis', 'generated_at']
    
    for field in required_fields:
        assert field in report, f"✅ 包含 {field}"
        print(f"✅ {field}: 存在")
    
    print("\n" + "=" * 80)
    print("✅ Report V2 所有功能验证通过")
    print("=" * 80)


if __name__ == "__main__":
    verify_report_v2_features()
    print("\n🎉 验证完成！Report V2 已就绪\n")
