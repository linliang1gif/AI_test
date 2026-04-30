#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行触发路由 - 触发真实测试执行
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from database import get_db
from core import TestCase, create_test_case
from services.execution_orchestrator import ExecutionOrchestrator
from modules.executor import ExecutionEngine


router = APIRouter(prefix="/api/v2/execution", tags=["执行触发"])


class TestCaseInput(BaseModel):
    """测试用例输入"""
    id: str
    title: str
    module: str = "default"
    priority: str = "medium"
    steps: List[dict] = []
    expected: str = ""
    data_type: str = "valid"
    expected_behavior: str = "success"
    execution_config: dict
    assertions: List[dict] = []


class ExecutionTriggerRequest(BaseModel):
    """执行触发请求"""
    project_id: int
    environment_id: int
    test_cases: List[TestCaseInput]
    trigger_type: str = "manual"
    created_by: str = "user"
    max_workers: int = 5
    parallel: bool = False


class ExecutionTriggerResponse(BaseModel):
    """执行触发响应"""
    success: bool
    run_id: str
    trace_id: str
    status: str
    message: str


@router.post("/trigger", response_model=ExecutionTriggerResponse)
async def trigger_execution(
    request: ExecutionTriggerRequest,
    db: Session = Depends(get_db)
):
    """
    触发测试执行
    
    - 创建TestRun
    - 执行测试用例
    - 返回run_id和trace_id
    
    Args:
        request: 执行触发请求
        
    Returns:
        ExecutionTriggerResponse: 包含run_id和trace_id
    """
    try:
        # 1. 转换测试用例
        test_cases = []
        for tc_input in request.test_cases:
            test_case = create_test_case(
                id=tc_input.id,
                title=tc_input.title,
                module=tc_input.module,
                priority=tc_input.priority,
                steps=tc_input.steps,
                expected=tc_input.expected,
                data_type=tc_input.data_type,
                expected_behavior=tc_input.expected_behavior,
                execution_config=tc_input.execution_config,
                assertions=tc_input.assertions
            )
            test_cases.append(test_case)
        
        # 2. 创建执行引擎和编排器
        execution_engine = ExecutionEngine()
        orchestrator = ExecutionOrchestrator(db, execution_engine)
        
        # 3. 执行测试
        result = orchestrator.execute_test_cases(
            test_cases=test_cases,
            project_id=request.project_id,
            environment_id=request.environment_id,
            trigger_type=request.trigger_type,
            created_by=request.created_by,
            max_workers=request.max_workers,
            parallel=request.parallel
        )
        
        # 4. 返回结果
        if result.get('success'):
            return ExecutionTriggerResponse(
                success=True,
                run_id=result['run_id'],
                trace_id=result.get('trace_id', ''),
                status=result.get('status', 'unknown'),
                message=f"执行完成: {result['statistics']['passed']}/{result['statistics']['total']} 通过"
            )
        else:
            return ExecutionTriggerResponse(
                success=False,
                run_id=result.get('run_id', ''),
                trace_id='',
                status='failed',
                message=f"执行失败: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"触发执行失败: {str(e)}"
        )


@router.post("/trigger-simple", response_model=ExecutionTriggerResponse)
async def trigger_simple_execution(
    project_id: int = Query(..., description="项目ID"),
    environment_id: int = Query(..., description="环境ID"),
    test_case_ids: List[str] = Query(..., description="测试用例ID列表"),
    db: Session = Depends(get_db)
):
    """
    简化的执行触发(用于快速测试)
    
    - 使用httpbin.org创建简单测试用例
    - 适合前端快速验证
    
    Args:
        project_id: 项目ID
        environment_id: 环境ID
        test_case_ids: 测试用例ID列表
        
    Returns:
        ExecutionTriggerResponse: 包含run_id和trace_id
    """
    try:
        # 创建简单的httpbin测试用例
        test_cases = []
        for tc_id in test_case_ids:
            test_case = create_test_case(
                id=tc_id,
                title=f"测试用例 - {tc_id}",
                module="httpbin",
                priority="medium",
                steps=[],
                expected="返回200",
                data_type="valid",
                expected_behavior="success",
                execution_config={
                    "method": "GET",
                    "url": "https://httpbin.org/get",
                    "headers": {"User-Agent": "Test"},
                    "params": {"test": tc_id}
                },
                assertions=[
                    {"type": "status_code", "expected": 200}
                ]
            )
            test_cases.append(test_case)
        
        # 执行
        execution_engine = ExecutionEngine()
        orchestrator = ExecutionOrchestrator(db, execution_engine)
        
        result = orchestrator.execute_test_cases(
            test_cases=test_cases,
            project_id=project_id,
            environment_id=environment_id,
            trigger_type='manual',
            created_by='user',
            max_workers=1,
            parallel=False
        )
        
        if result.get('success'):
            return ExecutionTriggerResponse(
                success=True,
                run_id=result['run_id'],
                trace_id=result.get('trace_id', ''),
                status=result.get('status', 'unknown'),
                message=f"执行完成: {result['statistics']['passed']}/{result['statistics']['total']} 通过"
            )
        else:
            return ExecutionTriggerResponse(
                success=False,
                run_id=result.get('run_id', ''),
                trace_id='',
                status='failed',
                message=f"执行失败: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"触发执行失败: {str(e)}"
        )
