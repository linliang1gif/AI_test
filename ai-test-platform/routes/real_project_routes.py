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
    yapi_email: Optional[str] = Field(None, description="YApi登录邮箱")
    yapi_password: Optional[str] = Field(None, description="YApi登录密码")


@router.post("/check-connection")
def check_connection(request: ConnectionCheckRequest):
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
def check_swagger(request: SwaggerCheckRequest):
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
            # JSON解析失败 → 可能是YApi HTML页面
            if _parse_yapi_base(request.swagger_url):
                return _try_yapi_check(request, duration_ms)
            return {
                "success": False,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "message": "Swagger文档格式错误",
                "error": f"无法解析JSON: {str(e)}"
            }
        
        # 判断是否为合法的OpenAPI/Swagger格式
        is_openapi = "openapi" in swagger_data or "swagger" in swagger_data
        
        # 检测YApi格式：errcode字段存在 → 尝试YApi登录流程
        if not is_openapi and "errcode" in swagger_data:
            return _try_yapi_check(request, duration_ms)
        
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
        
        # 判定 source_type
        detected_source_type = "swagger" if "swagger" in swagger_data else "openapi"

        return {
            "success": True,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "message": "Swagger文档检测成功",
            "source_type": detected_source_type,
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


def _parse_yapi_base(swagger_url: str) -> Optional[str]:
    """从各种YApi URL中提取base（如 https://yapi.xxx.com）"""
    from urllib.parse import urlparse
    parsed = urlparse(swagger_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    # 检测是否是YApi（域名含yapi 或 路径含/project/）
    if 'yapi' in parsed.netloc.lower() or '/project/' in parsed.path:
        return base
    return None


def _extract_yapi_project_id(swagger_url: str) -> Optional[int]:
    """从YApi URL中提取project_id"""
    import re
    # 匹配 /project/123 或 pid=123 或 project_id=123
    m = re.search(r'/project/(\d+)', swagger_url)
    if m:
        return int(m.group(1))
    m = re.search(r'pid=(\d+)', swagger_url)
    if m:
        return int(m.group(1))
    m = re.search(r'project_id=(\d+)', swagger_url)
    if m:
        return int(m.group(1))
    return None


def _try_yapi_check(request: "SwaggerCheckRequest", duration_ms: float) -> dict:
    """
    YApi检测逻辑：
    1. 解析YApi base URL和project_id
    2. 用邮箱密码登录获取cookie
    3. 用cookie访问 /api/interface/list_menu 获取接口列表
    """
    yapi_base = _parse_yapi_base(request.swagger_url)
    project_id = _extract_yapi_project_id(request.swagger_url)

    if not yapi_base:
        return {
            "success": False, "status_code": 0, "duration_ms": round(duration_ms, 2),
            "message": "不是合法的OpenAPI/Swagger文档",
            "error": "文档中缺少 'openapi' 或 'swagger' 字段"
        }

    if not project_id:
        return {
            "success": False, "status_code": 0, "duration_ms": round(duration_ms, 2),
            "message": "无法从URL中提取YApi项目ID",
            "error": "请使用类似 https://yapi.xxx.com/project/123/interface/api 格式的URL"
        }

    if not request.yapi_email or not request.yapi_password:
        return {
            "success": False, "status_code": 0, "duration_ms": round(duration_ms, 2),
            "message": "检测到YApi地址，但开放API不可用，需要登录",
            "error": "请填写YApi登录邮箱和密码",
            "need_yapi_login": True,
            "yapi_base": yapi_base,
            "yapi_project_id": project_id
        }

    # 尝试登录YApi
    session = requests.Session()
    try:
        start_time = time.time()
        login_resp = session.post(
            f"{yapi_base}/api/user/login",
            json={"email": request.yapi_email, "password": request.yapi_password},
            timeout=10
        )
        login_data = login_resp.json()
        if login_data.get("errcode") != 0:
            return {
                "success": False, "status_code": 0, "duration_ms": round(duration_ms, 2),
                "message": "YApi登录失败",
                "error": login_data.get("errmsg", "邮箱或密码错误")
            }

        # 获取接口菜单
        menu_resp = session.get(
            f"{yapi_base}/api/interface/list_menu",
            params={"project_id": project_id},
            timeout=10
        )
        menu_data = menu_resp.json()
        login_duration = (time.time() - start_time) * 1000

        if menu_data.get("errcode") != 0:
            return {
                "success": False, "status_code": 0, "duration_ms": round(login_duration, 2),
                "message": "YApi接口列表获取失败",
                "error": menu_data.get("errmsg", "未知错误")
            }

        categories = menu_data.get("data", [])
        total_interfaces = 0
        methods_count = {"get": 0, "post": 0, "put": 0, "delete": 0, "patch": 0}

        for cat in categories:
            for item in cat.get("list", []):
                total_interfaces += 1
                method = item.get("method", "").lower()
                if method in methods_count:
                    methods_count[method] += 1

        return {
            "success": True,
            "status_code": 200,
            "duration_ms": round(login_duration, 2),
            "message": "YApi文档检测成功",
            "source_type": "yapi",
            "yapi_base": yapi_base,
            "yapi_project_id": project_id,
            "swagger_info": {
                "title": f"YApi Project #{project_id}",
                "version": "yapi",
                "description": f"YApi接口，共{len(categories)}个分类，{total_interfaces}个接口",
                "openapi_version": "yapi",
                "total_paths": total_interfaces,
                "total_operations": total_interfaces,
                "methods_count": methods_count,
                "safe_operations": methods_count["get"],
                "write_operations": methods_count["post"] + methods_count["put"] + methods_count["patch"] + methods_count["delete"]
            }
        }

    except Exception as e:
        return {
            "success": False, "status_code": 0, "duration_ms": round(duration_ms, 2),
            "message": "YApi检测失败",
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
