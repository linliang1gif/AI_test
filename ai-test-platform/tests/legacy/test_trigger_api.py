#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试执行触发API
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_trigger_simple():
    """测试简化触发API"""
    print("\n测试简化触发API...")
    
    url = f"{BASE_URL}/api/v2/execution/trigger-simple"
    params = {
        "project_id": 1,
        "environment_id": 1,
        "test_case_ids": ["TC_TEST_001", "TC_TEST_002"]
    }
    
    response = requests.post(url, params=params)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 执行成功!")
        print(f"  Run ID: {result['run_id']}")
        print(f"  Trace ID: {result['trace_id']}")
        print(f"  状态: {result['status']}")
        print(f"  消息: {result['message']}")
        return result['run_id']
    else:
        print(f"❌ 执行失败: {response.text}")
        return None


def test_get_run_detail(run_id):
    """测试获取执行详情"""
    print(f"\n测试获取执行详情: {run_id}...")
    
    url = f"{BASE_URL}/api/v2/observability/runs/{run_id}"
    response = requests.get(url)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 获取成功!")
        data = result['data']
        print(f"  状态: {data['status']}")
        print(f"  总用例: {data['total_cases']}")
        print(f"  通过: {data['passed_cases']}")
        print(f"  失败: {data['failed_cases']}")
    else:
        print(f"❌ 获取失败: {response.text}")


if __name__ == '__main__':
    # 测试触发
    run_id = test_trigger_simple()
    
    # 测试获取详情
    if run_id:
        test_get_run_detail(run_id)
