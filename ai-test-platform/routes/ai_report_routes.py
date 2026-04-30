"""
Phase 19: AI 报告分析路由

接口:
  POST /api/v2/test-runs/{run_id}/ai-analysis   生成 AI 分析
  GET  /api/v2/test-runs/{run_id}/ai-analysis   查询最近一次分析
  POST /api/v2/reports/{report_id}/ai-analysis   对报告生成 AI 分析
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Body
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from database.models import TestRun, Report
from services.ai_report_analysis_service import AiReportAnalysisService

router = APIRouter(prefix="/api/v2", tags=["AIAnalysis"])


@router.post("/test-runs/{run_id}/ai-analysis")
def generate_ai_analysis(
    run_id: str = Path(..., description="执行记录 ID"),
    force: Optional[bool] = Body(False, embed=True),
    db: Session = Depends(get_db),
):
    """对指定执行记录生成 AI 分析。force=true 强制重新生成（调用 LLM）"""
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail=f"执行记录不存在: {run_id}")

    try:
        svc = AiReportAnalysisService(db)
        result = svc.generate_analysis(run_id, force=bool(force))
        return {"code": 0, "message": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 分析生成失败: {str(e)}")


@router.get("/test-runs/{run_id}/ai-analysis")
def get_ai_analysis(
    run_id: str = Path(..., description="执行记录 ID"),
    db: Session = Depends(get_db),
):
    """查询指定执行记录最近一次 AI 分析结果"""
    svc = AiReportAnalysisService(db)
    result = svc.get_latest_analysis(run_id)
    if not result:
        return {"code": 0, "message": "no analysis found", "data": None}
    return {"code": 0, "message": "success", "data": result}


@router.post("/reports/{report_id}/ai-analysis")
def generate_report_ai_analysis(
    report_id: int = Path(..., description="报告 ID"),
    db: Session = Depends(get_db),
):
    """对指定报告生成 AI 分析"""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail=f"报告不存在: {report_id}")

    run_id = report.run_id
    if not run_id:
        raise HTTPException(status_code=400, detail="报告未关联执行记录")

    try:
        svc = AiReportAnalysisService(db)
        result = svc.generate_analysis(run_id, report_id=report.id)
        return {"code": 0, "message": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 分析生成失败: {str(e)}")
