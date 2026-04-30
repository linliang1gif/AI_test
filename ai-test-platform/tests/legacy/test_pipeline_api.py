#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pipeline API 测试
测试 HTTP 接口功能
"""

import requests
import json


BASE_URL = "http://localhost:8000/api"


def test_run_pipeline_endpoint():
    """测试 Pipeline 运行接口"""
    print("\n" + "="*60)
    print("测试1: POST /pipeline/run")
    print("="*60)
    
    payload = {
        "requirement": "支付模块需要支持微信支付",
        "git_diff": "+def wechat_pay():\n+    return process_payment('wechat')",
        "context": {"priority": "P0"}
    }
    
    response = requests.post(f"{BASE_URL}/pipeline/run", json=payload)
    print(f"状态码: {response.status_code}")
    
    assert response.status_code == 200, f"应该返回200，实际: {response.status_code}"
    
    data = response.json()
    print(f"\n响应数据:")
    print(f"   Trace ID: {data['trace_id']}")
    print(f"   需要测试: {data['decision']['need_test']}")
    print(f"   策略模块数: {len(data.get('strategy', {}).get('strategy', []))}")
    print(f"   报告状态: {data['report']['summary']['status']}")
    print(f"   总耗时: {data['total_duration']}s")
    
    assert 'trace_id' in data, "应该包含 trace_id"
    assert 'decision' in data, "应该包含决策"
    assert 'report' in data, "应该包含报告"
    assert 'timeline' in data, "应该包含时间线"
    
    # 检查 timeline
    print(f"\n   Timeline:")
    for step in data['timeline']:
        print(f"      {step['stage']:15s} - {step['duration']}s")
    
    print("\n✅ 测试1通过: Pipeline 运行接口正常")
    
    return data['trace_id']  # 返回 trace_id 供后续测试使用


def test_history_endpoint():
    """测试历史记录接口"""
    print("\n" + "="*60)
    print("测试2: GET /pipeline/history")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/pipeline/history?limit=5")
    print(f"状态码: {response.status_code}")
    
    assert response.status_code == 200, "应该返回200"
    
    data = response.json()
    print(f"历史记录数: {data['count']}")
    
    assert data['success'] == True, "应该成功"
    assert 'data' in data, "应该包含数据"
    assert data['count'] > 0, "应该有历史记录"
    
    print("\n✅ 测试2通过: 历史记录接口正常")


def test_statistics_endpoint():
    """测试统计信息接口"""
    print("\n" + "="*60)
    print("测试3: GET /pipeline/statistics")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/pipeline/statistics")
    print(f"状态码: {response.status_code}")
    
    assert response.status_code == 200, "应该返回200"
    
    data = response.json()
    stats = data['data']
    
    print(f"\n统计信息:")
    print(f"   总 Pipeline 数: {stats['total_pipelines']}")
    print(f"   跳过执行: {stats['skipped']}")
    print(f"   实际执行: {stats['executed']}")
    print(f"   平均耗时: {stats['avg_duration']}s")
    print(f"   成功率: {stats['success_rate']}%")
    
    assert 'total_pipelines' in stats, "应该包含总数"
    assert 'success_rate' in stats, "应该包含成功率"
    
    print("\n✅ 测试3通过: 统计信息接口正常")


def test_health_endpoint():
    """测试健康检查接口"""
    print("\n" + "="*60)
    print("测试4: GET /pipeline/health")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/pipeline/health")
    print(f"状态码: {response.status_code}")
    
    assert response.status_code == 200, "应该返回200"
    
    data = response.json()
    print(f"健康状态: {data['status']}")
    print(f"Pipeline 记录数: {data['pipelines_count']}")
    
    assert data['status'] == 'healthy', "状态应该为 healthy"
    
    print("\n✅ 测试4通过: 健康检查接口正常")


def test_trace_endpoint(trace_id: str):
    """测试 trace 查询接口"""
    print("\n" + "="*60)
    print("测试5: GET /pipeline/trace/{trace_id}")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/pipeline/trace/{trace_id}")
    print(f"状态码: {response.status_code}")
    
    assert response.status_code == 200, "应该返回200"
    
    data = response.json()
    print(f"查询成功: {data['success']}")
    print(f"Trace ID: {data['data']['trace_id']}")
    
    assert data['success'] == True, "应该成功"
    assert data['data']['trace_id'] == trace_id, "trace_id 应该匹配"
    
    print("\n✅ 测试5通过: Trace 查询接口正常")


def run_all_tests():
    """运行所有API测试"""
    print("\n" + "="*60)
    print("🧪 Pipeline API 测试")
    print("="*60)
    
    try:
        trace_id = test_run_pipeline_endpoint()
        test_history_endpoint()
        test_statistics_endpoint()
        test_health_endpoint()
        test_trace_endpoint(trace_id)
        
        print("\n" + "="*60)
        print("✅ 所有API测试通过！(5/5)")
        print("="*60)
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return False
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 连接失败: 请确保后端服务器运行在 {BASE_URL}")
        return False
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
