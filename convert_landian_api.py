#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
蓝点项目 - YApi格式转Swagger格式转换器

将蓝点项目的YApi格式API文档转换为标准Swagger/OpenAPI格式
"""

import json
from pathlib import Path
from typing import Dict, List, Any


class YApiToSwaggerConverter:
    """YApi格式转Swagger格式转换器"""
    
    def __init__(self, yapi_file: str):
        """
        初始化转换器
        
        Args:
            yapi_file: YApi格式的JSON文件路径
        """
        self.yapi_file = Path(yapi_file)
        with open(self.yapi_file, 'r', encoding='utf-8') as f:
            self.yapi_data = json.load(f)
    
    def convert(self) -> Dict:
        """
        转换为Swagger格式
        
        Returns:
            Swagger格式的字典
        """
        swagger = {
            "openapi": "3.0.0",
            "info": {
                "title": "蓝点回收系统API",
                "version": "1.2.2",
                "description": "蓝点回收系统后端API文档"
            },
            "servers": [
                {
                    "url": "http://localhost:8080",
                    "description": "本地开发环境"
                }
            ],
            "paths": {},
            "components": {
                "schemas": {},
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer"
                    }
                }
            }
        }
        
        # 转换每个分类下的API
        for category in self.yapi_data:
            category_name = category.get('name', 'default')
            api_list = category.get('list', [])
            
            for api in api_list:
                self._convert_api(api, category_name, swagger)
        
        return swagger
    
    def _convert_api(self, api: Dict, category: str, swagger: Dict):
        """转换单个API"""
        path = api.get('path', '')
        method = api.get('method', 'GET').lower()
        
        if not path:
            return
        
        # 初始化path
        if path not in swagger['paths']:
            swagger['paths'][path] = {}
        
        # 构建operation对象
        operation = {
            "summary": api.get('title', ''),
            "description": api.get('desc', ''),
            "tags": [category],
            "operationId": f"{method}_{path.replace('/', '_')}",
            "parameters": [],
            "responses": {}
        }
        
        # 处理请求头
        req_headers = api.get('req_headers', [])
        for header in req_headers:
            if header.get('name') != 'Content-Type':  # Content-Type由requestBody处理
                operation['parameters'].append({
                    "name": header['name'],
                    "in": "header",
                    "required": header.get('required') == '1',
                    "schema": {"type": "string"},
                    "example": header.get('value', '')
                })
        
        # 处理查询参数
        req_query = api.get('req_query', [])
        for param in req_query:
            operation['parameters'].append({
                "name": param['name'],
                "in": "query",
                "required": param.get('required') == '1',
                "schema": {"type": "string"},
                "description": param.get('desc', '')
            })
        
        # 处理路径参数
        req_params = api.get('req_params', [])
        for param in req_params:
            operation['parameters'].append({
                "name": param['name'],
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
                "description": param.get('desc', '')
            })
        
        # 处理请求体
        if method in ['post', 'put', 'patch']:
            req_body_type = api.get('req_body_type', '')
            req_body_other = api.get('req_body_other', '')
            
            if req_body_type == 'json' and req_body_other:
                try:
                    # YApi使用JSON Schema格式
                    schema = json.loads(req_body_other)
                    operation['requestBody'] = {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": schema
                            }
                        }
                    }
                except:
                    pass
        
        # 处理响应
        res_body = api.get('res_body', '')
        if res_body:
            try:
                schema = json.loads(res_body)
                operation['responses']['200'] = {
                    "description": "成功响应",
                    "content": {
                        "application/json": {
                            "schema": schema
                        }
                    }
                }
            except:
                operation['responses']['200'] = {
                    "description": "成功响应"
                }
        else:
            operation['responses']['200'] = {
                "description": "成功响应"
            }
        
        # 添加常见错误响应
        operation['responses']['400'] = {
            "description": "请求参数错误"
        }
        operation['responses']['401'] = {
            "description": "未授权"
        }
        operation['responses']['500'] = {
            "description": "服务器错误"
        }
        
        swagger['paths'][path][method] = operation
    
    def save(self, output_file: str):
        """
        保存转换后的Swagger文件
        
        Args:
            output_file: 输出文件路径
        """
        swagger = self.convert()
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(swagger, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 转换完成: {output_file}")
        print(f"   - API数量: {len(swagger['paths'])}")
        print(f"   - 分类数量: {len(set(tag for path in swagger['paths'].values() for op in path.values() for tag in op.get('tags', [])))}")


def main():
    """主函数"""
    # 输入输出路径
    yapi_file = "蓝点/api.json"
    swagger_file = "ai测试/landian_swagger.json"
    
    print("=" * 60)
    print("蓝点项目 - YApi转Swagger转换器")
    print("=" * 60)
    
    # 检查输入文件
    if not Path(yapi_file).exists():
        print(f"❌ 错误: 找不到YApi文件: {yapi_file}")
        return
    
    # 执行转换
    converter = YApiToSwaggerConverter(yapi_file)
    converter.save(swagger_file)
    
    print("\n✅ 转换成功!")
    print(f"   Swagger文件: {swagger_file}")


if __name__ == "__main__":
    main()
