"""Phase 10A 一次性脚本：把 analytics_service.py 的静默 except 改为 logger.debug。

执行后即可删除（已在 task 完成清单中说明）。
"""
import re
import sys
from pathlib import Path


TARGET_FILES = [
    Path("services/analytics_service.py"),
    Path("services/code_compare_storage_service.py"),
    Path("services/test_selection_service.py"),
]

# 匹配:
#   except Exception:
#       pass
SILENT_RE = re.compile(
    r'except Exception:\n(?P<indent>\s+)pass',
)


def fix_file(p: Path, log_fn: str = "logger.debug"):
    if not p.exists():
        print(f"  SKIP (missing): {p}")
        return 0
    src = p.read_text(encoding="utf-8")
    count = 0

    def replace(m):
        nonlocal count
        count += 1
        indent = m.group("indent")
        return (
            "except Exception as _e:\n"
            f'{indent}{log_fn}("silent error suppressed at %s: %s", '
            f'__name__, _e)'
        )

    new = SILENT_RE.sub(replace, src)
    if count > 0:
        p.write_text(new, encoding="utf-8")
        print(f"  fixed {count} occurrences in {p}")
    else:
        print(f"  0 occurrences in {p}")
    return count


def main():
    total = 0
    root = Path(__file__).resolve().parent.parent
    for rel in TARGET_FILES:
        full = root / rel
        total += fix_file(full)
    print(f"DONE total replaced: {total}")
    return 0 if total >= 0 else 1


if __name__ == "__main__":
    sys.exit(main())
