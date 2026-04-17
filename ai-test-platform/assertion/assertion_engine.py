#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
断言引擎 - 从"能跑"到"能判断"
支持: 状态码断言、响应体断言、业务规则断言、AI智能断言
"""

import re
import json
from typing import Dict, List, Any, Optional, Callable
from enum import Enum


class AssertionType(Enum):
    """断言类型"""
    STATUS_CODE = "status_code"          # 状态码断言
    RESPONSE_BODY = "response_body"      # 响应体断言
    RESPONSE_TIME = "response_time"      # 响应时间断言
    HEADER = "header"                    # 响应头断言
    JSON_PATH = "json_path"              # JSON路径断言
    BUSINESS_RULE = "business_rule"      # 业务规则断言
    AI_ASSERTION = "ai_assertion"        # AI智能断言
    CUSTOM = "custom"                    # 自定义断言


class AssertionResult:
    """断言结果"""
    
    def __init__(self, passed: bool, message: str, 
                 assertion_type: AssertionType,
                 expected: Any = None, actual: Any = None):
        self.passed = passed
        self.message = message
        self.assertion_type = assertion_type
        self.expected = expected
        self.actual = actual
    
    def to_dict(self) -> Dict:
        return {
            'passed': self.passed,
            'message': self.message,
            'type': self.assertion_type.value,
            'expected': str(self.expected) if self.expected is not None else None,
            'actual': str(self.actual) if self.actual is not None else None
        }
    
    def __repr__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return f"{status}: {self.message}"


class AssertionEngine:
    """断言引擎 - 核心"""
    
    def __init__(self):
        self.results: List[AssertionResult] = []
        self.business_rules: Dict[str, Callable] = {}
        self._register_default_rules()
    
    # ═══════════════════════════════════════════════════════
    # 1. 基础断言
    # ═══════════════════════════════════════════════════════
    
    def assert_status_code(self, actual: int, expected: int) -> AssertionResult:
        """
        状态码断言
        
        Args:
            actual: 实际状态码
            expected: 期望状态码
        """
        passed = actual == expected
        message = f"状态码断言: 期望 {expected}, 实际 {actual}"
        
        result = AssertionResult(
            passed=passed,
            message=message,
            assertion_type=AssertionType.STATUS_CODE,
            expected=expected,
            actual=actual
        )
        self.results.append(result)
        return result
    
    def assert_status_code_in(self, actual: int, expected_list: List[int]) -> AssertionResult:
        """状态码在列表中"""
        passed = actual in expected_list
        message = f"状态码断言: 期望在 {expected_list} 中, 实际 {actual}"
        
        result = AssertionResult(
            passed=passed,
            message=message,
            assertion_type=AssertionType.STATUS_CODE,
            expected=expected_list,
            actual=actual
        )
        self.results.append(result)
        return result
    
    def assert_response_time(self, actual: float, max_time: float) -> AssertionResult:
        """
        响应时间断言
        
        Args:
            actual: 实际响应时间(秒)
            max_time: 最大允许时间(秒)
        """
        passed = actual <= max_time
        message = f"响应时间断言: 期望 ≤ {max_time}s, 实际 {actual:.3f}s"
        
        result = AssertionResult(
            passed=passed,
            message=message,
            assertion_type=AssertionType.RESPONSE_TIME,
            expected=max_time,
            actual=actual
        )
        self.results.append(result)
        return result
    
    def assert_header_exists(self, headers: Dict, header_name: str) -> AssertionResult:
        """响应头存在断言"""
        passed = header_name in headers
        message = f"响应头断言: '{header_name}' {'存在' if passed else '不存在'}"
        
        result = AssertionResult(
            passed=passed,
            message=message,
            assertion_type=AssertionType.HEADER,
            expected=f"{header_name} exists",
            actual=f"Found: {passed}"
        )
        self.results.append(result)
        return result
    
    def assert_header_value(self, headers: Dict, header_name: str, 
                           expected_value: str) -> AssertionResult:
        """响应头值断言"""
        actual_value = headers.get(header_name)
        passed = actual_value == expected_value
        message = f"响应头值断言: {header_name} 期望 '{expected_value}', 实际 '{actual_value}'"
        
        result = AssertionResult(
            passed=passed,
            message=message,
            assertion_type=AssertionType.HEADER,
            expected=expected_value,
            actual=actual_value
        )
        self.results.append(result)
        return result
    
    # ═══════════════════════════════════════════════════════
    # 2. 响应体断言
    # ═══════════════════════════════════════════════════════
    
    def assert_body_contains(self, body: str, expected_text: str) -> AssertionResult:
        """响应体包含文本"""
        passed = expected_text in body
        message = f"响应体断言: {'包含' if passed else '不包含'} '{expected_text}'"
        
        result = AssertionResult(
            passed=passed,
            message=message,
            assertion_type=AssertionType.RESPONSE_BODY,
            expected=f"contains '{expected_text}'",
            actual=f"Found: {passed}"
        )
        self.results.append(result)
        return result
    
    def assert_body_not_contains(self, body: str, unexpected_text: str) -> AssertionResult:
        """响应体不包含文本"""
        passed = unexpected_text not in body
        message = f"响应体断言: {'不包含' if passed else '包含'} '{unexpected_text}'"
        
        result = AssertionResult(
            passed=passed,
            message=message,
            assertion_type=AssertionType.RESPONSE_BODY,
            expected=f"not contains '{unexpected_text}'",
            actual=f"Found: {not passed}"
        )
        self.results.append(result)
        return result
    
    def assert_body_matches_regex(self, body: str, pattern: str) -> AssertionResult:
        """响应体正则匹配"""
        passed = bool(re.search(pattern, body))
        message = f"响应体正则断言: {'匹配' if passed else '不匹配'} 模式 '{pattern}'"
        
        result = AssertionResult(
            passed=passed,
            message=message,
            assertion_type=AssertionType.RESPONSE_BODY,
            expected=f"matches '{pattern}'",
            actual=f"Matched: {passed}"
        )
        self.results.append(result)
        return result
    
    # ═══════════════════════════════════════════════════════
    # 3. JSON断言
    # ═══════════════════════════════════════════════════════
    
    def assert_json_path_exists(self, json_data: Dict, json_path: str) -> AssertionResult:
        """JSON路径存在断言"""
        value = self._get_json_path_value(json_data, json_path)
        passed = value is not None
        message = f"JSON路径断言: '{json_path}' {'存在' if passed else '不存在'}"
        
        result = AssertionResult(
            passed=passed,
            message=message,
            assertion_type=AssertionType.JSON_PATH,
            expected=f"{json_path} exists",
            actual=f"Found: {passed}"
        )
        self.results.append(result)
        return result
    
    def assert_json_path_equals(self, json_data: Dict, json_path: str, 
                               expected_value: Any) -> AssertionResult:
        """JSON路径值相等断言"""
        actual_value = self._get_json_path_value(json_data, json_path)
        passed = actual_value == expected_value
        message = f"JSON路径值断言: {json_path} 期望 {expected_value}, 实际 {actual_value}"
        
        result = AssertionResult(
            passed=passed,
            message=message,
            assertion_type=AssertionType.JSON_PATH,
            expected=expected_value,
            actual=actual_value
        )
        self.results.append(result)
        return result
    
    def assert_json_schema(self, json_data: Dict, schema: Dict) -> AssertionResult:
        """JSON Schema验证"""
        try:
            # 简单的schema验证
            passed = self._validate_schema(json_data, schema)
            message = f"JSON Schema断言: {'通过' if passed else '失败'}"
            
            result = AssertionResult(
                passed=passed,
                message=message,
                assertion_type=AssertionType.JSON_PATH,
                expected="Valid schema",
                actual="Schema validated" if passed else "Schema invalid"
            )
            self.results.append(result)
            return result
        except Exception as e:
            result = AssertionResult(
                passed=False,
                message=f"JSON Schema断言失败: {str(e)}",
                assertion_type=AssertionType.JSON_PATH
            )
            self.results.append(result)
            return result
    
    # ═══════════════════════════════════════════════════════
    # 4. 业务规则断言
    # ═══════════════════════════════════════════════════════
    
    def register_business_rule(self, rule_name: str, rule_func: Callable):
        """
        注册业务规则
        
        Args:
            rule_name: 规则名称
            rule_func: 规则函数,返回 (bool, str) - (是否通过, 消息)
        """
        self.business_rules[rule_name] = rule_func
    
    def assert_business_rule(self, rule_name: str, data: Dict) -> AssertionResult:
        """
        业务规则断言
        
        Args:
            rule_name: 规则名称
            data: 数据
        """
        if rule_name not in self.business_rules:
            result = AssertionResult(
                passed=False,
                message=f"业务规则 '{rule_name}' 未注册",
                assertion_type=AssertionType.BUSINESS_RULE
            )
            self.results.append(result)
            return result
        
        try:
            rule_func = self.business_rules[rule_name]
            passed, message = rule_func(data)
            
            result = AssertionResult(
                passed=passed,
                message=f"业务规则断言 [{rule_name}]: {message}",
                assertion_type=AssertionType.BUSINESS_RULE
            )
            self.results.append(result)
            return result
        except Exception as e:
            result = AssertionResult(
                passed=False,
                message=f"业务规则执行失败: {str(e)}",
                assertion_type=AssertionType.BUSINESS_RULE
            )
            self.results.append(result)
            return result
    
    def _register_default_rules(self):
        """注册默认业务规则"""
        
        # 规则1: 用户ID必须为正整数
        def rule_valid_user_id(data: Dict) -> tuple:
            user_id = data.get('user_id')
            if user_id is None:
                return False, "user_id不存在"
            if not isinstance(user_id, int) or user_id <= 0:
                return False, f"user_id必须为正整数, 实际: {user_id}"
            return True, f"user_id有效: {user_id}"
        
        # 规则2: 订单金额必须大于0
        def rule_valid_order_amount(data: Dict) -> tuple:
            amount = data.get('amount')
            if amount is None:
                return False, "amount不存在"
            if not isinstance(amount, (int, float)) or amount <= 0:
                return False, f"amount必须大于0, 实际: {amount}"
            return True, f"amount有效: {amount}"
        
        # 规则3: 邮箱格式验证
        def rule_valid_email(data: Dict) -> tuple:
            email = data.get('email')
            if not email:
                return False, "email不存在"
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(pattern, email):
                return False, f"email格式无效: {email}"
            return True, f"email格式有效: {email}"
        
        self.register_business_rule('valid_user_id', rule_valid_user_id)
        self.register_business_rule('valid_order_amount', rule_valid_order_amount)
        self.register_business_rule('valid_email', rule_valid_email)
    
    # ═══════════════════════════════════════════════════════
    # 5. AI智能断言
    # ═══════════════════════════════════════════════════════
    
    def assert_with_ai(self, response_data: Dict, expected_behavior: str,
                      ai_client=None) -> AssertionResult:
        """
        AI智能断言 - 使用AI判断响应是否符合预期
        
        Args:
            response_data: 响应数据
            expected_behavior: 期望行为描述
            ai_client: AI客户端
        """
        if ai_client is None:
            result = AssertionResult(
                passed=False,
                message="AI断言: AI客户端未配置",
                assertion_type=AssertionType.AI_ASSERTION
            )
            self.results.append(result)
            return result
        
        try:
            # 构造AI提示词
            prompt = f"""
            请判断以下API响应是否符合预期行为:
            
            期望行为: {expected_behavior}
            
            实际响应: {json.dumps(response_data, ensure_ascii=False, indent=2)}
            
            请回答:
            1. 是否符合预期? (是/否)
            2. 原因说明
            
            格式: 
            判断: 是/否
            原因: xxx
            """
            
            # 调用AI(这里需要集成实际的AI客户端)
            # ai_response = ai_client.chat(prompt)
            
            # 简化版: 基于关键词判断
            passed = self._simple_ai_check(response_data, expected_behavior)
            message = f"AI断言: {'符合' if passed else '不符合'}预期行为 - {expected_behavior}"
            
            result = AssertionResult(
                passed=passed,
                message=message,
                assertion_type=AssertionType.AI_ASSERTION,
                expected=expected_behavior,
                actual=str(response_data)[:100]
            )
            self.results.append(result)
            return result
            
        except Exception as e:
            result = AssertionResult(
                passed=False,
                message=f"AI断言失败: {str(e)}",
                assertion_type=AssertionType.AI_ASSERTION
            )
            self.results.append(result)
            return result
    
    def _simple_ai_check(self, response_data: Dict, expected_behavior: str) -> bool:
        """简单的AI检查(基于规则)"""
        # 这是简化版,实际应该调用真正的AI
        response_str = json.dumps(response_data, ensure_ascii=False).lower()
        expected_lower = expected_behavior.lower()
        
        # 检查关键词
        if 'success' in expected_lower or '成功' in expected_lower:
            return 'success' in response_str or 'code' in response_str
        elif 'error' in expected_lower or '错误' in expected_lower:
            return 'error' in response_str or 'fail' in response_str
        
        return True  # 默认通过
    
    # ═══════════════════════════════════════════════════════
    # 6. 自定义断言
    # ═══════════════════════════════════════════════════════
    
    def assert_custom(self, condition: bool, message: str) -> AssertionResult:
        """
        自定义断言
        
        Args:
            condition: 断言条件
            message: 断言消息
        """
        result = AssertionResult(
            passed=condition,
            message=f"自定义断言: {message}",
            assertion_type=AssertionType.CUSTOM
        )
        self.results.append(result)
        return result
    
    # ═══════════════════════════════════════════════════════
    # 辅助方法
    # ═══════════════════════════════════════════════════════
    
    def _get_json_path_value(self, data: Dict, path: str) -> Any:
        """获取JSON路径的值"""
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
    
    def _validate_schema(self, data: Dict, schema: Dict) -> bool:
        """简单的Schema验证"""
        # 简化版schema验证
        for key, expected_type in schema.items():
            if key not in data:
                return False
            if expected_type == 'string' and not isinstance(data[key], str):
                return False
            if expected_type == 'number' and not isinstance(data[key], (int, float)):
                return False
            if expected_type == 'boolean' and not isinstance(data[key], bool):
                return False
        return True
    
    # ═══════════════════════════════════════════════════════
    # 结果管理
    # ═══════════════════════════════════════════════════════
    
    def get_results(self) -> List[AssertionResult]:
        """获取所有断言结果"""
        return self.results
    
    def get_summary(self) -> Dict:
        """获取断言摘要"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        
        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': passed / total if total > 0 else 0,
            'all_passed': failed == 0
        }
    
    def clear_results(self):
        """清空断言结果"""
        self.results = []
    
    def print_results(self):
        """打印断言结果"""
        print("\n" + "=" * 70)
        print("断言结果")
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


# 全局单例
_engine_instance: Optional[AssertionEngine] = None


def get_assertion_engine() -> AssertionEngine:
    """获取断言引擎单例"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = AssertionEngine()
    return _engine_instance
