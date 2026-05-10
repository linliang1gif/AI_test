"""
AI Product Studio — 服务层
职责: CRUD + AI 生成 + Artifact 管理
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import desc

import json
import re

from database.models import (
    ProductIdea, ProductStudioRun, ProductArtifact,
    ProductArtifactTraceLink, RequirementPoint, TestCase,
)
from services.product_studio_prompts import (
    PROMPT_BUILDERS, MAX_TOKENS_MAP, ARTIFACT_TITLE_MAP,
    build_requirement_points_from_artifact_prompt,
    build_test_cases_from_artifact_prompt,
)
from services.sanitize import sanitize_text

logger = logging.getLogger("product_studio")

ARTIFACT_TYPES = ["product_solution", "prd", "prototype", "test_strategy", "acceptance_criteria"]


def _uid() -> str:
    return uuid.uuid4().hex[:16]


def _now() -> datetime:
    return datetime.now()


# ══════════════════════════════════════════════════════════════════
#  Artifact Summary 动态计算
# ══════════════════════════════════════════════════════════════════

def _build_artifact_summary(db: Session, idea_id: str) -> Dict[str, Any]:
    arts = db.query(ProductArtifact).filter(ProductArtifact.idea_id == idea_id).all()
    types_present = {a.artifact_type for a in arts}
    latest_at = max((a.created_at for a in arts), default=None)
    return {
        "has_solution": "product_solution" in types_present,
        "has_prd": "prd" in types_present,
        "has_prototype": "prototype" in types_present,
        "has_test_strategy": "test_strategy" in types_present,
        "has_acceptance_criteria": "acceptance_criteria" in types_present,
        "latest_artifact_at": latest_at.isoformat() if latest_at else None,
    }


def _idea_to_dict(idea: ProductIdea) -> Dict[str, Any]:
    return {
        "idea_id": idea.idea_id,
        "project_id": idea.project_id,
        "title": idea.title,
        "product_direction": idea.product_direction,
        "target_users": idea.target_users,
        "pain_points": idea.pain_points,
        "existing_assets": idea.existing_assets,
        "current_blockers": idea.current_blockers,
        "constraints": idea.constraints,
        "status": idea.status,
        "created_at": idea.created_at.isoformat() if idea.created_at else None,
        "updated_at": idea.updated_at.isoformat() if idea.updated_at else None,
    }


def _artifact_to_dict(a: ProductArtifact) -> Dict[str, Any]:
    return {
        "artifact_id": a.artifact_id,
        "idea_id": a.idea_id,
        "run_id": a.run_id,
        "artifact_type": a.artifact_type,
        "title": a.title,
        "content_markdown": a.content_markdown,
        "content_json": a.content_json,
        "status": a.status,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
    }


def _run_to_dict(r: ProductStudioRun) -> Dict[str, Any]:
    return {
        "run_id": r.run_id,
        "idea_id": r.idea_id,
        "run_type": r.run_type,
        "status": r.status,
        "model_name": r.model_name,
        "token_input": r.token_input,
        "token_output": r.token_output,
        "cost_estimate": r.cost_estimate,
        "trace_id": r.trace_id,
        "error_message": r.error_message,
        "started_at": r.started_at.isoformat() if r.started_at else None,
        "finished_at": r.finished_at.isoformat() if r.finished_at else None,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


# ══════════════════════════════════════════════════════════════════
#  LLM 调用封装（复用 agent/llm_client.py）
# ══════════════════════════════════════════════════════════════════

def _call_llm(prompt: str, max_tokens: int = 8000, provider: str = None, model: str = None):
    """调用 LLM，返回 (text, model_name, is_mock)"""
    try:
        from agent.llm_client import get_llm_client
        client = get_llm_client(provider=provider, model=model)
        model_name = f"{client.provider}/{client.model}"
        is_mock = client.provider == "mock"

        text = client.generate(
            prompt=prompt,
            system_prompt="你是 AI Product Studio 的智能助手，请按要求输出结构化 Markdown。",
            temperature=0.3,
            max_tokens=max_tokens,
        )
        return text, model_name, is_mock
    except Exception as e:
        raise RuntimeError(f"LLM 调用失败: {sanitize_text(str(e))}")


# ══════════════════════════════════════════════════════════════════
#  CRUD
# ══════════════════════════════════════════════════════════════════

class ProductStudioService:
    def __init__(self, db: Session):
        self.db = db

    # ── 创建想法 ──
    def create_idea(self, data: Dict[str, Any]) -> Dict[str, Any]:
        idea_id = f"idea_{_uid()}"
        idea = ProductIdea(
            idea_id=idea_id,
            project_id=data.get("project_id"),
            title=data.get("title", "").strip(),
            product_direction=data.get("product_direction", ""),
            target_users=data.get("target_users", ""),
            pain_points=data.get("pain_points", ""),
            existing_assets=data.get("existing_assets", ""),
            current_blockers=data.get("current_blockers", ""),
            constraints=data.get("constraints", ""),
            status="created",
        )
        self.db.add(idea)
        self.db.commit()
        self.db.refresh(idea)
        return {"idea_id": idea_id, "status": "created"}

    # ── 列表 ──
    def list_ideas(self, keyword: str = None, project_id: int = None,
                   page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        q = self.db.query(ProductIdea)
        if keyword:
            q = q.filter(ProductIdea.title.contains(keyword))
        if project_id is not None:
            q = q.filter(ProductIdea.project_id == project_id)
        total = q.count()
        ideas = q.order_by(desc(ProductIdea.created_at)).offset((page - 1) * page_size).limit(page_size).all()
        items = []
        for idea in ideas:
            d = _idea_to_dict(idea)
            d["artifact_summary"] = _build_artifact_summary(self.db, idea.idea_id)
            items.append(d)
        return {"total": total, "page": page, "page_size": page_size, "items": items}

    # ── 详情 ──
    def get_idea_detail(self, idea_id: str) -> Optional[Dict[str, Any]]:
        idea = self.db.query(ProductIdea).filter(ProductIdea.idea_id == idea_id).first()
        if not idea:
            return None
        d = _idea_to_dict(idea)
        d["artifact_summary"] = _build_artifact_summary(self.db, idea_id)
        d["artifacts"] = [
            _artifact_to_dict(a) for a in
            self.db.query(ProductArtifact).filter(ProductArtifact.idea_id == idea_id)
            .order_by(desc(ProductArtifact.created_at)).all()
        ]
        d["runs"] = [
            _run_to_dict(r) for r in
            self.db.query(ProductStudioRun).filter(ProductStudioRun.idea_id == idea_id)
            .order_by(desc(ProductStudioRun.created_at)).all()
        ]
        return d

    # ── 获取 Artifact ──
    def get_artifact(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        a = self.db.query(ProductArtifact).filter(ProductArtifact.artifact_id == artifact_id).first()
        if not a:
            return None
        return _artifact_to_dict(a)

    # ── 更新 Artifact ──
    def update_artifact(self, artifact_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        a = self.db.query(ProductArtifact).filter(ProductArtifact.artifact_id == artifact_id).first()
        if not a:
            return None
        if "title" in data:
            a.title = data["title"]
        if "content_markdown" in data:
            a.content_markdown = data["content_markdown"]
        if "status" in data and data["status"] in ("draft", "confirmed", "archived"):
            a.status = data["status"]
        a.updated_at = _now()
        self.db.commit()
        self.db.refresh(a)
        return _artifact_to_dict(a)

    # ── 获取 Run ──
    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        r = self.db.query(ProductStudioRun).filter(ProductStudioRun.run_id == run_id).first()
        if not r:
            return None
        return _run_to_dict(r)

    # ── 导出 Artifact ──
    def export_artifact(self, artifact_id: str) -> Optional[Dict[str, str]]:
        a = self.db.query(ProductArtifact).filter(ProductArtifact.artifact_id == artifact_id).first()
        if not a:
            return None
        filename = f"{a.artifact_type}_{a.artifact_id}.md"
        return {"filename": filename, "content": a.content_markdown or ""}

    # ══════════════════════════════════════════════════════════════
    #  AI 生成（统一流程）
    # ══════════════════════════════════════════════════════════════

    def generate(self, idea_id: str, run_type: str,
                 provider: str = None, model: str = None) -> Dict[str, Any]:
        """统一生成入口"""
        if run_type not in ARTIFACT_TYPES:
            raise ValueError(f"不支持的 run_type: {run_type}")

        # 1. 获取 Idea
        idea = self.db.query(ProductIdea).filter(ProductIdea.idea_id == idea_id).first()
        if not idea:
            raise ValueError(f"产品想法不存在: {idea_id}")

        idea_dict = _idea_to_dict(idea)

        # 2. 收集已有 Artifact 上下文
        existing_artifacts: Dict[str, str] = {}
        for at in ARTIFACT_TYPES:
            latest = (
                self.db.query(ProductArtifact)
                .filter(ProductArtifact.idea_id == idea_id, ProductArtifact.artifact_type == at)
                .order_by(desc(ProductArtifact.created_at))
                .first()
            )
            if latest and latest.content_markdown:
                existing_artifacts[at] = latest.content_markdown

        # 3. 构建 Prompt
        builder = PROMPT_BUILDERS.get(run_type)
        if not builder:
            raise ValueError(f"未找到 {run_type} 的 Prompt 模板")
        prompt = builder(idea_dict, existing_artifacts)

        # 4. 创建 Run
        run_id = f"run_{_uid()}"
        trace_id = f"trace_{_uid()}"
        max_tokens = MAX_TOKENS_MAP.get(run_type, 8000)

        run = ProductStudioRun(
            run_id=run_id,
            idea_id=idea_id,
            run_type=run_type,
            input_payload={"prompt_length": len(prompt)},
            status="running",
            trace_id=trace_id,
            started_at=_now(),
        )
        self.db.add(run)
        self.db.commit()

        # 5. 调用 LLM
        artifact_id = f"art_{_uid()}"
        try:
            text, model_name, is_mock = _call_llm(prompt, max_tokens=max_tokens,
                                                   provider=provider, model=model)
            run.model_name = model_name

            if not text or not text.strip():
                raise RuntimeError("LLM 返回空内容")

            # 截断检测
            truncated = False
            if len(text) > max_tokens * 3:  # rough char estimate
                truncated = True

            run.output_text = text
            run.status = "succeeded"
            run.finished_at = _now()

            if is_mock:
                run.model_name = f"mock/{run.model_name}"

            # 6. 创建 Artifact
            title = ARTIFACT_TITLE_MAP.get(run_type, run_type)
            if is_mock:
                title = f"[Mock] {title}"
            if truncated:
                text += "\n\n---\n> ⚠️ 内容可能被截断，建议检查完整性。\n"

            artifact = ProductArtifact(
                artifact_id=artifact_id,
                idea_id=idea_id,
                run_id=run_id,
                artifact_type=run_type,
                title=title,
                content_markdown=text,
                status="draft",
            )
            self.db.add(artifact)
            self.db.commit()

            return {
                "run_id": run_id,
                "artifact_id": artifact_id,
                "status": "succeeded",
                "artifact_type": run_type,
                "trace_id": trace_id,
                "is_mock": is_mock,
            }

        except Exception as e:
            error_msg = sanitize_text(str(e))
            run.status = "failed"
            run.error_message = error_msg[:2000]
            run.finished_at = _now()
            self.db.commit()
            logger.error(f"Product Studio generate failed: {error_msg}")
            return {
                "run_id": run_id,
                "artifact_id": None,
                "status": "failed",
                "artifact_type": run_type,
                "trace_id": trace_id,
                "error_message": error_msg[:500],
                "is_mock": False,
            }

    # ══════════════════════════════════════════════════════════════
    #  Phase 2: Artifact → 测试资产 打通
    # ══════════════════════════════════════════════════════════════

    VALID_RP_TYPES = {"prd", "product_solution"}
    VALID_TC_TYPES = {"prd", "test_strategy", "acceptance_criteria"}

    def generate_requirement_points(self, artifact_id: str) -> Dict[str, Any]:
        """从 Artifact 提取需求点草稿"""
        artifact = self.db.query(ProductArtifact).filter(
            ProductArtifact.artifact_id == artifact_id).first()
        if not artifact:
            raise ValueError(f"Artifact 不存在: {artifact_id}")
        if artifact.artifact_type not in self.VALID_RP_TYPES:
            raise TypeError(
                f"artifact_type={artifact.artifact_type} 不支持生成需求点，"
                f"仅支持: {', '.join(self.VALID_RP_TYPES)}")

        content = artifact.content_markdown or ""
        if not content.strip():
            raise ValueError("Artifact 内容为空，无法提取需求点")

        # 创建 Run
        run_id = f"run_{_uid()}"
        trace_id = f"trace_{_uid()}"
        max_tokens = MAX_TOKENS_MAP.get("requirement_points_from_artifact", 8000)
        run = ProductStudioRun(
            run_id=run_id, idea_id=artifact.idea_id,
            run_type="requirement_points_from_artifact",
            input_payload={"artifact_id": artifact_id},
            status="running", trace_id=trace_id, started_at=_now(),
        )
        self.db.add(run)
        self.db.commit()

        try:
            prompt = build_requirement_points_from_artifact_prompt(
                content, artifact.artifact_type)
            text, model_name, is_mock = _call_llm(prompt, max_tokens=max_tokens)
            run.model_name = model_name
            run.output_text = text

            items = _parse_json_array(text)
            if not items:
                raise RuntimeError("LLM 未返回有效 JSON 数组")

            rps = []
            links = []
            for item in items:
                rp_id = f"RP_PS_{_uid()}"
                rp = RequirementPoint(
                    id=rp_id,
                    project_id=None,
                    source_type="ai_product_studio",
                    source_id=artifact_id,
                    point_type="feature",
                    title=item.get("requirement_title", "未命名需求点")[:500],
                    description=item.get("requirement_description", ""),
                    keywords_json=[
                        item.get("business_value", ""),
                        item.get("source_section", ""),
                        item.get("acceptance_hint", ""),
                    ],
                    priority=item.get("priority", "medium"),
                    module_name=item.get("risk_level", ""),
                )
                self.db.add(rp)

                link_id = f"link_{_uid()}"
                link = ProductArtifactTraceLink(
                    link_id=link_id, artifact_id=artifact_id,
                    source_artifact_type=artifact.artifact_type,
                    target_type="requirement_point", target_id=rp_id,
                    generation_run_id=run_id, confidence_score=0.8,
                    status="draft",
                )
                self.db.add(link)
                rps.append({"id": rp_id, "title": rp.title,
                            "priority": rp.priority, "status": "draft"})
                links.append({"link_id": link_id, "target_type": "requirement_point",
                              "target_id": rp_id, "status": "draft"})

            run.status = "succeeded"
            run.finished_at = _now()
            self.db.commit()
            return {
                "run_id": run_id, "trace_id": trace_id,
                "generated_count": len(rps),
                "requirement_points": rps, "trace_links": links,
                "is_mock": is_mock,
            }
        except Exception as e:
            error_msg = sanitize_text(str(e))
            run.status = "failed"
            run.error_message = error_msg[:2000]
            run.finished_at = _now()
            self.db.commit()
            logger.error(f"generate_requirement_points failed: {error_msg}")
            return {
                "run_id": run_id, "trace_id": trace_id,
                "generated_count": 0,
                "requirement_points": [], "trace_links": [],
                "error_message": error_msg[:500],
                "is_mock": False,
            }

    def generate_test_cases(self, artifact_id: str) -> Dict[str, Any]:
        """从 Artifact 生成测试用例草稿"""
        artifact = self.db.query(ProductArtifact).filter(
            ProductArtifact.artifact_id == artifact_id).first()
        if not artifact:
            raise ValueError(f"Artifact 不存在: {artifact_id}")
        if artifact.artifact_type not in self.VALID_TC_TYPES:
            raise TypeError(
                f"artifact_type={artifact.artifact_type} 不支持生成测试用例，"
                f"仅支持: {', '.join(self.VALID_TC_TYPES)}")

        content = artifact.content_markdown or ""
        if not content.strip():
            raise ValueError("Artifact 内容为空，无法生成测试用例")

        run_id = f"run_{_uid()}"
        trace_id = f"trace_{_uid()}"
        max_tokens = MAX_TOKENS_MAP.get("test_cases_from_artifact", 10000)
        run = ProductStudioRun(
            run_id=run_id, idea_id=artifact.idea_id,
            run_type="test_cases_from_artifact",
            input_payload={"artifact_id": artifact_id},
            status="running", trace_id=trace_id, started_at=_now(),
        )
        self.db.add(run)
        self.db.commit()

        try:
            prompt = build_test_cases_from_artifact_prompt(
                content, artifact.artifact_type)
            text, model_name, is_mock = _call_llm(prompt, max_tokens=max_tokens)
            run.model_name = model_name
            run.output_text = text

            items = _parse_json_array(text)
            if not items:
                raise RuntimeError("LLM 未返回有效 JSON 数组")

            VALID_CASE_TYPES = {"functional", "api", "ui", "abnormal", "ai_quality"}
            tcs = []
            links = []
            for item in items:
                tc_id = f"TC_PS_{_uid()}"
                case_type = item.get("case_type", "functional")
                if case_type not in VALID_CASE_TYPES:
                    case_type = "functional"
                priority = item.get("priority", "medium")
                if priority not in {"critical", "high", "medium", "low"}:
                    priority = "medium"

                steps_text = item.get("test_steps", "")
                steps_json = [{"step": 1, "action": steps_text}] if steps_text else []

                tc = TestCase(
                    id=tc_id,
                    title=item.get("case_title", "未命名用例")[:500],
                    module=item.get("source_artifact_section", ""),
                    priority=priority,
                    status="draft",
                    steps=steps_json,
                    expected=item.get("expected_result", ""),
                    case_type=case_type,
                    source="ai_product_studio",
                    created_by="ai_product_studio",
                    tags=["product_studio", artifact.artifact_type],
                )
                self.db.add(tc)

                link_id = f"link_{_uid()}"
                link = ProductArtifactTraceLink(
                    link_id=link_id, artifact_id=artifact_id,
                    source_artifact_type=artifact.artifact_type,
                    target_type="test_case", target_id=tc_id,
                    generation_run_id=run_id, confidence_score=0.75,
                    status="draft",
                )
                self.db.add(link)
                tcs.append({"id": tc_id, "title": tc.title,
                            "case_type": case_type, "priority": priority,
                            "status": "draft"})
                links.append({"link_id": link_id, "target_type": "test_case",
                              "target_id": tc_id, "status": "draft"})

            run.status = "succeeded"
            run.finished_at = _now()
            self.db.commit()
            return {
                "run_id": run_id, "trace_id": trace_id,
                "generated_count": len(tcs),
                "test_cases": tcs, "trace_links": links,
                "is_mock": is_mock,
            }
        except Exception as e:
            error_msg = sanitize_text(str(e))
            run.status = "failed"
            run.error_message = error_msg[:2000]
            run.finished_at = _now()
            self.db.commit()
            logger.error(f"generate_test_cases failed: {error_msg}")
            return {
                "run_id": run_id, "trace_id": trace_id,
                "generated_count": 0,
                "test_cases": [], "trace_links": [],
                "error_message": error_msg[:500],
                "is_mock": False,
            }

    def get_trace_links(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """查看 Artifact 追溯链路"""
        artifact = self.db.query(ProductArtifact).filter(
            ProductArtifact.artifact_id == artifact_id).first()
        if not artifact:
            return None
        links = self.db.query(ProductArtifactTraceLink).filter(
            ProductArtifactTraceLink.artifact_id == artifact_id
        ).order_by(desc(ProductArtifactTraceLink.created_at)).all()

        rps = []
        tcs = []
        link_dicts = []
        for lk in links:
            ld = {
                "link_id": lk.link_id, "artifact_id": lk.artifact_id,
                "source_artifact_type": lk.source_artifact_type,
                "target_type": lk.target_type, "target_id": lk.target_id,
                "generation_run_id": lk.generation_run_id,
                "confidence_score": lk.confidence_score,
                "status": lk.status,
                "quality_score": lk.quality_score,
                "quality_reason": lk.quality_reason,
                "review_reason": lk.review_reason,
                "promoted_at": lk.promoted_at.isoformat() if lk.promoted_at else None,
                "promoted_target_id": lk.promoted_target_id,
                "created_at": lk.created_at.isoformat() if lk.created_at else None,
            }
            link_dicts.append(ld)
            if lk.target_type == "requirement_point":
                rp = self.db.query(RequirementPoint).filter(
                    RequirementPoint.id == lk.target_id).first()
                if rp:
                    rps.append({"id": rp.id, "title": rp.title,
                                "priority": rp.priority,
                                "description": rp.description or "",
                                "link_status": lk.status})
            elif lk.target_type == "test_case":
                tc = self.db.query(TestCase).filter(
                    TestCase.id == lk.target_id).first()
                if tc:
                    tcs.append({"id": tc.id, "title": tc.title,
                                "case_type": tc.case_type,
                                "priority": tc.priority,
                                "status": tc.status,
                                "link_status": lk.status})
        return {
            "artifact": _artifact_to_dict(artifact),
            "requirement_points": rps,
            "test_cases": tcs,
            "trace_links": link_dicts,
        }

    def confirm_trace_link(self, link_id: str, review_reason: str = "") -> Optional[Dict[str, Any]]:
        lk = self.db.query(ProductArtifactTraceLink).filter(
            ProductArtifactTraceLink.link_id == link_id).first()
        if not lk:
            return None
        lk.status = "confirmed"
        lk.review_reason = review_reason or lk.review_reason
        lk.reviewed_at = _now()
        lk.updated_at = _now()
        self.db.commit()
        return {"link_id": link_id, "status": "confirmed", "review_reason": lk.review_reason}

    def reject_trace_link(self, link_id: str, review_reason: str = "") -> Optional[Dict[str, Any]]:
        lk = self.db.query(ProductArtifactTraceLink).filter(
            ProductArtifactTraceLink.link_id == link_id).first()
        if not lk:
            return None
        lk.status = "rejected"
        lk.review_reason = review_reason or lk.review_reason
        lk.reviewed_at = _now()
        lk.updated_at = _now()
        self.db.commit()
        return {"link_id": link_id, "status": "rejected", "review_reason": lk.review_reason}

    # ══════════════════════════════════════════════════════════════
    #  Phase 3: 质量评分 / 转正式 / 质量统计
    # ══════════════════════════════════════════════════════════════

    def score_trace_link(self, link_id: str) -> Optional[Dict[str, Any]]:
        from services.product_studio_quality_service import ProductStudioQualityService
        lk = self.db.query(ProductArtifactTraceLink).filter(
            ProductArtifactTraceLink.link_id == link_id).first()
        if not lk:
            return None
        qs = ProductStudioQualityService(self.db)
        result = qs.score_trace_link(lk)
        lk.quality_score = result["quality_score"]
        lk.quality_reason = result["quality_reason"]
        lk.updated_at = _now()
        self.db.commit()
        return {
            "link_id": link_id,
            "quality_score": result["quality_score"],
            "quality_reason": result["quality_reason"],
            "duplicate_candidates": result.get("duplicate_candidates", []),
        }

    def score_artifact_trace_links(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        from services.product_studio_quality_service import ProductStudioQualityService
        artifact = self.db.query(ProductArtifact).filter(
            ProductArtifact.artifact_id == artifact_id).first()
        if not artifact:
            return None
        links = self.db.query(ProductArtifactTraceLink).filter(
            ProductArtifactTraceLink.artifact_id == artifact_id).all()
        if not links:
            return {"artifact_id": artifact_id, "scored_count": 0, "average_quality_score": 0.0}
        qs = ProductStudioQualityService(self.db)
        scores = []
        for lk in links:
            result = qs.score_trace_link(lk)
            lk.quality_score = result["quality_score"]
            lk.quality_reason = result["quality_reason"]
            lk.updated_at = _now()
            scores.append(result["quality_score"])
        self.db.commit()
        avg = round(sum(scores) / len(scores), 2) if scores else 0.0
        return {"artifact_id": artifact_id, "scored_count": len(scores), "average_quality_score": avg}

    def promote_to_test_case(self, link_id: str) -> Optional[Dict[str, Any]]:
        lk = self.db.query(ProductArtifactTraceLink).filter(
            ProductArtifactTraceLink.link_id == link_id).first()
        if not lk:
            return None
        if lk.target_type != "test_case":
            raise TypeError(f"仅 target_type=test_case 支持转正式，当前: {lk.target_type}")
        if lk.status not in ("draft", "confirmed"):
            raise ValueError(f"仅 draft/confirmed 状态可转正式，当前: {lk.status}")
        if lk.promoted_at:
            return {"link_id": link_id, "promoted_target_id": lk.promoted_target_id,
                    "status": "already_promoted",
                    "warning": None}
        tc = self.db.query(TestCase).filter(TestCase.id == lk.target_id).first()
        if not tc:
            raise ValueError(f"目标 TestCase 不存在: {lk.target_id}")

        warning = None
        if lk.quality_score is not None and lk.quality_score < 0.6:
            warning = f"质量分 {lk.quality_score} 低于 0.6，建议优化后再转正式"

        # Promote: update status from draft to pending (standard TestCase status)
        tc.status = "pending"
        tc.source = "ai_product_studio_promoted"
        tc.updated_at = _now()

        lk.promoted_at = _now()
        lk.promoted_target_id = tc.id
        if lk.status == "draft":
            lk.status = "confirmed"
        lk.updated_at = _now()
        self.db.commit()

        return {
            "link_id": link_id,
            "promoted_target_id": tc.id,
            "status": "promoted",
            "warning": warning,
        }

    def get_quality_summary(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        artifact = self.db.query(ProductArtifact).filter(
            ProductArtifact.artifact_id == artifact_id).first()
        if not artifact:
            return None
        links = self.db.query(ProductArtifactTraceLink).filter(
            ProductArtifactTraceLink.artifact_id == artifact_id).all()
        total = len(links)
        confirmed = sum(1 for l in links if l.status == "confirmed")
        rejected = sum(1 for l in links if l.status == "rejected")
        draft = sum(1 for l in links if l.status == "draft")
        promoted = sum(1 for l in links if l.promoted_at is not None)
        scores = [l.quality_score for l in links if l.quality_score is not None]
        avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0
        return {
            "artifact_id": artifact_id,
            "total_links": total,
            "confirmed_count": confirmed,
            "rejected_count": rejected,
            "draft_count": draft,
            "average_quality_score": avg_score,
            "promotion_count": promoted,
            "acceptance_rate": round(confirmed / total, 2) if total else 0.0,
            "rejection_rate": round(rejected / total, 2) if total else 0.0,
        }

    # ══════════════════════════════════════════════════════════════
    #  Phase 5: quality-dashboard / quality-report / batch-promote
    # ══════════════════════════════════════════════════════════════

    def _collect_idea_stats(self, idea_id: str) -> Optional[Dict[str, Any]]:
        """收集 Idea 维度的全量统计数据"""
        idea = self.db.query(ProductIdea).filter(ProductIdea.idea_id == idea_id).first()
        if not idea:
            return None

        artifacts = self.db.query(ProductArtifact).filter(
            ProductArtifact.idea_id == idea_id).all()
        artifact_ids = [a.artifact_id for a in artifacts]

        links = []
        if artifact_ids:
            links = self.db.query(ProductArtifactTraceLink).filter(
                ProductArtifactTraceLink.artifact_id.in_(artifact_ids)).all()

        rp_count = sum(1 for l in links if l.target_type == "requirement_point")
        tc_count = sum(1 for l in links if l.target_type == "test_case")
        total = len(links)
        confirmed = sum(1 for l in links if l.status == "confirmed")
        rejected = sum(1 for l in links if l.status == "rejected")
        draft = sum(1 for l in links if l.status == "draft")
        promoted = sum(1 for l in links if l.promoted_at is not None)
        scores = [l.quality_score for l in links if l.quality_score is not None]
        avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0
        dup_count = 0
        for l in links:
            if l.quality_reason and "duplicate" in (l.quality_reason or "").lower():
                dup_count += 1

        confirmation_rate = round(confirmed / total, 2) if total else 0.0
        rejection_rate = round(rejected / total, 2) if total else 0.0
        promotion_rate = round(promoted / tc_count, 2) if tc_count else 0.0

        # artifact 按类型统计
        art_by_type = {}
        for a in artifacts:
            art_by_type.setdefault(a.artifact_type, []).append(a)

        # per-artifact breakdown
        per_artifact = []
        for a in artifacts:
            a_links = [l for l in links if l.artifact_id == a.artifact_id]
            a_rp = sum(1 for l in a_links if l.target_type == "requirement_point")
            a_tc = sum(1 for l in a_links if l.target_type == "test_case")
            a_confirmed = sum(1 for l in a_links if l.status == "confirmed")
            a_rejected = sum(1 for l in a_links if l.status == "rejected")
            a_draft = sum(1 for l in a_links if l.status == "draft")
            a_promoted = sum(1 for l in a_links if l.promoted_at is not None)
            per_artifact.append({
                "artifact_id": a.artifact_id,
                "artifact_type": a.artifact_type,
                "title": a.title,
                "requirement_point_count": a_rp,
                "test_case_count": a_tc,
                "confirmed": a_confirmed,
                "rejected": a_rejected,
                "draft": a_draft,
                "promoted": a_promoted,
            })

        return {
            "idea": _idea_to_dict(idea),
            "artifact_count": len(artifacts),
            "artifact_types": {k: len(v) for k, v in art_by_type.items()},
            "requirement_point_count": rp_count,
            "test_case_draft_count": tc_count,
            "trace_link_count": total,
            "average_quality_score": avg_score,
            "confirmed_count": confirmed,
            "rejected_count": rejected,
            "draft_count": draft,
            "promotion_count": promoted,
            "confirmation_rate": confirmation_rate,
            "rejection_rate": rejection_rate,
            "promotion_rate": promotion_rate,
            "duplicate_candidate_count": dup_count,
            "per_artifact": per_artifact,
            "links": links,        # raw ORM objects for report generation
            "artifacts": artifacts,  # raw ORM objects
        }

    def get_quality_dashboard(self, idea_id: str) -> Optional[Dict[str, Any]]:
        """GET /ideas/{id}/quality-dashboard"""
        data = self._collect_idea_stats(idea_id)
        if not data:
            return None

        # risk flags
        risk_flags = []
        if data["average_quality_score"] < 0.7:
            risk_flags.append("LOW_AVERAGE_QUALITY")
        if data["rejection_rate"] > 0.4:
            risk_flags.append("HIGH_REJECTION_RATE")
        if data["confirmation_rate"] < 0.5 and data["trace_link_count"] > 0:
            risk_flags.append("LOW_CONFIRMATION_RATE")
        if data["promotion_count"] == 0 and data["test_case_draft_count"] > 0:
            risk_flags.append("NO_PROMOTED_TEST_CASE")
        if data["duplicate_candidate_count"] > 0:
            risk_flags.append("DUPLICATE_RISK")
        if data["trace_link_count"] == 0 and data["artifact_count"] > 0:
            risk_flags.append("TRACE_LINK_MISSING")

        # recommendations
        recommendations = []
        if "LOW_AVERAGE_QUALITY" in risk_flags:
            recommendations.append("平均质量分低于 0.7，建议优化生成 Prompt 或人工补充用例")
        if "HIGH_REJECTION_RATE" in risk_flags:
            recommendations.append("驳回率过高(>40%)，建议审查驳回原因并重新生成")
        if "LOW_CONFIRMATION_RATE" in risk_flags:
            recommendations.append("确认率低于 50%，建议人工审核更多 TraceLink")
        if "NO_PROMOTED_TEST_CASE" in risk_flags:
            recommendations.append("尚无转正式测试用例，建议 promote 高质量用例")
        if "DUPLICATE_RISK" in risk_flags:
            recommendations.append("存在重复候选，建议去重后再 promote")
        if "TRACE_LINK_MISSING" in risk_flags:
            recommendations.append("缺少 TraceLink，建议先生成需求点/测试用例")
        if not risk_flags:
            recommendations.append("质量状态良好，建议进入测试执行阶段")

        return {
            "idea": data["idea"],
            "summary": {
                "artifact_count": data["artifact_count"],
                "artifact_types": data["artifact_types"],
                "requirement_point_count": data["requirement_point_count"],
                "test_case_draft_count": data["test_case_draft_count"],
                "trace_link_count": data["trace_link_count"],
                "average_quality_score": data["average_quality_score"],
                "confirmed_count": data["confirmed_count"],
                "rejected_count": data["rejected_count"],
                "draft_count": data["draft_count"],
                "promotion_count": data["promotion_count"],
                "confirmation_rate": data["confirmation_rate"],
                "rejection_rate": data["rejection_rate"],
                "promotion_rate": data["promotion_rate"],
                "duplicate_candidate_count": data["duplicate_candidate_count"],
            },
            "per_artifact": data["per_artifact"],
            "risk_flags": risk_flags,
            "recommendations": recommendations,
        }

    def generate_quality_report(self, idea_id: str) -> Optional[Dict[str, Any]]:
        """POST /ideas/{id}/generate-quality-report — 生成 Markdown 质量报告 Artifact"""
        data = self._collect_idea_stats(idea_id)
        if not data:
            return None

        idea = data["idea"]
        s = data  # shortcut

        # quality level
        avg = s["average_quality_score"]
        if avg >= 0.8 and s["confirmation_rate"] >= 0.6:
            level = "高"
        elif avg >= 0.6:
            level = "中"
        else:
            level = "低"

        # risk flags (same logic)
        risks = []
        if avg < 0.7:
            risks.append("平均质量分 < 0.7")
        if s["rejection_rate"] > 0.4:
            risks.append("驳回率 > 40%")
        if s["confirmation_rate"] < 0.5 and s["trace_link_count"] > 0:
            risks.append("确认率 < 50%")
        if s["duplicate_candidate_count"] > 0:
            risks.append(f"重复候选 {s['duplicate_candidate_count']} 个")
        if s["promotion_count"] == 0 and s["test_case_draft_count"] > 0:
            risks.append("无转正式测试用例")
        recommend_exec = (level != "低" and s["confirmation_rate"] >= 0.5
                          and s["promotion_count"] > 0)

        # per-artifact table
        pa_rows = ""
        for pa in s["per_artifact"]:
            pa_rows += (f"| {pa['artifact_type']} | {pa['artifact_id'][:12]}… "
                        f"| {pa['requirement_point_count']} | {pa['test_case_count']} "
                        f"| {pa['confirmed']} | {pa['rejected']} | {pa['draft']} "
                        f"| {pa['promoted']} |\n")

        # sample high-quality TCs
        tc_links = [l for l in s["links"]
                    if l.target_type == "test_case" and l.quality_score is not None]
        high_tcs = sorted(tc_links, key=lambda l: l.quality_score or 0, reverse=True)[:3]
        rejected_tcs = [l for l in tc_links if l.status == "rejected"][:3]
        rp_links = [l for l in s["links"] if l.target_type == "requirement_point"][:3]

        def _tc_row(l):
            tc = self.db.query(TestCase).filter(TestCase.id == l.target_id).first()
            title = (tc.title[:40] if tc else l.target_id) if tc else l.target_id
            return f"| {l.target_id[:16]}… | {title} | {l.quality_score} | {l.status} |"

        def _rp_row(l):
            rp = self.db.query(RequirementPoint).filter(RequirementPoint.id == l.target_id).first()
            title = (rp.title[:40] if rp else l.target_id) if rp else l.target_id
            return f"| {l.target_id[:16]}… | {title} | {l.quality_score} | {l.status} |"

        high_tc_rows = "\n".join(_tc_row(l) for l in high_tcs) if high_tcs else "| — | — | — | — |"
        rej_tc_rows = "\n".join(_tc_row(l) for l in rejected_tcs) if rejected_tcs else "| — | — | — | — |"
        rp_rows = "\n".join(_rp_row(l) for l in rp_links) if rp_links else "| — | — | — | — |"

        risk_text = "\n".join(f"- ⚠️ {r}" for r in risks) if risks else "- 无显著风险"

        md = f"""# Product Studio 质量报告

