#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T1A-P1 Rule Gate 集成测试

使用 tempdir 模拟 Java 源文件，验证 4 类规则的端到端流程：
  1. required（必填）
  2. endpoint（接口存在性）
  3. http_method（HTTP 方法）
  4. precision（精度）
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.rule_gate.classifier import classify_requirement
from utils.rule_gate.rule_registry import run_rule_gate
from utils.rule_gate._source_scan import clear_cache


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


# ══════════════════════════════════════════════════════════════════
# Fixture: 模拟 Java 项目
# ══════════════════════════════════════════════════════════════════

_JAVA_ENTITY = '''\
package com.example.entity;

import javax.validation.constraints.NotNull;
import javax.validation.constraints.NotBlank;
import javax.validation.constraints.Digits;
import io.swagger.annotations.ApiModelProperty;
import java.math.BigDecimal;

public class PaymentOrder {

    @ApiModelProperty("付款单号")
    @NotBlank(message = "付款单号不能为空")
    private String paymentNo;

    @ApiModelProperty("供应商")
    @NotNull
    private String supplier;

    @ApiModelProperty(value = "金额", required = true)
    @Digits(integer = 10, fraction = 2)
    private BigDecimal amount;

    @ApiModelProperty("备注")
    private String remark;  // 非必填

    public BigDecimal calcTotal() {
        return amount.setScale(2, BigDecimal.ROUND_HALF_UP);
    }
}
'''

_JAVA_CONTROLLER = '''\
package com.example.controller;

import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/finance/payment")
public class PaymentController {

    @PostMapping("/create")
    public Result create(@RequestBody PaymentOrder order) {
        return service.create(order);
    }

    @GetMapping("/list")
    public Result list(@RequestParam String status) {
        return service.list(status);
    }

    @PutMapping("/update/{id}")
    public Result update(@PathVariable Long id, @RequestBody PaymentOrder order) {
        return service.update(id, order);
    }
}
'''


def _setup_temp_project():
    """创建临时 Java 项目目录，返回 code_dir 路径"""
    tmpdir = tempfile.mkdtemp(prefix="t1a_test_")
    entity_dir = Path(tmpdir) / "src" / "main" / "java" / "com" / "example" / "entity"
    ctrl_dir = Path(tmpdir) / "src" / "main" / "java" / "com" / "example" / "controller"
    entity_dir.mkdir(parents=True)
    ctrl_dir.mkdir(parents=True)
    (entity_dir / "PaymentOrder.java").write_text(_JAVA_ENTITY, encoding="utf-8")
    (ctrl_dir / "PaymentController.java").write_text(_JAVA_CONTROLLER, encoding="utf-8")
    return tmpdir


def _mk(name, detail=""):
    return {"id": "REQ_T", "name": name, "detail": detail, "source": "test"}


# ══════════════════════════════════════════════════════════════════
# 测试用例
# ══════════════════════════════════════════════════════════════════

_CODE_DIR = None


def test_01_required_implemented():
    """需求: 供应商必填 → code 有 @NotNull → implemented"""
    req = [_mk("供应商必填")]
    r = run_rule_gate(req, {}, _CODE_DIR)
    assert r["stats"]["gated"] == 1, r["stats"]
    gf = r["gated_findings"][0]
    assert gf["status"] == "implemented", gf
    assert gf["rule_type"] == "required", gf


def test_02_required_inconsistent():
    """需求: 备注必填 → code 有 @ApiModelProperty("备注") 但无 @NotNull → inconsistent"""
    req = [_mk("备注必填")]
    r = run_rule_gate(req, {}, _CODE_DIR)
    assert r["stats"]["gated"] == 1, r["stats"]
    gf = r["gated_findings"][0]
    assert gf["status"] == "inconsistent", gf
    assert gf["rule_type"] == "required", gf
    assert "未发现" in gf["note"], gf["note"]


