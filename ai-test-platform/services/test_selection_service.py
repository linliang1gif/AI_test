"""
P3-5: 智能选测与风险推荐服务
基于历史执行数据、模块风险、缺陷、Flaky、性能/视觉退化，
生成 suite / case / module 推荐及 skip_candidate。
不依赖 AI Provider，纯规则引擎。
"""
import json
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from database.models import (
    TestCase, TestRun, RunCase, TestSuite, TestSuiteCase, Defect,
)


# ── helpers ──────────────────────────────────────────────────

def _cutoff(days: int):
    return datetime.now() - timedelta(days=days)


def _safe_json(val, default=None):
    if default is None:
        default = {}
    if isinstance(val, dict):
        return val
    if isinstance(val, str):
        try:
            return json.loads(val)
        except Exception:
            return default
    return default


# ── 1. case risk scoring ─────────────────────────────────────

def _build_case_risk_map(db: Session, project_id=None, days=14):
    """
    为每个用例计算 case_risk_score (0~1) 和风险理由。
    公式:
      history_failure_rate * 0.25
      + recent_failure_weight * 0.20
      + priority_weight * 0.15
      + module_risk * 0.15
      + defect_weight * 0.10
      + flaky_weight * 0.05
      + data_issue_weight * 0.05
      + gate_failure_weight * 0.05
    """
    cutoff = _cutoff(days)

    # ── runs & run_cases (limit to 50 most recent for perf) ──
    q_runs = db.query(TestRun).filter(TestRun.created_at >= cutoff)
    if project_id:
        q_runs = q_runs.filter(TestRun.project_id == project_id)
    runs = q_runs.order_by(TestRun.created_at.desc()).limit(50).all()
    if not runs:
        return {}

    run_ids = [r.id for r in runs]
    run_map = {r.id: r for r in runs}

    # batch query run_cases (SQLite max vars ~999)
    BATCH = 500
    run_cases = []
    for i in range(0, len(run_ids), BATCH):
        chunk = run_ids[i:i + BATCH]
        run_cases.extend(db.query(RunCase).filter(RunCase.run_id.in_(chunk)).all())
    if not run_cases:
        return {}

    # ── case stats: total, failed, passed, recent pass streak ──
    case_stats = {}
    # sort by run created_at for streak
    rc_sorted = sorted(run_cases, key=lambda rc: (rc.test_case_id, run_map.get(rc.run_id, runs[0]).created_at))
    for rc in rc_sorted:
        cid = rc.test_case_id
        if cid not in case_stats:
            case_stats[cid] = {
                "total": 0, "failed": 0, "passed": 0,
                "pass_streak": 0, "has_both": False,
                "run_statuses": [], "retried": False,
            }
        cs = case_stats[cid]
        cs["total"] += 1
        if rc.status == 'failed':
            cs["failed"] += 1
            cs["pass_streak"] = 0
        elif rc.status == 'passed':
            cs["passed"] += 1
            cs["pass_streak"] += 1
        cs["run_statuses"].append(rc.status)
        if rc.retry_count and rc.retry_count > 0:
            cs["retried"] = True

    # flaky: both passed and failed in period
    for cid, cs in case_stats.items():
        if cs["passed"] > 0 and cs["failed"] > 0:
            cs["has_both"] = True

    # ── load test_cases (batched) ──
    all_case_ids = list(case_stats.keys())
    tc_rows = []
    for i in range(0, len(all_case_ids), BATCH):
        chunk = all_case_ids[i:i + BATCH]
        tc_rows.extend(db.query(TestCase).filter(TestCase.id.in_(chunk)).all())
    tc_map = {tc.id: tc for tc in tc_rows}

    # ── module risk (reuse logic inline) ──
    mod_stats = {}
    for rc in run_cases:
        tc = tc_map.get(rc.test_case_id)
        m = (tc.module or '未知模块') if tc else '未知模块'
        if m not in mod_stats:
            mod_stats[m] = {"total": 0, "failed": 0}
        mod_stats[m]["total"] += 1
        if rc.status == 'failed':
            mod_stats[m]["failed"] += 1
    mod_risk = {}
    for m, st in mod_stats.items():
        mod_risk[m] = st["failed"] / st["total"] if st["total"] else 0

    # ── open defects per case ──
    q_def = db.query(Defect).filter(Defect.status.in_(['open', 'confirmed', 'reopened']))
    if project_id:
        q_def = q_def.filter(Defect.project_id == project_id)
    open_defects = q_def.all()
    case_defects = {}
    case_blocker = {}
    for d in open_defects:
        cid = d.case_id
        if cid:
            case_defects[cid] = case_defects.get(cid, 0) + 1
            if d.severity in ('blocker', 'critical'):
                case_blocker[cid] = case_blocker.get(cid, 0) + 1

    # ── gate failure runs ──
    gate_failed_runs = set()
    for r in runs:
        try:
            s = _safe_json(r.summary)
            if s.get('gate_status') == 'failed':
                gate_failed_runs.add(r.id)
        except Exception as _e:
            logger.debug("silent error suppressed at %s: %s", __name__, _e)
    case_gate_fail = set()
    for rc in run_cases:
        if rc.run_id in gate_failed_runs and rc.status == 'failed':
            case_gate_fail.add(rc.test_case_id)

    # ── data issue runs ──
    data_issue_runs = set()
    for r in runs:
        try:
            s = _safe_json(r.summary)
            ds = s.get('data_summary', {})
            if ds and (ds.get('data_validation_errors', 0) > 0 or ds.get('missing_variables', 0) > 0):
                data_issue_runs.add(r.id)
        except Exception as _e:
            logger.debug("silent error suppressed at %s: %s", __name__, _e)

    # ── pre-compute case_in_data_issue_run set ──
    case_in_data_issue_run = set()
    if data_issue_runs:
        for rc in run_cases:
            if rc.run_id in data_issue_runs:
                case_in_data_issue_run.add(rc.test_case_id)

    # ── compute scores ──
    result = {}
    priority_weight_map = {'critical': 1.0, 'high': 0.8, 'medium': 0.5, 'low': 0.2}
    risk_level_map = {'P0': 1.0, 'P1': 0.7, 'P2': 0.4}

    for cid, cs in case_stats.items():
        tc = tc_map.get(cid)
        if not tc:
            continue

        # history failure rate
        fr = cs["failed"] / cs["total"] if cs["total"] else 0

        # recent failure weight (amplified)
        rfw = min(fr * 1.5, 1.0)

        # priority weight
        pw = priority_weight_map.get(tc.priority, 0.5)
        # also consider risk_level
        rl_w = risk_level_map.get(tc.risk_level, 0.3)
        combined_pw = max(pw, rl_w)

        # module risk
        m = tc.module or '未知模块'
        mr = mod_risk.get(m, 0)

        # defect weight
        dc = case_defects.get(cid, 0)
        dw = min(dc / 5, 1.0)

        # flaky weight
        fw = 0.8 if cs["has_both"] else 0

        # data issue weight
        diw = 0.5 if cid in case_in_data_issue_run else 0

        # gate failure weight
        gfw = 0.8 if cid in case_gate_fail else 0

        score = round(
            fr * 0.25
            + rfw * 0.20
            + combined_pw * 0.15
            + mr * 0.15
            + dw * 0.10
            + fw * 0.05
            + diw * 0.05
            + gfw * 0.05,
            4
        )
        score = min(score, 1.0)

        level = "high" if score >= 0.75 else ("medium" if score >= 0.45 else "low")

        reasons = []
        if fr > 0.3:
            reasons.append(f"历史失败率 {fr*100:.0f}%")
        elif fr > 0:
            reasons.append(f"近 {days} 天有失败记录")
        if tc.priority in ('critical',):
            reasons.append("P0/critical 优先级")
        elif tc.priority == 'high':
            reasons.append("high 优先级")
        if mr > 0.2:
            reasons.append(f"所属模块 {m} 风险较高 ({mr*100:.0f}%)")
        if dc > 0:
            reasons.append(f"关联 {dc} 个未关闭缺陷")
        bc = case_blocker.get(cid, 0)
        if bc > 0:
            reasons.append(f"关联 {bc} 个 blocker/critical 缺陷")
        if cs["has_both"]:
            reasons.append("Flaky 候选 (同周期内既通过又失败)")
        if cid in case_gate_fail:
            reasons.append("最近质量门禁失败")
        if diw > 0:
            reasons.append("存在数据问题影响")

        result[cid] = {
            "case_id": cid,
            "title": tc.title,
            "module": m,
            "case_type": tc.case_type or 'api',
            "priority": tc.priority,
            "risk_score": score,
            "risk_level": level,
            "failure_rate": round(fr, 4),
            "pass_streak": cs["pass_streak"],
            "total_runs": cs["total"],
            "failed_runs": cs["failed"],
            "is_flaky": cs["has_both"],
            "open_defects": dc,
            "blocker_defects": bc,
            "reasons": reasons,
            "last_status": cs["run_statuses"][-1] if cs["run_statuses"] else "unknown",
        }

    return result


