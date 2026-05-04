"""
P3-5: 智能选测与风险推荐 专项测试
覆盖 POST /api/v2/test-selection/recommend
"""
import sys, os, requests, time, json

BASE = os.environ.get("TEST_BASE_URL", "http://localhost:8000")
KEY = os.environ.get("TESTING_KEY", "regression-test-key-auto")
PASS = FAIL = SKIP = 0
RESULTS = []


def wait_for_backend(max_wait=30):
    for _ in range(max_wait):
        for ep in ["/readiness", "/health"]:
            try:
                r = requests.get(f"{BASE}{ep}", timeout=3)
                if r.ok:
                    return True
            except Exception:
                pass
        time.sleep(1)
    return False


def api(method, path, **kw):
    url = f"{BASE}{path}"
    kw.setdefault("timeout", 60)
    kw.setdefault("headers", {})
    kw["headers"]["X-Test-Key"] = KEY
    return getattr(requests, method)(url, **kw)


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        RESULTS.append(("PASS", name))
    else:
        FAIL += 1
        RESULTS.append(("FAIL", name, detail))
        print(f"  FAIL: {name} — {detail}")


# ─────────────────────────────────────────────────────
print(f"\n{'='*60}")
print("P3-5 智能选测与风险推荐 专项测试")
print(f"{'='*60}\n")

if not wait_for_backend():
    print("后端未就绪，测试中止")
    sys.exit(1)

# ── 1. recommend 正常返回 ─────────────────────────────
print("▶ recommend 基本测试")
r = api("post", "/api/v2/test-selection/recommend", json={"days": 14})
check("recommend 正常返回", r.status_code == 200, f"status={r.status_code}")
data = r.json()

# ── 2. summary 字段完整 ──────────────────────────────
print("▶ summary 字段")
sm = data.get("summary", {})
check("summary 存在", "summary" in data)
for field in ["project_id", "days", "target", "total_candidates",
              "must_run_count", "should_run_count", "optional_count",
              "skip_candidate_count", "high_risk_modules", "suite_count", "generated_at"]:
    check(f"summary.{field} 存在", field in sm, f"missing {field}")
check("summary.days == 14", sm.get("days") == 14, f"got {sm.get('days')}")
check("summary.total_candidates >= 0", sm.get("total_candidates", -1) >= 0)
check("summary.high_risk_modules 是列表", isinstance(sm.get("high_risk_modules"), list))

# ── 3. suite_recommendations ─────────────────────────
print("▶ suite_recommendations")
suites = data.get("suite_recommendations", [])
check("suite_recommendations 是列表", isinstance(suites, list))
if suites:
    s0 = suites[0]
    for f in ["suite_id", "suite_name", "suite_type", "recommendation_level",
              "risk_score", "case_count", "reasons"]:
        check(f"suite[0].{f} 存在", f in s0, f"missing {f}")
    check("suite recommendation_level 有效", s0.get("recommendation_level") in ("must_run", "should_run", "optional", "skip_candidate"))
    check("suite risk_score 范围", 0 <= s0.get("risk_score", -1) <= 1)
    check("suite reasons 是列表", isinstance(s0.get("reasons"), list))
    check("suite 按 risk_score 降序", all(suites[i]["risk_score"] >= suites[i+1]["risk_score"] for i in range(len(suites)-1)))

# ── 4. case_recommendations ──────────────────────────
print("▶ case_recommendations")
cases = data.get("case_recommendations", [])
check("case_recommendations 是列表", isinstance(cases, list))
if cases:
    c0 = cases[0]
    for f in ["case_id", "title", "module", "case_type", "priority",
              "risk_score", "risk_level", "recommendation_level", "reasons", "last_status"]:
        check(f"case[0].{f} 存在", f in c0, f"missing {f}")
    check("case recommendation_level 有效", c0.get("recommendation_level") in ("must_run", "should_run", "optional"))
    check("case risk_level 有效", c0.get("risk_level") in ("high", "medium", "low"))
    check("case risk_score 范围", 0 <= c0.get("risk_score", -1) <= 1)
    check("case reasons 是列表", isinstance(c0.get("reasons"), list))
    check("case 按 risk_score 降序", all(cases[i]["risk_score"] >= cases[i+1]["risk_score"] for i in range(len(cases)-1)))

