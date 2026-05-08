# -*- coding: utf-8 -*-
"""
T1A rule registry + gate orchestrator.

Responsibilities:
  1. Register each rule_type -> checker function mapping.
  2. run_rule_gate(): iterate req_points, classify each, dispatch to
     matching checkers, collect deterministic findings, return the
     remaining (uncovered) points so the caller can feed them to AI.

Checker contract:
    def check(params: dict, code_analysis: dict, code_dir: Optional[str]) -> Optional[dict]
    Return None if the rule cannot reach a deterministic conclusion.
    Return a finding-like dict otherwise:
        {
            "status": "implemented" | "missing" | "inconsistent",
            "confidence": float (0~1),
            "evidence_file": str,
            "evidence_lines": Tuple[int, int],
            "evidence_quote": str,
            "note": str,
        }
"""
from __future__ import annotations

from typing import Dict, List, Optional, Any, Tuple

from .classifier import classify_requirement

# checker 延迟导入，避免在 rule checker 尚未写完时 import 失败
_RULE_REGISTRY: Dict[str, Any] = {}


def register(rule_type: str):
    """decorator 或 function — 注册 checker"""
    def _wrap(fn):
        _RULE_REGISTRY[rule_type] = fn
        return fn
    return _wrap


def _lazy_register_all():
    """把 rules/ 目录下的 checker 注册进来。懒加载避免循环依赖。"""
    if _RULE_REGISTRY:
        return
    try:
        from .rules.required import check as _req_check
        _RULE_REGISTRY["required"] = _req_check
    except Exception:
        pass
    try:
        from .rules.endpoint_existence import check as _ep_check
        _RULE_REGISTRY["endpoint"] = _ep_check
    except Exception:
        pass
    try:
        from .rules.http_method import check as _hm_check
        _RULE_REGISTRY["http_method"] = _hm_check
    except Exception:
        pass
    try:
        from .rules.precision import check as _pr_check
        _RULE_REGISTRY["precision"] = _pr_check
    except Exception:
        pass


def run_rule_gate(
    req_points: List[Dict[str, Any]],
    code_analysis: Dict[str, Any],
    code_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    主入口：遍历 req_points，尝试用规则判定。

    Returns:
        {
            "gated_findings": [
                {
                    "requirement": <req_point>,
                    "rule_type": str,
                    "status": "implemented"|"missing"|"inconsistent",
                    "confidence": float,
                    "evidence_file": str,
                    "evidence_lines": Tuple[int,int],
                    "evidence_quote": str,
                    "note": str,
                },
                ...
            ],
            "uncovered_points": [ <req_point>, ... ],
            "stats": {
                "total": int,
                "classified": int,
                "gated": int,
                "uncovered": int,
                "by_rule_type": { rule_type: int },
            }
        }
    """
    _lazy_register_all()

    gated: List[Dict[str, Any]] = []
    uncovered: List[Dict[str, Any]] = []
    classified_count = 0
    by_type: Dict[str, int] = {}

    for req in req_points or []:
        rules = classify_requirement(req)
        if not rules:
            uncovered.append(req)
            continue
        classified_count += 1

        any_hit = False
        for rule_type, params in rules:
            checker = _RULE_REGISTRY.get(rule_type)
            if not checker:
                continue
            try:
                finding = checker(params, code_analysis, code_dir)
            except Exception as e:
                # 规则自身出异常 → 视为未命中，交给 AI 兜底，但不崩溃
                finding = None
                # 不污染日志，只在 dev 时打印
                # print(f"[rule_gate] checker '{rule_type}' raised: {e}")
            if finding:
                any_hit = True
                gated.append({
                    "requirement": req,
                    "rule_type": rule_type,
                    "rule_params": params,
                    **finding,
                })
                by_type[rule_type] = by_type.get(rule_type, 0) + 1

        if not any_hit:
            uncovered.append(req)

    return {
        "gated_findings": gated,
        "uncovered_points": uncovered,
        "stats": {
            "total": len(req_points or []),
            "classified": classified_count,
            "gated": len(gated),
            "uncovered": len(uncovered),
            "by_rule_type": by_type,
        },
    }
