"""
P2-6B API 性能测试 MVP 路由

POST /api/v2/performance/run
"""
import os
import json
import uuid
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.session import get_db
from database.models import TestCase, TestRun, RunCase, RunStep, Environment
from services.performance_engine import (
    PerformanceConfig, run_performance_test, UNSAFE_METHODS,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/performance", tags=["Performance"])


# ---------- Request / Response Models ----------

class PerformanceRunRequest(BaseModel):
    project_id: int = Field(1, description="项目ID")
    case_ids: List[str] = Field(..., min_items=1, description="API 用例 ID 列表")
    concurrency: int = Field(5, ge=1, le=50, description="并发数")
    duration_seconds: int = Field(30, ge=1, le=300, description="持续时间(秒)")
    ramp_up_seconds: int = Field(0, ge=0, description="Ramp-up 时间(秒)")
    think_time_ms: int = Field(0, ge=0, description="请求间隔(ms)")
    thresholds: Dict[str, float] = Field(default_factory=dict, description="阈值: p95_ms, error_rate, avg_ms")
    allow_unsafe_methods: bool = Field(False, description="是否允许 POST/PUT/DELETE 性能测试")
    environment_id: Optional[int] = Field(None, description="环境ID")
    base_url: Optional[str] = Field(None, description="直接指定 base_url")


class PerformanceRunResponse(BaseModel):
    success: bool
    run_id: str = ""
    status: str = ""
    message: str = ""
    performance_summary: Optional[dict] = None
    error_message: str = ""


# ---------- Route ----------

@router.post("/run", response_model=PerformanceRunResponse)
def run_performance(
    req: PerformanceRunRequest,
    db: Session = Depends(get_db),
):
    """执行 API 性能测试"""

    # 1. Validate ramp_up
    if req.ramp_up_seconds > req.duration_seconds:
        raise HTTPException(status_code=400, detail="ramp_up_seconds 不能大于 duration_seconds")

    # 2. Load and validate cases
    cases = db.query(TestCase).filter(TestCase.id.in_(req.case_ids)).all()
    if not cases:
        raise HTTPException(status_code=404, detail="未找到指定的测试用例")

    found_ids = {tc.id for tc in cases}
    missing = [cid for cid in req.case_ids if cid not in found_ids]
    if missing:
        raise HTTPException(status_code=404, detail=f"未找到用例: {', '.join(missing[:10])}")

    # 3. Filter: only API cases allowed
    non_api = [tc for tc in cases if getattr(tc, 'case_type', None) in ('web_ui',)]
    if non_api:
        raise HTTPException(
            status_code=400,
            detail=f"性能测试仅支持 API 用例。以下用例类型不支持: "
                   f"{', '.join(f'{tc.id}({tc.case_type})' for tc in non_api[:5])}"
        )

    # 4. Real-mode safety
    app_mode = os.getenv("APP_MODE", "mock")
    if app_mode == "real" and not req.allow_unsafe_methods:
        unsafe = []
        for tc in cases:
            cfg = tc.execution_config or {}
            m = (cfg.get("method") or "GET").upper()
            if m in UNSAFE_METHODS:
                unsafe.append({"case_id": tc.id, "title": tc.title, "method": m})
        if unsafe:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "REAL_MODE_PERF_UNSAFE_BLOCKED",
                    "message": f"真实模式下性能测试默认禁止写操作方法。包含 {len(unsafe)} 个危险方法用例",
                    "unsafe_count": len(unsafe),
                    "unsafe_cases": unsafe[:10],
                    "app_mode": app_mode,
                }
            )

    # 5. Determine base_url
    base_url = req.base_url or ""
    env_id = req.environment_id
    if not base_url and env_id:
        env = db.query(Environment).filter(Environment.id == env_id).first()
        if env:
            base_url = env.base_url
    if not base_url:
        envs = db.query(Environment).all()
        if envs:
            base_url = envs[0].base_url
            env_id = envs[0].id
    if not base_url:
        raise HTTPException(status_code=400, detail="未配置测试环境地址")

    # 6. Prepare case data
    case_dicts = []
    for tc in cases:
        case_dicts.append({
            "id": tc.id,
            "title": tc.title,
            "execution_config": tc.execution_config or {},
        })

    config = PerformanceConfig(
        project_id=req.project_id,
        case_ids=req.case_ids,
        concurrency=req.concurrency,
        duration_seconds=req.duration_seconds,
        ramp_up_seconds=req.ramp_up_seconds,
        think_time_ms=req.think_time_ms,
        thresholds=req.thresholds,
        allow_unsafe_methods=req.allow_unsafe_methods,
    )

    validation_errors = config.validate()
    if validation_errors:
        raise HTTPException(status_code=400, detail="; ".join(validation_errors))

    # 7. Execute
    run_id = f"PERF_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
    start_time = datetime.now()

    try:
        summary = run_performance_test(case_dicts, base_url, config)
    except Exception as e:
        logger.error(f"Performance test failed: {e}")
        return PerformanceRunResponse(
            success=False,
            run_id=run_id,
            status="error",
            error_message=f"性能测试执行失败: {str(e)[:500]}",
        )

    end_time = datetime.now()
    perf_dict = summary.to_dict()
    final_status = "passed" if summary.threshold_passed else "failed"

    # 8. Write to DB
    try:
        test_run = TestRun(
            id=run_id,
            project_id=req.project_id,
            environment_id=env_id,
            trigger_type="performance",
            status=final_status,
            trace_id=f"TRACE_{uuid.uuid4().hex}",
            start_time=start_time,
            end_time=end_time,
            duration=summary.duration_seconds,
            total_cases=len(cases),
            passed_cases=len(cases) if final_status == "passed" else 0,
            failed_cases=len(cases) if final_status == "failed" else 0,
            summary=json.dumps({
                "type": "performance",
                "performance_summary": perf_dict,
            }, ensure_ascii=False),
        )
        db.add(test_run)

        # One RunCase per API case with aggregated stats
        for tc in cases:
            case_requests = [r for r in [] ]  # we don't keep per-case breakdown in MVP
            run_case = RunCase(
                run_id=run_id,
                test_case_id=tc.id,
                status=final_status,
                start_time=start_time,
                end_time=end_time,
                duration=summary.duration_seconds,
                request_snapshot={"type": "performance", "concurrency": config.concurrency,
                                  "duration_seconds": config.duration_seconds},
                response_snapshot={"performance_summary": perf_dict},
                assertions_passed=1 if summary.threshold_passed else 0,
                assertions_failed=0 if summary.threshold_passed else 1,
                assertion_details=[{"type": "threshold", "passed": summary.threshold_passed,
                                    "failures": summary.threshold_failures}],
            )
            db.add(run_case)

        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"Performance result DB write failed: {e}")

    return PerformanceRunResponse(
        success=True,
        run_id=run_id,
        status=final_status,
        message=f"性能测试完成: {summary.total_requests} 请求, QPS={round(summary.qps, 1)}, P95={round(summary.p95_ms, 1)}ms",
        performance_summary=perf_dict,
    )
