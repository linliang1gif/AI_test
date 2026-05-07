#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
D2-2 Axure type='label' 文本分类 单元测试

覆盖 16 个用例：
  01-03 noise: 控件类型 / 全角括号 / 单字符标点
  04-11 demo_value: 金额 / 单位金额 / 日期 / 时间 / 订单号 / 纯数字 / 演示人名 / 演示状态
  12-13 rule: 含义务规则关键词
  14-15 field_name: 普通业务字段名 / 含演示值的字段名（混合行保守保留）
  16    集成: parse_axure_folder_structured 中 demo_value/noise 不进 features

约束：
  - 不联网、不写 DB、不修改业务报告
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.document_parser import _classify_axure_label_text


# ══════════════════════════════════════════════════════════════════
#  最小测试运行器
# ══════════════════════════════════════════════════════════════════

class _Result:
    def __init__(self):
        self.passed = 0
        self.failed = 0

    def add_pass(self, name):
        self.passed += 1
        print(f"  PASS: {name}")

    def add_fail(self, name, msg):
        self.failed += 1
        print(f"  FAIL: {name}: {msg}")


def run(result: _Result, name, fn):
    try:
        fn()
        result.add_pass(name)
    except AssertionError as e:
        result.add_fail(name, str(e) or "AssertionError")
    except Exception as e:
        import traceback
        result.add_fail(name, f"{type(e).__name__}: {e}\n{traceback.format_exc()}")


def _expect(text, expected, msg=""):
    got = _classify_axure_label_text(text)
    assert got == expected, f"input={text!r}: expected {expected!r}, got {got!r} {msg}"


# ══════════════════════════════════════════════════════════════════
#  01-03 noise
# ══════════════════════════════════════════════════════════════════

def test_01_noise_widget_type_halfwidth():
    _expect("(下拉列表)", "noise")
    _expect("(矩形)", "noise")
    _expect("(文本框)", "noise")
    _expect("(矩形按钮)", "noise")


def test_02_noise_widget_type_fullwidth():
    _expect("（下拉列表）", "noise")
    _expect("（矩形）", "noise")
    _expect("（按钮）", "noise")


def test_03_noise_punct_or_single_char():
    _expect("<", "noise")
    _expect(">", "noise")
    _expect("*", "noise")
    _expect("-", "noise")
    _expect(" ", "noise")
    _expect("", "noise")
    _expect("|", "noise")


# ══════════════════════════════════════════════════════════════════
#  04-11 demo_value
# ══════════════════════════════════════════════════════════════════

def test_04_demo_amount_yuan():
    _expect("¥12303.33", "demo_value")
    _expect("¥123.03", "demo_value")
    _expect("¥250.00", "demo_value")
    _expect("¥105122.00", "demo_value")


def test_05_demo_amount_with_unit():
    _expect("19550KG", "demo_value")
    _expect("80%", "demo_value")
    _expect("250.00元", "demo_value")
    _expect("99个", "demo_value")


def test_06_demo_date():
    _expect("2025-09-30", "demo_value")
    _expect("2026/03/24", "demo_value")
    _expect("2025年09月30日", "demo_value")
    _expect("2025-09-30 12:30", "demo_value")
    _expect("2025-09-30 12：30", "demo_value")  # 全角冒号


def test_07_demo_time():
    _expect("12:30:00", "demo_value")
    _expect("09:15", "demo_value")
    _expect("23:59:59", "demo_value")


def test_08_demo_order_no():
    _expect("POA20260324001", "demo_value")
    _expect("IAN202603200001", "demo_value")
    _expect("ZGA20260330001", "demo_value")
    _expect("BUG2024100100", "demo_value")


def test_09_demo_pure_number():
    _expect("12303.33", "demo_value")
    _expect("123.03", "demo_value")
    _expect("123456", "demo_value")
    _expect("1,234,567.89", "demo_value")


def test_10_demo_persons():
    _expect("张三", "demo_value")
    _expect("李四", "demo_value")
    _expect("王五", "demo_value")
    _expect("test", "demo_value")
    _expect("demo", "demo_value")


def test_11_demo_status_words():
    _expect("待审核", "demo_value")
    _expect("已审核", "demo_value")
    _expect("草稿", "demo_value")
    _expect("已提交", "demo_value")
    _expect("待处理", "demo_value")
    _expect("已开票", "demo_value")


