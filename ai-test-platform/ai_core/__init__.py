"""
AI Core - AI调度层
智能测试代理调度和编排系统

这是一个独立的AI调度层，通过import方式调用现有模块，不修改任何已有代码。
"""

__version__ = "1.0.0"
__author__ = "AI Test Platform Team"

from .agents.test_agent import TestAgent
from .workflow.test_workflow import TestWorkflow
from .skills.pytest_skill import PytestSkill
from .orchestration.runner import OrchestrationRunner

__all__ = [
    "TestAgent",
    "TestWorkflow", 
    "PytestSkill",
    "OrchestrationRunner"
]
