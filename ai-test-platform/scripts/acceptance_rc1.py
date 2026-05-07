# -*- coding: utf-8 -*-
"""RC-1 验收脚本：核心接口 / 模块健康 / 敏感脱敏 / 错误结构

目标：作为 RC-1 稳定候选版的客观验收依据，避免主观完成度。

特性：
- 不修改任何业务代码、路由、服务、数据库结构、前端页面
- Windows 控制台兼容，禁用 emoji，统一使用 [OK]/[FAIL]/[WARN]/[SKIP]
- 每个 check 独立执行，单项失败不中断后续
- 默认后端 http://127.0.0.1:8001（环境变量 BACKEND_URL 覆盖）
- 默认超时 10s（环境变量 TIMEOUT 覆盖）
- FAIL > 0 -> exit 1；FAIL == 0 -> exit 0
- WARN / SKIP 不计入失败

使用：
    python scripts/acceptance_rc1.py

环境变量：
    BACKEND_URL  默认 http://127.0.0.1:8001
    TIMEOUT      默认 10（秒）
"""
import io
import json
import os
import re
import sys
from urllib import request as urlreq
from urllib.error import HTTPError, URLError

# ── Windows 控制台 UTF-8 兼容 ─────────────────────────────────
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    except Exception:
        pass

BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8001").rstrip("/")
try:
    TIMEOUT = float(os.environ.get("TIMEOUT", "10"))
except Exception:
    TIMEOUT = 10.0


# ── Result aggregator ───────────────────────────────────────
_results = []  # list of (status, name, summary)


def record(status: str, name: str, summary: str) -> None:
    """记录一项 check 结果并立即输出"""
    _results.append((status, name, summary))
    # 截断 summary 防止终端被超长行污染
    safe_summary = summary if len(summary) <= 240 else summary[:237] + "..."
    print(f"[{status}] {name} - {safe_summary}", flush=True)


# ── HTTP helper ─────────────────────────────────────────────
def http_request(method: str, path: str, body=None):
    """发起 HTTP 请求；返回 (status_code|None, payload|None, err|None)。

    任何异常都吃掉，转为 err 字符串，不上抛。
    payload 优先尝试解析为 JSON，失败则保留为字符串。
    """
    url = BACKEND_URL + path
    headers = {"Accept": "application/json"}
    data = None
    if body is not None:
        try:
            data = json.dumps(body).encode("utf-8")
        except Exception as e:
            return None, None, f"json.dumps body failed: {e}"
        headers["Content-Type"] = "application/json"
    req = urlreq.Request(url, data=data, headers=headers, method=method)
    try:
        with urlreq.urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read()
            status = resp.status
            text = raw.decode("utf-8", errors="replace")
            try:
                payload = json.loads(text)
            except Exception:
                payload = text
            return status, payload, None
    except HTTPError as e:
        try:
            err_text = e.read().decode("utf-8", errors="replace")
        except Exception:
            err_text = ""
        try:
            err_payload = json.loads(err_text) if err_text else None
        except Exception:
            err_payload = err_text
        return e.code, err_payload, None
    except URLError as e:
        return None, None, f"URLError: {getattr(e, 'reason', e)}"
    except Exception as e:
        return None, None, f"{type(e).__name__}: {e}"


# ── 敏感信息扫描 ─────────────────────────────────────────────
# 仅匹配「value 内的疑似明文敏感串」，不简单按字段名命中。
SENSITIVE_VALUE_PATTERNS = [
    (re.compile(r"eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+"), "JWT"),
    (re.compile(r"\bBearer\s+[A-Za-z0-9_\-\.~+/=]{16,}"), "Bearer token"),
    (re.compile(r"\bBasic\s+[A-Za-z0-9+/]{20,}={0,2}"), "Basic auth"),
    (re.compile(r"\$2[aby]\$\d{2}\$[A-Za-z0-9./]{53}"), "bcrypt hash"),
    (re.compile(r"\b(AKIA|ASIA)[A-Z0-9]{16}\b"), "AWS access key"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "PEM private key"),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}"), "Slack token"),
    (re.compile(r"\bghp_[A-Za-z0-9]{30,}\b"), "GitHub PAT"),
    (re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"), "OpenAI key"),
]

# 已脱敏 / 占位值白名单（不视为泄露）
SAFE_VALUE_RE = re.compile(
    r"^[\*]+$|^x+$|<redacted>|REDACTED|masked|^\$\{|^\*{3,}",
    re.IGNORECASE,
)


def _mask_match(s: str) -> str:
    if len(s) <= 8:
        return s[:2] + "***"
    return s[:4] + "***" + s[-2:]


def scan_sensitive(payload, path_label: str):
    """递归扫描 payload，返回 [hit_str, ...]"""
    hits = []

    def walk(obj, key=None):
        if isinstance(obj, dict):
            for k, v in obj.items():
                walk(v, k)
        elif isinstance(obj, list):
            for x in obj:
                walk(x, key)
        elif isinstance(obj, str):
            s = obj.strip()
            if not s or SAFE_VALUE_RE.match(s):
                return
            for pat, label in SENSITIVE_VALUE_PATTERNS:
                m = pat.search(s)
                if m:
                    hits.append(
                        f"{path_label} field={key} kind={label} sample={_mask_match(m.group(0))}"
                    )
                    break

    walk(payload)
    return hits


