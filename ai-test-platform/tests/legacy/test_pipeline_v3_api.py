#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Pipeline V3 API - 使用 TestContext
"""

import requests
import json

BASE_URL = "http://localhost:8000/api"


def test_pipeline_v3_api_response_structure():
    """测试 Pipeline V3 API 响应结构"""
    
    print("=" * 80)
    print("测试 Pipeline V3 API - TestContext 响应结构")
    print("=" * 80)
    
    payload = {
        "requirement": """
需求：支付系统
1. 支付模块
   - 支付接口
   - 退款接口
""",
        "git_diff": "+ def pay(): pass",
        "priority": "P0",
        "use_case_generator": True
    }
    
    print(f"\n📤 发送请求...")
    response = requests.post(f"{BASE_URL}/pipeline/run", json=payload, timeout=120)
    
    print(f"   状态码: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ 请求失败: {response.text}")
        return
    
    result = response.json()
    
    # 验证 TestContext 结构
    print(f"\n✅ TestContext 字段验证:")
    
    required_fields = [
        'trace_id', 'requirement', 'git_diff', 'priority',
        'use_case_generator', 'decision', 'strategy', 'cases',
        'execution', 'healing', 'report', 'timeline', 'created_at'
    ]
    
    for field in required_fields:
        exists = field in result
        status = "✅" if exists else "❌"
        print(f"   {status} {field}: {'存在' if exists else '缺失'}")
        assert exists, f"应该包含 {field}"
    
    # 验证 trace_id 格式
    trace_id = result.get('trace_id', '')
    print(f"\n✅ Trace ID: {trace_id}")
    assert len(trace_id) == 8, "Trace ID 应该是 8 位"
    
    # 验证时间线
    timeline = result.get('timeline', [])
    print(f"\n✅ 时间线: {len(timeline)} 个事件")
    
    for event in timeline:
        print(f"   📍 {event['stage']}: {event['status']} ({event.get('duration', 0)}s)")
    
    # 验证 Report V2 数据
    report = result.get('report', {})
    coverage = report.get('coverage', {})
    
    print(f"\n✅ Report V2 覆盖率:")
    print(f"   - 模式: {coverage.get('mode', 'N/A')}")
    print(f"   - 覆盖率: {coverage.get('coverage_rate', 0)}%")
    
    assert 'coverage' in report, "Report 应该包含 coverage"
    assert 'ai_analysis' in report, "Report 应该包含 ai_analysis"
    
    print("\n" + "=" * 80)


def test_pipeline_v3_api_backward_compatibility():
    """测试 Pipeline V3 API 向后兼容性"""
    
    print("\n" + "=" * 80)
    print("测试 Pipeline V3 API - 向后兼容性")
    print("=" * 80)
    
    # 使用旧的请求格式（不包含 priority）
    payload = {
        "requirement": "简单测试",
        "git_diff": "+ def test(): pass"
    }
    
    print(f"\n📤 发送请求（旧格式）...")
    response = requests.post(f"{BASE_URL}/pipeline/run", json=payload, timeout=120)
    
    print(f"   状态码: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ 请求失败: {response.text}")
        return
    
    result = response.json()
    
    # 验证默认值
    print(f"\n✅ 默认值验证:")
    print(f"   - Priority: {result.get('priority', 'N/A')}")
    print(f"   - Use Case Generator: {result.get('use_case_generator', 'N/A')}")
    
    # 应该使用默认值
    assert result.get('priority') in ['P0', 'P1', 'P2'], "应该有默认 priority"
    
    print(f"\n✅ 向后兼容性验证通过")
    print("=" * 80)


def test_pipeline_v3_api_statistics():
    """测试 Pipeline V3 API 统计信息"""
    
    print("\n" + "=" * 80)
    print("测试 Pipeline V3 API - 统计信息")
    print("=" * 80)
    
    print(f"\n📤 获取统计信息...")
    response = requests.get(f"{BASE_URL}/pipeline/statistics")
    
    print(f"   状态码: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ 请求失败: {response.text}")
        return
    
    stats = response.json()
    
    print(f"\n✅ 统计信息:")
    print(f"   - 总执行次数: {stats.get('total_pipelines', 0)}")
    print(f"   - 跳过次数: {stats.get('skipped', 0)}")
    print(f"   - 实际执行: {stats.get('executed', 0)}")
    print(f"   - 平均耗时: {stats.get('avg_duration', 0)}s")
    print(f"   - 成功率: {stats.get('success_rate', 0)}%")
    
    assert 'total_pipelines' in stats, "应该包含 total_pipelines"
    assert stats.get('total_pipelines', 0) >= 2, "应该至少有 2 次执行"
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    print("\n🚀 开始测试 Pipeline V3 API\n")
    
    # 测试1: TestContext 响应结构
    test_pipeline_v3_api_response_structure()
    
    # 测试2: 向后兼容性
    test_pipeline_v3_api_backward_compatibility()
    
    # 测试3: 统计信息
    test_pipeline_v3_api_statistics()
    
    print("\n🎉 所有 API 测试完成！Pipeline V3 已就绪\n")
