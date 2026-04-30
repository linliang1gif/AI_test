#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
当前系统功能验证
验证现有功能是否正常工作
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def test_health():
    """测试健康检查"""
    print_section("1. 健康检查")
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"✅ 状态码: {r.status_code}")
        print(f"✅ 响应: {r.json()}")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False

def test_dashboard():
    """测试Dashboard API"""
    print_section("2. Dashboard统计")
    try:
        r = requests.get(f"{BASE_URL}/api/dashboard/stats", timeout=5)
        if r.status_code == 200:
            data = r.json()
            print(f"✅ 总测试数: {data.get('totalTests', 0)}")
            print(f"✅ 通过数: {data.get('passed', 0)}")
            print(f"✅ 失败数: {data.get('failed', 0)}")
            print(f"✅ 覆盖率: {data.get('coverage', 0)}%")
            return True
        else:
            print(f"❌ 状态码: {r.status_code}")
            return False
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False

def test_testcases():
    """测试用例API"""
    print_section("3. 测试用例列表")
    try:
        r = requests.get(f"{BASE_URL}/api/test-cases", timeout=5)
        if r.status_code == 200:
            data = r.json()
            cases = data.get('data', [])
            print(f"✅ 测试用例数: {len(cases)}")
            if cases:
                print(f"\n前3个测试用例:")
                for i, tc in enumerate(cases[:3], 1):
                    print(f"   {i}. {tc.get('title', 'N/A')[:50]}")
            return True
        else:
            print(f"❌ 状态码: {r.status_code}")
            return False
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False

def test_projects():
    """测试项目API"""
    print_section("4. 项目列表")
    try:
        r = requests.get(f"{BASE_URL}/api/projects", timeout=5)
        if r.status_code == 200:
            data = r.json()
            projects = data.get('projects', [])
            print(f"✅ 项目数: {len(projects)}")
            if projects:
                print(f"\n项目列表:")
                for i, p in enumerate(projects, 1):
                    print(f"   {i}. {p.get('name', 'N/A')} - {p.get('status', 'N/A')}")
            return True
        else:
            print(f"❌ 状态码: {r.status_code}")
            return False
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False

def test_test_runs():
    """测试运行API"""
    print_section("5. 测试运行记录")
    try:
        r = requests.get(f"{BASE_URL}/api/test-runs", timeout=5)
        if r.status_code == 200:
            data = r.json()
            runs = data.get('testRuns', [])
            print(f"✅ 测试运行数: {len(runs)}")
            if runs:
                print(f"\n最近的测试运行:")
                for i, run in enumerate(runs[:3], 1):
                    print(f"   {i}. {run.get('name', 'N/A')} - {run.get('status', 'N/A')}")
            return True
        else:
            print(f"❌ 状态码: {r.status_code}")
            return False
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("  当前系统功能验证")
    print("="*60)
    
    results = []
    
    # 运行所有测试
    results.append(("健康检查", test_health()))
    results.append(("Dashboard", test_dashboard()))
    results.append(("测试用例", test_testcases()))
    results.append(("项目管理", test_projects()))
    results.append(("测试运行", test_test_runs()))
    
    # 总结
    print_section("测试总结")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"\n测试结果: {passed}/{total} 通过")
    print(f"\n详细结果:")
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {name}: {status}")
    
    if passed == total:
        print(f"\n🎉 所有功能正常工作!")
    else:
        print(f"\n⚠️  部分功能异常,请检查后端服务")
    
    print("\n" + "="*60 + "\n")
    
    return passed == total

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
