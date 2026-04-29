#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可观测性查询API
提供TestRun/RunCase/RunStep的查询接口
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from database import get_db, TestRun, RunCase, RunStep, RunStatusHistory
from services.test_run_service import TestRunService


router = APIRouter(prefix="/api/v2/observability", tags=["observability"])


# 敏感Header/字段脱敏
_SENSITIVE_KEYS = {
    'authorization', 'token', 'access_token', 'refresh_token',
    'password', 'secret', 'cookie', 'session', 'x-token', 'api-key',
}

def _sanitize(data):
    """递归脱敏敏感字段"""
    if isinstance(data, dict):
        return {k: ('******' if k.lower() in _SENSITIVE_KEYS and v else _sanitize(v)) for k, v in data.items()}
    elif isinstance(data, list):
        return [_sanitize(item) for item in data]
    return data


def _serialize_run_case(rc, full=False):
    """序列化RunCase，full=True时包含完整快照"""
    req_snap = rc.request_snapshot or {}
    resp_snap = rc.response_snapshot or {}
    result = {
        "id": rc.id,
        "run_id": rc.run_id,
        "test_case_id": rc.test_case_id,
        "status": rc.status,
        "start_time": rc.start_time.isoformat() if rc.start_time else None,
        "end_time": rc.end_time.isoformat() if rc.end_time else None,
        "duration": rc.duration,
        "error_message": rc.error_message,
        "error_type": rc.error_type,
        "assertions_passed": rc.assertions_passed or 0,
        "assertions_failed": rc.assertions_failed or 0,
        "assertion_details": rc.assertion_details or [],
        # 摘要信息（列表页用）
        "method": req_snap.get('method', ''),
        "request_url": req_snap.get('url', ''),
        "response_status_code": resp_snap.get('status_code', 0),
        "response_time_ms": resp_snap.get('elapsed_ms', rc.duration * 1000 if rc.duration else 0),
    }
    if full:
        result["request_snapshot"] = _sanitize(req_snap)
        result["response_snapshot"] = _sanitize(resp_snap)
    return result


