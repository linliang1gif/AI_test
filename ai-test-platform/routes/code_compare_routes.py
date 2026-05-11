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
from typing import Optional, List, Dict, Any, Tuple

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

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

try:
    from services.code_compare_storage_service import CodeCompareStorageService
    STORAGE_SVC_AVAILABLE = True
except ImportError:
    STORAGE_SVC_AVAILABLE = False

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
        except Exception as _e:
            logger.warning("[P1] report/cache load fallback: %s", _e)


def _load_persisted_requirements():
    """启动时从磁盘加载已缓存的需求数据"""
    for f in REQ_CACHE_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            req_id = f.stem  # filename without .json
            _requirement_cache[req_id] = data
        except Exception as _e:
            logger.warning("[P1] report/cache load fallback: %s", _e)


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
            except Exception as _e:
                logger.warning("[P1] report/cache load fallback: %s", _e)
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


def _get_storage_svc():
    """获取 DB 存储服务实例（每次新建 session 避免跨请求污染）"""
    if STORAGE_SVC_AVAILABLE and DB_AVAILABLE:
        try:
            sess = get_db_session()
            return CodeCompareStorageService(sess.__enter__())
        except Exception as e:
            logger.warning(f"Storage service init failed: {e}")
    return None


import logging as _logging
logger = _logging.getLogger(__name__)


def _save_report(report: dict):
    """持久化报告到磁盘"""
    path = REPORTS_DIR / f"{report['report_id']}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


# ══════════════════════════════════════════════════════════════════
#  D2-1: Finding 内容指纹索引（详见 docs/D2_1_FINGERPRINT_DESIGN.md）
# ══════════════════════════════════════════════════════════════════

# 索引 key = (project_scope, content_fingerprint)，value = source 快照
_fingerprint_index: Dict[Tuple[str, str], dict] = {}
_fingerprint_index_built: bool = False


def _get_or_compute_fingerprint(finding: dict, report: dict) -> Tuple[str, str]:
    """取或懒计算 finding 的 (project_scope, content_fingerprint)。

    若已有且版本一致，复用存值（仅重算 scope）；否则重新计算并写入内存（不立即落盘）。
    """
    from services.tapd_service import (
        compute_finding_fingerprint, FP_VERSION, FP_ALGORITHM,
    )
    have_fp = finding.get("content_fingerprint")
    have_v = finding.get("content_fingerprint_version")
    have_alg = finding.get("content_fingerprint_algorithm")
    if have_fp and have_v == FP_VERSION and have_alg == FP_ALGORITHM:
        scope, _ = compute_finding_fingerprint(finding, report)
        return scope, have_fp
    scope, fp = compute_finding_fingerprint(finding, report)
    finding["content_fingerprint"] = fp
    finding["content_fingerprint_version"] = FP_VERSION
    finding["content_fingerprint_algorithm"] = FP_ALGORITHM
    return scope, fp


def _build_fingerprint_index() -> int:
    """全量扫描 _reports，重建 fingerprint 索引。幂等，返回 source 数。"""
    from services.tapd_service import (
        is_dedup_source_eligible, build_dedup_source_record,
    )
    global _fingerprint_index, _fingerprint_index_built
    _fingerprint_index = {}
    for rpt in _reports.values():
        for f in rpt.get("findings", []):
            if not is_dedup_source_eligible(f):
                continue
            scope, fp = _get_or_compute_fingerprint(f, rpt)
            key = (scope, fp)
            if key in _fingerprint_index:
                continue  # 取最先入索引的有效 source
            _fingerprint_index[key] = build_dedup_source_record(f, rpt)
    _fingerprint_index_built = True
    return len(_fingerprint_index)


def _ensure_fingerprint_index() -> None:
    """懒触发：第一次 push 时全量构建。"""
    if not _fingerprint_index_built:
        _build_fingerprint_index()


def _register_fingerprint(finding: dict, report: dict) -> None:
    """推送/复用成功后增量入索引。若 finding 不符合 source 条件则忽略。"""
    from services.tapd_service import (
        is_dedup_source_eligible, build_dedup_source_record,
    )
    if not _fingerprint_index_built:
        _build_fingerprint_index()
        return  # 全量扫描已包含当前 finding
    if not is_dedup_source_eligible(finding):
        return
    scope, fp = _get_or_compute_fingerprint(finding, report)
    key = (scope, fp)
    if key not in _fingerprint_index:
        _fingerprint_index[key] = build_dedup_source_record(finding, report)


