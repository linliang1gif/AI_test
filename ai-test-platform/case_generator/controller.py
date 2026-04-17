#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Case Generator Controller - 用例生成器控制器
提供 FastAPI 路由和请求处理
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

from .case_service import get_case_service


# ==================== 请求模型 ====================

class GenerateCasesRequest(BaseModel):
    """生成用例请求"""
    strategy: dict = Field(..., description="策略引擎输出")
    
    class Config:
        json_schema_extra = {
            "example": {
                "strategy": {
                    "strategy": [
                        {
                            "module": {"name": "支付模块", "impact": "high"},
                            "priority": "P0",
                            "test_types": ["api", "integration"],
                            "case_count": 10,
                            "execution_order": 1,
                            "risk_level": "高",
                            "execution_hint": {"parallel": True, "timeout": 60}
                        }
                    ],
                    "total_modules": 1,
                    "total_cases": 10
                }
            }
        }


# ==================== 响应模型 ====================

class TestCaseModel(BaseModel):
    """测试用例模型"""
    id: str
    title: str
    module: str
    testpoint: str
    scenario_id: str
    precondition: str
    steps: List[str]
    test_data: str
    expected_result: str
    priority: str
    type: str
    complexity: str
    estimated_time: int
    automation_feasible: Dict[str, Any]
    risk_level: str
    tags: List[str]


class ModuleCasesModel(BaseModel):
    """模块用例模型"""
    module: str
    cases: List[TestCaseModel]


class GenerateCasesResponse(BaseModel):
    """生成用例响应"""
    cases: List[ModuleCasesModel]
    total_cases: int
    generated_at: str
    source_strategy: str


class CaseHistoryResponse(BaseModel):
    """用例历史响应"""
    history: List[Dict[str, Any]]
    total: int


class CaseStatisticsResponse(BaseModel):
    """用例统计响应"""
    total_generations: int
    total_cases: int
    avg_cases_per_generation: float


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    service: str
    timestamp: str


# ==================== 路由器 ====================

case_router = APIRouter(prefix="/case", tags=["Case Generator"])


@case_router.post("/generate", response_model=GenerateCasesResponse)
async def generate_cases(request: GenerateCasesRequest):
    """
    生成测试用例
    
    根据策略引擎输出生成详细的测试用例
    """
    try:
        service = get_case_service()
        result = service.generate_cases(request.strategy)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"用例生成失败: {str(e)}")


@case_router.get("/history", response_model=CaseHistoryResponse)
async def get_case_history(limit: int = 10):
    """
    获取用例生成历史
    
    Args:
        limit: 返回记录数量限制
    """
    try:
        service = get_case_service()
        history = service.get_case_history(limit)
        return {
            "history": history,
            "total": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史失败: {str(e)}")


@case_router.get("/statistics", response_model=CaseStatisticsResponse)
async def get_case_statistics():
    """
    获取用例生成统计信息
    """
    try:
        service = get_case_service()
        stats = service.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@case_router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    健康检查
    """
    return {
        "status": "healthy",
        "service": "case_generator",
        "timestamp": datetime.now().isoformat()
    }
