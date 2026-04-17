"""
触发系统 FastAPI 接口
"""
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from .test_trigger_system import TestTriggerSystem


# ==================== 请求模型 ====================

class GitPushRequest(BaseModel):
    """Git Push 触发请求"""
    repo: str = Field(..., description="仓库名称")
    branch: str = Field(..., description="分支名称")
    commit_id: str = Field(..., description="提交ID")
    commit_message: Optional[str] = Field(None, description="提交信息")
    changed_files: Optional[List[str]] = Field(None, description="变更文件列表")
    author: Optional[str] = Field(None, description="提交作者")


class ManualTriggerRequest(BaseModel):
    """手动触发请求"""
    requirement: str = Field(..., description="测试需求描述")
    priority: str = Field("P1", description="优先级 (P0/P1/P2/P3)")
    swagger_file: Optional[str] = Field(None, description="Swagger文件路径")
    config: Optional[Dict[str, Any]] = Field(None, description="额外配置")
    user: Optional[str] = Field(None, description="触发用户")


class ScheduledTriggerRequest(BaseModel):
    """定时触发请求"""
    cron_expression: str = Field(..., description="Cron表达式")
    requirement: str = Field(..., description="测试需求描述")
    job_name: str = Field(..., description="任务名称")
    priority: str = Field("P2", description="优先级")
    swagger_file: Optional[str] = Field(None, description="Swagger文件路径")
    config: Optional[Dict[str, Any]] = Field(None, description="额外配置")
    enabled: bool = Field(True, description="是否启用")


class UpdateScheduledJobRequest(BaseModel):
    """更新定时任务请求"""
    enabled: Optional[bool] = Field(None, description="是否启用")
    cron_expression: Optional[str] = Field(None, description="Cron表达式")


# ==================== 创建路由 ====================

def create_trigger_router(trigger_system: TestTriggerSystem) -> APIRouter:
    """
    创建触发系统路由
    
    Args:
        trigger_system: 触发系统实例
        
    Returns:
        FastAPI路由
    """
    router = APIRouter(prefix="/api/trigger", tags=["Trigger"])
    
    # ==================== Git Push 触发 ====================
    
    @router.post("/git-push")
    async def git_push_trigger(request: GitPushRequest):
        """
        Git Push 触发测试
        
        当代码推送到Git仓库时触发自动测试
        """
        try:
            result = trigger_system.on_git_push(
                repo=request.repo,
                branch=request.branch,
                commit_id=request.commit_id,
                commit_message=request.commit_message,
                changed_files=request.changed_files,
                author=request.author
            )
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # ==================== 手动触发 ====================
    
    @router.post("/manual")
    async def manual_trigger(request: ManualTriggerRequest):
        """
        手动触发测试
        
        通过API手动触发测试执行
        """
        try:
            result = trigger_system.manual_trigger(
                requirement=request.requirement,
                priority=request.priority,
                swagger_file=request.swagger_file,
                config=request.config,
                user=request.user
            )
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # ==================== 定时触发 ====================
    
    @router.post("/scheduled")
    async def create_scheduled_trigger(request: ScheduledTriggerRequest):
        """
        创建定时触发任务
        
        添加定时执行的测试任务（如每日回归测试）
        """
        try:
            result = trigger_system.schedule_trigger(
                cron_expression=request.cron_expression,
                requirement=request.requirement,
                job_name=request.job_name,
                priority=request.priority,
                swagger_file=request.swagger_file,
                config=request.config,
                enabled=request.enabled
            )
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/scheduled")
    async def list_scheduled_jobs():
        """
        列出所有定时任务
        """
        try:
            jobs = trigger_system.list_scheduled_jobs()
            return {"jobs": jobs, "total": len(jobs)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.put("/scheduled/{job_id}")
    async def update_scheduled_job(
        job_id: str,
        request: UpdateScheduledJobRequest
    ):
        """
        更新定时任务
        """
        try:
            result = trigger_system.update_scheduled_job(
                job_id=job_id,
                enabled=request.enabled,
                cron_expression=request.cron_expression
            )
            if not result.get("success"):
                raise HTTPException(status_code=404, detail=result.get("error"))
            return result
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.delete("/scheduled/{job_id}")
    async def delete_scheduled_job(job_id: str):
        """
        删除定时任务
        """
        try:
            result = trigger_system.delete_scheduled_job(job_id)
            if not result.get("success"):
                raise HTTPException(status_code=404, detail=result.get("error"))
            return result
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # ==================== 查询接口 ====================
    
    @router.get("/status/{trigger_id}")
    async def get_trigger_status(trigger_id: str):
        """
        获取触发状态
        
        查询指定触发ID的执行状态和结果
        """
        try:
            status = trigger_system.get_trigger_status(trigger_id)
            if not status:
                raise HTTPException(status_code=404, detail="触发记录不存在")
            return status
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/list")
    async def list_triggers(
        trigger_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ):
        """
        列出触发记录
        
        查询历史触发记录，支持按类型和状态过滤
        """
        try:
            triggers = trigger_system.list_triggers(
                trigger_type=trigger_type,
                status=status,
                limit=limit
            )
            return {"triggers": triggers, "total": len(triggers)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    return router
