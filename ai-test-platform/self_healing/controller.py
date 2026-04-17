"""
Self-Healing Controller - 自动修复API控制器
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from .healing_service import get_healing_service


# 创建路由器
router = APIRouter(prefix="/healing", tags=["Self-Healing"])


# ==================== 数据模型 ====================

class FixRequest(BaseModel):
    """修复请求模型"""
    module: str
    error: str
    test_type: str = "api"


class ErrorAnalysis(BaseModel):
    """错误分析模型"""
    type: str
    severity: str
    fixable: bool
    details: str


class RetryResult(BaseModel):
    """重试结果模型"""
    status: str
    duration: float
    details: str


class FixResponse(BaseModel):
    """修复响应模型"""
    fixed: bool
    reason: str
    confidence: float
    error_analysis: Optional[ErrorAnalysis] = None
    fix_strategy: Optional[str] = None
    retry_result: Optional[Dict[str, Any]] = None
    timestamp: str


# ==================== API路由 ====================

@router.post("/fix", response_model=FixResponse)
async def fix_error(request: FixRequest) -> Dict[str, Any]:
    """
    自动修复测试失败
    
    分析错误原因，应用修复策略，重新执行测试。
    支持的错误类型：
    - assertion: 断言错误
    - timeout: 超时错误
    - server_error: 服务器错误
    - not_found: 404 错误
    - auth_error: 认证错误
    """
    try:
        service = get_healing_service()
        
        failure_info = {
            "module": request.module,
            "error": request.error,
            "test_type": request.test_type
        }
        
        result = service.fix_and_retry(failure_info)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"修复失败: {str(e)}")


@router.get("/history")
async def get_healing_history(limit: int = 10):
    """
    获取修复历史
    
    Args:
        limit: 返回记录数量限制
    """
    try:
        service = get_healing_service()
        history = service.get_healing_history(limit)
        
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
        service = get_healing_service()
        stats = service.get_statistics()
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.get("/suggestions/{error_type}")
async def get_fix_suggestions(error_type: str):
    """
    获取修复建议
    
    Args:
        error_type: 错误类型
    """
    try:
        service = get_healing_service()
        suggestions = service.get_fix_suggestions(error_type)
        
        return {
            "success": True,
            "error_type": error_type,
            "suggestions": suggestions,
            "count": len(suggestions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取建议失败: {str(e)}")


@router.get("/health")
async def health_check():
    """健康检查"""
    try:
        service = get_healing_service()
        
        return {
            "status": "healthy",
            "healings_count": len(service.healing_history)
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
