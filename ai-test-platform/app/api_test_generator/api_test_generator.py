#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API测试生成器

根据解析的接口信息自动生成pytest接口测试脚本，包括：
- 正常请求测试
- 参数缺失测试
- 非法参数测试
- 权限测试
- 边界测试
"""

import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from jinja2 import Template

class ApiTestGenerator:
    """API测试生成器"""
    
    def __init__(self, output_dir: str = "tests"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 测试模板
        self.test_template = self._get_test_template()
    
    def generate_api_tests(self, apis: List[Dict[str, Any]], base_url: str = "") -> Dict[str, str]:
        """为所有API生成测试脚本"""
        generated_files = {}
        
        for api in apis:
            try:
                file_name = self._generate_test_file_name(api)
                file_path = self.output_dir / file_name
                
                test_content = self._generate_single_api_test(api, base_url)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(test_content)
                
                generated_files[api['endpoint']] = str(file_path)
                print(f"✅ 生成API测试: {file_name}")
                
            except Exception as e:
                print(f"❌ 生成API测试失败 {api['endpoint']}: {e}")
        
        return generated_files
    
    def _generate_single_api_test(self, api: Dict[str, Any], base_url: str) -> str:
        """生成单个API的测试脚本"""
        # 准备测试数据
        test_data = {
            'api': api,
            'base_url': base_url or api.get('full_url', '').replace(api['endpoint'], ''),
            'class_name': self._get_test_class_name(api),
            'test_cases': self._generate_test_cases(api)
        }
        
        # 渲染模板
        return self.test_template.render(**test_data)
    
    def _generate_test_cases(self, api: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成测试用例"""
        test_cases = []
        
        # 1. 正常请求测试
        test_cases.append(self._create_success_test_case(api))
        
        # 2. 参数缺失测试
        test_cases.extend(self._create_missing_param_test_cases(api))
        
        # 3. 非法参数测试
        test_cases.extend(self._create_invalid_param_test_cases(api))
        
        # 4. 权限测试
        if api.get('security'):
            test_cases.append(self._create_unauthorized_test_case(api))
        
        # 5. 边界测试
        test_cases.extend(self._create_boundary_test_cases(api))
        
        return test_cases
    
    def _create_success_test_case(self, api: Dict[str, Any]) -> Dict[str, Any]:
        """创建成功测试用例"""
        return {
            'name': 'test_success',
            'description': f'测试{api["endpoint"]}正常请求',
            'method': api['method'],
            'endpoint': api['endpoint'],
            'headers': self._get_default_headers(api),
            'params': self._get_valid_params(api),
            'data': self._get_valid_request_body(api),
            'expected_status': 200,
            'expected_response': None,
            'test_type': 'success'
        }
    
    def _create_missing_param_test_cases(self, api: Dict[str, Any]) -> List[Dict[str, Any]]:
        """创建参数缺失测试用例"""
        test_cases = []
        required_params = [p for p in api.get('params', []) if p.get('required')]
        
        for param in required_params:
            test_case = {
                'name': f'test_missing_{param["name"]}',
                'description': f'测试缺失必需参数{param["name"]}',
                'method': api['method'],
                'endpoint': api['endpoint'],
                'headers': self._get_default_headers(api),
                'params': self._get_params_without(api, param['name']),
                'data': self._get_valid_request_body(api),
                'expected_status': 400,
                'expected_response': None,
                'test_type': 'missing_param'
            }
            test_cases.append(test_case)
        
        return test_cases
    
    def _create_invalid_param_test_cases(self, api: Dict[str, Any]) -> List[Dict[str, Any]]:
        """创建非法参数测试用例"""
        test_cases = []
        
        for param in api.get('params', []):
            if param['type'] in ['integer', 'number']:
                test_case = {
                    'name': f'test_invalid_{param["name"]}_type',
                    'description': f'测试{param["name"]}参数类型错误',
                    'method': api['method'],
                    'endpoint': api['endpoint'],
                    'headers': self._get_default_headers(api),
                    'params': self._get_params_with_invalid_value(api, param['name'], 'invalid_string'),
                    'data': self._get_valid_request_body(api),
                    'expected_status': 400,
                    'expected_response': None,
                    'test_type': 'invalid_param'
                }
                test_cases.append(test_case)
        
        return test_cases
    
    def _create_unauthorized_test_case(self, api: Dict[str, Any]) -> Dict[str, Any]:
        """创建未授权测试用例"""
        return {
            'name': 'test_unauthorized',
            'description': f'测试{api["endpoint"]}未授权访问',
            'method': api['method'],
            'endpoint': api['endpoint'],
            'headers': {},  # 不包含认证头
            'params': self._get_valid_params(api),
            'data': self._get_valid_request_body(api),
            'expected_status': 401,
            'expected_response': None,
            'test_type': 'unauthorized'
        }
    
    def _create_boundary_test_cases(self, api: Dict[str, Any]) -> List[Dict[str, Any]]:
        """创建边界测试用例"""
        test_cases = []
        
        for param in api.get('params', []):
            if param['type'] == 'string':
                # 空字符串测试
                test_case = {
                    'name': f'test_{param["name"]}_empty_string',
                    'description': f'测试{param["name"]}空字符串',
                    'method': api['method'],
                    'endpoint': api['endpoint'],
                    'headers': self._get_default_headers(api),
                    'params': self._get_params_with_value(api, param['name'], ''),
                    'data': self._get_valid_request_body(api),
                    'expected_status': 400 if param.get('required') else 200,
                    'expected_response': None,
                    'test_type': 'boundary'
                }
                test_cases.append(test_case)
        
        return test_cases
    
    def _get_default_headers(self, api: Dict[str, Any]) -> Dict[str, str]:
        """获取默认请求头"""
        headers = {'Content-Type': 'application/json'}
        
        # 如果需要认证，添加认证头
        if api.get('security'):
            headers['Authorization'] = 'Bearer test_token'
        
        return headers
    
    def _get_valid_params(self, api: Dict[str, Any]) -> Dict[str, Any]:
        """获取有效参数"""
        params = {}
        
        for param in api.get('params', []):
            if param['in'] in ['query', 'path']:
                params[param['name']] = param.get('example', self._get_default_value_by_type(param['type']))
        
        return params
    
    def _get_valid_request_body(self, api: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """获取有效请求体"""
        request_body = api.get('request_body')
        if not request_body:
            return None
        
        return request_body.get('example', {})
    
    def _get_params_without(self, api: Dict[str, Any], exclude_param: str) -> Dict[str, Any]:
        """获取排除指定参数的参数集合"""
        params = {}
        
        for param in api.get('params', []):
            if param['in'] in ['query', 'path'] and param['name'] != exclude_param:
                params[param['name']] = param.get('example', self._get_default_value_by_type(param['type']))
        
        return params
    
    def _get_params_with_invalid_value(self, api: Dict[str, Any], param_name: str, invalid_value: Any) -> Dict[str, Any]:
        """获取包含无效值的参数集合"""
        params = {}
        
        for param in api.get('params', []):
            if param['in'] in ['query', 'path']:
                if param['name'] == param_name:
                    params[param['name']] = invalid_value
                else:
                    params[param['name']] = param.get('example', self._get_default_value_by_type(param['type']))
        
        return params
    
    def _get_params_with_value(self, api: Dict[str, Any], param_name: str, value: Any) -> Dict[str, Any]:
        """获取包含指定值的参数集合"""
        params = {}
        
        for param in api.get('params', []):
            if param['in'] in ['query', 'path']:
                if param['name'] == param_name:
                    params[param['name']] = value
                else:
                    params[param['name']] = param.get('example', self._get_default_value_by_type(param['type']))
        
        return params
    
    def _get_default_value_by_type(self, param_type: str) -> Any:
        """根据类型获取默认值"""
        type_defaults = {
            'string': 'test_value',
            'integer': 1,
            'number': 1.0,
            'boolean': True,
            'array': ['test'],
            'object': {'key': 'value'}
        }
        
        return type_defaults.get(param_type, 'test_value')
    
    def _generate_test_file_name(self, api: Dict[str, Any]) -> str:
        """生成测试文件名"""
        endpoint = api['endpoint'].replace('/', '_').replace('{', '').replace('}', '')
        method = api['method'].lower()
        
        # 移除开头的下划线
        if endpoint.startswith('_'):
            endpoint = endpoint[1:]
        
        return f"test_api_{method}_{endpoint}.py"
    
    def _get_test_class_name(self, api: Dict[str, Any]) -> str:
        """获取测试类名"""
        endpoint = api['endpoint'].replace('/', '_').replace('{', '').replace('}', '')
        method = api['method']
        
        # 移除开头的下划线并转换为驼峰命名
        if endpoint.startswith('_'):
            endpoint = endpoint[1:]
        
        parts = endpoint.split('_')
        class_name = 'Test' + method.capitalize() + ''.join(word.capitalize() for word in parts if word)
        
        return class_name
    
    def _get_test_template(self) -> Template:
        """获取测试模板"""
        template_str = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API自动化测试 - {{ api.endpoint }}

自动生成的接口测试脚本
API: {{ api.method }} {{ api.endpoint }}
描述: {{ api.description or api.summary }}
"""

import pytest
import requests
import json
from typing import Dict, Any, Optional

class {{ class_name }}:
    """{{ api.endpoint }} API测试类"""
    
    BASE_URL = "{{ base_url }}"
    ENDPOINT = "{{ api.endpoint }}"
    
    def setup_method(self):
        """测试前置设置"""
        self.session = requests.Session()
        self.base_url = self.BASE_URL.rstrip('/')
    
    def teardown_method(self):
        """测试后置清理"""
        if hasattr(self, 'session'):
            self.session.close()
    
    def _make_request(self, method: str, endpoint: str, headers: Dict[str, str] = None, 
                     params: Dict[str, Any] = None, data: Dict[str, Any] = None) -> requests.Response:
        """发送HTTP请求"""
        url = f"{self.base_url}{endpoint}"
        
        # 替换路径参数
        if params:
            for key, value in params.items():
                if f"{{{key}}}" in url:
                    url = url.replace(f"{{{key}}}", str(value))
                    # 从查询参数中移除路径参数
                    params = {k: v for k, v in params.items() if k != key}
        
        kwargs = {
            'headers': headers or {},
            'timeout': 30
        }
        
        if method.upper() in ['GET', 'DELETE']:
            kwargs['params'] = params
        else:
            kwargs['params'] = params
            if data:
                kwargs['json'] = data
        
        return self.session.request(method, url, **kwargs)

{% for test_case in test_cases %}
    def {{ test_case.name }}(self):
        """{{ test_case.description }}"""
        response = self._make_request(
            method="{{ test_case.method }}",
            endpoint="{{ test_case.endpoint }}",
            headers={{ test_case.headers | tojson }},
            params={{ test_case.params | tojson }},
            data={{ test_case.data | tojson }}
        )
        
        # 验证状态码
        assert response.status_code == {{ test_case.expected_status }}, \\
            f"期望状态码 {{ test_case.expected_status }}，实际 {response.status_code}，响应: {response.text}"
        
        {% if test_case.expected_response %}
        # 验证响应内容
        try:
            response_data = response.json()
            expected = {{ test_case.expected_response | tojson }}
            
            for key, value in expected.items():
                assert key in response_data, f"响应中缺少字段: {key}"
                assert response_data[key] == value, f"字段 {key} 值不匹配，期望: {value}，实际: {response_data[key]}"
        except json.JSONDecodeError:
            pytest.fail(f"响应不是有效的JSON格式: {response.text}")
        {% endif %}
        
        {% if test_case.test_type == 'success' %}
        # 成功测试的额外验证
        assert response.status_code < 400, f"请求失败: {response.text}"
        {% elif test_case.test_type == 'missing_param' %}
        # 参数缺失测试的额外验证
        assert response.status_code >= 400, f"应该返回错误状态码: {response.text}"
        {% elif test_case.test_type == 'invalid_param' %}
        # 无效参数测试的额外验证
        assert response.status_code >= 400, f"应该返回错误状态码: {response.text}"
        {% elif test_case.test_type == 'unauthorized' %}
        # 未授权测试的额外验证
        assert response.status_code in [401, 403], f"应该返回认证错误: {response.text}"
        {% endif %}

{% endfor %}

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''
        
        return Template(template_str)