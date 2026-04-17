"""
Pipeline Controller - 流程总调度API控制器
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from .pipeline_service import get_pipeline_service


# 创建路由器
router = APIRouter(prefix="/pipeline", tags=["AI Test Pipeline"])


# ==================== 数据模型 ====================

class PipelineRequest(BaseModel):
    """Pipeline 请求模型 V3 - 支持 TestContext"""
    requirement: str
    git_diff: Optional[str] = ""
    priority: Optional[str] = "P1"  # 新增：优先级
    use_case_generator: Optional[bool] = True  # 是否启用 Case Generator


class PipelineResponse(BaseModel):
    """Pipeline 响应模型 V3 - TestContext 结构"""
    # TestContext 核心字段
    trace_id: str
    requirement: str
    git_diff: str
    priority: str
    use_case_generator: bool
    
    # 阶段数据
    decision: Optional[Dict[str, Any]] = None
    strategy: Optional[Dict[str, Any]] = None
    cases: Optional[Dict[str, Any]] = None
    execution: Optional[Dict[str, Any]] = None
    healing: Optional[Dict[str, Any]] = None
    report: Optional[Dict[str, Any]] = None
    
    # 元数据
    timeline: List[Dict[str, Any]]
    created_at: str


# ==================== API路由 ====================

@router.post("/run", response_model=PipelineResponse)
async def run_pipeline(request: PipelineRequest) -> Dict[str, Any]:
    """
    运行完整测试流程 V3
    
    一键执行：
    1. Test Agent 决策分析（V3：含需求解析）
    2. Strategy Engine 策略生成
    3. Case Generator 用例生成（可选）
    4. Orchestrator 自动执行
    5. Self-Healing 自动修复
    6. Report 生成报告（V2：含覆盖率分析）
    
    支持提前退出：
    - 如果 Agent 判断无需测试，直接返回报告
    - 如果所有测试通过，跳过修复阶段
    
    支持可插拔：
    - use_case_generator=True: 启用 Case Generator（默认）
    - use_case_generator=False: 禁用 Case Generator，使用策略模式
    """
    try:
        service = get_pipeline_service()
        
        input_data = {
            "requirement": request.requirement,
            "git_diff": request.git_diff or "",
            "priority": request.priority or "P1",
            "use_case_generator": request.use_case_generator
        }
        
        result = service.run_pipeline(input_data)
        return result
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Pipeline 执行失败: {str(e)}")


@router.get("/history")
async def get_pipeline_history(limit: int = 10):
    """
    获取 Pipeline 历史
    
    Args:
        limit: 返回记录数量限制
    """
    try:
        service = get_pipeline_service()
        history = service.get_pipeline_history(limit)
        
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
        service = get_pipeline_service()
        stats = service.get_statistics()
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.get("/health")
async def health_check():
    """健康检查"""
    try:
        service = get_pipeline_service()
        
        return {
            "status": "healthy",
            "pipelines_count": len(service.pipeline_history)
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/trace/{trace_id}")
async def get_trace(trace_id: str):
    """
    根据 trace_id 查询流程详情
    
    Args:
        trace_id: 流程追踪ID
    """
    try:
        service = get_pipeline_service()
        
        # 查找对应的 pipeline
        for record in service.pipeline_history:
            if record.get('trace_id') == trace_id:
                return {
                    "success": True,
                    "data": record
                }
        
        raise HTTPException(status_code=404, detail=f"未找到 trace_id: {trace_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")
