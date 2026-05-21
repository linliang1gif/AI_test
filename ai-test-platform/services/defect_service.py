# -*- coding: utf-8 -*-
"""
P3-3B: 缺陷闭环 MVP 服务
- 缺陷 CRUD
- 状态流转校验
- duplicate_key 生成与重复检测
- evidence 脱敏
- 从 run_case / failure_analysis 创建缺陷
"""
import hashlib
import logging
import re
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

from database.models import Defect, DefectEvent, RunCase, TestCase, TestRun

logger = logging.getLogger("defect_service")

# ── 常量 ──────────────────────────────────────────────
VALID_STATUSES = {"open", "confirmed", "fixed", "verified", "closed", "rejected", "reopened"}
VALID_SEVERITIES = {"blocker", "critical", "major", "minor", "trivial"}
VALID_PRIORITIES = {"P0", "P1", "P2", "P3"}
VALID_SOURCES = {
    "manual", "product_review", "code_compare", "long_flow",
    "run_failure", "failure_analysis", "quality_gate", "visual_diff",
    "performance_regression", "data_issue",
}

ALLOWED_TRANSITIONS = {
    "open": {"confirmed", "rejected"},
    "confirmed": {"fixed"},
    "fixed": {"verified"},
    "verified": {"closed"},
    "closed": {"reopened"},
    "rejected": set(),
    "reopened": {"confirmed", "rejected"},
}

SENSITIVE_PATTERNS = re.compile(
    r'(token|cookie|authorization|password|secret|api_key|apikey|access_token)\s*[:=]\s*\S+',
    re.IGNORECASE,
)


# ── 工具函数 ──────────────────────────────────────────
def _sanitize_evidence(evidence: dict) -> dict:
    """脱敏 evidence 中的敏感信息"""
    if not evidence:
        return evidence
    sanitized = {}
    for k, v in evidence.items():
        if isinstance(v, str):
            sanitized[k] = SENSITIVE_PATTERNS.sub(lambda m: m.group().split(':', 1)[0] + ':****' if ':' in m.group() else m.group().split('=', 1)[0] + '=****', v)
        elif isinstance(v, list):
            sanitized[k] = [SENSITIVE_PATTERNS.sub(lambda m: m.group().split(':', 1)[0] + ':****' if ':' in m.group() else m.group().split('=', 1)[0] + '=****', str(item)) for item in v]
        else:
            sanitized[k] = v
    return sanitized


def _generate_duplicate_key(project_id, case_id, failure_category, error_message) -> str:
    """生成 duplicate_key 用于重复缺陷识别"""
    normalized = re.sub(r'\d+', 'N', str(error_message or ''))[:200].strip().lower()
    raw = f"{project_id or 0}|{case_id or ''}|{failure_category or ''}|{normalized}"
    return hashlib.md5(raw.encode()).hexdigest()


def _defect_to_dict(d: Defect, include_events: bool = False) -> dict:
    result = {
        "id": d.id,
        "title": d.title,
        "description": d.description,
        "project_id": d.project_id,
        "module": d.module,
        "severity": d.severity,
        "priority": d.priority,
        "status": d.status,
        "source": d.source,
        "failure_category": d.failure_category,
        "case_id": d.case_id,
        "run_id": d.run_id,
        "run_case_id": d.run_case_id,
        "report_id": d.report_id,
        "trace_path": d.trace_path,
        "screenshot_path": d.screenshot_path,
        "evidence_json": d.evidence_json,
        "duplicate_key": d.duplicate_key,
        "created_by": d.created_by,
        "assigned_to": d.assigned_to,
        "created_at": d.created_at.isoformat() if d.created_at else None,
        "updated_at": d.updated_at.isoformat() if d.updated_at else None,
        "closed_at": d.closed_at.isoformat() if d.closed_at else None,
    }
    if include_events:
        result["events"] = [_event_to_dict(e) for e in (d.events or [])]
    return result


def _event_to_dict(e: DefectEvent) -> dict:
    return {
        "id": e.id,
        "defect_id": e.defect_id,
        "event_type": e.event_type,
        "from_status": e.from_status,
        "to_status": e.to_status,
        "comment": e.comment,
        "evidence_json": e.evidence_json,
        "created_by": e.created_by,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }


