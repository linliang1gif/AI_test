#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试状态机功能
验证状态流转逻辑
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from services.state_machine import RunStateMachine


def test_valid_transitions():
    """测试合法的状态流转"""
    print("=" * 60)
    print("测试合法的状态流转")
    print("=" * 60)
    
    valid_cases = [
        ('created', 'queued'),
        ('queued', 'preparing'),
        ('queued', 'aborted'),
        ('preparing', 'running'),
        ('preparing', 'failed'),
        ('preparing', 'aborted'),
        ('running', 'passed'),
        ('running', 'failed'),
        ('running', 'aborted'),
        ('running', 'healing'),
        ('healing', 'passed'),
        ('healing', 'failed'),
        ('healing', 'aborted'),
    ]
    
    for from_status, to_status in valid_cases:
        is_valid, error = RunStateMachine.validate_transition(from_status, to_status)
        status_icon = "✅" if is_valid else "❌"
        print(f"{status_icon} {from_status:12} → {to_status:12} : {is_valid}")
        if not is_valid:
            print(f"   错误: {error}")
    
    print()


def test_invalid_transitions():
    """测试非法的状态流转"""
    print("=" * 60)
    print("测试非法的状态流转")
    print("=" * 60)
    
    invalid_cases = [
        ('created', 'running'),      # 跳过queued和preparing
        ('created', 'passed'),       # 直接到终态
        ('queued', 'passed'),        # 跳过preparing和running
        ('running', 'queued'),       # 回退
        ('passed', 'running'),       # 终态不能流转
        ('failed', 'healing'),       # 终态不能流转
        ('aborted', 'running'),      # 终态不能流转
        ('preparing', 'healing'),    # 跳过running
        ('healing', 'running'),      # 回退
    ]
    
    for from_status, to_status in invalid_cases:
        is_valid, error = RunStateMachine.validate_transition(from_status, to_status)
        status_icon = "✅" if not is_valid else "❌"  # 期望失败
        print(f"{status_icon} {from_status:12} → {to_status:12} : 拒绝")
        if error:
            print(f"   原因: {error}")
    
    print()


def test_final_states():
    """测试终态判断"""
    print("=" * 60)
    print("测试终态判断")
    print("=" * 60)
    
    all_states = ['created', 'queued', 'preparing', 'running', 'healing', 'passed', 'failed', 'aborted']
    
    for status in all_states:
        is_final = RunStateMachine.is_final_state(status)
        status_icon = "🔒" if is_final else "🔓"
        print(f"{status_icon} {status:12} : {'终态' if is_final else '中间态'}")
    
    print()


def test_allowed_transitions():
    """测试获取允许的流转"""
    print("=" * 60)
    print("测试获取允许的流转")
    print("=" * 60)
    
    all_states = ['created', 'queued', 'preparing', 'running', 'healing', 'passed', 'failed', 'aborted']
    
    for status in all_states:
        allowed = RunStateMachine.get_allowed_transitions(status)
        allowed_str = ', '.join(allowed) if allowed else '无(终态)'
        print(f"{status:12} → {allowed_str}")
    
    print()


def test_state_flow_diagram():
    """测试状态流转图"""
    print("=" * 60)
    print("状态流转图")
    print("=" * 60)
    print(RunStateMachine.get_state_flow_diagram())
    print()


def main():
    """主函数"""
    print("\n🧪 状态机功能测试\n")
    
    test_state_flow_diagram()
    test_valid_transitions()
    test_invalid_transitions()
    test_final_states()
    test_allowed_transitions()
    
    print("=" * 60)
    print("✅ 状态机测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