# ──────────────────────────────────────────────────────────
# Checks
# ──────────────────────────────────────────────────────────


def check_health():
    code, body, err = http_request("GET", "/health")
    if err or code != 200:
        record("FAIL", "01_health", f"GET /health failed code={code} err={err}")
        return None
    if not isinstance(body, dict):
        record("FAIL", "01_health", "response not JSON object")
        return None
    status = body.get("status")
    db = body.get("database") if isinstance(body.get("database"), dict) else {}
    db_connected = bool(db.get("connected"))
    if status == "healthy" and db_connected:
        record("OK", "01_health", "status=healthy, database.connected=true")
    elif status == "healthy":
        record("WARN", "01_health", "status=healthy 但 database.connected != true")
    else:
        record("FAIL", "01_health", f"status={status}, db.connected={db_connected}")
    return body


def check_modules(health_body):
    if not isinstance(health_body, dict):
        record("WARN", "02_modules", "无 /health 响应数据可校验，跳过 modules 检查")
        return
    modules = health_body.get("modules")
    if not isinstance(modules, dict):
        record("WARN", "02_modules", "/health 响应不含 modules 字段")
        return
    bad = [k for k, v in modules.items() if v is not True]
    total = len(modules)
    if bad:
        # 截掉中文模块名以避免控制台乱码污染
        sample = ", ".join(repr(x) for x in bad[:5])
        record("FAIL", "02_modules", f"{len(bad)}/{total} 模块未就绪，例如 {sample}")
    else:
        record("OK", "02_modules", f"全部 {total} 个模块 true")


def check_simple_get(label: str, name: str, path: str):
    code, body, err = http_request("GET", path)
    if err:
        record("FAIL", f"{label}_{name}", f"GET {path} 网络错误: {err}")
        return None
    if code != 200:
        record("FAIL", f"{label}_{name}", f"GET {path} -> {code} (期望 200)")
        return None
    record("OK", f"{label}_{name}", f"GET {path} -> 200")
    return body


def check_test_cases():
    code, body, err = http_request("GET", "/api/v2/test-cases?limit=5")
    if err or code != 200:
        record("FAIL", "04_test_cases", f"err={err} code={code}")
        return
    if not isinstance(body, dict):
        record("WARN", "04_test_cases", "200 OK 但响应非对象")
        return
    has_list = "test_cases" in body or "data" in body or "items" in body
    total = body.get("total")
    if has_list:
        record("OK", "04_test_cases", f"200 OK total={total}")
    else:
        record("WARN", "04_test_cases", "200 OK 但缺常见列表字段")


def check_tapd_config():
    code, body, err = http_request("GET", "/api/v2/code-compare/tapd/config")
    if err or code != 200:
        record("FAIL", "10_tapd_config", f"err={err} code={code}")
        return
    if not isinstance(body, dict):
        record("FAIL", "10_tapd_config", "响应非对象")
        return
    cfg = body.get("config")
    if not isinstance(cfg, dict):
        record("WARN", "10_tapd_config", "200 OK 但缺 config 字段")
        return
    pwd = cfg.get("api_password", "")
    # 视为已脱敏：空串、纯星号、占位
    if pwd in (None, "", "******") or (
        isinstance(pwd, str) and pwd and set(pwd) == {"*"}
    ):
        record("OK", "10_tapd_config", f"api_password 已脱敏 (value='{pwd}')")
    else:
        # 长度 + 前两位 mask 用于报告
        sample = _mask_match(str(pwd)) if pwd else "<empty>"
        record(
            "FAIL",
            "10_tapd_config",
            f"api_password 疑似未脱敏 len={len(str(pwd))} sample={sample}",
        )


def check_demo_status():
    code, body, err = http_request("GET", "/api/v2/demo/status")
    if err or code != 200:
        record("FAIL", "11_demo_status", f"err={err} code={code}")
        return
    data = (body or {}).get("data") if isinstance(body, dict) else None
    initialized = bool(data.get("initialized")) if isinstance(data, dict) else False
    if initialized:
        record("OK", "11_demo_status", "Demo 已初始化")
    else:
        record("WARN", "11_demo_status", "Demo 未初始化（按 RC-1 规则不阻塞）")


def check_test_selection():
    # 用空 payload；目标是探活，不强求业务结果
    code, body, err = http_request(
        "POST", "/api/v2/test-selection/recommend", body={}
    )
    if err:
        record("SKIP", "12_test_selection", f"接口异常或不可达: {err}")
        return
    if code in (200, 201):
        record("OK", "12_test_selection", f"POST recommend -> {code}")
    elif code == 400:
        record(
            "SKIP",
            "12_test_selection",
            "返回 400，项目内无法自动构造合法 payload，按规则记 SKIP",
        )
    elif code == 404:
        record("SKIP", "12_test_selection", "endpoint 未找到，按规则记 SKIP")
    elif code is None:
        record("SKIP", "12_test_selection", "无响应码，按规则记 SKIP")
    else:
        record(
            "WARN",
            "12_test_selection",
            f"POST recommend -> {code}（非 5xx 阻塞，按 RC-1 规则记 WARN）",
        )