# ── 核心服务 ──────────────────────────────────────────
def create_defect(db: Session, data: dict) -> dict:
    """创建缺陷"""
    evidence = _sanitize_evidence(data.get("evidence_json") or {})
    dup_key = _generate_duplicate_key(
        data.get("project_id"), data.get("case_id"),
        data.get("failure_category"), data.get("title", "") + str(evidence.get("error_message", ""))
    )

    defect = Defect(
        title=data["title"],
        description=data.get("description", ""),
        project_id=data.get("project_id"),
        module=data.get("module", ""),
        severity=data.get("severity", "major"),
        priority=data.get("priority", "P2"),
        status="open",
        source=data.get("source", "manual"),
        failure_category=data.get("failure_category", ""),
        case_id=data.get("case_id"),
        run_id=data.get("run_id"),
        run_case_id=data.get("run_case_id"),
        report_id=data.get("report_id"),
        trace_path=data.get("trace_path"),
        screenshot_path=data.get("screenshot_path"),
        evidence_json=evidence,
        duplicate_key=dup_key,
        created_by=data.get("created_by", "system"),
        assigned_to=data.get("assigned_to"),
    )
    db.add(defect)
    db.flush()

    event = DefectEvent(
        defect_id=defect.id,
        event_type="created",
        to_status="open",
        comment=f"缺陷已创建, 来源: {defect.source}",
        created_by=defect.created_by,
    )
    db.add(event)
    db.commit()
    db.refresh(defect)
    return _defect_to_dict(defect)


