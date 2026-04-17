#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
断言验证器 - 执行断言并验证结果
"""

import re
import json
from typing import Dict, List, Any, Optional
from assertion.assertion_types import (
    AssertionConfig, AssertionOperator, AssertionSeverity
)
from assertion.assertion_engine import AssertionResult, AssertionType


class AssertionValidator:
    """断言验证器 - 执行断言配置"""
    
    def __init__(self):
        self.results: List[AssertionResult] = []
    
    def validate(self, config: AssertionConfig, response_data: Dict) -> AssertionResult:
        """
        验证单个断言
        
        Args:
            config: 断言配置
            response_data: 响应数据
        
        Returns:
            断言结果
        """
        if not config.enabled:
            return AssertionResult(
                passed=True,
                message=f"断言已禁用: {config.name}",
                assertion_type=AssertionType.CUSTOM
            )
        
        # 获取实际值
        actual_value = self._get_actual_value(response_data, config.actual_path)
        
        # 执行断言
        result = self._execute_assertion(config, actual_value)
        
        # 记录结果
        self.results.append(result)
        
        # 如果失败且需要重试
        if not result.passed and config.retry_on_fail:
            for retry in range(config.max_retries):
                print(f"  重试 {retry + 1}/{config.max_retries}...")
                result = self._execute_assertion(config, actual_value)
                self.results.append(result)
                if result.passed:
                    break
        
        return result
    
    def validate_all(self, configs: List[AssertionConfig],
                    response_data: Dict) -> List[AssertionResult]:
        """
        验证所有断言
        
        Args:
            configs: 断言配置列表
            response_data: 响应数据
        
        Returns:
            断言结果列表
        """
        results = []
        for config in configs:
            result = self.validate(config, response_data)
            results.append(result)
        return results
    
    def _get_actual_value(self, data: Dict, path: Optional[str]) -> Any:
        """获取实际值"""
        if path is None:
            return data
        
        try:
            keys = path.split('.')
            value = data
            for key in keys:
                if isinstance(value, dict):
                    value = value.get(key)
                elif isinstance(value, list) and key.isdigit():
                    value = value[int(key)]
                else:
                    return None
            return value
        except:
            return None
    
    def _execute_assertion(self, config: AssertionConfig,
                          actual_value: Any) -> AssertionResult:
        """执行断言"""
        operator = config.operator
        expected = config.expected
        
        try:
            if operator == AssertionOperator.EQUALS:
                passed = actual_value == expected
                message = f"{config.name}: 期望 {expected}, 实际 {actual_value}"
            
            elif operator == AssertionOperator.NOT_EQUALS:
                passed = actual_value != expected
                message = f"{config.name}: 不应等于 {expected}, 实际 {actual_value}"
            
            elif operator == AssertionOperator.GREATER_THAN:
                passed = actual_value > expected
                message = f"{config.name}: 应 > {expected}, 实际 {actual_value}"
            
            elif operator == AssertionOperator.LESS_THAN:
                passed = actual_value < expected
                message = f"{config.name}: 应 < {expected}, 实际 {actual_value}"
            
            elif operator == AssertionOperator.GREATER_EQUAL:
                passed = actual_value >= expected
                message = f"{config.name}: 应 >= {expected}, 实际 {actual_value}"
            
            elif operator == AssertionOperator.LESS_EQUAL:
                passed = actual_value <= expected
                message = f"{config.name}: 应 <= {expected}, 实际 {actual_value}"
            
            elif operator == AssertionOperator.CONTAINS:
                passed = expected in str(actual_value)
                message = f"{config.name}: 应包含 '{expected}'"
            
            elif operator == AssertionOperator.NOT_CONTAINS:
                passed = expected not in str(actual_value)
                message = f"{config.name}: 不应包含 '{expected}'"
            
            elif operator == AssertionOperator.STARTS_WITH:
                passed = str(actual_value).startswith(str(expected))
                message = f"{config.name}: 应以 '{expected}' 开始"
            
            elif operator == AssertionOperator.ENDS_WITH:
                passed = str(actual_value).endswith(str(expected))
                message = f"{config.name}: 应以 '{expected}' 结束"
            
            elif operator == AssertionOperator.MATCHES:
                passed = bool(re.match(expected, str(actual_value)))
                message = f"{config.name}: 应匹配正则 '{expected}'"
            
            elif operator == AssertionOperator.IN:
                passed = actual_value in expected
                message = f"{config.name}: 应在 {expected} 中"
            
            elif operator == AssertionOperator.NOT_IN:
                passed = actual_value not in expected
                message = f"{config.name}: 不应在 {expected} 中"
            
            elif operator == AssertionOperator.EXISTS:
                passed = actual_value is not None
                message = f"{config.name}: 应存在"
            
            elif operator == AssertionOperator.NOT_EXISTS:
                passed = actual_value is None
                message = f"{config.name}: 不应存在"
            
            elif operator == AssertionOperator.IS_TYPE:
                type_map = {
                    'string': str,
                    'number': (int, float),
                    'integer': int,
                    'float': float,
                    'boolean': bool,
                    'dict': dict,
                    'object': dict,
                    'list': list,
                    'array': list
                }
                expected_type = type_map.get(expected, str)
                passed = isinstance(actual_value, expected_type)
                message = f"{config.name}: 类型应为 {expected}"
            
            elif operator == AssertionOperator.LENGTH_EQUALS:
                actual_length = len(actual_value) if actual_value else 0
                passed = actual_length == expected
                message = f"{config.name}: 长度应为 {expected}, 实际 {actual_length}"
            
            elif operator == AssertionOperator.IS_EMPTY:
                passed = not actual_value
                message = f"{config.name}: 应为空"
            
            elif operator == AssertionOperator.NOT_EMPTY:
                passed = bool(actual_value)
                message = f"{config.name}: 不应为空"
            
            else:
                passed = False
                message = f"{config.name}: 未知操作符 {operator}"
            
            return AssertionResult(
                passed=passed,
                message=message,
                assertion_type=AssertionType.CUSTOM,
                expected=expected,
                actual=actual_value
            )
        
        except Exception as e:
            return AssertionResult(
                passed=False,
                message=f"{config.name}: 执行失败 - {str(e)}",
                assertion_type=AssertionType.CUSTOM,
                expected=expected,
                actual=actual_value
            )
    
    def get_summary(self) -> Dict:
        """获取验证摘要"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        
        # 按严重程度统计失败
        blocker_failed = 0
        critical_failed = 0
        
        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': passed / total if total > 0 else 0,
            'all_passed': failed == 0,
            'blocker_failed': blocker_failed,
            'critical_failed': critical_failed
        }
    
    def print_results(self):
        """打印验证结果"""
        print("\n" + "=" * 70)
        print("断言验证结果")
        print("=" * 70)
        
        for i, result in enumerate(self.results, 1):
            print(f"{i}. {result}")
        
        summary = self.get_summary()
        print("\n" + "-" * 70)
        print(f"总计: {summary['total']}")
        print(f"通过: {summary['passed']} ✅")
        print(f"失败: {summary['failed']} ❌")
        print(f"通过率: {summary['pass_rate']:.1%}")
        print("=" * 70)
    
    def clear_results(self):
        """清空结果"""
        self.results = []


