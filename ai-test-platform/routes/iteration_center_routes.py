#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
D2-3A 迭代中心路由 — 16 个端点覆盖迭代测试闭环 MVP

POST   /api/v2/iterations                                    创建迭代
GET    /api/v2/projects/{pid}/iterations                     项目迭代列表
GET    /api/v2/iterations/{iid}                              迭代详情
PATCH  /api/v2/iterations/{iid}                              更新迭代
POST   /api/v2/iterations/{iid}/requirements                 录入需求
GET    /api/v2/iterations/{iid}/requirements                 查询需求
POST   /api/v2/iterations/{iid}/ai/analyze-requirements      AI解析需求
POST   /api/v2/iterations/{iid}/test-points/generate         生成测试点
GET    /api/v2/iterations/{iid}/test-points                  查询测试点
PATCH  /api/v2/iteration-test-points/{tpid}/confirm          确认测试点
POST   /api/v2/iterations/{iid}/test-cases/generate          生成测试用例
GET    /api/v2/iterations/{iid}/test-cases                   查询迭代用例
POST   /api/v2/iterations/{iid}/execution-sets               生成执行集
GET    /api/v2/iterations/{iid}/execution-sets               查询执行集
POST   /api/v2/iterations/{iid}/run                          执行迭代测试集
GET    /api/v2/iterations/{iid}/report                       迭代测试报告
"""
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.session import get_db
from database.models import (
    Iteration, IterationRequirement, IterationTestPoint, IterationExecutionSet,
    IterationExecutionSetCase,
    TestCase, TestRun, RunCase, Project, Report, Environment,
)
from services.sanitize import sanitize_exception
from services.iteration_template_service import get_iteration_template, list_iteration_templates

logger = logging.getLogger("iteration_center")
router = APIRouter(tags=["iteration-center"])

VALID_STATUSES = ["planning", "in_progress", "testing", "completed", "archived"]


# ═══════ Pydantic 请求模型 ═══════

class CreateIterationBody(BaseModel):
    project_id: int
    name: str
    version: Optional[str] = ""
    description: Optional[str] = ""
    status: str = "planning"
    owner: Optional[str] = ""
    test_owner: Optional[str] = ""
    planned_start_time: Optional[str] = ""
    planned_release_time: Optional[str] = ""
    template_key: Optional[str] = ""

class PatchIterationBody(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    owner: Optional[str] = None
    test_owner: Optional[str] = None
    planned_start_time: Optional[str] = None
    planned_release_time: Optional[str] = None

class CreateRequirementBody(BaseModel):
    title: str
    content: Optional[str] = ""
    source_type: Optional[str] = "manual"
    source_url: Optional[str] = ""
    risk_level: Optional[str] = "P1"

class ConfirmTestPointBody(BaseModel):
    confirmed: bool = True

class CreateExecutionSetBody(BaseModel):
    name: Optional[str] = None
    type: str = "iteration"  # smoke/iteration/regression

class RunIterationBody(BaseModel):
    execution_set_id: Optional[int] = None
    environment_id: Optional[int] = None
    base_url: Optional[str] = ""


# ═══════ 辅助函数 ═══════

def _iter_dict(it: Iteration, stats: dict = None) -> dict:
    d = {
        "id": it.id,
        "project_id": it.project_id,
        "name": it.name,
        "version": getattr(it, 'version', '') or '',
        "code": it.code or "",
        "description": it.description or "",
        "status": it.status,
        "owner": it.owner or "",
        "test_owner": getattr(it, 'test_owner', '') or '',
        "planned_start_time": getattr(it, 'planned_start_time', '') or '',
        "planned_release_time": getattr(it, 'planned_release_time', '') or '',
        "start_date": it.start_date or "",
        "end_date": it.end_date or "",
        "created_at": it.created_at.isoformat() if it.created_at else None,
        "updated_at": it.updated_at.isoformat() if it.updated_at else None,
    }
    if stats:
        d.update(stats)
    return d


def _get_iter_or_404(db: Session, iid: int) -> Iteration:
    it = db.query(Iteration).filter(Iteration.id == iid).first()
    if not it:
        _raise_api_error(404, "ITERATION_NOT_FOUND", "迭代不存在", {"iteration_id": iid})
    return it


def _raise_api_error(
    status_code: int,
    code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    detail = {"code": code, "message": message}
    if details:
        detail.update(details)
    raise HTTPException(status_code=status_code, detail=detail)


def _valid_base_url(base_url: Optional[str]) -> bool:
    value = (base_url or "").strip().lower()
    return value.startswith("http://") or value.startswith("https://")


def _resolve_iteration_environment(
    db: Session,
    it: Iteration,
    body: RunIterationBody,
) -> tuple[Optional[int], str]:
    """Resolve a real execution target for this iteration."""
    explicit_base_url = (body.base_url or "").strip()
    if explicit_base_url:
        if not _valid_base_url(explicit_base_url):
            _raise_api_error(
                400,
                "INVALID_BASE_URL",
                "测试环境地址必须以 http:// 或 https:// 开头",
                {"base_url_present": True},
            )
        return body.environment_id, explicit_base_url.rstrip("/")

    if body.environment_id:
        env = db.query(Environment).filter(Environment.id == body.environment_id).first()
        if not env:
            _raise_api_error(
                404,
                "ENVIRONMENT_NOT_FOUND",
                "测试环境不存在",
                {"environment_id": body.environment_id},
            )
        if env.project_id != it.project_id:
            _raise_api_error(
                400,
                "ENVIRONMENT_PROJECT_MISMATCH",
                "测试环境不属于当前迭代项目",
                {"environment_id": env.id, "project_id": it.project_id},
            )
        if not _valid_base_url(env.base_url):
            _raise_api_error(
                400,
                "ENVIRONMENT_BASE_URL_INVALID",
                "测试环境地址无效，请先配置测试环境",
                {"environment_id": env.id},
            )
        return env.id, env.base_url.rstrip("/")

    env = db.query(Environment).filter(
        Environment.project_id == it.project_id
    ).order_by(Environment.created_at.desc()).first()
    if not env:
        _raise_api_error(
            400,
            "ENVIRONMENT_REQUIRED",
            "当前迭代所属项目未配置测试环境，请先配置测试环境或在请求中传入 base_url",
            {"project_id": it.project_id},
        )
    if not _valid_base_url(env.base_url):
        _raise_api_error(
            400,
            "ENVIRONMENT_BASE_URL_INVALID",
            "测试环境地址无效，请先配置测试环境",
            {"environment_id": env.id},
        )
    return env.id, env.base_url.rstrip("/")


def _validate_execution_cases(cases: List[TestCase]) -> None:
    invalid_cases = []
    for tc in cases:
        cfg = tc.execution_config or {}
        method = (cfg.get("method") or "").strip()
        url = (cfg.get("url") or "").strip()
        if getattr(tc, "case_type", None) != "api":
            invalid_cases.append({
                "case_id": tc.id,
                "title": tc.title,
                "reason": "仅支持 api 用例进入迭代真实执行",
            })
        elif not method or not url:
            invalid_cases.append({
                "case_id": tc.id,
                "title": tc.title,
                "reason": "缺少 execution_config.method 或 execution_config.url",
            })
    if invalid_cases:
        _raise_api_error(
            400,
            "TEST_CASE_EXECUTION_CONFIG_INVALID",
            f"执行集中有 {len(invalid_cases)} 条用例缺少执行必要字段",
            {"invalid_cases": invalid_cases[:20]},
        )


def _iter_stats(db: Session, iid: int) -> dict:
    total = db.query(func.count(TestCase.id)).filter(TestCase.iteration_id == iid).scalar() or 0
    passed = db.query(func.count(TestCase.id)).filter(TestCase.iteration_id == iid, TestCase.last_run_status == 'passed').scalar() or 0
    failed = db.query(func.count(TestCase.id)).filter(TestCase.iteration_id == iid, TestCase.last_run_status == 'failed').scalar() or 0
    req_count = db.query(func.count(IterationRequirement.id)).filter(IterationRequirement.iteration_id == iid).scalar() or 0
    tp_total = db.query(func.count(IterationTestPoint.id)).filter(IterationTestPoint.iteration_id == iid).scalar() or 0
    tp_confirmed = db.query(func.count(IterationTestPoint.id)).filter(IterationTestPoint.iteration_id == iid, IterationTestPoint.confirmed == True).scalar() or 0
    es_count = db.query(func.count(IterationExecutionSet.id)).filter(IterationExecutionSet.iteration_id == iid).scalar() or 0
    return {
        "total_cases": total, "passed_cases": passed, "failed_cases": failed,
        "pass_rate": round(passed / total * 100, 1) if total > 0 else 0,
        "requirement_count": req_count, "test_point_total": tp_total,
        "test_point_confirmed": tp_confirmed, "execution_set_count": es_count,
    }


# ═══════ 1. POST /api/v2/iterations ═══════
@router.get("/api/v2/iteration-templates")
def get_templates():
    return {"templates": list_iteration_templates(), "total": len(list_iteration_templates())}


@router.post("/api/v2/iterations")
def create_iteration(body: CreateIterationBody, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == body.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    if body.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"无效状态: {body.status}")
    template = None
    if body.template_key:
        template = get_iteration_template(body.template_key)
        if not template:
            raise HTTPException(status_code=400, detail=f"无效迭代模板: {body.template_key}")
    it = Iteration(
        project_id=body.project_id, name=body.name,
        version=body.version or "", description=body.description or "",
        status=body.status, owner=body.owner or "",
        test_owner=body.test_owner or "",
        planned_start_time=body.planned_start_time or "",
        planned_release_time=body.planned_release_time or "",
    )
    db.add(it)
    db.flush()

    template_points = []
    if template:
        for tp_data in template.get("default_test_points", []):
            tp = IterationTestPoint(
                iteration_id=it.id,
                requirement_id=None,
                module_name=tp_data.get("module_name", ""),
                test_point=tp_data.get("test_point", ""),
                risk_level=tp_data.get("risk_level", "P1"),
                priority=tp_data.get("priority", "medium"),
                test_type=f"template_{template['template_key']}_{tp_data.get('test_type', 'functional')}",
                ai_generated=False,
                confirmed=False,
            )
            db.add(tp)
            template_points.append(tp)

    db.commit()
    db.refresh(it)
    logger.info(
        "迭代创建: id=%s name=%s project=%s template=%s template_points=%s",
        it.id, it.name, body.project_id, body.template_key or "", len(template_points),
    )
    result = _iter_dict(it)
    if template:
        result["template_key"] = template["template_key"]
        result["template_name"] = template["template_name"]
        result["template_test_point_count"] = len(template_points)
        result["template_default_execution_sets"] = template.get("default_execution_sets", [])
        result["message"] = "已根据模板生成初始测试点，请在测试点页确认后再生成用例。"
    return result


# ═══════ 2. GET /api/v2/projects/{pid}/iterations ═══════
# 注意: 这个路由已在 iteration_routes.py 中存在，但这里使用新模型字段
# 保持 iteration_routes.py 的路由不变，这里不重复注册


# ═══════ 3. GET /api/v2/iterations/{iid} ═══════
# 注意: 已在 iteration_routes.py 中存在，这里增强为 PATCH + 详情含新字段


# ═══════ 4. PATCH /api/v2/iterations/{iid} ═══════
@router.patch("/api/v2/iterations/{iteration_id}")
def patch_iteration(iteration_id: int, body: PatchIterationBody, db: Session = Depends(get_db)):
    it = _get_iter_or_404(db, iteration_id)
    if body.status is not None and body.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"无效状态: {body.status}")
    updates = body.dict(exclude_unset=True)
    for k, v in updates.items():
        setattr(it, k, v)
    it.updated_at = datetime.now()
    db.commit()
    db.refresh(it)
    return _iter_dict(it, _iter_stats(db, it.id))


# ═══════ 5. POST /api/v2/iterations/{iid}/requirements ═══════
@router.post("/api/v2/iterations/{iteration_id}/requirements")
def create_requirement(iteration_id: int, body: CreateRequirementBody, db: Session = Depends(get_db)):
    _get_iter_or_404(db, iteration_id)
    req = IterationRequirement(
        iteration_id=iteration_id, title=body.title,
        content=body.content or "", source_type=body.source_type or "manual",
        source_url=body.source_url or "", risk_level=body.risk_level or "P1",
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return _req_dict(req)


def _req_dict(r: IterationRequirement) -> dict:
    return {
        "id": r.id, "iteration_id": r.iteration_id, "title": r.title,
        "content": r.content or "", "source_type": r.source_type or "",
        "source_url": r.source_url or "", "ai_summary": r.ai_summary or "",
        "risk_level": r.risk_level or "P1",
        "confirm_questions": _safe_json_loads(r.confirm_questions),
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }


def _safe_json_loads(s):
    if not s:
        return []
    try:
        return json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return []


# ═══════ 6. GET /api/v2/iterations/{iid}/requirements ═══════
@router.get("/api/v2/iterations/{iteration_id}/requirements")
def list_requirements(iteration_id: int, db: Session = Depends(get_db)):
    _get_iter_or_404(db, iteration_id)
    items = db.query(IterationRequirement).filter(
        IterationRequirement.iteration_id == iteration_id
    ).order_by(IterationRequirement.created_at.desc()).all()
    return {"requirements": [_req_dict(r) for r in items], "total": len(items)}


# ═══════ 7. POST /api/v2/iterations/{iid}/ai/analyze-requirements ═══════
@router.post("/api/v2/iterations/{iteration_id}/ai/analyze-requirements")
def ai_analyze_requirements(iteration_id: int, db: Session = Depends(get_db)):
    it = _get_iter_or_404(db, iteration_id)
    reqs = db.query(IterationRequirement).filter(
        IterationRequirement.iteration_id == iteration_id
    ).all()
    if not reqs:
        raise HTTPException(status_code=400, detail="该迭代暂无需求，请先录入需求")

    from services.iteration_ai_service import analyze_requirements
    req_list = [{"title": r.title, "content": r.content or ""} for r in reqs]
    result = analyze_requirements(req_list)

    # 将 AI 摘要回写到各需求
    for r in reqs:
        r.ai_summary = json.dumps(result.get("functional_points", []), ensure_ascii=False)
        if result.get("confirm_questions"):
            r.confirm_questions = json.dumps(result["confirm_questions"], ensure_ascii=False)
        r.updated_at = datetime.now()
    db.commit()

    return {
        "iteration_id": iteration_id,
        "analysis": result,
        "source": result.get("_source", "unknown"),
    }


# ═══════ 8. POST /api/v2/iterations/{iid}/test-points/generate ═══════
@router.post("/api/v2/iterations/{iteration_id}/test-points/generate")
def generate_test_points(iteration_id: int, db: Session = Depends(get_db)):
    it = _get_iter_or_404(db, iteration_id)
    reqs = db.query(IterationRequirement).filter(
        IterationRequirement.iteration_id == iteration_id
    ).all()
    if not reqs:
        raise HTTPException(status_code=400, detail="该迭代暂无需求，请先录入需求")

    from services.iteration_ai_service import analyze_requirements
    req_list = [{"title": r.title, "content": r.content or ""} for r in reqs]
    result = analyze_requirements(req_list)

    created = []
    for tp_data in result.get("test_points", []):
        if isinstance(tp_data, dict):
            text = tp_data.get("test_point", str(tp_data))
            priority = tp_data.get("priority", "medium")
            test_type = tp_data.get("test_type", "functional")
            risk_level = tp_data.get("risk_level", "P1")
            module_name = tp_data.get("module_name", "")
            recommended_api = tp_data.get("recommended_api")
            execution_config = tp_data.get("execution_config")
        else:
            text = str(tp_data)
            priority, test_type, risk_level = "medium", "functional", "P1"
            module_name = ""
            recommended_api = None
            execution_config = None

        tp = IterationTestPoint(
            iteration_id=iteration_id,
            requirement_id=reqs[0].id if reqs else None,
            module_name=module_name,
            test_point=text, priority=priority,
            test_type=test_type, risk_level=risk_level,
            recommended_api=recommended_api,
            execution_config=execution_config,
            ai_generated=True, confirmed=False,
        )
        db.add(tp)
        created.append(tp)

    db.commit()
    for tp in created:
        db.refresh(tp)

    return {
        "iteration_id": iteration_id,
        "generated": len(created),
        "test_points": [_tp_dict(tp) for tp in created],
        "source": result.get("_source", "unknown"),
    }


def _tp_dict(tp: IterationTestPoint) -> dict:
    return {
        "id": tp.id, "iteration_id": tp.iteration_id,
        "requirement_id": tp.requirement_id,
        "module_name": tp.module_name or "",
        "test_point": tp.test_point, "risk_level": tp.risk_level or "P1",
        "priority": tp.priority or "medium",
        "test_type": tp.test_type or "functional",
        "recommended_api": tp.recommended_api,
        "execution_config": tp.execution_config,
        "ai_generated": tp.ai_generated, "confirmed": tp.confirmed,
        "created_at": tp.created_at.isoformat() if tp.created_at else None,
    }


# ═══════ 9. GET /api/v2/iterations/{iid}/test-points ═══════
@router.get("/api/v2/iterations/{iteration_id}/test-points")
def list_test_points(iteration_id: int, confirmed: Optional[bool] = Query(None), db: Session = Depends(get_db)):
    _get_iter_or_404(db, iteration_id)
    q = db.query(IterationTestPoint).filter(IterationTestPoint.iteration_id == iteration_id)
    if confirmed is not None:
        q = q.filter(IterationTestPoint.confirmed == confirmed)
    items = q.order_by(IterationTestPoint.created_at.desc()).all()
    return {"test_points": [_tp_dict(tp) for tp in items], "total": len(items)}


# ═══════ 10. PATCH /api/v2/iteration-test-points/{tpid}/confirm ═══════
@router.patch("/api/v2/iteration-test-points/{test_point_id}/confirm")
def confirm_test_point(test_point_id: int, body: ConfirmTestPointBody, db: Session = Depends(get_db)):
    tp = db.query(IterationTestPoint).filter(IterationTestPoint.id == test_point_id).first()
    if not tp:
        raise HTTPException(status_code=404, detail="测试点不存在")
    tp.confirmed = body.confirmed
    tp.updated_at = datetime.now()
    db.commit()
    db.refresh(tp)
    return _tp_dict(tp)


# ═══════ 11. POST /api/v2/iterations/{iid}/test-cases/generate ═══════
@router.post("/api/v2/iterations/{iteration_id}/test-cases/generate")
def generate_test_cases(iteration_id: int, db: Session = Depends(get_db)):
    it = _get_iter_or_404(db, iteration_id)
    confirmed_points = db.query(IterationTestPoint).filter(
        IterationTestPoint.iteration_id == iteration_id,
        IterationTestPoint.confirmed == True,
    ).all()
    if not confirmed_points:
        raise HTTPException(status_code=400, detail="暂无已确认的测试点，请先确认测试点")

    from services.iteration_ai_service import generate_test_cases_from_points
    tp_data = [_tp_dict(tp) for tp in confirmed_points]
    case_templates = generate_test_cases_from_points(tp_data, it.name)

    created_ids = []
    for tmpl in case_templates:
        case_id = f"TC_{it.project_id}_{iteration_id}_{uuid.uuid4().hex[:8]}"
        tc = TestCase(
            id=case_id,
            title=tmpl["name"][:500],
            module=tmpl.get("module_name", "")[:200] or None,
            priority=tmpl.get("priority", "medium"),
            case_type=tmpl.get("case_type", "functional"),
            source="ai_generated",
            module_name=tmpl.get("module_name", ""),
            risk_level=tmpl.get("risk_level", "P1"),
            iteration_id=iteration_id,
            test_point_id=str(tmpl.get("test_point_id") or ""),
            api_id=(tmpl.get("recommended_api") or {}).get("url") if isinstance(tmpl.get("recommended_api"), dict) else None,
            execution_config=tmpl.get("execution_config"),
            assertions=[],
            expected=tmpl.get("description", ""),
        )
        db.add(tc)
        created_ids.append(case_id)

    db.commit()
    logger.info("迭代 %s 生成 %d 个测试用例", iteration_id, len(created_ids))
    return {
        "iteration_id": iteration_id,
        "generated": len(created_ids),
        "case_ids": created_ids,
    }


# ═══════ 12. GET /api/v2/iterations/{iid}/test-cases ═══════
@router.get("/api/v2/iterations/{iteration_id}/test-cases")
def list_iteration_test_cases(iteration_id: int, db: Session = Depends(get_db)):
    _get_iter_or_404(db, iteration_id)
    cases = db.query(TestCase).filter(TestCase.iteration_id == iteration_id).all()
    result = []
    for c in cases:
        result.append({
            "id": c.id, "title": c.title or "", "name": c.title or "",
            "module": c.module or "",
            "priority": c.priority or "medium",
            "case_type": c.case_type or "api",
            "source": c.source or "",
            "module_name": c.module_name or "",
            "risk_level": c.risk_level or "",
            "last_run_status": c.last_run_status or "pending",
            "iteration_id": c.iteration_id,
            "expected": c.expected or "",
        })
    return {"test_cases": result, "total": len(result)}


# ═══════ 13. POST /api/v2/iterations/{iid}/execution-sets ═══════
@router.post("/api/v2/iterations/{iteration_id}/execution-sets")
def create_execution_set(iteration_id: int, body: CreateExecutionSetBody, db: Session = Depends(get_db)):
    it = _get_iter_or_404(db, iteration_id)
    cases = db.query(TestCase).filter(TestCase.iteration_id == iteration_id).all()
    if not cases:
        raise HTTPException(status_code=400, detail="该迭代暂无测试用例")

    set_type = body.type or "iteration"
    fallback_flag = False

    if set_type == "smoke":
        # P0/P1 + high priority + high risk
        selected = [c for c in cases if
                    (c.risk_level or "").upper() in ("P0", "P1") or
                    (c.priority or "").lower() in ("high", "critical")]
        if not selected:
            selected = cases[:min(5, len(cases))]
    elif set_type == "regression":
        # Current iteration cases + historical regression cases
        regression_extra = db.query(TestCase).filter(
            TestCase.iteration_id != iteration_id,
            TestCase.tags.isnot(None),
        ).all()
        regression_extra = [c for c in regression_extra
                           if isinstance(c.tags, list) and "regression" in c.tags]
        if regression_extra:
            selected = cases + regression_extra
        else:
            selected = cases
            fallback_flag = True
    else:
        selected = cases

    name = body.name or f"{it.name}-{set_type}-{datetime.now().strftime('%m%d%H%M')}"
    es = IterationExecutionSet(
        iteration_id=iteration_id, name=name,
        type=set_type, status="created", case_count=len(selected),
    )
    db.add(es)
    db.flush()

    # Write case associations
    for c in selected:
        db.add(IterationExecutionSetCase(
            execution_set_id=es.id, test_case_id=c.id,
        ))
    db.commit()
    db.refresh(es)

    result = _es_dict(es)
    result["case_ids"] = [c.id for c in selected]
    if fallback_flag:
        result["regression_fallback"] = True
    return result


def _es_dict(es: IterationExecutionSet) -> dict:
    return {
        "id": es.id, "iteration_id": es.iteration_id,
        "name": es.name, "type": es.type,
        "status": es.status, "case_count": es.case_count,
        "run_id": es.run_id or None,
        "created_at": es.created_at.isoformat() if es.created_at else None,
    }


# ═══════ 14. GET /api/v2/iterations/{iid}/execution-sets ═══════
@router.get("/api/v2/iterations/{iteration_id}/execution-sets")
def list_execution_sets(iteration_id: int, db: Session = Depends(get_db)):
    _get_iter_or_404(db, iteration_id)
    items = db.query(IterationExecutionSet).filter(
        IterationExecutionSet.iteration_id == iteration_id
    ).order_by(IterationExecutionSet.created_at.desc()).all()
    return {"execution_sets": [_es_dict(es) for es in items], "total": len(items)}


# ═══════ 15. POST /api/v2/iterations/{iid}/run ═══════
@router.post("/api/v2/iterations/{iteration_id}/run")
def run_iteration(
    iteration_id: int,
    body: RunIterationBody = Body(RunIterationBody()),
    db: Session = Depends(get_db),
):
    """执行迭代测试集 — 复用现有 ExecutionEngineV2 真实执行"""
    it = _get_iter_or_404(db, iteration_id)
    environment_id = None
    base_url = None
    if (body.base_url or "").strip():
        environment_id, base_url = _resolve_iteration_environment(db, it, body)

    # Resolve execution set
    es = None
    if body.execution_set_id:
        es = db.query(IterationExecutionSet).filter(
            IterationExecutionSet.id == body.execution_set_id,
        ).first()
        if not es:
            _raise_api_error(
                404,
                "EXECUTION_SET_NOT_FOUND",
                "执行集不存在",
                {"execution_set_id": body.execution_set_id},
            )
        if es.iteration_id != iteration_id:
            _raise_api_error(
                400,
                "EXECUTION_SET_ITERATION_MISMATCH",
                "执行集不属于当前迭代",
                {"iteration_id": iteration_id, "execution_set_id": body.execution_set_id},
            )
    else:
        es = db.query(IterationExecutionSet).filter(
            IterationExecutionSet.iteration_id == iteration_id,
            IterationExecutionSet.type == "iteration",
        ).order_by(IterationExecutionSet.created_at.desc()).first()
        if not es:
            es = db.query(IterationExecutionSet).filter(
                IterationExecutionSet.iteration_id == iteration_id,
            ).order_by(IterationExecutionSet.created_at.desc()).first()

    if not es:
        _raise_api_error(
            400,
            "EXECUTION_SET_REQUIRED",
            "该迭代暂无执行集，请先创建执行集",
            {"iteration_id": iteration_id},
        )

    # Get cases from execution set association
    set_case_rows = db.query(IterationExecutionSetCase).filter(
        IterationExecutionSetCase.execution_set_id == es.id
    ).all()
    case_ids = [sc.test_case_id for sc in set_case_rows]
    if not case_ids:
        _raise_api_error(
            400,
            "EXECUTION_SET_EMPTY",
            "执行集没有关联用例，请重新创建执行集",
            {"iteration_id": iteration_id, "execution_set_id": es.id},
        )

    cases = db.query(TestCase).filter(TestCase.id.in_(case_ids)).all()
    found_ids = {c.id for c in cases}
    missing_ids = [cid for cid in case_ids if cid not in found_ids]
    if missing_ids:
        _raise_api_error(
            400,
            "EXECUTION_SET_CASE_MISSING",
            "执行集中存在已失效或不存在的用例",
            {"execution_set_id": es.id, "missing_case_ids": missing_ids[:20]},
        )
    _validate_execution_cases(cases)
    if base_url is None:
        environment_id, base_url = _resolve_iteration_environment(db, it, body)

    from services.batch_execution_service import BatchExecutionService

    es.status = "running"
    db.commit()

    try:
        result = BatchExecutionService(db).execute(
            case_ids=case_ids,
            environment_id=environment_id,
            base_url=base_url,
            trigger_type="iteration",
            iteration_id=iteration_id,
            project_id=it.project_id,
            allow_unsafe_methods=True,
            allow_write_operations=True,
            skip_destructive=False,
        )
    except HTTPException as exc:
        db.rollback()
        es.status = "error"
        es.updated_at = datetime.now()
        db.commit()
        detail = exc.detail
        if isinstance(detail, dict):
            message = detail.get("message") or detail.get("detail") or "迭代执行失败"
            code = detail.get("code") or "ITERATION_RUN_FAILED"
            extra = {k: v for k, v in detail.items() if k not in ("code", "message", "detail", "trace_id")}
        else:
            message = str(detail) if detail else "迭代执行失败"
            code = "ITERATION_RUN_FAILED"
            extra = {}
        _raise_api_error(exc.status_code, code, message, extra)
    except Exception as exc:
        db.rollback()
        es.status = "error"
        es.updated_at = datetime.now()
        db.commit()
        logger.exception("迭代执行引擎异常: iter=%s es=%s err=%s", iteration_id, es.id, sanitize_exception(exc))
        _raise_api_error(
            500,
            "EXECUTION_ENGINE_ERROR",
            "执行引擎异常，请查看后端日志",
            {"iteration_id": iteration_id, "execution_set_id": es.id},
        )

    es.run_id = result["run_id"]
    if result["failed_cases"] > 0:
        es.status = "partial" if result["passed_cases"] > 0 else "failed"
    elif result["status"] in ("passed", "no_assertion"):
        es.status = "passed"
    else:
        es.status = result["status"]
    db.commit()

    logger.info(
        "迭代执行完成: run_id=%s iter=%d passed=%d failed=%d error=%d",
        result["run_id"], iteration_id,
        result["passed_cases"], result["failed_cases"], result["error_cases"],
    )

    return {
        "run_id": result["run_id"],
        "execution_set_id": es.id,
        "environment_id": environment_id,
        "base_url": base_url,
        "total_cases": result["total_cases"],
        "passed": result["passed_cases"],
        "failed": result["failed_cases"],
        "error": result["error_cases"],
        "skipped": result["skipped_cases"],
        "no_assertion": result["no_assertion_cases"],
        "pass_rate": result["pass_rate"],
        "status": result["status"],
        "duration_s": round(result["duration_ms"] / 1000, 2),
        "results": result["results"],
    }


# ═══════ 16. GET /api/v2/iterations/{iid}/report ═══════
@router.get("/api/v2/iterations/{iteration_id}/report")
def get_iteration_report(iteration_id: int, db: Session = Depends(get_db)):
    it = _get_iter_or_404(db, iteration_id)

    # All runs for this iteration
    runs = db.query(TestRun).filter(
        TestRun.iteration_id == iteration_id
    ).order_by(TestRun.created_at.desc()).all()

    latest_run = runs[0] if runs else None
    latest_run_id = latest_run.id if latest_run else None
    latest_execution_set = None
    if latest_run_id:
        latest_execution_set = db.query(IterationExecutionSet).filter(
            IterationExecutionSet.iteration_id == iteration_id,
            IterationExecutionSet.run_id == latest_run_id,
        ).order_by(IterationExecutionSet.updated_at.desc()).first()
    latest_execution_set_id = latest_execution_set.id if latest_execution_set else None

    run_summaries = []
    for r in runs[:20]:
        summary_cases = db.query(RunCase).filter(RunCase.run_id == r.id).all()
        summary_passed = sum(1 for rc in summary_cases if rc.status == "passed")
        summary_failed = sum(1 for rc in summary_cases if rc.status == "failed")
        summary_error = sum(1 for rc in summary_cases if rc.status == "error")
        summary_skipped = sum(1 for rc in summary_cases if rc.status == "skipped")
        run_summaries.append({
            "run_id": r.id, "status": r.status,
            "total": r.total_cases or len(summary_cases),
            "executed": len(summary_cases),
            "passed": summary_passed,
            "failed": summary_failed,
            "error": summary_error,
            "skipped": summary_skipped,
            "duration": round(r.duration, 2) if r.duration else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })

    run_cases = db.query(RunCase).filter(RunCase.run_id == latest_run_id).all() if latest_run_id else []
    executed_cases = len(run_cases)
    passed_cases = sum(1 for rc in run_cases if rc.status == "passed")
    failed_cases = sum(1 for rc in run_cases if rc.status == "failed")
    error_cases = sum(1 for rc in run_cases if rc.status == "error")
    skipped_cases = sum(1 for rc in run_cases if rc.status == "skipped")
    no_assertion_cases = sum(1 for rc in run_cases if rc.status == "no_assertion")

    if latest_execution_set_id:
        total_cases = db.query(func.count(IterationExecutionSetCase.id)).filter(
            IterationExecutionSetCase.execution_set_id == latest_execution_set_id
        ).scalar() or 0
    elif latest_run:
        total_cases = latest_run.total_cases or executed_cases
    else:
        total_cases = 0
    pass_rate = round(passed_cases / executed_cases * 100, 1) if executed_cases > 0 else 0.0

    if not latest_run_id or executed_cases == 0:
        exec_sets = db.query(IterationExecutionSet).filter(
            IterationExecutionSet.iteration_id == iteration_id
        ).order_by(IterationExecutionSet.created_at.desc()).all()
        reqs = db.query(IterationRequirement).filter(
            IterationRequirement.iteration_id == iteration_id
        ).all()
        return {
            "data_source": "real_run_case",
            "empty": True,
            "message": "暂无真实执行结果，请先创建执行集并执行测试",
            "latest_run_id": latest_run_id,
            "latest_execution_set_id": latest_execution_set_id,
            "generated_at": datetime.now().isoformat(),
            "has_real_result": False,
            "total_cases": 0,
            "executed_cases": 0,
            "passed_cases": 0,
            "failed_cases": 0,
            "error_cases": 0,
            "skipped_cases": 0,
            "no_assertion_cases": 0,
            "pass_rate": 0,
            "failure_categories": {},
            "risk_summary": {},
            "release_recommendation": "block",
            "release_reason": "暂无真实执行结果，请先创建执行集并执行测试",
            "iteration": _iter_dict(it),
            "stats": {
                "total_cases": 0,
                "executed_cases": 0,
                "passed_cases": 0,
                "failed_cases": 0,
                "error_cases": 0,
                "skipped_cases": 0,
                "no_assertion_cases": 0,
                "pass_rate": 0,
            },
            "runs": run_summaries,
            "execution_sets": [_es_dict(es) for es in exec_sets],
            "requirement_count": len(reqs),
            "requirements": [{"id": r.id, "title": r.title, "risk_level": r.risk_level} for r in reqs],
        }

    # Failure categories from RunCase
    failure_categories = {}
    for rc in run_cases:
        if rc.status in ("failed", "error"):
            cat = rc.error_type
            if not cat and rc.status == "failed":
                cat = "assertion_error"
            if not cat and rc.status == "error":
                cat = "unknown_error"
            if rc.test_case and rc.test_case.failure_category:
                cat = rc.test_case.failure_category
            failure_categories[cat] = failure_categories.get(cat, 0) + 1

    # Risk summary: check P0/P1 failures
    p0_failed = 0
    p1_failed = 0
    for rc in run_cases:
        if rc.status in ("failed", "error") and rc.test_case:
            rl = (rc.test_case.risk_level or "").upper()
            if rl == "P0":
                p0_failed += 1
            elif rl == "P1":
                p1_failed += 1

    risk_summary = {
        "p0_failed": p0_failed, "p1_failed": p1_failed,
        "error_cases": error_cases,
        "total_failed": failed_cases + error_cases,
    }

    # Release recommendation
    if latest_execution_set and latest_execution_set.status == "error":
        release_recommendation = "block"
        rec_reason = "执行集状态为 error，请先修复执行环境或用例参数"
    elif error_cases > 0:
        release_recommendation = "block"
        rec_reason = f"存在 {error_cases} 个执行错误，请先配置测试环境或检查用例执行参数"
    elif p0_failed > 0 or p1_failed > 0:
        release_recommendation = "block"
        rec_reason = f"P0失败 {p0_failed} 个, P1失败 {p1_failed} 个"
    elif failed_cases == 0 and pass_rate >= 95:
        release_recommendation = "pass"
        rec_reason = f"通过率 {pass_rate}%，无失败"
    elif failed_cases > 0:
        release_recommendation = "conditional_pass"
        rec_reason = f"有 {failed_cases} 个失败，但无 P0/P1 失败"
    else:
        release_recommendation = "pass"
        rec_reason = f"通过率 {pass_rate}%"

    # Execution sets
    exec_sets = db.query(IterationExecutionSet).filter(
        IterationExecutionSet.iteration_id == iteration_id
    ).order_by(IterationExecutionSet.created_at.desc()).all()

    reqs = db.query(IterationRequirement).filter(
        IterationRequirement.iteration_id == iteration_id
    ).all()

    return {
        "data_source": "real_run_case",
        "empty": False,
        "message": "",
        "latest_run_id": latest_run_id,
        "latest_execution_set_id": latest_execution_set_id,
        "generated_at": datetime.now().isoformat(),
        "has_real_result": bool(latest_run_id and executed_cases > 0),
        "total_cases": total_cases,
        "executed_cases": executed_cases,
        "passed_cases": passed_cases,
        "failed_cases": failed_cases,
        "error_cases": error_cases,
        "skipped_cases": skipped_cases,
        "no_assertion_cases": no_assertion_cases,
        "pass_rate": pass_rate,
        "failure_categories": failure_categories,
        "risk_summary": risk_summary,
        "release_recommendation": release_recommendation,
        "release_reason": rec_reason,
        "iteration": _iter_dict(it),
        "stats": {
            "total_cases": total_cases,
            "executed_cases": executed_cases,
            "passed_cases": passed_cases,
            "failed_cases": failed_cases,
            "error_cases": error_cases,
            "skipped_cases": skipped_cases,
            "no_assertion_cases": no_assertion_cases,
            "pass_rate": pass_rate,
        },
        "runs": run_summaries,
        "execution_sets": [_es_dict(es) for es in exec_sets],
        "requirement_count": len(reqs),
        "requirements": [{"id": r.id, "title": r.title, "risk_level": r.risk_level} for r in reqs],
    }
