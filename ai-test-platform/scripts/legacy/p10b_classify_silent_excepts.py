"""Phase 10B 一次性脚本：silent except 分级治理

策略：按文件 + 行号判定每个 silent except 的严重度，替换为对应日志级别。

  P0 — 数据完整性强相关（DB 写、文件删除、版本快照、baseline meta 写）
       → logger.exception("...", _e)  保留完整 traceback
  P1 — 第三方/可降级路径（webhook send、AI 检索、配置解析）
       → logger.warning("...: %s", _e)
  P2 — 兼容性兜底（资源关闭、JWT 解码可选解析等）
       → logger.debug("...: %s", _e)

匹配模式：
  except Exception:
      pass

替换为：
  except Exception as _e:
      <level>("[<grade>] <reason>: %s", _e)

执行后保留以便审计。
"""
from __future__ import annotations
import re
import sys
import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 文件级默认严重度（行级别可在 LINE_OVERRIDES 微调）
FILE_GRADE = {
    # P0 ─ 数据写入/删除关键路径
    "services/visual_baseline_service.py": ("P0", "baseline data write/delete"),
    "services/visual_diff.py":             ("P0", "baseline meta write"),
    # P1 ─ 第三方/缓存/容错路径
    "services/tapd_service.py":            ("P1", "tapd config read"),
    "services/quality_gate_service.py":    ("P1", "summary json parse"),
    "routes/ai_routes.py":                 ("P1", "knowledge base retrieve fallback"),
    "routes/code_compare_routes.py":       ("P1", "report/cache load fallback"),
    "routes/swagger_routes.py":            ("P1", "swagger schema parse"),
    "routes/case_execute_routes.py":       ("P1", "dataset lookup / jwt decode"),
    # P2 ─ 兼容性兜底
    "services/playwright_engine.py":       ("P2", "browser/pw cleanup"),
    "app/self_healing/self_healing_engine.py": ("P2", "self-healing fallback"),
    "backend/startup.py":                  ("P2", "startup probe fallback"),
}

# 关键行级覆盖：(file, line) → (grade, reason)
# 用于把同一文件中性质不同的 except 区分对待
LINE_OVERRIDES = {
    # visual_baseline_service.py: 第 296/339/497 行是 webhook 通知失败 → P1
    ("services/visual_baseline_service.py", 296): ("P1", "visual_notifier emit"),
    ("services/visual_baseline_service.py", 339): ("P1", "visual_notifier emit"),
    ("services/visual_baseline_service.py", 497): ("P1", "visual_notifier emit"),
    # visual_diff.py: 第 782/855 行是 webhook 通知；829 是 meta 写
    ("services/visual_diff.py", 782): ("P1", "visual_notifier emit"),
    ("services/visual_diff.py", 855): ("P1", "visual_notifier emit"),
    # visual_diff.py 第 133 行是 viewport 解析容错
    ("services/visual_diff.py", 133): ("P2", "viewport parse"),
}

GRADE_MAP = {
    "P0": "logger.exception",
    "P1": "logger.warning",
    "P2": "logger.debug",
}


SILENT_RE = re.compile(r"except Exception:\r?\n(?P<indent>[ \t]+)pass")


def patch_file(rel: str, grade_default: str, reason_default: str) -> tuple[int, int, int]:
    """处理单个文件，返回 (P0_count, P1_count, P2_count)"""
    p = ROOT / rel
    if not p.exists():
        print(f"  SKIP missing {rel}")
        return (0, 0, 0)
    raw = p.read_bytes().decode("utf-8")

    counters = {"P0": 0, "P1": 0, "P2": 0}

    # 检测主 EOL（CRLF 或 LF）
    eol = "\r\n" if raw.count("\r\n") > raw.count("\n") - raw.count("\r\n") else "\n"

    # 一边遍历一边替换：用 finditer + 反向构造
    parts: list[str] = []
    cursor = 0
    for m in SILENT_RE.finditer(raw):
        # 计算所在行号（1-indexed），对应 except 关键字所在行
        line = raw.count("\n", 0, m.start()) + 1
        key = (rel.replace("\\", "/"), line)
        grade, reason = LINE_OVERRIDES.get(key, (grade_default, reason_default))
        log_call = GRADE_MAP[grade]
        indent = m.group("indent")
        replacement = (
            f"except Exception as _e:{eol}"
            f'{indent}{log_call}("[{grade}] {reason}: %s", _e)'
        )
        parts.append(raw[cursor:m.start()])
        parts.append(replacement)
        cursor = m.end()
        counters[grade] += 1

    if cursor == 0:
        print(f"  -- 0 matches in {rel}")
        return (0, 0, 0)

    parts.append(raw[cursor:])
    new_src = "".join(parts)
    p.write_bytes(new_src.encode("utf-8"))

    # 编译验证
    try:
        py_compile.compile(str(p), doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  !! COMPILE FAIL {rel}: {str(e)[:200]}")
        return counters["P0"], counters["P1"], counters["P2"]

    print(f"  OK {rel:55s}  P0={counters['P0']} P1={counters['P1']} P2={counters['P2']}")
    return counters["P0"], counters["P1"], counters["P2"]


def main():
    total = {"P0": 0, "P1": 0, "P2": 0}
    for rel, (grade, reason) in FILE_GRADE.items():
        a, b, c = patch_file(rel, grade, reason)
        total["P0"] += a
        total["P1"] += b
        total["P2"] += c
    print(f"\nDONE  P0={total['P0']}  P1={total['P1']}  P2={total['P2']}  total={sum(total.values())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
