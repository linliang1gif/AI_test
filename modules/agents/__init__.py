"""
Agents Module - 智能代理模块

包含各种专用的智能代理：
- DesignAgent: 测试设计代理 - 负责生成测试用例
- ExecutionAgent: 测试执行代理 - 负责执行测试用例
- HealingAgent: 智能自愈代理 - 负责自动修复失败用例
- LearningAgent: 学习型代理 - 负责构建测试反馈闭环
- OptimizationAgent: 测试优化代理 - 负责优化测试用例和执行策略
- TestIntelligenceAgent: 测试智能决策引擎 - 负责测试用例选择和执行计划优化
"""

from .design_agent import DesignAgent
from .execution_agent import ExecutionAgent, ExecutionEnvironment, ExecutionStrategy
from .healing_agent import HealingAgent, FailureCategory, HealingStrategy
from .learning_agent import LearningAgent
from .optimization_agent import TestOptimizationAgent
from .test_intelligence_agent import TestIntelligenceAgent, TestCase, ExecutionDecision

__all__ = [
    'DesignAgent',
    'ExecutionAgent',
    'ExecutionEnvironment',
    'ExecutionStrategy',
    'HealingAgent',
    'FailureCategory',
    'HealingStrategy',
    'LearningAgent',
    'TestOptimizationAgent',
    'TestIntelligenceAgent',
    'TestCase',
    'ExecutionDecision'
]
