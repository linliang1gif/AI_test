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
    ProductArtifactTraceLink, RequirementPoint, TestCase,
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
    score = 0.0

    # 1. clear_precondition (0.15) — not directly stored; check steps structure
    steps = tc.steps or []
    has_steps = len(steps) > 0 and any(s.get("action", "") for s in steps if isinstance(s, dict))
    # We check expected for precondition hints
    expected = (tc.expected or "").strip()

    # 2. executable_steps (0.25)
    if has_steps:
        first_action = steps[0].get("action", "") if isinstance(steps[0], dict) else ""
        if len(first_action) >= 10:
            score += 0.25
        elif len(first_action) >= 3:
            score += 0.15
            reasons.append("测试步骤较简略")
        else:
            reasons.append("测试步骤缺乏可执行细节")
    else:
        reasons.append("缺少测试步骤")

    # 3. expected_result_clear (0.20)
    if len(expected) >= 10:
        score += 0.20
    elif len(expected) >= 3:
        score += 0.10
        reasons.append("预期结果较简短")
    else:
        reasons.append("缺少明确预期结果")

    # 4. clear_title (0.15)
    title = (tc.title or "").strip()
    if len(title) >= 5:
        score += 0.15
    elif len(title) >= 2:
        score += 0.08
        reasons.append("用例标题较短")
    else:
        reasons.append("用例标题缺失")

    # 5. source_traceable (0.10) — module field holds source_artifact_section
    module = (tc.module or "").strip()
    if module and len(module) >= 2:
        score += 0.10
    else:
        reasons.append("缺少来源章节追溯")

    # 6. assertion_value (0.15) — has expected + priority
    priority = (tc.priority or "").strip()
    if expected and priority in ("critical", "high", "medium", "low"):
        score += 0.15
    elif expected:
        score += 0.08
        reasons.append("优先级标注不规范")
    else:
        reasons.append("缺少断言价值")

    # Apply duplicate penalty
    if duplicate_penalty > 0:
        score = max(0, score - duplicate_penalty)
        reasons.append(f"疑似重复，降分 {duplicate_penalty}")

    score = round(min(score, 1.0), 2)
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
