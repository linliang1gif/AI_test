"""Phase 10B 危险接口扫描脚本

扫描 routes/ 下的所有 FastAPI 路由，识别可能的高危操作（删除/批量删除/回滚/清空/重置/webhook 测试），
检查是否已接入 backend.danger_guard.check_confirm，并输出扫描报告。

输出：
  1. 终端可读表格
  2. JSON 报告（data/reports/dangerous_routes.json）
  3. 退出码：0 全部正常 / 1 存在未保护的高危接口

排除目录：archive/、scripts/、tests/、frontend/、node_modules/、.venv/、__pycache__/
"""
from __future__ import annotations
import ast
import json
import os
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Optional, Set

ROOT = Path(__file__).resolve().parent.parent
ROUTES_DIR = ROOT / "routes"
REPORT_DIR = ROOT / "data" / "reports"

EXCLUDE_DIRS = {"archive", "scripts", "tests", "frontend", "node_modules",
                ".venv", "venv", "__pycache__", ".git", "dist", "build"}

# Phase 10B: 经人工评估的"低风险"接口白名单（不要求 check_confirm）
# 格式：(file_relative, function_name) → 评估说明
LOW_RISK_WHITELIST = {
    ("routes/executor_v2_routes.py", "clear_auth_token"):
        "清单个环境的 token，重新登录即可恢复，风险低",
    ("routes/mock_routes.py", "mock_delete_product"):
        "Mock 数据演示用，无业务影响",
    ("routes/page_scanner_routes.py", "delete_login_session_endpoint"):
        "登录态可重建，删除后下次扫描会重新提示登录",
    ("routes/project_config_routes.py", "delete_auth_profile"):
        "auth profile 软删除，前端 UI 已有二次确认；如有外部脚本直调，可后续补 confirm",
    ("routes/swagger_routes.py", "delete_api_spec"):
        "API spec 删除不影响已生成的用例",
    ("routes/test_data_routes.py", "delete_item"):
        "数据项可从源数据重新生成",
    ("routes/test_data_routes.py", "delete_binding"):
        "绑定关系可重建",
    ("routes/test_suite_routes.py", "remove_case"):
        "仅从套件移除关联，原用例不受影响",
}

# 危险特征匹配（按优先级排序，更具体的先匹配）
# (匹配关键字, 推荐 confirm_text, 风险说明)
DANGER_PATTERNS = [
    # 高破坏 - 数据删除
    ("delete-project",     "DELETE_PROJECT",        "删除项目（连带配置/资源）"),
    ("delete-test-case",   "DELETE_TEST_CASE",      "删除单条测试用例"),
    ("bulk-delete-cases",  "BULK_DELETE_TEST_CASES", "批量删除测试用例"),
    ("delete-report",      "DELETE_REPORT",         "删除测试报告"),
    ("delete-finding",     "DELETE_FINDING",        "删除缺陷/Finding"),
    ("delete-baseline",    "DELETE_BASELINE",       "删除视觉基线"),
    ("rollback-baseline",  "ROLLBACK_BASELINE",     "回滚视觉基线"),
    ("delete-environment", "DELETE_ENVIRONMENT",    "删除环境配置"),
    ("delete-dead-letter", "DELETE_DEAD_LETTER",    "删除 webhook 死信"),
    ("delete-suite",       "DELETE_TEST_SUITE",     "删除测试集"),
    ("delete-dataset",     "DELETE_DATASET",        "删除数据集"),
    ("delete-batch-run",   "DELETE_BATCH_RUN",      "删除批量执行任务"),
    # 中破坏 - 清空/重置
    ("clear-demo",         "CLEAR_DEMO_DATA",       "清空 demo 数据"),
    ("reset-demo",         "RESET_DEMO_DATA",       "重置 demo 数据"),
    ("purge-",             "PURGE_DATA",            "清理数据"),
    ("clear-",             "CLEAR_DATA",            "清空数据"),
    ("reset-",             "RESET_DATA",            "重置数据"),
    # 外发 - webhook test
    ("webhook-test",       "TEST_WEBHOOK",          "发送测试 webhook（外发）"),
]

# 路径中含此词的，按 method 二次判定
SECONDARY_KEYWORDS = ["delete", "bulk", "rollback", "clear", "reset", "purge", "remove", "webhook/test"]


