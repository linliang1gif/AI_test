#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
D2-3A 迭代中心 MVP 验收脚本
15 项核心验证 + trace_id + 422 + 敏感字段检查
"""
import os, sys, json, requests, re

BASE = "http://127.0.0.1:8001"
REQUIRED_FIELDS = {"code", "message", "trace_id"}
SENSITIVE = ["token", "access_token", "refresh_token", "authorization",
             "cookie", "api_key", "secret", "password", "client_secret"]
ok = 0
fail = 0
warn = 0

# ── 需要一个真实项目 ID ──
def get_first_project_id():
    r = requests.get(f"{BASE}/api/v2/projects")
    data = r.json()
    projects = data.get("projects", data.get("data", []))
    if projects:
        return projects[0]["id"]
    return None


def chk(label, passed, detail=""):
    global ok, fail
    sym = "\u2705" if passed else "\u274c"
    tag = "PASS" if passed else "FAIL"
    suffix = f" \u2014 {detail}" if detail else ""
    print(f"  {sym} [{tag}] {label}{suffix}")
    if passed:
        ok += 1
    else:
        fail += 1


def check_trace_id(resp, label):
    """检查响应体和 header 中是否有 trace_id"""
    has_header = "X-Trace-Id" in resp.headers
    try:
        body = resp.json()
        has_body = "trace_id" in body
    except Exception:
        has_body = False
    # 对于成功响应(2xx)，只需 header 中有；对于错误响应，body 中也应有
    if resp.status_code >= 400:
        chk(f"{label}: trace_id in body+header", has_header and has_body,
            f"header={has_header} body={has_body}")
    else:
        chk(f"{label}: X-Trace-Id header", has_header,
            resp.headers.get("X-Trace-Id", "MISSING"))


def check_no_sensitive(resp, label):
    """检查错误响应中不泄露敏感字段值"""
    try:
        text = json.dumps(resp.json(), ensure_ascii=False)
    except Exception:
        return
    for sw in SENSITIVE:
        if sw.upper() in text.upper() and "trace_id" not in sw:
            # 只检查值泄露，不检查字段名
            pass  # field names may appear in error messages, that's ok


def main():
    global ok, fail
    print("=" * 60)
    print("  D2-3A 迭代中心 MVP 验收")
    print("=" * 60)

    project_id = get_first_project_id()
    if not project_id:
        print("  \u274c 无法获取项目列表，验收终止")
        return
    print(f"  使用项目 ID: {project_id}\n")

    # ═══ 1. 创建迭代 ═══
    print("[1] 创建迭代")
    r = requests.post(f"{BASE}/api/v2/iterations", json={
        "project_id": project_id,
        "name": "D2-3A 验收迭代",
        "version": "1.0.0",
        "description": "自动化验收测试迭代",
        "owner": "test_user",
        "test_owner": "qa_user",
    })
    chk("创建迭代 status=200", r.status_code == 200, f"status={r.status_code}")
    iter_data = r.json()
    iter_id = iter_data.get("id")
    chk("返回 id", iter_id is not None, f"id={iter_id}")
    chk("返回 version", iter_data.get("version") == "1.0.0")
    chk("返回 test_owner", iter_data.get("test_owner") == "qa_user")
    check_trace_id(r, "创建迭代")

    if not iter_id:
        print("  \u274c 迭代创建失败，后续测试跳过")
        print(f"\n总计: {ok + fail}  通过: {ok}  失败: {fail}")
        return

    # ═══ 2. 查询迭代列表 ═══
    print("\n[2] 查询迭代列表")
    r = requests.get(f"{BASE}/api/v2/projects/{project_id}/iterations")
    chk("列表 status=200", r.status_code == 200)
    data = r.json()
    chk("iterations 是列表", isinstance(data.get("iterations"), list))
    found = any(it["id"] == iter_id for it in data.get("iterations", []))
    chk("列表包含刚创建的迭代", found)
    check_trace_id(r, "迭代列表")

    # ═══ 3. 查询迭代详情 ═══
    print("\n[3] 查询迭代详情")
    r = requests.get(f"{BASE}/api/v2/iterations/{iter_id}")
    chk("详情 status=200", r.status_code == 200)
    d = r.json()
    chk("包含 stats 字段", "total_cases" in d or "requirement_count" in d)
    check_trace_id(r, "迭代详情")

    # ═══ 4. 录入需求 ═══
    print("\n[4] 录入需求")
    r = requests.post(f"{BASE}/api/v2/iterations/{iter_id}/requirements", json={
        "title": "用户登录功能",
        "content": "用户必须输入用户名和密码进行登录。密码不能少于6位。登录失败3次应锁定账号。",
        "risk_level": "P0",
    })
    chk("录入需求 status=200", r.status_code == 200)
    req_data = r.json()
    req_id = req_data.get("id")
    chk("返回需求 id", req_id is not None)
    check_trace_id(r, "录入需求")

    # 录入第二个需求
    requests.post(f"{BASE}/api/v2/iterations/{iter_id}/requirements", json={
        "title": "用户信息修改",
        "content": "用户可以修改昵称、头像、手机号。手机号格式必须校验。",
        "risk_level": "P1",
    })

    # ═══ 5. AI 解析需求 ═══
    print("\n[5] AI 解析需求")
    r = requests.post(f"{BASE}/api/v2/iterations/{iter_id}/ai/analyze-requirements")
    chk("AI解析 status=200", r.status_code == 200)
    ai_data = r.json()
    analysis = ai_data.get("analysis", {})
    chk("返回 functional_points", isinstance(analysis.get("functional_points"), list))
    chk("返回 test_points", isinstance(analysis.get("test_points"), list))
    chk("返回 source", ai_data.get("source") in ("llm", "fallback", "empty"))
    check_trace_id(r, "AI解析")

    # ═══ 6. 生成测试点 ═══
    print("\n[6] 生成测试点")
    r = requests.post(f"{BASE}/api/v2/iterations/{iter_id}/test-points/generate")
    chk("生成测试点 status=200", r.status_code == 200)
    tp_data = r.json()
    generated_count = tp_data.get("generated", 0)
    chk("generated > 0", generated_count > 0, f"generated={generated_count}")
    chk("test_points 是列表", isinstance(tp_data.get("test_points"), list))
    if tp_data.get("test_points"):
        tp0 = tp_data["test_points"][0]
        chk("测试点含 ai_generated=True", tp0.get("ai_generated") == True)
    check_trace_id(r, "生成测试点")

    # ═══ 7. 查询测试点 ═══
    print("\n[7] 查询测试点")
    r = requests.get(f"{BASE}/api/v2/iterations/{iter_id}/test-points")
    chk("查询测试点 status=200", r.status_code == 200)
    tps = r.json().get("test_points", [])
    chk("测试点列表非空", len(tps) > 0, f"count={len(tps)}")
    check_trace_id(r, "查询测试点")

    # ═══ 8. 确认测试点 ═══
    print("\n[8] 确认测试点")
    if tps:
        first_tp_id = tps[0]["id"]
        r = requests.patch(f"{BASE}/api/v2/iteration-test-points/{first_tp_id}/confirm",
                           json={"confirmed": True})
        chk("确认测试点 status=200", r.status_code == 200)
        chk("confirmed=True", r.json().get("confirmed") == True)
        check_trace_id(r, "确认测试点")

        # 确认所有测试点
        for tp in tps[1:]:
            requests.patch(f"{BASE}/api/v2/iteration-test-points/{tp['id']}/confirm",
                           json={"confirmed": True})
    else:
        chk("确认测试点(跳过: 无测试点)", False)

    # ═══ 9. 生成测试用例 ═══
    print("\n[9] 生成测试用例")
    r = requests.post(f"{BASE}/api/v2/iterations/{iter_id}/test-cases/generate")
    chk("生成测试用例 status=200", r.status_code == 200)
    tc_data = r.json()
    tc_count = tc_data.get("generated", 0)
    chk("generated > 0", tc_count > 0, f"generated={tc_count}")
    chk("case_ids 是列表", isinstance(tc_data.get("case_ids"), list))
    check_trace_id(r, "生成测试用例")

    # ═══ 10. 生成执行集 ═══
    print("\n[10] 生成执行集")
    r = requests.post(f"{BASE}/api/v2/iterations/{iter_id}/execution-sets",
                      json={"type": "iteration"})
    chk("生成执行集 status=200", r.status_code == 200)
    es_data = r.json()
    chk("返回 type=iteration", es_data.get("type") == "iteration")
    chk("case_count > 0", es_data.get("case_count", 0) > 0)
    check_trace_id(r, "生成执行集")

    # ═══ 11. 查询执行集 ═══
    print("\n[11] 查询执行集")
    r = requests.get(f"{BASE}/api/v2/iterations/{iter_id}/execution-sets")
    chk("查询执行集 status=200", r.status_code == 200)
    chk("execution_sets 非空", len(r.json().get("execution_sets", [])) > 0)
    check_trace_id(r, "查询执行集")

    # ═══ 12. 迭代报告 ═══
    print("\n[12] 迭代报告")
    r = requests.get(f"{BASE}/api/v2/iterations/{iter_id}/report")
    chk("迭代报告 status=200", r.status_code == 200)
    rpt = r.json()
    chk("报告含 iteration", "iteration" in rpt)
    chk("报告含 stats", "stats" in rpt)
    chk("报告含 generated_at", "generated_at" in rpt)
    check_trace_id(r, "迭代报告")

    # ═══ 13. trace_id 全链路检查 ═══
    print("\n[13] trace_id 全链路")
    for path in [f"/api/v2/iterations/{iter_id}",
                 f"/api/v2/iterations/{iter_id}/requirements",
                 f"/api/v2/iterations/{iter_id}/test-points"]:
        r2 = requests.get(f"{BASE}{path}")
        has = "X-Trace-Id" in r2.headers
        chk(f"X-Trace-Id on {path}", has)

    # ═══ 14. 422 标准结构 ═══
    print("\n[14] 422 参数错误标准结构")
    r = requests.post(f"{BASE}/api/v2/iterations", json={})
    chk("422 status", r.status_code == 422)
    d422 = r.json()
    chk("422 含 code", "code" in d422)
    chk("422 含 message", "message" in d422)
    chk("422 含 trace_id", "trace_id" in d422)

    # ═══ 15. 敏感字段不泄露 ═══
    print("\n[15] 敏感字段不泄露")
    r = requests.get(f"{BASE}/api/v2/iterations/999999?token=SECRET123&api_key=KEY456")
    text = json.dumps(r.json(), ensure_ascii=False)
    chk("token 值未泄露", "SECRET123" not in text)
    chk("api_key 值未泄露", "KEY456" not in text)

    # ═══ 清理 ═══
    print("\n[cleanup] 清理验收数据")
    requests.delete(f"{BASE}/api/v2/iterations/{iter_id}",
                    json={"confirm": True, "confirm_text": "DELETE_ITERATION"})
    print("  清理完成")

    # ═══ Summary ═══
    total = ok + fail
    print(f"\n{'=' * 60}")
    print(f"  总计: {total}  通过: {ok}  失败: {fail}")
    if fail == 0:
        print("  \U0001f389 D2-3A 迭代中心 MVP 验收全部通过！")
    else:
        print(f"  \u26d4 存在 {fail} 项失败，需修复")
    print("=" * 60)


if __name__ == "__main__":
    main()
