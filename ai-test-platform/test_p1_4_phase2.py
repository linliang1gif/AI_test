#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
P1.4 阶段2测试脚本
测试Test Cases集成、Automation集成和Reports功能
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_section(title):
    """打印分节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_testcase_dataset_binding():
    """测试1: 测试用例绑定数据集"""
    print_section("测试1: 测试用例绑定数据集")
    
    # 1. 创建一个测试数据集
    print("1. 创建测试数据集...")
    dataset_data = {
        "name": "用户登录测试数据",
        "description": "用于测试用例的登录数据",
        "data": {
            "username": "testuser@example.com",
            "password": "Test123456",
            "remember_me": True
        },
        "tags": ["登录", "用户"]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/test-data/datasets",
        json=dataset_data
    )
    
    if response.status_code == 200:
        result = response.json()
        dataset_id = result['dataset']['id']
        print(f"✅ 数据集创建成功: {dataset_id}")
    else:
        print(f"❌ 数据集创建失败: {response.status_code}")
        return False
    
    # 2. 绑定数据集到测试用例
    print("\n2. 绑定数据集到测试用例...")
    test_case_id = 1  # 假设测试用例ID为1
    
    response = requests.post(
        f"{BASE_URL}/api/test-cases/{test_case_id}/bind-dataset",
        json={"dataset_id": dataset_id}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 数据集绑定成功")
        print(f"   测试用例ID: {result['test_case_id']}")
        print(f"   数据集ID: {result['dataset_id']}")
    else:
        print(f"❌ 数据集绑定失败: {response.status_code}")
        return False
    
    # 3. 查询测试用例的数据集
    print("\n3. 查询测试用例的数据集...")
    response = requests.get(f"{BASE_URL}/api/test-cases/{test_case_id}/dataset")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 查询成功")
        print(f"   测试用例ID: {result['test_case_id']}")
    else:
        print(f"❌ 查询失败: {response.status_code}")
        return False
    
    return True

def test_automation_with_dataset():
    """测试2: 自动化脚本集成数据集"""
    print_section("测试2: 自动化脚本集成数据集")
    
    # 1. 创建数据集
    print("1. 创建API测试数据集...")
    dataset_data = {
        "name": "API测试数据集",
        "description": "用于自动化脚本的API测试数据",
        "data": {
            "api_endpoint": "/api/users",
            "method": "POST",
            "payload": {
                "name": "Test User",
                "email": "test@example.com",
                "age": 25
            }
        },
        "tags": ["API", "自动化"]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/test-data/datasets",
        json=dataset_data
    )
    
    if response.status_code == 200:
        result = response.json()
        dataset_id = result['dataset']['id']
        print(f"✅ 数据集创建成功: {dataset_id}")
    else:
        print(f"❌ 数据集创建失败: {response.status_code}")
        return False
    
    # 2. 生成包含数据集的自动化脚本
    print("\n2. 生成包含数据集的自动化脚本...")
    script_data = {
        "type": "automation_script",
        "framework": "pytest",
        "language": "Python",
        "test_type": "API Tests",
        "dataset_id": dataset_id
    }
    
    response = requests.post(
        f"{BASE_URL}/api/ai/generate",
        json=script_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 脚本生成请求成功")
        print(f"   任务ID: {result.get('taskId', 'N/A')}")
        print(f"   消息: {result.get('message', 'N/A')}")
        print(f"   包含数据集: {dataset_id}")
    else:
        print(f"❌ 脚本生成失败: {response.status_code}")
        return False
    
    return True

def test_report_generation():
    """测试3: 报告生成功能"""
    print_section("测试3: 报告生成功能")
    
    # 1. 获取测试运行列表
    print("1. 获取测试运行列表...")
    response = requests.get(f"{BASE_URL}/api/test-runs")
    
    if response.status_code == 200:
        result = response.json()
        test_runs = result.get('test_runs', [])
        print(f"✅ 获取成功,共 {len(test_runs)} 个测试运行")
        
        if len(test_runs) > 0:
            test_run = test_runs[0]
            print(f"   第一个测试运行: {test_run.get('name', 'N/A')}")
            test_run_id = test_run.get('id')
        else:
            print("⚠️  没有测试运行,跳过报告生成测试")
            return True
    else:
        print(f"❌ 获取失败: {response.status_code}")
        return False
    
    # 2. 生成报告
    print("\n2. 生成测试报告...")
    report_data = {
        "test_run_id": test_run_id,
        "type": "comprehensive",
        "include_charts": True,
        "include_details": True
    }
    
    response = requests.post(
        f"{BASE_URL}/api/reports/generate",
        json=report_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 报告生成成功")
        print(f"   报告ID: {result.get('report_id', 'N/A')}")
        print(f"   消息: {result.get('message', 'N/A')}")
    else:
        print(f"❌ 报告生成失败: {response.status_code}")
        return False
    
    # 3. 获取报告列表
    print("\n3. 获取报告列表...")
    response = requests.get(f"{BASE_URL}/api/reports")
    
    if response.status_code == 200:
        result = response.json()
        reports = result.get('reports', [])
        print(f"✅ 获取成功,共 {len(reports)} 个报告")
        
        if len(reports) > 0:
            report = reports[0]
            print(f"   最新报告: {report.get('name', 'N/A')}")
            print(f"   类型: {report.get('type', 'N/A')}")
            print(f"   通过率: {report.get('passRate', 'N/A')}%")
    else:
        print(f"❌ 获取失败: {response.status_code}")
        return False
    
    return True

def test_dataset_stats():
    """测试4: 数据集统计"""
    print_section("测试4: 数据集统计")
    
    print("获取数据集统计信息...")
    response = requests.get(f"{BASE_URL}/api/test-data/datasets-stats")
    
    if response.status_code == 200:
        result = response.json()
        stats = result.get('stats', {})
        print(f"✅ 统计信息获取成功")
        print(f"   总数据集: {stats.get('total_datasets', 0)}")
        print(f"   总使用次数: {stats.get('total_usage', 0)}")
        
        most_used = stats.get('most_used', [])
        if most_used:
            print(f"\n   最常用数据集:")
            for i, dataset in enumerate(most_used[:3], 1):
                print(f"   {i}. {dataset.get('name', 'N/A')} - 使用 {dataset.get('usage_count', 0)} 次")
    else:
        print(f"❌ 获取失败: {response.status_code}")
        return False
    
    return True

def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("  P1.4 阶段2集成测试")
    print("  测试Test Cases、Automation、Reports集成")
    print("="*60)
    
    results = []
    
    # 运行所有测试
    tests = [
        ("测试用例绑定数据集", test_testcase_dataset_binding),
        ("自动化脚本集成数据集", test_automation_with_dataset),
        ("报告生成功能", test_report_generation),
        ("数据集统计", test_dataset_stats),
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ 测试异常: {e}")
            results.append((test_name, False))
    
    # 打印测试总结
    print_section("测试总结")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"测试项目                          结果")
    print(f"{'-'*60}")
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:<30} {status}")
    print(f"{'-'*60}")
    print(f"总计: {passed}/{total} 通过 ({passed*100//total}%)")
    
    if passed == total:
        print("\n🎉 所有测试通过!")
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试执行失败: {e}")
        exit(1)
