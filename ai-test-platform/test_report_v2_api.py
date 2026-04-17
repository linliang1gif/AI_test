#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Report V2 API 集成
验证覆盖率数据是否正确返回
"""

import requests
import json

BASE_URL = "http://localhost:8000/api"


def test_report_v2_coverage_in_pipeline():
    """测试 Pipeline API 返回的报告中是否包含覆盖率数据"""
    
    print("=" * 80)
    print("测试 Report V2 - 覆盖率数据在 Pipeline API 中")
    print("=" * 80)
    
    # 准备请求数据
    payload = {
        "requirement": """
需求：电商系统支付功能
1. 支付模块
   - 支付接口
   - 退款接口
""",
        "git_diff": """
+ def process_payment(amount):
+     return {"status": "success"}
""",
        "priority": "P0",
        "use_case_generator": True  # 启用 Case Generator
    }
    
    print(f"\n📤 发送请求...")
    response = requests.post(f"{BASE_URL}/pipeline/run", json=payload, timeout=120)
    
    print(f"   状态码: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ 请求失败: {response.text}")
        return
    
    result = response.json()
    
    # 验证报告结构
    report = result.get('report', {})
    
    print(f"\n✅ 报告数据:")
    print(f"   - 状态: {report.get('summary', {}).get('status', 'N/A')}")
    
    # 验证覆盖率数据（新增）
    coverage = report.get('coverage', {})
    
    print(f"\n✅ 覆盖率数据:")
    print(f"   - 模式: {coverage.get('mode', 'N/A')}")
    print(f"   - 总用例数: {coverage.get('total_cases', 0)}")
    print(f"   - 已执行: {coverage.get('executed_cases', 0)}")
    print(f"   - 覆盖率: {coverage.get('coverage_rate', 0)}%")
    
    # 显示模块覆盖率
    module_coverage = coverage.get('module_coverage', [])
    if module_coverage:
        print(f"\n   模块覆盖率:")
        for mc in module_coverage:
            print(f"      📦 {mc.get('module', 'N/A')}: {mc.get('coverage_rate', 0)}%")
    
    # 验证传统覆盖率
    trad_cov = report.get('traditional_coverage', {})
    print(f"\n✅ 传统覆盖率:")
    print(f"   - 可用: {trad_cov.get('available', False)}")
    
    # 验证 AI 总结
    ai_analysis = report.get('ai_analysis', '')
    print(f"\n✅ AI 总结:")
    
    try:
        ai_obj = json.loads(ai_analysis)
        print(f"   - 格式: JSON ✅")
        print(f"   - 总结: {ai_obj.get('summary', 'N/A')[:60]}...")
        print(f"   - 覆盖率: {ai_obj.get('coverage', 'N/A')}")
        print(f"   - 风险: {ai_obj.get('risk', 'N/A')}")
        
        # 验证必要字段
        assert 'summary' in ai_obj, "AI 总结应该包含 summary"
        assert 'coverage' in ai_obj, "AI 总结应该包含 coverage"
        assert 'risk' in ai_obj, "AI 总结应该包含 risk"
        
    except json.JSONDecodeError:
        print(f"   - 格式: 文本")
        print(f"   - 内容: {ai_analysis[:80]}...")
    
    # 验证必要字段存在
    assert 'coverage' in report, "报告应该包含 coverage 字段"
    assert 'traditional_coverage' in report, "报告应该包含 traditional_coverage 字段"
    assert 'ai_analysis' in report, "报告应该包含 ai_analysis 字段"
    
    # 验证覆盖率数据结构
    assert coverage.get('mode') in ['case_based', 'strategy_based'], "覆盖率模式应该是 case_based 或 strategy_based"
    assert coverage.get('total_cases', 0) > 0, "总用例数应该大于0"
    assert coverage.get('coverage_rate', 0) >= 0, "覆盖率应该大于等于0"
    
    print(f"\n✅ 所有验证通过")
    print("=" * 80)


def test_report_v2_with_strategy_mode():
    """测试 Report V2 - 策略模式（不使用 Case Generator）"""
    
    print("\n" + "=" * 80)
    print("测试 Report V2 - 策略模式覆盖率")
    print("=" * 80)
    
    payload = {
        "requirement": """
需求：用户管理功能
1. 用户模块
   - 用户注册
   - 用户登录
""",
        "git_diff": """
+ def register_user(username):
+     return {"status": "success"}
""",
        "priority": "P1",
        "use_case_generator": False  # 禁用 Case Generator，使用策略模式
    }
    
    print(f"\n📤 发送请求...")
    response = requests.post(f"{BASE_URL}/pipeline/run", json=payload, timeout=120)
    
    print(f"   状态码: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ 请求失败: {response.text}")
        return
    
    result = response.json()
    report = result.get('report', {})
    
    print(f"\n✅ 报告数据:")
    print(f"   - 状态: {report.get('summary', {}).get('status', 'N/A')}")
    
    # 验证覆盖率数据（策略模式）
    coverage = report.get('coverage', {})
    print(f"\n✅ 覆盖率数据:")
    print(f"   - 模式: {coverage.get('mode', 'N/A')}")
    print(f"   - 总用例数: {coverage.get('total_cases', 0)}")
    print(f"   - 覆盖率: {coverage.get('coverage_rate', 0)}%")
    
    # 验证策略模式
    assert coverage.get('mode') == 'strategy_based', "应该是 strategy_based 模式"
    assert coverage.get('coverage_rate') == 100.0, "策略模式覆盖率应该是 100%"
    
    print(f"\n✅ 策略模式覆盖率验证通过")
    print("=" * 80)


if __name__ == "__main__":
    print("\n🚀 开始测试 Report V2 API 集成\n")
    
    # 测试1: 覆盖率数据在 Pipeline API 中（Case Generator 模式）
    test_report_v2_coverage_in_pipeline()
    
    # 测试2: 策略模式覆盖率
    test_report_v2_with_strategy_mode()
    
    print("\n🎉 所有 API 测试完成！\n")
