"""
AI Dev Studio Phase 7 — CodeMap 服务层
职责: 代码结构扫描 + 基于 CodeMap 的增强影响文件分析 (file_impact_v2)
"""

import os
import uuid
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import desc

from database.models import CodeMapSnapshot, CodeMapFile, DevTask, DevArtifact, DevStudioRun
from services.sanitize import sanitize_text

logger = logging.getLogger("code_map")


def _uid() -> str:
    return uuid.uuid4().hex[:16]


def _now() -> datetime:
    return datetime.now()


# ── 文件类型 / 分类映射 ──────────────────────────────────────────

EXT_TYPE_MAP = {
    ".py": "py", ".pyx": "py",
    ".js": "js", ".jsx": "jsx", ".ts": "ts", ".tsx": "tsx",
    ".json": "json", ".yaml": "yaml", ".yml": "yaml", ".toml": "toml",
    ".md": "md", ".txt": "txt", ".rst": "rst",
    ".sql": "sql",
    ".html": "html", ".css": "css", ".scss": "scss",
    ".sh": "sh", ".bat": "bat", ".ps1": "ps1",
    ".env": "env", ".cfg": "cfg", ".ini": "ini",
}

# 基于 relative_path 前缀判断 category
CATEGORY_RULES = [
    ("routes/",              "route"),
    ("services/",            "service"),
    ("database/",            "model"),
    ("backend/",             "backend"),
    ("agent/",               "agent"),
    ("frontend/src/pages/",  "page"),
    ("frontend/src/components/", "component"),
    ("frontend/src/",        "frontend"),
    ("scripts/",             "script"),
    ("tests/",               "test"),
    ("docs/",                "doc"),
    ("config/",              "config"),
    ("configs/",             "config"),
    (".github/",             "ci"),
    (".windsurf/",           "config"),
]

# 忽略的目录
SKIP_DIRS = {
    "__pycache__", "node_modules", ".git", ".venv", "venv", "env",
    "dist", "build", ".next", ".nuxt", "coverage", ".mypy_cache",
    ".pytest_cache", ".tox", "egg-info", ".eggs", "htmlcov",
    "data",  # SQLite数据目录
}

# 忽略的文件模式
SKIP_FILES = {".pyc", ".pyo", ".so", ".dll", ".exe", ".db", ".sqlite", ".sqlite3"}

# 最大扫描文件数
MAX_FILES = 2000


def _classify_file(rel_path: str) -> str:
    """根据相对路径分类"""
    norm = rel_path.replace("\\", "/")
    for prefix, cat in CATEGORY_RULES:
        if norm.startswith(prefix):
            return cat
    return "other"


def _extract_module(rel_path: str) -> Optional[str]:
    """提取模块名"""
    name = Path(rel_path).stem
    if name in ("__init__", "__main__", "index"):
        return Path(rel_path).parent.name or None
    return name


def _count_lines(filepath: str) -> int:
    """安全统计行数"""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


