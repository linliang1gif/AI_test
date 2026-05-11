"""
AI Dev Studio — 服务层
职责: DevTask CRUD + AI 生成 DevPlan/ApiDesign/DbDesign/FileImpact/TestPlan
"""

import uuid
import json
import logging
import re
from datetime import datetime
from typing import Dict, Any, Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import desc

from database.models import (
    DevTask, DevStudioRun, DevArtifact,
    ProductArtifact, TestCase,
)
from services.dev_studio_prompts import (
    PROMPT_BUILDERS, MAX_TOKENS_MAP, ARTIFACT_TITLE_MAP, RUN_TYPES,
)
from services.sanitize import sanitize_text

logger = logging.getLogger("dev_studio")


def _uid() -> str:
    return uuid.uuid4().hex[:16]


def _now() -> datetime:
    return datetime.now()


def _call_llm(prompt: str, max_tokens: int = 8000, provider: str = None, model: str = None):
    try:
        from agent.llm_client import get_llm_client
        client = get_llm_client(provider=provider, model=model)
        model_name = f"{client.provider}/{client.model}"
        is_mock = client.provider == "mock"
        text = client.generate(
            prompt=prompt,
            system_prompt="你是 AI Dev Studio 的智能助手，请按要求输出结构化 Markdown。",
            temperature=0.3,
            max_tokens=max_tokens,
        )
        return text, model_name, is_mock
    except Exception as e:
        raise RuntimeError(f"LLM 调用失败: {sanitize_text(str(e))}")


def _load_source_context(db: Session, source_type: str, source_id: str) -> str:
    """根据 source_type + source_id 加载上下文内容"""
    if source_type == "product_artifact" and source_id:
        art = db.query(ProductArtifact).filter(ProductArtifact.artifact_id == source_id).first()
        if art:
            label = art.artifact_type or "artifact"
            return f"[来源: ProductArtifact ({label})]\n\n{art.content_markdown or ''}"
    elif source_type == "test_case" and source_id:
        tc = db.query(TestCase).filter(TestCase.id == int(source_id) if source_id.isdigit() else -1).first()
        if tc:
            parts = [f"# 测试用例: {tc.name or tc.title or ''}"]
            if hasattr(tc, "description") and tc.description:
                parts.append(f"描述: {tc.description}")
            if hasattr(tc, "steps") and tc.steps:
                parts.append(f"步骤: {tc.steps}")
            if hasattr(tc, "expected_result") and tc.expected_result:
                parts.append(f"预期结果: {tc.expected_result}")
            return "\n\n".join(parts)
    return ""


