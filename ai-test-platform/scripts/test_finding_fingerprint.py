#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
D2-1 Finding 内容指纹与去重 单元测试

覆盖 14 个用例（详见 docs/D2_1_FINGERPRINT_DESIGN.md §12）：
  01 同一 finding fingerprint 稳定
  02 sha256_32_v1 输出长度为 32 hex
  03 line number 改变不影响 fingerprint
  04 finding_id / report_id 改变不影响 fingerprint
  05 finding_type 改变会影响 fingerprint
  06 code_file 改变会影响 fingerprint
  07 project_scope 不同不会互相 dedup
  08 相同 project_scope + 相同 fingerprint + source 有 tapd_bug_id 时命中去重
  09 source 为 false_positive 时不命中去重
  10 没有 tapd_bug_id 的 source 不命中去重
  11 命中去重时不调用真实 TAPD HTTP（单条 push）
  12 批量推送中 dedup_by_fingerprint 结果正确
  13 老 finding 无 content_fingerprint 时可懒计算
  14 指纹输入不包含敏感字段

约束：
  - 不联网
  - 不写真实 DB
  - 不真实推 TAPD（HTTP 全部 mock）
  - 不污染 _reports（每个用例自己重置）
"""
from __future__ import annotations

import asyncio
import string
import sys
from pathlib import Path
from unittest import mock

# 让脚本能直接 import 项目模块
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.tapd_service import (
    FP_VERSION,
    FP_ALGORITHM,
    compute_finding_fingerprint,
    compute_project_scope,
    _clean_snapshot_name_for_scope,
    is_dedup_source_eligible,
    build_dedup_source_record,
    apply_dedup_to_finding,
    debug_fingerprint_input,
)


# ══════════════════════════════════════════════════════════════════
#  测试桩工厂
# ══════════════════════════════════════════════════════════════════

def make_finding(**kw):
    base = {
        "finding_id": kw.pop("finding_id", "f_test_001"),
        "type": kw.pop("type", "inconsistent"),
        "requirement": kw.pop("requirement", "采购订单列表展示已创建的采购订单"),
        "req_id": kw.pop("req_id", "RQ-001"),
        "code_evidence": kw.pop("code_evidence", {
            "file": "src/views/purchaseOrder/purchaseOrderList.vue",
            "line": 42,
            "code_item": "purchaseOrderList",
            "match_reason": "candidate match",
        }),
        "manual_status": kw.pop("manual_status", None),
        "tapd_bug_id": kw.pop("tapd_bug_id", None),
        "tapd_url": kw.pop("tapd_url", None),
    }
    base.update(kw)
    return base


def make_report(**kw):
    return {
        "report_id": kw.get("report_id", "rpt_test_001"),
        "project_id": kw.get("project_id"),
        "project_name": kw.get("project_name"),
        "repo_name": kw.get("repo_name"),
        "code_snapshot_name": kw.get("code_snapshot_name", "recycle-applet"),
        "findings": kw.get("findings", []),
    }


def _reset_routes_module():
    """每个用例开头：清空 routes 模块内的 _reports / 索引。"""
    from routes import code_compare_routes as cc
    cc._reports = {}
    cc._fingerprint_index = {}
    cc._fingerprint_index_built = False
    return cc


def _build_index_with(findings_with_reports):
    """工具：注入 finding+report 到 _reports 后重建索引。"""
    cc = _reset_routes_module()
    for f, rpt in findings_with_reports:
        rpt_id = rpt["report_id"]
        if rpt_id not in cc._reports:
            rpt_copy = dict(rpt)
            rpt_copy["findings"] = []
            cc._reports[rpt_id] = rpt_copy
        cc._reports[rpt_id]["findings"].append(f)
    cc._build_fingerprint_index()
    return cc


# ══════════════════════════════════════════════════════════════════
#  测试运行器（最小，无外部依赖）
# ══════════════════════════════════════════════════════════════════

class _Result:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors: list = []

    def add_pass(self, name):
        self.passed += 1
        print(f"  PASS: {name}")

    def add_fail(self, name, msg):
        self.failed += 1
        self.errors.append((name, msg))
        print(f"  FAIL: {name}: {msg}")


def run_test(result: _Result, name: str, fn):
    try:
        fn()
        result.add_pass(name)
    except AssertionError as e:
        result.add_fail(name, str(e) or "AssertionError")
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        result.add_fail(name, f"{type(e).__name__}: {e}\n{tb}")


# ══════════════════════════════════════════════════════════════════
#  用例 01-07：纯函数行为
# ══════════════════════════════════════════════════════════════════

def test_01_fingerprint_stable():
    f = make_finding()
    r = make_report(project_id="proj-A")
    s1, fp1 = compute_finding_fingerprint(f, r)
    s2, fp2 = compute_finding_fingerprint(f, r)
    assert s1 == s2, f"scope unstable: {s1!r} vs {s2!r}"
    assert fp1 == fp2, f"fp unstable: {fp1!r} vs {fp2!r}"


def test_02_output_length_32_hex():
    f = make_finding()
    r = make_report(project_id="proj-A")
    _, fp = compute_finding_fingerprint(f, r)
    assert len(fp) == 32, f"fp length = {len(fp)} (expect 32)"
    assert all(c in string.hexdigits for c in fp), f"non-hex chars in fp: {fp!r}"
    # 整体算法标签也要可访问
    assert FP_ALGORITHM == "sha256_32_v1", f"FP_ALGORITHM = {FP_ALGORITHM!r}"
    assert FP_VERSION == 1, f"FP_VERSION = {FP_VERSION!r}"


def test_03_line_does_not_affect():
    f1 = make_finding()
    f2 = make_finding()
    f2["code_evidence"] = {**f2["code_evidence"], "line": 999}
    r = make_report(project_id="proj-A")
    _, fp1 = compute_finding_fingerprint(f1, r)
    _, fp2 = compute_finding_fingerprint(f2, r)
    assert fp1 == fp2, f"line changed but fp differs: {fp1} vs {fp2}"


def test_04_finding_id_report_id_not_affect():
    f1 = make_finding(finding_id="f_aaaaaaaaaaaa")
    f2 = make_finding(finding_id="f_bbbbbbbbbbbb")
    r1 = make_report(report_id="rpt_aaaaaaa", project_id="proj-A")
    r2 = make_report(report_id="rpt_bbbbbbb", project_id="proj-A")
    _, fp1 = compute_finding_fingerprint(f1, r1)
    _, fp2 = compute_finding_fingerprint(f2, r2)
    assert fp1 == fp2, f"finding_id/report_id changed but fp differs: {fp1} vs {fp2}"


def test_05_type_affects():
    f1 = make_finding(type="missing")
    f2 = make_finding(type="risk")
    r = make_report(project_id="proj-A")
    _, fp1 = compute_finding_fingerprint(f1, r)
    _, fp2 = compute_finding_fingerprint(f2, r)
    assert fp1 != fp2, f"finding_type changed but fp same: {fp1}"


def test_06_code_file_affects():
    f1 = make_finding()
    f2 = make_finding()
    f2["code_evidence"] = {**f2["code_evidence"], "file": "src/other/different.vue"}
    r = make_report(project_id="proj-A")
    _, fp1 = compute_finding_fingerprint(f1, r)
    _, fp2 = compute_finding_fingerprint(f2, r)
    assert fp1 != fp2, f"code_file changed but fp same: {fp1}"


def test_07_different_scope_no_cross_dedup():
    f = make_finding()
    rA = make_report(project_id="proj-A")
    rB = make_report(project_id="proj-B")
    sA, fpA = compute_finding_fingerprint(f, rA)
    sB, fpB = compute_finding_fingerprint(f, rB)
    assert sA != sB, f"scope same but expected diff: {sA}"
    assert fpA != fpB, f"different scope should yield different fp (scope is in fp input): {fpA}"
    # project_scope 清洗稳健性附加断言
    cleaned = _clean_snapshot_name_for_scope(
        "D:\\360Downloads\\蓝点\\recycle-applet-feature-1.2.3_20260507161200_a3f912.zip"
    )
    assert cleaned and "20260507161200" not in cleaned, f"timestamp not stripped: {cleaned!r}"
    assert ".zip" not in cleaned, f"archive suffix not stripped: {cleaned!r}"
    assert "\\" not in cleaned and "/" not in cleaned, f"path separators not stripped: {cleaned!r}"


# ══════════════════════════════════════════════════════════════════
#  用例 08-10：索引 lookup 行为
# ══════════════════════════════════════════════════════════════════

def test_08_same_scope_fp_with_tapd_bug_id_hit():
    cc = _build_index_with([
        (make_finding(finding_id="f_src", tapd_bug_id="BUG-100", tapd_url="https://t/100"),
         make_report(report_id="rpt_1", project_id="proj-A")),
    ])
    f_target = make_finding(finding_id="f_target")
    rpt = list(cc._reports.values())[0]
    scope, fp = cc._get_or_compute_fingerprint(f_target, rpt)
    src = cc._lookup_dedup_source(scope, fp, exclude_finding_id="f_target")
    assert src is not None, "dedup source should be hit (same scope+fp+source has tapd_bug_id)"
    assert src["tapd_bug_id"] == "BUG-100"
    assert src["finding_id"] == "f_src"


def test_09_false_positive_source_not_hit():
    cc = _build_index_with([
        (make_finding(finding_id="f_src", tapd_bug_id="BUG-100",
                      manual_status="false_positive"),
         make_report(report_id="rpt_1", project_id="proj-A")),
    ])
    f_target = make_finding(finding_id="f_target")
    rpt = list(cc._reports.values())[0]
    scope, fp = cc._get_or_compute_fingerprint(f_target, rpt)
    src = cc._lookup_dedup_source(scope, fp, exclude_finding_id="f_target")
    assert src is None, f"false_positive source should NOT be hit, got {src!r}"


def test_10_no_tapd_bug_id_source_not_hit():
    cc = _build_index_with([
        (make_finding(finding_id="f_src", tapd_bug_id=None),
         make_report(report_id="rpt_1", project_id="proj-A")),
    ])
    f_target = make_finding(finding_id="f_target")
    rpt = list(cc._reports.values())[0]
    scope, fp = cc._get_or_compute_fingerprint(f_target, rpt)
    src = cc._lookup_dedup_source(scope, fp, exclude_finding_id="f_target")
    assert src is None, f"source without tapd_bug_id should NOT be hit, got {src!r}"


# ══════════════════════════════════════════════════════════════════
#  用例 11：单条 push 命中 dedup 时不调真实 TAPD HTTP
# ══════════════════════════════════════════════════════════════════

def test_11_single_push_dedup_no_http():
    cc = _reset_routes_module()
    src = make_finding(
        finding_id="f_src",
        tapd_bug_id="BUG-200",
        tapd_url="https://tapd/200",
        tapd_status="in_progress",
        tapd_status_name="处理中",
        tapd_pushed_at="2026-04-01T10:00:00",
    )
    target = make_finding(finding_id="f_target", tapd_bug_id=None)
    cc._reports = {
        "rpt_1": {
            "report_id": "rpt_1",
            "project_id": "proj-X",
            "code_snapshot_name": "recycle-applet",
            "findings": [src],
        },
        "rpt_2": {
            "report_id": "rpt_2",
            "project_id": "proj-X",
            "code_snapshot_name": "recycle-applet",
            "findings": [target],
        },
    }
    cc._fingerprint_index = {}
    cc._fingerprint_index_built = False

    # 阻止真正落盘 + 屏蔽 DB
    saved = []
    cc._save_report = lambda rpt: saved.append(rpt["report_id"])
    cc._get_storage_svc = lambda: None

    fake_config = {"workspace_id": "w1", "api_user": "u", "api_password": "p"}
    push_calls: list = []

    def fake_push(*args, **kwargs):
        push_calls.append(kwargs)
        return {"success": True, "bug_id": "SHOULD-NOT-BE-USED", "url": "x"}

    with mock.patch("services.tapd_service.load_tapd_config", return_value=fake_config), \
         mock.patch("services.tapd_service.push_bug_to_tapd", side_effect=fake_push):
        from routes.code_compare_routes import push_finding_to_tapd, PushToTapdRequest
        req = PushToTapdRequest()
        result = asyncio.run(push_finding_to_tapd("f_target", req))

    assert result.get("success") is True, f"unexpected: {result}"
    assert result.get("dedup_by_fingerprint") is True, f"expected dedup_by_fingerprint=True, got {result}"
    assert result.get("dedup_source_finding_id") == "f_src", f"got {result}"
    assert result.get("bug_id") == "BUG-200", f"got {result}"
    assert len(push_calls) == 0, (
        f"push_bug_to_tapd should NOT be called when dedup hits, "
        f"but called {len(push_calls)} times"
    )

    # 验证 target 字段已写回（且 tapd_pushed_at 未被伪造）
    assert target["tapd_bug_id"] == "BUG-200"
    assert target["dedup_by_fingerprint"] is True
    assert target.get("dedup_at"), "dedup_at must be set"
    assert target["dedup_source_finding_id"] == "f_src"
    assert target["dedup_source_report_id"] == "rpt_1"
    assert target.get("tapd_pushed_at") == "2026-04-01T10:00:00", (
        f"tapd_pushed_at should reuse source's value, not fabricated: "
        f"got {target.get('tapd_pushed_at')!r}"
    )
    assert target["content_fingerprint_version"] == FP_VERSION
    assert target["content_fingerprint_algorithm"] == FP_ALGORITHM


# ══════════════════════════════════════════════════════════════════
#  用例 12：批量推送中 dedup 与真推混合
# ══════════════════════════════════════════════════════════════════

def test_12_batch_push_dedup_mixed():
    cc = _reset_routes_module()
    src = make_finding(
        finding_id="f_src", tapd_bug_id="BUG-300",
        tapd_url="https://tapd/300",
        tapd_pushed_at="2026-04-01T10:00:00",
    )
    target_a = make_finding(finding_id="f_a", tapd_bug_id=None)  # 与 src 同 fp
    target_b = make_finding(finding_id="f_b", type="risk", tapd_bug_id=None)  # 不同 fp

    cc._reports = {
        "rpt_1": {
            "report_id": "rpt_1",
            "project_id": "proj-Y",
            "code_snapshot_name": "snap-y",
            "findings": [src, target_a, target_b],
        }
    }
    cc._fingerprint_index = {}
    cc._fingerprint_index_built = False

    saved = []
    cc._save_report = lambda rpt: saved.append(rpt["report_id"])
    cc._get_storage_svc = lambda: None

    push_calls: list = []

    def fake_push(*args, **kwargs):
        push_calls.append(kwargs.get("title", "?"))
        return {"success": True, "bug_id": "BUG-NEW", "url": "https://t/new"}

    fake_config = {"workspace_id": "w1", "api_user": "u", "api_password": "p"}

    with mock.patch("services.tapd_service.load_tapd_config", return_value=fake_config), \
         mock.patch("services.tapd_service.push_bug_to_tapd", side_effect=fake_push):
        from routes.code_compare_routes import (
            batch_push_findings_to_tapd, BatchPushToTapdRequest,
        )
        req = BatchPushToTapdRequest(finding_ids=["f_a", "f_b"])
        result = asyncio.run(batch_push_findings_to_tapd(req))

    data = result["data"]
    assert data["total"] == 2, f"data: {data}"
    assert data["pushed"] == 1, f"expected pushed=1, got data: {data}"
    assert data["dedup_by_fingerprint"] == 1, f"expected dedup=1, got data: {data}"
    statuses = {r["finding_id"]: r["status"] for r in data["results"]}
    assert statuses == {"f_a": "dedup_by_fingerprint", "f_b": "pushed"}, (
        f"unexpected results: {statuses}"
    )
    assert len(push_calls) == 1, (
        f"only target_b should call push, got {len(push_calls)} calls"
    )
    # 验证 target_a 字段已通过 dedup 写回
    assert target_a["tapd_bug_id"] == "BUG-300"
    assert target_a["dedup_by_fingerprint"] is True
    assert target_a["dedup_source_finding_id"] == "f_src"
    assert target_a["tapd_pushed_at"] == "2026-04-01T10:00:00"


# ══════════════════════════════════════════════════════════════════
#  用例 13：老 finding 无 fingerprint 时懒计算
# ══════════════════════════════════════════════════════════════════

def test_13_legacy_finding_lazy_compute():
    cc = _reset_routes_module()
    f = make_finding(finding_id="f_legacy")
    assert "content_fingerprint" not in f
    rpt = make_report(project_id="proj-Z")
    scope, fp = cc._get_or_compute_fingerprint(f, rpt)
    assert "content_fingerprint" in f, "fingerprint should be lazy-set on finding"
    assert f["content_fingerprint"] == fp
    assert f["content_fingerprint_version"] == FP_VERSION
    assert f["content_fingerprint_algorithm"] == FP_ALGORITHM
    # 第二次调用应复用而非重算（断言版本字段未被重写为别的值）
    scope2, fp2 = cc._get_or_compute_fingerprint(f, rpt)
    assert fp == fp2 and scope == scope2


# ══════════════════════════════════════════════════════════════════
#  用例 14：指纹输入串不包含敏感字段
# ══════════════════════════════════════════════════════════════════

def test_14_no_sensitive_in_input():
    f = make_finding(
        finding_id="f_xyz_unique_marker",  # 不应入指纹
        tapd_bug_id="BUG-NO-LEAK",
        tapd_url="https://t/no-leak",
        tapd_status="resolved",
    )
    r = make_report(report_id="rpt_xyz_unique_marker", project_id="proj-W-marker")
    raw = debug_fingerprint_input(f, r)

    # 严格禁止：finding_id / report_id / tapd_* 任意值进入指纹输入
    forbidden = [
        "f_xyz_unique_marker",
        "rpt_xyz_unique_marker",
        "BUG-NO-LEAK",
        "https://t/no-leak",
        "resolved",
    ]
    for kw in forbidden:
        assert kw.lower() not in raw.lower(), (
            f"forbidden value {kw!r} found in fingerprint input: {raw!r}"
        )

    # 安全侧关键字：测试集中假定我们没有把任何配置/凭据放进 finding 对象，
    # 验证 fingerprint 算法本身不会去读这些类名
    sensitive_keywords = ["password", "api_key", "api_password", "token"]
    for kw in sensitive_keywords:
        assert kw.lower() not in raw.lower(), (
            f"sensitive keyword {kw!r} unexpectedly in fingerprint input: {raw!r}"
        )


# ══════════════════════════════════════════════════════════════════
#  主入口
# ══════════════════════════════════════════════════════════════════

def main():
    print("=" * 64)
    print("D2-1 Finding Fingerprint 单元测试")
    print(f"FP_VERSION={FP_VERSION}  FP_ALGORITHM={FP_ALGORITHM}")
    print("=" * 64)

    result = _Result()
    cases = [
        ("01_fingerprint_stable", test_01_fingerprint_stable),
        ("02_output_length_32_hex", test_02_output_length_32_hex),
        ("03_line_does_not_affect", test_03_line_does_not_affect),
        ("04_finding_id_report_id_not_affect", test_04_finding_id_report_id_not_affect),
        ("05_type_affects", test_05_type_affects),
        ("06_code_file_affects", test_06_code_file_affects),
        ("07_different_scope_no_cross_dedup", test_07_different_scope_no_cross_dedup),
        ("08_same_scope_fp_with_tapd_bug_id_hit", test_08_same_scope_fp_with_tapd_bug_id_hit),
        ("09_false_positive_source_not_hit", test_09_false_positive_source_not_hit),
        ("10_no_tapd_bug_id_source_not_hit", test_10_no_tapd_bug_id_source_not_hit),
        ("11_single_push_dedup_no_http", test_11_single_push_dedup_no_http),
        ("12_batch_push_dedup_mixed", test_12_batch_push_dedup_mixed),
        ("13_legacy_finding_lazy_compute", test_13_legacy_finding_lazy_compute),
        ("14_no_sensitive_in_input", test_14_no_sensitive_in_input),
    ]
    for name, fn in cases:
        run_test(result, name, fn)

    print("=" * 64)
    print(f"PASS={result.passed}  FAIL={result.failed}  TOTAL={len(cases)}")
    print("=" * 64)

    return 0 if result.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
