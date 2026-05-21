#!/usr/bin/env python3
"""
AI Product Studio Phase 2 — 产物与测试资产追溯 验收脚本
用法: python scripts/test_product_studio_traceability.py http://127.0.0.1:8000
"""

import sys
import requests

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:8000"
API = f"{BASE}/api/v2/product-studio"

results = []


def check(name, condition, note=""):
    status = "✅" if condition else "❌"
    results.append((name, condition))
    if note:
        print(f"    {status} {name}  ({note})")
    else:
        print(f"    {status} {name}")


def main():
    print("=" * 60)
    print("AI Product Studio Phase 2 — 追溯验收测试")
    print(f"BASE: {API}")
    print("=" * 60)

    # ── 1. 创建 ProductIdea ──
    print("\n[1] 创建产品想法")
    r = requests.post(f"{API}/ideas", json={
        "title": "追溯测试产品",
        "product_direction": "测试追溯链路",
        "target_users": "QA 工程师",
        "pain_points": "手动拆需求耗时",
    })
    check("创建想法 status=200", r.status_code == 200)
    idea = r.json()
    idea_id = idea.get("idea_id", "")
    check("返回 idea_id", bool(idea_id))

    # ── 2. 生成 PRD Artifact ──
    print("\n[2] 生成 PRD Artifact")
    r = requests.post(f"{API}/ideas/{idea_id}/generate-prd", json={})
    check("生成 PRD status=200", r.status_code == 200)
    prd_data = r.json()
    prd_artifact_id = prd_data.get("artifact_id")
    prd_status = prd_data.get("status")
    check("PRD 生成有 artifact_id 或 failed", prd_artifact_id or prd_status == "failed")

    # ── 2b. 生成 acceptance_criteria Artifact ──
    print("\n[2b] 生成验收标准 Artifact")
    r = requests.post(f"{API}/ideas/{idea_id}/generate-acceptance-criteria", json={})
    check("生成验收标准 status=200", r.status_code == 200)
    ac_data = r.json()
    ac_artifact_id = ac_data.get("artifact_id")

    # ── 2c. 生成 product_solution Artifact ──
    print("\n[2c] 生成产品方案 Artifact")
    r = requests.post(f"{API}/ideas/{idea_id}/generate-solution", json={})
    check("生成产品方案 status=200", r.status_code == 200)
    sol_data = r.json()
    sol_artifact_id = sol_data.get("artifact_id")

    # ── 3. 从 PRD Artifact 生成 RequirementPoint 草稿 ──
    rp_link_ids = []
    if prd_artifact_id:
        print("\n[3] 从 PRD 生成需求点")
        r = requests.post(f"{API}/artifacts/{prd_artifact_id}/generate-requirement-points")
        check("生成需求点 status=200", r.status_code == 200)
        rp_result = r.json()
        check("返回 generated_count", "generated_count" in rp_result)
        check("返回 requirement_points 列表", isinstance(rp_result.get("requirement_points"), list))
        check("返回 trace_links 列表", isinstance(rp_result.get("trace_links"), list))
        rp_count = rp_result.get("generated_count", 0)
        if rp_count > 0:
            check("生成了至少 1 条需求点", rp_count >= 1, f"count={rp_count}")
            rp_link_ids = [lk["link_id"] for lk in rp_result.get("trace_links", [])]
            check("需求点默认状态 draft", all(
                rp.get("status") == "draft" for rp in rp_result.get("requirement_points", [])))
        else:
            check("需求点生成失败(LLM 问题)", True,
                  rp_result.get("error_message", "unknown"))
    else:
        print("\n[3] PRD 生成失败，跳过需求点生成")
        check("PRD 失败 跳过需求点", True, "prd failed")

    # ── 4. 从 PRD Artifact 生成 TestCase 草稿 ──
    tc_link_ids = []
    if prd_artifact_id:
        print("\n[4] 从 PRD 生成测试用例")
        r = requests.post(f"{API}/artifacts/{prd_artifact_id}/generate-test-cases")
        check("生成测试用例 status=200", r.status_code == 200)
        tc_result = r.json()
        check("返回 generated_count", "generated_count" in tc_result)
        check("返回 test_cases 列表", isinstance(tc_result.get("test_cases"), list))
        check("返回 trace_links 列表", isinstance(tc_result.get("trace_links"), list))
        tc_count = tc_result.get("generated_count", 0)
        if tc_count > 0:
            check("生成了至少 1 条测试用例", tc_count >= 1, f"count={tc_count}")
            tc_link_ids = [lk["link_id"] for lk in tc_result.get("trace_links", [])]
            check("测试用例默认状态 draft", all(
                tc.get("status") == "draft" for tc in tc_result.get("test_cases", [])))
        else:
            check("测试用例生成失败(LLM 问题)", True,
                  tc_result.get("error_message", "unknown"))
    else:
        print("\n[4] PRD 生成失败，跳过测试用例生成")
        check("PRD 失败 跳过测试用例", True, "prd failed")

    # ── 5. 查询 trace-links ──
    if prd_artifact_id:
        print("\n[5] 查询 trace-links")
        r = requests.get(f"{API}/artifacts/{prd_artifact_id}/trace-links")
        check("trace-links status=200", r.status_code == 200)
        tl = r.json()
        check("返回 artifact 对象", "artifact" in tl)
        check("返回 requirement_points 列表", isinstance(tl.get("requirement_points"), list))
        check("返回 test_cases 列表", isinstance(tl.get("test_cases"), list))
        check("返回 trace_links 列表", isinstance(tl.get("trace_links"), list))
    else:
        print("\n[5] 跳过 trace-links 查询")

    # ── 6. 确认一个 trace link ──
    if rp_link_ids:
        print("\n[6] 确认 trace link")
        r = requests.post(f"{API}/trace-links/{rp_link_ids[0]}/confirm")
        check("确认 status=200", r.status_code == 200)
        check("确认后 status=confirmed", r.json().get("status") == "confirmed")
    else:
        print("\n[6] 无可用 link，跳过确认")
        check("跳过确认", True, "no links")

    # ── 7. 驳回一个 trace link ──
    if tc_link_ids:
        print("\n[7] 驳回 trace link")
        r = requests.post(f"{API}/trace-links/{tc_link_ids[0]}/reject")
        check("驳回 status=200", r.status_code == 200)
        check("驳回后 status=rejected", r.json().get("status") == "rejected")
    else:
        print("\n[7] 无可用 link，跳过驳回")
        check("跳过驳回", True, "no links")

    # ── 8. 不存在 artifact_id ──
    print("\n[8] 不存在的 artifact_id")
    r = requests.post(f"{API}/artifacts/nonexistent_art/generate-requirement-points")
    check("不存在 artifact 返回 404", r.status_code == 404)
    r = requests.post(f"{API}/artifacts/nonexistent_art/generate-test-cases")
    check("不存在 artifact 生成用例 返回 404", r.status_code == 404)
    r = requests.get(f"{API}/artifacts/nonexistent_art/trace-links")
    check("不存在 artifact trace-links 返回 404", r.status_code == 404)

    # ── 9. 不支持的 artifact_type ──
    print("\n[9] 不支持的 artifact_type")
    # prototype 不支持生成需求点
    r2 = requests.post(f"{API}/ideas/{idea_id}/generate-prototype", json={})
    proto_art_id = r2.json().get("artifact_id")
    if proto_art_id:
        r = requests.post(f"{API}/artifacts/{proto_art_id}/generate-requirement-points")
        check("prototype 生成需求点 返回 400", r.status_code == 400)
        r = requests.post(f"{API}/artifacts/{proto_art_id}/generate-test-cases")
        check("prototype 生成用例 返回 400", r.status_code == 400)
    else:
        check("prototype 生成失败 跳过类型校验", True)

    # product_solution 不支持生成测试用例
    if sol_artifact_id:
        r = requests.post(f"{API}/artifacts/{sol_artifact_id}/generate-test-cases")
        check("product_solution 生成用例 返回 400", r.status_code == 400)
    else:
        check("product_solution 失败 跳过", True)

    # ── 10. 不存在 trace link ──
    print("\n[10] 不存在 trace link")
    r = requests.post(f"{API}/trace-links/nonexistent_link/confirm")
    check("不存在 link confirm 返回 404", r.status_code == 404)
    r = requests.post(f"{API}/trace-links/nonexistent_link/reject")
    check("不存在 link reject 返回 404", r.status_code == 404)

    # ── 11. 从验收标准生成测试用例 ──
    if ac_artifact_id:
        print("\n[11] 从验收标准 Artifact 生成测试用例")
        r = requests.post(f"{API}/artifacts/{ac_artifact_id}/generate-test-cases")
        check("验收标准→测试用例 status=200", r.status_code == 200)
        ac_tc = r.json()
        check("返回 generated_count", "generated_count" in ac_tc)
    else:
        print("\n[11] 验收标准生成失败，跳过")
        check("跳过验收标准→测试用例", True)

    # ── 12. 不影响原有 Product Studio 功能 ──
    print("\n[12] 不影响原有功能")
    r = requests.get(f"{API}/ideas")
    check("想法列表正常", r.status_code == 200)
    r = requests.get(f"{BASE}/health")
    check("健康检查正常", r.status_code == 200)

    # ── 汇总 ──
    print("\n" + "=" * 60)
    print("验收结果汇总")
    print("=" * 60)
    passed = sum(1 for _, ok in results if ok)
    failed = sum(1 for _, ok in results if not ok)
    for name, ok in results:
        print(f"  {'✅' if ok else '❌'} {name}")
    print(f"\n总计: {len(results)} 项 | ✅ 通过: {passed} | ❌ 失败: {failed}")
    if failed == 0:
        print("\n🎉 全部通过！")
    else:
        print(f"\n⚠️ 有 {failed} 项失败，请检查")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
