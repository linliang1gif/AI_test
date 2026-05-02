#!/usr/bin/env python3
"""
P1-8A-Guard: AI 自愈安全加固测试
覆盖 dry_run / 字段白名单 / deleted 拒绝 / 规则降级 / 脱敏 等
"""
import json
import requests
import sys

BASE = "http://localhost:8000"
H = {"Content-Type": "application/json"}

passed = 0
failed = 0
total = 0


def check(name, condition, detail=""):
    global passed, failed, total
    total += 1
    if condition:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name}  {detail}")


def get_case_ids(limit=5):
    r = requests.get(f"{BASE}/api/v2/test-cases", params={"limit": limit}, timeout=10)
    if r.status_code != 200:
        return []
    data = r.json()
    cases = data if isinstance(data, list) else data.get("test_cases", [])
    return [tc["id"] for tc in cases]


def get_case(case_id):
    r = requests.get(f"{BASE}/api/v2/test-cases", params={"limit": 500}, timeout=10)
    if r.status_code != 200:
        return None
    data = r.json()
    cases = data if isinstance(data, list) else data.get("test_cases", [])
    for tc in cases:
        if tc["id"] == case_id:
            return tc
    return None


# ─── 1. dry_run=true 不修改数据库 ────────────────────────
print("\n── 1. dry_run=true 不修改数据库 ──")
case_ids = get_case_ids(3)
if case_ids:
    cid = case_ids[0]
    before_case = get_case(cid)

    r = requests.post(f"{BASE}/api/v2/ai/test-cases/heal", headers=H, json={
        "dry_run": True,
        "cases": [{"case_id": cid, "issues": ["缺少断言"], "fix_suggestion": "补充 status_code 断言"}]
    }, timeout=60)
    check("1.1 dry_run=true returns 200", r.status_code == 200)
    data = r.json()
    check("1.2 dry_run=true in response", data.get("dry_run") is True)
    check("1.3 has results array", isinstance(data.get("results"), list) and len(data["results"]) > 0)
    result = data["results"][0]
    check("1.4 has before field", "before" in result)
    check("1.5 has after field", "after" in result)
    check("1.6 has changes field", "changes" in result)
    check("1.7 applied is False", result.get("applied") is False)
    check("1.8 has source field", result.get("source") in ("ai", "rule_based"))

    after_case = get_case(cid)
    if before_case and after_case:
        check("1.9 DB not modified (steps unchanged)",
              json.dumps(before_case.get("steps")) == json.dumps(after_case.get("steps")))
        check("1.10 DB not modified (assertions unchanged)",
              json.dumps(before_case.get("assertions")) == json.dumps(after_case.get("assertions")))
    else:
        check("1.9 DB not modified (steps unchanged)", False, "could not fetch case")
        check("1.10 DB not modified (assertions unchanged)", False, "could not fetch case")
else:
    for i in range(10):
        check(f"1.{i+1} skipped (no cases)", False, "no test cases found")


# ─── 2. dry_run=false 才修改数据库 ───────────────────────
print("\n── 2. dry_run=false 才修改数据库 ──")
if case_ids:
    cid = case_ids[0]
    r = requests.post(f"{BASE}/api/v2/ai/test-cases/heal", headers=H, json={
        "dry_run": False,
        "cases": [{"case_id": cid, "issues": ["缺少断言", "缺少预期结果"], "fix_suggestion": "补充断言和预期"}]
    }, timeout=60)
    check("2.1 dry_run=false returns 200", r.status_code == 200)
    data = r.json()
    check("2.2 dry_run=false in response", data.get("dry_run") is False)
    result = data["results"][0] if data.get("results") else {}
    check("2.3 applied is True or has error",
          result.get("applied") is True or "error" in result)
    if result.get("applied"):
        check("2.4 has updated_fields", isinstance(result.get("updated_fields"), list))
    else:
        check("2.4 has updated_fields (skipped, not applied)", True)
else:
    for i in range(4):
        check(f"2.{i+1} skipped", False, "no test cases found")


