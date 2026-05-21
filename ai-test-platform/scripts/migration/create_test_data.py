#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
创建测试数据用于演示报告生成
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8081"

def create_test_data():
    """创建测试数据"""
    print("=" * 60)
    print("创建测试数据")
    print("=" * 60)
    
    # 1. 创建项目
    print("\n1️⃣  创建测试项目...")
    response = requests.post(
        f"{BASE_URL}/api/projects",
        json={
            "name": "演示项目",
            "description": "用于演示报告生成的测试项目",
            "environment": "development",
            "base_url": "http://localhost:8080"
        }
    )
    
    if response.status_code == 200:
        project = response.json().get("project", {})
        print(f"✅ 项目创建成功: {project['name']} (ID: {project['id']})")
        project_id = project['id']
    else:
        print(f"❌ 创建项目失败: {response.status_code}")
        return
    
    # 2. 创建测试用例
    print("\n2️⃣  创建测试用例...")
    test_cases = []
    for i in range(5):
        response = requests.post(
            f"{BASE_URL}/api/test-cases",
            json={
                "title": f"测试用例 {i+1}",
                "description": f"这是第 {i+1} 个测试用例",
                "module": "功能模块",
                "priority": "high",
                "steps": [
                    f"步骤1: 执行操作 {i+1}",
                    f"步骤2: 验证结果 {i+1}"
                ],
                "expected_result": f"预期结果 {i+1}",
                "project_id": project_id,
                "source": "manual"
            }
        )
        
        if response.status_code == 200:
            test_case = response.json().get("test_case", {})
            test_cases.append(test_case)
            print(f"   ✅ 创建测试用例: {test_case['title']}")
        else:
            print(f"   ❌ 创建测试用例失败: {response.status_code}")
    
    # 3. 运行测试
    print("\n3️⃣  运行测试...")
    response = requests.post(
        f"{BASE_URL}/api/test-runs/start",
        json={
            "name": "演示测试运行",
            "project_id": project_id,
            "test_case_ids": [tc['id'] for tc in test_cases],
            "environment": "development"
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        run_id = result.get("run_id")
        print(f"✅ 测试运行已启动 (ID: {run_id})")
        
        # 等待测试完成
        print("   等待测试完成...")
        for i in range(30):
            time.sleep(1)
            response = requests.get(f"{BASE_URL}/api/test-runs/{run_id}/status")
            if response.status_code == 200:
                status = response.json()
                if status.get("status") == "completed":
                    print(f"✅ 测试运行完成!")
                    print(f"   总测试数: {status.get('totalTests', 0)}")
                    print(f"   通过: {status.get('passed', 0)}")
                    print(f"   失败: {status.get('failed', 0)}")
                    break
            print(f"   进度: {i+1}/30 秒...")
        
        print("\n✅ 测试数据创建完成!")
        print(f"   项目ID: {project_id}")
        print(f"   测试运行ID: {run_id}")
        print(f"   测试用例数: {len(test_cases)}")
        
    else:
        print(f"❌ 启动测试运行失败: {response.status_code}")
    
    print("\n" + "=" * 60)
    print("完成!")
    print("=" * 60)

if __name__ == "__main__":
    create_test_data()
