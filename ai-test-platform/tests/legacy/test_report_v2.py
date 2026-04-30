#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Report V2
验证覆盖率分析和 AI 总结增强
"""

import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.report_generator import generate_report, _analyze_coverage


def test_coverage_analysis_with_cases():
    """测试覆盖率分析 - 基于用例"""
    
    print("=" * 80)
    print("测试覆盖率分析 - 基于用例模式")
    print("=" * 80)
    
    # 准备 context 数据
    context = {
        "decision": {
            "need_test": True,
            "risk_level": "高",
            "test_types": ["api", "ui"]
        },
        "strategy": {
            "strategy": [
                {"module": {"name": "支付模块"}, "case_count": 10}
            ],
            "total_cases": 10
        },
        "cases": {
            "cases": [
                {
                    "module": "支付模块",
                    "cases": [
                        {"id": "TC_01", "title": "用例1"},
                        {"id": "TC_02", "title": "用例2"},
                        {"id": "TC_03", "title": "用例3"}
                    ]
                }
            ],
            "total_cases": 3
        },
        "execution": {
            "mode": "cases",
            "results": [
                {
                    "module": "支付模块",
                    "status": "passed",
                    "case_results": [
                        {"case_id": "TC_01", "status": "passed"},
                        {"case_id": "TC_02", "status": "passed"},
                        {"case_id": "TC_03", "status": "failed"}
                    ]
                }
            ],
            "summary": {
                "total": 1,
                "passed": 1,
                "failed": 0,
                "pass_rate": 100.0
            }
        },
        "healing": None
    }
    
    # 测试覆盖率分析
    coverage = _analyze_coverage(
        context['strategy'],
        context['cases'],
        context['execution']
    )
    
    print(f"\n✅ 覆盖率分析结果:")
    print(f"   - 模式: {coverage['mode']}")
    print(f"   - 总用例数: {coverage['total_cases']}")
    print(f"   - 已执行: {coverage['executed_cases']}")
    print(f"   - 覆盖率: {coverage['coverage_rate']}%")
    
    # 显示模块覆盖率
    print(f"\n   模块覆盖率:")
    for module_cov in coverage['module_coverage']:
        print(f"      📦 {module_cov['module']}: {module_cov['executed']}/{module_cov['total']} ({module_cov['coverage_rate']}%)")
    
    # 验证
    assert coverage['mode'] == 'case_based', "应该是 case_based 模式"
    assert coverage['total_cases'] == 3, "总用例数应该是3"
    assert coverage['executed_cases'] == 3, "已执行应该是3"
    assert coverage['coverage_rate'] == 100.0, "覆盖率应该是100%"
    
    print("\n" + "=" * 80)


def test_coverage_analysis_with_strategy():
    """测试覆盖率分析 - 基于策略"""
    
    print("\n" + "=" * 80)
    print("测试覆盖率分析 - 基于策略模式")
    print("=" * 80)
    
    # 准备 context 数据（无 cases）
    context = {
        "decision": {
            "need_test": True,
            "risk_level": "中",
            "test_types": ["api"]
        },
        "strategy": {
            "strategy": [
                {"module": {"name": "订单模块"}, "case_count": 15},
                {"module": {"name": "用户模块"}, "case_count": 10}
            ],
            "total_cases": 25
        },
        "cases": None,  # 无用例
        "execution": {
            "mode": "strategy",
            "results": [
                {"module": "订单模块", "status": "passed"},
                {"module": "用户模块", "status": "passed"}
            ],
            "summary": {
                "total": 2,
                "passed": 2,
                "failed": 0
            }
        },
        "healing": None
    }
    
    # 测试覆盖率分析
    coverage = _analyze_coverage(
        context['strategy'],
        context['cases'],
        context['execution']
    )
    
    print(f"\n✅ 覆盖率分析结果:")
    print(f"   - 模式: {coverage['mode']}")
    print(f"   - 总用例数: {coverage['total_cases']}")
    print(f"   - 已执行: {coverage['executed_cases']}")
    print(f"   - 覆盖率: {coverage['coverage_rate']}%")
    
    # 验证
    assert coverage['mode'] == 'strategy_based', "应该是 strategy_based 模式"
    assert coverage['total_cases'] == 25, "总用例数应该是25"
    assert coverage['coverage_rate'] == 100.0, "策略模式覆盖率应该是100%"
    
    print("\n" + "=" * 80)


def test_report_generation_v2():
    """测试完整报告生成 V2"""
    
    print("\n" + "=" * 80)
    print("测试完整报告生成 V2")
    print("=" * 80)
    
    # 准备完整的 context
    context = {
        "trace_id": "test-001",
        "decision": {
            "need_test": True,
            "risk_level": "高",
            "test_types": ["api", "ui", "integration"],
            "action": "run_tests"
        },
        "strategy": {
            "strategy": [
                {"module": {"name": "支付模块"}, "case_count": 10},
                {"module": {"name": "订单模块"}, "case_count": 8}
            ],
            "total_cases": 18
        },
        "cases": {
            "cases": [
                {
                    "module": "支付模块",
                    "cases": [
                        {"id": "TC_01", "title": "支付测试1"},
                        {"id": "TC_02", "title": "支付测试2"}
                    ]
                },
                {
                    "module": "订单模块",
                    "cases": [
                        {"id": "TC_03", "title": "订单测试1"}
                    ]
                }
            ],
            "total_cases": 3
        },
        "execution": {
            "mode": "cases",
            "results": [
                {
                    "module": "支付模块",
                    "status": "failed",
                    "duration": 0.5,
                    "case_results": [
                        {"case_id": "TC_01", "status": "passed"},
                        {"case_id": "TC_02", "status": "failed"}
                    ]
                },
                {
                    "module": "订单模块",
                    "status": "passed",
                    "duration": 0.3,
                    "case_results": [
                        {"case_id": "TC_03", "status": "passed"}
                    ]
                }
            ],
            "summary": {
                "total": 2,
                "passed": 1,
                "failed": 1,
                "pass_rate": 50.0
            }
        },
        "healing": {
            "records": [
                {
                    "module": "支付模块",
                    "fixed": False,
                    "fix_strategy": "retry",
                    "retry_status": "failed"
                }
            ],
            "statistics": {
                "total_healings": 1,
                "successful_fixes": 0,
                "failed_fixes": 1
            }
        }
    }
    
    # 生成报告
    report = generate_report(context)
    
    print(f"\n✅ 报告生成完成:")
    print(f"   - 状态: {report['summary']['status']}")
    print(f"   - 总数: {report['summary']['total']}")
    print(f"   - 通过: {report['summary']['passed']}")
    print(f"   - 失败: {report['summary']['failed']}")
    print(f"   - 通过率: {report['summary']['pass_rate']}%")
    
    # 验证覆盖率数据
    print(f"\n✅ 覆盖率分析:")
    coverage = report.get('coverage', {})
    print(f"   - 模式: {coverage.get('mode', 'N/A')}")
    print(f"   - 总用例数: {coverage.get('total_cases', 0)}")
    print(f"   - 已执行: {coverage.get('executed_cases', 0)}")
    print(f"   - 覆盖率: {coverage.get('coverage_rate', 0)}%")
    
    # 显示模块覆盖率
    for module_cov in coverage.get('module_coverage', []):
        print(f"      📦 {module_cov['module']}: {module_cov['coverage_rate']}%")
    
    # 验证传统覆盖率
    print(f"\n✅ 传统覆盖率:")
    trad_cov = report.get('traditional_coverage', {})
    print(f"   - 可用: {trad_cov.get('available', False)}")
    print(f"   - 消息: {trad_cov.get('message', 'N/A')}")
    
    # 验证 AI 总结
    print(f"\n✅ AI 总结:")
    ai_analysis = report.get('ai_analysis', '')
    
    # 尝试解析为 JSON
    try:
        ai_obj = json.loads(ai_analysis)
        print(f"   - 格式: JSON ✅")
        print(f"   - 总结: {ai_obj.get('summary', 'N/A')[:50]}...")
        print(f"   - 覆盖率: {ai_obj.get('coverage', 'N/A')}")
        print(f"   - 风险: {ai_obj.get('risk', 'N/A')}")
        
        if 'key_findings' in ai_obj:
            print(f"   - 关键发现: {len(ai_obj['key_findings'])}条")
        if 'recommendations' in ai_obj:
            print(f"   - 建议: {len(ai_obj['recommendations'])}条")
    except:
        print(f"   - 格式: 文本")
        print(f"   - 内容: {ai_analysis[:100]}...")
    
    # 验证必要字段
    assert 'summary' in report, "应该有 summary"
    assert 'details' in report, "应该有 details"
    assert 'coverage' in report, "应该有 coverage"
    assert 'traditional_coverage' in report, "应该有 traditional_coverage"
    assert 'ai_analysis' in report, "应该有 ai_analysis"
    
    print("\n" + "=" * 80)


def test_report_with_healing():
    """测试报告生成 - 含修复"""
    
    print("\n" + "=" * 80)
    print("测试报告生成 - 含修复")
    print("=" * 80)
    
    context = {
        "decision": {
            "need_test": True,
            "risk_level": "中",
            "test_types": ["api"]
        },
        "strategy": {
            "strategy": [{"module": {"name": "测试模块"}, "case_count": 5}],
            "total_cases": 5
        },
        "cases": {
            "cases": [
                {
                    "module": "测试模块",
                    "cases": [
                        {"id": "TC_01", "title": "测试1"},
                        {"id": "TC_02", "title": "测试2"}
                    ]
                }
            ],
            "total_cases": 2
        },
        "execution": {
            "mode": "cases",
            "results": [
                {
                    "module": "测试模块",
                    "status": "failed",
                    "case_results": [
                        {"case_id": "TC_01", "status": "passed"},
                        {"case_id": "TC_02", "status": "failed"}
                    ]
                }
            ],
            "summary": {
                "total": 1,
                "passed": 0,
                "failed": 1
            }
        },
        "healing": {
            "records": [
                {
                    "module": "测试模块",
                    "fixed": True,
                    "fix_strategy": "retry",
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
    
    report = generate_report(context)
    
    print(f"\n✅ 报告生成完成:")
    print(f"   - 状态: {report['summary']['status']}")
    print(f"   - 通过: {report['summary']['passed']}")
    print(f"   - 失败: {report['summary']['failed']}")
    
    # 验证修复后的统计
    # 原本 0 passed, 1 failed
    # 修复后应该是 1 passed, 0 failed
    assert report['summary']['passed'] == 1, "修复后应该有1个通过"
    assert report['summary']['failed'] == 0, "修复后应该没有失败"
    
    print(f"\n✅ 修复统计正确")
    
    print("\n" + "=" * 80)


def test_report_skip_scenario():
    """测试报告生成 - 跳过场景"""
    
    print("\n" + "=" * 80)
    print("测试报告生成 - 跳过场景")
    print("=" * 80)
    
    context = {
        "decision": {
            "need_test": False,
            "action": "skip",
            "reason": "仅修改注释",
            "risk_level": "低"
        },
        "strategy": None,
        "cases": None,
        "execution": None,
        "healing": None
    }
    
    report = generate_report(context)
    
    print(f"\n✅ 报告生成完成:")
    print(f"   - 状态: {report['summary']['status']}")
    print(f"   - 原因: {report['summary'].get('reason', 'N/A')}")
    
    assert report['summary']['status'] == 'skipped', "应该是 skipped 状态"
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    # 测试1: 基于用例的覆盖率分析
    test_coverage_analysis_with_cases()
    
    # 测试2: 基于策略的覆盖率分析
    test_coverage_analysis_with_strategy()
    
    # 测试3: 完整报告生成
    test_report_generation_v2()
    
    # 测试4: 含修复的报告
    test_report_with_healing()
    
    # 测试5: 跳过场景
    test_report_skip_scenario()
    
    print("\n🎉 所有测试完成！")


def test_coverage_analysis_with_strategy():
    """测试覆盖率分析 - 基于策略"""
    
    print("\n" + "=" * 80)
    print("测试覆盖率分析 - 基于策略模式")
    print("=" * 80)
    
    context = {
        "strategy": {
            "strategy": [
                {"module": {"name": "模块A"}, "case_count": 10},
                {"module": {"name": "模块B"}, "case_count": 15}
            ],
            "total_cases": 25
        },
        "cases": None,
        "execution": {
            "mode": "strategy",
            "results": [
                {"module": "模块A", "status": "passed"},
                {"module": "模块B", "status": "passed"}
            ],
            "summary": {"total": 2, "passed": 2, "failed": 0}
        }
    }
    
    coverage = _analyze_coverage(
        context['strategy'],
        context['cases'],
        context['execution']
    )
    
    print(f"\n✅ 覆盖率分析结果:")
    print(f"   - 模式: {coverage['mode']}")
    print(f"   - 总用例数: {coverage['total_cases']}")
    print(f"   - 覆盖率: {coverage['coverage_rate']}%")
    
    assert coverage['mode'] == 'strategy_based', "应该是 strategy_based 模式"
    assert coverage['coverage_rate'] == 100.0, "策略模式覆盖率应该是100%"
    
    print("\n" + "=" * 80)
