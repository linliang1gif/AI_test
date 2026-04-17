#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Test Platform - 认证模块

提供简单的API认证功能。
"""

import jwt
import time
import secrets
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from utils.logger import get_logger

logger = get_logger("auth")

# 配置
SECRET_KEY = "ai-test-platform-secret-key-2024"  # 生产环境应使用环境变量
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24小时

# 简单的用户存储（生产环境应使用数据库）
USERS = {
    "admin": {
        "username": "admin",
        "password": "admin123",  # 生产环境应使用哈希密码
        "role": "admin"
    },
    "user": {
        "username": "user",
        "password": "user123",
        "role": "user"
    }
}

security = HTTPBearer(auto_error=False)

class AuthManager:
    """认证管理器"""
    
    def __init__(self):
        self.secret_key = SECRET_KEY
        self.algorithm = ALGORITHM
        
    def create_access_token(self, username: str, role: str = "user") -> str:
        """创建访问令牌"""
        payload = {
            "sub": username,
            "role": role,
            "exp": time.time() + (ACCESS_TOKEN_EXPIRE_MINUTES * 60),
            "iat": time.time()
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        logger.info(f"创建访问令牌 - 用户: {username}, 角色: {role}")
        return token
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # 检查过期时间
            if payload.get("exp", 0) < time.time():
                logger.warning("令牌已过期")
                return None
            
            return {
                "username": payload.get("sub"),
                "role": payload.get("role", "user"),
                "exp": payload.get("exp")
            }
            
        except jwt.InvalidTokenError as e:
            logger.warning(f"无效令牌: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"令牌验证失败", e)
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """验证用户凭据"""
        user = USERS.get(username)
        if user and user["password"] == password:
            logger.info(f"用户认证成功: {username}")
            return user
        
        logger.warning(f"用户认证失败: {username}")
        return None

# 全局认证管理器
auth_manager = AuthManager()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """获取当前用户（依赖注入）"""
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_info = auth_manager.verify_token(credentials.credentials)
    if not user_info:
        raise HTTPException(
            status_code=401,
            detail="无效或过期的令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_info

def get_admin_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """获取管理员用户（依赖注入）"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="需要管理员权限"
        )
    
    return current_user

def optional_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[Dict[str, Any]]:
    """可选认证（不强制要求令牌）"""
    if not credentials:
        return None
    
    return auth_manager.verify_token(credentials.credentials)

class RateLimiter:
    """简单的速率限制器"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # {ip: [(timestamp, count), ...]}
    
    def is_allowed(self, client_ip: str) -> bool:
        """检查是否允许请求"""
        now = time.time()
        window_start = now - self.window_seconds
        
        # 清理过期记录
        if client_ip in self.requests:
            self.requests[client_ip] = [
                (ts, count) for ts, count in self.requests[client_ip]
                if ts > window_start
            ]
        else:
            self.requests[client_ip] = []
        
        # 计算当前窗口内的请求数
        current_requests = sum(count for ts, count in self.requests[client_ip])
        
        if current_requests >= self.max_requests:
            logger.warning(f"速率限制触发 - IP: {client_ip}, 请求数: {current_requests}")
            return False
        
        # 记录当前请求
        self.requests[client_ip].append((now, 1))
        return True

# 全局速率限制器
rate_limiter = RateLimiter()

def check_rate_limit(request: Request):
    """检查速率限制（依赖注入）"""
    client_ip = request.client.host
    
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=429,
            detail="请求过于频繁，请稍后再试"
        )
    
    return True