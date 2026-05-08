# -*- coding: utf-8 -*-
"""
T1A requirement classifier.

Classifies each requirement point into zero or more rule types by matching
keyword/regex patterns in the 'name' + 'detail' text. One requirement may
fire multiple rules (e.g. a single line may require a field BOTH to be
non-null AND to have 2-decimal precision).

Returns a list of (rule_type, extracted_params) pairs. The rule_registry
then routes each pair to the right checker.
"""
from __future__ import annotations

import re
from typing import Dict, List, Tuple, Any, Optional


# ── 规则关键词 / 正则 ─────────────────────────────────────────

# 1) 必填 required
_REQUIRED_RE = re.compile(
    r'(必填|必须填|必须输入|必须录入|不能为空|不得为空|不可为空|不允许为空)',
    re.IGNORECASE,
)

# 2) 精度 precision — "保留 2 位小数" / "精度 2 位" / "2 位小数"
_PRECISION_RE = re.compile(
    r'(?:保留|精度|精确到)?\s*(\d+)\s*位\s*小数'
    r'|精度[^\d]{0,4}(\d+)\s*位'
    r'|小数\s*点?\s*后\s*(\d+)\s*位',
)

# 3) 接口路径 endpoint — 含 '/path' 形式
# 匹配 "接口 /xx/yy" 或 "POST /xx/yy" 或 "调用 /xx"
_ENDPOINT_PATH_RE = re.compile(
    r'(?:(?P<method>GET|POST|PUT|DELETE|PATCH)\s+)?'
    r'(?P<path>/[A-Za-z][A-Za-z0-9_\-/{}:]{2,80})',
    re.IGNORECASE,
)

# 4) HTTP method 单独出现
_HTTP_METHOD_RE = re.compile(
    r'\b(GET|POST|PUT|DELETE|PATCH)\b',
    re.IGNORECASE,
)

# 字段名抽取：从需求文本里拿候选字段名（汉语 / 驼峰英文）
# 用于把 "供应商必填" 拆成 field_name="供应商" + rule=required
_FIELD_HINT_RE = re.compile(
    r'([\u4e00-\u9fff]{2,15}|[a-z][a-zA-Z0-9_]{2,40})'
)


# ── 小工具 ────────────────────────────────────────────────

def _text_of(req_point: Dict[str, Any]) -> str:
    """拼 req 的可分类文本（name + detail）"""
    parts: List[str] = []
    for k in ("name", "detail"):
        v = req_point.get(k)
        if isinstance(v, str) and v.strip():
            parts.append(v.strip())
    return " ".join(parts)


def _guess_field_name(text: str, anchor_idx: int) -> Optional[str]:
    """
    从 anchor_idx 位置往前最近找一个"字段名候选"。
    适合 "供应商必填" / "金额保留 2 位小数" 这种"字段 + 约束"模式。
    """
    head = text[:anchor_idx]
    if not head:
        return None
    matches = list(_FIELD_HINT_RE.finditer(head))
    if not matches:
        return None
    last = matches[-1].group(1)
    # 过滤一些明显不是字段名的辅助词
    if last in {"请", "必须", "不能", "不得", "不可", "支持", "实现"}:
        if len(matches) >= 2:
            return matches[-2].group(1)
        return None
    return last


# ── 主分类函数 ────────────────────────────────────────────

def classify_requirement(req_point: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
    """
    对一条 requirement_point 做分类。
    返回 [(rule_type, params), ...] 列表 — 可能为空（完全无法判定）。

    rule_type:
        "required"     : params = {"field_name": str}
        "precision"    : params = {"field_name": Optional[str], "digits": int}
        "endpoint"     : params = {"method": Optional[str], "path": str}
        "http_method"  : params = {"method": str, "path": Optional[str]}
    """
    out: List[Tuple[str, Dict[str, Any]]] = []
    text = _text_of(req_point)
    if not text:
        return out

    # 1) required
    m = _REQUIRED_RE.search(text)
    if m:
        field = _guess_field_name(text, m.start())
        if field:
            out.append(("required", {"field_name": field}))

    # 2) precision
    m = _PRECISION_RE.search(text)
    if m:
        digits_str = next((g for g in m.groups() if g), None)
        if digits_str:
            try:
                digits = int(digits_str)
                field = _guess_field_name(text, m.start())
                out.append(("precision", {"field_name": field, "digits": digits}))
            except ValueError:
                pass

    # 3) endpoint + http_method（路径和方法可能同时出现）
    #    注意避免重复触发：如 "POST /xxx" 同时产生 endpoint 和 http_method
    ep_match = _ENDPOINT_PATH_RE.search(text)
    if ep_match:
        path = ep_match.group("path")
        method = ep_match.group("method")
        method = method.upper() if method else None
        out.append(("endpoint", {"method": method, "path": path}))
        if method:
            out.append(("http_method", {"method": method, "path": path}))
    else:
        # 只有 method 没路径的情况（极少见，但兜底）
        m = _HTTP_METHOD_RE.search(text)
        if m and ("接口" in text or "API" in text.upper() or "api" in text):
            out.append(("http_method", {"method": m.group(1).upper(), "path": None}))

    return out