def test_03_required_unknown_field():
    """需求: 审批意见必填 → code 中无该字段 → uncovered（交给 AI）"""
    req = [_mk("审批意见必填")]
    r = run_rule_gate(req, {}, _CODE_DIR)
    assert r["stats"]["gated"] == 0, r["stats"]
    assert len(r["uncovered_points"]) == 1


def test_04_endpoint_implemented():
    """需求含路径 /finance/payment/create → code 有 → implemented"""
    req = [_mk("POST /finance/payment/create")]
    r = run_rule_gate(req, {}, _CODE_DIR)
    gated = [g for g in r["gated_findings"] if g["rule_type"] == "endpoint"]
    assert len(gated) >= 1, r["gated_findings"]
    assert gated[0]["status"] == "implemented", gated[0]


def test_05_endpoint_missing():
    """需求含路径 /finance/payment/delete → code 中不存在 → missing"""
    req = [_mk("接口 /finance/payment/delete")]
    r = run_rule_gate(req, {}, _CODE_DIR)
    gated = [g for g in r["gated_findings"] if g["rule_type"] == "endpoint"]
    assert len(gated) >= 1, r["gated_findings"]
    assert gated[0]["status"] == "missing", gated[0]


def test_06_http_method_inconsistent():
    """需求: DELETE /finance/payment/list → code 是 GET → inconsistent"""
    req = [_mk("DELETE /finance/payment/list")]
    r = run_rule_gate(req, {}, _CODE_DIR)
    gated = [g for g in r["gated_findings"] if g["rule_type"] == "http_method"]
    assert len(gated) >= 1, r["gated_findings"]
    assert gated[0]["status"] == "inconsistent", gated[0]


def test_07_precision_implemented():
    """需求: 金额保留 2 位小数 → code 有 setScale(2) + @Digits(fraction=2) → implemented"""
    req = [_mk("金额保留 2 位小数")]
    r = run_rule_gate(req, {}, _CODE_DIR)
    gated = [g for g in r["gated_findings"] if g["rule_type"] == "precision"]
    assert len(gated) >= 1, r["gated_findings"]
    assert gated[0]["status"] == "implemented", gated[0]


def test_08_precision_inconsistent():
    """需求: 金额保留 4 位小数 → code 只有 setScale(2) → inconsistent"""
    req = [_mk("金额保留 4 位小数")]
    r = run_rule_gate(req, {}, _CODE_DIR)
    gated = [g for g in r["gated_findings"] if g["rule_type"] == "precision"]
    assert len(gated) >= 1, r["gated_findings"]
    assert gated[0]["status"] == "inconsistent", gated[0]
    assert "4" in gated[0]["note"] and "2" in gated[0]["note"], gated[0]["note"]


def test_09_no_code_dir_graceful():
    """code_dir 为 None → 所有需求走 uncovered"""
    req = [_mk("供应商必填"), _mk("POST /finance/payment/create")]
    r = run_rule_gate(req, {}, None)
    assert r["stats"]["gated"] == 0, r["stats"]
    assert len(r["uncovered_points"]) == 2


def test_10_mixed_req_points():
    """混合需求：有些被规则截获，有些无法判定"""
    req = [
        _mk("供应商必填"),                     # required → implemented
        _mk("付款单号不能为空"),                 # required → implemented
        _mk("金额保留 2 位小数"),               # precision → implemented
        _mk("财务应付单列表"),                   # 无规则 → uncovered
        _mk("1、列表展示已创建的订单"),           # 无规则 → uncovered
    ]
    r = run_rule_gate(req, {}, _CODE_DIR)
    assert r["stats"]["gated"] >= 3, r["stats"]
    assert r["stats"]["uncovered"] == 2, r["stats"]


