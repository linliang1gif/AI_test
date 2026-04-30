#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P0-5.1 完整闭环验证脚本
测试从前端触发执行到查看详情的完整流程
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_execution_trigger_simple():
    """测试简化执行触发API"""
    print("\n" + "="*60)
    print("测试1: 简化执行触发API")
    print("="*60)
    
    # 准备参数
    project_id = 1
    environment_id = 1
    test_case_ids = ["TC_QUICK_001", "TC_QUICK_002", "TC_QUICK_003"]
    
    # 构建URL
    url = f"{BASE_URL}/api/v2/execution/trigger-simple"
    params = {
        "project_id": project_id,
        "environment_id": environment_id,
        "test_case_ids": test_case_ids
    }
    
    print(f"\n📤 发送请求: POST {url}")
    print(f"   参数: {params}")
    
    try:
        response = requests.post(url, params=params, timeout=60)
        print(f"\n✅ 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n📊 执行结果:")
            print(f"   成功: {result.get('success')}")
            print(f"   Run ID: {result.get('run_id')}")
            print(f"   Trace ID: {result.get('trace_id')}")
            print(f"   状态: {result.get('status')}")
            print(f"   消息: {result.get('message')}")
            
            return result.get('run_id')
        else:
            print(f"\n❌ 请求失败: {response.text}")
            return None
            
    except Exception as e:
        print(f"\n❌ 请求异常: {e}")
        return None


def test_observability_run_detail(run_id):
    """测试查询执行详情"""
    print("\n" + "="*60)
    print("测试2: 查询执行详情")
    print("="*60)
    
    url = f"{BASE_URL}/api/v2/observability/runs/{run_id}"
    
    print(f"\n📤 发送请求: GET {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"\n✅ 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            data = result.get('data', {})
            print(f"\n📊 执行详情:")
            print(f"   Run ID: {data.get('id')}")
            print(f"   项目ID: {data.get('project_id')}")
            print(f"   环境ID: {data.get('environment_id')}")
            print(f"   状态: {data.get('status')}")
            print(f"   Trace ID: {data.get('trace_id')}")
            print(f"   总用例数: {data.get('total_cases')}")
            print(f"   通过数: {data.get('passed_cases')}")
            print(f"   失败数: {data.get('failed_cases')}")
            print(f"   创建时间: {data.get('created_at')}")
            
            return True
        else:
            print(f"\n❌ 请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ 请求异常: {e}")
        return False


def test_observability_run_cases(run_id):
    """测试查询RunCase列表"""
    print("\n" + "="*60)
    print("测试3: 查询RunCase列表")
    print("="*60)
    
    url = f"{BASE_URL}/api/v2/observability/runs/{run_id}/cases"
    
    print(f"\n📤 发送请求: GET {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"\n✅ 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            cases = result.get('data', [])
            print(f"\n📊 RunCase列表 (共{len(cases)}个):")
            
            for i, case in enumerate(cases, 1):
                print(f"\n   Case {i}:")
                print(f"      ID: {case.get('id')}")
                print(f"      测试用例ID: {case.get('test_case_id')}")
                print(f"      标题: {case.get('title')}")
                print(f"      状态: {case.get('status')}")
                print(f"      耗时: {case.get('duration')}s")
            
            return cases[0].get('id') if cases else None
        else:
            print(f"\n❌ 请求失败: {response.text}")
            return None
            
    except Exception as e:
        print(f"\n❌ 请求异常: {e}")
        return None


def test_observability_case_steps(run_case_id):
    """测试查询RunStep列表"""
    print("\n" + "="*60)
    print("测试4: 查询RunStep列表")
    print("="*60)
    
    url = f"{BASE_URL}/api/v2/observability/cases/{run_case_id}/steps"
    
    print(f"\n📤 发送请求: GET {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"\n✅ 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            steps = result.get('data', [])
            print(f"\n📊 RunStep列表 (共{len(steps)}个):")
            
            for i, step in enumerate(steps, 1):
                print(f"\n   Step {i}:")
                print(f"      ID: {step.get('id')}")
                print(f"      步骤名称: {step.get('step_name')}")
                print(f"      状态: {step.get('status')}")
                print(f"      耗时: {step.get('duration')}s")
            
            return steps[0].get('id') if steps else None
        else:
            print(f"\n❌ 请求失败: {response.text}")
            return None
            
    except Exception as e:
        print(f"\n❌ 请求异常: {e}")
        return None


def test_observability_step_snapshot(run_step_id):
    """测试查询RunStep快照"""
    print("\n" + "="*60)
    print("测试5: 查询RunStep快照")
    print("="*60)
    
    url = f"{BASE_URL}/api/v2/observability/steps/{run_step_id}/snapshot"
    
    print(f"\n📤 发送请求: GET {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"\n✅ 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            snapshot = result.get('data', {})
            print(f"\n📊 请求/响应快照:")
            print(f"   Method: {snapshot.get('method')}")
            print(f"   URL: {snapshot.get('url')}")
            print(f"   状态码: {snapshot.get('response_status')}")
            print(f"   耗时: {snapshot.get('elapsed_time')}s")
            
            if snapshot.get('request_headers'):
                print(f"\n   请求头:")
                for k, v in snapshot.get('request_headers', {}).items():
                    print(f"      {k}: {v}")
            
            if snapshot.get('response_body'):
                print(f"\n   响应体 (前200字符):")
                body = str(snapshot.get('response_body'))[:200]
                print(f"      {body}...")
            
            return True
        else:
            print(f"\n❌ 请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ 请求异常: {e}")
        return False


def main():
    """主测试流程"""
    print("\n" + "="*60)
    print("P0-5.1 完整闭环验证")
    print("="*60)
    print("\n测试流程:")
    print("1. 触发执行 (简化API)")
    print("2. 查询执行详情")
    print("3. 查询RunCase列表")
    print("4. 查询RunStep列表")
    print("5. 查询请求/响应快照")
    
    # 测试1: 触发执行
    run_id = test_execution_trigger_simple()
    if not run_id:
        print("\n❌ 执行触发失败,终止测试")
        return False
    
    # 等待执行完成
    print("\n⏳ 等待2秒让执行完成...")
    time.sleep(2)
    
    # 测试2: 查询执行详情
    if not test_observability_run_detail(run_id):
        print("\n❌ 查询执行详情失败")
        return False
    
    # 测试3: 查询RunCase列表
    run_case_id = test_observability_run_cases(run_id)
    if not run_case_id:
        print("\n❌ 查询RunCase列表失败")
        return False
    
    # 测试4: 查询RunStep列表
    run_step_id = test_observability_case_steps(run_case_id)
    if not run_step_id:
        print("\n❌ 查询RunStep列表失败")
        return False
    
    # 测试5: 查询快照
    if not test_observability_step_snapshot(run_step_id):
        print("\n❌ 查询快照失败")
        return False
    
    # 全部通过
    print("\n" + "="*60)
    print("✅ P0-5.1 完整闭环验证通过!")
    print("="*60)
    print("\n验证内容:")
    print("✅ 执行触发API正常工作")
    print("✅ 执行详情查询正常工作")
    print("✅ RunCase列表查询正常工作")
    print("✅ RunStep列表查询正常工作")
    print("✅ 请求/响应快照查询正常工作")
    print("\n前端闭环:")
    print("1. 访问 http://localhost:5173/quick-execution-test")
    print("2. 选择测试用例")
    print("3. 点击执行")
    print("4. 自动跳转到 /test-runs-v2/{run_id}")
    print("5. 查看执行详情、Cases、Steps、快照")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
