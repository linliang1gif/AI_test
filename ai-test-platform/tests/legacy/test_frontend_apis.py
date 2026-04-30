#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试前端需要的所有V2 API是否可用
"""

import requests

BASE_URL = "http://localhost:8000"

def test_api(method, url, description):
    """测试单个API"""
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json={}, timeout=5)
        
        if response.status_code == 404:
            print(f"❌ {description}")
            print(f"   {method} {url}")
            print(f"   状态码: 404 Not Found")
            return False
        else:
            print(f"✅ {description}")
            print(f"   {method} {url}")
            print(f"   状态码: {response.status_code}")
            return True
    except Exception as e:
        print(f"❌ {description}")
        print(f"   {method} {url}")
        print(f"   错误: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("测试前端V2 API可用性")
    print("="*60)
    
    tests = [
        # 可观测性API
        ("GET", f"{BASE_URL}/api/v2/observability/runs", "获取执行记录列表"),
        ("GET", f"{BASE_URL}/api/v2/observability/runs/RUN_TEST", "获取执行详情(会404,正常)"),
        
        # 项目配置API
        ("GET", f"{BASE_URL}/api/v2/projects", "获取项目列表"),
        ("GET", f"{BASE_URL}/api/v2/environments/1", "获取环境详情(会404,正常)"),
        
        # 执行触发API
        ("POST", f"{BASE_URL}/api/v2/execution/trigger-simple?project_id=1&environment_id=1&test_case_ids=TEST", "执行触发API"),
        
        # 测试执行API
        ("GET", f"{BASE_URL}/api/v2/test-runs", "获取TestRun列表"),
    ]
    
    passed = 0
    failed = 0
    
    for method, url, description in tests:
        print()
        if test_api(method, url, description):
            passed += 1
        else:
            failed += 1
    
    print("\n" + "="*60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("="*60)
    
    # 检查Pilot API(预期404)
    print("\n" + "="*60)
    print("检查Pilot API(预期404,因为已禁用)")
    print("="*60)
    print()
    test_api("GET", f"{BASE_URL}/api/pilot/projects", "Pilot项目API")
    test_api("GET", f"{BASE_URL}/api/pilot/reports", "Pilot报告API")
    test_api("GET", f"{BASE_URL}/api/pilot/test-runs", "Pilot执行API")
    
    print("\n💡 提示:")
    print("   - V2 API应该全部可用")
    print("   - Pilot API返回404是正常的(已禁用)")
    print("   - 前端应该使用V2 API,不要使用Pilot API")

if __name__ == "__main__":
    main()
