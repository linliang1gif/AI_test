#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Swagger/OpenAPI 自动解析器

负责解析Swagger/OpenAPI JSON文档，提取接口信息用于自动化测试生成。
"""

import json
import yaml
from typing import Dict, List, Any, Optional
from pathlib import Path
from urllib.parse import urljoin
import logging

logger = logging.getLogger(__name__)

class SwaggerApiParser:
    """Swagger/OpenAPI解析器"""
    
    def __init__(self):
        self.swagger_data = None
        self.base_url = ""
        self.apis = []
    
    def load_swagger_file(self, file_path: str) -> bool:
        """加载Swagger文件"""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                raise FileNotFoundError(f"Swagger文件不存在: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    self.swagger_data = yaml.safe_load(f)
                else:
                    self.swagger_data = json.load(f)
            
            # 提取基础URL
            self._extract_base_url()
            return True
            
        except Exception as e:
            logger.info(f"加载Swagger文件失败: {e}")
            return False
    
    def load_swagger_url(self, url: str) -> bool:
        """从URL加载Swagger文档"""
        try:
            import requests
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            if 'yaml' in response.headers.get('content-type', ''):
                self.swagger_data = yaml.safe_load(response.text)
            else:
                self.swagger_data = response.json()
            
            self._extract_base_url()
            return True
            
        except Exception as e:
            logger.info(f"从URL加载Swagger失败: {e}")
            return False
    
    def _extract_base_url(self):
        """提取基础URL"""
        if not self.swagger_data:
            return
        
        # OpenAPI 3.x
        if 'servers' in self.swagger_data:
            self.base_url = self.swagger_data['servers'][0]['url']
        # Swagger 2.x
        elif 'host' in self.swagger_data:
            scheme = self.swagger_data.get('schemes', ['http'])[0]
            host = self.swagger_data['host']
            base_path = self.swagger_data.get('basePath', '')
            self.base_url = f"{scheme}://{host}{base_path}"
        else:
            self.base_url = "http://localhost:8000"
    
    def parse_apis(self) -> List[Dict[str, Any]]:
        """解析所有API接口"""
        if not self.swagger_data:
            return []
        
        self.apis = []
        paths = self.swagger_data.get('paths', {})
        
        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method.lower() in ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']:
                    api_info = self._parse_single_api(path, method.upper(), operation)
                    if api_info:
                        self.apis.append(api_info)
        
        return self.apis
    
    def _parse_single_api(self, path: str, method: str, operation: Dict[str, Any]) -> Dict[str, Any]:
        """解析单个API接口"""
        try:
            api_info = {
                'endpoint': path,
                'method': method,
                'summary': operation.get('summary', ''),
                'description': operation.get('description', ''),
                'operationId': operation.get('operationId', ''),
                'tags': operation.get('tags', []),
                'params': self._parse_parameters(operation.get('parameters', [])),
                'request_body': self._parse_request_body(operation.get('requestBody')),
                'responses': self._parse_responses(operation.get('responses', {})),
                'security': operation.get('security', []),
                'full_url': urljoin(self.base_url, path.lstrip('/'))
            }
            
            return api_info
            
        except Exception as e:
            logger.info(f"解析API失败 {method} {path}: {e}")
            return None
    
    def _parse_parameters(self, parameters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """解析参数"""
        parsed_params = []
        
        for param in parameters:
            param_info = {
                'name': param.get('name', ''),
                'in': param.get('in', ''),  # query, path, header, cookie
                'type': self._get_param_type(param),
                'required': param.get('required', False),
                'description': param.get('description', ''),
                'example': self._get_param_example(param)
            }
            parsed_params.append(param_info)
        
        return parsed_params
    
    def _parse_request_body(self, request_body: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """解析请求体"""
        if not request_body:
            return None
        
        content = request_body.get('content', {})
        
        # 优先处理JSON格式
        for content_type in ['application/json', 'application/x-www-form-urlencoded', 'multipart/form-data']:
            if content_type in content:
                schema = content[content_type].get('schema', {})
                return {
                    'content_type': content_type,
                    'required': request_body.get('required', False),
                    'description': request_body.get('description', ''),
                    'schema': schema,
                    'example': self._generate_example_from_schema(schema)
                }
        
        return None
    
    def _parse_responses(self, responses: Dict[str, Any]) -> Dict[str, Any]:
        """解析响应"""
        parsed_responses = {}
        
        for status_code, response in responses.items():
            parsed_responses[status_code] = {
                'description': response.get('description', ''),
                'content': response.get('content', {}),
                'headers': response.get('headers', {})
            }
        
        return parsed_responses
    
    def _get_param_type(self, param: Dict[str, Any]) -> str:
        """获取参数类型"""
        if 'schema' in param:
            return param['schema'].get('type', 'string')
        return param.get('type', 'string')
    
    def _get_param_example(self, param: Dict[str, Any]) -> Any:
        """获取参数示例"""
        if 'example' in param:
            return param['example']
        
        if 'schema' in param:
            schema = param['schema']
            if 'example' in schema:
                return schema['example']
            return self._generate_example_by_type(schema.get('type', 'string'))
        
        return self._generate_example_by_type(param.get('type', 'string'))
    
    def _generate_example_from_schema(self, schema: Dict[str, Any]) -> Any:
        """根据schema生成示例数据"""
        if 'example' in schema:
            return schema['example']
        
        schema_type = schema.get('type', 'object')
        
        if schema_type == 'object':
            properties = schema.get('properties', {})
            example = {}
            
            for prop_name, prop_schema in properties.items():
                example[prop_name] = self._generate_example_from_schema(prop_schema)
            
            return example
        
        elif schema_type == 'array':
            items_schema = schema.get('items', {})
            return [self._generate_example_from_schema(items_schema)]
        
        else:
            return self._generate_example_by_type(schema_type)
    
    def _generate_example_by_type(self, param_type: str) -> Any:
        """根据类型生成示例值"""
        type_examples = {
            'string': 'test_string',
            'integer': 123,
            'number': 123.45,
            'boolean': True,
            'array': ['item1', 'item2'],
            'object': {'key': 'value'}
        }
        
        return type_examples.get(param_type, 'test_value')
    
    def get_api_by_operation_id(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """根据operationId获取API"""
        for api in self.apis:
            if api.get('operationId') == operation_id:
                return api
        return None
    
    def get_apis_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """根据标签获取API列表"""
        return [api for api in self.apis if tag in api.get('tags', [])]
    
    def get_apis_by_method(self, method: str) -> List[Dict[str, Any]]:
        """根据HTTP方法获取API列表"""
        return [api for api in self.apis if api.get('method') == method.upper()]
    
    def export_api_summary(self) -> Dict[str, Any]:
        """导出API摘要信息"""
        return {
            'total_apis': len(self.apis),
            'base_url': self.base_url,
            'methods_count': self._count_by_method(),
            'tags_count': self._count_by_tags(),
            'apis': self.apis
        }
    
    def _count_by_method(self) -> Dict[str, int]:
        """按方法统计API数量"""
        method_count = {}
        for api in self.apis:
            method = api.get('method', 'UNKNOWN')
            method_count[method] = method_count.get(method, 0) + 1
        return method_count
    
    def _count_by_tags(self) -> Dict[str, int]:
        """按标签统计API数量"""
        tag_count = {}
        for api in self.apis:
            tags = api.get('tags', ['untagged'])
            for tag in tags:
                tag_count[tag] = tag_count.get(tag, 0) + 1
        return tag_count