@router.get("/runs", summary="获取TestRun列表")
def get_test_runs(
    project_id: Optional[int] = Query(None, description="项目ID"),
    status: Optional[str] = Query(None, description="状态过滤"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(50, ge=1, le=100, description="限制数量"),
    db: Session = Depends(get_db)
):
    """获取TestRun列表"""
    service = TestRunService(db)
    runs = service.get_test_runs(project_id=project_id, status=status, skip=skip, limit=limit)
    
    return {
        "success": True,
        "data": [
            {
                "id": run.id,
                "trace_id": run.trace_id,
                "project_id": run.project_id,
                "environment_id": run.environment_id,
                "status": run.status,
                "trigger_type": run.trigger_type,
                "start_time": run.start_time.isoformat() if run.start_time else None,
                "end_time": run.end_time.isoformat() if run.end_time else None,
                "duration": run.duration,
                "total_cases": run.total_cases,
                "passed_cases": run.passed_cases,
                "failed_cases": run.failed_cases,
                "skipped_cases": run.skipped_cases,
                "created_at": run.created_at.isoformat() if run.created_at else None,
                "created_by": run.created_by
            }
            for run in runs
        ],
        "pagination": {
            "skip": skip,
            "limit": limit,
            "total": len(runs)
        }
    }


@router.get("/runs/{run_id}", summary="获取TestRun详情")
def get_test_run_detail(
    run_id: str,
    db: Session = Depends(get_db)
):
    """获取TestRun详情(含统计)"""
    service = TestRunService(db)
    run = service.get_test_run(run_id)
    
    if not run:
        raise HTTPException(status_code=404, detail=f"TestRun {run_id} not found")
    
    # 获取RunCase列表
    run_cases = service.get_run_cases(run_id)
    
    return {
        "success": True,
        "data": {
            "id": run.id,
            "trace_id": run.trace_id,
            "project_id": run.project_id,
            "environment_id": run.environment_id,
            "status": run.status,
            "trigger_type": run.trigger_type,
            "start_time": run.start_time.isoformat() if run.start_time else None,
            "end_time": run.end_time.isoformat() if run.end_time else None,
            "duration": run.duration,
            "total_cases": run.total_cases,
            "passed_cases": run.passed_cases,
            "failed_cases": run.failed_cases,
            "skipped_cases": run.skipped_cases,
            "summary": run.summary,
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "created_by": run.created_by,
            "run_cases": [
                _serialize_run_case(rc)
                for rc in run_cases
            ]
        }
    }


@router.get("/runs/{run_id}/cases", summary="获取RunCase列表")
def get_run_cases(
    run_id: str,
    db: Session = Depends(get_db)
):
    """获取指定TestRun的所有RunCase"""
    service = TestRunService(db)
    run_cases = service.get_run_cases(run_id)
    
    return {
        "success": True,
        "data": [
            _serialize_run_case(rc)
            for rc in run_cases
        ]
    }


@router.get("/runs/{run_id}/cases/{case_id}", summary="获取单个RunCase执行详情")
def get_run_case_detail(
    run_id: str,
    case_id: str,
    db: Session = Depends(get_db)
):
    """获取单个用例的完整执行详情（含请求/响应快照和断言详情）"""
    rc = db.query(RunCase).filter(
        RunCase.run_id == run_id,
        RunCase.test_case_id == case_id
    ).first()
    if not rc:
        # 也按run_case.id查找
        rc = db.query(RunCase).filter(
            RunCase.run_id == run_id,
            RunCase.id == int(case_id) if case_id.isdigit() else -1
        ).first()
    if not rc:
        raise HTTPException(status_code=404, detail=f"RunCase not found: run={run_id}, case={case_id}")
    
    return {
        "success": True,
        "data": _serialize_run_case(rc, full=True)
    }


@router.get("/cases/{run_case_id}/steps", summary="获取RunStep列表")
def get_run_steps(
    run_case_id: int,
    db: Session = Depends(get_db)
):
    """获取指定RunCase的所有RunStep"""
    run_steps = db.query(RunStep).filter(
        RunStep.run_case_id == run_case_id
    ).order_by(RunStep.step_order).all()
    
    return {
        "success": True,
        "data": [
            {
                "id": step.id,
                "run_case_id": step.run_case_id,
                "step_name": step.step_name,
                "step_order": step.step_order,
                "status": step.status,
                "start_time": step.start_time.isoformat() if step.start_time else None,
                "end_time": step.end_time.isoformat() if step.end_time else None,
                "duration": step.duration,
                "error_message": step.error_message,
                "error_type": step.error_type
            }
            for step in run_steps
        ]
    }


@router.get("/steps/{run_step_id}/snapshot", summary="获取RunStep快照")
def get_run_step_snapshot(
    run_step_id: int,
    db: Session = Depends(get_db)
):
    """获取RunStep的请求/响应快照"""
    run_step = db.query(RunStep).filter(RunStep.id == run_step_id).first()
    
    if not run_step:
        raise HTTPException(status_code=404, detail=f"RunStep {run_step_id} not found")
    
    return {
        "success": True,
        "data": {
            "id": run_step.id,
            "step_name": run_step.step_name,
            "status": run_step.status,
            "request_snapshot": run_step.input_snapshot,
            "response_snapshot": run_step.output_snapshot,
            "error_message": run_step.error_message,
            "error_type": run_step.error_type
        }
    }


@router.get("/history/{entity_type}/{entity_id}", summary="获取状态历史")
def get_status_history(
    entity_type: str,
    entity_id: str,
    db: Session = Depends(get_db)
):
    """
    获取状态历史
    
    Args:
        entity_type: 实体类型(run/run_case/run_step)
        entity_id: 实体ID
    """
    service = TestRunService(db)
    history = service.get_status_history(entity_type, entity_id)
    
    return {
        "success": True,
        "data": [
            {
                "id": h.id,
                "entity_type": h.entity_type,
                "entity_id": h.entity_id,
                "from_status": h.from_status,
                "to_status": h.to_status,
                "changed_at": h.changed_at.isoformat() if h.changed_at else None,
                "changed_by": h.changed_by,
                "reason": h.reason
            }
            for h in history
        ]
    }


@router.get("/trace/{trace_id}", summary="通过Trace ID查询")
def get_by_trace_id(
    trace_id: str,
    db: Session = Depends(get_db)
):
    """通过Trace ID查询完整执行链路"""
    # 查询TestRun
    test_run = db.query(TestRun).filter(TestRun.trace_id == trace_id).first()
    
    if not test_run:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
    
    # 获取RunCase
    run_cases = db.query(RunCase).filter(RunCase.run_id == test_run.id).all()
    
    # 获取RunStep
    run_case_ids = [rc.id for rc in run_cases]
    run_steps = db.query(RunStep).filter(RunStep.run_case_id.in_(run_case_ids)).all()
    
    # 按run_case_id分组
    steps_by_case = {}
    for step in run_steps:
        if step.run_case_id not in steps_by_case:
            steps_by_case[step.run_case_id] = []
        steps_by_case[step.run_case_id].append(step)
    
    return {
        "success": True,
        "data": {
            "trace_id": trace_id,
            "run": {
                "id": test_run.id,
                "status": test_run.status,
                "duration": test_run.duration,
                "total_cases": test_run.total_cases,
                "passed_cases": test_run.passed_cases,
                "failed_cases": test_run.failed_cases
            },
            "cases": [
                {
                    "id": rc.id,
                    "test_case_id": rc.test_case_id,
                    "status": rc.status,
                    "duration": rc.duration,
                    "error_message": rc.error_message,
                    "steps": [
                        {
                            "id": step.id,
                            "step_name": step.step_name,
                            "status": step.status,
                            "duration": step.duration
                        }
                        for step in sorted(steps_by_case.get(rc.id, []), key=lambda s: s.step_order)
                    ]
                }
                for rc in run_cases
            ]
        }
    }
