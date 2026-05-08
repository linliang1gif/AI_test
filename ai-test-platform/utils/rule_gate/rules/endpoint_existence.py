# -*- coding: utf-8 -*-
"""
T1A rule: endpoint existence (接口存在性).

Decides whether a given path exists in the code base. Strategy priority:
  1. Check code_analysis.routes (already scanned by code_analyzer)
  2. Scan Java source under code_dir for @RequestMapping / @XxxMapping
  3. Scan Python source under code_dir for FastAPI decorators

Return None only when no evidence is reachable (code_dir absent and
no routes in code_analysis).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .._source_scan import scan_java_routes, scan_python_routes


def _normalize_path(p: str) -> str:
    """去掉末尾 / 与空白，保持大小写（路径区分大小写）"""
    if not p:
        return ""
    p = p.strip()
    if not p.startswith("/"):
        p = "/" + p
    p = p.rstrip("/")
    # 把 /{xxx} 占位符替换为 /* 便于模糊比较
    return p


def _path_match(req_path: str, code_path: str) -> bool:
    """
    宽松路径匹配：
      - 完全相等
      - 忽略 path-variable 差异 (/a/{id} ~ /a/{uuid} / /a/1)
      - 后缀子串匹配（req 可能带 context-path /recycle/xxx，code_path 没有）
    """
    if not req_path or not code_path:
        return False
    a = _normalize_path(req_path)
    b = _normalize_path(code_path)
    if a == b:
        return True
    # path-variable 归一：把 {xxx} 和纯数字段替换成占位符
    import re as _re
    _norm = lambda s: _re.sub(r'\{[^}]+\}', '{*}', _re.sub(r'/\d+(?=/|$)', '/{*}', s))
    if _norm(a) == _norm(b):
        return True
    # 后缀匹配（去 context-path）
    if a.endswith(b) or b.endswith(a):
        # 要求后缀至少包含 2 段路径，避免 '/id' 匹配万物
        suffix = b if a.endswith(b) else a
        if suffix.count("/") >= 2:
            return True
    return False


def _check_from_code_analysis(path: str, method: Optional[str],
                              code_analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    routes = code_analysis.get("routes") or []
    if not routes:
        return None
    for r in routes:
        r_path = r.get("path", "")
        r_method = (r.get("method") or "").upper()
        if _path_match(path, r_path):
            if method and r_method and r_method != method.upper() and r_method != "ANY":
                return {
                    "status": "inconsistent",
                    "confidence": 0.9,
                    "evidence_file": r.get("file", "code_analysis.routes"),
                    "evidence_lines": (0, 0),
                    "evidence_quote": f"{r_method} {r_path} -> {r.get('handler','')}",
                    "note": f"路径 {path} 存在，但代码使用 {r_method}，需求要求 {method}",
                    "rule_engine": "t1a.endpoint.code_analysis_routes",
                }
            return {
                "status": "implemented",
                "confidence": 0.95,
                "evidence_file": r.get("file", "code_analysis.routes"),
                "evidence_lines": (0, 0),
                "evidence_quote": f"{r_method or 'ANY'} {r_path} -> {r.get('handler','')}",
                "note": f"路径 {path} 存在于已索引的 routes 中",
                "rule_engine": "t1a.endpoint.code_analysis_routes",
            }
    return None  # 本索引找不到，交给下一个策略


def _check_from_source(path: str, method: Optional[str],
                       code_dir: str) -> Optional[Dict[str, Any]]:
    # 同时扫 Java / Python
    all_hits: List[Dict[str, Any]] = list(scan_java_routes(code_dir))
    all_hits.extend(scan_python_routes(code_dir))
    if not all_hits:
        return None

    matched = [h for h in all_hits if _path_match(path, h["path"])]
    if not matched:
        # 明确没找到
        return {
            "status": "missing",
            "confidence": 0.9,
            "evidence_file": code_dir,
            "evidence_lines": (0, 0),
            "evidence_quote": f"已扫描 {len(all_hits)} 条路由，未发现匹配 {path}",
            "note": f"路径 {path} 在代码路由扫描中未找到",
            "rule_engine": "t1a.endpoint.source_scan",
        }

    # 找到路径，进一步核对 method
    if method:
        method_up = method.upper()
        any_ok = any(h["method"] in (method_up, "ANY") for h in matched)
        if any_ok:
            h = next(h for h in matched if h["method"] in (method_up, "ANY"))
            return {
                "status": "implemented",
                "confidence": 1.0,
                "evidence_file": h["file"],
                "evidence_lines": h["evidence_lines"],
                "evidence_quote": h["evidence_quote"],
                "note": f"路径 {path} 方法 {method} 存在",
                "rule_engine": "t1a.endpoint.source_scan",
            }
        # 路径存在但方法不匹配
        h = matched[0]
        return {
            "status": "inconsistent",
            "confidence": 0.95,
            "evidence_file": h["file"],
            "evidence_lines": h["evidence_lines"],
            "evidence_quote": h["evidence_quote"],
            "note": f"路径 {path} 存在，但代码使用 {h['method']}，需求要求 {method_up}",
            "rule_engine": "t1a.endpoint.source_scan",
        }

    # 未指定方法，仅判存在性
    h = matched[0]
    return {
        "status": "implemented",
        "confidence": 1.0,
        "evidence_file": h["file"],
        "evidence_lines": h["evidence_lines"],
        "evidence_quote": h["evidence_quote"],
        "note": f"路径 {path} 存在",
        "rule_engine": "t1a.endpoint.source_scan",
    }


def check(params: Dict[str, Any], code_analysis: Dict[str, Any],
          code_dir: Optional[str] = None) -> Optional[Dict[str, Any]]:
    path = (params or {}).get("path", "")
    method = (params or {}).get("method")  # 可能为 None
    if not path:
        return None

    # 策略 1：使用已索引 routes（快）
    hit = _check_from_code_analysis(path, method, code_analysis)
    if hit:
        return hit

    # 策略 2：源码扫描（更完整）
    if code_dir:
        hit = _check_from_source(path, method, code_dir)
        if hit:
            return hit

    return None
