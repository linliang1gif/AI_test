"""
AI Product Studio Phase 3 — 质量评分 + 重复检测 服务
规则评分，不依赖 LLM。
"""

import re
import difflib
import logging
from typing import Dict, Any, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc

from database.models import (
    ProductArtifact, ProductArtifactTraceLink, RequirementPoint, TestCase,
)

logger = logging.getLogger("product_studio_quality")


# ══════════════════════════════════════════════════════════════════
#  文本归一化
# ══════════════════════════════════════════════════════════════════

def _normalize(text: str) -> str:
    """归一化：小写 + 去标点 + 去多余空格"""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\u4e00-\u9fff]', '', text)
    return text.strip()


def _text_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


# ══════════════════════════════════════════════════════════════════
#  RequirementPoint 评分
# ══════════════════════════════════════════════════════════════════

def score_requirement_point(rp: RequirementPoint) -> Dict[str, Any]:
    """对 RequirementPoint 进行规则评分"""
    reasons = []
    score = 0.0

    # 1. clear_title (0.25)
    title = (rp.title or "").strip()
    if len(title) >= 5:
        score += 0.25
    elif len(title) >= 2:
        score += 0.15
        reasons.append("标题较短，建议更具体")
    else:
        reasons.append("标题过短或缺失")

    # 2. business_value (0.20) — stored in keywords_json[0]
    kw = rp.keywords_json or []
    bv = kw[0] if len(kw) > 0 else ""
    if bv and len(str(bv).strip()) > 3:
        score += 0.20
    else:
        reasons.append("缺少业务价值说明")

    # 3. testability (0.20) — description length
    desc_text = (rp.description or "").strip()
    if len(desc_text) >= 20:
        score += 0.20
    elif len(desc_text) >= 5:
        score += 0.10
        reasons.append("描述较简短，可测试性待提升")
    else:
        reasons.append("缺少详细描述，可测试性不足")

    # 4. acceptance_hint (0.20) — stored in keywords_json[2]
    ah = kw[2] if len(kw) > 2 else ""
    if ah and len(str(ah).strip()) > 3:
        score += 0.20
    else:
        reasons.append("缺少验收提示")

    # 5. risk_level_reasonable (0.15) — module_name stores risk_level
    risk = (rp.module_name or "").strip()
    if risk in ("P0", "P1", "P2"):
        score += 0.15
    elif risk:
        score += 0.05
        reasons.append(f"风险等级 '{risk}' 非标准值")
    else:
        reasons.append("缺少风险等级")

    score = round(min(score, 1.0), 2)
    reason = "；".join(reasons) if reasons else "各维度均达标"
    return {"quality_score": score, "quality_reason": reason}


# ══════════════════════════════════════════════════════════════════
#  TestCase 评分
# ══════════════════════════════════════════════════════════════════

def score_test_case(tc: TestCase, duplicate_penalty: float = 0.0) -> Dict[str, Any]:
    """对 TestCase 进行规则评分"""
    reasons = []
    score = 1.0

    steps = tc.steps or []
    has_steps = len(steps) > 0 and any(s.get("action", "") for s in steps if isinstance(s, dict))
    expected = (tc.expected or "").strip()

    if not has_steps:
        score -= 0.10
        reasons.append("缺少测试步骤，扣 0.10")
    elif len(_extract_steps_text(tc)) < 10:
        score -= 0.05
        reasons.append("测试步骤较简略，扣 0.05")

    if not expected:
        score -= 0.10
        reasons.append("缺少明确预期结果，扣 0.10")
    elif len(expected) < 10:
        score -= 0.05
        reasons.append("预期结果较简短，扣 0.05")

    title = (tc.title or "").strip()
    if len(title) < 5:
        score -= 0.05
        reasons.append("用例标题不够明确，扣 0.05")

    priority = (tc.priority or "").strip()
    risk_level = (getattr(tc, "risk_level", "") or "").strip()
    if priority not in ("critical", "high", "medium", "low") or risk_level not in ("P0", "P1", "P2"):
        score -= 0.05
        reasons.append("缺少优先级或风险等级，扣 0.05")

    if not (tc.test_point_id or "").strip():
        score -= 0.25
        reasons.append("未关联需求点，扣 0.25")

    # Apply duplicate penalty
    if duplicate_penalty > 0:
        score = max(0, score - duplicate_penalty)
        reasons.append(f"疑似重复，降分 {duplicate_penalty}")

    score = round(max(0.0, min(score, 1.0)), 2)
    reason = "；".join(reasons) if reasons else "各维度均达标"
    return {"quality_score": score, "quality_reason": reason}