class CodeMapService:
    """代码结构扫描 + 影响文件增强分析"""

    # ── 扫描项目 ──────────────────────────────────────────────

    @staticmethod
    def scan_project(
        db: Session,
        project_root: str,
        dev_task_id: str = None,
    ) -> Dict[str, Any]:
        """扫描项目代码结构，生成 CodeMapSnapshot + CodeMapFile 记录"""
        root = Path(project_root).resolve()
        if not root.is_dir():
            return {"error": f"项目路径不存在: {project_root}"}

        snapshot_id = f"cmap_{_uid()}"
        start_ms = time.time()

        files_data = []
        dir_set = set()

        for dirpath, dirnames, filenames in os.walk(root):
            # 过滤忽略目录
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]

            for fname in filenames:
                if len(files_data) >= MAX_FILES:
                    break

                ext = Path(fname).suffix.lower()
                if ext in SKIP_FILES:
                    continue

                full_path = os.path.join(dirpath, fname)
                try:
                    rel_path = os.path.relpath(full_path, root).replace("\\", "/")
                except ValueError:
                    continue

                file_type = EXT_TYPE_MAP.get(ext, ext.lstrip(".") or "unknown")
                category = _classify_file(rel_path)
                module = _extract_module(rel_path)

                try:
                    size = os.path.getsize(full_path)
                except OSError:
                    size = 0

                # 只统计文本文件行数
                lines = 0
                if file_type in ("py", "js", "jsx", "ts", "tsx", "json", "yaml", "md", "sql", "html", "css"):
                    lines = _count_lines(full_path)

                files_data.append({
                    "file_path": full_path.replace("\\", "/"),
                    "relative_path": rel_path,
                    "file_type": file_type,
                    "category": category,
                    "module": module,
                    "size_bytes": size,
                    "line_count": lines,
                })

                dir_set.add(os.path.dirname(rel_path))

            if len(files_data) >= MAX_FILES:
                break

        elapsed_ms = int((time.time() - start_ms) * 1000)
        backend_count = sum(1 for f in files_data if f["category"] in ("route", "service", "model", "backend", "agent"))
        frontend_count = sum(1 for f in files_data if f["category"] in ("page", "component", "frontend"))

        # 保存 Snapshot
        snapshot = CodeMapSnapshot(
            snapshot_id=snapshot_id,
            dev_task_id=dev_task_id,
            project_root=str(root).replace("\\", "/"),
            total_files=len(files_data),
            total_dirs=len(dir_set),
            backend_files=backend_count,
            frontend_files=frontend_count,
            scan_duration_ms=elapsed_ms,
            status="completed",
            created_at=_now(),
        )
        db.add(snapshot)

        # 保存 Files
        for fd in files_data:
            db.add(CodeMapFile(
                snapshot_id=snapshot_id,
                file_path=fd["file_path"],
                relative_path=fd["relative_path"],
                file_type=fd["file_type"],
                category=fd["category"],
                module=fd["module"],
                size_bytes=fd["size_bytes"],
                line_count=fd["line_count"],
                created_at=_now(),
            ))

        db.commit()
        logger.info(f"CodeMap 扫描完成: {len(files_data)} 文件, {len(dir_set)} 目录, {elapsed_ms}ms")

        return {
            "snapshot_id": snapshot_id,
            "dev_task_id": dev_task_id,
            "project_root": str(root).replace("\\", "/"),
            "total_files": len(files_data),
            "total_dirs": len(dir_set),
            "backend_files": backend_count,
            "frontend_files": frontend_count,
            "scan_duration_ms": elapsed_ms,
            "status": "completed",
        }

    # ── 查询 Snapshot ────────────────────────────────────────

    @staticmethod
    def get_snapshot(db: Session, snapshot_id: str) -> Optional[Dict[str, Any]]:
        s = db.query(CodeMapSnapshot).filter(CodeMapSnapshot.snapshot_id == snapshot_id).first()
        if not s:
            return None

        # 按 category 聚合
        files = db.query(CodeMapFile).filter(CodeMapFile.snapshot_id == snapshot_id).all()
        cat_summary = {}
        for f in files:
            cat_summary[f.category] = cat_summary.get(f.category, 0) + 1

        return {
            "snapshot_id": s.snapshot_id,
            "dev_task_id": s.dev_task_id,
            "project_root": s.project_root,
            "total_files": s.total_files,
            "total_dirs": s.total_dirs,
            "backend_files": s.backend_files,
            "frontend_files": s.frontend_files,
            "scan_duration_ms": s.scan_duration_ms,
            "status": s.status,
            "category_summary": cat_summary,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }

    @staticmethod
    def list_snapshots(db: Session, dev_task_id: str = None) -> List[Dict[str, Any]]:
        q = db.query(CodeMapSnapshot)
        if dev_task_id:
            q = q.filter(CodeMapSnapshot.dev_task_id == dev_task_id)
        q = q.order_by(desc(CodeMapSnapshot.created_at))
        return [
            {
                "snapshot_id": s.snapshot_id,
                "dev_task_id": s.dev_task_id,
                "total_files": s.total_files,
                "backend_files": s.backend_files,
                "frontend_files": s.frontend_files,
                "scan_duration_ms": s.scan_duration_ms,
                "status": s.status,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in q.limit(50).all()
        ]

    @staticmethod
    def get_snapshot_files(
        db: Session, snapshot_id: str, category: str = None, file_type: str = None
    ) -> List[Dict[str, Any]]:
        """获取 snapshot 下的文件列表，支持按 category / file_type 过滤"""
        q = db.query(CodeMapFile).filter(CodeMapFile.snapshot_id == snapshot_id)
        if category:
            q = q.filter(CodeMapFile.category == category)
        if file_type:
            q = q.filter(CodeMapFile.file_type == file_type)
        q = q.order_by(CodeMapFile.category, CodeMapFile.relative_path)
        return [
            {
                "relative_path": f.relative_path,
                "file_type": f.file_type,
                "category": f.category,
                "module": f.module,
                "size_bytes": f.size_bytes,
                "line_count": f.line_count,
            }
            for f in q.limit(500).all()
        ]

    # ── 增强影响文件分析 (file_impact_v2) ──────────────────────

    @staticmethod
    def generate_file_impact_v2(
        db: Session,
        dev_task_id: str,
        snapshot_id: str,
    ) -> Dict[str, Any]:
        """基于 CodeMap 真实文件结构 + AI 生成增强影响文件分析"""
        task = db.query(DevTask).filter(DevTask.dev_task_id == dev_task_id).first()
        if not task:
            return None

        snapshot = db.query(CodeMapSnapshot).filter(
            CodeMapSnapshot.snapshot_id == snapshot_id
        ).first()
        if not snapshot:
            return {"_not_found": "snapshot"}

        # 读取文件列表
        files = db.query(CodeMapFile).filter(
            CodeMapFile.snapshot_id == snapshot_id
        ).order_by(CodeMapFile.category, CodeMapFile.relative_path).all()

        # 构造文件列表摘要（按 category 分组）
        file_summary = _build_file_summary(files)

        # 加载任务上下文
        context_parts = []
        if task.description:
            context_parts.append(f"## 需求描述\n{task.description}")

        # 加载已有产物上下文（dev_plan, api_design 等）
        existing_arts = db.query(DevArtifact).filter(
            DevArtifact.dev_task_id == dev_task_id,
        ).order_by(desc(DevArtifact.created_at)).all()
        for ea in existing_arts:
            if ea.artifact_type in ("dev_plan", "api_design", "db_design") and ea.content_markdown:
                title = ea.artifact_type.replace("_", " ").title()
                context_parts.append(f"## 已有 {title}\n{ea.content_markdown[:3000]}")

        context = "\n\n".join(context_parts)

        # 构造 Prompt
        prompt = _build_file_impact_v2_prompt(context, task.title, file_summary, snapshot.total_files)

        # 创建 Run
        run = DevStudioRun(
            run_id=f"drun_{_uid()}",
            dev_task_id=dev_task_id,
            run_type="file_impact_v2",
            trace_id=f"dtrace_{_uid()}",
            input_payload={
                "task_title": task.title,
                "snapshot_id": snapshot_id,
                "total_files": snapshot.total_files,
            },
            status="running",
            started_at=_now(),
        )
        db.add(run)
        db.commit()

        try:
            from agent.llm_client import get_llm_client
            client = get_llm_client()
            model_name = f"{client.provider}/{client.model}"
            is_mock = client.provider == "mock"

            text = client.generate(
                prompt=prompt,
                system_prompt="你是 AI Dev Studio 的智能助手，请基于真实项目代码结构输出影响文件分析。",
                temperature=0.2,
                max_tokens=8000,
            )

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
                artifact_type="file_impact_v2",
                title=f"增强影响文件分析 — {task.title}",
                content_markdown=text,
                status="draft",
            )
            db.add(artifact)
            db.commit()

            return {
                "run_id": run.run_id,
                "trace_id": run.trace_id,
                "dev_artifact_id": artifact.dev_artifact_id,
                "artifact_type": "file_impact_v2",
                "status": "succeeded",
                "model_name": model_name,
                "is_mock": is_mock,
                "snapshot_id": snapshot_id,
                "files_analyzed": snapshot.total_files,
            }

        except Exception as e:
            run.status = "failed"
            run.error_message = sanitize_text(str(e))[:500]
            run.finished_at = _now()
            db.commit()
            logger.error(f"file_impact_v2 生成失败: {e}")
            return {
                "run_id": run.run_id,
                "trace_id": run.trace_id,
                "dev_artifact_id": None,
                "artifact_type": "file_impact_v2",
                "status": "failed",
                "error_message": run.error_message,
                "snapshot_id": snapshot_id,
            }


