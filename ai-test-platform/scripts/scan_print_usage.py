"""Phase 10B print 使用扫描脚本

策略：
  禁止目录（业务代码必须 0 print）：
    routes/
    services/
    backend/
    app/executor_v2/
    app/self_healing/

  白名单（允许保留 print）：
    scripts/
    app/main.py
    app/web/web_server.py
    archive/
    其余 app/* 子模块（CLI/工具）按需放行，扫描时报告但不计违规

排除：
  archive/、frontend/、node_modules/、tests/、__pycache__/、.venv/、.git/、dist/、build/

输出：
  - 终端报告
  - JSON 报告 data/reports/print_usage.json
  - 退出码：0 全部合规 / 1 禁止目录存在 print
"""
from __future__ import annotations
import ast
import json
import os
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT / "data" / "reports"

# 必须为 0 print 的目录（违规即报错）
FORBIDDEN_DIRS = [
    "routes",
    "services",
    "backend",
    "app/executor_v2",
    "app/self_healing",
]

# 允许 print 的白名单文件/目录（仅作记录，不算违规）
WHITELIST_PATHS = [
    "scripts/",        # 一次性脚本
    "app/main.py",     # CLI 启动
    "app/web/",        # demo web server
    "archive/",        # 历史备份
]

# 扫描时排除目录
EXCLUDE_DIRS = {"archive", "scripts", "frontend", "node_modules",
                ".venv", "venv", "__pycache__", ".git", "dist", "build", "tests"}


@dataclass
class PrintUsage:
    file: str
    line: int
    col: int
    snippet: str


def find_prints_in_file(p: Path) -> List[PrintUsage]:
    try:
        src = p.read_bytes().decode("utf-8", errors="replace")
        tree = ast.parse(src)
    except (SyntaxError, UnicodeDecodeError):
        return []
    items: List[PrintUsage] = []
    lines = src.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name) and f.id == "print":
                ln = node.lineno
                snippet = lines[ln - 1].strip() if 0 < ln <= len(lines) else ""
                items.append(PrintUsage(
                    file=str(p.relative_to(ROOT)).replace("\\", "/"),
                    line=ln,
                    col=node.col_offset,
                    snippet=snippet[:160],
                ))
    return items


def is_forbidden(rel: str) -> bool:
    rel = rel.replace("\\", "/")
    for d in FORBIDDEN_DIRS:
        if rel.startswith(d.rstrip("/") + "/") or rel == d:
            return True
    return False


def is_whitelisted(rel: str) -> bool:
    rel = rel.replace("\\", "/")
    for w in WHITELIST_PATHS:
        if w.endswith("/"):
            if rel.startswith(w):
                return True
        else:
            if rel == w:
                return True
    return False


def scan_all() -> tuple[List[PrintUsage], List[PrintUsage], List[PrintUsage]]:
    """返回 (forbidden_violations, whitelist_allowed, other_observed)"""
    forbidden: List[PrintUsage] = []
    whitelist: List[PrintUsage] = []
    other: List[PrintUsage] = []

    for p, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            if not f.endswith(".py"):
                continue
            full = Path(p) / f
            rel = str(full.relative_to(ROOT)).replace("\\", "/")
            uses = find_prints_in_file(full)
            if not uses:
                continue
            if is_forbidden(rel):
                forbidden.extend(uses)
            elif is_whitelisted(rel):
                whitelist.extend(uses)
            else:
                other.extend(uses)
    return forbidden, whitelist, other


def render(uses: List[PrintUsage], limit: int = 200) -> str:
    by_file: dict[str, List[PrintUsage]] = {}
    for u in uses:
        by_file.setdefault(u.file, []).append(u)
    lines = []
    for f, items in sorted(by_file.items()):
        lines.append(f"  {f}  ({len(items)} prints)")
        for u in items[:5]:
            lines.append(f"    L{u.line:5d}: {u.snippet}")
        if len(items) > 5:
            lines.append(f"    ...({len(items) - 5} more)")
    return "\n".join(lines) if lines else "  (none)"


def main():
    forbidden, whitelist, other = scan_all()

    print("\n" + "=" * 90)
    print("  Phase 10B print 使用扫描报告")
    print("=" * 90)
    print(f"\n[FORBIDDEN] 业务目录违规 print: {len(forbidden)} (期望 0)")
    print(render(forbidden))

    print(f"\n[WHITELIST] 白名单允许的 print: {len(whitelist)}")
    print(render(whitelist))

    print(f"\n[OTHER] 其他位置（非违规非白名单，建议关注）: {len(other)}")
    print(render(other))

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = REPORT_DIR / "print_usage.json"
    report.write_text(json.dumps({
        "summary": {
            "forbidden_count": len(forbidden),
            "whitelist_count": len(whitelist),
            "other_count": len(other),
            "forbidden_dirs": FORBIDDEN_DIRS,
            "whitelist_paths": WHITELIST_PATHS,
        },
        "forbidden": [asdict(u) for u in forbidden],
        "whitelist": [asdict(u) for u in whitelist],
        "other": [asdict(u) for u in other],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nJSON 报告: {report.relative_to(ROOT)}")

    print("\n" + "=" * 90)
    if forbidden:
        print(f"  [FAIL] 业务目录仍有 {len(forbidden)} 处 print，必须改为 logger.*")
        return 1
    print("  [PASS] 业务目录无 print 违规")
    return 0


if __name__ == "__main__":
    sys.exit(main())
