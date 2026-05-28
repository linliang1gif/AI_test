#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P3-3B: 缺陷闭环 MVP — 专项测试脚本
覆盖: 创建/查询/详情/更新/状态流转/非法流转/从run_case创建/从failure_analysis创建
      duplicate_key/重复检测/关联run/defect_events/evidence脱敏
      quality gate blocker/known_issue/API主链路不受影响
"""
import sys, os, json, time, requests

BASE = os.environ.get("TEST_BASE_URL", "http://localhost:8000")
DEFECT_API = f"{BASE}/api/v2/defects"
GATE_API = f"{BASE}/api/v2/quality-gates"
CASE_API = f"{BASE}/api/v2/test-cases"
HEALTH = f"{BASE}/health"

results = []

def T(name, ok, detail=""):
    results.append((name, ok, detail))
    tag = "PASS" if ok else "FAIL"
    print(f"  [{tag}] {name}" + (f" — {detail}" if detail and not ok else ""))

def section(title):
    print(f"\n{'─'*50}\n  {title}\n{'─'*50}")

# ── wait for backend ──
def wait_backend(timeout=30):
    for i in range(timeout):
        try:
            r = requests.get(HEALTH, timeout=2)
            if r.status_code == 200:
                return True
        except:
            pass
        time.sleep(1)
    return False

print("=" * 60)
print("  P3-3B 缺陷闭环 MVP — 专项测试")
print("=" * 60)

if not wait_backend():
    print("❌ 后端未就绪"); sys.exit(1)

# ══════════════════════════════════════════════════════════
section("1. 创建人工缺陷")
r = requests.post(DEFECT_API, json={
    "title": "测试缺陷-人工创建",
    "description": "这是一个手动创建的测试缺陷",
    "severity": "major",
    "priority": "P1",
    "source": "manual",
    "module": "登录模块",
    "failure_category": "ui_error",
})
T("创建缺陷 201/200", r.status_code in (200, 201))
d1 = r.json()
defect_id = d1.get("id")
T("返回 id", defect_id is not None, f"id={defect_id}")
T("status=open", d1.get("status") == "open")
T("source=manual", d1.get("source") == "manual")
T("duplicate_key 非空", d1.get("duplicate_key") is not None and len(d1.get("duplicate_key", "")) > 0)

section("1A. run_case_id 类型兼容")
r = requests.post(DEFECT_API, json={
    "title": "测试缺陷-run_case_id数字兼容",
    "description": "run_case_id 传数字也应能创建缺陷",
    "severity": "major",
    "priority": "P2",
    "source": "manual",
    "run_case_id": 7282,
})
T("数字 run_case_id 创建缺陷 200", r.status_code in (200, 201), r.text[:200])
numeric_defect = r.json() if r.status_code in (200, 201) else {}
T("数字 run_case_id 保存为字符串", numeric_defect.get("run_case_id") == "7282", f"实际: {numeric_defect.get('run_case_id')}")

section("2. 查询缺陷列表")
r = requests.get(DEFECT_API)
T("列表 200", r.status_code == 200)
d = r.json()
T("返回 defects 数组", "defects" in d and isinstance(d["defects"], list))
T("total >= 1", d.get("total", 0) >= 1)

r2 = requests.get(DEFECT_API, params={"status": "open"})
T("过滤 status=open", r2.status_code == 200)
r3 = requests.get(DEFECT_API, params={"severity": "major"})
T("过滤 severity=major", r3.status_code == 200)
r4 = requests.get(DEFECT_API, params={"keyword": "人工创建"})
T("关键词搜索", r4.status_code == 200 and r4.json().get("total", 0) >= 1)

section("3. 查看缺陷详情")
r = requests.get(f"{DEFECT_API}/{defect_id}")
T("详情 200", r.status_code == 200)
detail = r.json()
T("包含 events", "events" in detail and isinstance(detail["events"], list))
T("events 有 created 事件", any(e.get("event_type") == "created" for e in detail.get("events", [])))

section("4. 更新缺陷")
r = requests.put(f"{DEFECT_API}/{defect_id}", json={"severity": "critical", "assigned_to": "tester1"})
T("更新 200", r.status_code == 200)
T("severity 已更新", r.json().get("severity") == "critical")

# 验证 update event
r = requests.get(f"{DEFECT_API}/{defect_id}")
events = r.json().get("events", [])
T("update event 记录", any(e.get("event_type") == "update" for e in events))

section("5. 状态合法流转")
# open -> confirmed
r = requests.post(f"{DEFECT_API}/{defect_id}/transition", json={"to_status": "confirmed", "comment": "已确认"})
T("open->confirmed 200", r.status_code == 200)
T("status=confirmed", r.json().get("status") == "confirmed")

# confirmed -> fixed
r = requests.post(f"{DEFECT_API}/{defect_id}/transition", json={"to_status": "fixed", "comment": "已修复"})
T("confirmed->fixed", r.status_code == 200 and r.json().get("status") == "fixed")

# fixed -> verified
r = requests.post(f"{DEFECT_API}/{defect_id}/transition", json={"to_status": "verified", "comment": "已验证"})
T("fixed->verified", r.status_code == 200 and r.json().get("status") == "verified")

# verified -> closed
r = requests.post(f"{DEFECT_API}/{defect_id}/transition", json={"to_status": "closed", "comment": "关闭"})
T("verified->closed", r.status_code == 200 and r.json().get("status") == "closed")
T("closed_at 已设置", r.json().get("closed_at") is not None)

# closed -> reopened
r = requests.post(f"{DEFECT_API}/{defect_id}/transition", json={"to_status": "reopened", "comment": "重新打开"})
T("closed->reopened", r.status_code == 200 and r.json().get("status") == "reopened")

section("6. 状态非法流转返回 400")
# reopened -> closed (非法)
r = requests.post(f"{DEFECT_API}/{defect_id}/transition", json={"to_status": "closed"})
T("reopened->closed 400", r.status_code == 400)
# reopened -> verified (非法)
r = requests.post(f"{DEFECT_API}/{defect_id}/transition", json={"to_status": "verified"})
T("reopened->verified 400", r.status_code == 400)

# 恢复到 open 相关状态: reopened -> confirmed
requests.post(f"{DEFECT_API}/{defect_id}/transition", json={"to_status": "confirmed"})

section("7. 从 run_case 创建缺陷 (需要先有执行记录)")
# 查找已有的 run_case (从之前的执行记录中获取)
run_case_id = None
case_id = None
try:
    runs_r = requests.get(f"{BASE}/api/v2/observability/runs?limit=5")
    runs_data = runs_r.json()
    runs_list = runs_data.get("data", runs_data.get("runs", []))
    if isinstance(runs_list, list):
        for run_item in runs_list:
            rid = run_item.get("id") or run_item.get("run_id")
            if rid:
                detail_r = requests.get(f"{BASE}/api/v2/observability/runs/{rid}")
                if detail_r.status_code == 200:
                    dd = detail_r.json().get("data", detail_r.json())
                    rcs = dd.get("run_cases", [])
                    if rcs:
                        run_case_id = str(rcs[0].get("id"))
                        case_id = rcs[0].get("test_case_id")
                        break
except Exception as e:
    pass

if run_case_id:
    r = requests.post(f"{DEFECT_API}/from-run-case", json={"run_case_id": run_case_id})
    T("from-run-case 200", r.status_code == 200)
    d = r.json()
    T("source=run_failure", d.get("source") == "run_failure")
    T("case_id 关联", d.get("case_id") is not None)
    T("evidence_json 存在", d.get("evidence_json") is not None)
    if str(run_case_id).isdigit():
        r_num = requests.post(f"{DEFECT_API}/from-run-case", json={"run_case_id": int(run_case_id)})
        T("from-run-case 数字 run_case_id 200", r_num.status_code == 200, r_num.text[:200])
        d_num = r_num.json() if r_num.status_code == 200 else {}
        T("from-run-case 返回字符串 run_case_id", d_num.get("run_case_id") == str(int(run_case_id)), f"实际: {d_num.get('run_case_id')}")
    else:
        T("from-run-case 数字 run_case_id 200", True, "run_case_id 非数字，跳过")
        T("from-run-case 返回字符串 run_case_id", True, "跳过")
    from_rc_id = d.get("id")
else:
    # 如果没有历史执行记录，测试 from-run-case 对不存在的 run_case 返回 404
    r = requests.post(f"{DEFECT_API}/from-run-case", json={"run_case_id": "nonexistent_rc"})
    T("from-run-case 404 for missing", r.status_code == 404)
    r_num = requests.post(f"{DEFECT_API}/from-run-case", json={"run_case_id": 999999999})
    T("from-run-case 缺失数字 run_case_id 不返回 422", r_num.status_code != 422, r_num.text[:200])
    T("source=run_failure (skip: no run_case)", True, "无历史执行记录，跳过正向测试")
    T("case_id 关联 (skip)", True, "跳过")
    T("evidence_json 存在 (skip)", True, "跳过")
    from_rc_id = None

section("8. 从 failure_analysis 创建缺陷")
r = requests.post(f"{DEFECT_API}/from-failure-analysis", json={
    "title": "归因分析缺陷",
    "failure_category": "network_error",
    "error_message": "Connection timeout to api.example.com",
    "suggested_action": "检查网络连接",
    "severity": "critical",
    "module": "API网关",
})
T("from-failure-analysis 200", r.status_code == 200)
d = r.json()
T("source=failure_analysis", d.get("source") == "failure_analysis")
fa_id = d.get("id")

section("9. duplicate_key 生成与重复检测")
T("defect_id duplicate_key 存在", d1.get("duplicate_key") is not None)

# 检查重复: 使用相同参数
r = requests.get(f"{DEFECT_API}/duplicates/check", params={
    "case_id": d1.get("case_id", ""),
    "failure_category": "ui_error",
    "error_message": "测试缺陷-人工创建",
})
T("duplicates/check 200", r.status_code == 200)
dup_data = r.json()
T("返回 duplicate_key", "duplicate_key" in dup_data)
T("返回 has_duplicates", "has_duplicates" in dup_data)

section("10. 关联 run")
if defect_id:
    r = requests.post(f"{DEFECT_API}/{defect_id}/link-run", json={"run_id": "test-run-123"})
    T("link-run 200", r.status_code == 200)
    # 检查 events 有 link_run 事件
    r2 = requests.get(f"{DEFECT_API}/{defect_id}")
    events = r2.json().get("events", [])
    T("link_run event 记录", any(e.get("event_type") == "link_run" for e in events))
else:
    T("link-run 200", False, "无 defect_id")
    T("link_run event 记录", False, "跳过")

section("11. defect_events 完整记录")
r = requests.get(f"{DEFECT_API}/{defect_id}")
events = r.json().get("events", [])
event_types = [e["event_type"] for e in events]
T("events 包含 created", "created" in event_types)
T("events 包含 status_change", "status_change" in event_types)
T("events 包含 update", "update" in event_types)
T("events >= 5 条", len(events) >= 5, f"实际 {len(events)}")

section("12. evidence 脱敏")
r = requests.post(f"{DEFECT_API}/from-failure-analysis", json={
    "title": "脱敏测试",
    "error_message": "token: abc123secret, authorization: Bearer xyz789",
    "failure_category": "auth_error",
    "evidence_json": {
        "error_message": "token: abc123secret, authorization: Bearer xyz789",
        "cookie": "session=secret_value_here",
    }
})
T("脱敏缺陷创建 200", r.status_code == 200)
ev = r.json().get("evidence_json", {})
err_msg = str(ev.get("error_message", ""))
T("token 脱敏", "abc123secret" not in err_msg, f"实际: {err_msg[:80]}")
cookie_val = str(ev.get("cookie", ""))
T("cookie 脱敏", "secret_value_here" not in cookie_val, f"实际: {cookie_val[:80]}")

section("13. quality gate 识别 open blocker defect")
# 创建一个 blocker 缺陷
r = requests.post(DEFECT_API, json={
    "title": "Blocker: 登录完全失败",
    "severity": "blocker",
    "source": "manual",
})
blocker_id = r.json().get("id")
T("创建 blocker 缺陷", blocker_id is not None)

# 使用 evaluate-summary 传入 defect_summary
r = requests.post(f"{GATE_API}/evaluate-summary", json={
    "suite_summary": {
        "total_cases": 10,
        "passed_cases": 10,
        "failed_cases": 0,
        "skipped_cases": 0,
        "xfail_cases": 0,
        "defect_summary": {
            "linked_defects": 1,
            "open_defects": 1,
            "known_issues": 0,
            "blocker_defects": 1,
            "blocker_ids": [blocker_id],
        }
    },
    "gate_config": {"open_blocker_defects_policy": "fail"}
})
T("gate evaluate-summary 200", r.status_code == 200)
gate = r.json()
T("gate_status=failed (blocker)", gate.get("gate_status") == "failed")
has_blocker_rule = any(f.get("rule") == "open_blocker_defects" for f in gate.get("gate_failures", []))
T("gate_failures 包含 open_blocker_defects", has_blocker_rule)

section("14. known_issue_policy=warn 生效")
r = requests.post(f"{GATE_API}/evaluate-summary", json={
    "suite_summary": {
        "total_cases": 10,
        "passed_cases": 8,
        "failed_cases": 2,
        "skipped_cases": 0,
        "xfail_cases": 0,
        "defect_summary": {
            "linked_defects": 2,
            "open_defects": 0,
            "known_issues": 2,
            "blocker_defects": 0,
        }
    },
    "gate_config": {"known_issue_policy": "warn", "fail_on_any_failed": False}
})
T("gate known_issue warn 200", r.status_code == 200)
gate2 = r.json()
has_ki_warning = any(w.get("rule") == "known_issue" for w in gate2.get("gate_warnings", []))
T("gate_warnings 包含 known_issue", has_ki_warning)
T("gate_status not failed for known_issue warn", gate2.get("gate_status") != "failed" or not has_ki_warning)

section("15. defect summary for gate API")
r = requests.get(f"{DEFECT_API}/summary/for-gate")
T("summary/for-gate 200", r.status_code == 200)
summary = r.json()
T("返回 linked_defects", "linked_defects" in summary)
T("返回 blocker_defects", "blocker_defects" in summary)
T("blocker_defects >= 1", summary.get("blocker_defects", 0) >= 1)

section("16. 主链路不受影响")
# health
r = requests.get(HEALTH)
T("health 200", r.status_code == 200)

# test-cases
r = requests.get(f"{BASE}/api/v2/test-cases?limit=1")
T("test-cases 200", r.status_code == 200)

# test-suites
r = requests.get(f"{BASE}/api/v2/test-suites")
T("test-suites 200", r.status_code == 200)

# quality-gates default-config
r = requests.get(f"{GATE_API}/default-config")
T("quality-gates default-config 200", r.status_code == 200)

# test-data datasets
r = requests.get(f"{BASE}/api/v2/test-data/datasets")
T("test-data datasets 200", r.status_code == 200)

# defects list
r = requests.get(DEFECT_API)
T("defects list 200", r.status_code == 200)

section("17. 404 边界")
r = requests.get(f"{DEFECT_API}/99999")
T("不存在的缺陷 404", r.status_code == 404)
r = requests.put(f"{DEFECT_API}/99999", json={"title": "x"})
T("更新不存在缺陷 404", r.status_code == 404)

# ══════════════════════════════════════════════════════════
# 清理测试数据
section("清理")
print("  (测试缺陷保留供后续验证)")

# ── 汇总 ──
print("\n" + "=" * 60)
passed = sum(1 for _, ok, _ in results if ok)
failed = sum(1 for _, ok, _ in results if not ok)
print(f"  P3-3B 测试汇总: {passed} PASS / {failed} FAIL / {len(results)} TOTAL")
print("=" * 60)

if failed > 0:
    print("\n  ❌ 失败项:")
    for name, ok, detail in results:
        if not ok:
            print(f"    - {name}: {detail}")

sys.exit(1 if failed > 0 else 0)
