"""
Phase 20: Dashboard 汇总路由

GET /api/v2/dashboard/summary  平台首页汇总数据
"""

import json
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import func

from fastapi import APIRouter, Depends

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.session import get_db
from database.models import (
    Project, Environment, TestCase, TestRun, RunCase, AiReportAnalysis,
)

router = APIRouter(prefix="/api/v2/dashboard", tags=["Dashboard"])


@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    """平台首页汇总数据"""
    try:
        data = _build_summary(db)
        return {"code": 0, "message": "success", "data": data}
    except Exception as e:
        return {"code": 0, "message": "success", "data": _empty_summary(str(e))}


def _build_summary(db: Session) -> dict:
    # ── 基础统计 ──
    project_count = db.query(func.count(Project.id)).scalar() or 0
    environment_count = db.query(func.count(Environment.id)).scalar() or 0
    test_case_count = db.query(func.count(TestCase.id)).scalar() or 0
    test_run_count = db.query(func.count(TestRun.id)).scalar() or 0

    # ── 最近一次执行 ──
    latest_run_obj = db.query(TestRun).order_by(TestRun.created_at.desc()).first()
    latest_run = None
    if latest_run_obj:
        proj = db.query(Project).filter(Project.id == latest_run_obj.project_id).first()
        env = db.query(Environment).filter(Environment.id == latest_run_obj.environment_id).first()
        summary_data = json.loads(latest_run_obj.summary or '{}')

        total = latest_run_obj.total_cases or 0
        passed = latest_run_obj.passed_cases or 0
        failed = latest_run_obj.failed_cases or 0
        skipped = latest_run_obj.skipped_cases or 0
        executed = total - skipped
        pass_rate = round(passed / max(executed, 1) * 100, 1)

        latest_run = {
            "run_id": latest_run_obj.id,
            "project_name": proj.name if proj else "",
            "environment_name": env.name if env else "",
            "preset": summary_data.get("preset", ""),
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "pass_rate": pass_rate,
            "created_at": latest_run_obj.created_at.strftime("%Y-%m-%d %H:%M:%S") if latest_run_obj.created_at else "",
        }

    # ── 最近一次 AI 分析 ──
    latest_ai = db.query(AiReportAnalysis).order_by(AiReportAnalysis.created_at.desc()).first()
    latest_ai_analysis = None
    if latest_ai:
        latest_ai_analysis = {
            "health_score": latest_ai.health_score,
            "release_recommendation": latest_ai.release_recommendation,
            "summary": latest_ai.summary or "",
            "provider": latest_ai.provider or "rule_based",
            "run_id": latest_ai.run_id,
        }

    # ── failure_categories (最近一次执行) ──
    failure_categories = {}
    if latest_run_obj:
        fc_rows = (
            db.query(RunCase.status, func.count(RunCase.id))
            .filter(RunCase.run_id == latest_run_obj.id, RunCase.status == 'failed')
            .all()
        )
        # 从 run_cases 聚合 failure_category (存在 test_case 上)
        fc_cases = (
            db.query(RunCase)
            .filter(RunCase.run_id == latest_run_obj.id, RunCase.status == 'failed')
            .all()
        )
        for rc in fc_cases:
            tc = db.query(TestCase).filter(TestCase.id == rc.test_case_id).first()
            fc = (tc.failure_category if tc else None) or 'unknown_error'
            failure_categories[fc] = failure_categories.get(fc, 0) + 1

    # ── risk_distribution ──
    risk_distribution = {"P0": 0, "P1": 0, "P2": 0}
    risk_rows = (
        db.query(TestCase.risk_level, func.count(TestCase.id))
        .filter(TestCase.risk_level.isnot(None))
        .group_by(TestCase.risk_level)
        .all()
    )
    for level, cnt in risk_rows:
        if level in risk_distribution:
            risk_distribution[level] = cnt

    # ── status_distribution ──
    status_distribution = {"passed": 0, "failed": 0, "pending": 0, "skipped": 0}
    status_rows = (
        db.query(TestCase.last_run_status, func.count(TestCase.id))
        .group_by(TestCase.last_run_status)
        .all()
    )
    for st, cnt in status_rows:
        key = st if st in status_distribution else "pending"
        status_distribution[key] += cnt

    # ── destructive_summary ──
    destructive_total = db.query(func.count(TestCase.id)).filter(TestCase.destructive == True).scalar() or 0
    destructive_skipped_latest = 0
    if latest_run_obj:
        destructive_skipped_latest = (
            db.query(func.count(RunCase.id))
            .filter(RunCase.run_id == latest_run_obj.id, RunCase.status == 'skipped')
            .join(TestCase, TestCase.id == RunCase.test_case_id)
            .filter(TestCase.destructive == True)
            .scalar() or 0
        )

    # ── recent_runs ──
    recent_runs_objs = db.query(TestRun).order_by(TestRun.created_at.desc()).limit(5).all()
    recent_runs = []
    for r in recent_runs_objs:
        t = r.total_cases or 0
        p = r.passed_cases or 0
        f = r.failed_cases or 0
        s = r.skipped_cases or 0
        ex = t - s
        pr = round(p / max(ex, 1) * 100, 1)
        sm = json.loads(r.summary or '{}')
        recent_runs.append({
            "run_id": r.id,
            "preset": sm.get("preset", ""),
            "total": t,
            "passed": p,
            "failed": f,
            "skipped": s,
            "pass_rate": pr,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else "",
        })

    return {
        "project_count": project_count,
        "environment_count": environment_count,
        "test_case_count": test_case_count,
        "test_run_count": test_run_count,
        "latest_run": latest_run,
        "latest_ai_analysis": latest_ai_analysis,
        "failure_categories": failure_categories,
        "risk_distribution": risk_distribution,
        "status_distribution": status_distribution,
        "destructive_summary": {
            "total": destructive_total,
            "skipped_latest": destructive_skipped_latest,
        },
        "recent_runs": recent_runs,
    }


def _empty_summary(error: str = "") -> dict:
    return {
        "project_count": 0,
        "environment_count": 0,
        "test_case_count": 0,
        "test_run_count": 0,
        "latest_run": None,
        "latest_ai_analysis": None,
        "failure_categories": {},
        "risk_distribution": {"P0": 0, "P1": 0, "P2": 0},
        "status_distribution": {"passed": 0, "failed": 0, "pending": 0, "skipped": 0},
        "destructive_summary": {"total": 0, "skipped_latest": 0},
        "recent_runs": [],
        "_error": error,
    }
