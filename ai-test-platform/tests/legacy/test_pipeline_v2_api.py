#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Pipeline V2 API
验证 API 端点支持 use_case_generator 参数
"""

import requests
import json

BASE_URL = "http://localhost:8000/api"


def test_pipeline_v2_api_with_case_generator():
    """测试 Pipeline V2 API - 启用 Case Generator"""
    
    print("=" * 80)
    print("测试 Pipeline V2 API - 启用 Case Generator")
    print("=" * 80)
    
    payload = {
        "requirement": """
需求：商品管理模块优化
1. 新增商品批量上架功能
2. 优化商品搜索性能
""",
        "git_diff": """
diff --git a/product/service.py b/product/service.py
+ def batch_publish_products(product_ids):
+     # 批量上架商品
""",
        "use_case_generator": True  # 启用 Case Generator
    }
    
    print(f"\n📤 发送请求...")
    response = requests.post(f"{BASE_URL}/pipeline/run", json=payload)
    
    print(f"   状态码: {response.status_code}")
    
    if response.status_code != 200:
        print(f"   ❌ 请求失败: {response.text}")
        return
    
    result = response.json()
    
    print(f"\n✅ Pipeline V2 执行完成:")
    print(f"   - Trace ID: {result['trace_id']}")
    print(f"   - 总耗时: {result.get('total_duration', 0)}秒")
    print(f"   - 阶段数: {len(result['timeline'])}")
    
    # 验证各阶段
    print(f"\n📊 各阶段执行情况:")
    for stage in result['timeline']:
        status_icon = "✅" if stage['status'] == 'completed' else "❌"
        print(f"   {status_icon} {stage['stage']}: {stage['duration']}秒")
    
    # 验证 Case Generator 被执行
    case_stage = next((s for s in result['timeline'] if s['stage'] == 'case_generator'), None)
    
    if case_stage:
        print(f"\n✅ Case Generator 已执行:")
        if result.get('cases'):
            print(f"   - 模块数: {len(result['cases'].get('cases', []))}")
            print(f"   - 总用例数: {result['cases'].get('total_cases', 0)}")
    else:
        print(f"\n❌ Case Generator 未执行（不符合预期）")
    
    # 验证 Orchestrator 模式
    if result.get('execution'):
        exec_mode = result['execution'].get('mode', 'unknown')
        print(f"\n✅ Orchestrator 执行模式: {exec_mode}")
        if exec_mode == 'cases':
            print(f"   ✅ 使用了 Case Generator 的用例（符合预期）")
    
    print("\n" + "=" * 80)


def test_pipeline_v2_api_without_case_generator():
    """测试 Pipeline V2 API - 禁用 Case Generator"""
    
    print("\n" + "=" * 80)
    print("测试 Pipeline V2 API - 禁用 Case Generator")
    print("=" * 80)
    
    payload = {
        "requirement": """
需求：库存管理优化
1. 优化库存查询性能
""",
        "git_diff": """
diff --git a/inventory/service.py b/inventory/service.py
+ def optimize_query():
+     # 优化查询
""",
        "use_case_generator": False  # 禁用 Case Generator
    }
    
    print(f"\n📤 发送请求...")
    response = requests.post(f"{BASE_URL}/pipeline/run", json=payload)
    
    print(f"   状态码: {response.status_code}")
    
    if response.status_code != 200:
        print(f"   ❌ 请求失败: {response.text}")
        return
    
    result = response.json()
    
    print(f"\n✅ Pipeline V2 执行完成:")
    print(f"   - Trace ID: {result['trace_id']}")
    print(f"   - 总耗时: {result.get('total_duration', 0)}秒")
    
    # 验证 Case Generator 被跳过
    case_stage = next((s for s in result['timeline'] if s['stage'] == 'case_generator'), None)
    
    if case_stage is None:
        print(f"\n✅ Case Generator 已跳过（符合预期）")
    else:
        print(f"\n❌ Case Generator 不应该执行")
    
    # 验证 Orchestrator 使用策略模式
    if result.get('execution'):
        exec_mode = result['execution'].get('mode', 'unknown')
        print(f"\n✅ Orchestrator 执行模式: {exec_mode}")
        if exec_mode == 'strategy':
            print(f"   ✅ 使用了 Strategy 模式（符合预期）")
    
    print("\n" + "=" * 80)


def test_pipeline_v2_api_health():
    """测试 Pipeline V2 API - 健康检查"""
    
    print("\n" + "=" * 80)
    print("测试 Pipeline V2 API - 健康检查")
    print("=" * 80)
    
    response = requests.get(f"{BASE_URL}/pipeline/health")
    
    if response.status_code == 200:
        health = response.json()
        print(f"\n✅ 健康状态: {health['status']}")
        print(f"   - Pipeline 执行次数: {health['pipelines_count']}")
    else:
        print(f"\n❌ 健康检查失败")
    
    print("\n" + "=" * 80)


def test_pipeline_v2_api_statistics():
    """测试 Pipeline V2 API - 统计信息"""
    
    print("\n" + "=" * 80)
    print("测试 Pipeline V2 API - 统计信息")
    print("=" * 80)
    
    response = requests.get(f"{BASE_URL}/pipeline/statistics")
    
    if response.status_code == 200:
        result = response.json()
        stats = result['data']
        
        print(f"\n✅ 统计信息:")
        print(f"   - 总执行次数: {stats['total_pipelines']}")
        print(f"   - 跳过次数: {stats['skipped']}")
        print(f"   - 实际执行: {stats['executed']}")
        print(f"   - 平均耗时: {stats['avg_duration']}秒")
        print(f"   - 成功率: {stats['success_rate']}%")
    else:
        print(f"\n❌ 获取统计失败")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        # 测试1: 启用 Case Generator
        test_pipeline_v2_api_with_case_generator()
        
        # 测试2: 禁用 Case Generator
        test_pipeline_v2_api_without_case_generator()
        
        # 测试3: 健康检查
        test_pipeline_v2_api_health()
        
        # 测试4: 统计信息
        test_pipeline_v2_api_statistics()
        
        print("\n🎉 所有 API 测试完成！")
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务器")
        print("   请确保后端服务器正在运行: python backend_api_server.py")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
