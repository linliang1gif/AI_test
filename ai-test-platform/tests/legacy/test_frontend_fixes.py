#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试前端修复 - 验证所有API端点
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_api(endpoint, method="GET", data=None):
    """测试API端点"""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        
        print(f"✅ {method} {endpoint}: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ {method} {endpoint}: {e}")
        return False

def main():
    print("=" * 60)
    print("🧪 测试前端修复 - API端点验证")
    print("=" * 60)
    
    tests = [
        # Dashboard
        ("/api/dashboard/stats", "GET"),
        
        # Projects
        ("/api/projects", "GET"),
        
        # APIs
        ("/api/apis", "GET"),
        
        # Test Cases
        ("/api/test-cases", "GET"),
        
        # Test Runs
        ("/api/test-runs", "GET"),
        
        # Reports
        ("/api/reports", "GET"),
        
        # AI
        ("/api/ai/agents", "GET"),
        ("/api/ai/providers/list", "GET"),
        ("/api/ai/current", "GET"),
        
        # Automation
        ("/api/automation/scripts", "GET"),
        
        # Knowledge
        ("/api/knowledge/stats", "GET"),
        ("/api/knowledge/coverage", "GET"),
        
        # Test Data Factory
        ("/api/test-data/stats", "GET"),
        ("/api/test-data/templates", "GET"),
    ]
    
    passed = 0
    failed = 0
    
    for endpoint, method in tests:
        if test_api(endpoint, method):
            passed += 1
        else:
            failed += 1
    
    print("=" * 60)
    print(f"📊 测试结果: {passed}/{len(tests)} 通过")
    if failed == 0:
        print("✅ 所有API端点正常工作!")
    else:
        print(f"❌ {failed} 个端点失败")
    print("=" * 60)

if __name__ == "__main__":
    main()
