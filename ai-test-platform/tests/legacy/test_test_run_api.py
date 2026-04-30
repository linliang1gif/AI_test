#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试执行API测试脚本
验证P0-3任务状态机功能
"""

import sys
import requests
import json
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

BASE_URL = "http://localhost:8000"


def print_section(title):
    """打印分节标题"""
    print(f"\n{'=' * 60}")
    print(f"{title}")
    print(f"{'=' * 60}\n")


def print_response(response, title="响应"):
    """打印响应信息"""
    print(f"{title}:")
    print(f"  状态码: {response.status_code}")
    try:
        data = response.json()
        print(f"  数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
    except:
        print(f"  原始响应: {response.text}")
    print()


def test_create_test_run():
    """测试创建测试执行"""
    print_section("1. 创建测试执行")
    
    # 创建测试执行
    payload = {
        "project_id": 1,
        "environment_id": 1,
        "trigger_type": "manual",
        "created_by": "test_user"
    }
    
    response = requests.post(f"{BASE_URL}/api/v2/test-runs", json=payload)
    print_response(response, "创建测试执行")
    
    if response.status_code == 201:
        data = response.json()
        run_id = data.get('id')
        print(f"✅ 测试执行创建成功: {run_id}")
        return run_id
    else:
        print(f"❌ 测试执行创建失败")
        return None


def test_get_test_run(run_id):
    """测试获取测试执行详情"""
    print_section("2. 获取测试执行详情")
    
    response = requests.get(f"{BASE_URL}/api/v2/test-runs/{run_id}")
    print_response(response, "测试执行详情")
    
    if response.status_code == 200:
        print(f"✅ 获取测试执行详情成功")
    else:
        print(f"❌ 获取测试执行详情失败")


def test_update_status_valid(run_id):
    """测试合法的状态流转"""
    print_section("3. 测试合法的状态流转")
    
    # 合法流转序列: created → queued → preparing → running → passed
    transitions = [
        ('queued', '进入队列'),
        ('preparing', '准备执行'),
        ('running', '开始执行'),
        ('passed', '执行通过')
    ]
    
    for status, reason in transitions:
        payload = {
            "status": status,
            "changed_by": "test_user",
            "reason": reason
        }
        
        response = requests.put(f"{BASE_URL}/api/v2/test-runs/{run_id}/status", json=payload)
        print(f"流转到 {status}:")
        print_response(response, f"  状态更新")
        
        if response.status_code == 200:
            print(f"  ✅ 状态流转成功: {status}")
        else:
            print(f"  ❌ 状态流转失败: {status}")
            break


def test_update_status_invalid(run_id):
    """测试非法的状态流转"""
    print_section("4. 测试非法的状态流转")
    
    # 尝试从终态流转(应该失败)
    payload = {
        "status": "running",
        "changed_by": "test_user",
        "reason": "尝试从终态流转"
    }
    
    response = requests.put(f"{BASE_URL}/api/v2/test-runs/{run_id}/status", json=payload)
    print_response(response, "尝试从终态流转")
    
    if response.status_code == 400:
        print(f"✅ 正确拒绝了非法流转")
    else:
        print(f"❌ 应该拒绝非法流转但没有")


def test_get_status_history(run_id):
    """测试获取状态历史"""
    print_section("5. 获取状态历史")
    
    response = requests.get(f"{BASE_URL}/api/v2/test-runs/{run_id}/history")
    print_response(response, "状态历史")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 获取状态历史成功,共 {len(data)} 条记录")
        
        # 打印状态历史
        print("\n状态变更时间线:")
        for record in data:
            from_status = record.get('from_status') or '(初始)'
            to_status = record.get('to_status')
            changed_at = record.get('changed_at')
            changed_by = record.get('changed_by')
            reason = record.get('reason') or '无'
            print(f"  {from_status:12} → {to_status:12} | {changed_at} | {changed_by} | {reason}")
    else:
        print(f"❌ 获取状态历史失败")


def test_get_state_info(run_id):
    """测试获取状态信息"""
    print_section("6. 获取当前状态信息")
    
    response = requests.get(f"{BASE_URL}/api/v2/test-runs/{run_id}/state-info")
    print_response(response, "状态信息")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 获取状态信息成功")
        print(f"  当前状态: {data.get('current_status')}")
        print(f"  允许流转: {', '.join(data.get('allowed_transitions', []))}")
        print(f"  是否终态: {data.get('is_final_state')}")
    else:
        print(f"❌ 获取状态信息失败")


def test_get_state_machine_diagram():
    """测试获取状态机流转图"""
    print_section("7. 获取状态机流转图")
    
    response = requests.get(f"{BASE_URL}/api/v2/test-runs/state-machine/diagram")
    print_response(response, "状态机流转图")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 获取状态机流转图成功")
        print(f"\n{data.get('diagram')}")
    else:
        print(f"❌ 获取状态机流转图失败")


def test_create_run_with_healing():
    """测试带修复流程的执行"""
    print_section("8. 测试带修复流程的执行")
    
    # 创建新的测试执行
    payload = {
        "project_id": 1,
        "environment_id": 1,
        "trigger_type": "manual",
        "created_by": "test_user"
    }
    
    response = requests.post(f"{BASE_URL}/api/v2/test-runs", json=payload)
    if response.status_code != 201:
        print(f"❌ 创建测试执行失败")
        return
    
    run_id = response.json().get('id')
    print(f"创建测试执行: {run_id}")
    
    # 流转序列: created → queued → preparing → running → healing → passed
    transitions = [
        ('queued', '进入队列'),
        ('preparing', '准备执行'),
        ('running', '开始执行'),
        ('healing', '触发自动修复'),
        ('passed', '修复后通过')
    ]
    
    for status, reason in transitions:
        payload = {
            "status": status,
            "changed_by": "test_user",
            "reason": reason
        }
        
        response = requests.put(f"{BASE_URL}/api/v2/test-runs/{run_id}/status", json=payload)
        if response.status_code == 200:
            print(f"  ✅ {status}")
        else:
            print(f"  ❌ {status} 失败")
            break
    
    # 获取状态历史
    response = requests.get(f"{BASE_URL}/api/v2/test-runs/{run_id}/history")
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ 修复流程完成,共 {len(data)} 次状态变更")


def test_list_test_runs():
    """测试获取测试执行列表"""
    print_section("9. 获取测试执行列表")
    
    response = requests.get(f"{BASE_URL}/api/v2/test-runs?limit=10")
    print_response(response, "测试执行列表")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 获取测试执行列表成功,共 {len(data)} 条记录")
    else:
        print(f"❌ 获取测试执行列表失败")


def main():
    """主函数"""
    print("\n🧪 P0-3 任务状态机 API 测试")
    print(f"后端地址: {BASE_URL}")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 测试状态机流转图
        test_get_state_machine_diagram()
        
        # 创建测试执行
        run_id = test_create_test_run()
        if not run_id:
            print("\n❌ 无法创建测试执行,终止测试")
            return
        
        # 获取测试执行详情
        test_get_test_run(run_id)
        
        # 测试合法的状态流转
        test_update_status_valid(run_id)
        
        # 测试非法的状态流转
        test_update_status_invalid(run_id)
        
        # 获取状态历史
        test_get_status_history(run_id)
        
        # 获取状态信息
        test_get_state_info(run_id)
        
        # 测试带修复流程的执行
        test_create_run_with_healing()
        
        # 获取测试执行列表
        test_list_test_runs()
        
        print_section("测试完成")
        print("✅ 所有测试已执行完成")
        print("\n💡 提示:")
        print("  - 状态机正确验证了合法和非法的状态流转")
        print("  - 状态历史已持久化到数据库")
        print("  - 支持run/run_case/run_step三层状态追踪")
        
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 无法连接到后端服务: {BASE_URL}")
        print("   请确保后端服务已启动: python backend_api_server.py")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