# ── 2. recommendation level ──────────────────────────────────

def _case_recommendation_level(info: dict) -> str:
    """
    must_run / should_run / optional / skip_candidate
    """
    score = info["risk_score"]
    priority = info.get("priority", "medium")
    pass_streak = info.get("pass_streak", 0)
    risk_level = info.get("risk_level", "low")
    open_defects = info.get("open_defects", 0)
    blocker = info.get("blocker_defects", 0)
    failure_rate = info.get("failure_rate", 0)

    # must_run conditions
    if priority in ('critical',) or info.get("priority") == 'critical':
        return "must_run"
    if blocker > 0:
        return "must_run"
    if score >= 0.75:
        return "must_run"
    if failure_rate > 0.5:
        return "must_run"

    # skip_candidate conditions
    if (pass_streak >= 5 and risk_level == "low" and open_defects == 0
            and priority not in ('critical', 'high') and not info.get("is_flaky", False)):
        return "skip_candidate"

    if score >= 0.45:
        return "should_run"

    if score >= 0.2:
        return "optional"

    # low risk, no failures, but not long enough streak
    return "optional"


# ── 3. suite recommendation ──────────────────────────────────

def _build_suite_recommendations(db: Session, case_risk_map: dict,
                                  project_id=None, days=14, suite_type=None):
    q = db.query(TestSuite).filter(TestSuite.status == 'active')
    if project_id:
        q = q.filter(TestSuite.project_id == project_id)
    if suite_type:
        q = q.filter(TestSuite.suite_type == suite_type)
    suites = q.all()

    if not suites:
        return []

    suite_ids = [s.id for s in suites]
    sc_rows = db.query(TestSuiteCase).filter(
        TestSuiteCase.suite_id.in_(suite_ids),
        TestSuiteCase.enabled == True
    ).all()

    suite_cases_map = {}
    for sc in sc_rows:
        suite_cases_map.setdefault(sc.suite_id, []).append(sc.case_id)

    # historical suite run status
    cutoff = _cutoff(days)
    q_runs = db.query(TestRun).filter(TestRun.created_at >= cutoff)
    if project_id:
        q_runs = q_runs.filter(TestRun.project_id == project_id)
    recent_runs = q_runs.all()
    suite_last_status = {}
    suite_gate_failed = set()
    for r in recent_runs:
        try:
            s = _safe_json(r.summary)
            sid = s.get('suite_id')
            if sid:
                suite_last_status[sid] = r.status
                if s.get('gate_status') == 'failed':
                    suite_gate_failed.add(sid)
        except Exception as _e:
            logger.debug("silent error suppressed at %s: %s", __name__, _e)

    type_priority = {'release': 3, 'smoke': 2, 'regression': 1}

    results = []
    for suite in suites:
        case_ids = suite_cases_map.get(suite.id, [])
        if not case_ids:
            continue

        # aggregate case risks
        risks = [case_risk_map[cid] for cid in case_ids if cid in case_risk_map]
        if not risks:
            continue

        avg_score = sum(r["risk_score"] for r in risks) / len(risks)
        max_score = max(r["risk_score"] for r in risks)
        must_count = sum(1 for r in risks if _case_recommendation_level(r) == "must_run")
        high_count = sum(1 for r in risks if r["risk_level"] == "high")
        has_blocker = any(r["blocker_defects"] > 0 for r in risks)

        # suite risk score
        tp = type_priority.get(suite.suite_type, 0)
        suite_score = round(
            avg_score * 0.30
            + max_score * 0.20
            + min(must_count / max(len(risks), 1), 1.0) * 0.15
            + min(high_count / max(len(risks), 1), 1.0) * 0.10
            + (0.15 if has_blocker else 0)
            + (0.05 * tp)
            + (0.10 if suite.id in suite_gate_failed else 0),
            4
        )
        suite_score = min(suite_score, 1.0)

        # recommendation level
        if suite_score >= 0.6 or suite.suite_type in ('release', 'smoke') or has_blocker:
            rec = "must_run"
        elif suite_score >= 0.35:
            rec = "should_run"
        elif suite_score >= 0.15:
            rec = "optional"
        else:
            rec = "skip_candidate"

        reasons = []
        if suite.suite_type in ('release', 'smoke'):
            reasons.append(f"{suite.suite_type} 类型测试集优先执行")
        if has_blocker:
            reasons.append("包含关联 blocker/critical 缺陷的用例")
        if high_count > 0:
            reasons.append(f"包含 {high_count} 个高风险用例")
        if suite.id in suite_gate_failed:
            reasons.append("最近质量门禁失败")
        last = suite_last_status.get(suite.id)
        if last == 'failed':
            reasons.append("最近一次执行失败")
        if must_count > 0:
            reasons.append(f"{must_count} 个用例建议必须执行")

        results.append({
            "suite_id": suite.id,
            "suite_name": suite.name,
            "suite_type": suite.suite_type or 'mixed',
            "recommendation_level": rec,
            "risk_score": suite_score,
            "case_count": len(case_ids),
            "must_run_cases": must_count,
            "high_risk_cases": high_count,
            "last_run_status": last or "unknown",
            "reasons": reasons,
        })

    results.sort(key=lambda x: x["risk_score"], reverse=True)
    return results


