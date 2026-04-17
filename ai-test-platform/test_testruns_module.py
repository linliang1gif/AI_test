#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试TestRuns模块功能
"""

import requests
import time
import json

BASE_URL = "http://127.0.0.1:8081"

def test_get_test_runs():
    """测试获取测试运行列表"""
    print("\n1. 测试获取测试运行列表")
    print("=" * 50)
    
    response = requests.get(f"{BASE_URL}/api/test-runs")
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        test_runs = data.get("testRuns", [])
        print(f"✅ 成功获取 {len(test_runs)} 个测试运行记录")
        
        if test_runs:
            print("\n最近的测试运行:")
            for run in test_runs[:3]:
                print(f"  - ID: {run['id']}, 名称: {run['name']}, 状态: {run['status']}")
        return test_runs
    else:
        print(f"❌ 获取失败: {response.text}")
        return []

def test_start_test_run():
    """测试启动新的测试运行"""
    print("\n2. 测试启动新的测试运行")
    print("=" * 50)
    
    payload = {
        "environment": "staging"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/test-runs",
        json=payload
    )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        test_run = data.get("testRun", {})
        task_id = data.get("taskId", "")
        
        print(f"✅ 测试运行已启动")
        print(f"  - 运行ID: {test_run.get('id')}")
        print(f"  - 名称: {test_run.get('name')}")
        print(f"  - 环境: {test_run.get('environment')}")
        print(f"  - 总测试数: {test_run.get('totalTests')}")
        print(f"  - 任务ID: {task_id}")
        
        return test_run
    else:
        print(f"❌ 启动失败: {response.text}")
        return None

def test_get_test_run_status(run_id):
    """测试获取测试运行状态"""
    print(f"\n3. 测试获取测试运行状态 (ID: {run_id})")
    print("=" * 50)
    
    response = requests.get(f"{BASE_URL}/api/test-runs/{run_id}/status")
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        test_run = data.get("testRun", {})
        
        print(f"✅ 成功获取状态")
        print(f"  - 状态: {test_run.get('status')}")
        print(f"  - 进度: {test_run.get('progress')}%")
        print(f"  - 通过: {test_run.get('passed')}")
        print(f"  - 失败: {test_run.get('failed')}")
        print(f"  - 待运行: {test_run.get('pending')}")
        print(f"  - 持续时间: {test_run.get('duration')}")
        
        logs = test_run.get('logs', [])
        if logs:
            print(f"\n  最新日志 (共{len(logs)}条):")
            for log in logs[-3:]:
                print(f"    [{log.get('level')}] {log.get('time')} - {log.get('message')}")
        
        return test_run
    else:
        print(f"❌ 获取失败: {response.text}")
        return None

def test_monitor_test_run(run_id, max_checks=10):
    """监控测试运行直到完成"""
    print(f"\n4. 监控测试运行 (ID: {run_id})")
    print("=" * 50)
    
    for i in range(max_checks):
        response = requests.get(f"{BASE_URL}/api/test-runs/{run_id}/status")
        
        if response.status_code == 200:
            data = response.json()
            test_run = data.get("testRun", {})
            status = test_run.get('status')
            progress = test_run.get('progress', 0)
            
            print(f"[{i+1}/{max_checks}] 状态: {status}, 进度: {progress}%, "
                  f"通过: {test_run.get('passed')}, 失败: {test_run.get('failed')}")
            
            if status in ['completed', 'failed', 'stopped']:
                print(f"\n✅ 测试运行已结束: {status}")
                print(f"  - 总测试数: {test_run.get('totalTests')}")
                print(f"  - 通过: {test_run.get('passed')}")
                print(f"  - 失败: {test_run.get('failed')}")
                print(f"  - 持续时间: {test_run.get('duration')}")
                return test_run
            
            time.sleep(3)  # 每3秒检查一次
        else:
            print(f"❌ 获取状态失败: {response.text}")
            break
    
    print("\n⚠️ 达到最大检查次数,停止监控")
    return None

def test_pause_test_run(run_id):
    """测试暂停测试运行"""
    print(f"\n5. 测试暂停测试运行 (ID: {run_id})")
    print("=" * 50)
    
    response = requests.post(f"{BASE_URL}/api/test-runs/{run_id}/pause")
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data.get('message')}")
        return True
    else:
        print(f"❌ 暂停失败: {response.text}")
        return False

def test_resume_test_run(run_id):
    """测试恢复测试运行"""
    print(f"\n6. 测试恢复测试运行 (ID: {run_id})")
    print("=" * 50)
    
    response = requests.post(f"{BASE_URL}/api/test-runs/{run_id}/resume")
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data.get('message')}")
        return True
    else:
        print(f"❌ 恢复失败: {response.text}")
        return False

def test_stop_test_run(run_id):
    """测试停止测试运行"""
    print(f"\n7. 测试停止测试运行 (ID: {run_id})")
    print("=" * 50)
    
    response = requests.post(f"{BASE_URL}/api/test-runs/{run_id}/stop")
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data.get('message')}")
        return True
    else:
        print(f"❌ 停止失败: {response.text}")
        return False

def main():
    """主测试流程"""
    print("=" * 60)
    print("TestRuns模块功能测试")
    print("=" * 60)
    
    try:
        # 1. 获取现有测试运行列表
        existing_runs = test_get_test_runs()
        
        # 2. 启动新的测试运行
        new_run = test_start_test_run()
        
        if new_run:
            run_id = new_run.get('id')
            
            # 3. 等待一下让测试开始执行
            print("\n等待3秒让测试开始执行...")
            time.sleep(3)
            
            # 4. 获取状态
            test_get_test_run_status(run_id)
            
            # 5. 监控测试运行(最多检查10次)
            final_run = test_monitor_test_run(run_id, max_checks=10)
            
            # 6. 如果测试还在运行,测试控制功能
            if final_run and final_run.get('status') == 'running':
                # 测试暂停
                if test_pause_test_run(run_id):
                    time.sleep(2)
                    test_get_test_run_status(run_id)
                    
                    # 测试恢复
                    if test_resume_test_run(run_id):
                        time.sleep(2)
                        test_get_test_run_status(run_id)
                
                # 测试停止
                test_stop_test_run(run_id)
                time.sleep(1)
                test_get_test_run_status(run_id)
        
        # 最后再次获取所有测试运行
        print("\n" + "=" * 60)
        print("最终测试运行列表")
        print("=" * 60)
        test_get_test_runs()
        
        print("\n" + "=" * 60)
        print("✅ TestRuns模块测试完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
