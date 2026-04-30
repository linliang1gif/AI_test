"""
Executor V2 - 真实 HTTP API 测试执行引擎

替代原有 Mock Runner，真正发送 HTTP 请求并执行断言。
"""

from .execution_engine import ExecutionEngineV2
from .http_runner import HttpRunner
from .assertion_engine import AssertionEngineV2
from .schema_validator import SchemaValidator
from .result_writer import ResultWriter
from .auth_manager import AuthManager
from .models import (
    TestCaseV2,
    ExecutionResult,
    AssertionResult,
    AssertionDef,
    HttpRequest,
    HttpResponse,
)

__all__ = [
    "ExecutionEngineV2",
    "HttpRunner",
    "AssertionEngineV2",
    "SchemaValidator",
    "ResultWriter",
    "TestCaseV2",
    "ExecutionResult",
    "AssertionResult",
    "HttpRequest",
    "HttpResponse",
    "AuthManager",
]
