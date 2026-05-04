"""
P3-4A: 质量驾驶舱聚合服务
基于已有 test_runs / run_cases / reports / defects / test_suites 聚合指标
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_
from database.models import TestRun, RunCase, Report, Defect, TestCase, TestSuite
import json
import logging

logger = logging.getLogger(__name__)

MAX_DAYS = 90


def _cutoff(days: int) -> datetime:
    return datetime.now() - timedelta(days=min(days, MAX_DAYS))


# ── 1. overview ──────────────────────────────────────────
def get_overview(db: Session, project_id: int = None, days: int = 7):
    cutoff = _cutoff(days)

    # --- runs ---
    q_runs = db.query(TestRun).filter(TestRun.created_at >= cutoff)
    if project_id:
        q_runs = q_runs.filter(TestRun.project_id == project_id)
    runs = q_runs.all()

    total_runs = len(runs)
    passed_runs = sum(1 for r in runs if r.status == 'passed')
    failed_runs = sum(1 for r in runs if r.status == 'failed')
    run_pass_rate = round(passed_runs / total_runs, 4) if total_runs else 0

    # --- cases ---
    run_ids = [r.id for r in runs]
    total_cases = 0
    passed_cases = 0
    if run_ids:
        q_cases = db.query(RunCase).filter(RunCase.run_id.in_(run_ids))
        all_cases = q_cases.all()
        total_cases = len(all_cases)
        passed_cases = sum(1 for c in all_cases if c.status == 'passed')
    case_pass_rate = round(passed_cases / total_cases, 4) if total_cases else 0

    # --- gate (从 runs summary 中解析) ---
    gate_evaluated = 0
    gate_passed_count = 0
    for r in runs:
        try:
            s = json.loads(r.summary or '{}')
            if 'gate_status' in s:
                gate_evaluated += 1
                if s['gate_status'] == 'passed':
                    gate_passed_count += 1
        except Exception:
            pass
    gate_pass_rate = round(gate_passed_count / gate_evaluated, 4) if gate_evaluated else 0

    # --- defects ---
    q_defects = db.query(Defect)
    if project_id:
        q_defects = q_defects.filter(Defect.project_id == project_id)
    all_defects = q_defects.all()
    open_defects = sum(1 for d in all_defects if d.status in ('open', 'confirmed', 'reopened'))
    blocker_defects = sum(1 for d in all_defects if d.severity == 'blocker' and d.status not in ('closed', 'rejected', 'verified'))
    known_issues = sum(1 for d in all_defects if d.status in ('confirmed', 'fixed'))

    # --- data issues (从 runs summary 中) ---
    data_issue_count = 0
    for r in runs:
        try:
            s = json.loads(r.summary or '{}')
            ds = s.get('data_summary', {})
            data_issue_count += ds.get('missing_variables', 0) + ds.get('data_validation_errors', 0)
        except Exception:
            pass

    # --- flaky candidates (run_cases failed then passed in same period) ---
    flaky_candidate_count = 0
    if run_ids:
        try:
            flaky_q = (
                db.query(RunCase.test_case_id)
                .filter(RunCase.run_id.in_(run_ids))
                .group_by(RunCase.test_case_id)
                .having(
                    and_(
                        func.sum(case((RunCase.status == 'passed', 1), else_=0)) > 0,
                        func.sum(case((RunCase.status == 'failed', 1), else_=0)) > 0,
                    )
                )
            )
            flaky_candidate_count = flaky_q.count()
        except Exception:
            pass

    # --- risk_level ---
    risk_level = "low"
    risk_reasons = []
    if blocker_defects > 0:
        risk_level = "high"
        risk_reasons.append(f"存在 {blocker_defects} 个未关闭 blocker 缺陷")
    if gate_pass_rate < 0.8 and gate_evaluated > 0:
        risk_level = "high"
        risk_reasons.append(f"门禁通过率 {gate_pass_rate*100:.0f}% < 80%")
    if case_pass_rate < 0.85 and total_cases > 0:
        risk_level = "high"
        risk_reasons.append(f"用例通过率 {case_pass_rate*100:.0f}% < 85%")
    if risk_level != "high":
        if data_issue_count > 10:
            risk_level = "medium"
            risk_reasons.append(f"数据问题 {data_issue_count} > 10")
        if open_defects > 20:
            risk_level = "medium"
            risk_reasons.append(f"未关闭缺陷 {open_defects} > 20")

    return {
        "total_runs": total_runs,
        "passed_runs": passed_runs,
        "failed_runs": failed_runs,
        "run_pass_rate": run_pass_rate,
        "total_cases_executed": total_cases,
        "case_pass_rate": case_pass_rate,
        "gate_evaluated": gate_evaluated,
        "gate_pass_rate": gate_pass_rate,
        "open_defects": open_defects,
        "blocker_defects": blocker_defects,
        "known_issues": known_issues,
        "data_issue_count": data_issue_count,
        "flaky_candidate_count": flaky_candidate_count,
        "risk_level": risk_level,
        "risk_reasons": risk_reasons,
        "days": days,
    }


# ── 2. test-suite-trend ─────────────────────────────────
def get_test_suite_trend(db: Session, project_id: int = None, days: int = 7, suite_type: str = None):
    cutoff = _cutoff(days)
    q = db.query(TestRun).filter(TestRun.created_at >= cutoff)
    if project_id:
        q = q.filter(TestRun.project_id == project_id)
    if suite_type:
        q = q.filter(TestRun.trigger_type == suite_type)
    runs = q.order_by(TestRun.created_at).all()

    buckets = {}
    for r in runs:
        day = r.created_at.strftime('%Y-%m-%d') if r.created_at else 'unknown'
        if day not in buckets:
            buckets[day] = {"total": 0, "passed": 0, "failed": 0}
        buckets[day]["total"] += 1
        if r.status == 'passed':
            buckets[day]["passed"] += 1
        elif r.status == 'failed':
            buckets[day]["failed"] += 1

    return [
        {
            "date": d,
            "total_suite_runs": v["total"],
            "passed_suite_runs": v["passed"],
            "failed_suite_runs": v["failed"],
            "pass_rate": round(v["passed"] / v["total"], 4) if v["total"] else 0,
        }
        for d, v in sorted(buckets.items())
    ]


# ── 3. gate-trend ────────────────────────────────────────
def get_gate_trend(db: Session, project_id: int = None, days: int = 7):
    cutoff = _cutoff(days)
    q = db.query(TestRun).filter(TestRun.created_at >= cutoff)
    if project_id:
        q = q.filter(TestRun.project_id == project_id)
    runs = q.order_by(TestRun.created_at).all()

    buckets = {}
    for r in runs:
        try:
            s = json.loads(r.summary or '{}')
            gs = s.get('gate_status')
            if not gs:
                continue
        except Exception:
            continue
        day = r.created_at.strftime('%Y-%m-%d') if r.created_at else 'unknown'
        if day not in buckets:
            buckets[day] = {"passed": 0, "failed": 0}
        if gs == 'passed':
            buckets[day]["passed"] += 1
        else:
            buckets[day]["failed"] += 1

    return [
        {
            "date": d,
            "gate_passed": v["passed"],
            "gate_failed": v["failed"],
            "gate_pass_rate": round(v["passed"] / (v["passed"] + v["failed"]), 4) if (v["passed"] + v["failed"]) else 0,
        }
        for d, v in sorted(buckets.items())
    ]


# ── 4. failure-modules ──────────────────────────────────
def get_failure_modules(db: Session, project_id: int = None, days: int = 7, top: int = 5):
    cutoff = _cutoff(days)
    q = db.query(TestRun).filter(TestRun.created_at >= cutoff)
    if project_id:
        q = q.filter(TestRun.project_id == project_id)
    run_ids = [r.id for r in q.all()]
    if not run_ids:
        return []

    cases = (
        db.query(RunCase)
        .filter(RunCase.run_id.in_(run_ids))
        .all()
    )

    # 先建 case_id -> module 映射
    case_ids = list({c.test_case_id for c in cases})
    module_map = {}
    if case_ids:
        tc_rows = db.query(TestCase.id, TestCase.module).filter(TestCase.id.in_(case_ids)).all()
        module_map = {r[0]: (r[1] or '未知模块') for r in tc_rows}

    module_stats = {}
    for c in cases:
        m = module_map.get(c.test_case_id, '未知模块')
        if m not in module_stats:
            module_stats[m] = {"total": 0, "failed": 0}
        module_stats[m]["total"] += 1
        if c.status == 'failed':
            module_stats[m]["failed"] += 1

    result = [
        {
            "module": m,
            "failed_count": v["failed"],
            "total_count": v["total"],
            "failure_rate": round(v["failed"] / v["total"], 4) if v["total"] else 0,
        }
        for m, v in module_stats.items() if v["failed"] > 0
    ]
    result.sort(key=lambda x: x["failed_count"], reverse=True)
    return result[:top]


# ── 5. failure-categories ───────────────────────────────
def get_failure_categories(db: Session, project_id: int = None, days: int = 7):
    cutoff = _cutoff(days)
    q = db.query(TestRun).filter(TestRun.created_at >= cutoff)
    if project_id:
        q = q.filter(TestRun.project_id == project_id)
    run_ids = [r.id for r in q.all()]
    if not run_ids:
        return []

    failed_cases = (
        db.query(RunCase)
        .filter(RunCase.run_id.in_(run_ids), RunCase.status == 'failed')
        .all()
    )
    if not failed_cases:
        return []

    # 获取 test_case failure_category
    case_ids = list({c.test_case_id for c in failed_cases})
    cat_map = {}
    if case_ids:
        tc_rows = db.query(TestCase.id, TestCase.failure_category).filter(TestCase.id.in_(case_ids)).all()
        cat_map = {r[0]: r[1] for r in tc_rows}

    cats = {}
    for c in failed_cases:
        cat = cat_map.get(c.test_case_id) or _classify_error(c.error_message or '') or 'unknown'
        cats[cat] = cats.get(cat, 0) + 1

    total = sum(cats.values())
    return [
        {
            "category": k,
            "count": v,
            "percentage": round(v / total, 4) if total else 0,
        }
        for k, v in sorted(cats.items(), key=lambda x: x[1], reverse=True)
    ]


def _classify_error(msg: str) -> str:
    msg_lower = msg.lower()
    if 'timeout' in msg_lower:
        return 'timeout_error'
    if 'connection' in msg_lower or 'network' in msg_lower:
        return 'network_error'
    if '401' in msg or '403' in msg or 'auth' in msg_lower:
        return 'auth_error'
    if 'assert' in msg_lower:
        return 'assertion_error'
    if '500' in msg or '502' in msg or '503' in msg:
        return 'server_error'
    return ''


# ── 6. defect-summary ───────────────────────────────────
def get_defect_summary(db: Session, project_id: int = None, days: int = None):
    q = db.query(Defect)
    if project_id:
        q = q.filter(Defect.project_id == project_id)
    if days:
        q = q.filter(Defect.created_at >= _cutoff(days))
    defects = q.all()

    status_counts = {}
    severity_counts = {}
    for d in defects:
        status_counts[d.status] = status_counts.get(d.status, 0) + 1
        severity_counts[d.severity] = severity_counts.get(d.severity, 0) + 1

    return {
        "total_defects": len(defects),
        "open_defects": status_counts.get('open', 0),
        "confirmed_defects": status_counts.get('confirmed', 0),
        "fixed_defects": status_counts.get('fixed', 0),
        "verified_defects": status_counts.get('verified', 0),
        "closed_defects": status_counts.get('closed', 0),
        "rejected_defects": status_counts.get('rejected', 0),
        "reopened_defects": status_counts.get('reopened', 0),
        "blocker_defects": severity_counts.get('blocker', 0),
        "critical_defects": severity_counts.get('critical', 0),
        "major_defects": severity_counts.get('major', 0),
        "minor_defects": severity_counts.get('minor', 0),
        "trivial_defects": severity_counts.get('trivial', 0),
        "known_issues": status_counts.get('confirmed', 0) + status_counts.get('fixed', 0),
        "status_distribution": status_counts,
        "severity_distribution": severity_counts,
    }


# ── 7. data-issues ──────────────────────────────────────
def get_data_issues(db: Session, project_id: int = None, days: int = 7):
    cutoff = _cutoff(days)
    q = db.query(TestRun).filter(TestRun.created_at >= cutoff)
    if project_id:
        q = q.filter(TestRun.project_id == project_id)
    runs = q.all()

    total_validation_errors = 0
    total_missing_vars = 0
    total_cleanup_failed = 0
    datasets_used = set()
    data_issue_runs = 0

    for r in runs:
        try:
            s = json.loads(r.summary or '{}')
            ds = s.get('data_summary', {})
            if not ds:
                continue
            ve = ds.get('data_validation_errors', 0)
            mv = ds.get('missing_variables', 0)
            cf = ds.get('cleanup_failed', 0)
            total_validation_errors += ve
            total_missing_vars += mv
            total_cleanup_failed += cf
            if ve or mv or cf:
                data_issue_runs += 1
            for did in ds.get('dataset_ids', []):
                datasets_used.add(str(did))
        except Exception:
            pass

    return {
        "data_validation_errors": total_validation_errors,
        "missing_variables": total_missing_vars,
        "cleanup_failed": total_cleanup_failed,
        "datasets_used": len(datasets_used),
        "data_issue_runs": data_issue_runs,
        "total_runs_analyzed": len(runs),
    }