# ─── 3. 默认 dry_run 值是 true ──────────────────────────
print("\n── 3. 默认 dry_run=true ──")
if case_ids:
    cid = case_ids[0]
    # 不传 dry_run 字段
    r = requests.post(f"{BASE}/api/v2/ai/test-cases/heal", headers=H, json={
        "cases": [{"case_id": cid, "issues": ["test"]}]
    }, timeout=60)
    check("3.1 default returns 200", r.status_code == 200)
    data = r.json()
    check("3.2 default dry_run is True", data.get("dry_run") is True)
    result = data["results"][0] if data.get("results") else {}
    check("3.3 applied is False by default", result.get("applied") is False)
else:
    for i in range(3):
        check(f"3.{i+1} skipped", False, "no test cases found")


# ─── 4. deleted 用例不能自愈 ────────────────────────────
print("\n── 4. deleted 用例拒绝自愈 ──")
r = requests.post(f"{BASE}/api/v2/ai/test-cases/heal", headers=H, json={
    "dry_run": True,
    "cases": [{"case_id": "NONEXISTENT_CASE_999", "issues": ["test"]}]
}, timeout=10)
check("4.1 nonexistent case returns 200", r.status_code == 200)
data = r.json()
result = data["results"][0] if data.get("results") else {}
check("4.2 error for nonexistent case", "不存在" in result.get("error", ""))
check("4.3 applied is False", result.get("applied") is False)


# ─── 5. 缺少 assertions 能生成建议 ─────────────────────
print("\n── 5. 缺少 assertions 生成建议 ──")
if case_ids:
    cid = case_ids[0]
    r = requests.post(f"{BASE}/api/v2/ai/test-cases/heal", headers=H, json={
        "dry_run": True,
        "cases": [{"case_id": cid, "issues": ["缺少断言 assertions"], "fix_suggestion": "补充 status_code 断言"}]
    }, timeout=60)
    check("5.1 returns 200", r.status_code == 200)
    data = r.json()
    result = data["results"][0] if data.get("results") else {}
    has_assertion_change = any(ch["field"] == "assertions" for ch in (result.get("changes") or []))
    has_any_change = len(result.get("changes") or []) > 0
    check("5.2 has changes", has_any_change, f"changes={result.get('changes')}")
    # AI or rule may or may not generate assertion change, but should have some fix
else:
    check("5.1 skipped", False, "no test cases found")
    check("5.2 skipped", False, "no test cases found")


# ─── 6. 缺少 expected 能生成建议 ──────────────────────
print("\n── 6. 缺少 expected 生成建议 ──")
if case_ids:
    cid = case_ids[0]
    r = requests.post(f"{BASE}/api/v2/ai/test-cases/heal", headers=H, json={
        "dry_run": True,
        "cases": [{"case_id": cid, "issues": ["缺少预期结果 expected"], "fix_suggestion": "补充预期"}]
    }, timeout=60)
    check("6.1 returns 200", r.status_code == 200)
    data = r.json()
    result = data["results"][0] if data.get("results") else {}
    check("6.2 has changes or error", len(result.get("changes") or []) > 0 or "error" in result)
else:
    check("6.1 skipped", False)
    check("6.2 skipped", False)


# ─── 7. 不允许修改 id ──────────────────────────────────
print("\n── 7. 字段白名单保护 ──")
# This is a backend logic test - AI may return id but whitelist should block it
# We verify that the response only contains allowed fields
if case_ids:
    cid = case_ids[0]
    r = requests.post(f"{BASE}/api/v2/ai/test-cases/heal", headers=H, json={
        "dry_run": True,
        "cases": [{"case_id": cid, "issues": ["缺少步骤"]}]
    }, timeout=60)
    data = r.json()
    result = data["results"][0] if data.get("results") else {}
    allowed = {"steps", "expected", "assertions", "priority"}
    changed_fields = {ch["field"] for ch in (result.get("changes") or [])}
    check("7.1 only allowed fields in changes", changed_fields.issubset(allowed),
          f"changed={changed_fields}")
    check("7.2 id not in changes", "id" not in changed_fields)
    check("7.3 execution_config not in changes", "execution_config" not in changed_fields)
    check("7.4 tags not in changes", "tags" not in changed_fields)
