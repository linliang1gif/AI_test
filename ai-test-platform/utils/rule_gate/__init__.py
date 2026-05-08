# -*- coding: utf-8 -*-
"""
T1A: Deterministic rule-gate for whitebox requirement-code comparison.

Design goal: intercept requirement types that can be judged by static
signals (annotations / decorators / AST symbols) BEFORE calling the AI
model, to reduce token cost and eliminate hallucination on simple cases.

Pipeline:
    req_points  ──▶  classifier  ──▶  rule_registry  ──▶  per-rule checker
                                                            │
                                                            ├─ hit  → finding (confidence=1.0, evidence=code lines)
                                                            └─ miss → forwarded to AI / rule-based fallback

Phase 1 rules:
    - required         (必填)
    - endpoint         (接口存在性)
    - http_method      (HTTP 方法)
    - precision        (小数位精度)
"""

from .classifier import classify_requirement
from .rule_registry import run_rule_gate

__all__ = ["classify_requirement", "run_rule_gate"]