## 1. 结论

- **是否建议进入测试执行**: {"✅ 是" if recommend_exec else "❌ 否，建议先解决风险项"}
- **当前质量等级**: **{level}**
- **主要风险**: {', '.join(risks) if risks else '无'}
- **下一步建议**: {"可进入测试执行阶段" if recommend_exec else "建议补充确认并提升质量分后再推进"}

## 2. 基础信息

| 字段 | 值 |
|------|-----|
| idea_id | {idea['idea_id']} |
| 产品名称 | {idea['title']} |
| 业务方向 | {idea.get('product_direction', '')[:60]} |
| 生成时间 | {_now().strftime('%Y-%m-%d %H:%M')} |

## 3. 产物统计

| 类型 | 数量 |
|------|------|
| ProductArtifact | {s['artifact_count']} |
| RequirementPoint | {s['requirement_point_count']} |
| TestCase 草稿 | {s['test_case_draft_count']} |
| TraceLink | {s['trace_link_count']} |
| Promoted TestCase | {s['promotion_count']} |

## 4. 质量统计

| 指标 | 值 | 判断 |
|------|-----|------|
| average_quality_score | {avg} | {"✅ 健康" if avg >= 0.7 else "⚠️ 偏低"} |
| confirmation_rate | {s['confirmation_rate']} | {"✅ 达标" if s['confirmation_rate'] >= 0.5 else "⚠️ 偏低"} |
| rejection_rate | {s['rejection_rate']} | {"✅ 正常" if s['rejection_rate'] <= 0.4 else "⚠️ 过高"} |
| promotion_rate | {s['promotion_rate']} | {"✅ 有转正" if s['promotion_count'] > 0 else "⚠️ 无"} |
| duplicate_candidate_count | {s['duplicate_candidate_count']} | {"✅ 无重复" if s['duplicate_candidate_count'] == 0 else "⚠️ 存在重复"} |

