# -*- coding: utf-8 -*-
"""
T1A rule: required (必填).

Decides whether a field is marked required in the code. Strategy:
  1. Scan Java source under code_dir for @ApiModelProperty / @Schema that
     matches params["field_name"] (Chinese label match).
  2. If matched, check whether @NotNull / @NotBlank / @NotEmpty / @Required
     appears within the same declaration window.

Return None when code_dir is unavailable or no matching field is located
(the requirement then falls through to the AI path).
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from .._source_scan import scan_java_field_annotations


def _label_match(label: str, field_name: str) -> bool:
    """宽松匹配：完全相等 / 子串包含（label 可能是 '供应商名称'，req 字段 '供应商'）"""
    if not label or not field_name:
        return False
    a = label.strip()
    b = field_name.strip()
    if a == b:
        return True
    # 允许 req_field 是 label 的一部分，或反之（字段名通常较短）
    if len(b) >= 2 and (b in a or a in b):
        return True
    return False


def check(params: Dict[str, Any], code_analysis: Dict[str, Any],
          code_dir: Optional[str] = None) -> Optional[Dict[str, Any]]:
    field_name = (params or {}).get("field_name", "")
    if not field_name or not code_dir:
        return None

    hits = scan_java_field_annotations(code_dir)
    if not hits:
        return None

    matched = [h for h in hits if _label_match(h.get("label", ""), field_name)]
    if not matched:
        return None

    # 若任意匹配条目 has_required=True → implemented（取第一个作证据）
    required_hits = [h for h in matched if h.get("has_required")]
    if required_hits:
        h = required_hits[0]
        return {
            "status": "implemented",
            "confidence": 1.0,
            "evidence_file": h["file"],
            "evidence_lines": h["window_lines"],
            "evidence_quote": h["window_quote"],
            "note": (
                f"字段 '{field_name}' 在实体 {h['field_name'] or '(未解析字段名)'} "
                f"上已通过 Java Bean Validation 注解声明必填"
            ),
            "rule_engine": "t1a.required.java_bean_validation",
        }

    # 有字段但无必填注解 → inconsistent
    h = matched[0]
    return {
        "status": "inconsistent",
        "confidence": 0.85,
        "evidence_file": h["file"],
        "evidence_lines": h["window_lines"],
        "evidence_quote": h["window_quote"],
        "note": (
            f"字段 '{field_name}' 在实体 {h['field_name'] or '(未解析字段名)'} "
            f"中有定义，但未发现 @NotNull/@NotBlank/@NotEmpty 必填注解"
        ),
        "rule_engine": "t1a.required.java_bean_validation",
    }
