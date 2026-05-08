# -*- coding: utf-8 -*-
"""
T1A shared source code scanning utilities.

Provides lazy, cached scanning of Java / Python / Vue source files under
a given code_dir. Each scan returns a list of structured hits that rule
checkers can reuse without re-reading files.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# 扫描上限（避免跑穿项目）
_MAX_FILES = 3000
_MAX_BYTES_PER_FILE = 500_000  # 500KB
_SCAN_EXTENSIONS = (".java", ".py")

# ── Java 相关正则 ─────────────────────────────────────────────

# @ApiModelProperty("供应商") / @ApiModelProperty(value="供应商", ...) / @Schema(description="供应商")
# Group "label": 字段语义标签（通常是中文）
_JAVA_FIELD_LABEL_RE = re.compile(
    r'@(?:ApiModelProperty|Schema|JsonProperty|Field)\s*\(\s*'
    r'(?:value\s*=\s*|description\s*=\s*|name\s*=\s*)?'
    r'["\']([^"\']{1,80})["\']',
)

# 必填注解：@NotNull / @NotBlank / @NotEmpty / @Required
_JAVA_REQUIRED_ANNOTATION_RE = re.compile(
    r'@(?:NotNull|NotBlank|NotEmpty|Required)\b'
)

# @RequestMapping(value="/xxx") / @GetMapping("/xxx") / @PostMapping("/xxx") 等
_JAVA_ROUTE_RE = re.compile(
    r'@(?P<anno>RequestMapping|GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping)'
    r'\s*\(\s*(?:value\s*=\s*|path\s*=\s*)?["\']([^"\']+)["\']'
)

# class 级别的路径前缀 @RequestMapping("/purchase") class Xxx
# 在同一个文件里 class 之前出现的 @RequestMapping 作为 class-level prefix
_JAVA_CLASS_HEAD_RE = re.compile(r'^\s*(?:public\s+|abstract\s+|final\s+)*class\s+\w+', re.MULTILINE)

# 方法精度：BigDecimal.setScale(n) / .setScale(n,
_JAVA_SETSCALE_RE = re.compile(r'\.setScale\s*\(\s*(\d+)')

# @Digits(fraction=2) / @Digits(integer=..., fraction=2)
_JAVA_DIGITS_RE = re.compile(r'@Digits\s*\([^)]*fraction\s*=\s*(\d+)')


# ── Python 相关正则 ───────────────────────────────────────────

# FastAPI router decorator: @router.post("/xxx") / @app.get("/xxx")
_PY_ROUTE_RE = re.compile(
    r'@(?:\w+)\.(?P<method>get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
    re.IGNORECASE,
)

# Pydantic Field(..., description="供应商")
_PY_FIELD_DESC_RE = re.compile(
    r'Field\s*\([^)]*description\s*=\s*["\']([^"\']{1,80})["\']'
)


# ══════════════════════════════════════════════════════════════════
# 文件缓存
# ══════════════════════════════════════════════════════════════════

@lru_cache(maxsize=32)
def _list_source_files(code_dir: str) -> Tuple[str, ...]:
    """列出 code_dir 下所有被支持的源文件相对路径，返回 tuple 以便 hash"""
    p = Path(code_dir)
    if not p.is_dir():
        return tuple()
    out: List[str] = []
    for ext in _SCAN_EXTENSIONS:
        for f in p.rglob(f"*{ext}"):
            if len(out) >= _MAX_FILES:
                break
            # 忽略 build / target / node_modules / venv
            parts = set(f.parts)
            if parts & {"target", "build", "node_modules", "venv", ".venv", "dist", "__pycache__"}:
                continue
            out.append(str(f))
        if len(out) >= _MAX_FILES:
            break
    return tuple(out)


@lru_cache(maxsize=4096)
def _read_source(file_path: str) -> str:
    """读单个源文件，带字节上限 + 多编码兜底"""
    try:
        data = Path(file_path).read_bytes()[:_MAX_BYTES_PER_FILE]
    except Exception:
        return ""
    for enc in ("utf-8", "gbk", "utf-8-sig"):
        try:
            return data.decode(enc)
        except Exception:
            continue
    return data.decode("utf-8", errors="replace")


# ══════════════════════════════════════════════════════════════════
# Scanner 主接口
# ══════════════════════════════════════════════════════════════════

def scan_java_field_annotations(code_dir: str) -> List[Dict[str, Any]]:
    """
    扫 Java 源文件，提取所有 @ApiModelProperty / @Schema 声明及其附近的
    必填注解信息。

    Returns:
        [
            {
                "file": absolute_path,
                "line": 1-based line number,
                "label": "供应商",       # 从 @ApiModelProperty 提取
                "field_name": "supplier", # 就近的字段声明名
                "has_required": bool,     # 附近 5 行内是否有 @NotNull 等
                "required_line": Optional[int],
                "window_quote": str,      # 用作 evidence 的代码片段
            },
            ...
        ]
    """
    out: List[Dict[str, Any]] = []
    for fp in _list_source_files(code_dir):
        if not fp.endswith(".java"):
            continue
        content = _read_source(fp)
        if not content:
            continue
        lines = content.split("\n")
        for m in _JAVA_FIELD_LABEL_RE.finditer(content):
            line_idx = content.count("\n", 0, m.start())
            lo = max(0, line_idx - 2)
            hi = min(len(lines), line_idx + 6)
            window = "\n".join(lines[lo:hi])
            required_m = _JAVA_REQUIRED_ANNOTATION_RE.search(window)
            # 就近字段名：往下找第一个 `private/public/protected? <type> <name>`
            field_name = ""
            for j in range(line_idx, min(len(lines), line_idx + 6)):
                fm = re.search(
                    r'(?:private|public|protected|static|final|\s)+\s+[\w<>,\[\]\s]+\s+(\w+)\s*[;=,]',
                    lines[j],
                )
                if fm:
                    field_name = fm.group(1)
                    break
            out.append({
                "file": fp,
                "line": line_idx + 1,
                "label": m.group(1).strip(),
                "field_name": field_name,
                "has_required": bool(required_m),
                "required_line": (line_idx + 1 + window[:required_m.start()].count("\n")
                                  if required_m else None),
                "window_quote": window[:400],
                "window_lines": (lo + 1, hi),
            })
    return out


def scan_java_routes(code_dir: str) -> List[Dict[str, Any]]:
    """
    扫 Java 源文件，提取所有 @RequestMapping / @XxxMapping 路由声明。

    Returns:
        [
            {
                "file": absolute_path,
                "line": 1-based,
                "method": "POST" | "GET" | ... | "ANY",
                "path": "/finance/payment/create",   # class-level prefix + method path
                "anno": "@PostMapping",
                "evidence_quote": str,
            },
            ...
        ]
    """
    out: List[Dict[str, Any]] = []
    anno_to_method = {
        "GetMapping": "GET",
        "PostMapping": "POST",
        "PutMapping": "PUT",
        "DeleteMapping": "DELETE",
        "PatchMapping": "PATCH",
        "RequestMapping": "ANY",
    }
    for fp in _list_source_files(code_dir):
        if not fp.endswith(".java"):
            continue
        content = _read_source(fp)
        if not content:
            continue
        lines = content.split("\n")
        # class-level prefix：取第一个 class 定义前出现的 @RequestMapping 作为 prefix
        class_prefix = ""
        cls_m = _JAVA_CLASS_HEAD_RE.search(content)
        if cls_m:
            head = content[:cls_m.start()]
            rm = _JAVA_ROUTE_RE.search(head)
            if rm and rm.group("anno") == "RequestMapping":
                class_prefix = rm.group(2).rstrip("/")

        for m in _JAVA_ROUTE_RE.finditer(content):
            anno = m.group("anno")
            path = m.group(2)
            # class 级别 @RequestMapping 作为 prefix 的那条本身跳过（已用来算 prefix）
            if anno == "RequestMapping" and m.start() < (cls_m.start() if cls_m else 0):
                continue
            line_idx = content.count("\n", 0, m.start())
            method = anno_to_method.get(anno, "ANY")
            # class_prefix + path 合并
            full_path = (class_prefix.rstrip("/") + "/" + path.lstrip("/")).replace("//", "/")
            lo = max(0, line_idx - 1)
            hi = min(len(lines), line_idx + 3)
            out.append({
                "file": fp,
                "line": line_idx + 1,
                "method": method,
                "path": full_path,
                "anno": f"@{anno}",
                "evidence_quote": "\n".join(lines[lo:hi])[:400],
                "evidence_lines": (lo + 1, hi),
            })
    return out


def scan_python_routes(code_dir: str) -> List[Dict[str, Any]]:
    """扫 Python 源文件的 FastAPI 路由装饰器"""
    out: List[Dict[str, Any]] = []
    for fp in _list_source_files(code_dir):
        if not fp.endswith(".py"):
            continue
        content = _read_source(fp)
        if not content:
            continue
        lines = content.split("\n")
        for m in _PY_ROUTE_RE.finditer(content):
            line_idx = content.count("\n", 0, m.start())
            lo = max(0, line_idx - 1)
            hi = min(len(lines), line_idx + 3)
            out.append({
                "file": fp,
                "line": line_idx + 1,
                "method": m.group("method").upper(),
                "path": m.group(2),
                "anno": "python_decorator",
                "evidence_quote": "\n".join(lines[lo:hi])[:400],
                "evidence_lines": (lo + 1, hi),
            })
    return out


def scan_precision_usages(code_dir: str) -> List[Dict[str, Any]]:
    """
    扫 BigDecimal.setScale(n) 与 @Digits(fraction=n) 的精度定义。
    """
    out: List[Dict[str, Any]] = []
    for fp in _list_source_files(code_dir):
        if not fp.endswith(".java"):
            continue
        content = _read_source(fp)
        if not content:
            continue
        lines = content.split("\n")
        for m in _JAVA_SETSCALE_RE.finditer(content):
            line_idx = content.count("\n", 0, m.start())
            lo = max(0, line_idx - 1)
            hi = min(len(lines), line_idx + 2)
            out.append({
                "file": fp,
                "line": line_idx + 1,
                "digits": int(m.group(1)),
                "kind": "setScale",
                "evidence_quote": "\n".join(lines[lo:hi])[:300],
                "evidence_lines": (lo + 1, hi),
            })
        for m in _JAVA_DIGITS_RE.finditer(content):
            line_idx = content.count("\n", 0, m.start())
            lo = max(0, line_idx - 1)
            hi = min(len(lines), line_idx + 2)
            out.append({
                "file": fp,
                "line": line_idx + 1,
                "digits": int(m.group(1)),
                "kind": "@Digits",
                "evidence_quote": "\n".join(lines[lo:hi])[:300],
                "evidence_lines": (lo + 1, hi),
            })
    return out


# ── 缓存清理（供测试使用）────────────────────────────────────────

def clear_cache():
    _list_source_files.cache_clear()
    _read_source.cache_clear()
