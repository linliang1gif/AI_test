#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
状态机 - 管理测试执行状态流转
"""

from typing import Optional, Dict, Set
from datetime import datetime


class RunStateMachine:
    """
    测试执行状态机
    管理状态流转的合法性校验
    """
    
    # 定义合法的状态流转
    VALID_TRANSITIONS: Dict[str, Set[str]] = {
        'created': {'queued', 'running'},  # 允许created直接到running(用于RunCase)
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
        """
        检查状态流转是否合法
        
        Args:
            from_status: 当前状态
            to_status: 目标状态
            
        Returns:
            bool: 是否允许流转
        """
        if from_status not in cls.VALID_TRANSITIONS:
            return False
        
        return to_status in cls.VALID_TRANSITIONS[from_status]
    
    @classmethod
    def validate_transition(cls, from_status: str, to_status: str) -> tuple[bool, Optional[str]]:
        """
        验证状态流转并返回详细信息
        
        Args:
            from_status: 当前状态
            to_status: 目标状态
            
        Returns:
            tuple: (是否合法, 错误信息)
        """
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
        """
        获取当前状态允许的目标状态
        
        Args:
            from_status: 当前状态
            
        Returns:
            Set[str]: 允许的目标状态集合
        """
        return cls.VALID_TRANSITIONS.get(from_status, set())
    
    @classmethod
    def is_final_state(cls, status: str) -> bool:
        """
        判断是否为终态
        
        Args:
            status: 状态
            
        Returns:
            bool: 是否为终态
        """
        return status in cls.FINAL_STATES
    
    @classmethod
    def get_state_flow_diagram(cls) -> str:
        """
        获取状态流转图(文字描述)
        
        Returns:
            str: 状态流转图
        """
        lines = ["状态流转图:", ""]
        lines.append("created → queued")
        lines.append("queued → preparing | aborted")
        lines.append("preparing → running | failed | aborted")
        lines.append("running → passed | failed | aborted | healing")
        lines.append("healing → passed | failed | aborted")
        lines.append("")
        lines.append("终态: passed, failed, aborted")
        return "\n".join(lines)
