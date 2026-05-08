# -*- coding: utf-8 -*-
"""
T1A rule: precision (小数位精度).

Decides whether the code enforces the required decimal precision for a
given field (e.g. "金额保留 2 位小数").

Strategy:
  1. Scan Java source for BigDecimal.setScale(N) / @Digits(fraction=N).
  2. If a match with the correct N is found near the field → implemented.
  3. If found but N differs → inconsistent.
  4. If no precision enforcement found at all → None (fallback to AI).

NOTE: Field association is approximate — we check if the field_name
(Chinese) appears in the same file or nearby @ApiModelProperty label.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from .._source_scan import scan_precision_usages, scan_java_field_annotations


def check(params: Dict[str, Any], code_analysis: Dict[str, Any],
          code_dir: Optional[str] = None) -> Optional[Dict[str, Any]]:
    digits = (params or {}).get("digits")
    field_name = (params or {}).get("field_name")  # 可能为 None
    if digits is None or not code_dir:
        return None

    prec_hits = scan_precision_usages(code_dir)
    if not prec_hits:
        return None

    # 如果有 field_name，尝试精确定位到该字段所在文件
    candidate_files: set = set()
    if field_name:
        field_annos = scan_java_field_annotations(code_dir)
        for fa in field_annos:
            label = fa.get("label", "")
            if field_name in label or label in field_name:
                candidate_files.add(fa["file"])

    # 筛选与 field 相关的精度用法
    if candidate_files:
        relevant = [h for h in prec_hits if h["file"] in candidate_files]
    else:
        relevant = prec_hits  # 无法定位字段，看全局

    if not relevant:
        # 字段所在文件没有精度代码 → 可能缺失，但不确定
        return None

    # 检查精度值
    exact_match = [h for h in relevant if h["digits"] == digits]
    if exact_match:
        h = exact_match[0]
        return {
            "status": "implemented",
            "confidence": 0.95 if candidate_files else 0.75,
            "evidence_file": h["file"],
            "evidence_lines": h["evidence_lines"],
            "evidence_quote": h["evidence_quote"],
            "note": (
                f"代码中{'字段相关文件' if candidate_files else '全局'}发现 "
                f"{h['kind']}({digits}) 精度声明"
                + (f"（关联字段: {field_name}）" if field_name else "")
            ),
            "rule_engine": "t1a.precision",
        }

    # 有精度声明但数字不对 → inconsistent
    h = relevant[0]
    return {
        "status": "inconsistent",
        "confidence": 0.85 if candidate_files else 0.6,
        "evidence_file": h["file"],
        "evidence_lines": h["evidence_lines"],
        "evidence_quote": h["evidence_quote"],
        "note": (
            f"需求要求 {digits} 位小数，但代码中 {h['kind']} 使用了 {h['digits']} 位"
            + (f"（关联字段: {field_name}）" if field_name else "")
        ),
        "rule_engine": "t1a.precision",
    }
