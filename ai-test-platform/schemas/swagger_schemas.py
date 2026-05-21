#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Swagger/OpenAPI 相关的 Pydantic 模型
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SwaggerImportFromUrlRequest(BaseModel):
    """从 URL 导入 Swagger 请求"""
    project_id: int = Field(..., description="项目ID")
    url: str = Field(..., description="Swagger URL")
    generate_cases: bool = Field(True, description="是否自动生成测试用例")
    auth_type: Optional[str] = Field(None, description="鉴权方式: none/bearer/basic")
    token: Optional[str] = Field(None, description="鉴权Token（仅用于请求，不存储）")


class SwaggerImportResponse(BaseModel):
    """Swagger 导入响应"""
    api_spec_id: int = Field(..., description="API规范ID")
    project_id: int = Field(..., description="项目ID")
    version: str = Field(..., description="API版本")
    api_count: int = Field(..., description="API数量")
    test_cases_generated: int = Field(..., description="生成的测试用例数量")
    test_case_ids: List[str] = Field(..., description="测试用例ID列表")
    imported_at: str = Field(..., description="导入时间")


class ApiSpecResponse(BaseModel):
    """API规范响应"""
    id: int
    project_id: int
    source_type: str
    source_url: Optional[str]
    version: Optional[str]
    api_count: int
    imported_at: datetime
    
    class Config:
        from_attributes = True


class TestCaseResponse(BaseModel):
    """测试用例响应"""
    id: str
    title: str
    module: Optional[str] = None
    priority: str = 'medium'
    status: str = 'pending'
    data_type: Optional[str] = None
    expected_behavior: Optional[str] = None
    source: Optional[str] = None
    case_type: Optional[str] = None
    created_at: Optional[datetime] = None
    tags: Optional[List[str]] = None
    # 前端展示所需字段
    steps: Optional[list] = None
    expected: Optional[str] = None
    execution_config: Optional[dict] = None
    assertions: Optional[list] = None
    dataset_id: Optional[str] = None
    api_id: Optional[str] = None
    # Phase 16: 治理字段
    module_name: Optional[str] = None
    api_pattern: Optional[str] = None
    risk_level: Optional[str] = None
    executable: Optional[bool] = None
    requires_auth: Optional[bool] = None
    requires_dependency: Optional[bool] = None
    destructive: Optional[bool] = None
    assertion_status: Optional[str] = None
    last_run_status: Optional[str] = None
    failure_category: Optional[str] = None
    # Iteration
    iteration_id: Optional[int] = None
    
    class Config:
        from_attributes = True


class TestCaseListResponse(BaseModel):
    """测试用例列表响应"""
    total: int
    test_cases: List[TestCaseResponse]


class GenerateTestCasesRequest(BaseModel):
    """生成测试用例请求"""
    api_spec_id: int = Field(..., description="API规范ID")


class GenerateTestCasesResponse(BaseModel):
    """生成测试用例响应"""
    api_spec_id: int
    test_cases_generated: int
    test_case_ids: List[str]
