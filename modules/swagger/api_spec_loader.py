"""
API规范加载器
从Swagger/OpenAPI文件加载API定义
"""
import json
import yaml
from typing import Dict, List, Optional
from pathlib import Path


class ApiSpecLoader:
    """
    API规范加载器
    
    支持：
    - Swagger 2.0
    - OpenAPI 3.0
    - JSON和YAML格式
    """
    
    def __init__(self, spec_file: str):
        """
        初始化加载器
        
        Args:
            spec_file: Swagger/OpenAPI文件路径
        """
        self.spec_file = Path(spec_file)
        self.spec = None
        self.version = None
        self.base_path = ""
        self.apis = []
        
        self._load_spec()
        self._parse_spec()
    
    def _load_spec(self):
        """加载规范文件"""
        if not self.spec_file.exists():
            raise FileNotFoundError(f"Spec file not found: {self.spec_file}")
        
        content = self.spec_file.read_text(encoding='utf-8')
        
        if not content.strip():
            raise ValueError("Spec file is empty")
        
        # 尝试JSON
        try:
            self.spec = json.loads(content)
            if not isinstance(self.spec, dict):
                raise ValueError("Spec must be a JSON object (dictionary)")
            return
        except json.JSONDecodeError as e:
            json_error = str(e)
        
        # 尝试YAML
        try:
            self.spec = yaml.safe_load(content)
            if not isinstance(self.spec, dict):
                raise ValueError("Spec must be a YAML object (dictionary)")
            return
        except yaml.YAMLError as e:
            yaml_error = str(e)
        
        raise ValueError(
            f"Invalid spec file format. File must be valid JSON or YAML.\n"
            f"JSON error: {json_error}\n"
            f"YAML error: {yaml_error}"
        )
    
    def _parse_spec(self):
        """解析规范"""
        # 检测版本
        if 'swagger' in self.spec:
            swagger_version = self.spec.get('swagger', '')
            self.version = f'swagger_{swagger_version}'
            self._parse_swagger_2()
        elif 'openapi' in self.spec:
            openapi_version = self.spec.get('openapi', '')
            self.version = f'openapi_{openapi_version}'
            self._parse_openapi_3()
        else:
            # 提供更详细的错误信息
            available_keys = list(self.spec.keys()) if isinstance(self.spec, dict) else []
            raise ValueError(
                f"Unknown spec version. Expected 'swagger' or 'openapi' key in spec. "
                f"Available keys: {available_keys}. "
                f"Please ensure the file is a valid Swagger 2.0 or OpenAPI 3.x specification."
            )
    
    def _parse_swagger_2(self):
        """解析Swagger 2.0"""
        self.base_path = self.spec.get('basePath', '')
        paths = self.spec.get('paths', {})
        
        for path, methods in paths.items():
            for method, definition in methods.items():
                if method.upper() not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    continue
                
                api = self._parse_api_definition(path, method.upper(), definition)
                self.apis.append(api)
    
    def _parse_openapi_3(self):
        """解析OpenAPI 3.0"""
        servers = self.spec.get('servers', [])
        if servers:
            self.base_path = servers[0].get('url', '')
        
        paths = self.spec.get('paths', {})
        
        for path, methods in paths.items():
            for method, definition in methods.items():
                if method.upper() not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    continue
                
                api = self._parse_api_definition(path, method.upper(), definition)
                self.apis.append(api)
    
    def _parse_api_definition(self, path: str, method: str, definition: Dict) -> Dict:
        """
        解析单个API定义
        
        Returns:
            {
                'path': '/api/users',
                'method': 'POST',
                'summary': 'Create user',
                'description': '...',
                'parameters': [...],
                'request_body': {...},
                'responses': {...},
                'tags': [...]
            }
        """
        api = {
            'path': path,
            'method': method,
            'summary': definition.get('summary', ''),
            'description': definition.get('description', ''),
            'operation_id': definition.get('operationId', ''),
            'tags': definition.get('tags', []),
            'parameters': [],
            'request_body': None,
            'responses': definition.get('responses', {})
        }
        
        # 解析参数
        parameters = definition.get('parameters', [])
        for param in parameters:
            api['parameters'].append(self._parse_parameter(param))
        
        # 解析请求体（OpenAPI 3.0）
        if 'requestBody' in definition:
            api['request_body'] = self._parse_request_body(definition['requestBody'])
        
        # 解析请求体（Swagger 2.0 - body参数）
        for param in parameters:
            if param.get('in') == 'body':
                api['request_body'] = {
                    'required': param.get('required', False),
                    'schema': param.get('schema', {})
                }
        
        return api
    
    def _parse_parameter(self, param: Dict) -> Dict:
        """
        解析参数
        
        Returns:
            {
                'name': 'user_id',
                'in': 'path',  # path/query/header/cookie
                'required': True,
                'type': 'integer',
                'description': '...',
                'schema': {...}
            }
        """
        return {
            'name': param.get('name'),
            'in': param.get('in'),
            'required': param.get('required', False),
            'type': param.get('type', param.get('schema', {}).get('type')),
            'description': param.get('description', ''),
            'schema': param.get('schema', {}),
            'example': param.get('example'),
            'enum': param.get('enum', param.get('schema', {}).get('enum')),
            'minimum': param.get('minimum', param.get('schema', {}).get('minimum')),
            'maximum': param.get('maximum', param.get('schema', {}).get('maximum')),
            'min_length': param.get('minLength', param.get('schema', {}).get('minLength')),
            'max_length': param.get('maxLength', param.get('schema', {}).get('maxLength')),
            'pattern': param.get('pattern', param.get('schema', {}).get('pattern'))
        }
    
    def _parse_request_body(self, request_body: Dict) -> Dict:
        """
        解析请求体（OpenAPI 3.0）
        
        Returns:
            {
                'required': True,
                'content_type': 'application/json',
                'schema': {...}
            }
        """
        content = request_body.get('content', {})
        
        # 优先使用application/json
        if 'application/json' in content:
            return {
                'required': request_body.get('required', False),
                'content_type': 'application/json',
                'schema': content['application/json'].get('schema', {})
            }
        
        # 使用第一个content type
        if content:
            content_type = list(content.keys())[0]
            return {
                'required': request_body.get('required', False),
                'content_type': content_type,
                'schema': content[content_type].get('schema', {})
            }
        
        return None
    
    def get_all_apis(self) -> List[Dict]:
        """获取所有API定义"""
        return self.apis
    
    def get_api_by_path(self, path: str, method: str = None) -> Optional[Dict]:
        """根据路径获取API定义"""
        for api in self.apis:
            if api['path'] == path:
                if method is None or api['method'] == method.upper():
                    return api
        return None
    
    def get_apis_by_tag(self, tag: str) -> List[Dict]:
        """根据标签获取API列表"""
        return [api for api in self.apis if tag in api['tags']]
    
    def get_base_path(self) -> str:
        """获取基础路径"""
        return self.base_path
    
    def get_spec_info(self) -> Dict:
        """获取规范信息"""
        return {
            'version': self.version,
            'title': self.spec.get('info', {}).get('title', ''),
            'description': self.spec.get('info', {}).get('description', ''),
            'api_version': self.spec.get('info', {}).get('version', ''),
            'base_path': self.base_path,
            'total_apis': len(self.apis)
        }
