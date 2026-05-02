"""
Phase 16: 用例治理 + 推荐测试集路由

POST /api/v2/test-cases/govern           批量治理（打标签）
GET  /api/v2/test-cases/governance-summary   治理概况
GET  /api/v2/test-cases/recommended/smoke        冒烟测试集
GET  /api/v2/test-cases/recommended/regression   回归测试集
GET  /api/v2/test-cases/recommended/query-safe   查询安全集
GET  /api/v2/test-cases/recommended/failed-rerun 失败重跑集
GET  /api/v2/test-cases/recommended/p0           P0测试集
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.session import get_db
from database.models import TestCase
from services.case_governance_service import CaseGovernanceService

router = APIRouter(prefix="/api/v2/test-cases", tags=["CaseGovernance"])


# ── 请求/响应模型 ────────────────────────────────────────

class GovernRequest(BaseModel):
    force: bool = Field(False, description="是否强制覆盖已有标签")


class GovernResponse(BaseModel):
    success: bool
    total: int
    updated: int
    patterns: dict
    risk_levels: dict


class CaseBrief(BaseModel):
    id: str
    title: str
    module: Optional[str] = None
    module_name: Optional[str] = None
    api_pattern: Optional[str] = None
    risk_level: Optional[str] = None
    destructive: Optional[bool] = None
    assertion_status: Optional[str] = None
    last_run_status: Optional[str] = None
    failure_category: Optional[str] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True


class RecommendedSetResponse(BaseModel):
    preset: str
    total: int
    case_ids: List[str]
    cases: List[CaseBrief]


class GovernanceSummaryResponse(BaseModel):
    total: int
    governed: int
    ungoverned: int
    pattern_counts: dict
    risk_counts: dict
    destructive_count: int
    no_assertion_count: int
    failed_count: int


class TestCaseUpdateRequest(BaseModel):
    title: Optional[str] = None
    steps: Optional[list] = None
    expected: Optional[str] = None
    assertions: Optional[list] = None
    execution_config: Optional[dict] = None
    priority: Optional[str] = None
    module: Optional[str] = None
    data_type: Optional[str] = None
    status: Optional[str] = None
    case_type: Optional[str] = None


# ── 路由 ─────────────────────────────────────────────────

@router.put("/{case_id}", summary="更新测试用例")
async def update_test_case(
    case_id: str,
    req: TestCaseUpdateRequest,
    db: Session = Depends(get_db),
):
    """更新单条测试用例的字段"""
    from services.test_case_service import TestCaseService
    svc = TestCaseService(db)
    update_data = {k: v for k, v in req.dict().items() if v is not None}
    if not update_data:
        return {"success": False, "message": "没有要更新的字段"}
    tc = svc.update_test_case(case_id, update_data)
    if not tc:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"用例 {case_id} 不存在")
    return {
        "success": True,
        "message": f"用例 {case_id} 已更新",
        "updated_fields": list(update_data.keys()),
    }


@router.post("/govern", response_model=GovernResponse)
async def govern_test_cases(
    req: GovernRequest = GovernRequest(),
    db: Session = Depends(get_db),
):
    """批量治理：自动给所有用例打标签（api_pattern / risk_level / destructive 等）"""
    svc = CaseGovernanceService(db)
    stats = svc.govern_all(force=req.force)
    return GovernResponse(
        success=True,
        total=stats['total'],
        updated=stats['updated'],
        patterns=stats['patterns'],
        risk_levels=stats['risk_levels'],
    )


@router.get("/governance-summary", response_model=GovernanceSummaryResponse)
async def get_governance_summary(db: Session = Depends(get_db)):
    """获取治理概况统计"""
    svc = CaseGovernanceService(db)
    return svc.get_governance_summary()


def _cases_to_response(preset: str, cases: list) -> RecommendedSetResponse:
    briefs = []
    for tc in cases:
        briefs.append(CaseBrief(
            id=tc.id,
            title=tc.title or '',
            module=tc.module,
            module_name=tc.module_name,
            api_pattern=tc.api_pattern,
            risk_level=tc.risk_level,
            destructive=tc.destructive,
            assertion_status=tc.assertion_status,
            last_run_status=tc.last_run_status,
            failure_category=tc.failure_category,
            status=tc.status,
        ))
    return RecommendedSetResponse(
        preset=preset,
        total=len(briefs),
        case_ids=[b.id for b in briefs],
        cases=briefs,
    )


@router.get("/recommended/smoke", response_model=RecommendedSetResponse)
async def recommended_smoke(
    limit: int = Query(200, ge=1, le=2000),
    db: Session = Depends(get_db),
):
    """冒烟测试集: P0+P1、非破坏性"""
    svc = CaseGovernanceService(db)
    cases = svc.recommend_smoke(limit)
    return _cases_to_response('smoke', cases)


@router.get("/recommended/regression", response_model=RecommendedSetResponse)
async def recommended_regression(
    limit: int = Query(500, ge=1, le=5000),
    db: Session = Depends(get_db),
):
    """回归测试集: 所有可执行+非破坏性"""
    svc = CaseGovernanceService(db)
    cases = svc.recommend_regression(limit)
    return _cases_to_response('regression', cases)


@router.get("/recommended/query-safe", response_model=RecommendedSetResponse)
async def recommended_query_safe(
    limit: int = Query(500, ge=1, le=5000),
    db: Session = Depends(get_db),
):
    """查询安全集: list/page/detail 类"""
    svc = CaseGovernanceService(db)
    cases = svc.recommend_query_safe(limit)
    return _cases_to_response('query-safe', cases)


@router.get("/recommended/failed-rerun", response_model=RecommendedSetResponse)
async def recommended_failed_rerun(
    limit: int = Query(500, ge=1, le=5000),
    db: Session = Depends(get_db),
):
    """失败重跑集"""
    svc = CaseGovernanceService(db)
    cases = svc.recommend_failed_rerun(limit)
    return _cases_to_response('failed-rerun', cases)


@router.get("/recommended/p0", response_model=RecommendedSetResponse)
async def recommended_p0(
    limit: int = Query(200, ge=1, le=2000),
    db: Session = Depends(get_db),
):
    """P0 测试集"""
    svc = CaseGovernanceService(db)
    cases = svc.recommend_p0(limit)
    return _cases_to_response('p0', cases)


# ── 增强查询：支持治理字段筛选 ────────────────────────────

class FilteredCaseListResponse(BaseModel):
    total: int
    test_cases: List[CaseBrief]


@router.get("/filtered", response_model=FilteredCaseListResponse)
async def get_filtered_test_cases(
    status: Optional[str] = Query(None, description="passed/failed/pending/no_assertion/error"),
    risk_level: Optional[str] = Query(None, description="P0/P1/P2"),
    api_pattern: Optional[str] = Query(None, description="list/page/detail/save/modify/delete/unknown"),
    destructive: Optional[bool] = Query(None),
    assertion_status: Optional[str] = Query(None, description="has_assertion/no_assertion"),
    module_name: Optional[str] = Query(None),
    failure_category: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None, description="标题关键字搜索"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=2000),
    db: Session = Depends(get_db),
):
    """带治理字段筛选的用例查询"""
    query = db.query(TestCase)
    filters = []

    if status:
        filters.append(TestCase.status == status)
    if risk_level:
        filters.append(TestCase.risk_level == risk_level)
    if api_pattern:
        filters.append(TestCase.api_pattern == api_pattern)
    if destructive is not None:
        filters.append(TestCase.destructive == destructive)
    if assertion_status:
        filters.append(TestCase.assertion_status == assertion_status)
    if module_name:
        filters.append(TestCase.module_name.like(f'%{module_name}%'))
    if failure_category:
        filters.append(TestCase.failure_category == failure_category)
    if keyword:
        filters.append(TestCase.title.like(f'%{keyword}%'))

    if filters:
        query = query.filter(and_(*filters))

    total = query.count()
    cases = query.offset(skip).limit(limit).all()

    briefs = [CaseBrief(
        id=tc.id,
        title=tc.title or '',
        module=tc.module,
        module_name=tc.module_name,
        api_pattern=tc.api_pattern,
        risk_level=tc.risk_level,
        destructive=tc.destructive,
        assertion_status=tc.assertion_status,
        last_run_status=tc.last_run_status,
        failure_category=tc.failure_category,
        status=tc.status,
    ) for tc in cases]

    return FilteredCaseListResponse(total=total, test_cases=briefs)
