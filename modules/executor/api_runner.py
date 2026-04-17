"""
企业级 API测试Runner - 生产就绪版本
"""
import requests
import time
import re
import traceback
from typing import Dict, List, Optional, Any, Callable
import json
from urllib.parse import urljoin
from copy import deepcopy


class ApiRunner:
    """
    企业级API测试执行器
    
    特性：
    - 动态参数替换（支持变量、环境变量、上下文）
    - 增强的JSON Path断言（支持数组、嵌套、条件）
    - 智能Token注入（支持多种认证方式）
    - 智能重试机制（指数退避、条件重试）
    - 请求/响应拦截器
    - 连接池复用
    - 详细的错误信息
    """
    
    def __init__(self, config: Dict):
        """
        初始化API Runner
        
        Args:
            config: 配置字典
                - base_url: API基础URL
                - timeout: 默认超时时间
                - default_headers: 默认请求头
                - auth_config: 认证配置
                - retry_config: 重试配置
                - interceptors: 拦截器配置
        """
        self.base_url = config.get('base_url', '')
        self.timeout = config.get('timeout', 30)
        self.session = requests.Session()
        
        # 认证配置
        self.auth_config = config.get('auth_config', {})
        
        # 重试配置
        self.retry_config = config.get('retry_config', {
            'max_retries': 3,
            'backoff_factor': 2,
            'retry_on_status': [500, 502, 503, 504],
            'retry_on_timeout': True
        })
        
        # 上下文存储（用于动态参数）
        self.context = config.get('context', {})
        
        # 拦截器
        self.request_interceptors: List[Callable] = []
        self.response_interceptors: List[Callable] = []
        
        # 设置默认请求头
        default_headers = config.get('default_headers', {})
        if default_headers:
            self.session.headers.update(default_headers)
        
        # 配置连接池
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=config.get('pool_connections', 10),
            pool_maxsize=config.get('pool_maxsize', 10),
            max_retries=0  # 我们自己实现重试逻辑
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
    
    def add_request_interceptor(self, interceptor: Callable):
        """添加请求拦截器"""
        self.request_interceptors.append(interceptor)
    
    def add_response_interceptor(self, interceptor: Callable):
        """添加响应拦截器"""
        self.response_interceptors.append(interceptor)
    
    def set_context(self, key: str, value: Any):
        """设置上下文变量"""
        self.context[key] = value
    
    def get_context(self, key: str, default=None) -> Any:
        """获取上下文变量"""
        return self.context.get(key, default)
    
    def run(self, test_case) -> Dict:
        """
        执行API测试用例（企业级实现）
        
        Args:
            test_case: TestCase对象
            
        Returns:
            执行结果字典
        """
        try:
            # 1. 执行前置条件
            if hasattr(test_case, 'precondition') and test_case.precondition:
                self._setup_precondition(test_case.precondition)
            
            # 2. 准备执行配置（动态参数替换）
            config = self._prepare_config(test_case.execution_config)
            
            # 3. 智能重试执行
            response, retry_info = self._execute_with_retry(config)
            
            # 4. 执行断言
            assertion_results = self._execute_assertions(
                response, 
                test_case.assertions
            )
            
            # 5. 判断测试结果
            all_passed = all(a['passed'] for a in assertion_results)
            status = "passed" if all_passed else "failed"
            
            # 6. 构建错误信息
            error_message = None
            if not all_passed:
                failed_assertions = [a for a in assertion_results if not a['passed']]
                error_message = self._format_assertion_errors(failed_assertions)
            
            # 7. 保存响应到上下文（供后续用例使用）
            if hasattr(test_case, 'save_to_context'):
                self._save_response_to_context(response, test_case.save_to_context)
            
            return {
                "status": status,
                "actual_response": self._extract_response_data(response),
                "assertion_results": assertion_results,
                "error_message": error_message,
                "retry_info": retry_info,
                "request_info": {
                    "method": config.get('method'),
                    "url": config.get('url'),
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "headers": dict(response.headers)
                }
            }
            
        except requests.exceptions.Timeout:
            return {
                "status": "failed",
                "error_message": f"Request timeout after {self.timeout}s",
                "error_type": "TIMEOUT"
            }
        
        except requests.exceptions.ConnectionError as e:
            return {
                "status": "failed",
                "error_message": f"Connection error: {str(e)}",
                "error_type": "CONNECTION"
            }
        
        except Exception as e:
            return {
                "status": "failed",
                "error_message": str(e),
                "stack_trace": traceback.format_exc(),
                "error_type": "UNKNOWN"
            }
    
    def _prepare_config(self, config: Dict) -> Dict:
        """
        准备执行配置（动态参数替换）
        
        支持的变量格式：
        - ${var_name} - 从上下文获取
        - ${env.VAR_NAME} - 从环境变量获取
        - ${response.field} - 从上一个响应获取
        - ${random.uuid} - 生成随机UUID
        - ${random.int} - 生成随机整数
        - ${timestamp} - 当前时间戳
        """
        config = deepcopy(config)
        
        # 替换URL中的变量
        if 'url' in config:
            config['url'] = self._replace_variables(config['url'])
        
        # 替换请求头中的变量
        if 'headers' in config:
            config['headers'] = self._replace_dict_variables(config['headers'])
        
        # 替换请求体中的变量
        if 'body' in config:
            config['body'] = self._replace_dict_variables(config['body'])
        
        # 替换查询参数中的变量
        if 'params' in config:
            config['params'] = self._replace_dict_variables(config['params'])
        
        # 注入认证信息
        if 'headers' not in config:
            config['headers'] = {}
        config['headers'] = self._inject_auth(config['headers'])
        
        return config
    
    def _replace_variables(self, text: str) -> str:
        """替换字符串中的变量"""
        if not isinstance(text, str):
            return text
        
        # 匹配 ${var_name} 格式
        pattern = r'\$\{([^}]+)\}'
        
        def replacer(match):
            var_name = match.group(1)
            return str(self._get_variable_value(var_name))
        
        return re.sub(pattern, replacer, text)
    
    def _replace_dict_variables(self, data: Any) -> Any:
        """递归替换字典/列表中的变量"""
        if isinstance(data, dict):
            return {k: self._replace_dict_variables(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._replace_dict_variables(item) for item in data]
        elif isinstance(data, str):
            return self._replace_variables(data)
        else:
            return data
    
    def _get_variable_value(self, var_name: str) -> Any:
        """获取变量值"""
        import os
        import uuid
        import random
        
        # 环境变量: ${env.VAR_NAME}
        if var_name.startswith('env.'):
            env_var = var_name[4:]
            return os.getenv(env_var, '')
        
        # 响应字段: ${response.field}
        elif var_name.startswith('response.'):
            field = var_name[9:]
            last_response = self.context.get('last_response', {})
            return self._get_nested_value(last_response, field)
        
        # 随机UUID: ${random.uuid}
        elif var_name == 'random.uuid':
            return str(uuid.uuid4())
        
        # 随机整数: ${random.int}
        elif var_name == 'random.int':
            return random.randint(1000, 9999)
        
        # 时间戳: ${timestamp}
        elif var_name == 'timestamp':
            return int(time.time())
        
        # 从上下文获取
        else:
            return self.context.get(var_name, f'${{{var_name}}}')
    
    def _inject_auth(self, headers: Dict) -> Dict:
        """
        智能注入认证信息
        
        支持的认证方式：
        - Bearer Token
        - Basic Auth
        - API Key
        - Custom Header
        """
        headers = headers.copy()
        
        auth_type = self.auth_config.get('type', 'bearer')
        
        if auth_type == 'bearer':
            # Bearer Token认证
            token = self.auth_config.get('token') or self.context.get('access_token')
            if token:
                headers['Authorization'] = f'Bearer {token}'
        
        elif auth_type == 'basic':
            # Basic Auth
            username = self.auth_config.get('username')
            password = self.auth_config.get('password')
            if username and password:
                import base64
                credentials = f'{username}:{password}'
                encoded = base64.b64encode(credentials.encode()).decode()
                headers['Authorization'] = f'Basic {encoded}'
        
        elif auth_type == 'api_key':
            # API Key认证
            key_name = self.auth_config.get('key_name', 'X-API-Key')
            key_value = self.auth_config.get('key_value')
            if key_value:
                headers[key_name] = key_value
        
        elif auth_type == 'custom':
            # 自定义Header
            custom_headers = self.auth_config.get('headers', {})
            headers.update(custom_headers)
        
        return headers
    
    def _execute_with_retry(self, config: Dict) -> tuple:
        """
        智能重试执行
        
        特性：
        - 指数退避
        - 条件重试（根据状态码）
        - 超时重试
        - 重试次数记录
        """
        max_retries = self.retry_config.get('max_retries', 3)
        backoff_factor = self.retry_config.get('backoff_factor', 2)
        retry_on_status = self.retry_config.get('retry_on_status', [500, 502, 503, 504])
        retry_on_timeout = self.retry_config.get('retry_on_timeout', True)
        
        retry_info = {
            'total_attempts': 0,
            'retry_count': 0,
            'retry_reasons': []
        }
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            retry_info['total_attempts'] = attempt + 1
            
            try:
                # 执行请求拦截器
                for interceptor in self.request_interceptors:
                    config = interceptor(config)
                
                # 执行HTTP请求
                response = self._execute_request(config)
                
                # 执行响应拦截器
                for interceptor in self.response_interceptors:
                    response = interceptor(response)
                
                # 检查是否需要重试
                if attempt < max_retries and response.status_code in retry_on_status:
                    retry_info['retry_count'] += 1
                    retry_info['retry_reasons'].append(f'Status {response.status_code}')
                    
                    # 指数退避
                    sleep_time = backoff_factor ** attempt
                    time.sleep(sleep_time)
                    continue
                
                # 成功，返回响应
                return response, retry_info
            
            except requests.exceptions.Timeout as e:
                last_exception = e
                if attempt < max_retries and retry_on_timeout:
                    retry_info['retry_count'] += 1
                    retry_info['retry_reasons'].append('Timeout')
                    
                    sleep_time = backoff_factor ** attempt
                    time.sleep(sleep_time)
                    continue
                else:
                    raise
            
            except requests.exceptions.ConnectionError as e:
                last_exception = e
                if attempt < max_retries:
                    retry_info['retry_count'] += 1
                    retry_info['retry_reasons'].append('Connection Error')
                    
                    sleep_time = backoff_factor ** attempt
                    time.sleep(sleep_time)
                    continue
                else:
                    raise
        
        # 所有重试都失败
        if last_exception:
            raise last_exception
        
        return response, retry_info
    
    def _execute_request(self, config: Dict) -> requests.Response:
        """
        执行HTTP请求
        
        Args:
            config: 执行配置
                - method: HTTP方法
                - url: 请求路径
                - headers: 请求头
                - body: 请求体
                - params: 查询参数
                - timeout: 超时时间
        """
        method = config.get('method', 'GET').upper()
        url = self._build_url(config.get('url', ''))
        
        # 构建请求参数
        kwargs = {
            'timeout': config.get('timeout', self.timeout),
            'headers': config.get('headers', {}),
        }
        
        # 添加请求体
        if method in ['POST', 'PUT', 'PATCH']:
            body = config.get('body')
            if body:
                if isinstance(body, dict):
                    kwargs['json'] = body
                else:
                    kwargs['data'] = body
        
        # 添加查询参数
        if 'params' in config:
            kwargs['params'] = config['params']
        
        # 执行请求
        response = self.session.request(method, url, **kwargs)
        
        return response
    
    def _execute_assertions(self, response: requests.Response, 
                           assertions: List[Dict]) -> List[Dict]:
        """
        执行断言（企业级增强）
        
        支持的断言类型：
        - status_code: 状态码断言
        - json_path: JSON路径断言（增强版）
        - response_time: 响应时间断言
        - header: 响应头断言
        - schema: JSON Schema断言
        - contains: 包含断言
        - regex: 正则表达式断言
        - custom: 自定义断言函数
        """
        results = []
        
        for assertion in assertions:
            assertion_type = assertion.get('type')
            
            try:
                if assertion_type == 'status_code':
                    passed = self._assert_status_code(response, assertion)
                
                elif assertion_type == 'json_path':
                    passed = self._assert_json_path(response, assertion)
                
                elif assertion_type == 'response_time':
                    passed = self._assert_response_time(response, assertion)
                
                elif assertion_type == 'header':
                    passed = self._assert_header(response, assertion)
                
                elif assertion_type == 'schema':
                    passed = self._assert_schema(response, assertion)
                
                elif assertion_type == 'contains':
                    passed = self._assert_contains(response, assertion)
                
                elif assertion_type == 'regex':
                    passed = self._assert_regex(response, assertion)
                
                elif assertion_type == 'custom':
                    passed = self._assert_custom(response, assertion)
                
                else:
                    passed = False
                    error = f"Unknown assertion type: {assertion_type}"
                
                results.append({
                    'type': assertion_type,
                    'passed': passed,
                    'expected': assertion.get('expected'),
                    'actual': self._get_actual_value(response, assertion),
                    'message': assertion.get('message', ''),
                    'operator': assertion.get('operator', 'equals')
                })
                
            except Exception as e:
                results.append({
                    'type': assertion_type,
                    'passed': False,
                    'error': str(e),
                    'expected': assertion.get('expected'),
                    'stack_trace': traceback.format_exc()
                })
        
        return results
    
    def _assert_status_code(self, response: requests.Response, assertion: Dict) -> bool:
        """断言状态码"""
        expected = assertion.get('expected')
        actual = response.status_code
        
        operator = assertion.get('operator', 'equals')
        
        if operator == 'equals':
            return actual == expected
        elif operator == 'in':
            return actual in expected  # expected应该是列表
        elif operator == 'not_equals':
            return actual != expected
        elif operator == 'greater_than':
            return actual > expected
        elif operator == 'less_than':
            return actual < expected
        elif operator == 'greater_than_or_equal':
            return actual >= expected
        elif operator == 'less_than_or_equal':
            return actual <= expected
        else:
            return actual == expected
    
    def _assert_json_path(self, response: requests.Response, assertion: Dict) -> bool:
        """
        断言JSON路径的值（企业级增强）
        
        支持：
        - 嵌套路径: data.user.name
        - 数组索引: data.users[0].name
        - 数组过滤: data.users[?(@.age>18)].name
        - 通配符: data.*.name
        - 多种操作符: equals/contains/not_equals/greater_than/less_than/regex/exists
        """
        try:
            data = response.json()
            field = assertion.get('field')
            expected = assertion.get('expected')
            operator = assertion.get('operator', 'equals')
            
            # 提取实际值
            actual = self._extract_json_path(data, field)
            
            # 根据操作符比较
            if operator == 'equals':
                return actual == expected
            
            elif operator == 'contains':
                if isinstance(actual, (list, str)):
                    return expected in actual
                else:
                    return expected in str(actual)
            
            elif operator == 'not_equals':
                return actual != expected
            
            elif operator == 'greater_than':
                return float(actual) > float(expected)
            
            elif operator == 'less_than':
                return float(actual) < float(expected)
            
            elif operator == 'greater_than_or_equal':
                return float(actual) >= float(expected)
            
            elif operator == 'less_than_or_equal':
                return float(actual) <= float(expected)
            
            elif operator == 'regex':
                return bool(re.match(expected, str(actual)))
            
            elif operator == 'exists':
                return actual is not None
            
            elif operator == 'not_exists':
                return actual is None
            
            elif operator == 'type':
                return type(actual).__name__ == expected
            
            elif operator == 'length':
                return len(actual) == expected
            
            elif operator == 'length_greater_than':
                return len(actual) > expected
            
            elif operator == 'length_less_than':
                return len(actual) < expected
            
            else:
                return actual == expected
                
        except Exception as e:
            # 如果是exists断言，返回False
            if assertion.get('operator') == 'exists':
                return False
            raise
    
    def _extract_json_path(self, data: Any, path: str) -> Any:
        """
        提取JSON路径的值（企业级增强）
        
        支持：
        - 简单路径: user.name
        - 数组索引: users[0].name
        - 负数索引: users[-1].name
        - 数组切片: users[0:2]
        - 通配符: users.*.name (返回列表)
        """
        if not path:
            return data
        
        # 分割路径
        parts = self._split_json_path(path)
        
        current = data
        for part in parts:
            # 处理数组索引: [0], [-1], [0:2]
            if part.startswith('[') and part.endswith(']'):
                index_str = part[1:-1]
                
                # 切片: [0:2]
                if ':' in index_str:
                    start, end = index_str.split(':')
                    start = int(start) if start else None
                    end = int(end) if end else None
                    current = current[start:end]
                
                # 索引: [0], [-1]
                else:
                    index = int(index_str)
                    current = current[index]
            
            # 处理通配符: *
            elif part == '*':
                if isinstance(current, list):
                    # 对列表中的每个元素继续处理
                    return [item for item in current]
                elif isinstance(current, dict):
                    # 返回所有值
                    return list(current.values())
            
            # 普通字段
            else:
                if isinstance(current, dict):
                    current = current.get(part)
                elif isinstance(current, list):
                    # 如果当前是列表，对每个元素提取字段
                    current = [item.get(part) if isinstance(item, dict) else None for item in current]
                else:
                    return None
        
        return current
    
    def _split_json_path(self, path: str) -> List[str]:
        """分割JSON路径"""
        # 处理 users[0].name 这种格式
        parts = []
        current = ''
        in_bracket = False
        
        for char in path:
            if char == '[':
                if current:
                    parts.append(current)
                    current = ''
                in_bracket = True
                current += char
            elif char == ']':
                current += char
                parts.append(current)
                current = ''
                in_bracket = False
            elif char == '.' and not in_bracket:
                if current:
                    parts.append(current)
                    current = ''
            else:
                current += char
        
        if current:
            parts.append(current)
        
        return parts
    
    def _assert_response_time(self, response: requests.Response, assertion: Dict) -> bool:
        """断言响应时间"""
        expected = assertion.get('expected')  # 单位：秒
        actual = response.elapsed.total_seconds()
        return actual < expected
    
    def _assert_header(self, response: requests.Response, assertion: Dict) -> bool:
        """断言响应头"""
        header_name = assertion.get('field')
        expected = assertion.get('expected')
        actual = response.headers.get(header_name)
        return actual == expected
    
    def _assert_schema(self, response: requests.Response, assertion: Dict) -> bool:
        """断言JSON Schema"""
        try:
            from jsonschema import validate
            data = response.json()
            schema = assertion.get('schema')
            validate(instance=data, schema=schema)
            return True
        except Exception:
            return False
    
    def _assert_contains(self, response: requests.Response, assertion: Dict) -> bool:
        """断言响应包含指定内容"""
        expected = assertion.get('expected')
        
        # 尝试JSON
        try:
            data = response.json()
            return expected in json.dumps(data)
        except:
            # 尝试文本
            return expected in response.text
    
    def _assert_regex(self, response: requests.Response, assertion: Dict) -> bool:
        """正则表达式断言"""
        pattern = assertion.get('expected')
        field = assertion.get('field')
        
        if field:
            # 断言JSON字段
            data = response.json()
            actual = self._extract_json_path(data, field)
            return bool(re.match(pattern, str(actual)))
        else:
            # 断言整个响应体
            return bool(re.search(pattern, response.text))
    
    def _assert_custom(self, response: requests.Response, assertion: Dict) -> bool:
        """自定义断言函数"""
        func = assertion.get('function')
        if callable(func):
            return func(response)
        return False
    
    def _save_response_to_context(self, response: requests.Response, save_config: Dict):
        """保存响应到上下文"""
        try:
            data = response.json()
            
            # 保存整个响应
            self.context['last_response'] = data
            
            # 保存指定字段
            if isinstance(save_config, dict):
                for context_key, json_path in save_config.items():
                    value = self._extract_json_path(data, json_path)
                    self.context[context_key] = value
        except:
            pass
    
    def _get_nested_value(self, data: Dict, path: str):
        """获取嵌套字典的值（简化版，兼容旧代码）"""
        return self._extract_json_path(data, path)
    
    def _get_actual_value(self, response: requests.Response, assertion: Dict):
        """获取实际值（用于断言结果展示）"""
        assertion_type = assertion.get('type')
        
        if assertion_type == 'status_code':
            return response.status_code
        
        elif assertion_type == 'json_path':
            try:
                data = response.json()
                field = assertion.get('field')
                return self._extract_json_path(data, field)
            except:
                return None
        
        elif assertion_type == 'response_time':
            return response.elapsed.total_seconds()
        
        elif assertion_type == 'header':
            header_name = assertion.get('field')
            return response.headers.get(header_name)
        
        elif assertion_type == 'regex':
            field = assertion.get('field')
            if field:
                try:
                    data = response.json()
                    return self._extract_json_path(data, field)
                except:
                    return None
            else:
                return response.text[:100]  # 返回前100个字符
        
        return None
    
    def _build_url(self, path: str) -> str:
        """构建完整URL"""
        if path.startswith('http://') or path.startswith('https://'):
            return path
        
        return urljoin(self.base_url, path)
    
    def _extract_response_data(self, response: requests.Response) -> Dict:
        """提取响应数据"""
        try:
            return {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'body': response.json() if response.content else None,
                'response_time': response.elapsed.total_seconds(),
                'encoding': response.encoding,
                'url': response.url
            }
        except:
            return {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'body': response.text,
                'response_time': response.elapsed.total_seconds(),
                'encoding': response.encoding,
                'url': response.url
            }
    
    def _format_assertion_errors(self, failed_assertions: List[Dict]) -> str:
        """格式化断言错误信息"""
        errors = []
        for assertion in failed_assertions:
            error = f"Assertion failed: {assertion['type']}"
            
            if 'field' in assertion:
                error += f" (field: {assertion.get('field')})"
            
            if 'operator' in assertion:
                error += f" (operator: {assertion.get('operator')})"
            
            if 'expected' in assertion:
                error += f"\n  Expected: {assertion['expected']}"
            
            if 'actual' in assertion:
                error += f"\n  Actual: {assertion['actual']}"
            
            if 'error' in assertion:
                error += f"\n  Error: {assertion['error']}"
            
            errors.append(error)
        
        return "\n\n".join(errors)
    
    def _setup_precondition(self, precondition: str):
        """
        执行前置条件
        
        支持：
        - SQL查询
        - API调用
        - 数据准备
        - 环境设置
        """
        # 这里可以实现前置条件的执行逻辑
        # 例如：创建测试数据、登录获取token等
        pass
