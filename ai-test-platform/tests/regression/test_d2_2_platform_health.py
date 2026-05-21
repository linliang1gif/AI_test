#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
D2-2 验收脚本 — 平台健康检查 + 工程收敛验证

验证项:
  1. /api/v2/health/full 返回 200，字段完整
  2. trace_id 存在
  3. 数据库状态可识别
  4. 错误响应不泄露敏感字段
  5. 至少一个核心 v2 接口可用
  6. 前端 api.js 不再引用明显 legacy 硬编码路径
  7. 错误响应标准化结构验证

用法:
  python scripts/test_d2_2_platform_health.py [--base http://127.0.0.1:8001]
"""
import sys
import os
import json
import re
import argparse
import requests

PASS = "✅ PASS"
FAIL = "❌ FAIL"
WARN = "⚠️  WARN"

results = []


def check(name, passed, detail=""):
    status = PASS if passed else FAIL
    results.append((name, passed, detail))
    print(f"  {status}  {name}" + (f" — {detail}" if detail else ""))
    return passed


def warn(name, detail=""):
    results.append((name, None, detail))
    print(f"  {WARN}  {name}" + (f" — {detail}" if detail else ""))


def main():
    parser = argparse.ArgumentParser(description="D2-2 验收脚本")
    parser.add_argument("--base", default="http://127.0.0.1:8001", help="后端 base URL")
    args = parser.parse_args()
    base = args.base.rstrip("/")

    print(f"\n{'='*60}")
    print(f"  D2-2 平台健康检查验收  (backend={base})")
    print(f"{'='*60}\n")

    # ── 1. /api/v2/health/full ──
    print("[1] /api/v2/health/full 接口验证")
    try:
        resp = requests.get(f"{base}/api/v2/health/full", timeout=10)
        check("health/full 返回 200", resp.status_code == 200, f"status={resp.status_code}")
        data = resp.json()

        required_fields = ["backend_status", "database_status", "ai_config_status",
                           "environment_status", "latest_run_status", "trace_id", "timestamp"]
        missing = [f for f in required_fields if f not in data]
        check("返回字段完整", len(missing) == 0,
              f"缺少: {missing}" if missing else f"包含全部 {len(required_fields)} 个必要字段")

        # 2. trace_id
        tid = data.get("trace_id", "")
        check("trace_id 存在且非空", bool(tid), f"trace_id={tid}")

        # 响应头中也应有 X-Trace-Id
        header_tid = resp.headers.get("X-Trace-Id", "")
        check("响应头包含 X-Trace-Id", bool(header_tid), f"X-Trace-Id={header_tid}")

        # 3. 数据库状态可识别
        db_status = data.get("database_status", "")
        valid_db = db_status in ("ok", "degraded", "error")
        check("数据库状态可识别", valid_db, f"database_status={db_status}")

        # backend_status
        check("后端状态为 ok", data.get("backend_status") == "ok", f"backend_status={data.get('backend_status')}")

    except requests.ConnectionError:
        check("health/full 可连接", False, f"无法连接 {base}")
        print("\n⛔ 后端未启动，后续测试跳过。")
        _summary()
        return
    except Exception as e:
        check("health/full 无异常", False, str(e))

    # ── 4. 错误响应不泄露敏感字段 ──
    print("\n[2] 错误响应标准化验证")
    try:
        err_resp = requests.get(f"{base}/api/v2/this-does-not-exist-d2-2-test", timeout=5)
        check("不存在路由返回 404", err_resp.status_code == 404)
        err_data = err_resp.json()

        # 标准化结构
        has_code = "code" in err_data
        has_message = "message" in err_data
        has_trace = "trace_id" in err_data
        check("错误响应含 code 字段", has_code, f"code={err_data.get('code')}")
        check("错误响应含 message 字段", has_message)
        check("错误响应含 trace_id 字段", has_trace)

        # 敏感字段泄露检查
        err_text = json.dumps(err_data, ensure_ascii=False).lower()
        sensitive_patterns = ["token", "authorization", "cookie", "api_key", "secret", "password"]
        leaked = [p for p in sensitive_patterns if p in err_text]
        check("错误响应不泄露敏感字段", len(leaked) == 0,
              f"发现敏感词: {leaked}" if leaked else "无敏感词泄露")
    except Exception as e:
        check("错误响应检查无异常", False, str(e))

    # ── 5. 至少一个核心 v2 接口可用 ──
    print("\n[3] 核心 v2 接口可用性")
    v2_endpoints = [
        ("GET", "/api/v2/projects", "项目列表"),
        ("GET", "/api/v2/test-cases?limit=1", "测试用例"),
        ("GET", "/api/v2/dashboard/summary", "仪表盘"),
    ]
    v2_ok_count = 0
    for method, path, label in v2_endpoints:
        try:
            r = requests.request(method, f"{base}{path}", timeout=5)
            ok = r.status_code == 200
            if ok:
                v2_ok_count += 1
            check(f"v2 {label} ({method} {path})", ok, f"status={r.status_code}")
        except Exception as e:
            check(f"v2 {label}", False, str(e))
    check("至少一个核心 v2 接口返回 200", v2_ok_count > 0, f"{v2_ok_count}/{len(v2_endpoints)} 可用")

    # ── 6. 前端 api.js legacy 路径检查 ──
    print("\n[4] 前端 api.js legacy 路径检查")
    api_js_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               "frontend", "src", "services", "api.js")
    if os.path.exists(api_js_path):
        with open(api_js_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 检查是否有 http://localhost:8000 硬编码
        hardcoded = re.findall(r'http://localhost:\d+', content)
        check("api.js 无 http://localhost 硬编码", len(hardcoded) == 0,
              f"发现: {hardcoded}" if hardcoded else "")

        # 检查 legacy 标记
        legacy_markers = content.count("[LEGACY]")
        check("api.js legacy 接口已标记", legacy_markers > 0, f"找到 {legacy_markers} 处 [LEGACY] 标记")

        # 检查 X-Trace-Id
        has_trace_header = "X-Trace-Id" in content
        check("api.js request() 携带 X-Trace-Id", has_trace_header)

        # 检查 health.full
        has_health_full = "health/full" in content
        check("api.js 包含 health.full 调用", has_health_full)
    else:
        warn("api.js 文件未找到", api_js_path)

    # ── 7. 前端路由检查 ──
    print("\n[5] 前端路由检查")
    app_jsx = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "frontend", "src", "App.jsx")
    if os.path.exists(app_jsx):
        with open(app_jsx, "r", encoding="utf-8") as f:
            app_content = f.read()
        check("/platform-health 路由已注册", "/platform-health" in app_content)
        check("PlatformHealth 组件已导入", "PlatformHealth" in app_content)
    else:
        warn("App.jsx 文件未找到", app_jsx)

    _summary()


def _summary():
    print(f"\n{'='*60}")
    total = len(results)
    passed = sum(1 for _, ok, _ in results if ok is True)
    failed = sum(1 for _, ok, _ in results if ok is False)
    warns = sum(1 for _, ok, _ in results if ok is None)
    print(f"  总计: {total} 项  |  通过: {passed}  |  失败: {failed}  |  警告: {warns}")
    if failed == 0:
        print(f"  🎉 D2-2 验收通过！")
    else:
        print(f"  ⛔ D2-2 验收未通过，请修复 {failed} 项失败项。")
    print(f"{'='*60}\n")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