def _unregister_fingerprint(finding: dict, report: dict) -> None:
    """finding 状态变更（如标记 false_positive）后从索引移除。"""
    from services.tapd_service import compute_finding_fingerprint
    fp_existing = finding.get("content_fingerprint")
    if not fp_existing:
        return
    scope, _ = compute_finding_fingerprint(finding, report)
    key = (scope, fp_existing)
    src = _fingerprint_index.get(key)
    # 仅当该 source 就是当前 finding 时才移除，避免误删别的 source
    if src and src.get("finding_id") == finding.get("finding_id"):
        _fingerprint_index.pop(key, None)


def _lookup_dedup_source(
    scope: str, fp: str, exclude_finding_id: Optional[str] = None,
) -> Optional[dict]:
    """查 (scope, fp) 命中。若命中的 source 与 exclude_finding_id 相同则返回 None。"""
    src = _fingerprint_index.get((scope, fp))
    if not src:
        return None
    if exclude_finding_id and src.get("finding_id") == exclude_finding_id:
        return None
    return src


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

# ── Phase C2: SSRF 防护 ──
import ipaddress
import socket
from urllib.parse import urlparse

_SSRF_ALLOW_LOCAL_HTTP = os.getenv("ALLOW_LOCAL_GIT_HTTP", "false").lower() == "true"


def _parse_allowed_git_hosts() -> set:
    """解析 ALLOWED_GIT_HOSTS 环境变量为小写 host 集合"""
    raw = os.getenv("ALLOWED_GIT_HOSTS", "")
    return {h.strip().lower() for h in raw.split(",") if h.strip()}


def _parse_allowed_git_cidrs() -> list:
    """解析 ALLOWED_GIT_CIDRS 环境变量为 ip_network 列表"""
    raw = os.getenv("ALLOWED_GIT_CIDRS", "")
    nets = []
    for c in raw.split(","):
        c = c.strip()
        if not c:
            continue
        try:
            nets.append(ipaddress.ip_network(c, strict=False))
        except ValueError:
            # 静默忽略非法 CIDR（也不暴露原始值到日志）
            pass
    return nets


_ALLOWED_GIT_HOSTS = _parse_allowed_git_hosts()
_ALLOWED_GIT_CIDRS = _parse_allowed_git_cidrs()


def _is_host_in_private_whitelist(host_lower: str, ip_str: str) -> bool:
    """判断 host / ip 是否命中内网白名单（仅放开 private 检查）"""
    if host_lower in _ALLOWED_GIT_HOSTS:
        return True
    if ip_str in _ALLOWED_GIT_HOSTS:  # 用户也可能直接把 IP 放到 ALLOWED_GIT_HOSTS
        return True
    if _ALLOWED_GIT_CIDRS:
        try:
            ip_obj = ipaddress.ip_address(ip_str)
            for net in _ALLOWED_GIT_CIDRS:
                if ip_obj in net:
                    return True
        except ValueError:
            pass
    return False


def _sanitize_git_url_for_log(url: str) -> str:
    """脱敏 Git URL 中的 token，用于安全日志"""
    return re.sub(r'(https?://)([^@]+)@', r'\1***@', url)


