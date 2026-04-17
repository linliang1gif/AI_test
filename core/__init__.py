#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心数据模型层 - Single Source of Truth
所有模块必须使用这里定义的数据结构
"""

from core.models import (
    TestCase,
    ExecutionResult,
    TestReport,
    HealingRecord,
    TestPoint,
    APISpec,
    ExecutionConfig,
    Assertion,
    create_test_case,
    create_execution_result,
)

from core.enums import (
    TestCaseStatus,
    TestCasePriority,
    DataType,
    ExpectedBehavior,
    AssertionOperator,
    HealingLevel,
    RiskLevel,
    TestType,
    ExecutionMode,
    ReportFormat,
)

from core.interfaces import (
    ITestCaseGenerator,
    IExecutor,
    IHealingEngine,
    IReportGenerator,
    IDataManager,
)

__all__ = [
    # 数据模型
    'TestCase',
    'ExecutionResult',
    'TestReport',
    'HealingRecord',
    'TestPoint',
    'APISpec',
    'ExecutionConfig',
    'Assertion',
    # 工厂函数
    'create_test_case',
    'create_execution_result',
    # 枚举
    'TestCaseStatus',
    'TestCasePriority',
    'DataType',
    'ExpectedBehavior',
    'AssertionOperator',
    'HealingLevel',
    'RiskLevel',
    'TestType',
    'ExecutionMode',
    'ReportFormat',
    # 接口
    'ITestCaseGenerator',
    'IExecutor',
    'IHealingEngine',
    'IReportGenerator',
    'IDataManager',
]

__version__ = '1.0.0'