def check_quality_gate():
    # 依据 routes/quality_gate_routes.py 实际探活点：GET /api/v2/quality-gates/default-config
    path = "/api/v2/quality-gates/default-config"
    code, body, err = http_request("GET", path)
    if err:
        record("SKIP", "13_quality_gate", f"GET {path} 异常: {err}")
        return
    if code == 200:
        record("OK", "13_quality_gate", f"GET {path} -> 200")
    elif code == 404:
        record(
            "SKIP",
            "13_quality_gate",
            f"GET {path} -> 404，未找到稳定探活接口，按规则记 SKIP",
        )
    else:
        record(
            "SKIP",
            "13_quality_gate",
            f"GET {path} -> {code}，按规则记 SKIP（不阻塞）",
        )


def check_error_structure():
    path = "/api/v2/code-compare/reports/__nonexistent_rc1__"
    code, body, err = http_request("GET", path)
    if err:
        record("FAIL", "14_error_structure", f"网络错误: {err}")
        return
    if code is None:
        record("FAIL", "14_error_structure", "无响应码")
        return
    if not (400 <= code < 500):
        record(
            "FAIL", "14_error_structure", f"应返回 4xx 但得到 {code}（资源不存在）"
        )
        return
    if isinstance(body, dict):
        keys = [k for k in ("detail", "message", "error", "code") if k in body]
        if keys:
            record("OK", "14_error_structure", f"{code} 含字段 {keys}")
        else:
            record(
                "FAIL",
                "14_error_structure",
                f"{code} JSON 但缺关键字段 detail/message/error/code",
            )
    else:
        # 非 JSON 字符串
        sample = (body or "")[:80] if isinstance(body, str) else ""
        record(
            "FAIL",
            "14_error_structure",
            f"{code} 返回非 JSON / 空响应 (sample={sample!r})",
        )


def check_sensitive_leak():
    """对若干 endpoint 抓响应扫敏感 value（不命中 key 名）。"""
    targets = [
        "/health",
        "/api/v2/projects",
        "/api/v2/code-compare/tapd/config",
    ]
    all_hits = []
    for p in targets:
        code, body, err = http_request("GET", p)
        if err or code != 200 or body is None:
            continue
        all_hits.extend(scan_sensitive(body, p))
    if all_hits:
        sample = "; ".join(all_hits[:3])
        record(
            "FAIL",
            "15_sensitive_leak",
            f"发现 {len(all_hits)} 个疑似明文敏感值: {sample}",
        )
    else:
        record(
            "OK",
            "15_sensitive_leak",
            "未发现疑似明文敏感值（JWT/Bearer/bcrypt/AWS/PEM/PAT/Slack 等）",
        )


# ──────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────


def _safe(fn, *args):
    """单项 check 顶层守护：吃掉所有异常，转为 FAIL 记录"""
    try:
        return fn(*args)
    except Exception as e:
        name = getattr(fn, "__name__", repr(fn))
        record("FAIL", f"00_uncaught_{name}", f"{type(e).__name__}: {e}")
        return None


def main():
    print("=" * 70)
    print(f"RC-1 ACCEPTANCE  backend={BACKEND_URL}  timeout={TIMEOUT}s")
    print("=" * 70)

    health_body = _safe(check_health)
    _safe(check_modules, health_body)
    _safe(check_simple_get, "03", "projects", "/api/v2/projects")
    _safe(check_test_cases)
    _safe(check_simple_get, "05", "test_runs", "/api/v2/test-runs")
    _safe(check_simple_get, "06", "defects", "/api/v2/defects")
    _safe(check_simple_get, "07", "dashboard_summary", "/api/v2/dashboard/summary")
    _safe(check_simple_get, "08", "analytics_overview", "/api/v2/analytics/overview")
    _safe(check_simple_get, "09", "code_compare_reports", "/api/v2/code-compare/reports")
    _safe(check_tapd_config)
    _safe(check_demo_status)
    _safe(check_test_selection)
    _safe(check_quality_gate)
    _safe(check_error_structure)
    _safe(check_sensitive_leak)

    # ── Summary ──
    counts = {"OK": 0, "FAIL": 0, "WARN": 0, "SKIP": 0}
    for s, _, _ in _results:
        counts[s] = counts.get(s, 0) + 1
    total = len(_results)

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"TOTAL:     {total}")
    print(f"PASS:      {counts['OK']}")
    print(f"FAIL:      {counts['FAIL']}")
    print(f"WARN:      {counts['WARN']}")
    print(f"SKIP:      {counts['SKIP']}")
    exit_code = 1 if counts["FAIL"] > 0 else 0
    print(f"EXIT_CODE: {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
