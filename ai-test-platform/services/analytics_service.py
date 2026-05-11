"""
P3-4A: 质量驾驶舱聚合服务
基于已有 test_runs / run_cases / reports / defects / test_suites 聚合指标
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_
from database.models import TestRun, RunCase, Report, Defect, DefectEvent, TestCase, TestSuite
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
        except Exception as _e:
            logger.debug("silent error suppressed at %s: %s", __name__, _e)
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
        except Exception as _e:
            logger.debug("silent error suppressed at %s: %s", __name__, _e)

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
        except Exception as _e:
            logger.debug("silent error suppressed at %s: %s", __name__, _e)

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
        except Exception as _e:
            logger.debug("silent error suppressed at %s: %s", __name__, _e)

    return {
        "data_validation_errors": total_validation_errors,
        "missing_variables": total_missing_vars,
        "cleanup_failed": total_cleanup_failed,
        "datasets_used": len(datasets_used),
        "data_issue_runs": data_issue_runs,
        "total_runs_analyzed": len(runs),
    }


# ── 8. case-trend ──────────────────────────────────────────
def get_case_trend(db: Session, project_id: int = None, days: int = 14):
    cutoff = _cutoff(days)
    q = db.query(TestRun).filter(TestRun.created_at >= cutoff)
    if project_id:
        q = q.filter(TestRun.project_id == project_id)
    runs = q.order_by(TestRun.created_at).all()

    buckets = {}
    for r in runs:
        day = r.created_at.strftime('%Y-%m-%d') if r.created_at else 'unknown'
        if day not in buckets:
            buckets[day] = {"total": 0, "passed": 0, "failed": 0, "skipped": 0}
        buckets[day]["total"] += (r.total_cases or 0)
        buckets[day]["passed"] += (r.passed_cases or 0)
        buckets[day]["failed"] += (r.failed_cases or 0)
        buckets[day]["skipped"] += (r.skipped_cases or 0)

    return [
        {
            "date": d,
            "total_cases": v["total"],
            "passed_cases": v["passed"],
            "failed_cases": v["failed"],
            "skipped_cases": v["skipped"],
            "case_pass_rate": round(v["passed"] / v["total"], 4) if v["total"] else 0,
        }
        for d, v in sorted(buckets.items())
    ]


# ── 9. defect-trend ─────────────────────────────────────────
def get_defect_trend(db: Session, project_id: int = None, days: int = 14):
    cutoff = _cutoff(days)
    q = db.query(Defect)
    if project_id:
        q = q.filter(Defect.project_id == project_id)
    defects = q.all()

    now = datetime.now()
    buckets = {}
    for i in range(min(days, MAX_DAYS)):
        d = (now - timedelta(days=i)).strftime('%Y-%m-%d')
        buckets[d] = {"new": 0, "closed": 0, "reopened": 0}

    for d in defects:
        if d.created_at and d.created_at >= cutoff:
            day = d.created_at.strftime('%Y-%m-%d')
            if day in buckets:
                buckets[day]["new"] += 1
        if d.closed_at and d.closed_at >= cutoff:
            day = d.closed_at.strftime('%Y-%m-%d')
            if day in buckets:
                buckets[day]["closed"] += 1

    try:
        reopen_events = (
            db.query(DefectEvent)
            .filter(
                DefectEvent.event_type == 'status_change',
                DefectEvent.to_status == 'reopened',
                DefectEvent.created_at >= cutoff,
            ).all()
        )
        for ev in reopen_events:
            day = ev.created_at.strftime('%Y-%m-%d') if ev.created_at else None
            if day and day in buckets:
                buckets[day]["reopened"] += 1
    except Exception as _e:
        logger.debug("silent error suppressed at %s: %s", __name__, _e)

    open_before = sum(1 for d in defects
                      if d.created_at and d.created_at < cutoff
                      and d.status in ('open', 'confirmed', 'reopened'))
    result = []
    running = open_before
    for d in sorted(buckets.keys()):
        v = buckets[d]
        running = running + v["new"] - v["closed"]
        result.append({
            "date": d,
            "new_defects": v["new"],
            "closed_defects": v["closed"],
            "reopened_defects": v["reopened"],
            "open_defects": max(running, 0),
        })
    return result


# ── 10. data-issue-trend ────────────────────────────────────
def get_data_issue_trend(db: Session, project_id: int = None, days: int = 14):
    cutoff = _cutoff(days)
    q = db.query(TestRun).filter(TestRun.created_at >= cutoff)
    if project_id:
        q = q.filter(TestRun.project_id == project_id)
    runs = q.order_by(TestRun.created_at).all()

    buckets = {}
    for r in runs:
        day = r.created_at.strftime('%Y-%m-%d') if r.created_at else 'unknown'
        if day not in buckets:
            buckets[day] = {"ve": 0, "mv": 0, "cf": 0, "issue_runs": 0, "total": 0}
        buckets[day]["total"] += 1
        try:
            s = json.loads(r.summary or '{}')
            ds = s.get('data_summary', {})
            if not ds:
                continue
            ve = ds.get('data_validation_errors', 0)
            mv = ds.get('missing_variables', 0)
            cf = ds.get('cleanup_failed', 0)
            buckets[day]["ve"] += ve
            buckets[day]["mv"] += mv
            buckets[day]["cf"] += cf
            if ve or mv or cf:
                buckets[day]["issue_runs"] += 1
        except Exception as _e:
            logger.debug("silent error suppressed at %s: %s", __name__, _e)

    return [
        {
            "date": d,
            "data_validation_errors": v["ve"],
            "missing_variables": v["mv"],
            "cleanup_failed": v["cf"],
            "data_issue_runs": v["issue_runs"],
            "total_runs": v["total"],
        }
        for d, v in sorted(buckets.items())
    ]


# ── 11. flaky-trend ─────────────────────────────────────────
def get_flaky_trend(db: Session, project_id: int = None, days: int = 14):
    cutoff = _cutoff(days)
    q = db.query(TestRun).filter(TestRun.created_at >= cutoff)
    if project_id:
        q = q.filter(TestRun.project_id == project_id)
    runs = q.order_by(TestRun.created_at).all()
    if not runs:
        return []

    run_day = {r.id: (r.created_at.strftime('%Y-%m-%d') if r.created_at else 'unknown') for r in runs}
    run_ids = list(run_day.keys())
    all_rcs = db.query(RunCase).filter(RunCase.run_id.in_(run_ids)).all()

    day_cases = {}
    for rc in all_rcs:
        d = run_day.get(rc.run_id, 'unknown')
        if d not in day_cases:
            day_cases[d] = {}
        cid = rc.test_case_id
        if cid not in day_cases[d]:
            day_cases[d][cid] = {"p": False, "f": False, "retried": False}
        if rc.status == 'passed':
            day_cases[d][cid]["p"] = True
        if rc.status == 'failed':
            day_cases[d][cid]["f"] = True
        if (rc.retry_count or 0) > 0:
            day_cases[d][cid]["retried"] = True

    return [
        {
            "date": d,
            "flaky_candidate_count": sum(1 for c in cs.values() if c["p"] and c["f"]),
            "retried_cases": sum(1 for c in cs.values() if c["retried"]),
            "recovered_by_retry_count": sum(1 for c in cs.values() if c["retried"] and c["p"]),
        }
        for d, cs in sorted(day_cases.items())
    ]


# ── 12. performance-trend ───────────────────────────────────
def get_performance_trend(db: Session, project_id: int = None, days: int = 14):
    cutoff = _cutoff(days)
    q = db.query(TestRun).filter(TestRun.created_at >= cutoff)
    if project_id:
        q = q.filter(TestRun.project_id == project_id)
    runs = q.order_by(TestRun.created_at).all()
    if not runs:
        return []

    run_day = {r.id: (r.created_at.strftime('%Y-%m-%d') if r.created_at else 'unknown') for r in runs}
    buckets = {}

    for r in runs:
        day = run_day[r.id]
        try:
            s = json.loads(r.summary or '{}')
            ps = s.get('performance_summary', {})
            if ps:
                if day not in buckets:
                    buckets[day] = {"times": [], "errors": 0, "total": 0, "tf": 0}
                if 'avg_response_time_ms' in ps:
                    buckets[day]["times"].append(ps['avg_response_time_ms'])
                buckets[day]["errors"] += ps.get('error_count', 0)
                buckets[day]["total"] += ps.get('total_requests', 0)
                buckets[day]["tf"] += ps.get('threshold_failed_count', 0)
        except Exception as _e:
            logger.debug("silent error suppressed at %s: %s", __name__, _e)

    run_ids = list(run_day.keys())
    perf_ids = [r[0] for r in db.query(TestCase.id).filter(TestCase.case_type == 'performance').all()]
    if perf_ids:
        rcs = db.query(RunCase).filter(
            RunCase.run_id.in_(run_ids), RunCase.test_case_id.in_(perf_ids)
        ).all()
        for rc in rcs:
            day = run_day.get(rc.run_id, 'unknown')
            if day not in buckets:
                buckets[day] = {"times": [], "errors": 0, "total": 0, "tf": 0}
            if rc.duration:
                buckets[day]["times"].append(rc.duration * 1000)
            buckets[day]["total"] += 1
            if rc.status == 'failed':
                buckets[day]["errors"] += 1

    if not buckets:
        return []

    result = []
    for d in sorted(buckets.keys()):
        v = buckets[d]
        t = sorted(v["times"]) if v["times"] else []
        avg_ms = round(sum(t) / len(t), 1) if t else 0
        p95 = round(t[int(len(t) * 0.95)] if len(t) > 1 else (t[0] if t else 0), 1)
        p99 = round(t[int(len(t) * 0.99)] if len(t) > 1 else (t[0] if t else 0), 1)
        er = round(v["errors"] / v["total"], 4) if v["total"] else 0
        result.append({
            "date": d, "avg_response_time_ms": avg_ms,
            "p95_ms": p95, "p99_ms": p99, "error_rate": er,
            "threshold_failed_count": v["tf"], "total_requests": v["total"],
        })
    return result


# ── 13. visual-trend ────────────────────────────────────────
def get_visual_trend(db: Session, project_id: int = None, days: int = 14):
    cutoff = _cutoff(days)
    q = db.query(TestRun).filter(TestRun.created_at >= cutoff)
    if project_id:
        q = q.filter(TestRun.project_id == project_id)
    runs = q.order_by(TestRun.created_at).all()
    if not runs:
        return []

    run_day = {r.id: (r.created_at.strftime('%Y-%m-%d') if r.created_at else 'unknown') for r in runs}
    buckets = {}

    for r in runs:
        day = run_day[r.id]
        try:
            s = json.loads(r.summary or '{}')
            vs = s.get('visual_summary', {})
            if vs:
                if day not in buckets:
                    buckets[day] = {"failed": 0, "baseline": 0, "diffs": []}
                buckets[day]["failed"] += vs.get('visual_failed_count', 0)
                buckets[day]["baseline"] += vs.get('baseline_created_count', 0)
                dr = vs.get('max_diff_ratio', 0)
                if dr:
                    buckets[day]["diffs"].append(dr)
        except Exception as _e:
            logger.debug("silent error suppressed at %s: %s", __name__, _e)

    run_ids = list(run_day.keys())
    vis_ids = [r[0] for r in db.query(TestCase.id).filter(TestCase.case_type == 'visual').all()]
    if vis_ids:
        rcs = db.query(RunCase).filter(
            RunCase.run_id.in_(run_ids), RunCase.test_case_id.in_(vis_ids)
        ).all()
        for rc in rcs:
            day = run_day.get(rc.run_id, 'unknown')
            if day not in buckets:
                buckets[day] = {"failed": 0, "baseline": 0, "diffs": []}
            if rc.status == 'failed':
                buckets[day]["failed"] += 1
            try:
                ad = rc.assertion_details or []
                for a in (ad if isinstance(ad, list) else []):
                    if isinstance(a, dict) and 'diff_ratio' in a:
                        buckets[day]["diffs"].append(a['diff_ratio'])
            except Exception as _e:
                logger.debug("silent error suppressed at %s: %s", __name__, _e)

    if not buckets:
        return []

    return [
        {
            "date": d,
            "visual_failed_count": v["failed"],
            "baseline_created_count": v["baseline"],
            "max_diff_ratio": round(max(v["diffs"]) if v["diffs"] else 0, 4),
        }
        for d, v in sorted(buckets.items())
    ]


# ── 14. module-risk ──────────────────────────────────────────
def get_module_risk(db: Session, project_id: int = None, days: int = 14, module: str = None):
    cutoff = _cutoff(days)
    q_runs = db.query(TestRun).filter(TestRun.created_at >= cutoff)
    if project_id:
        q_runs = q_runs.filter(TestRun.project_id == project_id)
    run_ids = [r.id for r in q_runs.all()]
    if not run_ids:
        return []

    run_cases = db.query(RunCase).filter(RunCase.run_id.in_(run_ids)).all()
    case_ids = list({rc.test_case_id for rc in run_cases})
    if not case_ids:
        return []

    tc_rows = db.query(TestCase.id, TestCase.module).filter(TestCase.id.in_(case_ids)).all()
    mod_map = {r[0]: (r[1] or '未知模块') for r in tc_rows}

    mod_stats = {}
    case_outcomes = {}
    for rc in run_cases:
        m = mod_map.get(rc.test_case_id, '未知模块')
        if module and m != module:
            continue
        if m not in mod_stats:
            mod_stats[m] = {"total": 0, "failed": 0}
        mod_stats[m]["total"] += 1
        if rc.status == 'failed':
            mod_stats[m]["failed"] += 1
        key = (m, rc.test_case_id)
        if key not in case_outcomes:
            case_outcomes[key] = {"p": False, "f": False}
        if rc.status == 'passed':
            case_outcomes[key]["p"] = True
        if rc.status == 'failed':
            case_outcomes[key]["f"] = True

    mod_flaky = {}
    for (m, _), v in case_outcomes.items():
        if v["p"] and v["f"]:
            mod_flaky[m] = mod_flaky.get(m, 0) + 1

    q_def = db.query(Defect).filter(Defect.status.in_(['open', 'confirmed', 'reopened']))
    if project_id:
        q_def = q_def.filter(Defect.project_id == project_id)
    all_open = q_def.all()
    mod_defects = {}
    mod_blockers = {}
    for d in all_open:
        dm = d.module or '未知模块'
        mod_defects[dm] = mod_defects.get(dm, 0) + 1
        if d.severity in ('blocker', 'critical'):
            mod_blockers[dm] = mod_blockers.get(dm, 0) + 1

    results = []
    for m, st in mod_stats.items():
        fr = st["failed"] / st["total"] if st["total"] else 0
        od = mod_defects.get(m, 0)
        bc = mod_blockers.get(m, 0)
        fc = mod_flaky.get(m, 0)

        rfw = min(fr * 1.5, 1.0)
        odw = min(od / 10, 1.0)
        bw = min(bc / 3, 1.0)
        diw = 0
        fw = min(fc / 5, 1.0)

        score = round(fr * 0.30 + rfw * 0.20 + odw * 0.20 + bw * 0.15 + diw * 0.10 + fw * 0.05, 4)
        level = "high" if score >= 0.7 else ("medium" if score >= 0.4 else "low")

        reasons = []
        if fr > 0.15:
            reasons.append(f"最近 {days} 天失败率 {fr*100:.0f}% 较高")
        if bc > 0:
            reasons.append(f"存在 {bc} 个 blocker/critical 缺陷")
        if od > 3:
            reasons.append(f"存在 {od} 个未关闭缺陷")
        if fc > 0:
            reasons.append(f"存在 {fc} 个 Flaky 候选用例")

        results.append({
            "module": m, "risk_score": score, "risk_level": level,
            "failure_rate": round(fr, 4), "recent_failures": st["failed"],
            "open_defects": od, "blocker_defects": bc, "data_issues": 0,
            "flaky_candidates": fc, "risk_reasons": reasons,
        })

    results.sort(key=lambda x: x["risk_score"], reverse=True)
    return results


# ── 15. quality-regression ──────────────────────────────────
def get_quality_regression(db: Session, project_id: int = None, days: int = 7):
    now = datetime.now()
    cur_start = now - timedelta(days=days)
    prev_start = now - timedelta(days=days * 2)

    def _stats(start, end):
        q = db.query(TestRun).filter(TestRun.created_at >= start, TestRun.created_at < end)
        if project_id:
            q = q.filter(TestRun.project_id == project_id)
        runs = q.all()
        tc = sum(r.total_cases or 0 for r in runs)
        pc = sum(r.passed_cases or 0 for r in runs)
        cpr = pc / tc if tc else 0
        ge, gp = 0, 0
        vis_f, di = 0, 0
        p95_vals = []
        for r in runs:
            try:
                s = json.loads(r.summary or '{}')
                if 'gate_status' in s:
                    ge += 1
                    if s['gate_status'] == 'passed':
                        gp += 1
                ps = s.get('performance_summary', {})
                if ps and 'p95_ms' in ps:
                    p95_vals.append(ps['p95_ms'])
                vs = s.get('visual_summary', {})
                if vs:
                    vis_f += vs.get('visual_failed_count', 0)
                ds = s.get('data_summary', {})
                if ds:
                    di += ds.get('data_validation_errors', 0) + ds.get('missing_variables', 0)
            except Exception as _e:
                logger.debug("silent error suppressed at %s: %s", __name__, _e)
        gpr = gp / ge if ge else 0
        dq = db.query(Defect).filter(Defect.created_at >= start, Defect.created_at < end)
        if project_id:
            dq = dq.filter(Defect.project_id == project_id)
        nd = dq.count()
        return {
            "case_pass_rate": cpr, "gate_pass_rate": gpr, "new_defects": nd,
            "p95_ms": (sum(p95_vals) / len(p95_vals)) if p95_vals else 0,
            "visual_failed": vis_f, "data_issues": di,
        }

    cur = _stats(cur_start, now)
    prev = _stats(prev_start, cur_start)

    defs = [
        ("case_pass_rate", "用例通过率", True),
        ("gate_pass_rate", "门禁通过率", True),
        ("new_defects", "新增缺陷", False),
        ("p95_ms", "性能 P95", False),
        ("visual_failed", "视觉失败", False),
        ("data_issues", "数据问题", False),
    ]

    result = []
    for key, label, hib in defs:
        cv, pv = cur[key], prev[key]
        delta = round(cv - pv, 4)
        if hib:
            degraded = delta < -0.02
            sev = "high" if delta < -0.1 else ("medium" if delta < -0.05 else "low") if degraded else "none"
        else:
            degraded = delta > max(pv * 0.1, 0.01) if pv else delta > 0
            sev = ("high" if (pv and delta > pv * 0.5) else ("medium" if (pv and delta > pv * 0.2) else "low")) if degraded else "none"
        result.append({
            "metric": key, "label": label,
            "current_value": round(cv, 4), "previous_value": round(pv, 4),
            "delta": delta, "degraded": degraded, "severity": sev,
        })
    return result
