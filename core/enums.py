#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心枚举定义
"""

from enum import Enum

# ==================== 测试用例相关 ====================

class TestCaseStatus(Enum):
    """测试用例状态"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"

class TestCasePriority(Enum):
    """测试用例优先级"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

# ==================== 数据类型相关 ====================

class DataType(Enum):
    """测试数据类型"""
    VALID = "valid"           # 正常数据
    BOUNDARY = "boundary"     # 边界数据
    INVALID = "invalid"       # 异常数据
    NULL = "null"             # 空值
    EMPTY = "empty"           # 空字符串

class ExpectedBehavior(Enum):
    """预期行为"""
    SUCCESS = "success"              # 成功响应 (200-299)
    CLIENT_ERROR = "client_error"    # 客户端错误 (400-499)
    SERVER_ERROR = "server_error"    # 服务器错误 (500-599)

# ==================== 断言相关 ====================

class AssertionOperator(Enum):
    """断言操作符"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    IN = "in"
    NOT_IN = "not_in"
    MATCHES = "matches"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"
    IS_TYPE = "is_type"

# ==================== 修复相关 ====================

class HealingLevel(Enum):
    """修复层级"""
    L1_RETRY = "L1"          # 环境问题（重试）
    L2_DATA = "L2"           # 数据问题（重建数据）
    L3_TOLERANCE = "L3"      # 不稳定（容错）
    L4_MANUAL = "L4"         # 断言失败（人工）

# ==================== 测试类型相关 ====================

class RiskLevel(Enum):
    """风险等级"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class TestType(Enum):
    """测试类型"""
    FUNCTIONAL = "functional"      # 功能测试
    PERFORMANCE = "performance"    # 性能测试
    SECURITY = "security"          # 安全测试
    COMPATIBILITY = "compatibility" # 兼容性测试
    BOUNDARY = "boundary"          # 边界测试
    EXCEPTION = "exception"        # 异常测试

# ==================== 执行相关 ====================

class ExecutionMode(Enum):
    """执行模式"""
    SEQUENTIAL = "sequential"      # 顺序执行
    PARALLEL = "parallel"          # 并行执行
    DISTRIBUTED = "distributed"    # 分布式执行

# ==================== 报告相关 ====================

class ReportFormat(Enum):
    """报告格式"""
    JSON = "json"
    HTML = "html"
    TXT = "txt"
    PDF = "pdf"
    EXCEL = "excel"
