#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试状态机功能(简化版,不依赖数据库)
验证状态流转逻辑
"""

from typing import Optional, Dict, Set


class RunStateMachine:
    """
    测试执行状态机
    管理状态流转的合法性校验
    """
    
    # 定义合法的状态流转
    VALID_TRANSITIONS: Dict[str, Set[str]] = {
        'created': {'queued'},
        'queued': {'preparing', 'aborted'},
        'preparing': {'running', 'failed', 'aborted'},
        'running': {'passed', 'failed', 'aborted', 'healing'},
        'healing': {'passed', 'failed', 'aborted'},
        'passed': set(),  # 终态
        'failed': set(),  # 终态
        'aborted': set()  # 终态
    }
    
    # 终态集合
    FINAL_STATES = {'passed', 'failed', 'aborted'}
    
    @classmethod
    def can_transition(cls, from_status: str, to_status: str) -> bool:
        """检查状态流转是否合法"""
        if from_status not in cls.VALID_TRANSITIONS:
            return False
        return to_status in cls.VALID_TRANSITIONS[from_status]
    
    @classmethod
    def validate_transition(cls, from_status: str, to_status: str) -> tuple:
        """验证状态流转并返回详细信息"""
        # 检查状态是否存在
        if from_status not in cls.VALID_TRANSITIONS:
            return False, f"无效的源状态: {from_status}"
        
        if to_status not in cls.VALID_TRANSITIONS:
            return False, f"无效的目标状态: {to_status}"
        
        # 检查是否为终态
        if from_status in cls.FINAL_STATES:
            return False, f"状态 '{from_status}' 是终态,不允许再次流转"
        
        # 检查流转是否合法
        if not cls.can_transition(from_status, to_status):
            allowed = cls.VALID_TRANSITIONS[from_status]
            allowed_str = ', '.join(allowed) if allowed else '无(终态)'
            return False, f"不允许从 '{from_status}' 流转到 '{to_status}',允许的目标状态: {allowed_str}"
        
        return True, None
    
    @classmethod
    def get_allowed_transitions(cls, from_status: str) -> Set[str]:
        """获取当前状态允许的目标状态"""
        return cls.VALID_TRANSITIONS.get(from_status, set())
    
    @classmethod
    def is_final_state(cls, status: str) -> bool:
        """判断是否为终态"""
        return status in cls.FINAL_STATES
    
    @classmethod
    def get_state_flow_diagram(cls) -> str:
        """获取状态流转图(文字描述)"""
        lines = ["状态流转图:", ""]
        lines.append("created → queued")
        lines.append("queued → preparing | aborted")
        lines.append("preparing → running | failed | aborted")
        lines.append("running → passed | failed | aborted | healing")
        lines.append("healing → passed | failed | aborted")
        lines.append("")
        lines.append("终态: passed, failed, aborted")
        return "\n".join(lines)


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
