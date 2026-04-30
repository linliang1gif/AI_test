#!/usr/bin/env python3
"""YApi格式转OpenAPI 3.0格式"""

import json
import sys

def convert_yapi_to_openapi(yapi_data):
    """转换YApi格式到OpenAPI 3.0"""
    
    openapi = {
        "openapi": "3.0.0",
        "info": {
            "title": "蓝点回收系统API",
            "version": "1.2.2",
            "description": "蓝点新生废品回收B2B平台"
        },
        "servers": [
            {
                "url": "https://dev-recycle.szhibu.com/dev-api/recycle",
                "description": "测试环境"
            }
        ],
        "paths": {}
    }
    
    # 遍历所有分类
    for category in yapi_data:
        if not isinstance(category, dict):
            continue
            
        category_name = category.get("name", "未分类")
        apis = category.get("list", [])
        
        # 遍历该分类下的所有API
        for api in apis:
            if not isinstance(api, dict):
                continue
                
            path = api.get("path", "")
            method = api.get("method", "GET").lower()
            title = api.get("title", "")
            desc = api.get("desc", "")
            
            if not path:
                continue
            
            # 初始化path
            if path not in openapi["paths"]:
                openapi["paths"][path] = {}
            
            # 构建operation
            operation = {
                "summary": title,
                "description": desc or title,
                "tags": [category_name],
                "parameters": [],
                "responses": {
                    "200": {
                        "description": "成功",
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"}
                            }
                        }
                    }
                }
            }
            
            # 添加请求体（如果是POST/PUT/PATCH）
            if method in ["post", "put", "patch"]:
                req_body_other = api.get("req_body_other", "")
                if req_body_other:
                    try:
                        schema = json.loads(req_body_other)
                        operation["requestBody"] = {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": schema
                                }
                            }
                        }
                    except:
                        pass
            
            # 添加查询参数
            req_query = api.get("req_query", [])
            for param in req_query:
                if isinstance(param, dict):
                    operation["parameters"].append({
                        "name": param.get("name", ""),
                        "in": "query",
                        "required": param.get("required") == "1",
                        "schema": {"type": "string"},
                        "description": param.get("desc", "")
                    })
            
            # 添加响应
            res_body = api.get("res_body", "")
            if res_body:
                try:
                    schema = json.loads(res_body)
                    operation["responses"]["200"]["content"]["application/json"]["schema"] = schema
                except:
                    pass
            
            openapi["paths"][path][method] = operation
    
    return openapi

if __name__ == "__main__":
    input_file = r"D:\360Downloads\蓝点\api.json"
    output_file = "蓝点/bluedot_openapi.json"
    
    print(f"读取YApi文件: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        yapi_data = json.load(f)
    
    print(f"转换中...")
    openapi_data = convert_yapi_to_openapi(yapi_data)
    
    print(f"保存OpenAPI文件: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(openapi_data, f, ensure_ascii=False, indent=2)
    
    api_count = len(openapi_data["paths"])
    print(f"✓ 转换完成！共 {api_count} 个API")
