#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实项目快速接入路由

提供真实项目连接检测、Swagger检测等功能
"""

import time
import requests
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v2/real-project", tags=["真实项目接入"])


class ConnectionCheckRequest(BaseModel):
    """连接检测请求"""
    base_url: str = Field(..., description="真实项目基础URL")
    token: Optional[str] = Field(None, description="认证Token（可选）")
    health_path: Optional[str] = Field("/health", description="健康检查路径")
    auth_type: Optional[str] = Field("none", description="认证方式: none/bearer/basic")
    timeout: Optional[int] = Field(10, description="超时时间（秒）")


class SwaggerCheckRequest(BaseModel):
    """Swagger检测请求"""
    swagger_url: str = Field(..., description="Swagger文档URL")
    token: Optional[str] = Field(None, description="认证Token（可选）")
    auth_type: Optional[str] = Field("none", description="认证方式: none/bearer/basic")
    timeout: Optional[int] = Field(10, description="超时时间（秒）")


@router.post("/check-connection")
async def check_connection(request: ConnectionCheckRequest):
    """
    检测真实项目连接
    
    - 不保存Token
    - 不打印Token到日志
    - 不执行任何写操作
    - 只做连接测试
    """
    try:
        # 构建完整URL
        base_url = request.base_url.rstrip('/')
        health_path = request.health_path.lstrip('/')
        full_url = f"{base_url}/{health_path}"
        
        # 构建请求头（不打印Token）
        headers = {
            "User-Agent": "AI-Test-Platform/1.0",
            "Accept": "application/json"
        }
        
        # 添加认证（不打印Token）
        if request.token and request.auth_type == "bearer":
            headers["Authorization"] = f"Bearer {request.token}"
        elif request.token and request.auth_type == "basic":
            import base64
            encoded = base64.b64encode(request.token.encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"
        
        # 发起请求
        start_time = time.time()
        response = requests.get(
            full_url,
            headers=headers,
            timeout=request.timeout,
            verify=True  # 验证SSL证书
        )
        duration_ms = (time.time() - start_time) * 1000
        
        # 判断连接状态
        success = response.status_code in [200, 201, 204]
        
        # 返回结果（不包含Token）
        return {
            "success": success,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "url": full_url,
            "message": "连接成功" if success else f"连接失败: HTTP {response.status_code}",
            "response_preview": response.text[:200] if response.text else None,
            "headers": dict(response.headers) if success else None
        }
    
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "status_code": 0,
            "duration_ms": request.timeout * 1000,
            "url": full_url if 'full_url' in locals() else request.base_url,
            "message": "连接超时",
            "error": "请求超时，请检查网络或增加超时时间"
        }
    
    except requests.exceptions.ConnectionError as e:
        return {
            "success": False,
            "status_code": 0,
            "duration_ms": 0,
            "url": full_url if 'full_url' in locals() else request.base_url,
            "message": "连接失败",
            "error": f"无法连接到服务器: {str(e)}"
        }
    
    except requests.exceptions.SSLError as e:
        return {
            "success": False,
            "status_code": 0,
            "duration_ms": 0,
            "url": full_url if 'full_url' in locals() else request.base_url,
            "message": "SSL证书验证失败",
            "error": f"SSL错误: {str(e)}"
        }
    
    except Exception as e:
        return {
            "success": False,
            "status_code": 0,
            "duration_ms": 0,
            "url": full_url if 'full_url' in locals() else request.base_url,
            "message": "检测失败",
            "error": str(e)
        }


@router.post("/check-swagger")
async def check_swagger(request: SwaggerCheckRequest):
    """
    检测Swagger文档
    
    - 检查URL是否可访问
    - 判断是否为合法OpenAPI/Swagger格式
    - 返回接口统计信息
    - 不落库，只做检测
    - 不打印Token到日志
    """
    try:
        # 构建请求头（不打印Token）
        headers = {
            "User-Agent": "AI-Test-Platform/1.0",
            "Accept": "application/json"
        }
        
        # 添加认证（不打印Token）
        if request.token and request.auth_type == "bearer":
            headers["Authorization"] = f"Bearer {request.token}"
        elif request.token and request.auth_type == "basic":
            import base64
            encoded = base64.b64encode(request.token.encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"
        
        # 发起请求
        start_time = time.time()
        response = requests.get(
            request.swagger_url,
            headers=headers,
            timeout=request.timeout,
            verify=True
        )
        duration_ms = (time.time() - start_time) * 1000
        
        if response.status_code != 200:
            return {
                "success": False,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "message": f"无法访问Swagger文档: HTTP {response.status_code}",
                "error": response.text[:200] if response.text else None
            }
        
        # 解析Swagger文档
        try:
            swagger_data = response.json()
        except Exception as e:
            return {
                "success": False,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "message": "Swagger文档格式错误",
                "error": f"无法解析JSON: {str(e)}"
            }
        
        # 判断是否为合法的OpenAPI/Swagger格式
        is_openapi = "openapi" in swagger_data or "swagger" in swagger_data
        
        if not is_openapi:
            return {
                "success": False,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "message": "不是合法的OpenAPI/Swagger文档",
                "error": "文档中缺少 'openapi' 或 'swagger' 字段"
            }
        
        # 统计接口信息
        paths = swagger_data.get("paths", {})
        total_paths = len(paths)
        total_operations = 0
        methods_count = {"get": 0, "post": 0, "put": 0, "delete": 0, "patch": 0}
        
        for path, methods in paths.items():
            for method in methods.keys():
                if method.lower() in methods_count:
                    methods_count[method.lower()] += 1
                    total_operations += 1
        
        # 提取基本信息
        info = swagger_data.get("info", {})
        title = info.get("title", "未知")
        version = info.get("version", "未知")
        description = info.get("description", "")
        
        return {
            "success": True,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "message": "Swagger文档检测成功",
            "swagger_info": {
                "title": title,
                "version": version,
                "description": description[:200] if description else "",
                "openapi_version": swagger_data.get("openapi") or swagger_data.get("swagger"),
                "total_paths": total_paths,
                "total_operations": total_operations,
                "methods_count": methods_count,
                "safe_operations": methods_count["get"],
                "write_operations": methods_count["post"] + methods_count["put"] + methods_count["patch"] + methods_count["delete"]
            }
        }
    
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "status_code": 0,
            "duration_ms": request.timeout * 1000,
            "message": "请求超时",
            "error": "Swagger文档请求超时"
        }
    
    except requests.exceptions.ConnectionError as e:
        return {
            "success": False,
            "status_code": 0,
            "duration_ms": 0,
            "message": "连接失败",
            "error": f"无法连接到Swagger服务: {str(e)}"
        }
    
    except Exception as e:
        return {
            "success": False,
            "status_code": 0,
            "duration_ms": 0,
            "message": "检测失败",
            "error": str(e)
        }


@router.get("/safe-methods")
async def get_safe_methods():
    """
    获取安全的HTTP方法列表
    
    真实项目模式下，默认只允许执行这些方法
    """
    return {
        "safe_methods": ["GET", "HEAD", "OPTIONS"],
        "unsafe_methods": ["POST", "PUT", "PATCH", "DELETE"],
        "message": "真实项目模式下，默认只允许执行安全方法（GET/HEAD/OPTIONS）",
        "warning": "执行写操作（POST/PUT/PATCH/DELETE）需要用户明确确认"
    }