def test_11_merge_gate_findings():
    """验证 _merge_gate_findings 输出结构正确"""
    from utils.req_code_diff import _merge_gate_findings, _empty_result

    gated = [{
        "requirement": {"name": "供应商必填", "id": "R1"},
        "rule_type": "required",
        "status": "implemented",
        "confidence": 1.0,
        "evidence_file": "Entity.java",
        "evidence_lines": (5, 10),
        "evidence_quote": "@NotNull private String supplier;",
        "note": "字段 '供应商' 已通过 @NotNull 声明必填",
        "rule_engine": "t1a.required.java_bean_validation",
    }, {
        "requirement": {"name": "备注必填", "id": "R2"},
        "rule_type": "required",
        "status": "inconsistent",
        "confidence": 0.85,
        "evidence_file": "Entity.java",
        "evidence_lines": (15, 20),
        "evidence_quote": "private String remark;",
        "note": "字段 '备注' 未发现 @NotNull",
        "rule_engine": "t1a.required.java_bean_validation",
    }]
    stats = {"total": 5, "classified": 3, "gated": 2, "uncovered": 3, "by_rule_type": {"required": 2}}
    merged = _merge_gate_findings(gated, _empty_result(), stats)

    assert len(merged["matched"]) == 1, merged["matched"]
    assert merged["matched"][0]["requirement"] == "供应商必填"
    assert len(merged["bugs"]) == 1, merged["bugs"]
    assert merged["bugs"][0]["requirement"] == "备注必填"
    assert merged["summary"]["rule_gate_stats"] == stats


def test_12_run_req_code_diff_integration():
    """完整 run_req_code_diff 流程（无 AI，但 rule_gate 能截获部分需求点）"""
    from utils.req_code_diff import run_req_code_diff

    req_data = {
        "features": [
            {"name": "供应商必填", "source": "axure_annotation"},
            {"name": "金额保留 2 位小数", "source": "axure_annotation"},
            {"name": "财务应付单列表", "source": "axure_annotation"},
        ],
        "rules": [],
        "fields": [],
    }
    code_analysis = {"components": [], "routes": [], "functions": []}

    result = run_req_code_diff(req_data, code_analysis, code_dir=_CODE_DIR)
    # rule_gate 应该截获 required + precision
    summary = result.get("summary", {})
    gate_stats = summary.get("rule_gate_stats", {})
    assert gate_stats.get("gated", 0) >= 2, f"expected >=2 gated, got: {gate_stats}"
    # 整体结构合法
    assert "matched" in result
    assert "unimplemented" in result


# ══════════════════════════════════════════════════════════════════
# 主入口
# ══════════════════════════════════════════════════════════════════

def main():
    global _CODE_DIR
    print("=" * 64)
    print("T1A-P1 Rule Gate 集成测试")
    print("=" * 64)

    # 搭建临时 Java 项目
    _CODE_DIR = _setup_temp_project()
    print(f"  temp code_dir: {_CODE_DIR}")
    clear_cache()

    result = _R()
    cases = [
        ("01_required_implemented", test_01_required_implemented),
        ("02_required_inconsistent", test_02_required_inconsistent),
        ("03_required_unknown_field", test_03_required_unknown_field),
        ("04_endpoint_implemented", test_04_endpoint_implemented),
        ("05_endpoint_missing", test_05_endpoint_missing),
        ("06_http_method_inconsistent", test_06_http_method_inconsistent),
        ("07_precision_implemented", test_07_precision_implemented),
        ("08_precision_inconsistent", test_08_precision_inconsistent),
        ("09_no_code_dir_graceful", test_09_no_code_dir_graceful),
        ("10_mixed_req_points", test_10_mixed_req_points),
        ("11_merge_gate_findings", test_11_merge_gate_findings),
        ("12_run_req_code_diff_integration", test_12_run_req_code_diff_integration),
    ]
    for name, fn in cases:
        run(result, name, fn)

    # 清理
    import shutil
    shutil.rmtree(_CODE_DIR, ignore_errors=True)
    clear_cache()

    print("=" * 64)
    print(f"PASS={result.p}  FAIL={result.f}  TOTAL={len(cases)}")
    print("=" * 64)
    return 0 if result.f == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