# ── 4. module recommendation ─────────────────────────────────

def _build_module_recommendations(case_risk_map: dict):
    mod_cases = {}
    for info in case_risk_map.values():
        m = info["module"]
        mod_cases.setdefault(m, []).append(info)

    results = []
    for m, cases in mod_cases.items():
        avg_score = sum(c["risk_score"] for c in cases) / len(cases)
        max_score = max(c["risk_score"] for c in cases)
        high_count = sum(1 for c in cases if c["risk_level"] == "high")
        total_defects = sum(c["open_defects"] for c in cases)
        total_blocker = sum(c["blocker_defects"] for c in cases)
        total_flaky = sum(1 for c in cases if c["is_flaky"])
        fr = sum(c["failure_rate"] for c in cases) / len(cases)

        score = round((avg_score + max_score) / 2, 4)
        level = "high" if score >= 0.6 else ("medium" if score >= 0.35 else "low")

        reasons = []
        if fr > 0.2:
            reasons.append(f"模块平均失败率 {fr*100:.0f}%")
        if total_blocker > 0:
            reasons.append(f"存在 {total_blocker} 个 blocker/critical 缺陷")
        if total_defects > 0:
            reasons.append(f"存在 {total_defects} 个未关闭缺陷")
        if total_flaky > 0:
            reasons.append(f"存在 {total_flaky} 个 Flaky 候选")
        if high_count > 0:
            reasons.append(f"包含 {high_count} 个高风险用例")

        results.append({
            "module": m,
            "risk_score": score,
            "risk_level": level,
            "case_count": len(cases),
            "high_risk_cases": high_count,
            "failure_rate": round(fr, 4),
            "open_defects": total_defects,
            "blocker_defects": total_blocker,
            "flaky_candidates": total_flaky,
            "reasons": reasons,
        })

    results.sort(key=lambda x: x["risk_score"], reverse=True)
    return results


