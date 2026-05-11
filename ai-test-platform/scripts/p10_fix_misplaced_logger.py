"""Phase 10A 一次性脚本：修复 p10_print_to_logger.py 把 logger 插入到多行 import 内部的位置错误。

策略：
  1. 找到 'from xxx import (\nimport logging\n\nlogger = logging.getLogger(__name__)\n'
  2. 删除错放的 logger 块
  3. 在文件 docstring 之后、第一个 import 之前插入正确位置
"""
from __future__ import annotations
import re
import sys
import py_compile
from pathlib import Path

TARGETS = [
    "services/ai_report_analysis_service.py",
    "app/executor_v2/execution_engine.py",
    "routes/swagger_routes.py",
    "routes/batch_run_routes.py",
]

MISPLACED_RE = re.compile(
    r'(from [^\r\n]*import \()\r?\nimport logging\r?\n\r?\nlogger = logging\.getLogger\(__name__\)\r?\n',
    re.MULTILINE,
)


def find_insert_point(src: str) -> int:
    """在文件开头的 docstring/shebang 之后，第一个真正代码行之前找插入点。"""
    # 跳过 shebang
    idx = 0
    if src.startswith("#!"):
        nl = src.find("\n", idx)
        idx = nl + 1 if nl != -1 else len(src)
    # 跳过 encoding 注释
    while idx < len(src) and src[idx] == "#":
        nl = src.find("\n", idx)
        idx = nl + 1 if nl != -1 else len(src)
    # 跳过空行
    while idx < len(src) and src[idx] in ("\n", "\r"):
        idx += 1
    # 跳过 docstring
    triple = '"""'
    if src[idx:idx + 3] == triple:
        end = src.find(triple, idx + 3)
        if end != -1:
            end += 3
            nl = src.find("\n", end)
            idx = nl + 1 if nl != -1 else end
    # 跳过空行
    while idx < len(src) and src[idx] in ("\n", "\r"):
        idx += 1
    return idx


def fix_one(p: Path) -> bool:
    raw = p.read_bytes().decode("utf-8")
    m = MISPLACED_RE.search(raw)
    if not m:
        print(f"  NO_MATCH {p}")
        return False
    cleaned = MISPLACED_RE.sub(m.group(1) + "\n", raw, count=1)
    insert_pt = find_insert_point(cleaned)
    block = "import logging\n\nlogger = logging.getLogger(__name__)\n\n"
    fixed = cleaned[:insert_pt] + block + cleaned[insert_pt:]
    p.write_bytes(fixed.encode("utf-8"))
    try:
        py_compile.compile(str(p), doraise=True)
        print(f"  FIXED + COMPILED OK {p}")
        return True
    except py_compile.PyCompileError as e:
        print(f"  FIXED but COMPILE FAIL {p}: {str(e)[:200]}")
        return False


def main():
    root = Path(__file__).resolve().parent.parent
    ok = 0
    for rel in TARGETS:
        if fix_one(root / rel):
            ok += 1
    print(f"DONE {ok}/{len(TARGETS)}")
    return 0 if ok == len(TARGETS) else 1


if __name__ == "__main__":
    sys.exit(main())