def _validate_repo_url(repo_url: str) -> tuple:
    """
    Phase C2 SSRF 防护: 校验 Git 仓库 URL 是否安全。

    支持内网白名单（环境变量）：
      - ALLOWED_GIT_HOSTS=host1,host2,ip1   # host/IP 精确命中后放开 private 检查
      - ALLOWED_GIT_CIDRS=10.0.0.0/8,...    # CIDR 命中后放开 private 检查
    白名单 *不能* 绕过 loopback/link-local/multicast/reserved/metadata 检查。

    返回 (ok: bool, error_message: str)
    """
    parsed = urlparse(repo_url)
    scheme = parsed.scheme.lower()

    # 只允许 https / http / git (ssh)
    if scheme not in ("https", "http", "git", "ssh") and not repo_url.startswith("git@"):
        return False, f"不允许的协议: {scheme}. 仅支持 https/http/git@"

    # 禁止 file / ftp / ssh:// 等
    if scheme in ("file", "ftp", "ftps", "ssh"):
        return False, f"不允许的协议: {scheme}"

    # 对 git@host:path 格式提取 host
    if repo_url.startswith("git@"):
        host_part = repo_url.split("git@", 1)[1].split(":", 1)[0]
    else:
        host_part = parsed.hostname or ""

    if not host_part:
        return False, "无法解析仓库地址中的 host"

    host_lower = host_part.lower()

    # 禁止 localhost 名称（除非显式加入白名单）
    if host_lower in ("localhost", "localhost.localdomain"):
        if host_lower in _ALLOWED_GIT_HOSTS:
            return True, ""
        return False, "不允许访问 localhost。如确需放行，请在环境变量 ALLOWED_GIT_HOSTS 中添加该 host"

    # DNS 解析并检查 IP
    try:
        addrs = socket.getaddrinfo(host_part, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        for _, _, _, _, sockaddr in addrs:
            ip_str = sockaddr[0]
            ip = ipaddress.ip_address(ip_str)

            # 优先检查 metadata / loopback / link-local / multicast / reserved
            # 这些不可被白名单绕过
            if ip_str == "169.254.169.254":
                return False, "不允许访问 metadata 服务地址 169.254.169.254"
            if ip.is_loopback:
                return False, f"不允许访问 loopback 地址: {ip_str}"
            if ip.is_link_local:
                return False, f"不允许访问 link-local 地址: {ip_str}"
            if ip.is_multicast:
                return False, f"不允许访问 multicast 地址: {ip_str}"
            if ip.is_reserved:
                return False, f"不允许访问 reserved 地址: {ip_str}"

            # private 检查：可被白名单豁免
            if ip.is_private:
                if _is_host_in_private_whitelist(host_lower, ip_str):
                    continue  # 此 IP 放行，继续检查下一条 sockaddr
                return False, (
                    f"不允许访问内网地址: {ip_str}. "
                    f"如需访问内网 Git 服务器，请在后端环境变量配置 "
                    f"ALLOWED_GIT_HOSTS=<host_or_ip> 或 ALLOWED_GIT_CIDRS=<CIDR>"
                )
    except socket.gaierror:
        # DNS 无法解析，允许继续（git clone 自己会报错）
        pass

    return True, ""


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


class BatchPushToTapdRequest(BaseModel):
    finding_ids: List[str]
    skip_already_pushed: bool = True   # 已推送 finding 是否跳过（默认是）
    iteration: Optional[str] = None    # 可选：批量为所有 finding 指定同一迭代


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

    # Phase C1: 写 DB
    svc = _get_storage_svc()
    if svc:
        try:
            svc.save_snapshot(
                snapshot_id=snapshot_id, name=meta["name"],
                source_type='zip_upload', source_path=str(extract_dir),
                file_count=total_files, language_stats=lang_dist,
                ignored_dirs=sorted(IGNORED_DIRS),
            )
        except Exception as e:
            logger.warning(f"Save snapshot to DB failed: {e}")

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

    # 安全校验：协议 + SSRF 防护 (Phase C2)
    if not (repo_url.startswith("http://") or repo_url.startswith("https://") or repo_url.startswith("git@")):
        raise HTTPException(status_code=400, detail="仅支持 http(s) 或 git@ 协议的仓库地址")

    # Phase C2: SSRF 防护 — 阻止内网/localhost/metadata 地址
    url_ok, url_err = _validate_repo_url(repo_url)
    if not url_ok:
        logger.warning(f"Clone SSRF blocked: {_sanitize_git_url_for_log(repo_url)} | {url_err}")
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "code": "REPO_URL_NOT_ALLOWED",
                "message": "仓库地址不允许访问内网、localhost 或不安全协议",
                "detail": url_err,
            },
        )

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

    # Phase C1: 写 DB
    svc = _get_storage_svc()
    if svc:
        try:
            svc.save_snapshot(
                snapshot_id=snapshot_id, name=meta["name"],
                source_type='git_clone', source_path=str(scan_dir),
                file_count=total_files, language_stats=lang_dist,
            )
        except Exception as e:
            logger.warning(f"Save snapshot to DB failed: {e}")

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
            logger.info(f"🤖 代码对比使用: provider={actual_provider}, model={actual_model} (请求: provider={request.provider}, model={request.model})")
            ai_mode = "ai_deep"
        except Exception as e:
            logger.info(f"⚠️ AI 客户端初始化失败，使用规则匹配: {e}")
            ai_mode = "fallback"

    try:
        diff_result = run_req_code_diff(
            requirement_data, code_analysis,
            ai_client=ai_client, code_dir=code_path,
        )
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
            "inconsistent": len([f for f in findings if f["type"] == "inconsistent"]),
        },
        "findings": findings,
        "code_summary": code_summary,
    }
    _reports[report_id] = report
    _save_report(report)

    # Phase C1: 写 DB
    svc = _get_storage_svc()
    if svc:
        try:
            svc.save_report(report, findings)
        except Exception as e:
            logger.warning(f"Save report to DB failed: {e}")

    return {"success": True, "report": report}


