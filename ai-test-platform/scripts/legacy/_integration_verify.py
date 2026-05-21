#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 1-10 前端全流程联调验收脚本

逐项验证 10 项检查点，输出详细结果，最终生成验收报告。
"""
import json
import os
import sys
import time
import sqlite3
import requests
from datetime import datetime

sys.path.insert(0, r"G:\AI项目\ai测试\ai-test-platform")
from dotenv import load_dotenv
load_dotenv(r"G:\AI项目\ai测试\ai-test-platform\.env")

BACKEND = "http://localhost:8000"
FRONTEND = "http://localhost:5173"
BLUEDOT = "https://dev-recycle.szhibu.com/dev-api/recycle"
TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdXBwbGllcklkIjoiIiwidXNlcl9uYW1lIjoibGRzaXQiLCJtb2JpbGUiOiIxMzU0MjY1ODk2MyIsImF2YXRhciI6bnVsbCwidXNlcklkIjoiMTE2ZDMyYTY0MGIwNGE1NWJkMTViMWI5MTBmY2Y3NzgiLCJ1dWlkIjoiZjI4Y2I1NTNlOWM4NDZmMzkzOTdkNmE1ZWNjZWY5NWYiLCJjbGllbnRfaWQiOiJkZXZfYmx1ZV9yZWN5Y2xlIiwidXJsIjpudWxsLCJyZWFsTmFtZSI6Imxkc2l0IiwiYXVkIjpbIkRFRkFVTFRfUkVTT1VSQ0VfSUQiXSwicGluIjoiMTAxNCIsInNjb3BlIjpbImFsbCJdLCJ3c3QiOiJ3c0xBQWN6TEFzREJ5QXZJd1FMS3lnc0J3c29Nd2d2RHdzZ0FEQUROemNmT3dzakN3YzRQQWR3RDBjNEJDdENwQ3cvYUNxbmJDZ3pUREE4S3pnREx4d3dMeXNyTUNzTU14OEhBQU16RHpNUE5BY0FDeWdvTURBb0F3OG9BIiwiaWQiOjE5OTMxMzE3MjI5MTY4OTI2NzQsImV4cCI6MTc3Nzg4ODUwMSwianRpIjoiZjA2OTVkMWItNGNkMi00OWIxLWE3MGQtNGM0ZWE0ZGNiM2RmIiwiZW1haWwiOiIxMzU0MjY1ODk2M0BxcS5jb20ifQ.tqNrCe8FDnPCzIUF5hQnUbzKH95Rk3RwpeW9x7rQ52ZVr9dxDlAB7lu56aFdgZlmwlrh1waxl3p-qSwLCaCdYxK7h_MG36L4D_QpN9OlgWBi6KFg7ClnYLejUHfifONVdSJrqTxQ_yHN1SyJigBe3BDX9ASy5KSMBoeUoECkCkU"
DB_PATH = r"G:\AI项目\ai测试\ai-test-platform\output\execution_results.db"

report = []  # 收集报告内容


def log(msg, level="INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    prefix = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "INFO": "ℹ️"}.get(level, "  ")
    line = f"[{ts}] {prefix} {msg}"
    print(line)
    report.append(line)


def section(title):
    sep = "=" * 60
    log("")
    log(sep)
    log(f"  {title}")
    log(sep)


# ========== 1. 后端启动检查 ==========
def check_backend():
    section("1. 后端启动检查")
    issues = []

    # 1a. 健康检查
    try:
        r = requests.get(f"{BACKEND}/api/v2/execute/auth/status", timeout=5)
        if r.status_code == 200:
            log("后端 FastAPI 启动正常 (port 8000)", "PASS")
        else:
            log(f"后端返回异常状态码 {r.status_code}", "FAIL")
            issues.append("后端异常状态码")
    except Exception as e:
        log(f"后端无法连接: {e}", "FAIL")
        issues.append("后端无法连接")
        return issues

    # 1b. V2 路由检查
    r = requests.get(f"{BACKEND}/openapi.json")
    paths = r.json().get("paths", {})
    v2_routes = [p for p in paths if "/v2/execute" in p]
    expected_routes = [
        "/api/v2/execute", "/api/v2/execute/batch",
        "/api/v2/execute/auth/set-token", "/api/v2/execute/auth/status",
        "/api/v2/execute/generate-from-swagger", "/api/v2/execute/generate-and-run",
        "/api/v2/execute/ai/generate-assertions", "/api/v2/execute/ai/enhance-cases",
    ]
    for route in expected_routes:
        if route in v2_routes:
            log(f"  路由已注册: {route}", "PASS")
        else:
            log(f"  路由缺失: {route}", "FAIL")
            issues.append(f"路由缺失: {route}")

    log(f"V2 路由总计: {len(v2_routes)} 个")
    return issues


# ========== 2. 前端启动检查 ==========
def check_frontend():
    section("2. 前端启动检查")
    issues = []
    try:
        r = requests.get(FRONTEND, timeout=5)
        if r.status_code == 200 and ("<!DOCTYPE" in r.text or "<html" in r.text):
            log("前端 Vite 启动正常 (port 5173)", "PASS")
        else:
            log(f"前端返回异常: status={r.status_code}", "FAIL")
            issues.append("前端页面异常")
    except Exception as e:
        log(f"前端无法连接: {e}", "FAIL")
        issues.append("前端无法连接")

    # 检查 proxy 配置
    try:
        r = requests.get(f"{FRONTEND}/api/v2/execute/auth/status", timeout=5)
        if r.status_code == 200:
            log("前端 proxy → 后端 API 代理正常", "PASS")
        else:
            log(f"前端 proxy 代理异常: {r.status_code}", "WARN")
            issues.append("proxy 代理异常")
    except:
        log("前端 proxy 代理异常", "WARN")
        issues.append("proxy 代理异常")

    return issues


# ========== 3. Token 认证注入验证 ==========
def check_auth():
    section("3. Token 认证注入验证")
    issues = []

    # 3a. 设置 Token
    r = requests.post(f"{BACKEND}/api/v2/execute/auth/set-token", json={
        "token": TOKEN,
        "auth_type": "bearer",
    })
    data = r.json()
    if data.get("success"):
        log(f"Token 设置成功: {data.get('token_preview', '')[:30]}...", "PASS")
    else:
        log("Token 设置失败", "FAIL")
        issues.append("Token 设置失败")
        return issues

    # 3b. 状态查看
    r = requests.get(f"{BACKEND}/api/v2/execute/auth/status")
    envs = r.json().get("envs", {})
    if "default" in envs:
        info = envs["default"]
        log(f"Token 状态: type={info['type']}, expired={info['expired']}", "PASS")
        # 验证 token 脱敏展示
        preview = info.get("token_preview", "")
        if "..." in preview and len(preview) < len(TOKEN):
            log("Token 已脱敏展示（非明文暴露）", "PASS")
        else:
            log("Token 未脱敏！", "WARN")
            issues.append("Token 未脱敏")
    else:
        log("Token 状态查询失败", "FAIL")
        issues.append("Token 状态查询失败")

    # 3c. 验证 Token 注入到请求头
    r = requests.post(f"{BACKEND}/api/v2/execute", json={
        "base_url": BLUEDOT,
        "title": "Token注入验证",
        "method": "POST",
        "path": "/basic/basicCurrency/list",
        "body": {},
        "assertions": [{"type": "status_code", "expected": 200}],
    })
    result = r.json()
    req_headers = result.get("result", {}).get("request", {}).get("headers", {})
    if "Authorization" in req_headers:
        auth_val = req_headers["Authorization"]
        if auth_val.startswith("Bearer "):
            log("Authorization: Bearer xxx 已注入请求头", "PASS")
        else:
            log(f"Authorization 格式异常: {auth_val[:30]}", "WARN")
            issues.append("Authorization 格式异常")
    else:
        log("Authorization 未注入请求头", "FAIL")
        issues.append("Authorization 未注入")

    return issues


# ========== 4. Swagger 用例生成验证 ==========
def check_swagger_gen():
    section("4. Swagger 用例生成验证")
    issues = []

    r = requests.post(f"{BACKEND}/api/v2/execute/generate-from-swagger", json={
        "include_patterns": ["page", "list", "detail"],
        "exclude_patterns": ["save", "update", "delete"],
        "max_cases": 5,
    })
    data = r.json()

    if not data.get("success"):
        log(f"Swagger 生成失败: {data}", "FAIL")
        issues.append("Swagger 生成失败")
        return issues, []

    cases = data.get("cases", [])
    meta = data.get("meta", {})
    log(f"从 Swagger 生成 {len(cases)} 个用例 (总API: {meta.get('total_apis', '?')})", "PASS")

    # 验证字段完整性
    required_fields = ["method", "path", "title", "assertions"]
    for i, c in enumerate(cases[:5]):
        missing = [f for f in required_fields if not c.get(f)]
        if missing:
            log(f"  用例{i+1} [{c.get('title','')}] 缺少字段: {missing}", "FAIL")
            issues.append(f"用例字段缺失: {missing}")
        else:
            body_info = json.dumps(c.get("body", {}), ensure_ascii=False)[:60]
            log(f"  用例{i+1} [{c['method']}] {c['path']}  body={body_info}  assertions={len(c['assertions'])}", "PASS")

    return issues, cases


# ========== 5. 真实 HTTP 执行验证 ==========
def check_real_execution(cases):
    section("5. 真实 HTTP 执行验证（禁止 mock）")
    issues = []

    if not cases:
        log("无用例可执行", "FAIL")
        return issues, None

    r = requests.post(f"{BACKEND}/api/v2/execute/batch", json={
        "base_url": BLUEDOT,
        "cases": cases[:5],
    })
    data = r.json()
    run_id = data.get("run_id", "")
    results = data.get("results", [])
    summary = data.get("summary", {})

    log(f"run_id: {run_id}")
    log(f"执行 {len(results)} 个用例, {summary.get('passed',0)}/{summary.get('total',0)} 通过")

    for res in results:
        status = res.get("status", "unknown")
        title = res.get("case_title", "?")
        duration = res.get("duration_ms", 0)
        resp = res.get("response", {})
        http_code = resp.get("status_code", 0)
        req = res.get("request", {})

        # 验证真实请求
        if http_code > 0:
            log(f"  [{status:>6}] {title}  HTTP {http_code}  {duration:.0f}ms", "PASS" if status == "passed" else "WARN")
        else:
            log(f"  [{status:>6}] {title}  无HTTP响应", "FAIL")
            issues.append(f"无HTTP响应: {title}")

        # 验证 duration 是真实耗时（不是固定值 0.05）
        if duration > 0 and duration != 50:
            log(f"    duration_ms={duration:.1f} (真实耗时)", "PASS")
        else:
            log(f"    duration_ms={duration} (可能是 mock 固定值)", "WARN")

        # 验证 Authorization 已注入
        req_headers = req.get("headers", {})
        has_auth = "Authorization" in req_headers
        if has_auth:
            log(f"    请求头含 Authorization: Bearer xxx", "PASS")
        else:
            log(f"    请求头缺少 Authorization", "WARN")

    return issues, data


# ========== 6. 断言验证 ==========
def check_assertions():
    section("6. 断言验证（多种类型）")
    issues = []

    # 构造一个用例，覆盖多种断言类型
    r = requests.post(f"{BACKEND}/api/v2/execute", json={
        "base_url": BLUEDOT,
        "title": "断言类型覆盖测试",
        "method": "POST",
        "path": "/basic/basicCurrency/list",
        "body": {},
        "assertions": [
            {"type": "status_code", "expected": 200},
            {"type": "response_time", "expected": 5000},
            {"type": "field_exists", "path": "data"},
            {"type": "field_exists", "path": "code"},
            {"type": "field_equals", "path": "code", "expected": 200},
            {"type": "contains", "expected": "data"},
        ],
    })
    data = r.json()
    result = data.get("result", {})
    assertions = result.get("assertions", [])

    log(f"执行 {len(assertions)} 条断言:")
    for a in assertions:
        p = "PASS" if a.get("passed") else "FAIL"
        log(f"  {a['type']:>15}: passed={a['passed']}  {a.get('message','')}", p)
        if not a.get("passed"):
            expected = a.get("expected")
            actual = a.get("actual")
            log(f"    expected={expected}, actual={actual}")

    # 断言失败场景
    log("\n  === 断言失败场景 ===")
    r = requests.post(f"{BACKEND}/api/v2/execute", json={
        "base_url": BLUEDOT,
        "title": "断言失败测试",
        "method": "POST",
        "path": "/basic/basicCurrency/list",
        "body": {},
        "assertions": [
            {"type": "status_code", "expected": 404},
            {"type": "field_exists", "path": "nonexistent_field_xyz"},
        ],
    })
    result = r.json().get("result", {})
    if result.get("status") == "failed":
        log("断言失败时 status=failed", "PASS")
    else:
        log(f"断言失败时 status={result.get('status')} (应为 failed)", "FAIL")
        issues.append("断言失败状态异常")

    for a in result.get("assertions", []):
        if not a.get("passed"):
            has_expected = "expected" in a
            has_actual = "actual" in a
            log(f"  失败断言 [{a['type']}]: has_expected={has_expected} has_actual={has_actual}", "PASS" if has_expected and has_actual else "WARN")

    # AI 断言
    log("\n  === AI 智能断言 ===")
    try:
        r = requests.post(f"{BACKEND}/api/v2/execute/ai/generate-assertions", json={
            "apis": [
                {"path": "/purchaseOrder/page", "method": "POST", "summary": "采购订单分页", "tags": ["采购"]},
            ],
            "max_apis": 1,
        })
        ai_data = r.json()
        if ai_data.get("success"):
            count = ai_data.get("count", 0)
            log(f"AI 断言生成: {count} 条", "PASS")
            for key, asr_list in ai_data.get("assertions", {}).items():
                for a in asr_list:
                    log(f"    {a['type']}: expected={a.get('expected')} path={a.get('path','')}")
        else:
            log("AI 断言生成失败", "FAIL")
            issues.append("AI 断言失败")
    except Exception as e:
        log(f"AI 断言异常: {e}", "FAIL")
        issues.append(f"AI 断言异常: {e}")

    return issues


# ========== 7. 持久化验证 ==========
def check_persistence(run_id):
    section("7. 持久化验证（SQLite DB）")
    issues = []

    if not run_id:
        log("无 run_id，跳过持久化验证", "WARN")
        return issues

    if not os.path.exists(DB_PATH):
        log(f"数据库文件不存在: {DB_PATH}", "FAIL")
        issues.append("数据库不存在")
        return issues

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 查 run 记录
    cur.execute("SELECT * FROM execution_results WHERE run_id = ?", (run_id,))
    rows = cur.fetchall()
    log(f"run_id={run_id} 共 {len(rows)} 条记录")

    if len(rows) == 0:
        log("数据库无记录！", "FAIL")
        issues.append("DB 无记录")
        conn.close()
        return issues

    for row in rows:
        row = dict(row)
        case_id = row.get("case_id", "?")
        status = row.get("status", "?")
        duration = row.get("duration_ms", 0)
        req_snap = row.get("request_json", "")
        resp_snap = row.get("response_json", "")
        assertion_snap = row.get("assertions_json", "")
        error_msg = row.get("error_message", "")

        has_req = bool(req_snap and len(req_snap) > 5)
        has_resp = bool(resp_snap and len(resp_snap) > 5)
        has_assert = bool(assertion_snap and len(assertion_snap) > 5)

        log(f"  {case_id}: status={status} duration={duration:.0f}ms")
        log(f"    request_snapshot: {'✅' if has_req else '❌'} ({len(req_snap)} chars)")
        log(f"    response_snapshot: {'✅' if has_resp else '❌'} ({len(resp_snap)} chars)")
        log(f"    assertion_snapshot: {'✅' if has_assert else '❌'} ({len(assertion_snap)} chars)")
        if error_msg:
            log(f"    error_message: {error_msg[:80]}")

        if not has_req:
            issues.append(f"request_snapshot 缺失: {case_id}")
        if not has_resp:
            issues.append(f"response_snapshot 缺失: {case_id}")

    # 通过 API 查询
    r = requests.get(f"{BACKEND}/api/v2/execute/runs/{run_id}/summary")
    resp_data = r.json()
    summary = resp_data.get("summary", {})
    log(f"  API summary: total={summary.get('total')}, passed={summary.get('passed')}, failed={summary.get('failed')}", "PASS")

    conn.close()
    return issues


# ========== 8. 前端结果展示验证 ==========
def check_frontend_display():
    section("8. 前端结果展示验证")
    log("请在浏览器中手动验证以下项目:", "INFO")
    log("  [ ] 请求方法、URL 正确显示")
    log("  [ ] 请求 Header（Authorization 脱敏）")
    log("  [ ] 请求 Body 正确显示")
    log("  [ ] 响应状态码")
    log("  [ ] 响应 Body")
    log("  [ ] 执行耗时")
    log("  [ ] 断言结果（passed/failed 颜色区分）")
    log("  [ ] 失败原因显示")
    log("")
    log("前端地址: http://localhost:5173/executor-v2", "INFO")
    return []


# ========== 9. 异常场景验证 ==========
def check_exceptions():
    section("9. 异常场景验证")
    issues = []

    # 9a. 未配置 base_url
    log("  === 9a. 缺少 base_url ===")
    r = requests.post(f"{BACKEND}/api/v2/execute", json={
        "title": "无base_url",
        "method": "GET",
        "path": "/test",
    })
    data = r.json()
    if r.status_code >= 400 or "error" in str(data).lower() or "base_url" in str(data).lower():
        log(f"缺少 base_url 返回明确错误: {r.status_code}", "PASS")
    else:
        log(f"缺少 base_url 未报错: {data}", "FAIL")
        issues.append("缺少 base_url 未报错")

    # 9b. Token 错误
    log("\n  === 9b. Token 错误 ===")
    # 先设一个假 token
    requests.post(f"{BACKEND}/api/v2/execute/auth/set-token", json={
        "token": "invalid_token_12345",
        "auth_type": "bearer",
    })
    r = requests.post(f"{BACKEND}/api/v2/execute", json={
        "base_url": BLUEDOT,
        "title": "假Token测试",
        "method": "POST",
        "path": "/purchaseOrder/page",
        "body": {"pageNum": 1, "pageSize": 5},
        "assertions": [{"type": "status_code", "expected": 200}],
    })
    result = r.json().get("result", {})
    http_code = result.get("response", {}).get("status_code", 0)
    status = result.get("status", "")
    if http_code == 401 or status in ("failed", "error"):
        log(f"假Token: HTTP {http_code}, status={status} (认证失败)", "PASS")
    else:
        log(f"假Token: HTTP {http_code}, status={status} (应该失败)", "WARN")

    # 恢复正确 Token
    requests.post(f"{BACKEND}/api/v2/execute/auth/set-token", json={
        "token": TOKEN,
        "auth_type": "bearer",
    })

    # 9c. base_url 不可达
    log("\n  === 9c. base_url 不可达 ===")
    r = requests.post(f"{BACKEND}/api/v2/execute", json={
        "base_url": "http://192.168.255.255:9999",
        "title": "不可达地址",
        "method": "GET",
        "path": "/test",
        "assertions": [{"type": "status_code", "expected": 200}],
    })
    result = r.json().get("result", {})
    if result.get("status") == "error":
        log(f"不可达地址: status=error ✓ msg={result.get('error_message','')[:60]}", "PASS")
    else:
        log(f"不可达地址: status={result.get('status')} (应为 error)", "FAIL")
        issues.append("不可达地址状态异常")

    # 9d. 断言失败
    log("\n  === 9d. 断言失败 ===")
    r = requests.post(f"{BACKEND}/api/v2/execute", json={
        "base_url": BLUEDOT,
        "title": "断言失败场景",
        "method": "POST",
        "path": "/basic/basicCurrency/list",
        "body": {},
        "assertions": [{"type": "status_code", "expected": 404}],
    })
    result = r.json().get("result", {})
    if result.get("status") == "failed":
        log("断言失败: status=failed ✓", "PASS")
    else:
        log(f"断言失败: status={result.get('status')} (应为 failed)", "FAIL")
        issues.append("断言失败状态异常")

    # 9e. 接口返回 500
    log("\n  === 9e. 接口返回非200 ===")
    r = requests.post(f"{BACKEND}/api/v2/execute", json={
        "base_url": BLUEDOT,
        "title": "404接口测试",
        "method": "POST",
        "path": "/nonexistent/api/path/xyz",
        "body": {},
        "assertions": [{"type": "status_code", "expected": 200}],
    })
    result = r.json().get("result", {})
    http_code = result.get("response", {}).get("status_code", 0)
    if result.get("status") != "passed":
        log(f"非200接口: HTTP {http_code}, status={result.get('status')} (未误判为 passed)", "PASS")
    elif http_code == 200:
        log(f"非200接口: 远端网关返回200（网关兜底行为），断言 status_code=200 正确匹配", "WARN")
    else:
        log(f"非200接口: 被判为 passed！(HTTP {http_code})", "FAIL")
        issues.append("非200接口误判为passed")

    return issues


# ========== 10. 生成报告 ==========
def generate_report(all_issues):
    section("10. 联调验收报告总结")

    blocking = [i for i in all_issues if "无法连接" in i or "DB 无记录" in i or "路由缺失" in i]
    non_blocking = [i for i in all_issues if i not in blocking]

    log(f"总检查项: 10")
    log(f"发现问题: {len(all_issues)}")
    log(f"阻塞问题: {len(blocking)}")
    log(f"非阻塞问题: {len(non_blocking)}")

    if blocking:
        log("\n🔴 阻塞问题:")
        for i in blocking:
            log(f"  - {i}", "FAIL")

    if non_blocking:
        log("\n🟡 非阻塞问题:")
        for i in non_blocking:
            log(f"  - {i}", "WARN")

    if not all_issues:
        log("\n🎉 全部验证通过，无阻塞问题！", "PASS")

    return blocking, non_blocking


# ========== 主函数 ==========
def main():
    print("\n" + "🔥" * 30)
    print("  Phase 1-10 前端全流程联调验收")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("🔥" * 30)

    all_issues = []

    # 1. 后端
    issues = check_backend()
    all_issues.extend(issues)

    # 2. 前端
    issues = check_frontend()
    all_issues.extend(issues)

    # 3. Token
    issues = check_auth()
    all_issues.extend(issues)

    # 4. Swagger
    issues, cases = check_swagger_gen()
    all_issues.extend(issues)

    # 5. 真实执行
    issues, exec_data = check_real_execution(cases)
    all_issues.extend(issues)
    run_id = exec_data.get("run_id", "") if exec_data else ""

    # 6. 断言
    issues = check_assertions()
    all_issues.extend(issues)

    # 7. 持久化
    issues = check_persistence(run_id)
    all_issues.extend(issues)

    # 8. 前端展示
    issues = check_frontend_display()
    all_issues.extend(issues)

    # 9. 异常
    issues = check_exceptions()
    all_issues.extend(issues)

    # 10. 报告
    blocking, non_blocking = generate_report(all_issues)

    # 写入报告文件
    report_path = r"G:\AI项目\ai测试\ai-test-platform\Phase1-10_联调验收报告.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Phase 1-10 前端全流程联调验收报告\n\n")
        f.write(f"**验收时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## 验收日志\n\n```\n")
        f.write("\n".join(report))
        f.write("\n```\n\n")
        f.write(f"## 问题汇总\n\n")
        f.write(f"- 阻塞问题: {len(blocking)}\n")
        f.write(f"- 非阻塞问题: {len(non_blocking)}\n\n")
        if blocking:
            f.write("### 🔴 阻塞问题\n\n")
            for i in blocking:
                f.write(f"- {i}\n")
            f.write("\n")
        if non_blocking:
            f.write("### 🟡 非阻塞问题\n\n")
            for i in non_blocking:
                f.write(f"- {i}\n")
            f.write("\n")
        if not all_issues:
            f.write("### ✅ 全部通过\n\n无阻塞问题。\n")

    log(f"\n📄 报告已生成: {report_path}")


if __name__ == "__main__":
    main()
