#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
断言构建器 - 流式API构建断言
"""

from typing import Any, List, Optional, Dict
from assertion.assertion_types import (
    AssertionConfig, AssertionOperator, AssertionSeverity,
    AssertionTemplate, AssertionTemplates
)


class AssertionBuilder:
    """断言构建器 - 提供流式API"""
    
    def __init__(self):
        self._configs: List[AssertionConfig] = []
        self._current_config: Optional[Dict[str, Any]] = None
    
    def new_assertion(self, name: str, description: str = "") -> 'AssertionBuilder':
        """
        开始构建新断言
        
        Args:
            name: 断言名称
            description: 断言描述
        """
        if self._current_config:
            # 保存上一个断言
            self._save_current()
        
        self._current_config = {
            'name': name,
            'description': description or name,
            'operator': None,
            'expected': None,
            'actual_path': None,
            'severity': AssertionSeverity.MAJOR,
            'enabled': True,
            'retry_on_fail': False,
            'max_retries': 0,
            'tags': [],
            'metadata': {}
        }
        return self
    
    def equals(self, expected: Any) -> 'AssertionBuilder':
        """等于断言"""
        self._current_config['operator'] = AssertionOperator.EQUALS
        self._current_config['expected'] = expected
        return self
    
    def not_equals(self, expected: Any) -> 'AssertionBuilder':
        """不等于断言"""
        self._current_config['operator'] = AssertionOperator.NOT_EQUALS
        self._current_config['expected'] = expected
        return self
    
    def greater_than(self, expected: Any) -> 'AssertionBuilder':
        """大于断言"""
        self._current_config['operator'] = AssertionOperator.GREATER_THAN
        self._current_config['expected'] = expected
        return self
    
    def less_than(self, expected: Any) -> 'AssertionBuilder':
        """小于断言"""
        self._current_config['operator'] = AssertionOperator.LESS_THAN
        self._current_config['expected'] = expected
        return self
    
    def contains(self, expected: Any) -> 'AssertionBuilder':
        """包含断言"""
        self._current_config['operator'] = AssertionOperator.CONTAINS
        self._current_config['expected'] = expected
        return self
    
    def not_contains(self, expected: Any) -> 'AssertionBuilder':
        """不包含断言"""
        self._current_config['operator'] = AssertionOperator.NOT_CONTAINS
        self._current_config['expected'] = expected
        return self
    
    def matches(self, pattern: str) -> 'AssertionBuilder':
        """正则匹配断言"""
        self._current_config['operator'] = AssertionOperator.MATCHES
        self._current_config['expected'] = pattern
        return self
    
    def in_list(self, expected_list: List[Any]) -> 'AssertionBuilder':
        """在列表中断言"""
        self._current_config['operator'] = AssertionOperator.IN
        self._current_config['expected'] = expected_list
        return self
    
    def exists(self) -> 'AssertionBuilder':
        """存在断言"""
        self._current_config['operator'] = AssertionOperator.EXISTS
        self._current_config['expected'] = True
        return self
    
    def not_exists(self) -> 'AssertionBuilder':
        """不存在断言"""
        self._current_config['operator'] = AssertionOperator.NOT_EXISTS
        self._current_config['expected'] = True
        return self
    
    def is_type(self, expected_type: str) -> 'AssertionBuilder':
        """类型检查断言"""
        self._current_config['operator'] = AssertionOperator.IS_TYPE
        self._current_config['expected'] = expected_type
        return self
    
    def not_empty(self) -> 'AssertionBuilder':
        """不为空断言"""
        self._current_config['operator'] = AssertionOperator.NOT_EMPTY
        self._current_config['expected'] = True
        return self
    
    def at_path(self, json_path: str) -> 'AssertionBuilder':
        """指定JSON路径"""
        self._current_config['actual_path'] = json_path
        return self
    
    def with_severity(self, severity: AssertionSeverity) -> 'AssertionBuilder':
        """设置严重程度"""
        self._current_config['severity'] = severity
        return self
    
    def blocker(self) -> 'AssertionBuilder':
        """设置为阻塞级"""
        return self.with_severity(AssertionSeverity.BLOCKER)
    
    def critical(self) -> 'AssertionBuilder':
        """设置为严重级"""
        return self.with_severity(AssertionSeverity.CRITICAL)
    
    def major(self) -> 'AssertionBuilder':
        """设置为主要级"""
        return self.with_severity(AssertionSeverity.MAJOR)
    
    def with_retry(self, max_retries: int = 3) -> 'AssertionBuilder':
        """启用重试"""
        self._current_config['retry_on_fail'] = True
        self._current_config['max_retries'] = max_retries
        return self
    
    def with_tags(self, *tags: str) -> 'AssertionBuilder':
        """添加标签"""
        self._current_config['tags'].extend(tags)
        return self
    
    def with_metadata(self, **metadata) -> 'AssertionBuilder':
        """添加元数据"""
        self._current_config['metadata'].update(metadata)
        return self
    
    def _save_current(self):
        """保存当前断言配置"""
        if self._current_config and self._current_config['operator']:
            config = AssertionConfig(**self._current_config)
            self._configs.append(config)
    
    def build(self) -> List[AssertionConfig]:
        """构建并返回所有断言配置"""
        if self._current_config:
            self._save_current()
            self._current_config = None
        return self._configs
    
    def build_one(self) -> Optional[AssertionConfig]:
        """构建并返回单个断言配置"""
        configs = self.build()
        return configs[0] if configs else None
    
    def reset(self) -> 'AssertionBuilder':
        """重置构建器"""
        self._configs = []
        self._current_config = None
        return self
    
    # ═══════════════════════════════════════════════════════
    # 快捷方法 - 常用断言组合
    # ═══════════════════════════════════════════════════════
    
    def status_code_200(self) -> 'AssertionBuilder':
        """快捷: 状态码200"""
        return self.new_assertion(
            "状态码为200",
            "HTTP状态码应为200"
        ).equals(200).at_path("status_code").blocker()
    
    def response_time_under(self, seconds: float) -> 'AssertionBuilder':
        """快捷: 响应时间小于指定秒数"""
        return self.new_assertion(
            f"响应时间小于{seconds}秒",
            f"响应时间应小于{seconds}秒"
        ).less_than(seconds).at_path("response_time").major()
    
    def business_code_success(self, code_path: str = "body.code") -> 'AssertionBuilder':
        """快捷: 业务返回码成功"""
        return self.new_assertion(
            "业务返回码为0",
            "业务返回码应为0表示成功"
        ).equals(0).at_path(code_path).critical()
    
    def data_not_empty(self, data_path: str = "body.data") -> 'AssertionBuilder':
        """快捷: 数据不为空"""
        return self.new_assertion(
            "数据不为空",
            "返回的数据不应为空"
        ).not_empty().at_path(data_path).critical()
    
    def from_template(self, template: AssertionTemplate) -> 'AssertionBuilder':
        """从模板创建断言"""
        for config in template.configs:
            self._configs.append(config)
        return self
    
    def api_success_assertions(self) -> 'AssertionBuilder':
        """快捷: API成功响应的标准断言"""
        template = AssertionTemplates.get_api_success_template()
        return self.from_template(template)
    
    def api_error_assertions(self) -> 'AssertionBuilder':
        """快捷: API错误响应的标准断言"""
        template = AssertionTemplates.get_api_error_template()
        return self.from_template(template)


# 便捷函数
def create_assertion() -> AssertionBuilder:
    """创建断言构建器"""
    return AssertionBuilder()


def quick_assertions() -> AssertionBuilder:
    """快速创建常用断言"""
    return (AssertionBuilder()
            .status_code_200()
            .response_time_under(2.0)
            .business_code_success()
            .data_not_empty())


# 使用示例
if __name__ == "__main__":
    # 示例1: 流式API构建单个断言
    builder = AssertionBuilder()
    config = (builder
              .new_assertion("用户ID必须为正整数", "验证用户ID的有效性")
              .greater_than(0)
              .at_path("body.data.user_id")
              .critical()
              .with_tags("user", "validation")
              .build_one())
    
    print("示例1 - 单个断言:")
    print(config.to_dict())
    print()
    
    # 示例2: 构建多个断言
    builder = AssertionBuilder()
    configs = (builder
               .new_assertion("状态码200").equals(200).at_path("status_code").blocker()
               .new_assertion("响应时间<1秒").less_than(1.0).at_path("response_time").major()
               .new_assertion("返回码为0").equals(0).at_path("body.code").critical()
               .build())
    
    print("示例2 - 多个断言:")
    for config in configs:
        print(f"  - {config.name}: {config.operator.value} {config.expected}")
    print()
    
    # 示例3: 使用快捷方法
    configs = quick_assertions().build()
    print("示例3 - 快捷断言:")
    for config in configs:
        print(f"  - {config.name}")
    print()
    
    # 示例4: 使用模板
    builder = AssertionBuilder()
    configs = builder.api_success_assertions().build()
    print("示例4 - 模板断言:")
    for config in configs:
        print(f"  - {config.name} [{config.severity.value}]")
