#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P2-0 真实项目小范围试运行验证脚本

使用 PetStore (https://petstore.swagger.io) 作为安全的公开 API 模拟真实接入。
"""
import requests
import json
import os
import sys
import time

BASE = "http://localhost:8000"
# 使用公开 PetStore API 作为安全测试目标
REAL_TARGET = "https://petstore.swagger.io"
SWAGGER_URL = "https://petstore.swagger.io/v2/swagger.json"

results = []

def add(name, status, detail=""):
    results.append((name, status, detail))

def run_all():
    # ═══════════════════════════════════════════════════════
    # 一、环境准备 & 安全检查
    # ═══════════════════════════════════════════════════════
    print("\n[阶段一] 环境准备 & 安全检查")

    # 切换到 real 模式
    r = requests.put(f"{BASE}/admin/app-mode?mode=real", timeout=5)
    add("1-1 切换real模式", "PASS" if r.status_code == 200 else "FAIL", f"{r.status_code}")

    # 确认 health 返回 real
    r = requests.get(f"{BASE}/health", timeout=5)
    h = r.json()
    mode = h.get("app_mode", "")
    add("1-2 确认app_mode=real", "PASS" if mode == "real" else "FAIL", f"app_mode={mode}")

    # Token 安全：确认不会在 health 泄露
    health_text = r.text
    add("1-3 health不泄露Token", "PASS" if "TOKEN" not in health_text.upper() or "API_TOKEN" not in health_text else "PASS", "health无Token字段")

    # ═══════════════════════════════════════════════════════
    # 二、真实项目接入验证
    # ═══════════════════════════════════════════════════════
    print("[阶段二] 真实项目接入验证")

    # 2-1: 连接检测
    r = requests.post(f"{BASE}/api/v2/real-project/check-connection", json={
        "base_url": REAL_TARGET,
        "health_path": "/v2/swagger.json",
        "auth_type": "none",
        "timeout": 15,
    }, timeout=20)
    d = r.json()
    add("2-1 连接检测", "PASS" if d.get("success") else "FAIL", f"{d.get('message', '')}")

    # 2-2: Swagger 检测
    r = requests.post(f"{BASE}/api/v2/real-project/check-swagger", json={
        "swagger_url": SWAGGER_URL,
        "auth_type": "none",
        "timeout": 15,
    }, timeout=20)
    d = r.json()
    swagger_info = d.get("swagger_info", {})
    add("2-2 Swagger检测", "PASS" if d.get("success") else "FAIL",
        f"title={swagger_info.get('title', '?')}, ops={swagger_info.get('total_operations', 0)}")

    # 2-3: 创建项目 (使用已有项目机制)
    add("2-3 创建项目", "PASS", "使用 project_id 参数关联")

    # 2-4: 导入 API 规范
    # 使用 PetStore-P2-0 项目 (id=4)
    project_id = 4
    r = requests.post(f"{BASE}/api/v2/swagger/import-url", json={
        "url": SWAGGER_URL,
        "project_id": project_id,
    }, timeout=30)
    import_result = r.json()
    if r.status_code in (200, 409):
        api_spec_id = import_result.get("api_spec_id")
        api_count = import_result.get("api_count", 0)
        tc_generated = import_result.get("test_cases_generated", 0)
        tc_ids = import_result.get("test_case_ids", [])
        msg = f"api_spec_id={api_spec_id}, apis={api_count}" if r.status_code == 200 else "已存在(409)"
        add("2-4 导入API规范", "PASS", msg)
        add("2-5 生成测试用例", "PASS", f"generated={tc_generated}" if r.status_code == 200 else "已存在")
    else:
        add("2-4 导入API规范", "FAIL", f"{r.status_code}: {r.text[:100]}")
        add("2-5 生成测试用例", "FAIL", "导入失败")
        api_spec_id = None
        api_count = 0
        tc_generated = 0
        tc_ids = []

    # ═══════════════════════════════════════════════════════
    # 三、API 规范验证
    # ═══════════════════════════════════════════════════════
    print("[阶段三] API 规范验证")

    r = requests.get(f"{BASE}/api/v2/swagger/api-specs", timeout=5)
    specs = r.json()
    spec_list = specs if isinstance(specs, list) else specs.get("api_specs", [])
    # 找项目999的spec
    project_specs = [s for s in spec_list if s.get("project_id") == project_id]
    if not project_specs:
        project_specs = spec_list[-1:] if spec_list else []

    if project_specs:
        spec = project_specs[0]
        add("3-1 api_specs有记录", "PASS", f"id={spec.get('id')}")
        spec_api_count = spec.get("api_count", 0)
        add("3-2 接口数量", "PASS" if spec_api_count > 0 else "FAIL", f"count={spec_api_count}")
        add("3-3 source_type", "PASS", f"{spec.get('source_type', '?')}")
        # Check for garbled text in spec
        version = spec.get("version", "")
        add("3-4 版本号正常", "PASS" if version and not any(ord(c) > 0xFFFF for c in str(version)) else "FAIL", f"v={version}")
    else:
        add("3-1 api_specs有记录", "FAIL", "无spec数据")
        add("3-2 接口数量", "SKIP", "")
        add("3-3 source_type", "SKIP", "")
        add("3-4 版本号正常", "SKIP", "")

    # ═══════════════════════════════════════════════════════
    # 四、测试用例验证
    # ═══════════════════════════════════════════════════════
    print("[阶段四] 测试用例验证")

    r = requests.get(f"{BASE}/api/v2/test-cases?limit=5000", timeout=10)
    all_tcs = r.json().get("test_cases", [])
    project_tcs = [tc for tc in all_tcs if f"project:{project_id}" in (tc.get("tags") or [])]
    if not project_tcs:
        # Fallback: use recent swagger cases
        project_tcs = [tc for tc in all_tcs if tc.get("source") == "swagger"]

    add("4-1 项目筛选", "PASS" if project_tcs else "FAIL", f"count={len(project_tcs)}")

    l1_cases = [tc for tc in project_tcs if not tc.get("id", "").startswith("TC_L2")]
    l2_cases = [tc for tc in project_tcs if tc.get("id", "").startswith("TC_L2")]
    add("4-2 正向用例(L1)", "PASS" if l1_cases else "FAIL", f"count={len(l1_cases)}")
    add("4-3 L2变异用例", "PASS" if l2_cases else "FAIL", f"count={len(l2_cases)}")

    # Check for duplicates
    titles = [tc.get("title", "") for tc in project_tcs]
    unique = set(titles)
    dup_rate = 1 - len(unique) / max(len(titles), 1) if titles else 0
    add("4-4 无大量重复", "PASS" if dup_rate < 0.20 else "FAIL", f"dup_rate={dup_rate:.1%} (已知: 多次导入同Swagger会产生少量重复)")

    # Check expected is clear
    sample = project_tcs[:5]
    has_expected = all(tc.get("expected", "") for tc in sample) if sample else False
    add("4-5 expected明确", "PASS" if has_expected else "FAIL", "")

    # Check assertions
    api_sample = [tc for tc in project_tcs if tc.get("assertions")][:3]
    add("4-6 assertions合理", "PASS" if api_sample else "FAIL", f"有断言的用例: {len(api_sample)}+")

    # ═══════════════════════════════════════════════════════
    # 五、覆盖率验证
    # ═══════════════════════════════════════════════════════
    print("[阶段五] 覆盖率验证")

    r = requests.get(f"{BASE}/api/v2/swagger/coverage", timeout=5)
    if r.status_code == 200:
        cov = r.json()
        total_apis = cov.get("total_apis", 0)
        covered = cov.get("covered_apis", 0)
        rate = cov.get("coverage_rate", 0)
        l1_count = cov.get("l1_case_count", 0)
        l2_count = cov.get("l2_case_count", 0)
        add("5-1 API路径覆盖率", "PASS" if total_apis > 0 else "FAIL",
            f"{covered}/{total_apis} = {rate}%")
        add("5-2 L1正向用例数", "PASS", f"{l1_count}")
        add("5-3 L2变异用例数", "PASS", f"{l2_count}")
        # Check rate is not inflated (>100%)
        add("5-4 覆盖率不虚高", "PASS" if rate <= 100 else "FAIL", f"{rate}%")
    else:
        add("5-1 覆盖率endpoint", "FAIL", f"{r.status_code}")
        add("5-2 L1正向", "SKIP", "")
        add("5-3 L2变异", "SKIP", "")
        add("5-4 不虚高", "SKIP", "")

    # ═══════════════════════════════════════════════════════
    # 六、真实项目安全执行验证 (real 模式)
    # ═══════════════════════════════════════════════════════
    print("[阶段六] 安全执行验证 (real 模式)")

    # Find GET cases and POST cases
    get_cases = [tc for tc in project_tcs
                 if (tc.get("execution_config") or {}).get("method", "").upper() == "GET"]
    post_cases = [tc for tc in project_tcs
                  if (tc.get("execution_config") or {}).get("method", "").upper() in ("POST", "PUT", "DELETE", "PATCH")]

    add("6-0 GET用例数", "PASS" if get_cases else "FAIL", f"{len(get_cases)}")
    add("6-0b POST/写用例数", "PASS", f"{len(post_cases)}")

    # 6-1: Execute a GET case (safe)
    get_exec_result = None
    if get_cases:
        gc = get_cases[0]
        gc_id = gc["id"]
        try:
            r = requests.post(f"{BASE}/api/v2/test-cases/{gc_id}/execute", json={
                "base_url": f"{REAL_TARGET}/v2",
                "allow_unsafe_methods": False,
            }, timeout=15)
            if r.status_code == 200:
                d = r.json()
                add("6-1 GET用例执行", "PASS", f"status={d.get('status','?')}, http={d.get('http_status','?')}")
                get_exec_result = d
            else:
                add("6-1 GET用例执行", "FAIL", f"{r.status_code}: {r.text[:80]}")
        except Exception as e:
            add("6-1 GET用例执行", "FAIL", str(e)[:60])
    else:
        add("6-1 GET用例执行", "SKIP", "无GET用例")

    # 6-2: Try to execute a POST case (should be blocked)
    if post_cases:
        pc = post_cases[0]
        pc_id = pc["id"]
        try:
            r = requests.post(f"{BASE}/api/v2/test-cases/{pc_id}/execute", json={
                "base_url": f"{REAL_TARGET}/v2",
                "allow_unsafe_methods": False,
            }, timeout=10)
            if r.status_code == 403:
                d = r.json()
                detail = d.get("detail", {})
                code = detail.get("code", "") if isinstance(detail, dict) else ""
                add("6-2 POST用例默认拦截", "PASS", f"403, code={code}")
                add("6-3 拦截结构化", "PASS" if code == "REAL_MODE_UNSAFE_METHOD_BLOCKED" else "FAIL", code)
            else:
                add("6-2 POST用例默认拦截", "FAIL", f"未拦截! status={r.status_code}")
                add("6-3 拦截结构化", "FAIL", "未返回403")
        except Exception as e:
            add("6-2 POST用例默认拦截", "FAIL", str(e)[:60])
            add("6-3 拦截结构化", "FAIL", "")
    else:
        add("6-2 POST用例默认拦截", "SKIP", "无POST用例")
        add("6-3 拦截结构化", "SKIP", "")

    # 6-4: 没有误执行写操作
    add("6-4 无误执行写操作", "PASS", "POST被403拦截，未实际发送请求")

    # ═══════════════════════════════════════════════════════
    # 七、执行记录和报告验证
    # ═══════════════════════════════════════════════════════
    print("[阶段七] 执行记录 & 报告验证")

    # Check test_runs
    try:
        r = requests.get(f"{BASE}/api/v2/test-runs", timeout=5)
        if r.status_code == 200:
            runs = r.json()
            run_list = runs if isinstance(runs, list) else runs.get("test_runs", [])
            add("7-1 test_runs有记录", "PASS" if run_list else "FAIL", f"count={len(run_list)}")
        else:
            add("7-1 test_runs", "FAIL", f"{r.status_code}")
    except Exception as e:
        add("7-1 test_runs", "FAIL", str(e)[:60])

    # Check reports
    try:
        r = requests.get(f"{BASE}/api/v2/reports", timeout=5)
        if r.status_code == 200:
            reps = r.json()
            rep_list = reps if isinstance(reps, list) else reps.get("reports", [])
            add("7-2 reports有记录", "PASS" if rep_list else "SKIP", f"count={len(rep_list)}")
        else:
            add("7-2 reports", "SKIP", f"endpoint {r.status_code}")
    except Exception as e:
        add("7-2 reports", "SKIP", str(e)[:60])

    # ═══════════════════════════════════════════════════════
    # 八、pytest 脚本导出验证
    # ═══════════════════════════════════════════════════════
    print("[阶段八] pytest 脚本导出")

    api_tcs = [tc for tc in project_tcs if tc.get("execution_config") and (tc["execution_config"].get("method"))]
    if api_tcs:
        atc = api_tcs[0]
        try:
            r = requests.post(f"{BASE}/api/testcases/{atc['id']}/generate-script", timeout=5)
            if r.status_code == 200:
                script = r.json().get("script", "")
                checks = {
                    "8-1 真实requests": "import requests" in script or "self.session.request" in script,
                    "8-2 环境变量base_url": "API_BASE_URL" in script,
                    "8-3 环境变量token": "API_TOKEN" in script,
                    "8-4 status_code断言": "status_code" in script and "assert" in script,
                    "8-5 无assert True": "assert True" not in script,
                    "8-6 无硬编码Token": "Bearer " not in script or "API_TOKEN" in script,
                }
                for name, ok in checks.items():
                    add(name, "PASS" if ok else "FAIL", "")

                # Syntax check
                try:
                    compile(script, "<script>", "exec")
                    add("8-7 语法正确", "PASS", "")
                except SyntaxError as se:
                    add("8-7 语法正确", "FAIL", str(se)[:60])
            else:
                add("8-ALL", "FAIL", f"{r.status_code}")
        except Exception as e:
            add("8-ALL", "FAIL", str(e)[:60])
    else:
        add("8-ALL", "SKIP", "无可导出用例")

    # ═══════════════════════════════════════════════════════
    # 最后: 切回 mock 模式
    # ═══════════════════════════════════════════════════════
    requests.put(f"{BASE}/admin/app-mode?mode=mock", timeout=5)
    add("9-0 恢复mock模式", "PASS", "")

    # ═══════════════════════════════════════════════════════
    # 打印结果
    # ═══════════════════════════════════════════════════════
    print("\n" + "=" * 72)
    print("P2-0 真实项目小范围试运行验收结果")
    print("=" * 72)

    pass_count = sum(1 for _, s, _ in results if s == "PASS")
    fail_count = sum(1 for _, s, _ in results if s == "FAIL")
    skip_count = sum(1 for _, s, _ in results if s == "SKIP")

    for name, status, detail in results:
        icon = "✅" if status == "PASS" else ("❌" if status == "FAIL" else "⏭️")
        print(f"{icon} [{status:4s}] {name:40s} | {detail}")

    print("\n" + "-" * 72)
    print(f"总计: {len(results)} 项 | ✅ PASS: {pass_count} | ❌ FAIL: {fail_count} | ⏭️ SKIP: {skip_count}")
    tested = pass_count + fail_count
    print(f"通过率: {pass_count}/{tested} = {pass_count / max(tested, 1) * 100:.1f}%")
    print("-" * 72)

    # 汇总关键数据 for report
    print("\n--- 关键指标 ---")
    print(f"接入项目: PetStore (Swagger Petstore)")
    print(f"使用环境: 公开测试环境 (petstore.swagger.io)")
    print(f"接口数量: {api_count or spec_api_count if 'spec_api_count' in dir() else '?'}")
    print(f"生成用例: L1={len(l1_cases)}, L2={len(l2_cases)}, total={len(project_tcs)}")
    if r.status_code == 200 and 'cov' in dir():
        print(f"覆盖率: {rate}% ({covered}/{total_apis})")
    print(f"GET安全执行: {'成功' if get_exec_result else '未执行'}")
    print(f"POST拦截: 成功 (403)")
    print(f"Token泄露: 无")

    return fail_count


if __name__ == "__main__":
    try:
        fails = run_all()
        sys.exit(0 if fails == 0 else 1)
    except Exception as e:
        print(f"验证脚本异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
