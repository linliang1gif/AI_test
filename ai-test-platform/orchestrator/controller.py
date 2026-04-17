"""
Orchestrator Controller - 调度器API控制器
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

from .orchestrator_service import get_orchestrator_service


# 创建路由器
router = APIRouter(prefix="/orchestrator", tags=["Test Orchestrator"])


# ==================== 数据模型 ====================

class RunRequest(BaseModel):
    """执行请求模型"""
    strategy: Dict[str, Any]
    cases: Dict[str, Any] = None  # 可选：来自 Case Generator 的用例


class TestResult(BaseModel):
    """测试结果模型"""
    module: str
    status: str
    duration: float
    details: str


class ExecutionSummary(BaseModel):
    """执行摘要模型"""
    total: int
    passed: int
    failed: int
    duration: float
    pass_rate: float


class RunResponse(BaseModel):
    """执行响应模型"""
    results: List[Dict[str, Any]]
    summary: ExecutionSummary
    executed_at: str


# ==================== API路由 ====================

@router.post("/run", response_model=RunResponse)
async def run_tests(request: RunRequest) -> Dict[str, Any]:
    """
    执行测试
    
    根据 Strategy Engine 生成的策略，自动调度并执行测试。
    支持：
    - 按 execution_order 排序执行
    - 并发执行（根据 execution_hint.parallel）
    - 多种测试类型（api/ui/integration）
    - 兼容模式：可选传入 cases 参数（来自 Case Generator）
    """
    try:
        service = get_orchestrator_service()
        result = service.run(request.strategy, cases=request.cases)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")


@router.get("/history")
async def get_execution_history(limit: int = 10):
    """
    获取执行历史
    
    Args:
        limit: 返回记录数量限制
    """
    try:
        service = get_orchestrator_service()
        history = service.get_execution_history(limit)
        
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
        service = get_orchestrator_service()
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
        service = get_orchestrator_service()
        
        return {
            "status": "healthy",
            "executions_count": len(service.execution_history)
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