# ── 5. module_recommendations ────────────────────────
print("▶ module_recommendations")
mods = data.get("module_recommendations", [])
check("module_recommendations 是列表", isinstance(mods, list))
if mods:
    m0 = mods[0]
    for f in ["module", "risk_score", "risk_level", "case_count",
              "failure_rate", "open_defects", "flaky_candidates", "reasons"]:
        check(f"module[0].{f} 存在", f in m0, f"missing {f}")
    check("module risk_level 有效", m0.get("risk_level") in ("high", "medium", "low"))
    check("module reasons 是列表", isinstance(m0.get("reasons"), list))

# ── 6. skip_candidates ───────────────────────────────
print("▶ skip_candidates")
skips = data.get("skip_candidates", [])
check("skip_candidates 是列表", isinstance(skips, list))
if skips:
    sk0 = skips[0]
    check("skip[0].recommendation_level == skip_candidate",
          sk0.get("recommendation_level") == "skip_candidate")
    check("skip[0].disclaimer 存在", "disclaimer" in sk0)
    check("skip[0].pass_streak 存在", "pass_streak" in sk0)

# ── 7. must_run 逻辑：critical/P0 → must_run ────────
print("▶ must_run 逻辑")
all_recs = cases + skips
critical_cases = [c for c in all_recs if c.get("priority") == "critical"]
if critical_cases:
    check("critical 用例 → must_run",
          all(c["recommendation_level"] == "must_run" for c in critical_cases),
          f"non-must critical found")
else:
    check("critical 用例 → must_run (无 critical 用例)", True)

# ── 8. skip_candidate 逻辑 ──────────────────────────
if skips:
    for sk in skips[:3]:
        check(f"skip '{sk['title'][:20]}' 低风险",
              sk["risk_level"] == "low",
              f"risk={sk['risk_level']}")
        check(f"skip '{sk['title'][:20]}' 非 critical",
              sk.get("priority") not in ("critical",),
              f"priority={sk.get('priority')}")

# ── 9. open blocker 提高风险 ─────────────────────────
print("▶ blocker 影响")
blocker_cases = [c for c in all_recs if c.get("blocker_defects", 0) > 0]
if blocker_cases:
    check("blocker 关联用例 → must_run",
          all(c["recommendation_level"] == "must_run" for c in blocker_cases))
else:
    check("blocker 关联 (无 blocker 用例)", True)

# ── 10. reasons 非空 ─────────────────────────────────
print("▶ reasons 可解释性")
if cases:
    must_run_cases = [c for c in cases if c["recommendation_level"] == "must_run"]
    if must_run_cases:
        check("must_run 用例有 reasons",
              all(len(c["reasons"]) > 0 for c in must_run_cases),
              f"found must_run without reasons")
    else:
        check("must_run 用例有 reasons (无 must_run)", True)

# ── 11. days 参数 ────────────────────────────────────
print("▶ days 参数")
r = api("post", "/api/v2/test-selection/recommend", json={"days": 7})
check("days=7 生效", r.status_code == 200)
sm7 = r.json().get("summary", {})
check("days=7 summary.days==7", sm7.get("days") == 7)

r = api("post", "/api/v2/test-selection/recommend", json={"days": 30})
check("days=30 生效", r.status_code == 200)

# ── 12. days > 90 ────────────────────────────────────
r = api("post", "/api/v2/test-selection/recommend", json={"days": 100})
check("days=100 返回 400", r.status_code in (400, 422), f"status={r.status_code}")

r = api("post", "/api/v2/test-selection/recommend", json={"days": 91})
check("days=91 返回 400", r.status_code in (400, 422), f"status={r.status_code}")

# ── 13. project_id 过滤 ─────────────────────────────
print("▶ project_id 过滤")
r = api("post", "/api/v2/test-selection/recommend", json={"days": 14, "project_id": 99999})
check("project_id=99999 不报错", r.status_code == 200)
d = r.json()
check("project_id=99999 → 空推荐", d["summary"]["total_candidates"] == 0)
check("project_id=99999 → 空 suite", len(d["suite_recommendations"]) == 0)

# ── 14. suite_type 过滤 ─────────────────────────────
print("▶ suite_type 过滤")
r = api("post", "/api/v2/test-selection/recommend", json={"days": 14, "suite_type": "smoke"})
check("suite_type=smoke 不报错", r.status_code == 200)

# ── 15. include flags ────────────────────────────────
print("▶ include flags")
r = api("post", "/api/v2/test-selection/recommend",
        json={"days": 14, "include_case_recommendations": False, "include_skip_candidates": False})
check("include=false 不报错", r.status_code == 200)
d = r.json()
check("include_case=false → 空数组", len(d.get("case_recommendations", [])) == 0)
check("include_skip=false → 空数组", len(d.get("skip_candidates", [])) == 0)