# 使用示例
if __name__ == "__main__":
    from assertion.assertion_builder import AssertionBuilder
    
    # 创建断言配置
    builder = AssertionBuilder()
    configs = (builder
               .new_assertion("状态码200").equals(200).at_path("status_code").blocker()
               .new_assertion("响应时间<1秒").less_than(1.0).at_path("response_time").major()
               .new_assertion("返回码为0").equals(0).at_path("body.code").critical()
               .new_assertion("数据不为空").not_empty().at_path("body.data").critical()
               .new_assertion("用户ID存在").exists().at_path("body.data.user_id").major()
               .build())
    
    # 模拟响应数据
    response_data = {
        'status_code': 200,
        'response_time': 0.5,
        'body': {
            'code': 0,
            'message': 'success',
            'data': {
                'user_id': 12345,
                'username': 'test_user'
            }
        }
    }
    
    # 验证断言
    validator = AssertionValidator()
    results = validator.validate_all(configs, response_data)
    
    # 打印结果
    validator.print_results()
    
    # 测试失败场景
    print("\n\n测试失败场景:")
    response_data_fail = {
        'status_code': 500,
        'response_time': 2.5,
        'body': {
            'code': -1,
            'message': 'error'
        }
    }
    
    validator2 = AssertionValidator()
    results2 = validator2.validate_all(configs, response_data_fail)
    validator2.print_results()