class DevStudioService:

    # ── Task CRUD ──────────────────────────────────────────────

    @staticmethod
    def create_task(db: Session, data: Dict[str, Any]) -> Dict[str, Any]:
        source_type = data.get("source_type", "manual")
        source_id = data.get("source_id")

        # 如果 source_type 是 product_artifact，校验来源存在
        if source_type == "product_artifact" and source_id:
            art = db.query(ProductArtifact).filter(ProductArtifact.artifact_id == source_id).first()
            if not art:
                raise ValueError(f"来源 ProductArtifact 不存在: {source_id}")

        task = DevTask(
            dev_task_id=f"dtask_{_uid()}",
            source_type=source_type,
            source_id=source_id,
            idea_id=data.get("idea_id"),
            project_id=data.get("project_id"),
            title=data.get("title", ""),
            description=data.get("description", ""),
            status="created",
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return {"dev_task_id": task.dev_task_id, "status": task.status}

    @staticmethod
    def list_tasks(db: Session, keyword: str = None, project_id: int = None,
                   idea_id: str = None, source_type: str = None,
                   page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        q = db.query(DevTask)
        if keyword:
            q = q.filter(DevTask.title.ilike(f"%{keyword}%"))
        if project_id is not None:
            q = q.filter(DevTask.project_id == project_id)
        if idea_id:
            q = q.filter(DevTask.idea_id == idea_id)
        if source_type:
            q = q.filter(DevTask.source_type == source_type)

        total = q.count()
        items = q.order_by(desc(DevTask.created_at)).offset((page - 1) * page_size).limit(page_size).all()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [
                {
                    "dev_task_id": t.dev_task_id,
                    "source_type": t.source_type,
                    "source_id": t.source_id,
                    "idea_id": t.idea_id,
                    "project_id": t.project_id,
                    "title": t.title,
                    "description": t.description,
                    "status": t.status,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "updated_at": t.updated_at.isoformat() if t.updated_at else None,
                }
                for t in items
            ],
        }

    @staticmethod
    def get_task_detail(db: Session, dev_task_id: str) -> Dict[str, Any]:
        task = db.query(DevTask).filter(DevTask.dev_task_id == dev_task_id).first()
        if not task:
            return None

        artifacts = db.query(DevArtifact).filter(
            DevArtifact.dev_task_id == dev_task_id
        ).order_by(desc(DevArtifact.created_at)).all()

        runs = db.query(DevStudioRun).filter(
            DevStudioRun.dev_task_id == dev_task_id
        ).order_by(desc(DevStudioRun.created_at)).all()

        # 加载来源摘要
        source_summary = _load_source_context(db, task.source_type, task.source_id or "")
        if len(source_summary) > 500:
            source_summary = source_summary[:500] + "..."

        return {
            "dev_task_id": task.dev_task_id,
            "source_type": task.source_type,
            "source_id": task.source_id,
            "idea_id": task.idea_id,
            "project_id": task.project_id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            "source_summary": source_summary,
            "artifacts": [
                {
                    "dev_artifact_id": a.dev_artifact_id,
                    "artifact_type": a.artifact_type,
                    "title": a.title,
                    "status": a.status,
                    "run_id": a.run_id,
                    "batch_id": getattr(a, "batch_id", None),
                    "batch_index": getattr(a, "batch_index", None),
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                for a in artifacts
            ],
            "runs": [
                {
                    "run_id": r.run_id,
                    "run_type": r.run_type,
                    "status": r.status,
                    "model_name": r.model_name,
                    "trace_id": r.trace_id,
                    "error_message": r.error_message,
                    "started_at": r.started_at.isoformat() if r.started_at else None,
                    "finished_at": r.finished_at.isoformat() if r.finished_at else None,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in runs
            ],
        }

    # ── 通用生成方法 ──────────────────────────────────────────

    @staticmethod
    def _generate(db: Session, dev_task_id: str, run_type: str,
                  batch_id: str = None, batch_index: int = None) -> Dict[str, Any]:
        if run_type not in RUN_TYPES:
            raise ValueError(f"不支持的 run_type: {run_type}")

        task = db.query(DevTask).filter(DevTask.dev_task_id == dev_task_id).first()
        if not task:
            return None

        # 加载上下文
        context = _load_source_context(db, task.source_type, task.source_id or "")
        if task.description:
            context = f"{task.description}\n\n{context}"

        # 检查已有同类型 artifact 并追加上下文
        existing_arts = db.query(DevArtifact).filter(
            DevArtifact.dev_task_id == dev_task_id,
        ).order_by(desc(DevArtifact.created_at)).all()
        for ea in existing_arts:
            if ea.artifact_type != run_type and ea.content_markdown:
                context += f"\n\n## 已生成的{ARTIFACT_TITLE_MAP.get(ea.artifact_type, ea.artifact_type)}\n\n{ea.content_markdown[:3000]}"

        # 创建 Run
        run = DevStudioRun(
            run_id=f"drun_{_uid()}",
            dev_task_id=dev_task_id,
            run_type=run_type,
            trace_id=f"dtrace_{_uid()}",
            batch_id=batch_id,
            input_payload={"task_title": task.title, "source_type": task.source_type, "source_id": task.source_id},
            status="running",
            started_at=_now(),
        )
        db.add(run)
        db.commit()

        # 更新 task 状态
        task.status = "planning"
        task.updated_at = _now()
        db.commit()

        try:
            prompt_builder = PROMPT_BUILDERS[run_type]
            prompt = prompt_builder(context, task.title)
            max_tokens = MAX_TOKENS_MAP.get(run_type, 8000)

            text, model_name, is_mock = _call_llm(prompt, max_tokens)

            if not text or not text.strip():
                raise RuntimeError("LLM 返回空内容")

            run.output_text = text
            run.model_name = model_name
            run.status = "succeeded"
            run.finished_at = _now()
            db.commit()

            # 创建 DevArtifact
            artifact = DevArtifact(
                dev_artifact_id=f"dart_{_uid()}",
                dev_task_id=dev_task_id,
                run_id=run.run_id,
                artifact_type=run_type,
                title=f"{ARTIFACT_TITLE_MAP.get(run_type, run_type)} — {task.title}",
                content_markdown=text,
                status="draft",
                batch_id=batch_id,
                batch_index=batch_index,
            )
            db.add(artifact)

            # 更新 task 状态
            task.status = "planned"
            task.updated_at = _now()
            db.commit()

            return {
                "run_id": run.run_id,
                "trace_id": run.trace_id,
                "dev_artifact_id": artifact.dev_artifact_id,
                "artifact_type": run_type,
                "status": run.status,
                "model_name": model_name,
                "is_mock": is_mock,
            }

        except Exception as e:
            run.status = "failed"
            run.error_message = sanitize_text(str(e))[:500]
            run.finished_at = _now()
            db.commit()
            logger.error(f"Dev Studio generate failed [{run_type}]: {e}")
            return {
                "run_id": run.run_id,
                "trace_id": run.trace_id,
                "dev_artifact_id": None,
                "artifact_type": run_type,
                "status": "failed",
                "error_message": run.error_message,
            }

    @staticmethod
    def generate_dev_plan(db: Session, dev_task_id: str) -> Dict[str, Any]:
        return DevStudioService._generate(db, dev_task_id, "dev_plan")

    @staticmethod
    def generate_api_design(db: Session, dev_task_id: str) -> Dict[str, Any]:
        return DevStudioService._generate(db, dev_task_id, "api_design")

    @staticmethod
    def generate_db_design(db: Session, dev_task_id: str) -> Dict[str, Any]:
        return DevStudioService._generate(db, dev_task_id, "db_design")

    @staticmethod
    def generate_file_impact(db: Session, dev_task_id: str) -> Dict[str, Any]:
        return DevStudioService._generate(db, dev_task_id, "file_impact")

    @staticmethod
    def generate_test_plan(db: Session, dev_task_id: str) -> Dict[str, Any]:
        return DevStudioService._generate(db, dev_task_id, "test_plan")

    # ── 批量生成 ──────────────────────────────────────────────

    @staticmethod
    def generate_all_artifacts(
        db: Session,
        dev_task_id: str,
        artifact_types: List[str] = None,
        continue_on_error: bool = True,
        regenerate_existing: bool = True,
    ) -> Dict[str, Any]:
        """批量生成全部 DevArtifact，按固定顺序依次生成，创建 batch_id"""
        ALLOWED = RUN_TYPES
        FIXED_ORDER = list(ALLOWED)

        if artifact_types is None:
            artifact_types = FIXED_ORDER
        else:
            invalid = [t for t in artifact_types if t not in ALLOWED]
            if invalid:
                raise TypeError(f"非法 artifact_type: {', '.join(invalid)}")
            artifact_types = [t for t in FIXED_ORDER if t in artifact_types]

        task = db.query(DevTask).filter(DevTask.dev_task_id == dev_task_id).first()
        if not task:
            return None

        batch_id = f"dbatch_{_uid()}"
        results = []
        succeeded_count = 0
        failed_count = 0

        for idx, run_type in enumerate(artifact_types, start=1):
            try:
                result = DevStudioService._generate(
                    db, dev_task_id, run_type,
                    batch_id=batch_id, batch_index=idx,
                )
                if result and result.get("status") == "succeeded":
                    succeeded_count += 1
                    results.append({
                        "artifact_type": run_type,
                        "status": "succeeded",
                        "run_id": result.get("run_id"),
                        "dev_artifact_id": result.get("dev_artifact_id"),
                        "error_message": None,
                    })
                else:
                    failed_count += 1
                    results.append({
                        "artifact_type": run_type,
                        "status": "failed",
                        "run_id": result.get("run_id") if result else None,
                        "dev_artifact_id": None,
                        "error_message": sanitize_text(result.get("error_message", "生成失败"))[:200] if result else "生成返回空",
                    })
                    if not continue_on_error:
                        break
            except Exception as e:
                failed_count += 1
                results.append({
                    "artifact_type": run_type,
                    "status": "failed",
                    "run_id": None,
                    "dev_artifact_id": None,
                    "error_message": sanitize_text(str(e))[:200],
                })
                logger.error(f"Batch generate failed [{run_type}]: {e}")
                if not continue_on_error:
                    break

        # 更新 dev_plan 引用同批次其他产物
        try:
            DevStudioService._update_dev_plan_references(db, batch_id)
        except Exception as e:
            logger.warning(f"更新 dev_plan 引用失败: {e}")

        return {
            "dev_task_id": dev_task_id,
            "batch_id": batch_id,
            "total": len(artifact_types),
            "succeeded_count": succeeded_count,
            "failed_count": failed_count,
            "results": results,
        }

    @staticmethod
    def _update_dev_plan_references(db: Session, batch_id: str):
        """在同批次 dev_plan 的 reference_artifact_ids 中记录其他产物 ID"""
        batch_arts = db.query(DevArtifact).filter(
            DevArtifact.batch_id == batch_id
        ).order_by(DevArtifact.batch_index).all()
        if not batch_arts:
            return

        dev_plan_art = None
        other_arts = []
        for a in batch_arts:
            if a.artifact_type == "dev_plan":
                dev_plan_art = a
            else:
                other_arts.append(a)

        if not dev_plan_art or not other_arts:
            return

        ref_ids = [a.dev_artifact_id for a in other_arts]
        dev_plan_art.reference_artifact_ids = json.dumps(ref_ids)

        # 追加关联产物章节到 markdown（替换已有的）
        ref_section = "\n\n## 关联开发产物\n\n"
        ref_section += "> 以下产物与本开发计划同批次生成，需人工确认。\n\n"
        ref_section += "| 类型 | Artifact ID | 说明 |\n|---|---|---|\n"
        for a in other_arts:
            label = ARTIFACT_TITLE_MAP.get(a.artifact_type, a.artifact_type)
            ref_section += f"| {label} | {a.dev_artifact_id} | 同批次生成 |\n"

        md = dev_plan_art.content_markdown or ""
        # 替换已有章节
        pattern = r"\n*## 关联开发产物[\s\S]*$"
        md = re.sub(pattern, "", md)
        dev_plan_art.content_markdown = md + ref_section
        dev_plan_art.updated_at = _now()
        db.commit()

    # ── 开发包查询 ──────────────────────────────────────────────

    @staticmethod
    def list_packages(db: Session, dev_task_id: str) -> Dict[str, Any]:
        """按 batch_id 聚合同一 DevTask 的开发包列表"""
        task = db.query(DevTask).filter(DevTask.dev_task_id == dev_task_id).first()
        if not task:
            return None

        arts = db.query(DevArtifact).filter(
            DevArtifact.dev_task_id == dev_task_id,
            DevArtifact.batch_id.isnot(None),
        ).order_by(desc(DevArtifact.created_at)).all()

        runs = db.query(DevStudioRun).filter(
            DevStudioRun.dev_task_id == dev_task_id,
            DevStudioRun.batch_id.isnot(None),
        ).all()

        # 聚合
        batch_map = {}
        for a in arts:
            bid = a.batch_id
            if bid not in batch_map:
                batch_map[bid] = {"batch_id": bid, "created_at": None, "artifact_types": [], "artifact_count": 0}
            batch_map[bid]["artifact_count"] += 1
            batch_map[bid]["artifact_types"].append(a.artifact_type)
            if a.created_at and (batch_map[bid]["created_at"] is None or a.created_at < batch_map[bid]["created_at"]):
                batch_map[bid]["created_at"] = a.created_at

        # 统计 run succeeded/failed
        run_stats = {}
        for r in runs:
            bid = r.batch_id
            if bid not in run_stats:
                run_stats[bid] = {"succeeded": 0, "failed": 0}
            if r.status == "succeeded":
                run_stats[bid]["succeeded"] += 1
            elif r.status == "failed":
                run_stats[bid]["failed"] += 1

        packages = []
        for bid, info in batch_map.items():
            stats = run_stats.get(bid, {"succeeded": 0, "failed": 0})
            packages.append({
                "batch_id": bid,
                "created_at": info["created_at"].isoformat() if info["created_at"] else None,
                "artifact_count": info["artifact_count"],
                "succeeded_count": stats["succeeded"],
                "failed_count": stats["failed"],
                "artifact_types": info["artifact_types"],
            })

        # 按 created_at 降序
        packages.sort(key=lambda p: p["created_at"] or "", reverse=True)

        return {"dev_task_id": dev_task_id, "packages": packages}

    @staticmethod
    def get_package_detail(db: Session, dev_task_id: str, batch_id: str) -> Dict[str, Any]:
        """获取单个开发包的详情"""
        task = db.query(DevTask).filter(DevTask.dev_task_id == dev_task_id).first()
        if not task:
            return None

        arts = db.query(DevArtifact).filter(
            DevArtifact.dev_task_id == dev_task_id,
            DevArtifact.batch_id == batch_id,
        ).order_by(DevArtifact.batch_index).all()

        runs = db.query(DevStudioRun).filter(
            DevStudioRun.dev_task_id == dev_task_id,
            DevStudioRun.batch_id == batch_id,
        ).order_by(DevStudioRun.created_at).all()

        if not arts and not runs:
            return {"_not_found": True}

        return {
            "batch_id": batch_id,
            "dev_task_id": dev_task_id,
            "artifacts": [
                {
                    "dev_artifact_id": a.dev_artifact_id,
                    "artifact_type": a.artifact_type,
                    "title": a.title,
                    "status": a.status,
                    "batch_index": a.batch_index,
                    "reference_artifact_ids": json.loads(a.reference_artifact_ids) if a.reference_artifact_ids else None,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                for a in arts
            ],
            "runs": [
                {
                    "run_id": r.run_id,
                    "run_type": r.run_type,
                    "status": r.status,
                    "model_name": r.model_name,
                    "trace_id": r.trace_id,
                    "error_message": r.error_message,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in runs
            ],
        }

    # ── Patch Draft 生成 ──────────────────────────────────────

    @staticmethod
    def generate_patch_draft(
        db: Session,
        dev_task_id: str,
        source_file_impact_artifact_id: str = None,
        snapshot_id: str = None,
        max_files: int = 10,
    ) -> Dict[str, Any]:
        """基于 file_impact_v2 + CodeMap 生成 Patch Draft 草稿"""
        task = db.query(DevTask).filter(DevTask.dev_task_id == dev_task_id).first()
        if not task:
            return None

        max_files = min(max(1, max_files), 20)

        # 查找 file_impact_v2 artifact
        fi_art = None
        if source_file_impact_artifact_id:
            fi_art = db.query(DevArtifact).filter(
                DevArtifact.dev_artifact_id == source_file_impact_artifact_id,
            ).first()
        if not fi_art:
            # 回退: 最新的 file_impact_v2 或 file_impact
            fi_art = db.query(DevArtifact).filter(
                DevArtifact.dev_task_id == dev_task_id,
                DevArtifact.artifact_type.in_(["file_impact_v2", "file_impact"]),
            ).order_by(desc(DevArtifact.created_at)).first()

        if not fi_art or not fi_art.content_markdown:
            return {"_error": "no_file_impact", "message": "请先生成影响文件分析 (file_impact 或 file_impact_v2)"}

        # 构建候选文件摘要
        candidate_text = fi_art.content_markdown[:4000]

        # 如有 snapshot_id, 补充 CodeMapFile 上下文
        codemap_ctx = ""
        if snapshot_id:
            try:
                from database.models import CodeMapFile
                cm_files = db.query(CodeMapFile).filter(
                    CodeMapFile.snapshot_id == snapshot_id
                ).order_by(CodeMapFile.category, CodeMapFile.relative_path).limit(200).all()
                if cm_files:
                    parts = []
                    for f in cm_files[:50]:
                        parts.append(f"- `{f.relative_path}` [{f.category}] ({f.line_count} 行)")
                    codemap_ctx = "\n### 项目代码结构摘要\n" + "\n".join(parts)
            except Exception:
                pass

        # 构建上下文
        context_parts = []
        if task.description:
            context_parts.append(f"## 需求描述\n{task.description}")
        # 加载其他已有产物
        for art_type in ("dev_plan", "api_design", "db_design"):
            ea = db.query(DevArtifact).filter(
                DevArtifact.dev_task_id == dev_task_id,
                DevArtifact.artifact_type == art_type,
            ).order_by(desc(DevArtifact.created_at)).first()
            if ea and ea.content_markdown:
                label = art_type.replace("_", " ").title()
                context_parts.append(f"## 已有 {label}\n{ea.content_markdown[:2000]}")

        context = "\n\n".join(context_parts)

        # 构造 prompt
        from services.dev_studio_prompts import build_patch_draft_prompt
        full_candidate = candidate_text + codemap_ctx
        prompt = build_patch_draft_prompt(context, task.title, full_candidate)

        # 创建 Run
        run = DevStudioRun(
            run_id=f"drun_{_uid()}",
            dev_task_id=dev_task_id,
            run_type="patch_draft",
            trace_id=f"dtrace_{_uid()}",
            input_payload={
                "task_title": task.title,
                "source_artifact_id": fi_art.dev_artifact_id,
                "snapshot_id": snapshot_id,
                "max_files": max_files,
            },
            status="running",
            started_at=_now(),
        )
        db.add(run)
        db.commit()

        try:
            text, model_name, is_mock = _call_llm(prompt, max_tokens=12000)
            if not text or not text.strip():
                raise RuntimeError("LLM 返回空内容")

            run.output_text = text
            run.model_name = model_name
            run.status = "succeeded"
            run.finished_at = _now()
            db.commit()

            artifact = DevArtifact(
                dev_artifact_id=f"dart_{_uid()}",
                dev_task_id=dev_task_id,
                run_id=run.run_id,
                artifact_type="patch_draft",
                title=f"补丁草稿 — {task.title}",
                content_markdown=text,
                status="draft",
            )
            db.add(artifact)
            db.commit()

            return {
                "run_id": run.run_id,
                "trace_id": run.trace_id,
                "dev_artifact_id": artifact.dev_artifact_id,
                "artifact_type": "patch_draft",
                "status": "succeeded",
                "model_name": model_name,
                "is_mock": is_mock,
            }
        except Exception as e:
            run.status = "failed"
            run.error_message = sanitize_text(str(e))[:500]
            run.finished_at = _now()
            db.commit()
            logger.error(f"patch_draft 生成失败: {e}")
            return {
                "run_id": run.run_id,
                "trace_id": run.trace_id,
                "dev_artifact_id": None,
                "artifact_type": "patch_draft",
                "status": "failed",
                "error_message": run.error_message,
            }

    # ── Patch Review ─────────────────────────────────────────

    @staticmethod
    def review_patch_draft(
        db: Session,
        dev_artifact_id: str,
        strict_mode: bool = True,
        include_test_mapping: bool = True,
        include_security_check: bool = True,
    ) -> Dict[str, Any]:
        """对 patch_draft Artifact 进行 AI 评审"""
        art = db.query(DevArtifact).filter(DevArtifact.dev_artifact_id == dev_artifact_id).first()
        if not art:
            return None
        if art.artifact_type != "patch_draft":
            return {"_error": "not_patch_draft", "message": f"artifact_type 必须为 patch_draft，当前为 {art.artifact_type}"}
        if not art.content_markdown or not art.content_markdown.strip():
            return {"_error": "empty_content", "message": "Patch Draft 内容为空"}

        task = db.query(DevTask).filter(DevTask.dev_task_id == art.dev_task_id).first()
        task_title = task.title if task else "未知任务"

        # 加载关联上下文
        fi_ctx = ""
        tp_ctx = ""
        if art.dev_task_id:
            fi_art = db.query(DevArtifact).filter(
                DevArtifact.dev_task_id == art.dev_task_id,
                DevArtifact.artifact_type.in_(["file_impact_v2", "file_impact"]),
            ).order_by(desc(DevArtifact.created_at)).first()
            if fi_art and fi_art.content_markdown:
                fi_ctx = fi_art.content_markdown[:2000]

            tp_art = db.query(DevArtifact).filter(
                DevArtifact.dev_task_id == art.dev_task_id,
                DevArtifact.artifact_type == "test_plan",
            ).order_by(desc(DevArtifact.created_at)).first()
            if tp_art and tp_art.content_markdown:
                tp_ctx = tp_art.content_markdown[:2000]

        from services.dev_studio_prompts import build_patch_review_prompt
        prompt = build_patch_review_prompt(
            art.content_markdown, task_title,
            file_impact_ctx=fi_ctx, test_plan_ctx=tp_ctx,
            strict_mode=strict_mode,
            include_test_mapping=include_test_mapping,
            include_security_check=include_security_check,
        )

        run = DevStudioRun(
            run_id=f"drun_{_uid()}",
            dev_task_id=art.dev_task_id,
            run_type="patch_review",
            trace_id=f"dtrace_{_uid()}",
            input_payload={
                "source_artifact_id": dev_artifact_id,
                "strict_mode": strict_mode,
                "include_test_mapping": include_test_mapping,
                "include_security_check": include_security_check,
            },
            status="running",
            started_at=_now(),
        )
        db.add(run)
        db.commit()

        try:
            text, model_name, is_mock = _call_llm(prompt, max_tokens=12000)
            if not text or not text.strip():
                raise RuntimeError("LLM 返回空内容")

            run.output_text = text
            run.model_name = model_name
            run.status = "succeeded"
            run.finished_at = _now()
            db.commit()

            # 解析结构化 JSON
            content_json = None
            risk_level = "medium"
            review_score = 0.0
            should_apply = False
            try:
                import re as _re
                json_match = _re.search(r'```json\s*(\{[\s\S]*?\})\s*```', text)
                if json_match:
                    content_json = json.loads(json_match.group(1))
                    risk_level = content_json.get("risk_level", "medium")
                    review_score = float(content_json.get("review_score", 0.0))
                    should_apply = bool(content_json.get("should_apply", False))
            except Exception:
                pass

            review_art = DevArtifact(
                dev_artifact_id=f"dart_{_uid()}",
                dev_task_id=art.dev_task_id,
                run_id=run.run_id,
                artifact_type="patch_review",
                title=f"补丁评审 — {task_title}",
                content_markdown=text,
                content_json=json.dumps(content_json, ensure_ascii=False) if content_json else None,
                status="draft",
            )
            db.add(review_art)
            db.commit()

            return {
                "run_id": run.run_id,
                "trace_id": run.trace_id,
                "dev_artifact_id": review_art.dev_artifact_id,
                "artifact_type": "patch_review",
                "risk_level": risk_level,
                "review_score": review_score,
                "should_apply": should_apply,
                "status": "succeeded",
                "model_name": model_name,
            }
        except Exception as e:
            run.status = "failed"
            run.error_message = sanitize_text(str(e))[:500]
            run.finished_at = _now()
            db.commit()
            logger.error(f"patch_review 生成失败: {e}")
            return {
                "run_id": run.run_id,
                "trace_id": run.trace_id,
                "dev_artifact_id": None,
                "artifact_type": "patch_review",
                "status": "failed",
                "error_message": run.error_message,
            }

    # ── Artifact CRUD ──────────────────────────────────────────

    @staticmethod
    def get_artifact(db: Session, dev_artifact_id: str) -> Dict[str, Any]:
        a = db.query(DevArtifact).filter(DevArtifact.dev_artifact_id == dev_artifact_id).first()
        if not a:
            return None
        return {
            "dev_artifact_id": a.dev_artifact_id,
            "dev_task_id": a.dev_task_id,
            "run_id": a.run_id,
            "artifact_type": a.artifact_type,
            "title": a.title,
            "content_markdown": a.content_markdown,
            "content_json": a.content_json,
            "status": a.status,
            "batch_id": getattr(a, "batch_id", None),
            "batch_index": getattr(a, "batch_index", None),
            "parent_artifact_id": getattr(a, "parent_artifact_id", None),
            "reference_artifact_ids": json.loads(a.reference_artifact_ids) if getattr(a, "reference_artifact_ids", None) else None,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "updated_at": a.updated_at.isoformat() if a.updated_at else None,
        }

    @staticmethod
    def update_artifact(db: Session, dev_artifact_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        a = db.query(DevArtifact).filter(DevArtifact.dev_artifact_id == dev_artifact_id).first()
        if not a:
            return None
        if "title" in data:
            a.title = data["title"]
        if "content_markdown" in data:
            a.content_markdown = data["content_markdown"]
        if "status" in data and data["status"] in ("draft", "confirmed", "archived"):
            a.status = data["status"]
        a.updated_at = _now()
        db.commit()
        return DevStudioService.get_artifact(db, dev_artifact_id)

    @staticmethod
    def export_artifact(db: Session, dev_artifact_id: str) -> Optional[Dict[str, Any]]:
        a = db.query(DevArtifact).filter(DevArtifact.dev_artifact_id == dev_artifact_id).first()
        if not a:
            return None
        filename = f"{a.artifact_type}_{a.dev_artifact_id}.md"
        return {
            "filename": filename,
            "content": a.content_markdown or "",
            "content_type": "text/markdown; charset=utf-8",
        }

    # ── Run 查询 ──────────────────────────────────────────────

    @staticmethod
    def get_run(db: Session, run_id: str) -> Dict[str, Any]:
        r = db.query(DevStudioRun).filter(DevStudioRun.run_id == run_id).first()
        if not r:
            return None
        return {
            "run_id": r.run_id,
            "dev_task_id": r.dev_task_id,
            "run_type": r.run_type,
            "status": r.status,
            "model_name": r.model_name,
            "trace_id": r.trace_id,
            "error_message": r.error_message,
            "input_payload": r.input_payload,
            "output_text": r.output_text,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