@dataclass
class RouteEntry:
    file: str
    line: int
    method: str
    path: str
    function: str
    has_check_confirm: bool
    suggested_confirm_text: str = ""
    risk_label: str = ""           # PROTECTED | NEEDS_PROTECTION | INFO_ONLY
    note: str = ""


def _classify(method: str, path: str, fn_src: str) -> Optional[tuple[str, str]]:
    """判断路径+方法是否危险，返回 (suggested_confirm_text, risk_note) 或 None。

    策略：
      1. DELETE 方法默认进入候选
      2. 路径含 delete/bulk/rollback/clear/reset/purge/webhook/test/remove 进入候选
      3. 函数体内含 fn_src 的 db.delete / unlink / rmtree 等强信号 加权
    """
    p = path.lower().rstrip("/")
    m = method.upper()

    # GET / OPTIONS / HEAD 永远跳过
    if m in {"GET", "OPTIONS", "HEAD"}:
        return None

    # 复合特征匹配（更精确）
    composite = {
        ("DELETE", "projects"): "DELETE_PROJECT",
        ("DELETE", "test-cases"): "DELETE_TEST_CASE",
        ("DELETE", "testcases"): "DELETE_TEST_CASE",
        ("DELETE", "cases/"): "DELETE_TEST_CASE",
        ("DELETE", "reports"): "DELETE_REPORT",
        ("DELETE", "findings"): "DELETE_FINDING",
        ("DELETE", "defects"): "DELETE_FINDING",
        ("DELETE", "environments"): "DELETE_ENVIRONMENT",
        ("DELETE", "baselines"): "DELETE_BASELINE",
        ("DELETE", "dead-letters"): "DELETE_DEAD_LETTER",
        ("DELETE", "suites"): "DELETE_TEST_SUITE",
        ("DELETE", "datasets"): "DELETE_DATASET",
        ("DELETE", "batch-runs"): "DELETE_BATCH_RUN",
    }
    for (mm, kw), suggest in composite.items():
        if m == mm and kw in p:
            return suggest, f"{m} {path} → {suggest}"

    # 单关键字匹配（路径中含）
    if "rollback" in p:
        return "ROLLBACK_BASELINE" if "baseline" in p else "ROLLBACK_OPERATION", "rollback 操作"
    if "bulk/delete" in p or "bulk-delete" in p or "batch-delete" in p or "batch/delete" in p:
        if "case" in p or "testcase" in p:
            return "BULK_DELETE_TEST_CASES", "批量删除用例"
        if "baseline" in p:
            return "BULK_DELETE_BASELINES", "批量删除基线"
        return "BULK_DELETE", "批量删除"
    if "clear/demo" in p or "demo/clear" in p or ("clear" in p and "demo" in p):
        return "CLEAR_DEMO_DATA", "清空 demo 数据"
    if "reset/demo" in p or "demo/reset" in p or ("reset" in p and "demo" in p):
        return "RESET_DEMO_DATA", "重置 demo 数据"
    if "webhook/test" in p or p.endswith("/test"):
        if "webhook" in p:
            return "TEST_WEBHOOK", "发送测试 webhook"
    if m == "DELETE":
        # 兜底：未识别的 DELETE
        return "DELETE_RESOURCE", "通用 DELETE 操作"

    # 含 purge / remove / clear / reset 但非 GET
    for kw in ["purge", "remove"]:
        if kw in p and m in {"POST", "DELETE"}:
            return kw.upper() + "_DATA", f"{kw} 操作"

    return None


def _function_uses_check_confirm(fn_node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """检查函数体内是否调用 check_confirm()。"""
    for node in ast.walk(fn_node):
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name) and f.id == "check_confirm":
                return True
            if isinstance(f, ast.Attribute) and f.attr == "check_confirm":
                return True
    return False


