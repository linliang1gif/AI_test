#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T1A-P1 需求分类器单元测试

覆盖 4 类规则：required / precision / endpoint / http_method
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.rule_gate.classifier import classify_requirement


# ══════════════════════════════════════════════════════════════════
# 测试运行器
# ══════════════════════════════════════════════════════════════════

class _R:
    def __init__(self):
        self.p = 0
        self.f = 0

    def pas(self, n):
        self.p += 1
        print(f"  PASS: {n}")

    def fai(self, n, msg):
        self.f += 1
        print(f"  FAIL: {n}: {msg}")


def run(result, name, fn):
    try:
        fn()
        result.pas(name)
    except AssertionError as e:
        result.fai(name, str(e) or "AssertionError")
    except Exception as e:
        import traceback
        result.fai(name, f"{type(e).__name__}: {e}\n{traceback.format_exc()}")


def _mk(name, detail=""):
    return {"id": "REQ_T", "name": name, "detail": detail, "source": "test"}


def _types(req_point):
    return [rt for rt, _ in classify_requirement(req_point)]


def _params(req_point, rule_type):
    return next((p for rt, p in classify_requirement(req_point) if rt == rule_type), None)


# ══════════════════════════════════════════════════════════════════
# 1-3 required
# ══════════════════════════════════════════════════════════════════

def test_01_required_basic():
    r = _mk("供应商必填")
    assert "required" in _types(r), _types(r)
    assert _params(r, "required")["field_name"] == "供应商"


def test_02_required_synonyms():
    for text in ("付款单号不能为空", "申请人不得为空", "金额不可为空", "供应商必须输入"):
        r = _mk(text)
        assert "required" in _types(r), f"{text}: {_types(r)}"


def test_03_required_no_field_name():
    """没有字段名候选（只有'必填'二字）→ 不产生 required"""
    r = _mk("必填")
    assert "required" not in _types(r), _types(r)


# ══════════════════════════════════════════════════════════════════
# 4-6 precision
# ══════════════════════════════════════════════════════════════════

def test_04_precision_basic():
    r = _mk("金额保留 2 位小数")
    types = _types(r)
    assert "precision" in types, types
    p = _params(r, "precision")
    assert p["digits"] == 2, p
    assert p["field_name"] == "金额", p


def test_05_precision_no_space():
    r = _mk("实付金额保留2位小数，四舍五入")
    p = _params(r, "precision")
    assert p is not None
    assert p["digits"] == 2, p


def test_06_precision_with_required_combined():
    """同一条需求同时含必填+精度"""
    r = _mk("金额必填", detail="保留 2 位小数")
    types = _types(r)
    assert "required" in types, types
    assert "precision" in types, types


# ══════════════════════════════════════════════════════════════════
# 7-9 endpoint + http_method
# ══════════════════════════════════════════════════════════════════

def test_07_endpoint_with_method():
    r = _mk("POST /finance/payment/create")
    types = _types(r)
    assert "endpoint" in types, types
    assert "http_method" in types, types
    ep = _params(r, "endpoint")
    assert ep["path"] == "/finance/payment/create", ep
    assert ep["method"] == "POST", ep
    hm = _params(r, "http_method")
    assert hm["method"] == "POST", hm


def test_08_endpoint_path_only():
    r = _mk("接口 /api/v2/purchase/confirm")
    types = _types(r)
    assert "endpoint" in types, types
    assert "http_method" not in types, types
    ep = _params(r, "endpoint")
    assert ep["path"] == "/api/v2/purchase/confirm", ep
    assert ep["method"] is None, ep


def test_09_no_rule_matched():
    """纯文本，无 required/precision/endpoint 信号 → 空结果"""
    r = _mk("财务应付单列表")
    types = _types(r)
    assert not types, f"expected empty but got: {types}"


# ══════════════════════════════════════════════════════════════════
# 主入口
# ══════════════════════════════════════════════════════════════════

def main():
    print("=" * 64)
    print("T1A-P1 需求分类器 单元测试")
    print("=" * 64)
    result = _R()
    cases = [
        ("01_required_basic", test_01_required_basic),
        ("02_required_synonyms", test_02_required_synonyms),
        ("03_required_no_field_name", test_03_required_no_field_name),
        ("04_precision_basic", test_04_precision_basic),
        ("05_precision_no_space", test_05_precision_no_space),
        ("06_precision_with_required_combined", test_06_precision_with_required_combined),
        ("07_endpoint_with_method", test_07_endpoint_with_method),
        ("08_endpoint_path_only", test_08_endpoint_path_only),
        ("09_no_rule_matched", test_09_no_rule_matched),
    ]
    for name, fn in cases:
        run(result, name, fn)
    print("=" * 64)
    print(f"PASS={result.p}  FAIL={result.f}  TOTAL={len(cases)}")
    print("=" * 64)
    return 0 if result.f == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