def list_defects(db: Session, project_id=None, status=None, severity=None, source=None,
                 keyword=None, limit=50, offset=0) -> dict:
    """查询缺陷列表"""
    q = db.query(Defect)
    if project_id:
        q = q.filter(Defect.project_id == int(project_id))
    if status:
        q = q.filter(Defect.status == status)
    if severity:
        q = q.filter(Defect.severity == severity)
    if source:
        q = q.filter(Defect.source == source)
    if keyword:
        q = q.filter(Defect.title.contains(keyword))
    total = q.count()
    items = q.order_by(Defect.updated_at.desc()).offset(offset).limit(limit).all()
    return {
        "defects": [_defect_to_dict(d) for d in items],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


def get_defect(db: Session, defect_id: int) -> Optional[dict]:
    """查看缺陷详情（含事件）"""
    d = db.query(Defect).filter(Defect.id == defect_id).first()
    if not d:
        return None
    return _defect_to_dict(d, include_events=True)


def update_defect(db: Session, defect_id: int, data: dict) -> Optional[dict]:
    """更新缺陷基础信息"""
    d = db.query(Defect).filter(Defect.id == defect_id).first()
    if not d:
        return None

    updatable = ["title", "description", "module", "severity", "priority", "assigned_to", "failure_category"]
    changed = []
    for field in updatable:
        if field in data and getattr(d, field) != data[field]:
            setattr(d, field, data[field])
            changed.append(field)

    if changed:
        event = DefectEvent(
            defect_id=d.id,
            event_type="update",
            comment=f"更新字段: {', '.join(changed)}",
            created_by=data.get("updated_by", "system"),
        )
        db.add(event)
        db.commit()
        db.refresh(d)

    return _defect_to_dict(d)


def transition_defect(db: Session, defect_id: int, to_status: str, comment: str = "", by: str = "system") -> dict:
    """状态流转"""
    d = db.query(Defect).filter(Defect.id == defect_id).first()
    if not d:
        return {"error": "defect_not_found"}

    if to_status not in VALID_STATUSES:
        return {"error": f"invalid_status: {to_status}"}

    allowed = ALLOWED_TRANSITIONS.get(d.status, set())
    if to_status not in allowed:
        return {"error": f"invalid_transition: {d.status} -> {to_status}", "allowed": list(allowed)}

    from_status = d.status
    d.status = to_status
    if to_status == "closed":
        d.closed_at = datetime.now()
    if to_status == "reopened":
        d.closed_at = None

    event = DefectEvent(
        defect_id=d.id,
        event_type="status_change",
        from_status=from_status,
        to_status=to_status,
        comment=comment,
        created_by=by,
    )
    db.add(event)
    db.commit()
    db.refresh(d)
    return _defect_to_dict(d)


def check_duplicates(db: Session, project_id=None, case_id=None, failure_category=None, error_message=None) -> dict:
    """检查重复缺陷"""
    dup_key = _generate_duplicate_key(project_id, case_id, failure_category, error_message)
    existing = db.query(Defect).filter(
        Defect.duplicate_key == dup_key,
        Defect.status.in_(["open", "confirmed", "fixed", "reopened"]),
    ).all()
    return {
        "duplicate_key": dup_key,
        "has_duplicates": len(existing) > 0,
        "duplicates": [_defect_to_dict(d) for d in existing],
    }


def create_from_run_case(db: Session, run_case_id: str, data: dict = None) -> dict:
    """从 run_case 创建缺陷"""
    data = data or {}
    rc = db.query(RunCase).filter(RunCase.id == run_case_id).first()
    if not rc:
        return {"error": f"run_case {run_case_id} not found"}

    tc = db.query(TestCase).filter(TestCase.id == rc.test_case_id).first()

    evidence = _sanitize_evidence({
        "error_message": rc.error_message or "",
        "error_type": rc.error_type or "",
        "status": rc.status,
    })

    defect_data = {
        "title": data.get("title") or f"[{rc.status}] {tc.title if tc else rc.test_case_id}",
        "description": data.get("description", ""),
        "source": "run_failure",
        "case_id": rc.test_case_id,
        "run_id": rc.run_id,
        "run_case_id": run_case_id,
        "failure_category": rc.error_type or "unknown",
        "severity": data.get("severity", "major"),
        "priority": data.get("priority", "P2"),
        "evidence_json": evidence,
        "created_by": data.get("created_by", "system"),
        "module": data.get("module", ""),
        "project_id": data.get("project_id"),
    }
    return create_defect(db, defect_data)


def create_from_failure_analysis(db: Session, data: dict) -> dict:
    """从失败归因创建缺陷"""
    evidence = _sanitize_evidence({
        "error_message": data.get("error_message", ""),
        "failure_category": data.get("failure_category", ""),
        "suggested_action": data.get("suggested_action", ""),
        "console_errors": data.get("console_errors", []),
        "network_errors": data.get("network_errors", []),
    })
    defect_data = {
        "title": data.get("title") or f"[归因] {data.get('failure_category', 'unknown')}",
        "description": data.get("description", ""),
        "source": "failure_analysis",
        "case_id": data.get("case_id"),
        "run_id": data.get("run_id"),
        "run_case_id": data.get("run_case_id"),
        "failure_category": data.get("failure_category", "unknown"),
        "severity": data.get("severity", "major"),
        "priority": data.get("priority", "P2"),
        "screenshot_path": data.get("screenshot_path"),
        "trace_path": data.get("trace_path"),
        "evidence_json": evidence,
        "created_by": data.get("created_by", "system"),
        "module": data.get("module", ""),
        "project_id": data.get("project_id"),
    }
    return create_defect(db, defect_data)


def link_run(db: Session, defect_id: int, run_id: str, by: str = "system") -> dict:
    """关联执行记录到缺陷"""
    d = db.query(Defect).filter(Defect.id == defect_id).first()
    if not d:
        return {"error": "defect_not_found"}

    event = DefectEvent(
        defect_id=d.id,
        event_type="link_run",
        comment=f"关联执行记录: {run_id}",
        evidence_json={"linked_run_id": run_id},
        created_by=by,
    )
    db.add(event)
    if not d.run_id:
        d.run_id = run_id
    db.commit()
    db.refresh(d)
    return _defect_to_dict(d)


def get_defect_summary_for_gate(db: Session, case_ids: List[str] = None, run_id: str = None) -> dict:
    """获取缺陷摘要供质量门禁使用"""
    q = db.query(Defect)
    if run_id:
        q = q.filter(Defect.run_id == run_id)
    elif case_ids:
        q = q.filter(Defect.case_id.in_(case_ids))
    else:
        q = q.filter(Defect.status.in_(["open", "confirmed", "reopened"]))

    defects = q.all()
    open_defects = [d for d in defects if d.status in ("open", "confirmed", "reopened")]
    blocker_defects = [d for d in open_defects if d.severity == "blocker"]
    known_issues = [d for d in defects if d.status in ("confirmed", "fixed")]

    return {
        "linked_defects": len(defects),
        "open_defects": len(open_defects),
        "known_issues": len(known_issues),
        "blocker_defects": len(blocker_defects),
        "blocker_ids": [d.id for d in blocker_defects],
    }
