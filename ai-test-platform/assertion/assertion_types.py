#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
断言类型定义 - 标准化断言类型和配置
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class AssertionOperator(Enum):
    """断言操作符"""
    EQUALS = "equals"                    # 等于
    NOT_EQUALS = "not_equals"           # 不等于
    GREATER_THAN = "greater_than"       # 大于
    LESS_THAN = "less_than"             # 小于
    GREATER_EQUAL = "greater_equal"     # 大于等于
    LESS_EQUAL = "less_equal"           # 小于等于
    CONTAINS = "contains"               # 包含
    NOT_CONTAINS = "not_contains"       # 不包含
    STARTS_WITH = "starts_with"         # 开始于
    ENDS_WITH = "ends_with"             # 结束于
    MATCHES = "matches"                 # 正则匹配
    IN = "in"                           # 在列表中
    NOT_IN = "not_in"                   # 不在列表中
    EXISTS = "exists"                   # 存在
    NOT_EXISTS = "not_exists"           # 不存在
    IS_TYPE = "is_type"                 # 类型检查
    LENGTH_EQUALS = "length_equals"     # 长度等于
    IS_EMPTY = "is_empty"               # 为空
    NOT_EMPTY = "not_empty"             # 不为空


class AssertionSeverity(Enum):
    """断言严重程度"""
    BLOCKER = "blocker"      # 阻塞级 - 必须通过
    CRITICAL = "critical"    # 严重级 - 核心功能
    MAJOR = "major"          # 主要级 - 重要功能
    MINOR = "minor"          # 次要级 - 一般功能
    TRIVIAL = "trivial"      # 轻微级 - 可选功能


@dataclass
class AssertionConfig:
    """断言配置"""
    name: str                                    # 断言名称
    description: str                             # 断言描述
    operator: AssertionOperator                  # 操作符
    expected: Any                                # 期望值
    actual_path: Optional[str] = None           # 实际值路径(JSON Path)
    severity: AssertionSeverity = AssertionSeverity.MAJOR
    enabled: bool = True                         # 是否启用
    retry_on_fail: bool = False                 # 失败时是否重试
    max_retries: int = 0                        # 最大重试次数
    tags: List[str] = field(default_factory=list)  # 标签
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'name': self.name,
            'description': self.description,
            'operator': self.operator.value,
            'expected': self.expected,
            'actual_path': self.actual_path,
            'severity': self.severity.value,
            'enabled': self.enabled,
            'retry_on_fail': self.retry_on_fail,
            'max_retries': self.max_retries,
            'tags': self.tags,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AssertionConfig':
        """从字典创建"""
        return cls(
            name=data['name'],
            description=data['description'],
            operator=AssertionOperator(data['operator']),
            expected=data['expected'],
            actual_path=data.get('actual_path'),
            severity=AssertionSeverity(data.get('severity', 'major')),
            enabled=data.get('enabled', True),
            retry_on_fail=data.get('retry_on_fail', False),
            max_retries=data.get('max_retries', 0),
            tags=data.get('tags', []),
            metadata=data.get('metadata', {})
        )


@dataclass
class AssertionTemplate:
    """断言模板 - 预定义的常用断言"""
    template_id: str
    name: str
    description: str
    configs: List[AssertionConfig]
    category: str = "general"
    
    def to_dict(self) -> Dict:
        return {
            'template_id': self.template_id,
            'name': self.name,
            'description': self.description,
            'configs': [c.to_dict() for c in self.configs],
            'category': self.category
        }


class AssertionTemplates:
    """预定义断言模板库"""
    
    @staticmethod
    def get_api_success_template() -> AssertionTemplate:
        """API成功响应模板"""
        return AssertionTemplate(
            template_id="api_success",
            name="API成功响应",
            description="验证API返回成功状态",
            category="api",
            configs=[
                AssertionConfig(
                    name="状态码为200",
                    description="HTTP状态码应为200",
                    operator=AssertionOperator.EQUALS,
                    expected=200,
                    actual_path="status_code",
                    severity=AssertionSeverity.BLOCKER
                ),
                AssertionConfig(
                    name="响应时间小于2秒",
                    description="响应时间应小于2秒",
                    operator=AssertionOperator.LESS_THAN,
                    expected=2.0,
                    actual_path="response_time",
                    severity=AssertionSeverity.MAJOR
                ),
                AssertionConfig(
                    name="返回码为0",
                    description="业务返回码应为0",
                    operator=AssertionOperator.EQUALS,
                    expected=0,
                    actual_path="body.code",
                    severity=AssertionSeverity.CRITICAL
                )
            ]
        )
    
    @staticmethod
    def get_api_error_template() -> AssertionTemplate:
        """API错误响应模板"""
        return AssertionTemplate(
            template_id="api_error",
            name="API错误响应",
            description="验证API返回错误状态",
            category="api",
            configs=[
                AssertionConfig(
                    name="状态码为4xx或5xx",
                    description="HTTP状态码应为错误码",
                    operator=AssertionOperator.IN,
                    expected=[400, 401, 403, 404, 500, 502, 503],
                    actual_path="status_code",
                    severity=AssertionSeverity.BLOCKER
                ),
                AssertionConfig(
                    name="包含错误信息",
                    description="响应应包含错误信息",
                    operator=AssertionOperator.EXISTS,
                    expected=True,
                    actual_path="body.error",
                    severity=AssertionSeverity.CRITICAL
                )
            ]
        )
    
    @staticmethod
    def get_data_validation_template() -> AssertionTemplate:
        """数据验证模板"""
        return AssertionTemplate(
            template_id="data_validation",
            name="数据验证",
            description="验证返回数据的完整性和正确性",
            category="data",
            configs=[
                AssertionConfig(
                    name="数据不为空",
                    description="返回的数据字段不应为空",
                    operator=AssertionOperator.NOT_EMPTY,
                    expected=True,
                    actual_path="body.data",
                    severity=AssertionSeverity.CRITICAL
                ),
                AssertionConfig(
                    name="数据类型正确",
                    description="数据类型应符合预期",
                    operator=AssertionOperator.IS_TYPE,
                    expected="dict",
                    actual_path="body.data",
                    severity=AssertionSeverity.MAJOR
                )
            ]
        )
    
    @staticmethod
    def get_all_templates() -> List[AssertionTemplate]:
        """获取所有模板"""
        return [
            AssertionTemplates.get_api_success_template(),
            AssertionTemplates.get_api_error_template(),
            AssertionTemplates.get_data_validation_template()
        ]


# 断言优先级映射
SEVERITY_PRIORITY = {
    AssertionSeverity.BLOCKER: 1,
    AssertionSeverity.CRITICAL: 2,
    AssertionSeverity.MAJOR: 3,
    AssertionSeverity.MINOR: 4,
    AssertionSeverity.TRIVIAL: 5
}