# ══════════════════════════════════════════════════════════════════
#  3. 报告列表
# ══════════════════════════════════════════════════════════════════

@router.get("/api/v2/code-compare/reports")
async def get_reports():
    # Phase C1: 优先从 DB 查询
    svc = _get_storage_svc()
    if svc:
        try:
            items = svc.list_reports()
            return {"success": True, "reports": items}
        except Exception as e:
            logger.warning(f"DB list_reports failed, fallback to memory: {e}")

    # fallback: 内存
    items = []
    for r in _reports.values():
        items.append({
            "report_id": r["report_id"],
            "requirement_source": r["requirement_source"],
            "code_snapshot_name": r.get("code_snapshot_name", ""),
            "summary": r["summary"],
            "ai_mode": r.get("ai_mode", "unknown"),
            "created_at": r["created_at"],
            "source": "memory",
        })
    items.sort(key=lambda x: x["created_at"], reverse=True)
    return {"success": True, "reports": items}


# ══════════════════════════════════════════════════════════════════
#  4. 报告详情
# ══════════════════════════════════════════════════════════════════

_TAPD_MERGE_FIELDS = (
    "tapd_bug_id", "tapd_url", "tapd_pushed_at",
    "tapd_status", "tapd_status_name", "tapd_last_sync_at",
    "tapd_modified",
)


def _merge_tapd_fields_from_memory(detail: dict, report_id: str) -> None:
    """DB schema 缺 tapd_* 列，从 _reports 内存（持久化 JSON 来源）补齐"""
    mem = _reports.get(report_id)
    if not mem:
        return
    mem_by_id = {f.get("finding_id"): f for f in mem.get("findings", [])}
    for fdb in detail.get("findings", []):
        fmem = mem_by_id.get(fdb.get("finding_id"))
        if not fmem:
            continue
        for k in _TAPD_MERGE_FIELDS:
            v = fmem.get(k)
            if v is not None:
                fdb[k] = v


