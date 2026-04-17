#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI辅助断言生成器 - 使用AI智能生成断言
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from assertion.assertion_types import (
    AssertionConfig, AssertionOperator, AssertionSeverity
)
from assertion.assertion_builder import AssertionBuilder


class AIAssertionGenerator:
    """AI辅助断言生成器"""
    
    def __init__(self, ai_client=None):
        """
        初始化
        
        Args:
            ai_client: AI客户端(可选)
        """
        self.ai_client = ai_client
    
    def generate_from_api_spec(self, api_spec: Dict) -> List[AssertionConfig]:
        """
        根据API规范生成断言
        
        Args:
            api_spec: API规范 {
                'endpoint': '/api/users',
                'method': 'GET',
                'description': '获取用户列表',
                'response_schema': {...}
            }
        
        Returns:
            断言配置列表
        """
        builder = AssertionBuilder()
        
        # 基础断言
        builder.status_code_200()
        builder.response_time_under(2.0)
        
        # 根据响应schema生成断言
        if 'response_schema' in api_spec:
            schema = api_spec['response_schema']
            self._generate_from_schema(builder, schema, "body")
        
        # 根据描述生成业务断言
        if 'description' in api_spec and self.ai_client:
            business_assertions = self._generate_business_assertions(
                api_spec['description'],
                api_spec
            )
            for assertion in business_assertions:
                builder._configs.append(assertion)
        
        return builder.build()
    
    def generate_from_test_case(self, test_case: Dict) -> List[AssertionConfig]:
        """
        根据测试用例生成断言
        
        Args:
            test_case: 测试用例 {
                'title': '测试用户登录',
                'precondition': '用户已注册',
                'steps': [...],
                'expected': '登录成功,返回用户信息'
            }
        
        Returns:
            断言配置列表
        """
        if not self.ai_client:
            # 没有AI客户端,返回基础断言
            return AssertionBuilder().api_success_assertions().build()
        
        # 使用AI生成断言
        prompt = self._build_testcase_prompt(test_case)
        
        try:
            # 调用AI
            response = self._call_ai(prompt)
            assertions = self._parse_ai_response(response)
            return assertions
        except Exception as e:
            print(f"AI生成断言失败: {e}")
            # 返回基础断言
            return AssertionBuilder().api_success_assertions().build()
    
    def generate_from_requirement(self, requirement: str) -> List[AssertionConfig]:
        """
        根据需求描述生成断言
        
        Args:
            requirement: 需求描述
        
        Returns:
            断言配置列表
        """
        if not self.ai_client:
            return AssertionBuilder().api_success_assertions().build()
        
        prompt = f"""
        根据以下需求描述,生成测试断言:
        
        需求: {requirement}
        
        请生成JSON格式的断言列表,每个断言包含:
        - name: 断言名称
        - description: 断言描述
        - operator: 操作符(equals/contains/greater_than等)
        - expected: 期望值
        - actual_path: JSON路径
        - severity: 严重程度(blocker/critical/major/minor)
        
        示例:
        [
            {{
                "name": "状态码为200",
                "description": "HTTP状态码应为200",
                "operator": "equals",
                "expected": 200,
                "actual_path": "status_code",
                "severity": "blocker"
            }}
        ]
        
        请只返回JSON数组,不要其他内容。
        """
        
        try:
            response = self._call_ai(prompt)
            assertions = self._parse_ai_response(response)
            return assertions
        except Exception as e:
            print(f"AI生成断言失败: {e}")
            return AssertionBuilder().api_success_assertions().build()
    
    def enhance_assertions(self, existing_assertions: List[AssertionConfig],
                          context: Dict) -> List[AssertionConfig]:
        """
        增强现有断言
        
        Args:
            existing_assertions: 现有断言列表
            context: 上下文信息
        
        Returns:
            增强后的断言列表
        """
        if not self.ai_client:
            return existing_assertions
        
        # 构建提示词
        assertions_json = [a.to_dict() for a in existing_assertions]
        prompt = f"""
        请分析以下断言,并提供改进建议或补充断言:
        
        现有断言:
        {json.dumps(assertions_json, ensure_ascii=False, indent=2)}
        
        上下文:
        {json.dumps(context, ensure_ascii=False, indent=2)}
        
        请返回:
        1. 改进建议
        2. 补充的断言(JSON格式)
        
        格式:
        {{
            "suggestions": ["建议1", "建议2"],
            "additional_assertions": [...]
        }}
        """
        
        try:
            response = self._call_ai(prompt)
            # 解析响应并合并断言
            enhanced = self._merge_assertions(existing_assertions, response)
            return enhanced
        except Exception as e:
            print(f"增强断言失败: {e}")
            return existing_assertions
    
    def _generate_from_schema(self, builder: AssertionBuilder,
                              schema: Dict, path_prefix: str):
        """从schema生成断言"""
        if 'properties' in schema:
            for prop_name, prop_schema in schema['properties'].items():
                json_path = f"{path_prefix}.{prop_name}"
                
                # 必填字段断言
                if 'required' in schema and prop_name in schema['required']:
                    builder.new_assertion(
                        f"{prop_name}字段存在",
                        f"{prop_name}是必填字段"
                    ).exists().at_path(json_path).critical()
                
                # 类型断言
                if 'type' in prop_schema:
                    expected_type = prop_schema['type']
                    builder.new_assertion(
                        f"{prop_name}类型为{expected_type}",
                        f"{prop_name}字段类型应为{expected_type}"
                    ).is_type(expected_type).at_path(json_path).major()
                
                # 枚举值断言
                if 'enum' in prop_schema:
                    builder.new_assertion(
                        f"{prop_name}值在枚举范围内",
                        f"{prop_name}应为{prop_schema['enum']}之一"
                    ).in_list(prop_schema['enum']).at_path(json_path).major()
    
    def _generate_business_assertions(self, description: str,
                                      api_spec: Dict) -> List[AssertionConfig]:
        """生成业务断言"""
        assertions = []
        
        # 简化版: 基于关键词生成
        desc_lower = description.lower()
        
        if '登录' in description or 'login' in desc_lower:
            # 登录相关断言
            assertions.append(AssertionConfig(
                name="返回token",
                description="登录成功应返回token",
                operator=AssertionOperator.EXISTS,
                expected=True,
                actual_path="body.data.token",
                severity=AssertionSeverity.CRITICAL
            ))
        
        if '列表' in description or 'list' in desc_lower:
            # 列表相关断言
            assertions.append(AssertionConfig(
                name="返回数组",
                description="列表接口应返回数组",
                operator=AssertionOperator.IS_TYPE,
                expected="list",
                actual_path="body.data",
                severity=AssertionSeverity.CRITICAL
            ))
        
        if '创建' in description or 'create' in desc_lower:
            # 创建相关断言
            assertions.append(AssertionConfig(
                name="返回ID",
                description="创建成功应返回ID",
                operator=AssertionOperator.EXISTS,
                expected=True,
                actual_path="body.data.id",
                severity=AssertionSeverity.CRITICAL
            ))
        
        return assertions
    
    def _build_testcase_prompt(self, test_case: Dict) -> str:
        """构建测试用例提示词"""
        return f"""
        根据以下测试用例,生成测试断言:
        
        用例标题: {test_case.get('title', '')}
        前置条件: {test_case.get('precondition', '')}
        操作步骤: {test_case.get('steps', '')}
        预期结果: {test_case.get('expected', '')}
        
        请生成JSON格式的断言列表,格式如下:
        [
            {{
                "name": "断言名称",
                "description": "断言描述",
                "operator": "equals",
                "expected": "期望值",
                "actual_path": "body.xxx",
                "severity": "critical"
            }}
        ]
        
        请只返回JSON数组。
        """
    
    def _call_ai(self, prompt: str) -> str:
        """调用AI"""
        if not self.ai_client:
            raise Exception("AI客户端未配置")
        
        # 这里应该调用实际的AI客户端
        # response = self.ai_client.chat(prompt)
        # return response
        
        # 简化版: 返回示例
        return """
        [
            {
                "name": "状态码为200",
                "description": "HTTP状态码应为200",
                "operator": "equals",
                "expected": 200,
                "actual_path": "status_code",
                "severity": "blocker"
            },
            {
                "name": "返回码为0",
                "description": "业务返回码应为0",
                "operator": "equals",
                "expected": 0,
                "actual_path": "body.code",
                "severity": "critical"
            }
        ]
        """
    
    def _parse_ai_response(self, response: str) -> List[AssertionConfig]:
        """解析AI响应"""
        try:
            # 提取JSON部分
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                
                assertions = []
                for item in data:
                    config = AssertionConfig(
                        name=item['name'],
                        description=item.get('description', item['name']),
                        operator=AssertionOperator(item['operator']),
                        expected=item['expected'],
                        actual_path=item.get('actual_path'),
                        severity=AssertionSeverity(item.get('severity', 'major'))
                    )
                    assertions.append(config)
                
                return assertions
        except Exception as e:
            print(f"解析AI响应失败: {e}")
        
        # 解析失败,返回基础断言
        return AssertionBuilder().api_success_assertions().build()
    
    def _merge_assertions(self, existing: List[AssertionConfig],
                         ai_response: str) -> List[AssertionConfig]:
        """合并断言"""
        # 简化版: 直接返回现有断言
        return existing


# 使用示例
if __name__ == "__main__":
    generator = AIAssertionGenerator()
    
    # 示例1: 从API规范生成
    api_spec = {
        'endpoint': '/api/users',
        'method': 'GET',
        'description': '获取用户列表',
        'response_schema': {
            'type': 'object',
            'properties': {
                'code': {'type': 'number'},
                'data': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'number'},
                            'name': {'type': 'string'},
                            'email': {'type': 'string'}
                        },
                        'required': ['id', 'name']
                    }
                }
            },
            'required': ['code', 'data']
        }
    }
    
    assertions = generator.generate_from_api_spec(api_spec)
    print("从API规范生成的断言:")
    for assertion in assertions:
        print(f"  - {assertion.name} [{assertion.severity.value}]")
    print()
    
    # 示例2: 从测试用例生成
    test_case = {
        'title': '测试用户登录',
        'precondition': '用户已注册',
        'steps': '1. 输入用户名密码\n2. 点击登录',
        'expected': '登录成功,返回用户信息和token'
    }
    
    assertions = generator.generate_from_test_case(test_case)
    print("从测试用例生成的断言:")
    for assertion in assertions:
        print(f"  - {assertion.name}")
