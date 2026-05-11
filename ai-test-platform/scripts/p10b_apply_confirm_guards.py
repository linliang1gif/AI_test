"""Phase 10B 一次性脚本：给 6 个 P0 高危路由接入 check_confirm 守卫。

策略：
  1. 在每个目标文件顶部 import 段补 `from backend.danger_guard import check_confirm, ConfirmRequest`
     和 `from fastapi import Body`（若未引入）
  2. 给目标函数签名追加 `body: Optional[ConfirmRequest] = Body(None)`
  3. 在函数体首行插入 check_confirm 调用 + body 默认实例化

目标：
  routes/project_config_routes.py
    - delete_project        → DELETE_PROJECT
    - delete_environment    → DELETE_ENVIRONMENT
  routes/test_data_routes.py
    - delete_dataset        → DELETE_DATASET
  routes/test_suite_routes.py
    - delete_suite          → DELETE_TEST_SUITE
  routes/executor_v2_routes.py
    - clear_all_auth_tokens → CLEAR_ALL_AUTH_TOKENS
  routes/swagger_routes.py
    - batch_delete_test_cases → BULK_DELETE_TEST_CASES

执行后保留脚本以便审计。
"""
from __future__ import annotations
import ast
import re
import sys
import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (function_name, confirm_text)
TARGETS = {
    "routes/project_config_routes.py": [
        ("delete_project", "DELETE_PROJECT"),
        ("delete_environment", "DELETE_ENVIRONMENT"),
    ],
    "routes/test_data_routes.py": [
        ("delete_dataset", "DELETE_DATASET"),
    ],
    "routes/test_suite_routes.py": [
        ("delete_suite", "DELETE_TEST_SUITE"),
    ],
    "routes/executor_v2_routes.py": [
        ("clear_all_auth_tokens", "CLEAR_ALL_AUTH_TOKENS"),
    ],
    "routes/swagger_routes.py": [
        ("batch_delete_test_cases", "BULK_DELETE_TEST_CASES"),
    ],
}


def _find_last_import_end_line(src: str) -> int:
    """用 ast 找出文件顶层 import 块的最后结束行（1-indexed），找不到返回 0。"""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return 0
    last = 0
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            end = getattr(node, "end_lineno", node.lineno) or node.lineno
            if end > last:
                last = end
        else:
            # 顶层 import 段被非 import 打断后停止扫描
            if last > 0:
                break
    return last


def ensure_imports(src: str) -> str:
    """补 from backend.danger_guard / Body / Optional 的 import"""
    needs_guard = "from backend.danger_guard" not in src and "check_confirm" not in src
    # 仅检查 from fastapi import 语句中是否有 Body
    needs_body = not re.search(r"from\s+fastapi\s+import\s+(?:\([^)]*\bBody\b[^)]*\)|[^\n]*\bBody\b)", src)
    needs_optional = not re.search(r"from\s+typing\s+import\s+(?:\([^)]*\bOptional\b[^)]*\)|[^\n]*\bOptional\b)", src)

    lines = src.split("\n")
    insertions: list[tuple[int, str]] = []

    # 用 ast 找真实 import 段末尾行
    last_imp_lineno = _find_last_import_end_line(src)
    last_imp = last_imp_lineno - 1  # 转 0-indexed

    # 处理 fastapi import 补 Body
    if needs_body:
        for i, ln in enumerate(lines):
            m = re.match(r"^(from\s+fastapi\s+import\s+)(.+)$", ln)
            if m:
                head, rest = m.group(1), m.group(2).rstrip()
                # 简单追加
                if "Body" not in rest:
                    if rest.endswith(")"):
                        rest = rest[:-1].rstrip().rstrip(",") + ", Body)"
                    else:
                        rest = rest + ", Body"
                lines[i] = head + rest
                needs_body = False
                break
        # 若仍需要（无 fastapi 导入行），在 last_imp 后追加
        if needs_body and last_imp >= 0:
            insertions.append((last_imp + 1, "from fastapi import Body"))

    # 处理 typing Optional 补充
    if needs_optional:
        for i, ln in enumerate(lines):
            m = re.match(r"^(from\s+typing\s+import\s+)(.+)$", ln)
            if m:
                head, rest = m.group(1), m.group(2).rstrip()
                if "Optional" not in rest:
                    rest = rest + ", Optional"
                lines[i] = head + rest
                needs_optional = False
                break
        if needs_optional and last_imp >= 0:
            insertions.append((last_imp + 1, "from typing import Optional"))

    # 处理 check_confirm
    if needs_guard and last_imp >= 0:
        insertions.append((last_imp + 1, "from backend.danger_guard import check_confirm, ConfirmRequest"))

    # 应用插入（按行号倒序）
    for idx, content in sorted(insertions, key=lambda x: -x[0]):
        lines.insert(idx, content)

    return "\n".join(lines)