# ══════════════════════════════════════════════════════════════════
#  12-13 rule
# ══════════════════════════════════════════════════════════════════

def test_12_rule_must():
    _expect("金额必须大于零", "rule")
    _expect("提交后不能修改", "rule")
    _expect("最大不超过 100", "rule")


def test_13_rule_conditional():
    _expect("如果金额大于100，则需要审批", "rule")
    _expect("当状态为已审核时，按钮置灰", "rule")
    _expect("若用户未填写则提示必填", "rule")


# ══════════════════════════════════════════════════════════════════
#  14-15 field_name
# ══════════════════════════════════════════════════════════════════

def test_14_field_name_basic():
    _expect("采购订单列表", "field_name")
    _expect("申请开票金额", "field_name")
    _expect("反向开票申请单详情", "field_name")
    _expect("供应商", "field_name")
    _expect("付款单审核", "field_name")


def test_15_field_name_with_value_suffix_kept_conservative():
    """混合行（字段名+演示值）当前保守保留为 field_name；后续可由方案 D 处理。"""
    # 这种"字段名:演示值"行整体保留，避免误删字段名
    _expect("供应商：张三", "field_name")
    _expect("订单重量 19550KG", "field_name")
    _expect("申请开票金额：¥12303.33", "field_name")


# ══════════════════════════════════════════════════════════════════
#  16 集成：parse_axure_folder_structured 分发逻辑
# ══════════════════════════════════════════════════════════════════

def test_16_integration_parse_axure_folder_structured(tmp_dir=None):
    """
    通过 monkey-patch 注入伪造的 _parse_axure_datajs 输出，
    验证 parse_axure_folder_structured：
      - field_name 进 features
      - demo_value / noise 进 demo_values, 不进 features
      - rule 同时进 rules + features (作为 axure_label_rule)
      - type='annotation' / 'note' 行为不变
    """
    from utils import document_parser as dp

    fake_annotations = [
        # type='label' 项
        {"type": "label", "content": "采购订单列表", "source": "x"},          # field_name
        {"type": "label", "content": "申请开票金额", "source": "x"},          # field_name
        {"type": "label", "content": "(下拉列表)", "source": "x"},            # noise
        {"type": "label", "content": "（矩形）", "source": "x"},               # noise
        {"type": "label", "content": "¥12303.33", "source": "x"},             # demo_value
        {"type": "label", "content": "待审核", "source": "x"},                # demo_value
        {"type": "label", "content": "POA20260324001", "source": "x"},         # demo_value
        {"type": "label", "content": "金额必须大于零", "source": "x"},        # rule
        # type='annotation' 项（核心：annotation.label 也参与分类）
        # label=field_name → features.name = label
        {"type": "annotation", "label": "供应商", "content": "供应商名称必须非空",
         "source": "x"},
        # label=demo_value → features.name = content (desc)，原 label 进 demo_values
        {"type": "annotation", "label": "¥250.00",
         "content": "对应订单主表的实付/退总金额", "source": "x"},
        # label=noise → features.name = content
        {"type": "annotation", "label": "(下拉列表)",
         "content": "支持全部、待审核筛选", "source": "x"},
        # label=订单号 demo_value → features.name = content
        {"type": "annotation", "label": "FKA202604070001",
         "content": "付款单号", "source": "x"},
        # type='note' 项（行为不变）
        {"type": "note", "content": "页面描述：用于展示订单详情", "source": "x"},
    ]

    # mock _parse_axure_datajs 与 parse_axure_folder
    orig_parse_datajs = dp._parse_axure_datajs
    orig_parse_folder = dp.parse_axure_folder
    dp._parse_axure_datajs = lambda folder: fake_annotations
    dp.parse_axure_folder = lambda folder_path: "fake raw text"

    try:
        # 制造一个真实存在的目录（用 PROJECT_ROOT 自身代替）
        result = dp.parse_axure_folder_structured(str(PROJECT_ROOT))
    finally:
        dp._parse_axure_datajs = orig_parse_datajs
        dp.parse_axure_folder = orig_parse_folder

    # ── 1) demo_values 字段存在并包含 demo_value/noise 项 ──
    assert "demo_values" in result, f"result missing 'demo_values' key: {list(result.keys())}"
    demo_set = set(result["demo_values"])
    assert "(下拉列表)" in demo_set, demo_set
    assert "（矩形）" in demo_set, demo_set
    assert "¥12303.33" in demo_set, demo_set
    assert "待审核" in demo_set, demo_set
    assert "POA20260324001" in demo_set, demo_set

    # ── 2) features 不应包含 demo_value/noise 项 ──
    feature_names = {f["name"] for f in result["features"]}
    forbidden_in_features = {"(下拉列表)", "（矩形）", "¥12303.33", "待审核", "POA20260324001"}
    leak = forbidden_in_features & feature_names
    assert not leak, f"demo_value/noise leaked into features: {leak}"

    # ── 3) features 应包含 field_name 项 ──
    assert "采购订单列表" in feature_names, feature_names
    assert "申请开票金额" in feature_names, feature_names

    # ── 4) rule 既进 rules 也进 features (axure_label_rule) ──
    assert "金额必须大于零" in result["rules"], result["rules"]
    assert "金额必须大于零" in feature_names, feature_names
    rule_sources = [f["source"] for f in result["features"] if f["name"] == "金额必须大于零"]
    assert "axure_label_rule" in rule_sources, rule_sources

    # ── 5) type='annotation' 新行为：label=field_name 时正常进 features ──
    assert "供应商" in feature_names, feature_names
    assert any("供应商" in n for n in result["axure_notes"]), result["axure_notes"]

    # ── 6) type='annotation' 新行为：label=demo_value 时，
    #       features.name = content (desc)，原 label 进 demo_values ──
    # ¥250.00 不应作为 feature.name；它的 desc "对应订单主表的实付/退总金额" 才是 feature.name
    assert "¥250.00" not in feature_names, (
        f"annotation.label='¥250.00' should NOT be feature name, but found: {feature_names}"
    )
    assert "对应订单主表的实付/退总金额" in feature_names, (
        f"annotation desc should be used as feature name, got: {feature_names}"
    )
    assert "¥250.00" in result["demo_values"], result["demo_values"]

    # 同理：(下拉列表) label
    assert "(下拉列表)" not in feature_names or list(feature_names).count("(下拉列表)") == 0, (
        f"annotation.label='(下拉列表)' should NOT leak into features"
    )
    assert "支持全部、待审核筛选" in feature_names, feature_names

    # 同理：订单号 label
    assert "FKA202604070001" not in feature_names, feature_names
    assert "付款单号" in feature_names, feature_names
    assert "FKA202604070001" in result["demo_values"], result["demo_values"]

    # ── 7) type='note' 行为不变（仅进 axure_notes） ──
    assert "页面描述：用于展示订单详情" in result["axure_notes"], result["axure_notes"]

    # ── 8) stats 含 demo_values 计数 ──
    assert "demo_values" in result["stats"], result["stats"]
    assert result["stats"]["demo_values"] == len(result["demo_values"])


