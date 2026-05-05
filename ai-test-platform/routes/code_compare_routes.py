#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
需求-代码对比路由 (v2)

端点:
  POST /api/v2/code-compare/upload                            上传代码 ZIP 快照
  POST /api/v2/code-compare/clone-repo                        从 Git 仓库克隆代码
  POST /api/v2/code-compare/analyze                           执行需求-代码对比分析
  GET  /api/v2/code-compare/reports                           历史报告列表
  GET  /api/v2/code-compare/reports/{id}                      报告详情
  POST /api/v2/code-compare/reports/{id}/confirm              人工确认 finding
  POST /api/v2/code-compare/cache-requirement                 缓存需求
  POST /api/v2/code-compare/findings/{id}/convert-to-defect   转缺陷
  POST /api/v2/code-compare/findings/{id}/convert-to-test-case 转测试用例
  POST /api/v2/code-compare/findings/{id}/convert-to-question  转待确认问题
  POST /api/v2/code-compare/findings/{id}/mark-false-positive  标记误报
  POST /api/v2/code-compare/findings/{id}/push-to-tapd        推送 finding 到 TAPD
  GET  /api/v2/code-compare/tapd/config                        获取 TAPD 配置
  POST /api/v2/code-compare/tapd/config                        保存 TAPD 配置
  POST /api/v2/code-compare/tapd/test                          测试 TAPD 连接