# ── 5. main recommend entry ──────────────────────────────────

def generate_recommendation(
    db: Session,
    project_id: int = None,
    days: int = 14,
    target: str = None,
    include_case_recommendations: bool = True,
    include_skip_candidates: bool = True,
    suite_type: str = None,
):
    """
    生成智能选测推荐。
    Returns dict with summary, suite_recommendations, case_recommendations,
    module_recommendations, skip_candidates.
    """
    case_risk_map = _build_case_risk_map(db, project_id=project_id, days=days)

    # ── case recommendations ──
    case_recs = []
    skip_candidates = []
    for cid, info in case_risk_map.items():
        rec_level = _case_recommendation_level(info)
        entry = {**info, "recommendation_level": rec_level}
        if rec_level == "skip_candidate":
            entry["disclaimer"] = "仅建议，不自动跳过"
            skip_candidates.append(entry)
        else:
            case_recs.append(entry)

    case_recs.sort(key=lambda x: x["risk_score"], reverse=True)
    skip_candidates.sort(key=lambda x: x["risk_score"])

    # ── suite recommendations ──
    suite_recs = _build_suite_recommendations(
        db, case_risk_map, project_id=project_id, days=days, suite_type=suite_type)

    # ── module recommendations ──
    mod_recs = _build_module_recommendations(case_risk_map)
    high_risk_modules = [m["module"] for m in mod_recs if m["risk_level"] == "high"]

    # ── counts ──
    must_run = sum(1 for c in case_recs if c["recommendation_level"] == "must_run")
    should_run = sum(1 for c in case_recs if c["recommendation_level"] == "should_run")
    optional = sum(1 for c in case_recs if c["recommendation_level"] == "optional")
    skip_count = len(skip_candidates)

    summary = {
        "project_id": project_id,
        "days": days,
        "target": target or "general",
        "total_candidates": len(case_risk_map),
        "must_run_count": must_run,
        "should_run_count": should_run,
        "optional_count": optional,
        "skip_candidate_count": skip_count,
        "high_risk_modules": high_risk_modules,
        "suite_count": len(suite_recs),
        "generated_at": datetime.now().isoformat(),
    }

    result = {
        "summary": summary,
        "suite_recommendations": suite_recs,
        "module_recommendations": mod_recs,
    }

    if include_case_recommendations:
        result["case_recommendations"] = case_recs
    else:
        result["case_recommendations"] = []

    if include_skip_candidates:
        result["skip_candidates"] = skip_candidates
    else:
        result["skip_candidates"] = []

    return result
