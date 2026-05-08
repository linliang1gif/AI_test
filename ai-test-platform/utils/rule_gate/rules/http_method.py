# -*- coding: utf-8 -*-
"""
T1A rule: HTTP method check.

Decides whether a given path uses the correct HTTP method as specified in
the requirement. Reuses the same route scanning as endpoint_existence but
focuses on method mismatch (endpoint exists, but is GET instead of POST).

Return None when no code evidence is available.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from .endpoint_existence import check as _endpoint_check


def check(params: Dict[str, Any], code_analysis: Dict[str, Any],
          code_dir: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    HTTP method 规则逻辑与 endpoint 几乎相同：
    - 若 endpoint_check 返回 implemented → HTTP 方法也对，本规则不再重复。
    - 若返回 inconsistent（路径存在，方法不同）→ 直接用该结论。
    - 若无 path → None
    """
    method = (params or {}).get("method")
    path = (params or {}).get("path")
    if not method:
        return None
    if not path:
        # 只有 method 无 path → 无法确定性判断
        return None

    # 调 endpoint checker（它已经判断了方法一致性）
    result = _endpoint_check(params, code_analysis, code_dir)
    if not result:
        return None

    # 如果 endpoint 返回 implemented，说明路径 + 方法都对 → 本规则也 implemented
    if result["status"] == "implemented":
        result["note"] = f"接口 {method} {path} 方法匹配"
        result["rule_engine"] = "t1a.http_method"
        return result

    # inconsistent → 已包含方法不匹配信息
    if result["status"] == "inconsistent":
        result["rule_engine"] = "t1a.http_method"
        return result

    # missing → 路径都不在，http_method 规则不应该再重复报
    # 让 endpoint 规则去报 missing，这里返回 None 不重复
    return None
