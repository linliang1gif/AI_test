#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心数据模型 - Single Source of Truth
所有模块必须使用这里定义的数据结构
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from core.enums import (
    TestCaseStatus,
    TestCasePriority,
    DataType,
    ExpectedBehavior,
    AssertionOperator,
    HealingLevel,
    RiskLevel,
    TestType,
)

# ==================== 核心数据模型 ====================

@dataclass
class TestCase:
    """测试用例 - 唯一定义"""
    id: str
    title: str
    module: str
    priority: TestCasePriority
    status: TestCaseStatus = TestCaseStatus.PENDING
    
    # 测试步骤
    steps: List[str] = field(default_factory=list)
    expected: str = ""
    
    # 🆕 数据语义字段
    data_type: DataType = DataType.VALID
    expected_behavior: ExpectedBehavior = ExpectedBehavior.SUCCESS
    
    # 执行配置
    execution_config: Optional[Dict[str, Any]] = None
    
    # 断言配置
    assertions: List[Dict[str, Any]] = field(default_factory=list)
    
    # 元数据
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: str = "system"
    tags: List[str] = field(default_factory=list)
    
    # 关联信息
    test_point_id: Optional[str] = None
    api_id: Optional[str] = None
    dataset_id: Optional[str] = None

@dataclass
class ExecutionConfig:
    """执行配置"""
    method: str                              # HTTP方法
    url: str                                 # 请求URL
    headers: Dict[str, str] = field(default_factory=dict)
    params: Dict[str, Any] = field(default_factory=dict)
    body: Optional[Dict[str, Any]] = None
    timeout: int = 30
    retry_count: int = 0
    retry_delay: float = 1.0

@dataclass
class Assertion:
    """断言定义"""
    field: str                               # 断言字段（支持JSONPath）
    operator: AssertionOperator              # 断言操作符
    expected: Any                            # 期望值
    description: str = ""                    # 断言描述

@dataclass
class ExecutionResult:
    """执行结果"""
    test_case_id: str
    status: TestCaseStatus
    start_time: datetime
    end_time: datetime
    duration: float                          # 秒
    
    # 请求响应
    request: Optional[Dict[str, Any]] = None
    response: Optional[Dict[str, Any]] = None
    status_code: Optional[int] = None
    
    # 断言结果
    assertions_passed: int = 0
    assertions_failed: int = 0
    assertion_details: List[Dict[str, Any]] = field(default_factory=list)
    
    # 错误信息
    error: Optional[str] = None
    error_type: Optional[str] = None
    stack_trace: Optional[str] = None
    
    # 修复信息
    healing_applied: bool = False
    healing_level: Optional[HealingLevel] = None
    healing_details: Optional[str] = None

@dataclass
class HealingRecord:
    """修复记录"""
    test_case_id: str
    error_type: str
    healing_level: HealingLevel
    healing_strategy: str
    success: bool
    timestamp: datetime
    details: str = ""
    retry_count: int = 0

@dataclass
class TestReport:
    """测试报告"""
    report_id: str
    title: str
    start_time: datetime
    end_time: datetime
    duration: float
    
    # 统计信息
    total_tests: int
    passed: int
    failed: int
    skipped: int
    pass_rate: float
    
    # 测试结果
    results: List[ExecutionResult] = field(default_factory=list)
    
    # 修复信息
    healing_summary: Dict[str, int] = field(default_factory=dict)
    healed_cases: List[str] = field(default_factory=list)
    
    # 元数据
    environment: str = "test"
    tags: List[str] = field(default_factory=list)

@dataclass
class TestPoint:
    """测试点"""
    id: str
    name: str
    description: str
    risk_level: RiskLevel
    test_type: TestType
    module: str
    priority: TestCasePriority
    
    # 关联信息
    api_path: Optional[str] = None
    api_method: Optional[str] = None
    
    # 元数据
    created_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)

@dataclass
class APISpec:
    """API规范"""
    path: str
    method: str
    summary: str = ""
    description: str = ""
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    request_body: Optional[Dict[str, Any]] = None
    responses: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

# ==================== 工厂函数 ====================

def create_test_case(
    id: str,
    title: str,
    module: str,
    priority: str = "medium",
    **kwargs
) -> TestCase:
    """创建测试用例的工厂函数"""
    # 转换字符串为枚举
    if isinstance(priority, str):
        priority = TestCasePriority(priority)
    
    # 处理 data_type
    if 'data_type' in kwargs and isinstance(kwargs['data_type'], str):
        kwargs['data_type'] = DataType(kwargs['data_type'])
    
    # 处理 expected_behavior
    if 'expected_behavior' in kwargs and isinstance(kwargs['expected_behavior'], str):
        kwargs['expected_behavior'] = ExpectedBehavior(kwargs['expected_behavior'])
    
    # 处理 status
    if 'status' in kwargs and isinstance(kwargs['status'], str):
        kwargs['status'] = TestCaseStatus(kwargs['status'])
    
    return TestCase(
        id=id,
        title=title,
        module=module,
        priority=priority,
        **kwargs
    )

def create_execution_result(
    test_case_id: str,
    status: str,
    start_time: datetime,
    end_time: datetime,
    **kwargs
) -> ExecutionResult:
    """创建执行结果的工厂函数"""
    # 转换字符串为枚举
    if isinstance(status, str):
        status = TestCaseStatus(status)
    
    # 处理 healing_level
    if 'healing_level' in kwargs and isinstance(kwargs['healing_level'], str):
        kwargs['healing_level'] = HealingLevel(kwargs['healing_level'])
    
    return ExecutionResult(
        test_case_id=test_case_id,
        status=status,
        start_time=start_time,
        end_time=end_time,
        duration=(end_time - start_time).total_seconds(),
        **kwargs
    )
