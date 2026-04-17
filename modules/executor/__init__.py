"""
测试执行模块
"""
from .execution_engine import ExecutionEngine
from .api_runner import ApiRunner
from .ui_runner import UiRunner
from .integration_runner import IntegrationRunner

# ExecutionResult, TestCaseStatus, TestType 现在从 core 导入
from core import ExecutionResult, TestCaseStatus, TestType

__all__ = [
    'ExecutionEngine',
    'ExecutionResult',
    'TestCaseStatus',
    'TestType',
    'ApiRunner',
    'UiRunner',
    'IntegrationRunner'
]