"""

import io
import json
import os
import re
import shutil
import subprocess
import uuid
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

# ── 导入解析工具 ──
try:
    from utils.code_analyzer import scan_code_directory, summarize_code_analysis
    CODE_ANALYZER_AVAILABLE = True
except ImportError:
    CODE_ANALYZER_AVAILABLE = False

try:
    from utils.document_parser import parse_document_structured, parse_axure_folder_structured
    DOC_PARSER_AVAILABLE = True
except ImportError:
    DOC_PARSER_AVAILABLE = False

try:
    from utils.req_code_diff import run_req_code_diff
    DIFF_ENGINE_AVAILABLE = True
except ImportError:
    DIFF_ENGINE_AVAILABLE = False

try:
    from ai.ai_client import get_ai_client
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

try:
    from database.session import get_db_session
    from database.models import Defect, DefectEvent, TestCase
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

router = APIRouter()

# ── 持久化目录 ──
DATA_DIR = Path("data/code_compare")
DATA_DIR.mkdir(parents=True, exist_ok=True)
SNAPSHOT_DIR = Path("data/code_snapshots")
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR = DATA_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
QUESTIONS_DIR = DATA_DIR / "questions"
QUESTIONS_DIR.mkdir(parents=True, exist_ok=True)
REQ_CACHE_DIR = DATA_DIR / "req_cache"
REQ_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ── 内存缓存（启动时从磁盘加载） ──
_code_snapshots: dict = {}
_reports: dict = {}
_requirement_cache: dict = {}
_questions: dict = {}


def _load_persisted_reports():
    """启动时从磁盘加载已有报告"""
    for f in REPORTS_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            _reports[data["report_id"]] = data
        except Exception:
            pass


def _load_persisted_requirements():
    """启动时从磁盘加载已缓存的需求数据"""
    for f in REQ_CACHE_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            req_id = f.stem  # filename without .json
            _requirement_cache[req_id] = data
        except Exception:
            pass


def _save_requirement_cache(req_id: str, data: dict):
    """持久化需求缓存到磁盘"""
    path = REQ_CACHE_DIR / f"{req_id}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_persisted_snapshots():
    """启动时从磁盘加载已有的代码快照元数据"""
    for snap_dir in SNAPSHOT_DIR.iterdir():
        if not snap_dir.is_dir():
            continue
        sid = snap_dir.name
        meta_file = snap_dir / "_snapshot_meta.json"
        if meta_file.exists():
            try:
                info = json.loads(meta_file.read_text(encoding="utf-8"))
                sid = info.get("meta", {}).get("snapshot_id") or sid
                info["path"] = str(snap_dir)
                _code_snapshots[sid] = info
            except Exception:
                pass
        elif sid.startswith("snap_"):
            # 兼容旧快照：没有 meta 文件但目录存在，自动恢复
            total_files = sum(1 for _ in snap_dir.rglob("*") if _.is_file())
            meta = {
                "snapshot_id": sid,
                "name": sid,
                "total_files": total_files,
                "upload_time": datetime.fromtimestamp(snap_dir.stat().st_mtime).isoformat(),
            }
            info = {"meta": meta, "path": str(snap_dir)}
            _code_snapshots[sid] = info
            _save_snapshot_meta(sid, info)


def _save_snapshot_meta(snapshot_id: str, info: dict):
    """持久化快照元数据到对应目录"""
    snap_dir = Path(info["path"])
    meta_file = snap_dir / "_snapshot_meta.json"
    meta_file.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")


_load_persisted_reports()
_load_persisted_requirements()
_load_persisted_snapshots()


def _save_report(report: dict):
    """持久化报告到磁盘"""
    path = REPORTS_DIR / f"{report['report_id']}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def _save_question(q: dict):
    path = QUESTIONS_DIR / f"{q['question_id']}.json"
    path.write_text(json.dumps(q, ensure_ascii=False, indent=2), encoding="utf-8")


# ── ZIP 安全常量 ──
MAX_ZIP_SIZE = 50 * 1024 * 1024       # 50MB
MAX_SINGLE_FILE_SIZE = 2 * 1024 * 1024  # 2MB

IGNORED_DIRS = {
    'node_modules', '.git', 'dist', 'build', 'target',
    'coverage', '__pycache__', '.venv', 'venv',
}

SENSITIVE_FILES = {
    '.env', '.pem', '.key', 'id_rsa', 'id_dsa',
    'credentials.json', 'application-prod.yml', 'application-prod.properties',
}
SENSITIVE_PATTERNS = re.compile(
    r'config\.secret\.|id_rsa|id_dsa|\.pem$|\.key$|credentials\.json'
    r'|application-prod\.(yml|properties)',
    re.IGNORECASE,
)

SENSITIVE_CONTENT_PATTERNS = re.compile(
    r'(?i)(token|password|secret|authorization|cookie|api_key|access_key|private_key)'
    r'\s*[:=]\s*[\'"]?[^\s\'"]{8,}',
)


def _is_sensitive_file(name: str) -> bool:
    base = os.path.basename(name).lower()
    return base in SENSITIVE_FILES or bool(SENSITIVE_PATTERNS.search(name))


def _sanitize_content(text: str) -> str:
    """脱敏文本中的敏感值"""
    return SENSITIVE_CONTENT_PATTERNS.sub(
        lambda m: m.group(1) + ' = ***REDACTED***', text
    )


def _is_in_ignored_dir(name: str) -> bool:
    parts = Path(name).parts
    return any(p in IGNORED_DIRS for p in parts)


# ── 请求模型 ──

class CloneRepoRequest(BaseModel):
    repo_url: str                        # Git 仓库地址
    branch: str = "main"                 # 分支名
    token: Optional[str] = None          # 私有仓库 Access Token
    sub_dir: Optional[str] = None        # 仅扫描子目录 (如 "src")


class AnalyzeRequest(BaseModel):
    requirement_id: Optional[str] = None
    requirement_text: Optional[str] = None
    code_snapshot_id: str
    project_id: Optional[str] = None
    use_ai: bool = True
    provider: Optional[str] = None
    model: Optional[str] = None


class ConfirmRequest(BaseModel):
    finding_id: str
    manual_status: str


class ConvertToDefectRequest(BaseModel):
    severity: str = "major"       # critical | major | minor
    priority: str = "P2"          # P0 | P1 | P2
    assignee: Optional[str] = ""
    review_comment: Optional[str] = ""


class ConvertToTestCaseRequest(BaseModel):
    case_priority: str = "P1"     # P0 | P1 | P2
    case_type: str = "whitebox_enhanced"
    module_name: Optional[str] = ""


class ConvertToQuestionRequest(BaseModel):
    owner: str = "product"
    question: str
    review_comment: Optional[str] = ""


class MarkFalsePositiveRequest(BaseModel):
    reason: str


class TapdConfigRequest(BaseModel):
    workspace_id: str
    api_user: str
    api_password: str
    default_reporter: Optional[str] = ""
    default_assignee: Optional[str] = ""
    default_bug_type: Optional[str] = "codeerr"


class PushToTapdRequest(BaseModel):
    title: Optional[str] = None
    severity: Optional[str] = None
    priority: Optional[str] = None
    assignee: Optional[str] = None
    iteration: Optional[str] = None       # 迭代名称，如 "1.2.3"
    module: Optional[str] = None          # 模块名
    steps: Optional[str] = None           # 操作步骤
    expected: Optional[str] = None        # 预期结果
    actual: Optional[str] = None          # 实际结果
    code_location: Optional[str] = None   # 代码位置


# ══════════════════════════════════════════════════════════════════
#  1. 上传代码快照（含安全加固）
# ══════════════════════════════════════════════════════════════════

@router.post("/api/v2/code-compare/upload")
async def upload_code_snapshot(file: UploadFile = File(...)):
    """上传代码 ZIP 并解压为快照（安全加固版）"""
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="仅支持 ZIP 格式")

    content = await file.read()
    if len(content) > MAX_ZIP_SIZE:
        raise HTTPException(status_code=400, detail=f"文件过大，最大 {MAX_ZIP_SIZE // 1024 // 1024}MB")

    try:
        zf = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="ZIP 格式错误，无法解压")

    snapshot_id = f"snap_{uuid.uuid4().hex[:12]}"
    extract_dir = SNAPSHOT_DIR / snapshot_id
    extract_dir.mkdir(parents=True, exist_ok=True)
    abs_extract = extract_dir.resolve()

    skipped_sensitive = []
    skipped_large = []
    skipped_ignored = []

    try:
        for info in zf.infolist():
            name = info.filename
            # ── Zip Slip 防护 ──
            if name.startswith('/') or '..' in name:
                zf.close()
                shutil.rmtree(str(extract_dir), ignore_errors=True)
                raise HTTPException(status_code=400, detail=f"ZIP 包存在路径穿越风险: {name}")
            target = (extract_dir / name).resolve()
            if not str(target).startswith(str(abs_extract)):
                zf.close()
                shutil.rmtree(str(extract_dir), ignore_errors=True)
                raise HTTPException(status_code=400, detail=f"ZIP 包存在路径穿越风险: {name}")

            # 目录
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue

            # ── 忽略目录 ──
            if _is_in_ignored_dir(name):
                skipped_ignored.append(name)
                continue

            # ── 敏感文件 ──
            if _is_sensitive_file(name):
                skipped_sensitive.append(name)
                continue

            # ── 单文件大小 ──
            if info.file_size > MAX_SINGLE_FILE_SIZE:
                skipped_large.append(name)
                continue

            # 安全解压
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, open(target, 'wb') as dst:
                dst.write(src.read())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解压失败: {str(e)}")
    finally:
        zf.close()

    # 统计
    total_files = 0
    lang_dist = {}
    ext_lang = {
        '.vue': 'Vue', '.js': 'JavaScript', '.ts': 'TypeScript', '.jsx': 'JSX',
        '.py': 'Python', '.java': 'Java', '.html': 'HTML', '.css': 'CSS',
        '.scss': 'SCSS', '.less': 'Less', '.json': 'JSON', '.xml': 'XML',
    }
    top_dirs = set()
    for root, dirs, files in os.walk(extract_dir):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        rel = os.path.relpath(root, extract_dir)
        parts = rel.split(os.sep)
        if len(parts) >= 1 and parts[0] != '.':
            top_dirs.add(parts[0])
        for fname in files:
            ext = Path(fname).suffix.lower()
            if ext in ext_lang:
                lang_dist[ext_lang[ext]] = lang_dist.get(ext_lang[ext], 0) + 1
            total_files += 1

    meta = {
        "snapshot_id": snapshot_id,
        "name": file.filename.replace('.zip', ''),
        "total_files": total_files,
        "language_distribution": lang_dist,
        "ignored_dirs": sorted(IGNORED_DIRS),
        "top_dirs": sorted(top_dirs)[:20],
        "upload_time": datetime.now().isoformat(),
        "security": {
            "skipped_sensitive": len(skipped_sensitive),
            "skipped_large": len(skipped_large),
            "skipped_ignored_dirs": len(skipped_ignored),
        },
    }
    snap_info = {"meta": meta, "path": str(extract_dir)}
    _code_snapshots[snapshot_id] = snap_info
    _save_snapshot_meta(snapshot_id, snap_info)

    return {"success": True, "snapshot": meta}


# ══════════════════════════════════════════════════════════════════
#  1b. 从 Git 仓库克隆代码
# ══════════════════════════════════════════════════════════════════

@router.post("/api/v2/code-compare/clone-repo")
async def clone_repo(request: CloneRepoRequest):
    """从 Git 仓库克隆代码创建快照"""
    repo_url = request.repo_url.strip()
    if not repo_url:
        raise HTTPException(status_code=400, detail="请提供 Git 仓库地址")

    # 安全校验：仅允许 http(s) 和 git@ 协议
    if not (repo_url.startswith("http://") or repo_url.startswith("https://") or repo_url.startswith("git@")):
        raise HTTPException(status_code=400, detail="仅支持 http(s) 或 git@ 协议的仓库地址")

    snapshot_id = f"snap_{uuid.uuid4().hex[:12]}"
    clone_dir = SNAPSHOT_DIR / snapshot_id

    # 构造 clone URL（注入 token 用于私有仓库）
    clone_url = repo_url
    if request.token and repo_url.startswith("https://"):
        # https://token@gitlab.example.com/group/repo.git
        clone_url = repo_url.replace("https://", f"https://oauth2:{request.token}@")

    try:
        cmd = [
            "git", "clone",
            "--depth", "1",
            "--single-branch",
            "--branch", request.branch,
            clone_url,
            str(clone_dir),
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
        if result.returncode != 0:
            err = result.stderr.strip()
            # 隐藏 token 信息
            if request.token:
                err = err.replace(request.token, "***")
            raise HTTPException(status_code=400, detail=f"Git 克隆失败: {err}")
    except subprocess.TimeoutExpired:
        shutil.rmtree(clone_dir, ignore_errors=True)
        raise HTTPException(status_code=408, detail="Git 克隆超时 (120s)，请检查仓库地址或网络")
    except HTTPException:
        raise
    except Exception as e:
        shutil.rmtree(clone_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"克隆异常: {str(e)}")

    # 删除 .git 目录节省空间
    git_dir = clone_dir / ".git"
    if git_dir.exists():
        shutil.rmtree(git_dir, ignore_errors=True)

    # 如果指定了子目录，则把子目录作为根
    scan_dir = clone_dir
    if request.sub_dir:
        sub = clone_dir / request.sub_dir.strip("/")
        if sub.exists() and sub.is_dir():
            scan_dir = sub
        else:
            shutil.rmtree(clone_dir, ignore_errors=True)
            raise HTTPException(status_code=400, detail=f"子目录不存在: {request.sub_dir}")

    # 删除忽略目录和敏感文件
    for root, dirs, files in os.walk(scan_dir, topdown=True):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for fn in files:
            fp = os.path.join(root, fn)
            if _is_sensitive_file(fn):
                os.remove(fp)

    # 统计
    total_files = sum(1 for _ in scan_dir.rglob("*") if _.is_file())
    lang_dist = {}
    ext_map = {".py": "Python", ".js": "JavaScript", ".jsx": "React/JSX",
               ".ts": "TypeScript", ".tsx": "React/TSX", ".vue": "Vue",
               ".java": "Java", ".go": "Go", ".rs": "Rust", ".rb": "Ruby"}
    top_dirs = set()
    for f in scan_dir.rglob("*"):
        if f.is_file():
            ext = f.suffix.lower()
            if ext in ext_map:
                lang_dist[ext_map[ext]] = lang_dist.get(ext_map[ext], 0) + 1
            rel = f.relative_to(scan_dir)
            if len(rel.parts) > 1:
                top_dirs.add(rel.parts[0])

    # 提取仓库名
    repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    branch_label = request.branch

    meta = {
        "snapshot_id": snapshot_id,
        "name": f"{repo_name} ({branch_label})",
        "source": "git_clone",
        "repo_url": repo_url,
        "branch": branch_label,
        "total_files": total_files,
        "language_distribution": lang_dist,
        "top_dirs": sorted(top_dirs)[:20],
        "upload_time": datetime.now().isoformat(),
    }
    snap_info = {"meta": meta, "path": str(scan_dir)}
    _code_snapshots[snapshot_id] = snap_info
    _save_snapshot_meta(snapshot_id, snap_info)

    return {"success": True, "snapshot": meta}


# ══════════════════════════════════════════════════════════════════
#  2. 执行对比分析
# ══════════════════════════════════════════════════════════════════

@router.post("/api/v2/code-compare/analyze")
async def analyze_requirement_code(request: AnalyzeRequest):
    """需求-代码对比分析"""
    if not CODE_ANALYZER_AVAILABLE:
        raise HTTPException(status_code=503, detail="代码分析模块不可用")
    if not DIFF_ENGINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="对比引擎模块不可用")

    snap = _code_snapshots.get(request.code_snapshot_id)
    if not snap:
        raise HTTPException(status_code=404, detail=f"代码快照不存在: {request.code_snapshot_id}")

    code_path = snap["path"]
    requirement_data = None
    if request.requirement_id and request.requirement_id in _requirement_cache:
        requirement_data = _requirement_cache[request.requirement_id]
    if not requirement_data and request.requirement_text:
        requirement_data = _text_to_requirement_data(request.requirement_text)
    if not requirement_data:
        raise HTTPException(status_code=400, detail="缺少需求数据：请提供 requirement_id 或 requirement_text")

    try:
        code_analysis = scan_code_directory(code_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"代码扫描失败: {str(e)}")

    ai_client = None
    ai_mode = "rule_based"
    if request.use_ai and AI_AVAILABLE:
        try:
            ai_client = get_ai_client(provider=request.provider)
            if request.model and hasattr(ai_client, 'ai_config'):
                ai_client.ai_config["model"] = request.model
            actual_model = getattr(ai_client, 'ai_config', {}).get('model', '?')
            actual_provider = getattr(ai_client, 'provider', '?')
            print(f"🤖 代码对比使用: provider={actual_provider}, model={actual_model} (请求: provider={request.provider}, model={request.model})")
            ai_mode = "ai_deep"
        except Exception as e:
            print(f"⚠️ AI 客户端初始化失败，使用规则匹配: {e}")
            ai_mode = "fallback"

    try:
        diff_result = run_req_code_diff(requirement_data, code_analysis, ai_client=ai_client)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对比分析失败: {str(e)}")

    # 如果 AI diff 内部降级了也标记
    if diff_result.get("_ai_fallback"):
        ai_mode = "fallback"

    findings = _diff_to_findings(diff_result)

    # 脱敏 code_summary
    code_summary = _sanitize_content(summarize_code_analysis(code_analysis))

    report_id = f"rpt_{uuid.uuid4().hex[:12]}"
    report = {
        "report_id": report_id,
        "requirement_source": request.requirement_id or "manual_text",
        "code_snapshot_id": request.code_snapshot_id,
        "code_snapshot_name": snap["meta"]["name"],
        "project_id": request.project_id,
        "created_at": datetime.now().isoformat(),
        "ai_mode": ai_mode,
        "summary": {
            "total_req_points": diff_result["summary"]["total_req_points"],
            "implemented": len([f for f in findings if f["type"] == "implemented"]),
            "missing": len([f for f in findings if f["type"] == "missing"]),
            "extra": len([f for f in findings if f["type"] == "extra"]),
            "uncertain": len([f for f in findings if f["type"] == "uncertain"]),
            "risk": len([f for f in findings if f["type"] == "risk"]),
        },
        "findings": findings,
        "code_summary": code_summary,
    }
    _reports[report_id] = report
    _save_report(report)

    return {"success": True, "report": report}


# ══════════════════════════════════════════════════════════════════
#  3. 报告列表
# ══════════════════════════════════════════════════════════════════

@router.get("/api/v2/code-compare/reports")
async def get_reports():
    items = []
    for r in _reports.values():
        items.append({
            "report_id": r["report_id"],
            "requirement_source": r["requirement_source"],
            "code_snapshot_name": r.get("code_snapshot_name", ""),
            "summary": r["summary"],
            "ai_mode": r.get("ai_mode", "unknown"),
            "created_at": r["created_at"],
        })
    items.sort(key=lambda x: x["created_at"], reverse=True)
    return {"success": True, "reports": items}


# ══════════════════════════════════════════════════════════════════
#  4. 报告详情
# ══════════════════════════════════════════════════════════════════

@router.get("/api/v2/code-compare/reports/{report_id}")
async def get_report_detail(report_id: str):
    report = _reports.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"报告不存在: {report_id}")
    return {"success": True, "report": report}


# ══════════════════════════════════════════════════════════════════
#  5. 人工确认 finding
# ══════════════════════════════════════════════════════════════════

@router.post("/api/v2/code-compare/reports/{report_id}/confirm")
async def confirm_finding(report_id: str, request: ConfirmRequest):
    report = _reports.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"报告不存在: {report_id}")

    valid_statuses = {
        "confirmed_implemented", "confirmed_missing", "false_positive",
        "need_discussion", "converted_to_bug", "converted_to_case", "need_product_confirm",
    }
    if request.manual_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"无效状态，可选: {valid_statuses}")

    for f in report["findings"]:
        if f["finding_id"] == request.finding_id:
            f["manual_status"] = request.manual_status
            f["confirmed_at"] = datetime.now().isoformat()
            _save_report(report)
            return {"success": True, "finding": f}

    raise HTTPException(status_code=404, detail=f"finding 不存在: {request.finding_id}")


# ══════════════════════════════════════════════════════════════════
#  6. 缓存需求
# ══════════════════════════════════════════════════════════════════

@router.post("/api/v2/code-compare/cache-requirement")
async def cache_requirement(data: dict):
    req_id = f"req_{uuid.uuid4().hex[:12]}"
    _requirement_cache[req_id] = data
    _save_requirement_cache(req_id, data)
    return {"success": True, "requirement_id": req_id}


# ══════════════════════════════════════════════════════════════════
#  7. Finding → 缺陷
# ══════════════════════════════════════════════════════════════════

@router.post("/api/v2/code-compare/findings/{finding_id}/convert-to-defect")
async def convert_finding_to_defect(finding_id: str, request: ConvertToDefectRequest):
    report, finding = _find_finding(finding_id)

    evidence = finding.get("code_evidence") or {}
    suggestion = finding.get("test_suggestion") or {}
    steps = suggestion.get("steps", ["请根据分析说明复现"])
    steps_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps)) if isinstance(steps, list) else str(steps)

    description = (
        f"## 来源\n需求-代码对比分析\n\n"
        f"## 需求点\n{finding.get('requirement', '')}\n\n"
        f"## 分析说明\n{finding.get('analysis', '')}\n\n"
        f"## 代码证据\n"
        f"- 文件: {evidence.get('file', 'N/A')}\n"
        f"- 行号: {evidence.get('line', 'N/A')}\n"
        f"- 匹配原因: {evidence.get('match_reason', 'N/A')}\n\n"
        f"## 复现步骤\n{steps_text}\n\n"
        f"## 预期结果\n{suggestion.get('expected', 'N/A')}\n\n"
        f"## Finding ID\n{finding_id}"
    )

    defect_id = None
    if DB_AVAILABLE:
        try:
            with get_db_session() as db:
                defect = Defect(
                    title=f"[对比发现] {finding.get('requirement', '')[:200]}",
                    description=_sanitize_content(description),
                    severity=request.severity,
                    priority=request.priority,
                    source="whitebox_compare",
                    assigned_to=request.assignee or None,
                    evidence_json={
                        "finding_id": finding_id,
                        "finding_type": finding.get("type"),
                        "confidence": finding.get("confidence"),
                        "code_evidence": evidence,
                    },
                    created_by="code_compare",
                )
                db.add(defect)
                db.flush()
                defect_id = defect.id
                db.add(DefectEvent(
                    defect_id=defect.id,
                    event_type="status_change",
                    to_status="open",
                    comment=request.review_comment or "从需求-代码对比 Finding 转换",
                    created_by="code_compare",
                ))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"创建缺陷失败: {str(e)}")
    else:
        defect_id = f"defect_{uuid.uuid4().hex[:8]}"

    finding["manual_status"] = "converted_to_bug"
    finding["target_type"] = "defect"
    finding["target_id"] = str(defect_id)
    finding["converted_at"] = datetime.now().isoformat()
    finding["review_comment"] = request.review_comment
    _save_report(report)

    return {"success": True, "data": {"defect_id": defect_id, "finding_id": finding_id}}


# ══════════════════════════════════════════════════════════════════
#  8. Finding → 测试用例
# ══════════════════════════════════════════════════════════════════

@router.post("/api/v2/code-compare/findings/{finding_id}/convert-to-test-case")
async def convert_finding_to_test_case(finding_id: str, request: ConvertToTestCaseRequest):
    report, finding = _find_finding(finding_id)

    suggestions = []
    ts = finding.get("test_suggestion")
    if ts:
        suggestions = [ts] if isinstance(ts, dict) else ts
    if not suggestions:
        suggestions = [{
            "title": f"验证: {finding.get('requirement', '')[:80]}",
            "precondition": "系统正常运行",
            "steps": ["根据需求点进行操作", "检查实际结果"],
            "expected": "功能按需求正常工作",
        }]

    priority_map = {"P0": "critical", "P1": "high", "P2": "medium"}
    case_ids = []

    for idx, sug in enumerate(suggestions):
        case_id = f"TC_WB_{uuid.uuid4().hex[:8]}"
        steps = sug.get("steps", [])
        if isinstance(steps, str):
            steps = [steps]

        if DB_AVAILABLE:
            try:
                with get_db_session() as db:
                    tc = TestCase(
                        id=case_id,
                        title=sug.get("title", f"白盒用例-{finding_id}")[:500],
                        module=request.module_name or "需求-代码对比",
                        priority=priority_map.get(request.case_priority, "medium"),
                        steps=[{"step": i+1, "action": s, "expected": ""} for i, s in enumerate(steps)],
                        expected=sug.get("expected", ""),
                        source="whitebox_compare",
                        case_type="functional",
                        module_name=request.module_name or "需求-代码对比",
                        created_by="code_compare",
                        tags=["whitebox", "code_compare", finding_id],
                    )
                    db.add(tc)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"创建测试用例失败: {str(e)}")

        case_ids.append(case_id)

    finding["manual_status"] = "converted_to_case"
    finding["target_type"] = "test_case"
    finding["target_id"] = case_ids if len(case_ids) > 1 else case_ids[0]
    finding["converted_at"] = datetime.now().isoformat()
    _save_report(report)

    return {"success": True, "data": {"case_ids": case_ids, "finding_id": finding_id}}


# ══════════════════════════════════════════════════════════════════
#  9. Finding → 待确认问题
# ══════════════════════════════════════════════════════════════════

@router.post("/api/v2/code-compare/findings/{finding_id}/convert-to-question")
async def convert_finding_to_question(finding_id: str, request: ConvertToQuestionRequest):
    report, finding = _find_finding(finding_id)

    evidence = finding.get("code_evidence") or {}
    q_id = f"q_{uuid.uuid4().hex[:8]}"
    question = {
        "question_id": q_id,
        "title": f"[待确认] {finding.get('requirement', '')[:100]}",
        "question": request.question,
        "requirement_context": finding.get("requirement", ""),
        "code_evidence": evidence,
        "analysis": finding.get("analysis", ""),
        "owner": request.owner,
        "status": "open",
        "review_comment": request.review_comment,
        "finding_id": finding_id,
        "created_at": datetime.now().isoformat(),
    }
    _questions[q_id] = question
    _save_question(question)

    finding["manual_status"] = "need_product_confirm"
    finding["target_type"] = "question"
    finding["target_id"] = q_id
    finding["converted_at"] = datetime.now().isoformat()
    finding["review_comment"] = request.review_comment
    _save_report(report)

    return {"success": True, "data": {"question_id": q_id, "finding_id": finding_id}}


# ══════════════════════════════════════════════════════════════════
#  10. Finding → 标记误报
# ══════════════════════════════════════════════════════════════════

@router.post("/api/v2/code-compare/findings/{finding_id}/mark-false-positive")
async def mark_finding_false_positive(finding_id: str, request: MarkFalsePositiveRequest):
    if not request.reason.strip():
        raise HTTPException(status_code=400, detail="误报原因不能为空")

    report, finding = _find_finding(finding_id)
    finding["manual_status"] = "false_positive"
    finding["review_comment"] = request.reason
    finding["confirmed_at"] = datetime.now().isoformat()
    _save_report(report)

    return {"success": True, "data": {"finding_id": finding_id, "manual_status": "false_positive"}}


# ══════════════════════════════════════════════════════════════════
#  工具函数
# ══════════════════════════════════════════════════════════════════

def _find_finding(finding_id: str):
    """在所有报告中查找 finding，返回 (report, finding) 或抛 404"""
    for report in _reports.values():
        for f in report.get("findings", []):
            if f["finding_id"] == finding_id:
                return report, f
    raise HTTPException(status_code=404, detail=f"finding 不存在: {finding_id}")


def _text_to_requirement_data(text: str) -> dict:
    lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
    features = []
    rules = []
    for line in lines:
        if any(kw in line for kw in ('规则', '必须', '不允许', '校验', '限制', '要求')):
            rules.append(line)
        else:
            features.append({"name": line[:60], "description": line})
    return {
        "features": features,
        "rules": rules,
        "modules": [],
        "fields": [],
        "axure_notes": [],
        "stats": {"features": len(features), "rules": len(rules)}
    }


def _new_finding(ftype: str, requirement: str, confidence: float,
                 analysis: str, code_evidence=None, test_suggestion=None,
                 risk_level="medium") -> dict:
    """标准 Finding 构造"""
    return {
        "finding_id": f"f_{uuid.uuid4().hex[:8]}",
        "type": ftype,
        "requirement": requirement,
        "confidence": confidence,
        "analysis": _sanitize_content(analysis) if analysis else "",
        "risk_level": risk_level,
        "code_evidence": code_evidence,
        "test_suggestion": test_suggestion,
        "manual_status": None,
        "target_type": None,
        "target_id": None,
        "reviewer": None,
        "review_comment": None,
        "converted_at": None,
        "confirmed_at": None,
    }


def _diff_to_findings(diff_result: dict) -> list:
    findings = []

    for item in diff_result.get("matched", []):
        conf = item.get("confidence", 0.8)
        ftype = "uncertain" if conf <= 0.5 else "implemented"
        findings.append(_new_finding(
            ftype=ftype,
            requirement=item.get("requirement", ""),
            confidence=conf,
            analysis=item.get("notes", ""),
            code_evidence={
                "file": item.get("file", ""),
                "line": item.get("line", 0),
                "match_reason": item.get("notes", ""),
            },
        ))

    for item in diff_result.get("unimplemented", []):
        findings.append(_new_finding(
            ftype="missing",
            requirement=item.get("requirement", ""),
            confidence=0.7,
            analysis=item.get("suggestion", ""),
            risk_level=item.get("severity", "medium"),
            test_suggestion={
                "title": f"验证: {item.get('requirement', '')[:40]}",
                "precondition": "需求文档中定义了该功能",
                "steps": ["检查代码中是否有对应实现", "尝试在系统中操作该功能", "确认是否存在该功能入口"],
                "expected": "功能应按需求文档描述正常运行",
            },
        ))

    for item in diff_result.get("extra_code", []):
        findings.append(_new_finding(
            ftype="extra",
            requirement=f"代码实现: {item.get('code_item', '')}",
            confidence=0.6,
            analysis=item.get("notes", "代码中存在但需求文档中未提及"),
            code_evidence={
                "file": item.get("file", ""),
                "line": 0,
                "match_reason": "需求文档中未找到对应需求点",
            },
        ))

    for bug in diff_result.get("bugs", []):
        findings.append(_new_finding(
            ftype="risk",
            requirement=bug.get("title", ""),
            confidence=0.85,
            analysis=f"严重度: {bug.get('severity', '')}",
            risk_level="high",
            test_suggestion={
                "title": bug.get("title", ""),
                "precondition": "",
                "steps": [bug.get("steps", "")],
                "expected": bug.get("expected", ""),
            },
        ))

    return findings


# ══════════════════════════════════════════════════════════════════
#  7. TAPD 对接
# ══════════════════════════════════════════════════════════════════

def _resolve_tapd_iteration(config: dict, iteration_name: str) -> Optional[str]:
    """根据迭代名称查找 TAPD 迭代 ID"""
    import requests as req_lib
    try:
        resp = req_lib.get(
            "https://api.tapd.cn/iterations",
            params={"workspace_id": config["workspace_id"], "name": iteration_name},
            auth=(config["api_user"], config["api_password"]),
            timeout=10,
        )
        data = resp.json()
        if data.get("status") == 1 and data.get("data"):
            for item in data["data"]:
                it = item.get("Iteration", {})
                if it.get("name") == iteration_name:
                    return it.get("id")
            # 模糊匹配：名称包含
            for item in data["data"]:
                it = item.get("Iteration", {})
                if iteration_name in (it.get("name") or ""):
                    return it.get("id")
    except Exception as e:
        print(f"⚠️  查找 TAPD 迭代失败: {e}")
    return None

@router.get("/api/v2/code-compare/tapd/config")
async def get_tapd_config():
    """获取 TAPD 配置（密码脱敏）"""
    from services.tapd_service import load_tapd_config
    config = load_tapd_config()
    safe = {**config}
    if safe.get("api_password"):
        safe["api_password"] = "******"
    return {"success": True, "config": safe}


@router.post("/api/v2/code-compare/tapd/config")
async def save_tapd_config_endpoint(request: TapdConfigRequest):
    """保存 TAPD 配置"""
    from services.tapd_service import save_tapd_config
    config = request.dict()
    # 自动 trim 所有字符串字段，防止复制时带入空白字符
    for k, v in config.items():
        if isinstance(v, str):
            config[k] = v.strip()
    save_tapd_config(config)
    return {"success": True, "message": "TAPD 配置已保存"}


@router.post("/api/v2/code-compare/tapd/test")
async def test_tapd_connection_endpoint():
    """测试 TAPD 连接"""
    from services.tapd_service import load_tapd_config, test_tapd_connection
    config = load_tapd_config()
    if not config:
        raise HTTPException(status_code=400, detail="请先配置 TAPD 信息")
    result = test_tapd_connection(config)
    return result


@router.post("/api/v2/code-compare/findings/{finding_id}/push-to-tapd")
async def push_finding_to_tapd(finding_id: str, request: PushToTapdRequest):
    """推送 finding 到 TAPD 创建缺陷"""
    from services.tapd_service import (
        load_tapd_config, push_bug_to_tapd, finding_to_tapd_bug,
    )

    config = load_tapd_config()
    if not config.get("workspace_id"):
        raise HTTPException(status_code=400, detail="请先配置 TAPD 信息（项目设置 → TAPD 配置）")

    # 在所有报告中查找 finding
    target_finding = None
    report_context = {}
    for rpt in _reports.values():
        for f in rpt.get("findings", []):
            if f.get("finding_id") == finding_id:
                target_finding = f
                report_context = {
                    "report_id": rpt.get("report_id"),
                    "code_snapshot_name": rpt.get("code_snapshot_name"),
                }
                break
        if target_finding:
            break

    if not target_finding:
        raise HTTPException(status_code=404, detail=f"Finding 不存在: {finding_id}")

    # 检查是否已推送过
    if target_finding.get("tapd_bug_id"):
        return {
            "success": True,
            "already_pushed": True,
            "bug_id": target_finding["tapd_bug_id"],
            "url": target_finding.get("tapd_url", ""),
            "message": "该 Finding 已推送过 TAPD",
        }

    # 如果用户填写了表单字段，使用用户填写的；否则从 finding 自动生成
    if request.steps or request.expected or request.actual:
        # 用户手动填写的格式
        desc_lines = []
        if request.module:
            desc_lines.append(f"模块：{request.module}\n")
        desc_lines.append("操作步骤：")
        desc_lines.append(request.steps or "")
        desc_lines.append(f"\n预期结果：\n{request.expected or ''}")
        desc_lines.append(f"\n实际结果：\n{request.actual or ''}")
        if request.code_location:
            desc_lines.append(f"\n代码位置：{request.code_location}")
        desc_lines.append("\n---\n来源: AI测试平台 - 需求代码对比")
        description = "\n".join(desc_lines)
    else:
        bug_fields = finding_to_tapd_bug(target_finding, report_context)
        description = bug_fields["description"]

    title = request.title or finding_to_tapd_bug(target_finding, report_context)["title"]
    severity = request.severity or finding_to_tapd_bug(target_finding, report_context).get("severity", "minor")
    priority = request.priority or finding_to_tapd_bug(target_finding, report_context).get("priority", "P2")

    # 查找迭代 ID
    extra_fields = {}
    if request.iteration:
        iteration_id = _resolve_tapd_iteration(config, request.iteration)
        if iteration_id:
            extra_fields["iteration_id"] = iteration_id

    result = push_bug_to_tapd(
        config=config,
        title=title,
        description=description,
        severity=severity,
        priority=priority,
        module=request.module or "",
        reporter=config.get("default_reporter", ""),
        extra_fields=extra_fields,
    )

    if result["success"]:
        # 记录推送信息到 finding
        target_finding["tapd_bug_id"] = result["bug_id"]
        target_finding["tapd_url"] = result["url"]
        target_finding["tapd_pushed_at"] = datetime.now().isoformat()

        # 持久化报告
        for rpt in _reports.values():
            if rpt.get("report_id") == report_context.get("report_id"):
                _save_report(rpt)
                break

    return result