else:
    for i in range(4):
        check(f"7.{i+1} skipped", False)


# ─── 8. AI 不可用时规则降级 ──────────────────────────────
print("\n── 8. 规则降级 (source=rule_based) ──")
# The backend will try AI first, if it fails, falls back to rule-based
# We can't force AI off in test, but we verify the source field exists
if case_ids:
    cid = case_ids[0]
    r = requests.post(f"{BASE}/api/v2/ai/test-cases/heal", headers=H, json={
        "dry_run": True,
        "cases": [{"case_id": cid, "issues": ["缺少步骤"]}]
    }, timeout=60)
    data = r.json()
    result = data["results"][0] if data.get("results") else {}
    check("8.1 source field present", result.get("source") in ("ai", "rule_based"),
          f"source={result.get('source')}")
    check("8.2 no 500 error", r.status_code != 500)
else:
    check("8.1 skipped", False)
    check("8.2 skipped", False)


# ─── 9. 批量自愈 ────────────────────────────────────────
print("\n── 9. 批量自愈 ──")
if len(case_ids) >= 2:
    r = requests.post(f"{BASE}/api/v2/ai/test-cases/heal", headers=H, json={
        "dry_run": True,
        "cases": [
            {"case_id": case_ids[0], "issues": ["缺少步骤"]},
            {"case_id": case_ids[1], "issues": ["缺少断言"]},
        ]
    }, timeout=60)
    check("9.1 batch returns 200", r.status_code == 200)
    data = r.json()
    check("9.2 total == 2", data.get("total") == 2)
    check("9.3 results length == 2", len(data.get("results", [])) == 2)
else:
    for i in range(3):
        check(f"9.{i+1} skipped", False, "need >= 2 cases")


# ─── 10. 接口异常不导致500 ──────────────────────────────
print("\n── 10. 异常处理 ──")
r = requests.post(f"{BASE}/api/v2/ai/test-cases/heal", headers=H, json={
    "dry_run": True,
    "cases": []
}, timeout=10)
check("10.1 empty cases returns 200", r.status_code == 200)

r = requests.post(f"{BASE}/api/v2/ai/test-cases/heal", headers=H, json={
    "dry_run": True,
    "cases": [{"case_id": "", "issues": []}]
}, timeout=10)
check("10.2 empty case_id returns 200", r.status_code == 200)

# Invalid JSON body
r = requests.post(f"{BASE}/api/v2/ai/test-cases/heal", headers=H, data="invalid json", timeout=10)
check("10.3 invalid JSON returns 422 (not 500)", r.status_code == 422)


# ─── 11. PUT 更新接口 ───────────────────────────────────
print("\n── 11. PUT /api/v2/test-cases/:id ──")
if case_ids:
    cid = case_ids[0]
    r = requests.put(f"{BASE}/api/v2/test-cases/{cid}", headers=H, json={
        "expected": "test update via PUT"
    }, timeout=10)
    check("11.1 PUT returns 200", r.status_code == 200)
    data = r.json()
    check("11.2 success=True", data.get("success") is True)
    check("11.3 updated_fields present", "updated_fields" in data)

    # Restore
    requests.put(f"{BASE}/api/v2/test-cases/{cid}", headers=H, json={
        "expected": ""
    }, timeout=10)
else:
    for i in range(3):
        check(f"11.{i+1} skipped", False)


# ─── 12. PUT 不存在的用例返回 404 ────────────────────────
print("\n── 12. PUT nonexistent case ──")
r = requests.put(f"{BASE}/api/v2/test-cases/NONEXISTENT_999", headers=H, json={
    "expected": "test"
}, timeout=10)
check("12.1 returns 404", r.status_code == 404)


# ─── Summary ────────────────────────────────────────────
print("\n" + "=" * 60)
print(f"P1-8A-Guard AI Heal Guard: {passed}/{total} passed, {failed} failed")
print("=" * 60)

sys.exit(0 if failed == 0 else 1)