# ══════════════════════════════════════════════════════════════════
#  重复检测
# ══════════════════════════════════════════════════════════════════

def detect_duplicates(tc: TestCase, existing_cases: List[TestCase],
                      title_threshold: float = 0.85,
                      steps_threshold: float = 0.80) -> List[Dict[str, Any]]:
    """检测疑似重复的 TestCase"""
    norm_title = _normalize(tc.title or "")
    tc_steps_text = _normalize(_extract_steps_text(tc))

    candidates = []
    for other in existing_cases:
        if other.id == tc.id:
            continue
        other_norm_title = _normalize(other.title or "")
        title_sim = _text_similarity(norm_title, other_norm_title)

        other_steps_text = _normalize(_extract_steps_text(other))
        steps_sim = _text_similarity(tc_steps_text, other_steps_text) if tc_steps_text and other_steps_text else 0.0

        if title_sim > title_threshold or steps_sim > steps_threshold:
            candidates.append({
                "duplicate_id": other.id,
                "duplicate_title": other.title,
                "title_similarity": round(title_sim, 3),
                "steps_similarity": round(steps_sim, 3),
            })
    return candidates


def _extract_steps_text(tc: TestCase) -> str:
    steps = tc.steps or []
    parts = []
    for s in steps:
        if isinstance(s, dict):
            parts.append(s.get("action", ""))
        elif isinstance(s, str):
            parts.append(s)
    return " ".join(parts)


