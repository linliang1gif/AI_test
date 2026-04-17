"""
Swagger测试用例生成器（企业级）
从Swagger/OpenAPI自动生成高质量测试用例
"""
import re
from typing import Dict, List, Optional, Any
from .api_spec_loader import ApiSpecLoader
from ..data.test_data_manager import TestDataManager

# 🔧 使用 core 层的统一模型
from core import (
    TestCase,
    TestCasePriority,
    TestCaseStatus,
    DataType,
    ExpectedBehavior,
    TestType as CoreTestType,
    create_test_case
)


class SwaggerTestCaseGenerator:
    """
    Swagger测试用例生成器（企业级）
    
    特性：
    - 每个接口生成5个用例（1正常+2边界+2异常）
    - 严格使用Swagger定义，不虚构接口
    - 自动生成边界值（0、最大值、null）
    - 完整的execution_config和assertions
    - 支持路径参数、查询参数、请求体
    """
    
    def __init__(self, swagger_file: str, business_context: str = ""):
        """
        初始化生成器
        
        Args:
            swagger_file: Swagger/OpenAPI文件路径
            business_context: 业务描述（可选）
        """
        self.loader = ApiSpecLoader(swagger_file)
        self.business_context = business_context
        self.test_case_counter = 0
        self.data_manager = TestDataManager()  # 初始化数据管理器
    
    def generate_all_testcases(self) -> List[TestCase]:
        """
        为所有API生成测试用例
        
        Returns:
            所有测试用例列表
        """
        all_test_cases = []
        apis = self.loader.get_all_apis()
        
        for api in apis:
            test_cases = self.generate_testcases_for_api(api)
            all_test_cases.extend(test_cases)
        
        return all_test_cases
    
    def generate_testcases_for_api(self, api: Dict) -> List[TestCase]:
        """
        为单个API生成测试用例
        
        生成策略：
        - 1个正常流程用例
        - 2个边界用例
        - 2个异常用例
        
        Args:
            api: API定义
            
        Returns:
            测试用例列表
        """
        test_cases = []
        
        # 1. 正常流程用例
        normal_case = self._generate_normal_case(api)
        if normal_case:
            test_cases.append(normal_case)
        
        # 2. 边界用例
        boundary_cases = self._generate_boundary_cases(api)
        test_cases.extend(boundary_cases)
        
        # 3. 异常用例
        error_cases = self._generate_error_cases(api)
        test_cases.extend(error_cases)
        
        return test_cases
    
    def _generate_normal_case(self, api: Dict) -> Optional[TestCase]:
        """生成正常流程用例"""
        self.test_case_counter += 1
        case_id = f"TC_{self.test_case_counter:03d}"
        
        module = api['tags'][0] if api['tags'] else 'default'
        
        execution_config = self._build_execution_config(api, scenario='normal', case_id=case_id)
        assertions = self._build_assertions(api, scenario='normal', expected_behavior='success')
        
        # 🔧 使用 create_test_case 工厂函数
        test_case = create_test_case(
            id=case_id,
            title=f"{api['summary'] or api['path']} - 正常流程",
            module=module,
            priority="critical",  # P0 -> critical
            status="pending",
            steps=[f"调用 {api['method']} {api['path']}"],
            expected=self._extract_expected_response(api, scenario='normal'),
            data_type="valid",
            expected_behavior="success",
            execution_config=execution_config,
            assertions=assertions,
            test_point_id=f"TP_{self.test_case_counter:03d}"
        )
        
        return test_case
    
    def _generate_boundary_cases(self, api: Dict) -> List[TestCase]:
        """生成边界用例"""
        boundary_cases = []
        
        min_case = self._generate_boundary_case(api, 'minimum')
        if min_case:
            boundary_cases.append(min_case)
        
        max_case = self._generate_boundary_case(api, 'maximum')
        if max_case:
            boundary_cases.append(max_case)
        
        return boundary_cases
    
    def _generate_boundary_case(self, api: Dict, boundary_type: str) -> Optional[TestCase]:
        """生成单个边界用例"""
        self.test_case_counter += 1
        case_id = f"TC_{self.test_case_counter:03d}"
        
        module = api['tags'][0] if api['tags'] else 'default'
        
        # 边界用例的预期行为：通常应该成功，但某些情况可能返回客户端错误
        expected_behavior = self._determine_boundary_behavior(api, boundary_type)
        
        execution_config = self._build_execution_config(api, scenario=boundary_type, case_id=case_id)
        assertions = self._build_assertions(api, scenario=boundary_type, expected_behavior=expected_behavior)
        
        boundary_label = "最小值/空值" if boundary_type == 'minimum' else "最大值"
        
        # 🔧 使用 create_test_case 工厂函数
        test_case = create_test_case(
            id=case_id,
            title=f"{api['summary'] or api['path']} - 边界测试({boundary_label})",
            module=module,
            priority="high",  # P1 -> high
            status="pending",
            steps=[f"调用 {api['method']} {api['path']} (使用{boundary_label})"],
            expected=self._extract_expected_response(api, scenario=boundary_type),
            data_type="boundary",
            expected_behavior=expected_behavior,
            execution_config=execution_config,
            assertions=assertions,
            test_point_id=f"TP_{self.test_case_counter:03d}"
        )
        
        return test_case
    
    def _determine_boundary_behavior(self, api: Dict, boundary_type: str) -> str:
        """
        确定边界用例的预期行为
        
        Args:
            api: API定义
            boundary_type: 边界类型（minimum/maximum）
        
        Returns:
            预期行为（success/client_error）
        """
        # 大多数边界值应该是合法的，返回success
        # 但某些特殊情况可能返回client_error
        
        # 检查是否有严格的约束
        if api.get('request_body'):
            schema = api['request_body'].get('schema', {})
            properties = schema.get('properties', {})
            
            # 如果有exclusiveMinimum或exclusiveMaximum，边界值可能无效
            for prop_schema in properties.values():
                # 确保 prop_schema 是字典
                if not isinstance(prop_schema, dict):
                    continue
                    
                if boundary_type == 'minimum' and prop_schema.get('exclusiveMinimum'):
                    return "client_error"
                if boundary_type == 'maximum' and prop_schema.get('exclusiveMaximum'):
                    return "client_error"
        
        # 默认：边界值应该成功
        return "success"
    
    def _generate_error_cases(self, api: Dict) -> List[TestCase]:
        """生成异常用例"""
        error_cases = []
        
        missing_case = self._generate_error_case(api, 'missing_required')
        if missing_case:
            error_cases.append(missing_case)
        
        invalid_case = self._generate_error_case(api, 'invalid_type')
        if invalid_case:
            error_cases.append(invalid_case)
        
        return error_cases
    
    def _generate_error_case(self, api: Dict, error_type: str) -> Optional[TestCase]:
        """生成单个异常用例"""
        self.test_case_counter += 1
        case_id = f"TC_{self.test_case_counter:03d}"
        
        module = api['tags'][0] if api['tags'] else 'default'
        
        execution_config = self._build_execution_config(api, scenario=error_type, case_id=case_id)
        assertions = self._build_assertions(api, scenario=error_type, expected_behavior='client_error')
        
        error_label = "缺少必填参数" if error_type == 'missing_required' else "无效参数类型"
        
        # 🔧 使用 create_test_case 工厂函数
        test_case = create_test_case(
            id=case_id,
            title=f"{api['summary'] or api['path']} - 异常测试({error_label})",
            module=module,
            priority="medium",  # P2 -> medium
            status="pending",
            steps=[f"调用 {api['method']} {api['path']} ({error_label})"],
            expected="返回错误响应（4xx）",
            data_type="invalid",
            expected_behavior="client_error",
            execution_config=execution_config,
            assertions=assertions,
            test_point_id=f"TP_{self.test_case_counter:03d}"
        )
        
        return test_case