## 5. 追溯链路分析

| 类型 | artifact_id | RP数 | TC数 | confirmed | rejected | draft | promoted |
|------|-------------|------|------|-----------|----------|-------|----------|
{pa_rows}
## 6. 风险项

{risk_text}

## 7. 样例数据

### 高质量 TestCase (Top 3)

| target_id | 标题 | quality_score | status |
|-----------|------|---------------|--------|
{high_tc_rows}

### 被驳回 TestCase (最多 3 条)

| target_id | 标题 | quality_score | status |
|-----------|------|---------------|--------|
{rej_tc_rows}

### RequirementPoint 样例 (最多 3 条)

| target_id | 标题 | quality_score | status |
|-----------|------|---------------|--------|
{rp_rows}

## 8. 建议

{"- ✅ 建议进入测试执行阶段" if recommend_exec else "- ❌ 暂不建议进入测试执行"}
{"- 建议批量转正式高质量用例" if s['promotion_count'] == 0 and s['test_case_draft_count'] > 0 else ""}
{"- 建议人工审核低质量用例" if avg < 0.7 else ""}
{"- 建议重新生成或人工补充" if s['rejection_rate'] > 0.4 else ""}
{"- 质量状态良好，可持续迭代" if not risks else ""}
"""

        # 存为 Artifact
        artifact_id = f"art_{_uid()}"
        artifact = ProductArtifact(
            artifact_id=artifact_id,
            idea_id=idea_id,
            artifact_type="quality_report",
            title="质量报告",
            content_markdown=md.strip(),
            status="final",
        )
        self.db.add(artifact)
        self.db.commit()

        return {
            "artifact_id": artifact_id,
            "artifact_type": "quality_report",
            "summary": {
                "artifact_count": s["artifact_count"],
                "requirement_point_count": s["requirement_point_count"],
                "test_case_draft_count": s["test_case_draft_count"],
                "trace_link_count": s["trace_link_count"],
                "average_quality_score": avg,
                "confirmed_count": s["confirmed_count"],
                "rejected_count": s["rejected_count"],
                "draft_count": s["draft_count"],
                "promotion_count": s["promotion_count"],
                "confirmation_rate": s["confirmation_rate"],
                "rejection_rate": s["rejection_rate"],
                "promotion_rate": s["promotion_rate"],
            },
        }

    def batch_promote_test_cases(self, idea_id: str,
                                  min_quality_score: float = 0.8,
                                  only_confirmed: bool = True,
                                  max_count: int = 20) -> Optional[Dict[str, Any]]:
        """POST /ideas/{id}/batch-promote-test-cases"""
        idea = self.db.query(ProductIdea).filter(ProductIdea.idea_id == idea_id).first()
        if not idea:
            return None

        artifacts = self.db.query(ProductArtifact).filter(
            ProductArtifact.idea_id == idea_id).all()
        artifact_ids = [a.artifact_id for a in artifacts]
        if not artifact_ids:
            return {"promoted_count": 0, "skipped_count": 0, "skipped_reasons": []}

        links = self.db.query(ProductArtifactTraceLink).filter(
            ProductArtifactTraceLink.artifact_id.in_(artifact_ids),
            ProductArtifactTraceLink.target_type == "test_case",
        ).all()

        promoted_count = 0
        skipped_count = 0
        skipped_reasons = []

        for lk in links:
            if promoted_count >= max_count:
                break
            # already promoted — idempotent
            if lk.promoted_at:
                skipped_count += 1
                skipped_reasons.append({"link_id": lk.link_id, "reason": "already_promoted"})
                continue
            # status filter
            if only_confirmed and lk.status != "confirmed":
                skipped_count += 1
                skipped_reasons.append({"link_id": lk.link_id, "reason": f"status={lk.status}"})
                continue
            # quality filter
            if lk.quality_score is not None and lk.quality_score < min_quality_score:
                skipped_count += 1
                skipped_reasons.append({"link_id": lk.link_id,
                                        "reason": f"quality_score={lk.quality_score}<{min_quality_score}"})
                continue

            tc = self.db.query(TestCase).filter(TestCase.id == lk.target_id).first()
            if not tc:
                skipped_count += 1
                skipped_reasons.append({"link_id": lk.link_id, "reason": "test_case_not_found"})
                continue

            tc.status = "pending"
            tc.source = "ai_product_studio_promoted"
            tc.updated_at = _now()
            lk.promoted_at = _now()
            lk.promoted_target_id = tc.id
            if lk.status == "draft":
                lk.status = "confirmed"
            lk.updated_at = _now()
            promoted_count += 1

        self.db.commit()
        return {
            "promoted_count": promoted_count,
            "skipped_count": skipped_count,
            "skipped_reasons": skipped_reasons[:50],  # cap output
        }


# ── JSON 解析辅助 ─────────────────────────────────────────────
def _parse_json_array(text: str) -> list:
    """从 LLM 文本中提取 JSON 数组"""
    if not text:
        return []
    # 尝试直接解析
    stripped = text.strip()
    if stripped.startswith("["):
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass
    # 尝试从 markdown code block 提取
    m = re.search(r'```(?:json)?\s*\n(\[.*?\])\s*\n```', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    # 尝试找第一个 [ ... ] 范围
    start = text.find('[')
    end = text.rfind(']')
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    return []
