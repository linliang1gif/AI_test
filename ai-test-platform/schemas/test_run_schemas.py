#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试执行相关的Pydantic Schema
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class TestRunCreate(BaseModel):
    """创建测试执行请求"""
    project_id: int = Field(..., description="项目ID")
    environment_id: int = Field(..., description="环境ID")
    trigger_type: Optional[str] = Field('manual', description="触发类型: manual/scheduled/ci/api")
    created_by: Optional[str] = Field('system', description="创建人")
    
    @validator('trigger_type')
    def validate_trigger_type(cls, v):
        allowed = ['manual', 'scheduled', 'ci', 'api']
        if v and v not in allowed:
            raise ValueError(f"trigger_type必须是以下之一: {', '.join(allowed)}")
        return v


class TestRunUpdate(BaseModel):
    """更新测试执行请求"""
    total_cases: Optional[int] = None
    passed_cases: Optional[int] = None
    failed_cases: Optional[int] = None
    skipped_cases: Optional[int] = None
    summary: Optional[str] = None


class StatusUpdateRequest(BaseModel):
    """状态更新请求"""
    status: str = Field(..., description="新状态")
    changed_by: Optional[str] = Field('system', description="操作人")
    reason: Optional[str] = Field(None, description="变更原因")
    
    @validator('status')
    def validate_status(cls, v):
        allowed = ['created', 'queued', 'preparing', 'running', 'healing', 'passed', 'failed', 'aborted']
        if v not in allowed:
            raise ValueError(f"status必须是以下之一: {', '.join(allowed)}")
        return v


class TestRunResponse(BaseModel):
    """测试执行响应"""
    id: str
    project_id: Optional[int]
    environment_id: Optional[int]
    trigger_type: str
    status: str
    trace_id: str
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    duration: Optional[float]
    total_cases: int
    passed_cases: int
    failed_cases: int
    skipped_cases: int
    summary: Optional[str]
    created_at: datetime
    created_by: str
    
    class Config:
        from_attributes = True


class RunCaseResponse(BaseModel):
    """用例执行记录响应"""
    id: int
    run_id: str
    test_case_id: str
    status: str
    retry_count: int
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    duration: Optional[float]
    error_message: Optional[str]
    error_type: Optional[str]
    assertions_passed: int
    assertions_failed: int
    healing_applied: bool
    healing_level: Optional[str]
    
    class Config:
        from_attributes = True


class StatusHistoryResponse(BaseModel):
    """状态历史响应"""
    id: int
    entity_type: str
    entity_id: str
    from_status: Optional[str]
    to_status: str
    changed_at: datetime
    changed_by: str
    reason: Optional[str]
    
    class Config:
        from_attributes = True


class StateTransitionInfo(BaseModel):
    """状态流转信息"""
    current_status: str
    allowed_transitions: List[str]
    is_final_state: bool
