# -*- coding: utf-8 -*-
"""验证 finding_to_tapd_bug 修复后输出正确"""
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from services.tapd_service import finding_to_tapd_bug  # noqa: E402

cases = [
    # 实测 finding f_de87c09d (risk + high + 0.85)
    {
        "name": "纯组件类型【(矩形)】被丢弃 → 只剩模块前缀",
        "finding": {
            "type": "risk",
            "confidence": 0.85,
            "risk_level": "high",
            "requirement": "[实现不一致] 【(矩形)】1、分录非必填字段未填写，在查看状态下默认隐藏，&nbsp; 如品牌、颜色、规格型号等",
            "analysis": "严重度: medium",
        },
        "report_context": {"code_snapshot_name": "purchaseOrder_snapshot"},
        # (矩形) 是组件类型噪音被丢弃，回退按句末标点切首句
        "expect": {
            "severity": "minor",
            "priority": "P2",
            "title_contains": "采购订单",
            "title_not_contains": "(矩形)",
        },
    },
    {
        "name": "risk + high + 高置信 → major + 模块名",
        "finding": {
            "type": "risk",
            "confidence": 0.95,
            "risk_level": "high",
            "requirement": "【支付校验】支付金额必须>0",
        },
        "report_context": {"code_snapshot_name": "payment"},
        "expect": {
            "severity": "major",
            "priority": "P2",
            "title_contains": "付款单-支付校验",
        },
    },
    {
        "name": "星号必填标识被清理",
        "finding": {
            "type": "inconsistent",
            "confidence": 0.7,
            "risk_level": "medium",
            "requirement": "【*供应商】1、新增 默认为空，支持下拉选",
        },
        "report_context": {"code_snapshot_name": "purchaseOrder"},
        "expect": {
            "severity": "minor",
            "priority": "P2",
            "title_contains": "采购订单-供应商",
            "title_not_contains": "*",
        },
    },
    {
        "name": "inconsistencies 优先用作问题描述",
        "finding": {
            "type": "inconsistent",
            "confidence": 0.7,
            "risk_level": "medium",
            "requirement": "【个税承担方】下拉选项",
            "inconsistencies": [
                {"aspect": "默认值/下拉选项", "expected": "...", "actual": "..."},
            ],
        },
        "report_context": {"code_snapshot_name": "purchaseOrder"},
        "expect": {
            "title_contains": "默认值/下拉选项",
        },
    },
    {
        "name": "missing 高置信 + risk_level=high → minor (不再一律严重)",
        "finding": {
            "type": "missing",
            "confidence": 1.0,
            "risk_level": "high",
            "requirement": "POA20260324001",
        },
        "expect": {"severity": "minor", "priority": "P3"},
    },
    {
        "name": "missing 低置信 → trivial",
        "finding": {
            "type": "missing",
            "confidence": 0.3,
            "requirement": "草稿状态",
        },
        "expect": {"severity": "trivial", "priority": "P3"},
    },
    {
        "name": "历史字段 requirement_point 兼容",
        "finding": {
            "type": "risk",
            "confidence": 0.95,
            "risk_level": "high",
            "requirement_point": "【支付】兼容历史字段名",
        },
        "report_context": {"code_snapshot_name": "payment"},
        "expect": {"severity": "major", "title_contains": "付款单-支付"},
    },
    {
        "name": "无 report_context 兜底用「白盒对比」",
        "finding": {
            "type": "missing",
            "confidence": 0.6,
            "requirement": "【模块】描述",
        },
        "expect": {"title_contains": "白盒对比-模块"},
    },
]

passed = 0
for c in cases:
    out = finding_to_tapd_bug(c["finding"], c.get("report_context"))
    okmark = "✅"
    fails = []
    for k, v in c["expect"].items():
        if k == "title_contains":
            if v not in out["title"]:
                fails.append(f"title 不含 '{v}': '{out['title']}'")
        elif k == "title_not_contains":
            if v in out["title"]:
                fails.append(f"title 不应含 '{v}': '{out['title']}'")
        elif out.get(k) != v:
            fails.append(f"{k}={out.get(k)} (期望 {v})")
    if fails:
        okmark = "❌"
    else:
        passed += 1
    print(f"\n{okmark} [{c['name']}]")
    print(f"   title    = {out['title']}")
    print(f"   severity = {out['severity']}    priority = {out['priority']}")
    if fails:
        for f in fails:
            print(f"   FAIL: {f}")

print(f"\n=== {passed}/{len(cases)} passed ===")
sys.exit(0 if passed == len(cases) else 1)