# ── 辅助函数 ──────────────────────────────────────────────────

def _build_file_summary(files: list) -> str:
    """按 category 分组构造文件列表摘要"""
    groups = {}
    for f in files:
        cat = f.category
        if cat not in groups:
            groups[cat] = []
        groups[cat].append(f)

    CATEGORY_LABELS = {
        "route": "路由层 (Routes)",
        "service": "服务层 (Services)",
        "model": "数据模型 (Database)",
        "backend": "后端核心 (Backend)",
        "agent": "AI Agent",
        "page": "前端页面 (Pages)",
        "component": "前端组件 (Components)",
        "frontend": "前端其他",
        "script": "脚本 (Scripts)",
        "test": "测试 (Tests)",
        "doc": "文档 (Docs)",
        "config": "配置 (Config)",
        "ci": "CI/CD",
        "other": "其他",
    }

    parts = []
    for cat in ("route", "service", "model", "backend", "agent",
                "page", "component", "frontend",
                "script", "config", "doc", "ci", "other"):
        if cat not in groups:
            continue
        label = CATEGORY_LABELS.get(cat, cat)
        items = groups[cat]
        parts.append(f"\n### {label} ({len(items)} 文件)")
        for f in items[:30]:  # 每类最多30
            parts.append(f"- `{f.relative_path}` ({f.line_count} 行, {f.file_type})")
        if len(items) > 30:
            parts.append(f"- ... 以及 {len(items) - 30} 个其他文件")

    return "\n".join(parts)