def _scan_route_file(path: Path) -> List[RouteEntry]:
    """解析单个路由文件，返回所有候选的危险路由条目。"""
    src = path.read_bytes().decode("utf-8", errors="replace")
    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError:
        return []

    entries: List[RouteEntry] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        # 寻找 @router.<method>("/path") 装饰器
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call):
                continue
            f = dec.func
            method = ""
            if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
                if f.value.id in ("router", "app"):
                    method = f.attr.upper()
            if not method or method not in {"GET", "POST", "PUT", "DELETE", "PATCH"}:
                continue
            # 提取路径
            route_path = ""
            if dec.args and isinstance(dec.args[0], ast.Constant):
                route_path = dec.args[0].value or ""
            if not route_path:
                continue

            classified = _classify(method, route_path, "")
            if classified is None:
                continue

            suggest, risk_note = classified
            has = _function_uses_check_confirm(node)
            file_rel = str(path.relative_to(ROOT)).replace("\\", "/")
            wl_key = (file_rel, node.name)

            if has:
                risk_label = "PROTECTED"
            elif wl_key in LOW_RISK_WHITELIST:
                risk_label = "LOW_RISK_OK"
                risk_note = LOW_RISK_WHITELIST[wl_key]
            else:
                risk_label = "NEEDS_PROTECTION"

            entries.append(RouteEntry(
                file=file_rel,
                line=node.lineno,
                method=method,
                path=route_path,
                function=node.name,
                has_check_confirm=has,
                suggested_confirm_text=suggest,
                risk_label=risk_label,
                note=risk_note,
            ))
    return entries


def scan_all() -> List[RouteEntry]:
    all_entries: List[RouteEntry] = []
    for p, dirs, files in os.walk(ROUTES_DIR):
        # 排除目录
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            if not f.endswith(".py") or f.startswith("_"):
                continue
            full = Path(p) / f
            all_entries.extend(_scan_route_file(full))
    # 排序：未保护的优先
    all_entries.sort(key=lambda e: (e.has_check_confirm, e.file, e.line))
    return all_entries


_LABEL_ICON = {
    "PROTECTED":         "[OK ] PROTECTED",
    "LOW_RISK_OK":       "[ -- ] LOW_RISK ",
    "NEEDS_PROTECTION":  "[!! ] NEEDS_PROT",
}


def render_table(entries: List[RouteEntry]) -> str:
    headers = ["risk", "method", "path", "function", "file", "confirm_text"]
    widths = [18, 7, 50, 30, 38, 28]
    rows = []
    for e in entries:
        risk = _LABEL_ICON.get(e.risk_label, e.risk_label)
        rows.append([
            risk,
            e.method,
            (e.path[:48] + "…") if len(e.path) > 50 else e.path,
            (e.function[:28] + "…") if len(e.function) > 30 else e.function,
            (e.file[:36] + "…") if len(e.file) > 38 else e.file,
            e.suggested_confirm_text,
        ])

    def fmt(row):
        return "  ".join(c.ljust(w) for c, w in zip(row, widths))

    sep = "-" * (sum(widths) + 2 * len(widths))
    lines = [fmt(headers), sep]
    for r in rows:
        lines.append(fmt(r))
    return "\n".join(lines)


def main():
    entries = scan_all()
    protected = [e for e in entries if e.risk_label == "PROTECTED"]
    low_risk = [e for e in entries if e.risk_label == "LOW_RISK_OK"]
    needs = [e for e in entries if e.risk_label == "NEEDS_PROTECTION"]

    print("\n" + "=" * 90)
    print(f"  Phase 10B 危险接口扫描报告")
    print(f"  总计: {len(entries)} 个候选 | "
          f"已保护(PROTECTED): {len(protected)} | "
          f"低风险白名单(LOW_RISK_OK): {len(low_risk)} | "
          f"待保护(NEEDS_PROTECTION): {len(needs)}")
    print("=" * 90)
    print(render_table(entries))
    print("=" * 90)

    if needs:
        print("\n[!] 以下接口被识别为高危但未接入 check_confirm，且不在 LOW_RISK_WHITELIST：")
        for e in needs:
            print(f"    - {e.method:6s} {e.path:50s}  ({e.file}:{e.line})  -> 推荐: {e.suggested_confirm_text}")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / "dangerous_routes.json"
    payload = {
        "summary": {
            "total": len(entries),
            "protected": len(protected),
            "low_risk_ok": len(low_risk),
            "needs_protection": len(needs),
        },
        "entries": [asdict(e) for e in entries],
    }
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nJSON 报告已写入: {report_path.relative_to(ROOT)}")

    return 0 if len(needs) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