def score_artifact_quality(db: Session, artifact_id: str) -> Dict[str, Any]:
    """按产物维度计算质量分，覆盖 TraceLink / RP / TC 完整链路。"""
    artifact = db.query(ProductArtifact).filter(ProductArtifact.artifact_id == artifact_id).first()
    if not artifact:
        return {"quality_score": 0.0, "deduction_reasons": [{"code": "ARTIFACT_NOT_FOUND", "message": "产物不存在", "deduction": 1.0}]}

    links = db.query(ProductArtifactTraceLink).filter(
        ProductArtifactTraceLink.artifact_id == artifact_id
    ).all()
    rp_link_ids = [l.target_id for l in links if l.target_type == "requirement_point"]
    tc_link_ids = [l.target_id for l in links if l.target_type == "test_case"]

    rp_query = db.query(RequirementPoint).filter(RequirementPoint.source_id == artifact_id)
    if rp_link_ids:
        rp_query = rp_query.union(db.query(RequirementPoint).filter(RequirementPoint.id.in_(rp_link_ids)))
    rps = rp_query.all()
    rp_ids = [rp.id for rp in rps]

    tcs = []
    if tc_link_ids:
        tcs.extend(db.query(TestCase).filter(TestCase.id.in_(tc_link_ids)).all())
    if rp_ids:
        linked_by_rp = db.query(TestCase).filter(TestCase.test_point_id.in_(rp_ids)).all()
        known = {tc.id for tc in tcs}
        tcs.extend([tc for tc in linked_by_rp if tc.id not in known])

    score = 1.0
    deductions = []

    def deduct(code: str, message: str, value: float):
        nonlocal score
        score -= value
        deductions.append({"code": code, "message": message, "deduction": value})

    if not links:
        deduct("TRACE_LINK_MISSING", "缺少 TraceLink", 0.25)
    if not tcs:
        deduct("TEST_CASE_MISSING", "缺少测试用例", 0.20)
    if not rps:
        deduct("REQUIREMENT_POINT_MISSING", "缺少需求点", 0.20)

    if tcs:
        no_steps = [tc for tc in tcs if not (tc.steps and _extract_steps_text(tc).strip())]
        if no_steps:
            deduct("TEST_CASE_STEPS_MISSING", f"{len(no_steps)} 条用例没有步骤", 0.10)

        no_expected = [tc for tc in tcs if not (tc.expected or "").strip()]
        if no_expected:
            deduct("TEST_CASE_EXPECTED_MISSING", f"{len(no_expected)} 条用例没有预期结果", 0.10)

        no_priority_or_risk = [
            tc for tc in tcs
            if (tc.priority or "") not in ("critical", "high", "medium", "low")
            or (getattr(tc, "risk_level", "") or "") not in ("P0", "P1", "P2")
        ]
        if no_priority_or_risk:
            deduct("TEST_CASE_PRIORITY_RISK_MISSING", f"{len(no_priority_or_risk)} 条用例缺少优先级或风险等级", 0.05)

        has_abnormal = any(
            (tc.case_type or "") == "abnormal"
            or "异常" in (tc.title or "")
            or "失败" in (tc.title or "")
            or "错误" in (tc.title or "")
            for tc in tcs
        )
        if not has_abnormal:
            deduct("ABNORMAL_SCENARIO_MISSING", "缺少异常场景", 0.10)

        duplicate_count = 0
        for tc in tcs:
            others = [other for other in tcs if other.id != tc.id]
            if detect_duplicates(tc, others):
                duplicate_count += 1
        if duplicate_count >= max(2, len(tcs) // 3 + 1):
            deduct("DUPLICATE_CASES_TOO_MANY", f"重复用例过多，疑似 {duplicate_count} 条", 0.10)

    quality_score = round(max(0.0, score), 2)
    warnings = []
    if not links:
        warnings.append("当前产物未建立需求-用例追踪关系，请先生成需求点和测试用例。")

    return {
        "artifact_id": artifact_id,
        "quality_score": quality_score,
        "deduction_reasons": deductions,
        "warnings": warnings,
        "requirement_point_count": len(rps),
        "test_case_count": len(tcs),
        "trace_link_count": len(links),
        "duplicate_candidate_count": duplicate_count if tcs else 0,
    }


# ══════════════════════════════════════════════════════════════════
#  综合评分入口
# ══════════════════════════════════════════════════════════════════

class ProductStudioQualityService:
    def __init__(self, db: Session):
        self.db = db

    def score_trace_link(self, link: ProductArtifactTraceLink) -> Dict[str, Any]:
        """对单个 TraceLink 关联的目标进行评分"""
        duplicate_candidates = []

        if link.target_type == "requirement_point":
            rp = self.db.query(RequirementPoint).filter(
                RequirementPoint.id == link.target_id).first()
            if not rp:
                return {"quality_score": 0.0, "quality_reason": "目标需求点不存在",
                        "duplicate_candidates": []}
            result = score_requirement_point(rp)

        elif link.target_type == "test_case":
            tc = self.db.query(TestCase).filter(
                TestCase.id == link.target_id).first()
            if not tc:
                return {"quality_score": 0.0, "quality_reason": "目标测试用例不存在",
                        "duplicate_candidates": []}
            # Duplicate detection: compare with other test cases from same source
            sibling_ids = [
                lk.target_id for lk in
                self.db.query(ProductArtifactTraceLink).filter(
                    ProductArtifactTraceLink.artifact_id == link.artifact_id,
                    ProductArtifactTraceLink.target_type == "test_case",
                    ProductArtifactTraceLink.link_id != link.link_id,
                ).all()
            ]
            if sibling_ids:
                siblings = self.db.query(TestCase).filter(
                    TestCase.id.in_(sibling_ids)).all()
            else:
                siblings = []
            duplicate_candidates = detect_duplicates(tc, siblings)
            dup_penalty = 0.15 if duplicate_candidates else 0.0
            result = score_test_case(tc, duplicate_penalty=dup_penalty)
        else:
            return {"quality_score": 0.0,
                    "quality_reason": f"不支持的 target_type: {link.target_type}",
                    "duplicate_candidates": []}

        result["duplicate_candidates"] = duplicate_candidates
        return result
