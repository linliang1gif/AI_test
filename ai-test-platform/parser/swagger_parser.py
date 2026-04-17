#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Test Platform - Swagger解析模块

负责解析Swagger/OpenAPI文档，提取接口信息用于自动化测试。
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from config.config import get_config

# 知识库（懒加载）
try:
    from knowledge.business_knowledge import BusinessKnowledge, THRESHOLD_MAPPING
    _biz_kb = BusinessKnowledge()
except Exception:
    _biz_kb = None
    THRESHOLD_MAPPING = 0.70

class SwaggerParser:
    """Swagger文档解析器"""
    
    def __init__(self):
        self.config = get_config()
        self.swagger_data = None
    
    def load_swagger_file(self, file_path: str = None) -> Dict[str, Any]:
        """加载Swagger文件"""
        if file_path is None:
            file_path = self.config.paths.data_dir / "swagger.json"
        
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Swagger文件不存在: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.swagger_data = json.load(f)
            
            return self.swagger_data
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Swagger文件格式错误: {str(e)}")
    
    def parse_apis(self) -> List[Dict[str, Any]]:
        """解析所有API接口，并做需求-接口语义映射（第三阶段）"""
        if not self.swagger_data:
            raise ValueError("请先加载Swagger文件")

        apis = []
        paths = self.swagger_data.get('paths', {})

        for path, path_info in paths.items():
            for method, method_info in path_info.items():
                if method.lower() in ['get', 'post', 'put', 'delete', 'patch']:
                    api_info = self._parse_single_api(path, method, method_info)
                    apis.append(api_info)

        # 需求-接口语义映射
        if _biz_kb:
            try:
                mapped = 0
                for api in apis:
                    query = f"{api.get('summary', '')} {api.get('description', '')} {api['path']}"
                    rules = _biz_kb.search_relevant_rules(query, top_k=3)
                    for rule in rules:
                        if rule['similarity'] >= THRESHOLD_MAPPING and rule.get('source_req_id'):
                            _biz_kb.save_req_api_mapping(
                                req_id=rule['source_req_id'],
                                api_path=api['path'],
                                api_method=api['method'],
                                confidence=rule['similarity']
                            )
                            mapped += 1
                if mapped:
                    print(f"✅ 需求-接口映射完成，新增 {mapped} 条映射")
            except Exception as e:
                print(f"⚠️ 需求-接口映射失败（静默）: {e}")

        return apis
    
    def _parse_single_api(self, path: str, method: str, method_info: Dict[str, Any]) -> Dict[str, Any]:
        """解析单个API接口"""
        api_info = {
            'name': method_info.get('operationId', f"{method}_{path.replace('/', '_')}"),
            'method': method.upper(),
            'path': path,
            'summary': method_info.get('summary', ''),
            'description': method_info.get('description', ''),
            'tags': method_info.get('tags', []),
            'parameters': self._parse_parameters(method_info.get('parameters', [])),
            'request_body': self._parse_request_body(method_info.get('requestBody', {})),
            'responses': self._parse_responses(method_info.get('responses', {})),
            'security': method_info.get('security', [])
        }
        
        return api_info
    
    def _parse_parameters(self, parameters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """解析参数信息"""
        parsed_params = []
        
        for param in parameters:
            param_info = {
                'name': param.get('name', ''),
                'in': param.get('in', ''),  # query, path, header, cookie
                'required': param.get('required', False),
                'type': self._get_parameter_type(param),
                'description': param.get('description', ''),
                'example': self._get_parameter_example(param)
            }
            parsed_params.append(param_info)
        
        return parsed_params
    
    def _parse_request_body(self, request_body: Dict[str, Any]) -> Dict[str, Any]:
        """解析请求体信息"""
        if not request_body:
            return {}
        
        content = request_body.get('content', {})
        
        # 优先处理JSON格式
        if 'application/json' in content:
            json_content = content['application/json']
            schema = json_content.get('schema', {})
            
            return {
                'content_type': 'application/json',
                'required': request_body.get('required', False),
                'schema': self._parse_schema(schema),
                'example': self._generate_example_from_schema(schema)
            }
        
        # 处理其他格式
        for content_type, content_info in content.items():
            schema = content_info.get('schema', {})
            return {
                'content_type': content_type,
                'required': request_body.get('required', False),
                'schema': self._parse_schema(schema),
                'example': self._generate_example_from_schema(schema)
            }
        
        return {}
    
    def _parse_responses(self, responses: Dict[str, Any]) -> Dict[str, Any]:
        """解析响应信息"""
        parsed_responses = {}
        
        for status_code, response_info in responses.items():
            content = response_info.get('content', {})
            
            response_data = {
                'description': response_info.get('description', ''),
                'content': {}
            }
            
            for content_type, content_info in content.items():
                schema = content_info.get('schema', {})
                response_data['content'][content_type] = {
                    'schema': self._parse_schema(schema),
                    'example': self._generate_example_from_schema(schema)
                }
            
            parsed_responses[status_code] = response_data
        
        return parsed_responses
    
    def _parse_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """解析数据模式"""
        if not schema:
            return {}
        
        parsed_schema = {
            'type': schema.get('type', 'object'),
            'properties': {},
            'required': schema.get('required', [])
        }
        
        properties = schema.get('properties', {})
        for prop_name, prop_info in properties.items():
            parsed_schema['properties'][prop_name] = {
                'type': prop_info.get('type', 'string'),
                'description': prop_info.get('description', ''),
                'format': prop_info.get('format', ''),
                'example': prop_info.get('example', ''),
                'enum': prop_info.get('enum', []),
                'minimum': prop_info.get('minimum'),
                'maximum': prop_info.get('maximum'),
                'minLength': prop_info.get('minLength'),
                'maxLength': prop_info.get('maxLength')
            }
        
        return parsed_schema
    
    def _get_parameter_type(self, param: Dict[str, Any]) -> str:
        """获取参数类型"""
        schema = param.get('schema', {})
        return schema.get('type', 'string')
    
    def _get_parameter_example(self, param: Dict[str, Any]) -> Any:
        """获取参数示例"""
        # 优先使用example字段
        if 'example' in param:
            return param['example']
        
        schema = param.get('schema', {})
        if 'example' in schema:
            return schema['example']
        
        # 根据类型生成默认示例
        param_type = self._get_parameter_type(param)
        return self._generate_default_example(param_type)
    
    def _generate_example_from_schema(self, schema: Dict[str, Any]) -> Any:
        """根据schema生成示例数据"""
        if not schema:
            return {}
        
        schema_type = schema.get('type', 'object')
        
        if schema_type == 'object':
            example = {}
            properties = schema.get('properties', {})
            
            for prop_name, prop_info in properties.items():
                prop_type = prop_info.get('type', 'string')
                
                if 'example' in prop_info:
                    example[prop_name] = prop_info['example']
                else:
                    example[prop_name] = self._generate_default_example(prop_type)
            
            return example
        
        elif schema_type == 'array':
            items = schema.get('items', {})
            item_example = self._generate_example_from_schema(items)
            return [item_example]
        
        else:
            return self._generate_default_example(schema_type)
    
    def _generate_default_example(self, data_type: str) -> Any:
        """生成默认示例值"""
        type_examples = {
            'string': 'example_string',
            'integer': 123,
            'number': 123.45,
            'boolean': True,
            'array': [],
            'object': {}
        }
        
        return type_examples.get(data_type, 'example_value')
    
    def get_api_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """根据标签获取API"""
        apis = self.parse_apis()
        return [api for api in apis if tag in api.get('tags', [])]
    
    def get_api_by_path(self, path: str) -> List[Dict[str, Any]]:
        """根据路径获取API"""
        apis = self.parse_apis()
        return [api for api in apis if api['path'] == path]
    
    def generate_api_summary(self) -> Dict[str, Any]:
        """生成API摘要信息"""
        apis = self.parse_apis()
        
        summary = {
            'total_apis': len(apis),
            'methods': {},
            'tags': {},
            'paths': len(set(api['path'] for api in apis))
        }
        
        for api in apis:
            # 统计HTTP方法
            method = api['method']
            summary['methods'][method] = summary['methods'].get(method, 0) + 1
            
            # 统计标签
            for tag in api.get('tags', []):
                summary['tags'][tag] = summary['tags'].get(tag, 0) + 1
        
        return summary
    
    def validate_swagger(self) -> Dict[str, Any]:
        """验证Swagger文档"""
        if not self.swagger_data:
            return {'is_valid': False, 'errors': ['未加载Swagger文档']}
        
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        # 检查必要字段
        required_fields = ['openapi', 'info', 'paths']
        for field in required_fields:
            if field not in self.swagger_data:
                validation_result['errors'].append(f"缺少必要字段: {field}")
                validation_result['is_valid'] = False
        
        # 检查API数量
        paths = self.swagger_data.get('paths', {})
        if not paths:
            validation_result['errors'].append("未定义任何API路径")
            validation_result['is_valid'] = False
        
        # 检查每个API的完整性
        for path, path_info in paths.items():
            for method, method_info in path_info.items():
                if method.lower() in ['get', 'post', 'put', 'delete', 'patch']:
                    if 'responses' not in method_info:
                        validation_result['warnings'].append(f"{method.upper()} {path} 缺少响应定义")
        
        return validation_result

def create_sample_swagger():
    """创建示例Swagger文档"""
    sample_swagger = {
        "openapi": "3.0.0",
        "info": {
            "title": "用户管理系统API",
            "version": "1.0.0",
            "description": "用户管理系统的RESTful API接口文档"
        },
        "servers": [
            {
                "url": "http://localhost:8000",
                "description": "开发环境"
            }
        ],
        "paths": {
            "/api/user/register": {
                "post": {
                    "tags": ["用户管理"],
                    "summary": "用户注册",
                    "description": "新用户注册接口",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["email", "password"],
                                    "properties": {
                                        "email": {
                                            "type": "string",
                                            "format": "email",
                                            "description": "用户邮箱",
                                            "example": "user@example.com"
                                        },
                                        "password": {
                                            "type": "string",
                                            "minLength": 8,
                                            "description": "用户密码",
                                            "example": "password123"
                                        },
                                        "phone": {
                                            "type": "string",
                                            "description": "手机号码",
                                            "example": "13800138000"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "注册成功",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "code": {
                                                "type": "integer",
                                                "example": 200
                                            },
                                            "message": {
                                                "type": "string",
                                                "example": "注册成功"
                                            },
                                            "data": {
                                                "type": "object",
                                                "properties": {
                                                    "user_id": {
                                                        "type": "integer",
                                                        "example": 12345
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "请求参数错误"
                        }
                    }
                }
            },
            "/api/user/login": {
                "post": {
                    "tags": ["用户管理"],
                    "summary": "用户登录",
                    "description": "用户登录接口",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["username", "password"],
                                    "properties": {
                                        "username": {
                                            "type": "string",
                                            "description": "用户名或邮箱",
                                            "example": "user@example.com"
                                        },
                                        "password": {
                                            "type": "string",
                                            "description": "密码",
                                            "example": "password123"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "登录成功",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "code": {
                                                "type": "integer",
                                                "example": 200
                                            },
                                            "message": {
                                                "type": "string",
                                                "example": "登录成功"
                                            },
                                            "data": {
                                                "type": "object",
                                                "properties": {
                                                    "token": {
                                                        "type": "string",
                                                        "example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                                                    },
                                                    "user_info": {
                                                        "type": "object",
                                                        "properties": {
                                                            "user_id": {
                                                                "type": "integer",
                                                                "example": 12345
                                                            },
                                                            "username": {
                                                                "type": "string",
                                                                "example": "testuser"
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/user/profile": {
                "get": {
                    "tags": ["用户管理"],
                    "summary": "获取用户信息",
                    "description": "获取当前登录用户的详细信息",
                    "security": [
                        {
                            "bearerAuth": []
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "获取成功",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "code": {
                                                "type": "integer",
                                                "example": 200
                                            },
                                            "data": {
                                                "type": "object",
                                                "properties": {
                                                    "user_id": {
                                                        "type": "integer",
                                                        "example": 12345
                                                    },
                                                    "username": {
                                                        "type": "string",
                                                        "example": "testuser"
                                                    },
                                                    "email": {
                                                        "type": "string",
                                                        "example": "user@example.com"
                                                    },
                                                    "phone": {
                                                        "type": "string",
                                                        "example": "13800138000"
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                }
            }
        }
    }
    
    config = get_config()
    swagger_file = config.paths.data_dir / "swagger.json"
    
    with open(swagger_file, 'w', encoding='utf-8') as f:
        json.dump(sample_swagger, f, ensure_ascii=False, indent=2)
    
    print(f"示例Swagger文档已创建: {swagger_file}")
    return swagger_file