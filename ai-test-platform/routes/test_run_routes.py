#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试执行路由 - 使用数据库和状态机
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from services.test_run_service import TestRunService
from services.state_machine import RunStateMachine
from schemas.test_run_schemas import (
    TestRunCreate,
    TestRunUpdate,
    TestRunResponse,
    RunCaseResponse,
    StatusUpdateRequest,
    StatusHistoryResponse,
    StateTransitionInfo
)

router = APIRouter(prefix="/api/v2/test-runs", tags=["测试执行"])


@router.post("", response_model=TestRunResponse, status_code=201)
async def create_test_run(
    run_data: TestRunCreate,
    db: Session = Depends(get_db)
):
    """
    创建测试执行
    
    - 自动生成run_id和trace_id
    - 初始状态为'created'
    - 记录状态历史
    """
    try:
        service = TestRunService(db)
        test_run = service.create_test_run(run_data)
        return test_run
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建测试执行失败: {str(e)}")


@router.get("", response_model=List[TestRunResponse])
async def get_test_runs(
    project_id: Optional[int] = Query(None, description="项目ID过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(50, ge=1, le=100, description="限制数量"),
    db: Session = Depends(get_db)
):
    """
    获取测试执行列表
    
    - 支持按项目ID过滤
    - 支持按状态过滤
    - 支持分页
    """
    try:
        service = TestRunService(db)
        test_runs = service.get_test_runs(
            project_id=project_id,
            status=status,
            skip=skip,
            limit=limit
        )
        return test_runs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取测试执行列表失败: {str(e)}")


@router.get("/{run_id}", response_model=TestRunResponse)
async def get_test_run(
    run_id: str,
    db: Session = Depends(get_db)
):
    """
    获取测试执行详情
    
    - 返回完整的测试执行信息
    """
    try:
        service = TestRunService(db)
        test_run = service.get_test_run(run_id)
        if not test_run:
            raise HTTPException(status_code=404, detail=f"测试执行 {run_id} 不存在")
        return test_run
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取测试执行失败: {str(e)}")


@router.put("/{run_id}/status", response_model=TestRunResponse)
async def update_run_status(
    run_id: str,
    status_data: StatusUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    更新测试执行状态
    
    - 自动验证状态流转合法性
    - 记录状态历史
    - 自动更新时间戳
    
    状态流转规则:
    - created → queued
    - queued → preparing | aborted
    - preparing → running | failed | aborted
    - running → passed | failed | aborted | healing
    - healing → passed | failed | aborted
    """
    try:
        service = TestRunService(db)
        updated_run = service.update_run_status(run_id, status_data)
        return updated_run
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新状态失败: {str(e)}")


@router.get("/{run_id}/cases", response_model=List[RunCaseResponse])
async def get_run_cases(
    run_id: str,
    db: Session = Depends(get_db)
):
    """
    获取测试执行的所有用例记录
    
    - 返回该run下所有用例的执行记录
    """
    try:
        service = TestRunService(db)
        
        # 先检查run是否存在
        test_run = service.get_test_run(run_id)
        if not test_run:
            raise HTTPException(status_code=404, detail=f"测试执行 {run_id} 不存在")
        
        run_cases = service.get_run_cases(run_id)
        return run_cases
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用例记录失败: {str(e)}")


@router.get("/{run_id}/history", response_model=List[StatusHistoryResponse])
async def get_run_status_history(
    run_id: str,
    db: Session = Depends(get_db)
):
    """
    获取测试执行的状态历史
    
    - 返回该run的所有状态变更记录
    - 按时间升序排列
    """
    try:
        service = TestRunService(db)
        
        # 先检查run是否存在
        test_run = service.get_test_run(run_id)
        if not test_run:
            raise HTTPException(status_code=404, detail=f"测试执行 {run_id} 不存在")
        
        history = service.get_status_history('run', run_id)
        return history
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取状态历史失败: {str(e)}")


@router.get("/{run_id}/state-info", response_model=StateTransitionInfo)
async def get_state_transition_info(
    run_id: str,
    db: Session = Depends(get_db)
):
    """
    获取当前状态的流转信息
    
    - 返回当前状态
    - 返回允许的目标状态
    - 返回是否为终态
    """
    try:
        service = TestRunService(db)
        test_run = service.get_test_run(run_id)
        if not test_run:
            raise HTTPException(status_code=404, detail=f"测试执行 {run_id} 不存在")
        
        current_status = test_run.status
        allowed_transitions = list(RunStateMachine.get_allowed_transitions(current_status))
        is_final = RunStateMachine.is_final_state(current_status)
        
        return StateTransitionInfo(
            current_status=current_status,
            allowed_transitions=allowed_transitions,
            is_final_state=is_final
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取状态信息失败: {str(e)}")


@router.get("/{run_id}/cases/{case_id}")
async def get_run_case_detail(
    run_id: str,
    case_id: int,
    db: Session = Depends(get_db)
):
    """
    获取单个 RunCase 详情
    
    - 返回 RunCase 的完整信息，包括快照
    """
    try:
        from database import RunCase
        
        # 查询 RunCase
        run_case = db.query(RunCase).filter(
            RunCase.run_id == run_id,
            RunCase.id == case_id
        ).first()
        
        if not run_case:
            raise HTTPException(status_code=404, detail=f"RunCase {case_id} 不存在")
        
        return {
            "id": run_case.id,
            "run_id": run_case.run_id,
            "test_case_id": run_case.test_case_id,
            "status": run_case.status,
            "retry_count": run_case.retry_count,
            "start_time": run_case.start_time.isoformat() if run_case.start_time else None,
            "end_time": run_case.end_time.isoformat() if run_case.end_time else None,
            "duration": run_case.duration,
            "error_message": run_case.error_message,
            "error_type": run_case.error_type,
            "stack_trace": run_case.stack_trace,
            "request_snapshot": run_case.request_snapshot,
            "response_snapshot": run_case.response_snapshot,
            "assertions_passed": run_case.assertions_passed,
            "assertions_failed": run_case.assertions_failed,
            "assertion_details": run_case.assertion_details,
            "healing_applied": run_case.healing_applied,
            "healing_level": run_case.healing_level,
            "healing_details": run_case.healing_details
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取 RunCase 详情失败: {str(e)}")


@router.get("/cases/{run_case_id}/history", response_model=List[StatusHistoryResponse])
async def get_run_case_status_history(
    run_case_id: int,
    db: Session = Depends(get_db)
):
    """
    获取用例执行的状态历史
    
    - 返回该run_case的所有状态变更记录
    """
    try:
        service = TestRunService(db)
        history = service.get_status_history('run_case', str(run_case_id))
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用例状态历史失败: {str(e)}")


@router.get("/steps/{run_step_id}/history", response_model=List[StatusHistoryResponse])
async def get_run_step_status_history(
    run_step_id: int,
    db: Session = Depends(get_db)
):
    """
    获取步骤执行的状态历史
    
    - 返回该run_step的所有状态变更记录
    """
    try:
        service = TestRunService(db)
        history = service.get_status_history('run_step', str(run_step_id))
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取步骤状态历史失败: {str(e)}")


@router.get("/state-machine/diagram")
async def get_state_machine_diagram():
    """
    获取状态机流转图
    
    - 返回状态流转规则的文字描述
    """
    return {
        "success": True,
        "diagram": RunStateMachine.get_state_flow_diagram(),
        "valid_transitions": RunStateMachine.VALID_TRANSITIONS,
        "final_states": list(RunStateMachine.FINAL_STATES)
    }