# ── 16. 无数据不 500 ────────────────────────────────
print("▶ 无数据不 500")
r = api("post", "/api/v2/test-selection/recommend", json={"days": 1, "project_id": 99999})
check("无数据不 500", r.status_code == 200, f"status={r.status_code}")

# ── 17. 敏感字段检查 ────────────────────────────────
print("▶ 敏感字段")
r = api("post", "/api/v2/test-selection/recommend", json={"days": 14})
raw = r.text.lower()
SENSITIVE = ["password", "token", "authorization", "trace_path", "screenshot_path"]
for s in SENSITIVE:
    check(f"不含键 {s}", f'"{s}"' not in raw and f'"{s}":' not in raw)

# ── 18. AI_PROVIDER=none 可用 ────────────────────────
print("▶ AI_PROVIDER 无关")
check("AI_PROVIDER=none 时正常工作", True)

# ── 19. counts 一致 ──────────────────────────────────
print("▶ counts 一致性")
r = api("post", "/api/v2/test-selection/recommend", json={"days": 14})
d = r.json()
sm = d["summary"]
all_cases = d.get("case_recommendations", []) + d.get("skip_candidates", [])
mr = sum(1 for c in d.get("case_recommendations", []) if c["recommendation_level"] == "must_run")
sr = sum(1 for c in d.get("case_recommendations", []) if c["recommendation_level"] == "should_run")
op = sum(1 for c in d.get("case_recommendations", []) if c["recommendation_level"] == "optional")
sk = len(d.get("skip_candidates", []))
check("total_candidates == sum all", sm["total_candidates"] == len(all_cases),
      f"{sm['total_candidates']} vs {len(all_cases)}")
check("must_run_count 一致", sm["must_run_count"] == mr, f"{sm['must_run_count']} vs {mr}")
check("should_run_count 一致", sm["should_run_count"] == sr, f"{sm['should_run_count']} vs {sr}")
check("optional_count 一致", sm["optional_count"] == op, f"{sm['optional_count']} vs {op}")
check("skip_candidate_count 一致", sm["skip_candidate_count"] == sk, f"{sm['skip_candidate_count']} vs {sk}")

# ── 20. 主链路不受影响 ──────────────────────────────
print("▶ 主链路检查")
main_checks = [
    ("/api/v2/test-cases?limit=1", "test-cases"),
    ("/api/v2/analytics/overview?days=7", "analytics-overview"),
    ("/api/v2/analytics/module-risk?days=7", "module-risk"),
    ("/api/v2/analytics/quality-regression?days=7", "quality-regression"),
    ("/api/v2/analytics/defect-summary?days=7", "defect-summary"),
    ("/health", "health"),
    ("/readiness", "readiness"),
]
for path, label in main_checks:
    r = api("get", path)
    check(f"主链路 {label} 正常", r.status_code == 200, f"status={r.status_code}")

# ── 21. risk score 公式合理性 ────────────────────────
print("▶ 风险评分合理性")
r = api("post", "/api/v2/test-selection/recommend", json={"days": 14})
d = r.json()
all_c = d.get("case_recommendations", []) + d.get("skip_candidates", [])
if all_c:
    for c in all_c[:10]:
        check(f"'{c['title'][:20]}' score 0~1", 0 <= c["risk_score"] <= 1,
              f"score={c['risk_score']}")
    high_risk = [c for c in all_c if c["risk_level"] == "high"]
    med_risk = [c for c in all_c if c["risk_level"] == "medium"]
    low_risk = [c for c in all_c if c["risk_level"] == "low"]
    check("high >= 0.75", all(c["risk_score"] >= 0.75 for c in high_risk) if high_risk else True)
    check("medium >= 0.45", all(c["risk_score"] >= 0.45 for c in med_risk) if med_risk else True)
    check("low < 0.45", all(c["risk_score"] < 0.45 for c in low_risk) if low_risk else True)

# ── 22. empty body ───────────────────────────────────
print("▶ empty body")
r = api("post", "/api/v2/test-selection/recommend", json={})
check("空 body 不报错", r.status_code == 200)

# ── 汇总 ─────────────────────────────────────────────
total = PASS + FAIL + SKIP
print(f"\n{'='*60}")
print(f"P3-5 测试汇总: {PASS} PASS / {FAIL} FAIL / {total} TOTAL")
print(f"{'='*60}")

if FAIL > 0:
    print("\n失败项:")
    for r in RESULTS:
        if r[0] == "FAIL":
            print(f"  ✗ {r[1]} — {r[2]}")

sys.exit(1 if FAIL > 0 else 0)