def patch_function(src: str, fn_name: str, confirm_text: str) -> tuple[str, bool]:
    """给 fn_name 函数签名末尾追加 body 参数，并在函数体首行插入 check_confirm。"""
    # 查找 def 行（兼容 async def 与 多行参数）
    fn_def_re = re.compile(
        r"(?P<head>(?:async\s+)?def\s+" + re.escape(fn_name) + r"\s*\()(?P<args>.*?)(?P<close>\)\s*(?:->\s*[^:]+)?:\s*\n)",
        re.DOTALL,
    )
    m = fn_def_re.search(src)
    if not m:
        return src, False

    head, args, close = m.group("head"), m.group("args"), m.group("close")

    # 已经有 body: ConfirmRequest 就跳过
    if re.search(r"\bbody\s*:\s*Optional\[\s*ConfirmRequest", args) or "ConfirmRequest" in args:
        # 仍要确保函数体首行有 check_confirm
        pass
    else:
        # 在最后一个参数后追加 body
        # args 末尾可能有逗号或不有
        args_stripped = args.rstrip()
        sep = "," if args_stripped and not args_stripped.endswith(",") else ""
        new_args = args_stripped + f"{sep}\n    body: Optional[ConfirmRequest] = Body(None),\n"
        src = src[:m.start()] + head + new_args + close + src[m.end():]

    # 重新匹配定位函数体起始
    m2 = fn_def_re.search(src)
    if not m2:
        return src, True
    body_start = m2.end()
    # 跳过 docstring（如果有）
    after = src[body_start:]
    # 检测 leading whitespace
    indent_m = re.match(r"(\s*)", after)
    leading_ws = indent_m.group(1) if indent_m else ""
    rest = after[len(leading_ws):]
    if rest.startswith('"""') or rest.startswith("'''"):
        quote = rest[:3]
        end_doc = rest.find(quote, 3)
        if end_doc != -1:
            # docstring 结束位置
            doc_end_abs = body_start + len(leading_ws) + end_doc + 3
            # 跳过其后的换行
            tail = src[doc_end_abs:]
            nl = tail.find("\n")
            if nl != -1:
                body_start = doc_end_abs + nl + 1
            else:
                body_start = doc_end_abs

    # 检测函数体 indent（找 body_start 后第一行非空白行）
    after_body = src[body_start:]
    next_line_m = re.match(r"(\s*)(\S)", after_body)
    if not next_line_m:
        return src, True
    indent = next_line_m.group(1)
    indent = indent.replace("\n", "")  # 防止把换行当 indent

    # 检查是否已经有 check_confirm
    inserted = f'{indent}# Phase 10B: 危险操作守卫\n{indent}check_confirm("{confirm_text}", (body or ConfirmRequest()).confirm, (body or ConfirmRequest()).confirm_text)\n'

    # 取函数前 600 字节，看是否已经接入
    fn_head_src = src[m2.start():body_start + 800]
    if "check_confirm(" in fn_head_src:
        return src, True

    src = src[:body_start] + inserted + src[body_start:]
    return src, True


def process_file(rel: str, fns: list[tuple[str, str]]):
    p = ROOT / rel
    src = p.read_bytes().decode("utf-8")
    orig = src
    src = ensure_imports(src)
    patched_count = 0
    for fn_name, ct in fns:
        src, ok = patch_function(src, fn_name, ct)
        if ok:
            patched_count += 1
            print(f"  patched {rel}::{fn_name} → {ct}")
        else:
            print(f"  MISSING {rel}::{fn_name}")
    if src != orig:
        p.write_bytes(src.encode("utf-8"))
    # 编译验证
    try:
        py_compile.compile(str(p), doraise=True)
        print(f"  COMPILE OK {rel}")
    except py_compile.PyCompileError as e:
        print(f"  COMPILE FAIL {rel}: {str(e)[:200]}")
        return False
    return True


def main():
    ok = True
    for rel, fns in TARGETS.items():
        if not process_file(rel, fns):
            ok = False
    print(f"\nDONE {'all OK' if ok else 'with failures'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