def _build_file_impact_v2_prompt(context: str, task_title: str, file_summary: str, total_files: int) -> str:
    return f"""你是 AI Dev Studio 的影响文件分析专家。

当前项目共有 {total_files} 个文件。以下是真实的项目代码结构：

{file_summary}

---

任务标题: {task_title}

{context}

---

请基于以上真实项目代码结构，分析实现该需求需要修改或新增哪些文件。

## 输出要求

请输出 Markdown 格式，包含以下内容：

### 1. 影响文件总览

| # | 文件路径 | 文件类型 | 当前职责 | 修改原因 | 置信度 | 风险等级 | 需人工确认 |
|---|---|---|---|---|---|---|---|
| 1 | routes/xxx.py | route | xxx路由 | 新增xxx接口 | 高 | 低 | 否 |

置信度: 高(文件确实存在且明确需要修改) / 中(可能需要修改) / 低(不确定)
风险等级: 高(核心逻辑/数据模型) / 中(业务逻辑) / 低(配置/文档)
需人工确认: 是/否

### 2. 需要新增的文件

如果需要新增文件，列出建议的文件路径和职责。

### 3. 影响范围评估

- 后端影响文件数
- 前端影响文件数
- 数据库变更: 是/否
- 新增 API: 数量
- 风险评估

### 4. 修改建议

对每个高风险文件，给出具体的修改建议要点。

### 5. 注意事项

列出实现过程中需要特别注意的事项。

**重要**:
- 只列出项目中真实存在的文件路径，不要编造不存在的文件
- 如果建议新增文件，明确标注为"新增"
- 置信度要诚实，不确定的标为"低"
- 这是分析建议，不是自动修改，所有改动需人工确认
"""
