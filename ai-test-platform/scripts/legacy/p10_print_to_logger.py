"""Phase 10A 一次性脚本：将业务模块的 print() 改成 logger.info()。

策略：
  1. 仅处理 PRINT_TARGETS 列表中的文件
  2. 若文件未声明 logger，则自动插入 import logging + logger = logging.getLogger(__name__)
  3. 顶层 print(...) 全部替换为 logger.info(...)
  4. 不动 app/web/web_server.py（demo HTML 内联），不动 app/main.py（CLI 启动文件）

执行后保留脚本本身用于审计。
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

PRINT_TARGETS = [
    "routes/ai_routes.py",
    "services/execution_orchestrator.py",
    "services/swagger_service.py",
    "services/ai_report_analysis_service.py",
    "app/self_healing/self_healing_engine.py",
    "app/executor_v2/oauth2_token_fetcher.py",
    "app/pipeline/pipeline_orchestrator.py",
    "app/api_parser/swagger_api_parser.py",
    "app/api_test_generator/api_test_generator.py",
    "app/executor_v2/ai_assertion_gen.py",
    "app/executor_v2/execution_engine.py",
    "routes/ai_case_review_routes.py",
    "routes/case_execute_routes.py",
    "routes/code_compare_routes.py",
    "routes/demo_routes.py",
    "routes/swagger_routes.py",
    "routes/batch_run_routes.py",
    "routes/code_analysis_routes.py",
    "routes/report_routes.py",
    "app/api_server.py",
]

PRINT_RE = re.compile(r'(^[^\n]*?)\bprint\(', re.MULTILINE)


def has_logger(src: str) -> bool:
    return bool(re.search(r'^logger\s*=\s*logging\.getLogger', src, re.MULTILINE))


def has_logging_import(src: str) -> bool:
    return bool(re.search(r'^import\s+logging\s*$', src, re.MULTILINE))


def insert_logger(src: str) -> str:
    """在第一个 import 段后插入 logger 声明"""
    lines = src.split("\n")
    # 找最后一个 import 行
    last_import = -1
    for i, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            last_import = i
        elif last_import >= 0 and line.strip() and not (line.startswith("#") or line.startswith("import ") or line.startswith("from ")):
            break
    if last_import < 0:
        return src
    insert_lines = []
    if not has_logging_import(src):
        insert_lines.append("import logging")
    insert_lines.append("")
    insert_lines.append("logger = logging.getLogger(__name__)")
    new_lines = lines[:last_import + 1] + insert_lines + lines[last_import + 1:]
    return "\n".join(new_lines)


def replace_prints(src: str) -> tuple[str, int]:
    """把 print( 替换为 logger.info(，仅在不在字符串字面量中的情况"""
    count = 0

    def repl(m: re.Match) -> str:
        nonlocal count
        prefix = m.group(1) or ""
        # 跳过：注释 / 字符串中
        if "#" in prefix:
            return m.group(0)
        if prefix.count('"') % 2 != 0 or prefix.count("'") % 2 != 0:
            return m.group(0)
        count += 1
        return prefix + "logger.info("

    new = PRINT_RE.sub(repl, src)
    return new, count


def fix_file(p: Path) -> int:
    if not p.exists():
        print(f"  SKIP (missing): {p}")
        return 0
    raw = p.read_bytes()
    src = raw.decode("utf-8")
    if not has_logger(src):
        src = insert_logger(src)
    new, n = replace_prints(src)
    if n > 0:
        p.write_bytes(new.encode("utf-8"))
        print(f"  fixed {n} prints in {p}")
    else:
        print(f"  0 prints in {p}")
    return n


def main():
    total = 0
    root = Path(__file__).resolve().parent.parent
    for rel in PRINT_TARGETS:
        full = root / rel
        total += fix_file(full)
    print(f"DONE total replaced: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
