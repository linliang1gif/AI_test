#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Agent 测试系统

多个专业化AI Agent协同工作：
- RequirementAgent: 需求解析
- TestDesignAgent: 测试设计
- TestCaseAgent: 测试用例生成
- ApiTestAgent: API测试生成
- AutomationAgent: 自动化脚本生成
- BugAnalyzerAgent: Bug分析
"""

from .base_agent import BaseAgent
from .requirement_agent import RequirementAgent
from .test_design_agent import TestDesignAgent
from .test_case_agent import TestCaseAgent
from .api_test_agent import ApiTestAgent
from .automation_agent import AutomationAgent
from .bug_analyzer_agent import BugAnalyzerAgent
from .agent_coordinator import AgentCoordinator

__all__ = [
    'BaseAgent',
    'RequirementAgent', 
    'TestDesignAgent',
    'TestCaseAgent',
    'ApiTestAgent',
    'AutomationAgent',
    'BugAnalyzerAgent',
    'AgentCoordinator'
]