@router.get("/api/v2/code-compare/reports/{report_id}")
async def get_report_detail(report_id: str):
    # Phase C1: 优先查 DB
    svc = _get_storage_svc()
    if svc:
        try:
            detail = svc.get_report_detail(report_id)
            if detail:
                # 补齐 DB schema 缺失的 tapd_* 字段
                _merge_tapd_fields_from_memory(detail, report_id)
                return {"success": True, "report": detail}
        except Exception as e:
            logger.warning(f"DB get_report_detail failed: {e}")

    # fallback: 内存
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

            # Phase C1: 同步更新 DB
            svc = _get_storage_svc()
            if svc:
                try:
                    svc.update_finding_status(request.finding_id, request.manual_status)
                except Exception as e:
                    logger.warning(f"DB update finding status failed: {e}")

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

    # Phase C1: 同步 DB finding
    svc = _get_storage_svc()
    if svc:
        try:
            svc.update_finding_status(
                finding_id, "converted_to_bug",
                review_comment=request.review_comment,
                target_type="defect", target_id=str(defect_id),
                converted_at=datetime.now(),
            )
        except Exception as e:
            logger.warning(f"DB update finding (defect) failed: {e}")

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

    # Phase C1: 同步 DB finding
    svc = _get_storage_svc()
    if svc:
        try:
            tid = ",".join(case_ids) if len(case_ids) > 1 else case_ids[0]
            svc.update_finding_status(
                finding_id, "converted_to_case",
                target_type="test_case", target_id=tid,
                converted_at=datetime.now(),
            )
        except Exception as e:
            logger.warning(f"DB update finding (test_case) failed: {e}")

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

    # Phase C1: 同步 DB
    svc = _get_storage_svc()
    if svc:
        try:
            svc.save_question(question)
            svc.update_finding_status(
                finding_id, "need_product_confirm",
                review_comment=request.review_comment,
                target_type="question", target_id=q_id,
                converted_at=datetime.now(),
            )
        except Exception as e:
            logger.warning(f"DB update finding (question) failed: {e}")

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
    # D2-1: 从 fingerprint 索引中移除（若存在）
    _unregister_fingerprint(finding, report)
    _save_report(report)

    # Phase C1: 同步 DB
    svc = _get_storage_svc()
    if svc:
        try:
            svc.update_finding_status(
                finding_id, "false_positive",
                review_comment=request.reason,
            )
        except Exception as e:
            logger.warning(f"DB update finding (false_positive) failed: {e}")

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
                 risk_level="medium", inconsistencies=None,
                 evidence_snippet=None, req_id: str = "") -> dict:
    """标准 Finding 构造"""
    return {
        "finding_id": f"f_{uuid.uuid4().hex[:8]}",
        "type": ftype,
        "requirement": requirement,
        "req_id": req_id,
        "confidence": confidence,
        "analysis": _sanitize_content(analysis) if analysis else "",
        "risk_level": risk_level,
        "code_evidence": code_evidence,
        "evidence_snippet": evidence_snippet,
        "inconsistencies": inconsistencies or [],
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

    # 收集 test_suggestions，按 req_id 索引方便回填
    sugg_by_req = {}
    for s in diff_result.get("test_suggestions", []) or []:
        rid = s.get("req_id")
        if rid:
            sugg_by_req[rid] = s

    def _build_test_suggestion(req_id, fallback_title):
        s = sugg_by_req.get(req_id)
        if not s:
            return None
        return {
            "title": s.get("title") or fallback_title,
            "priority": s.get("priority", "medium"),
            "test_points": s.get("test_points", []),
        }

    for item in diff_result.get("matched", []):
        conf = item.get("confidence", 0.8)
        status = item.get("status") or item.get("status_norm")
        # 部分实现 → 单独 partial 类型映射到 inconsistent（前端会显示）
        if status in ("部分实现", "partial"):
            ftype = "inconsistent"
        elif conf <= 0.5:
            ftype = "uncertain"
        else:
            ftype = "implemented"
        rid = item.get("req_id", "")
        findings.append(_new_finding(
            ftype=ftype,
            requirement=item.get("requirement", ""),
            req_id=rid,
            confidence=conf,
            analysis=item.get("notes", ""),
            inconsistencies=item.get("inconsistencies") or [],
            evidence_snippet=item.get("evidence_snippet"),
            code_evidence={
                "file": item.get("file", ""),
                "line": item.get("line", 0),
                "match_reason": item.get("notes", ""),
                "code_item": item.get("code_item", ""),
            },
            test_suggestion=_build_test_suggestion(rid, f"验证: {item.get('requirement','')[:40]}"),
        ))

    for item in diff_result.get("inconsistent", []):
        rid = item.get("req_id", "")
        findings.append(_new_finding(
            ftype="inconsistent",
            requirement=item.get("requirement", ""),
            req_id=rid,
            confidence=item.get("confidence", 0.75),
            analysis=item.get("notes", ""),
            risk_level="high",
            inconsistencies=item.get("inconsistencies") or [],
            evidence_snippet=item.get("evidence_snippet"),
            code_evidence={
                "file": item.get("file", ""),
                "line": item.get("line", 0),
                "match_reason": item.get("notes", ""),
                "code_item": item.get("code_item", ""),
            },
            test_suggestion=_build_test_suggestion(rid, f"复核: {item.get('requirement','')[:40]}"),
        ))

    for item in diff_result.get("unimplemented", []):
        rid = item.get("req_id", "")
        findings.append(_new_finding(
            ftype="missing",
            requirement=item.get("requirement", ""),
            req_id=rid,
            confidence=item.get("confidence", 0.7),
            analysis=item.get("suggestion", ""),
            risk_level=item.get("severity", "medium"),
            test_suggestion=_build_test_suggestion(rid, f"验证: {item.get('requirement','')[:40]}") or {
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
                "line": item.get("line", 0),
                "match_reason": "需求文档中未找到对应需求点",
            },
        ))

    for bug in diff_result.get("bugs", []):
        rid = bug.get("req_id", "")
        findings.append(_new_finding(
            ftype="risk",
            requirement=bug.get("title", ""),
            req_id=rid,
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
        logger.info(f"⚠️  查找 TAPD 迭代失败: {e}")
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
        apply_dedup_to_finding,
    )

    config = load_tapd_config()
    if not config.get("workspace_id"):
        raise HTTPException(status_code=400, detail="请先配置 TAPD 信息（项目设置 → TAPD 配置）")

    # D2-1: 确保 fingerprint 索引已构建
    _ensure_fingerprint_index()

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

    # D2-1: fingerprint 去重命中检查
    target_report = _reports.get(report_context.get("report_id")) or {}
    fp_scope, fp_value = _get_or_compute_fingerprint(target_finding, target_report)
    dedup_source = _lookup_dedup_source(fp_scope, fp_value, exclude_finding_id=finding_id)
    if dedup_source:
        apply_dedup_to_finding(target_finding, dedup_source, fp_scope, fp_value)
        if target_report:
            _save_report(target_report)
        return {
            "success": True,
            "already_pushed": True,
            "dedup_by_fingerprint": True,
            "dedup_source_finding_id": dedup_source.get("finding_id"),
            "bug_id": target_finding.get("tapd_bug_id"),
            "url": target_finding.get("tapd_url", ""),
            "message": "已通过内容指纹去重，复用源 finding 的 TAPD Bug",
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

        # D2-1: 推送成功后注册到 fingerprint 索引
        _register_fingerprint(target_finding, target_report or {})

        # 持久化报告
        for rpt in _reports.values():
            if rpt.get("report_id") == report_context.get("report_id"):
                _save_report(rpt)
                break

    return result



# ══════════════════════════════════════════════════════════════════
#  11. Finding TAPD 状态回流（A1）
# ══════════════════════════════════════════════════════════════════

def _apply_tapd_status_to_finding(finding: dict, status_result: dict) -> None:
    """将 TAPD 状态结果写回 finding（内存对象）"""
    finding["tapd_status"] = status_result.get("tapd_status", "unknown")
    finding["tapd_status_name"] = status_result.get("tapd_status_name", "未知")
    finding["tapd_last_sync_at"] = datetime.now().isoformat()
    if status_result.get("tapd_modified"):
        finding["tapd_modified"] = status_result["tapd_modified"]


# sync_finding_tapd_status_endpoint
@router.post("/api/v2/code-compare/findings/{finding_id}/sync-tapd-status")
async def sync_finding_tapd_status(finding_id: str):
    """同步单个 Finding 关联 TAPD Bug 的最新状态"""
    from services.tapd_service import load_tapd_config, fetch_tapd_bug_status

    # 查找 finding
    target_finding = None
    target_report = None
    for rpt in _reports.values():
        for f in rpt.get("findings", []):
            if f.get("finding_id") == finding_id:
                target_finding = f
                target_report = rpt
                break
        if target_finding:
            break

    if not target_finding:
        raise HTTPException(status_code=404, detail=f"Finding 不存在: {finding_id}")

    bug_id = target_finding.get("tapd_bug_id") or ""
    if not bug_id:
        # 不抛 HTTP 错误，返回结构化错误（业务正常分支）
        return {
            "success": False,
            "code": "TAPD_BUG_NOT_LINKED",
            "message": "当前 Finding 尚未关联 TAPD Bug",
            "detail": {"finding_id": finding_id},
        }

    config = load_tapd_config()
    if not config.get("workspace_id"):
        return {
            "success": False,
            "code": "TAPD_NOT_CONFIGURED",
            "message": "TAPD 未配置，请先在 TAPD 配置页面设置",
            "detail": {},
        }

    result = fetch_tapd_bug_status(config, bug_id)

    if not result.get("success"):
        # TAPD 调用失败：不修改 finding 数据
        logger.warning(f"sync_tapd_bug failed: finding={finding_id} bug={bug_id} code={result.get('code')}")
        return {
            "success": False,
            "code": result.get("code", "TAPD_API_ERROR"),
            "message": result.get("message", "TAPD 同步失败"),
            "detail": {"finding_id": finding_id, "bug_id": bug_id},
        }

    # 写回 finding 内存对象
    _apply_tapd_status_to_finding(target_finding, result)
    _save_report(target_report)

    # 同步 DB（best-effort，复用 target_type="tapd_bug"）
    svc = _get_storage_svc()
    if svc:
        try:
            svc.update_finding_status(
                finding_id, target_finding.get("manual_status") or "linked_to_tapd",
                target_type="tapd_bug",
                target_id=str(bug_id),
            )
        except Exception as e:
            logger.warning(f"DB update finding tapd link failed: {e}")

    return {
        "success": True,
        "data": {
            "finding_id": finding_id,
            "tapd_bug_id": bug_id,
            "tapd_status": target_finding["tapd_status"],
            "tapd_status_name": target_finding["tapd_status_name"],
            "tapd_last_sync_at": target_finding["tapd_last_sync_at"],
        },
    }


@router.post("/api/v2/code-compare/reports/{report_id}/sync-tapd-status")
async def sync_report_tapd_status(report_id: str):
    """批量同步报告下所有已关联 TAPD Bug 的 Finding 状态"""
    from services.tapd_service import load_tapd_config, fetch_tapd_bug_status

    report = _reports.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"报告不存在: {report_id}")

    config = load_tapd_config()
    if not config.get("workspace_id"):
        return {
            "success": False,
            "code": "TAPD_NOT_CONFIGURED",
            "message": "TAPD 未配置，请先在 TAPD 配置页面设置",
            "detail": {"report_id": report_id},
        }

    findings = report.get("findings", [])
    total = len(findings)
    synced = 0
    skipped = 0
    failed = 0
    failures: list = []

    for f in findings:
        bug_id = f.get("tapd_bug_id") or ""
        if not bug_id:
            skipped += 1
            continue

        result = fetch_tapd_bug_status(config, bug_id)
        if result.get("success"):
            _apply_tapd_status_to_finding(f, result)
            synced += 1
        else:
            failed += 1
            failures.append({
                "finding_id": f.get("finding_id"),
                "bug_id": bug_id,
                "code": result.get("code", "TAPD_API_ERROR"),
            })

    # 整份报告只保存一次，减少 IO
    if synced > 0:
        _save_report(report)

    return {
        "success": True,
        "data": {
            "report_id": report_id,
            "total": total,
            "synced": synced,
            "skipped": skipped,
            "failed": failed,
            "failures": failures[:10],  # 最多返回 10 条失败明细
        },
    }



# ══════════════════════════════════════════════════════════════════
#  12. Finding 批量推送 TAPD（A2）
# ══════════════════════════════════════════════════════════════════

@router.post("/api/v2/code-compare/findings/batch-push-to-tapd")
async def batch_push_findings_to_tapd(request: BatchPushToTapdRequest):
    """批量将多个 Finding 推送到 TAPD 创建缺陷

    返回结构:
        {
          "success": true,
          "data": {
            "total": N, "pushed": M, "skipped": X, "failed": Y, "not_found": Z,
            "results": [
              {"finding_id":..., "status": "pushed|already_pushed|skipped_implemented|skipped_false_positive|not_found|failed",
               "bug_id":..., "url":..., "error":...}
            ]
          }
        }
    """
    from services.tapd_service import (
        load_tapd_config, push_bug_to_tapd, finding_to_tapd_bug,
        apply_dedup_to_finding,
    )

    # D2-1: 确保 fingerprint 索引已构建
    _ensure_fingerprint_index()

    if not request.finding_ids:
        raise HTTPException(status_code=400, detail="finding_ids 不能为空")

    if len(request.finding_ids) > 100:
        raise HTTPException(status_code=400, detail="单次批量推送不能超过 100 条")

    config = load_tapd_config()
    if not config.get("workspace_id"):
        raise HTTPException(status_code=400, detail="请先配置 TAPD 信息（项目设置 → TAPD 配置）")

    # 解析迭代 ID（仅一次，避免每条 finding 都查询 TAPD）
    extra_fields_common: Dict[str, Any] = {}
    if request.iteration:
        iteration_id = _resolve_tapd_iteration(config, request.iteration)
        if iteration_id:
            extra_fields_common["iteration_id"] = iteration_id

    # 构建 finding -> report 索引（按 report 分组，便于最后批量持久化）
    finding_index: Dict[str, tuple] = {}
    for rpt in _reports.values():
        for f in rpt.get("findings", []):
            fid = f.get("finding_id")
            if fid:
                finding_index[fid] = (rpt, f)

    results = []
    pushed = 0
    skipped = 0
    failed = 0
    not_found = 0
    dirty_reports = set()  # 需要持久化的 report_id 集合

    for fid in request.finding_ids:
        if fid not in finding_index:
            results.append({"finding_id": fid, "status": "not_found"})
            not_found += 1
            continue

        rpt, finding = finding_index[fid]

        # 跳过 type=implemented（已实现的 finding 没必要推 bug）
        if finding.get("type") == "implemented":
            results.append({"finding_id": fid, "status": "skipped_implemented"})
            skipped += 1
            continue

        # 跳过已标记为误报的
        if finding.get("manual_status") == "false_positive":
            results.append({"finding_id": fid, "status": "skipped_false_positive"})
            skipped += 1
            continue

        # 跳过已推送过的（除非用户明确要求强推）
        if finding.get("tapd_bug_id") and request.skip_already_pushed:
            results.append({
                "finding_id": fid,
                "status": "already_pushed",
                "bug_id": finding["tapd_bug_id"],
                "url": finding.get("tapd_url", ""),
            })
            skipped += 1
            continue

        # D2-1: fingerprint 去重命中检查
        fp_scope, fp_value = _get_or_compute_fingerprint(finding, rpt)
        dedup_source = _lookup_dedup_source(fp_scope, fp_value, exclude_finding_id=fid)
        if dedup_source:
            apply_dedup_to_finding(finding, dedup_source, fp_scope, fp_value)
            dirty_reports.add(rpt.get("report_id"))
            results.append({
                "finding_id": fid,
                "status": "dedup_by_fingerprint",
                "bug_id": finding.get("tapd_bug_id"),
                "url": finding.get("tapd_url", ""),
                "dedup_source_finding_id": dedup_source.get("finding_id"),
            })
            skipped += 1
            continue

        # 自动生成 bug 字段
        report_context = {
            "report_id": rpt.get("report_id"),
            "code_snapshot_name": rpt.get("code_snapshot_name"),
        }
        bug_fields = finding_to_tapd_bug(finding, report_context)

        try:
            result = push_bug_to_tapd(
                config=config,
                title=bug_fields["title"],
                description=bug_fields["description"],
                severity=bug_fields.get("severity", "minor"),
                priority=bug_fields.get("priority", "P2"),
                module=bug_fields.get("module", ""),
                reporter=config.get("default_reporter", ""),
                extra_fields=dict(extra_fields_common) if extra_fields_common else None,
            )
        except Exception as e:
            logger.warning(f"batch_push: finding={fid} push exception: {type(e).__name__}")
            results.append({"finding_id": fid, "status": "failed", "error": f"{type(e).__name__}"})
            failed += 1
            continue

        if result.get("success"):
            finding["tapd_bug_id"] = result["bug_id"]
            finding["tapd_url"] = result["url"]
            finding["tapd_pushed_at"] = datetime.now().isoformat()
            dirty_reports.add(rpt.get("report_id"))
            # D2-1: 推送成功后注册到 fingerprint 索引
            _register_fingerprint(finding, rpt)
            results.append({
                "finding_id": fid,
                "status": "pushed",
                "bug_id": result["bug_id"],
                "url": result["url"],
            })
            pushed += 1
        else:
            err_msg = result.get("message", "unknown error")
            # 截断防止过长
            if len(err_msg) > 200:
                err_msg = err_msg[:200]
            results.append({"finding_id": fid, "status": "failed", "error": err_msg})
            failed += 1

    # 批量持久化所有有改动的 report
    for rpt_id in dirty_reports:
        rpt = _reports.get(rpt_id)
        if rpt:
            try:
                _save_report(rpt)
            except Exception as e:
                logger.warning(f"batch_push: save report {rpt_id} failed: {e}")

    # D2-1: 统计 dedup_by_fingerprint 项
    dedup_count = sum(1 for r in results if r.get("status") == "dedup_by_fingerprint")
    return {
        "success": True,
        "data": {
            "total": len(request.finding_ids),
            "pushed": pushed,
            "skipped": skipped,
            "dedup_by_fingerprint": dedup_count,
            "failed": failed,
            "not_found": not_found,
            "results": results,
        },
    }
