"""
Strategy Controller - 策略API控制器
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from .strategy_service import get_strategy_service


# 创建路由器
router = APIRouter(prefix="/strategy", tags=["Test Strategy"])


# ==================== 数据模型 ====================

class GenerateStrategyRequest(BaseModel):
    """生成策略请求模型"""
    agent_decision: Dict[str, Any]


class ModuleInfo(BaseModel):
    """模块信息模型 - V2"""
    name: str
    impact: str


class ExecutionHint(BaseModel):
    """执行建议模型 - V2"""
    parallel: bool
    timeout: int


class ModuleStrategy(BaseModel):
    """模块策略模型 - V2增强"""
    module: ModuleInfo
    priority: str
    test_types: List[str]
    case_count: int
    execution_order: int
    risk_level: str = "中"
    execution_hint: ExecutionHint


class StrategySummary(BaseModel):
    """策略摘要模型 - V2"""
    total_modules: int
    estimated_total_cases: int
    risk_level: str


class GenerateStrategyResponse(BaseModel):
    """生成策略响应模型 - V2增强"""
    strategy: List[Dict[str, Any]]
    total_modules: int
    total_cases: int
    generated_at: str
    source_decision: str
    confidence: float
    summary: StrategySummary


# ==================== API路由 ====================

@router.post("/generate", response_model=GenerateStrategyResponse)
async def generate_strategy(request: GenerateStrategyRequest) -> Dict[str, Any]:
    """
    生成测试策略
    
    根据 Test Agent 的决策结果，生成结构化的测试策略。
    策略包含：
    - 每个模块的测试类型
    - 预估用例数量
    - 执行顺序
    """
    try:
        service = get_strategy_service()
        result = service.generate_strategy(request.agent_decision)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"策略生成失败: {str(e)}")


@router.get("/history")
async def get_strategy_history(limit: int = 10):
    """
    获取策略历史
    
    Args:
        limit: 返回记录数量限制
    """
    try:
        service = get_strategy_service()
        history = service.get_strategy_history(limit)
        
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
        service = get_strategy_service()
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
        service = get_strategy_service()
        
        return {
            "status": "healthy",
            "strategies_count": len(service.strategy_history)
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
