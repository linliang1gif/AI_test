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
    module: Optional[str]
    priority: str
    status: str
    data_type: Optional[str]
    expected_behavior: Optional[str]
    source: Optional[str]
    created_at: datetime
    tags: Optional[List[str]]
    
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
