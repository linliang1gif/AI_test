#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目配置相关Schemas
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class EnvironmentType(str, Enum):
    """环境类型枚举"""
    dev = "dev"
    test = "test"
    staging = "staging"
    prod = "prod"


class AuthType(str, Enum):
    """鉴权类型枚举"""
    none = "none"
    bearer = "bearer"
    basic = "basic"
    apikey = "apikey"
    cookie = "cookie"
    oauth2 = "oauth2"
    custom = "custom"


# ==================== Project Schemas ====================

class ProjectCreate(BaseModel):
    """创建项目请求"""
    name: str = Field(..., min_length=1, max_length=200, description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    owner: Optional[str] = Field(None, max_length=100, description="负责人")
    team: Optional[str] = Field(None, max_length=100, description="团队")


class ProjectUpdate(BaseModel):
    """更新项目请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|archived)$")
    owner: Optional[str] = Field(None, max_length=100)
    team: Optional[str] = Field(None, max_length=100)


class ProjectResponse(BaseModel):
    """项目响应"""
    id: int
    name: str
    description: Optional[str]
    status: str
    owner: Optional[str]
    team: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # Pydantic v2
        # orm_mode = True  # Pydantic v1


# ==================== Environment Schemas ====================

class EnvironmentCreate(BaseModel):
    """创建环境请求"""
    project_id: int = Field(..., description="项目ID")
    name: EnvironmentType = Field(..., description="环境名称")
    base_url: str = Field(..., min_length=1, max_length=500, description="基础URL")
    is_protected: bool = Field(False, description="是否保护环境")
    allow_write: bool = Field(True, description="是否允许写操作测试")
    timeout_seconds: int = Field(30, ge=1, le=300, description="超时时间(秒)")
    retry_count: int = Field(0, ge=0, le=5, description="重试次数")
    
    @validator('base_url')
    def validate_base_url(cls, v):
        """验证base_url格式"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('base_url必须以http://或https://开头')
        return v.rstrip('/')  # 移除末尾斜杠


class EnvironmentUpdate(BaseModel):
    """更新环境请求"""
    name: Optional[EnvironmentType] = None
    base_url: Optional[str] = Field(None, min_length=1, max_length=500)
    is_protected: Optional[bool] = None
    allow_write: Optional[bool] = None
    timeout_seconds: Optional[int] = Field(None, ge=1, le=300)
    retry_count: Optional[int] = Field(None, ge=0, le=5)
    
    @validator('base_url')
    def validate_base_url(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('base_url必须以http://或https://开头')
        return v.rstrip('/') if v else v


class EnvironmentResponse(BaseModel):
    """环境响应"""
    id: int
    project_id: int
    name: str
    base_url: str
    is_protected: bool
    allow_write: bool
    timeout_seconds: int
    retry_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ==================== AuthProfile Schemas ====================

class AuthProfileCreate(BaseModel):
    """创建鉴权配置请求"""
    environment_id: int = Field(..., description="环境ID")
    auth_type: AuthType = Field(..., description="鉴权类型")
    auth_config: Optional[Dict[str, Any]] = Field(None, description="鉴权配置")
    default_headers: Optional[Dict[str, str]] = Field(None, description="默认请求头")
    
    @validator('auth_config')
    def validate_auth_config(cls, v, values):
        """根据auth_type验证auth_config"""
        if not v:
            return v
        
        auth_type = values.get('auth_type')
        
        if auth_type == AuthType.bearer:
            if 'token' not in v:
                raise ValueError('bearer类型需要提供token字段')
        elif auth_type == AuthType.apikey:
            if 'key_name' not in v or 'key_value' not in v:
                raise ValueError('apikey类型需要提供key_name和key_value字段')
        
        return v


class AuthProfileUpdate(BaseModel):
    """更新鉴权配置请求"""
    auth_type: Optional[AuthType] = None
    auth_config: Optional[Dict[str, Any]] = None
    default_headers: Optional[Dict[str, str]] = None


class AuthProfileResponse(BaseModel):
    """鉴权配置响应(敏感信息脱敏)"""
    id: int
    environment_id: int
    auth_type: str
    auth_config_masked: Optional[Dict[str, Any]] = Field(None, description="脱敏后的鉴权配置")
    default_headers: Optional[Dict[str, str]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
