# -*- coding: utf-8 -*-
"""
P3-1: 质量门禁 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from database import get_db
from services.quality_gate_service import QualityGateService, DEFAULT_GATE_CONFIG

router = APIRouter(prefix="/api/v2/quality-gates", tags=["质量门禁"])


class GateEvaluateRequest(BaseModel):
    run_id: str
    gate_config: Optional[dict] = None


class GateSummaryEvaluateRequest(BaseModel):
    suite_summary: dict
    gate_config: Optional[dict] = None


@router.post("/evaluate")
def evaluate_quality_gate(req: GateEvaluateRequest, db: Session = Depends(get_db)):
    """
    评估质量门禁。
    传入 run_id 和可选的 gate_config，返回 gate_status + gate_failures。
    """
    svc = QualityGateService(db)
    result = svc.evaluate(req.run_id, req.gate_config)
    if result.get("gate_status") == "error":
        raise HTTPException(status_code=404, detail=result.get("message", "评估失败"))
    return result


@router.post("/evaluate-summary")
def evaluate_quality_gate_from_summary(req: GateSummaryEvaluateRequest):
    """
    P3-3A: 直接传入 suite_summary 评估质量门禁 (不需要 run_id)。
    用于 CLI、测试脚本和前端预览。
    """
    svc = QualityGateService()
    result = svc.evaluate_from_summary(req.suite_summary, gate_config=req.gate_config)
    return result


@router.get("/default-config")
def get_default_config():
    """返回默认质量门禁配置。"""
    return DEFAULT_GATE_CONFIG