# 这是第二部分的代码，稍后会合并

    def _build_execution_config(self, api: Dict, scenario: str, case_id: str = None) -> Dict:
        """构建execution_config"""
        config = {
            'method': api['method'],
            'url': api['path'],
            'timeout': 30
        }
        
        path_params = [p for p in api['parameters'] if p['in'] == 'path']
        if path_params:
            config['url'] = self._replace_path_params(api['path'], path_params, scenario)
        
        query_params = [p for p in api['parameters'] if p['in'] == 'query']
        if query_params:
            config['params'] = self._build_query_params(query_params, scenario)
        
        header_params = [p for p in api['parameters'] if p['in'] == 'header']
        if header_params:
            config['headers'] = self._build_headers(header_params, scenario)
        
        if api['request_body']:
            config['body'] = self._build_request_body(api['request_body'], scenario, case_id)
        
        return config
    
    def _replace_path_params(self, path: str, params: List[Dict], scenario: str) -> str:
        """替换路径参数"""
        result_path = path
        for param in params:
            param_name = param['name']
            param_value = self._generate_param_value(param, scenario)
            result_path = result_path.replace(f'{{{param_name}}}', str(param_value))
            result_path = result_path.replace(f':{param_name}', str(param_value))
        return result_path
    
    def _build_query_params(self, params: List[Dict], scenario: str) -> Dict:
        """构建查询参数"""
        query_params = {}
        for param in params:
            if scenario == 'missing_required' and param['required']:
                continue
            param_value = self._generate_param_value(param, scenario)
            query_params[param['name']] = param_value
        return query_params
    
    def _build_headers(self, params: List[Dict], scenario: str) -> Dict:
        """构建请求头"""
        headers = {}
        for param in params:
            param_value = self._generate_param_value(param, scenario)
            headers[param['name']] = str(param_value)
        return headers
    
    def _build_request_body(self, request_body: Dict, scenario: str, case_id: str = None) -> Dict:
        """
        构建请求体（使用TestDataManager）
        
        Args:
            request_body: 请求体schema
            scenario: 场景类型（normal/minimum/maximum/missing_required/invalid_type）
            case_id: 用例ID（用于数据缓存）
        
        Returns:
            生成的请求体数据
        """
        schema = request_body.get('schema', {})
        if not schema:
            return {}
        
        # 将schema转换为TestDataManager可用的格式
        data_schema = self._convert_schema_for_data_manager(schema)
        
        # 根据scenario选择数据分类
        if scenario == 'normal':
            category = 'valid'
        elif scenario == 'minimum':
            category = 'boundary'
        elif scenario == 'maximum':
            category = 'boundary'
        elif scenario == 'missing_required':
            category = 'invalid'
        elif scenario == 'invalid_type':
            category = 'invalid'
        else:
            category = 'valid'
        
        # 使用TestDataManager生成数据
        body = self.data_manager.generate_data(data_schema, category, case_id)
        
        # 特殊处理：missing_required场景需要移除必填字段
        if scenario == 'missing_required':
            required = schema.get('required', [])
            if required:
                # 移除第一个必填字段
                body.pop(required[0], None)
        
        return body
    
    def _convert_schema_for_data_manager(self, schema: Dict) -> Dict:
        """
        将Swagger schema转换为TestDataManager可用的格式
        
        Args:
            schema: Swagger schema
        
        Returns:
            TestDataManager schema格式
        """
        if schema.get('type') != 'object':
            # 如果不是object类型，返回简化schema
            return {"value": schema}
        
        properties = schema.get('properties', {})
        data_schema = {}
        
        for prop_name, prop_schema in properties.items():
            # 如果 prop_schema 不是字典（可能是 $ref 字符串），跳过或使用默认值
            if not isinstance(prop_schema, dict):
                data_schema[prop_name] = {"type": "string"}
                continue
            
            # 提取字段类型和约束
            field_def = {
                "type": prop_schema.get('type', 'string')
            }
            
            # 添加约束条件
            if 'minimum' in prop_schema:
                field_def['minimum'] = prop_schema['minimum']
            if 'maximum' in prop_schema:
                field_def['maximum'] = prop_schema['maximum']
            if 'minLength' in prop_schema:
                field_def['minLength'] = prop_schema['minLength']
            if 'maxLength' in prop_schema:
                field_def['maxLength'] = prop_schema['maxLength']
            if 'format' in prop_schema:
                field_def['format'] = prop_schema['format']
            if 'pattern' in prop_schema:
                field_def['pattern'] = prop_schema['pattern']
            if 'enum' in prop_schema:
                field_def['enum'] = prop_schema['enum']
            if 'example' in prop_schema:
                field_def['example'] = prop_schema['example']
            
            data_schema[prop_name] = field_def
        
        return data_schema
    
    def _generate_object_from_schema(self, schema: Dict, scenario: str) -> Any:
        """从schema生成对象"""
        schema_type = schema.get('type')
        if schema_type == 'object':
            return self._generate_object(schema, scenario)
        elif schema_type == 'array':
            return self._generate_array(schema, scenario)
        else:
            return self._generate_primitive_value(schema, scenario)
    
    def _generate_object(self, schema: Dict, scenario: str) -> Dict:
        """生成对象"""
        obj = {}
        properties = schema.get('properties', {})
        required = schema.get('required', [])
        
        for prop_name, prop_schema in properties.items():
            if scenario == 'missing_required' and prop_name in required:
                continue
            obj[prop_name] = self._generate_object_from_schema(prop_schema, scenario)
        return obj
    
    def _generate_array(self, schema: Dict, scenario: str) -> List:
        """生成数组"""
        items_schema = schema.get('items', {})
        if scenario == 'minimum':
            return []
        elif scenario == 'maximum':
            return [
                self._generate_object_from_schema(items_schema, 'normal'),
                self._generate_object_from_schema(items_schema, 'normal'),
                self._generate_object_from_schema(items_schema, 'normal')
            ]
        else:
            return [self._generate_object_from_schema(items_schema, 'normal')]
    
    def _generate_param_value(self, param: Dict, scenario: str) -> Any:
        """生成参数值"""
        param_type = param.get('type', 'string')
        
        if scenario == 'invalid_type':
            return self._generate_invalid_value(param_type)
        
        if param_type == 'integer':
            return self._generate_integer_value(param, scenario)
        elif param_type == 'number':
            return self._generate_number_value(param, scenario)
        elif param_type == 'string':
            return self._generate_string_value(param, scenario)
        elif param_type == 'boolean':
            return self._generate_boolean_value(param, scenario)
        elif param_type == 'array':
            return self._generate_array_value(param, scenario)
        else:
            return None
    
    def _generate_primitive_value(self, schema: Dict, scenario: str) -> Any:
        """生成基本类型值"""
        schema_type = schema.get('type', 'string')
        
        if scenario == 'invalid_type':
            return self._generate_invalid_value(schema_type)
        
        if schema_type == 'integer':
            return self._generate_integer_value(schema, scenario)
        elif schema_type == 'number':
            return self._generate_number_value(schema, scenario)
        elif schema_type == 'string':
            return self._generate_string_value(schema, scenario)
        elif schema_type == 'boolean':
            return self._generate_boolean_value(schema, scenario)
        else:
            return None
    
    def _generate_integer_value(self, schema: Dict, scenario: str) -> int:
        """生成整数值"""
        if scenario == 'minimum':
            minimum = schema.get('minimum', 0)
            return minimum if minimum is not None else 0
        elif scenario == 'maximum':
            maximum = schema.get('maximum', 999999)
            return maximum if maximum is not None else 999999
        else:
            example = schema.get('example')
            if example is not None:
                return int(example)
            return 1
    
    def _generate_number_value(self, schema: Dict, scenario: str) -> float:
        """生成数字值"""
        if scenario == 'minimum':
            minimum = schema.get('minimum', 0.0)
            return float(minimum if minimum is not None else 0.0)
        elif scenario == 'maximum':
            maximum = schema.get('maximum', 999999.99)
            return float(maximum if maximum is not None else 999999.99)
        else:
            example = schema.get('example')
            if example is not None:
                return float(example)
            return 1.0
    
    def _generate_string_value(self, schema: Dict, scenario: str) -> str:
        """生成字符串值"""
        if scenario == 'minimum':
            min_length = schema.get('min_length', 0)
            # 确保 min_length 不是 None
            if min_length is None:
                min_length = 0
            if min_length == 0:
                return ""
            return "a" * int(min_length)
        elif scenario == 'maximum':
            max_length = schema.get('max_length', 255)
            # 确保 max_length 不是 None
            if max_length is None:
                max_length = 255
            return "a" * int(max_length)
        else:
            example = schema.get('example')
            if example:
                return str(example)
            
            enum = schema.get('enum')
            if enum:
                return enum[0]
            
            pattern = schema.get('pattern')
            if pattern:
                return self._generate_from_pattern(pattern)
            
            return "test_value"
    
    def _generate_boolean_value(self, schema: Dict, scenario: str) -> bool:
        """生成布尔值"""
        example = schema.get('example')
        if example is not None:
            return bool(example)
        return True
    
    def _generate_array_value(self, schema: Dict, scenario: str) -> List:
        """生成数组值"""
        items_schema = schema.get('items', {})
        if scenario == 'minimum':
            return []
        elif scenario == 'maximum':
            return [1, 2, 3]
        else:
            return [1]
    
    def _generate_invalid_value(self, expected_type: str) -> Any:
        """生成无效类型的值"""
        if expected_type == 'integer':
            return "not_an_integer"
        elif expected_type == 'number':
            return "not_a_number"
        elif expected_type == 'string':
            return 12345
        elif expected_type == 'boolean':
            return "not_a_boolean"
        elif expected_type == 'array':
            return "not_an_array"
        else:
            return None
    
    def _generate_from_pattern(self, pattern: str) -> str:
        """从正则模式生成示例值"""
        if 'email' in pattern.lower() or '@' in pattern:
            return "test@example.com"
        elif 'phone' in pattern.lower():
            return "13800138000"
        elif 'url' in pattern.lower() or 'http' in pattern:
            return "https://example.com"
        elif 'uuid' in pattern.lower():
            return "123e4567-e89b-12d3-a456-426614174000"
        else:
            return "test_value"
