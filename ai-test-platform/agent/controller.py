#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Agent Controller - API路由控制器
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from .test_agent_service import get_test_agent_service


# 创建路由器
router = APIRouter(prefix="/agent", tags=["Test Agent"])


# ==================== 数据模型 ====================

class AnalyzeRequest(BaseModel):
    """分析请求模型"""
    requirement: str
    git_diff: Optional[str] = ""


class AnalyzeResponse(BaseModel):
    """分析响应模型 - V2增强版"""
    # V1 基础字段
    need_test: bool
    modules: list
    priority: str
    reason: str
    test_types: Optional[list] = []
    estimated_effort: Optional[str] = ""
    risk_level: Optional[str] = ""
    
    # V2 增强字段
    action: Optional[str] = ""
    confidence: Optional[float] = 0.0
    test_scope: Optional[Dict[str, Any]] = {}
    execution_hint: Optional[Dict[str, Any]] = {}
    timestamp: Optional[str] = ""
    
    # 元数据
    analyzed_at: Optional[str] = ""
    duration: Optional[str] = ""
    provider: Optional[str] = ""
    model: Optional[str] = ""


# ==================== API路由 ====================

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_test_need(request: AnalyzeRequest) -> Dict[str, Any]:
    """
    分析是否需要测试
    
    根据需求描述和代码变更，AI智能判断：
    - 是否需要执行测试
    - 影响哪些模块
    - 测试优先级
    - 预估工作量
    """
    try:
        service = get_test_agent_service()
        result = service.analyze(request.requirement, request.git_diff)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.get("/history")
async def get_decision_history(limit: int = 10):
    """
    获取决策历史
    
    Args:
        limit: 返回记录数量限制
    """
    try:
        service = get_test_agent_service()
        history = service.get_decision_history(limit)
        
        return {
            "success": True,
            "data": history,
            "count": len(history)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史失败: {str(e)}")


@router.get("/statistics")
async def get_statistics():
    """获取统计信息"""
    try:
        service = get_test_agent_service()
        stats = service.get_statistics()
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.get("/health")
async def health_check():
    """健康检查"""
    try:
        service = get_test_agent_service()
        
        return {
            "status": "healthy",
            "provider": service.llm_client.provider,
            "model": service.llm_client.model,
            "decisions_count": len(service.decision_history)
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