# ══════════════════════════════════════════════════════════════════
#  主入口
# ══════════════════════════════════════════════════════════════════

def main():
    print("=" * 64)
    print("D2-2 Axure type='label' 文本分类 单元测试")
    print("=" * 64)

    result = _Result()
    cases = [
        ("01_noise_widget_type_halfwidth", test_01_noise_widget_type_halfwidth),
        ("02_noise_widget_type_fullwidth", test_02_noise_widget_type_fullwidth),
        ("03_noise_punct_or_single_char", test_03_noise_punct_or_single_char),
        ("04_demo_amount_yuan", test_04_demo_amount_yuan),
        ("05_demo_amount_with_unit", test_05_demo_amount_with_unit),
        ("06_demo_date", test_06_demo_date),
        ("07_demo_time", test_07_demo_time),
        ("08_demo_order_no", test_08_demo_order_no),
        ("09_demo_pure_number", test_09_demo_pure_number),
        ("10_demo_persons", test_10_demo_persons),
        ("11_demo_status_words", test_11_demo_status_words),
        ("12_rule_must", test_12_rule_must),
        ("13_rule_conditional", test_13_rule_conditional),
        ("14_field_name_basic", test_14_field_name_basic),
        ("15_field_name_with_value_suffix_kept_conservative",
         test_15_field_name_with_value_suffix_kept_conservative),
        ("16_integration_parse_axure_folder_structured",
         test_16_integration_parse_axure_folder_structured),
    ]

    for name, fn in cases:
        run(result, name, fn)

    print("=" * 64)
    print(f"PASS={result.passed}  FAIL={result.failed}  TOTAL={len(cases)}")
    print("=" * 64)

    return 0 if result.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