# 这是第三部分的代码，稍后会合并

    def _build_assertions(self, api: Dict, scenario: str, expected_behavior: str = "success") -> List[Dict]:
        """
        构建assertions（动态断言生成）
        
        Args:
            api: API定义
            scenario: 场景类型
            expected_behavior: 预期行为（success/client_error/server_error）
        
        Returns:
            断言列表
        """
        assertions = []
        
        # 根据expected_behavior动态生成状态码断言
        if expected_behavior == "success":
            # 成功场景：200, 201, 204等2xx状态码
            expected_status = self._extract_success_status(api)
            assertions.append({
                'type': 'status_code',
                'operator': 'in',
                'expected': [expected_status, 200, 201, 204]  # 包含多个可能的成功状态码
            })
        elif expected_behavior == "client_error":
            # 客户端错误：400, 422等4xx状态码
            assertions.append({
                'type': 'status_code',
                'operator': 'in',
                'expected': [400, 422, 404, 403]
            })
        elif expected_behavior == "server_error":
            # 服务器错误：500, 502, 503等5xx状态码
            assertions.append({
                'type': 'status_code',
                'operator': 'greater_than_or_equal',
                'expected': 500
            })
        else:
            # 默认：期望成功
            expected_status = self._extract_success_status(api)
            assertions.append({
                'type': 'status_code',
                'expected': expected_status
            })
        
        # 响应体断言（仅成功场景）
        if expected_behavior == "success" and scenario == 'normal':
            response_assertions = self._extract_response_assertions(api)
            assertions.extend(response_assertions)
        
        return assertions
    
    def _extract_success_status(self, api: Dict) -> int:
        """提取成功状态码"""
        responses = api.get('responses', {})
        
        if '200' in responses:
            return 200
        elif '201' in responses:
            return 201
        elif '204' in responses:
            return 204
        else:
            for status_code in responses.keys():
                if status_code.startswith('2'):
                    return int(status_code)
        
        return 200
    
    def _extract_response_assertions(self, api: Dict) -> List[Dict]:
        """提取响应断言"""
        assertions = []
        responses = api.get('responses', {})
        
        success_response = None
        for status_code in ['200', '201', '204']:
            if status_code in responses:
                success_response = responses[status_code]
                break
        
        if not success_response:
            return assertions
        
        schema = self._extract_response_schema(success_response)
        if not schema:
            return assertions
        
        properties = schema.get('properties', {})
        for prop_name, prop_schema in properties.items():
            # 确保 prop_schema 是字典
            if not isinstance(prop_schema, dict):
                continue
                
            prop_type = prop_schema.get('type')
            
            assertions.append({
                'type': 'json_path',
                'field': prop_name,
                'operator': 'exists',
                'expected': True
            })
            
            if prop_type:
                assertions.append({
                    'type': 'json_path',
                    'field': prop_name,
                    'operator': 'type',
                    'expected': prop_type
                })
        
        return assertions[:3]
    
    def _extract_response_schema(self, response: Dict) -> Optional[Dict]:
        """提取响应schema"""
        if 'content' in response:
            content = response['content']
            if 'application/json' in content:
                return content['application/json'].get('schema', {})
        
        if 'schema' in response:
            return response['schema']
        
        return None
    
    def _extract_precondition(self, api: Dict) -> str:
        """提取前置条件"""
        description = api.get('description', '')
        
        if 'auth' in description.lower() or 'token' in description.lower():
            return "用户已认证"
        elif 'create' in api['path'].lower() or api['method'] == 'POST':
            return "无"
        elif 'update' in api['path'].lower() or api['method'] == 'PUT':
            return "资源已存在"
        elif 'delete' in api['path'].lower() or api['method'] == 'DELETE':
            return "资源已存在"
        else:
            return "无"
    
    def _extract_expected_response(self, api: Dict, scenario: str) -> str:
        """提取预期响应"""
        if scenario in ['missing_required', 'invalid_type']:
            return "返回错误响应（4xx）"
        
        method = api['method']
        if method == 'POST':
            return "返回201状态码，创建成功"
        elif method == 'PUT' or method == 'PATCH':
            return "返回200状态码，更新成功"
        elif method == 'DELETE':
            return "返回204状态码，删除成功"
        else:
            return "返回200状态码，查询成功"
    
    def export_to_json(self, test_cases: List[TestCase]) -> List[Dict]:
        """导出为JSON格式"""
        result = []
        for tc in test_cases:
            result.append({
                'id': tc.id,
                'test_point_id': tc.test_point_id,
                'title': tc.title,
                'steps': tc.steps,
                'expected': tc.expected,
                'priority': tc.priority.value,  # 枚举转字符串
                'status': tc.status.value,      # 枚举转字符串
                'module': tc.module,
                'execution_config': tc.execution_config,
                'assertions': tc.assertions,
                'data_type': tc.data_type.value,  # 枚举转字符串
                'expected_behavior': tc.expected_behavior.value,  # 枚举转字符串
                'tags': tc.tags,
                'created_by': tc.created_by
            })
        return result
    
    def get_statistics(self, test_cases: List[TestCase]) -> Dict:
        """获取统计信息"""
        total = len(test_cases)
        by_priority = {}
        by_module = {}
        by_data_type = {}
        by_expected_behavior = {}
        
        for tc in test_cases:
            # 枚举转字符串
            priority = tc.priority.value
            by_priority[priority] = by_priority.get(priority, 0) + 1
            
            module = tc.module
            by_module[module] = by_module.get(module, 0) + 1
            
            # 枚举转字符串
            data_type = tc.data_type.value
            by_data_type[data_type] = by_data_type.get(data_type, 0) + 1
            
            # 枚举转字符串
            expected_behavior = tc.expected_behavior.value
            by_expected_behavior[expected_behavior] = by_expected_behavior.get(expected_behavior, 0) + 1
        
        return {
            'total': total,
            'by_priority': by_priority,
            'by_module': by_module,
            'by_data_type': by_data_type,
            'by_expected_behavior': by_expected_behavior,
            'apis_covered': len(self.loader.get_all_apis())
        }
