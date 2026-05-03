"""
P2-9B: Web UI 稳定性增强
- selector 稳定性评分
- 等待策略分析
- 执行前环境检查
- retry / flaky 辅助
"""
import os
import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# ── Selector 稳定性评分 ──

HIGH_STABILITY_PATTERNS = [
    (r'\[data-testid[=~]', 100, "data-testid 选择器"),
    (r'\[data-test[=~]', 100, "data-test 选择器"),
    (r'\[role[=~]', 95, "ARIA role 选择器"),
    (r'\[aria-label[=~]', 95, "aria-label 选择器"),
]

MEDIUM_STABILITY_PATTERNS = [
    (r'^#[\w-]+$', 80, "ID 选择器"),
    (r'\[name[=~]', 75, "name 属性选择器"),
    (r'\[placeholder[=~]', 70, "placeholder 选择器"),
    (r'^input\[type=', 70, "input type 选择器"),
]

LOW_STABILITY_PATTERNS = [
    (r':nth-child\(', 30, "使用 nth-child，页面结构变化时容易失效"),
    (r'^//', 20, "绝对 XPath，DOM 变化时极易失效"),
    (r'xpath=', 20, "XPath 选择器，不推荐使用"),
    (r'(div\s*>\s*){3,}', 25, "深层级 CSS 嵌套，结构变化时容易失效"),
    (r'\.\w{6,}(?:\s|$|>)', 35, "可能包含动态生成的 class name"),
]


def score_selector(selector: str) -> dict:
    """对单个 selector 评分，返回 {score, reason, level}"""
    if not selector or not selector.strip():
        return {"score": 50, "reason": "空选择器", "level": "medium"}

    s = selector.strip()

    # 纯数字 = wait_for timeout
    if s.isdigit():
        return {"score": 50, "reason": "数值(超时/等待)", "level": "medium"}

    # Check high stability patterns
    for pattern, score, reason in HIGH_STABILITY_PATTERNS:
        if re.search(pattern, s, re.IGNORECASE):
            return {"score": score, "reason": reason, "level": "high"}

    # Check low stability patterns first (override medium)
    for pattern, score, reason in LOW_STABILITY_PATTERNS:
        if re.search(pattern, s, re.IGNORECASE):
            return {"score": score, "reason": reason, "level": "low"}

    # Check medium stability patterns
    for pattern, score, reason in MEDIUM_STABILITY_PATTERNS:
        if re.search(pattern, s, re.IGNORECASE):
            return {"score": score, "reason": reason, "level": "medium"}

    # Default: simple CSS selector
    if re.match(r'^[\w.#\[\]="\'-]+$', s):
        return {"score": 65, "reason": "标准 CSS 选择器", "level": "medium"}

    return {"score": 55, "reason": "复合选择器", "level": "medium"}


def analyze_selectors(steps: List[Dict[str, Any]]) -> dict:
    """分析所有步骤的 selector 稳定性"""
    unstable = []
    scores = []
    for idx, step in enumerate(steps):
        action = step.get("action", "")
        target = step.get("target", "")
        # skip non-selector actions
        if action in ("screenshot", "switch_main") or not target:
            continue
        if action == "wait_for" and target.isdigit():
            continue  # pure timeout, scored elsewhere

        result = score_selector(target)
        scores.append(result["score"])
        if result["level"] == "low":
            unstable.append({
                "step_index": idx,
                "target": target,
                "score": result["score"],
                "reason": result["reason"],
            })

    avg_score = round(sum(scores) / len(scores)) if scores else 100
    return {
        "selector_score": avg_score,
        "unstable_selectors": unstable,
        "total_scored": len(scores),
        "low_score_count": len(unstable),
    }


# ── 等待策略分析 ──

def analyze_wait_strategies(steps: List[Dict[str, Any]]) -> dict:
    """分析步骤中的等待策略，标记低稳定等待"""
    warnings = []
    for idx, step in enumerate(steps):
        action = step.get("action", "")
        target = step.get("target", "")
        value = step.get("value", "")

        if action != "wait_for":
            continue

        # 纯固定等待
        if target.isdigit():
            ms = int(target)
            if ms >= 3000:
                warnings.append({
                    "step_index": idx,
                    "type": "fixed_timeout",
                    "target": target,
                    "reason": f"固定等待 {ms}ms，建议使用 wait_for_selector 或 wait_for_text",
                    "severity": "medium" if ms < 5000 else "high",
                })
            continue

        # Enhanced wait strategies (P2-9B)
        if value in ("visible", "attached", "detached", "hidden"):
            continue  # good: wait_for_selector with state
        if value == "url_contains":
            continue  # good: wait for URL
        if value == "text_visible":
            continue  # good: wait for text
        if value == "network_idle":
            continue  # reserved for future
        # Default: wait_for_selector (acceptable)

    return {
        "wait_strategy_warnings": warnings,
        "warning_count": len(warnings),
    }


# ── 执行前环境检查 ──

def preflight_check(
    case_type: str,
    steps: List[Dict[str, Any]],
    assertions: List[Dict[str, Any]],
    execution_config: Dict[str, Any],
) -> dict:
    """执行前检查，返回 {ok, errors, warnings}"""
    errors = []
    warnings = []

    # 1. case_type check
    if case_type != "web_ui":
        errors.append(f"用例类型 '{case_type}' 不是 web_ui，不能使用 Playwright 引擎执行")

    # 2. steps check
    if not steps:
        errors.append("用例步骤为空，无法执行")

    # 3. assertions check
    if not assertions:
        warnings.append("用例未配置断言，执行后无法验证结果正确性")

    # 4. base_url check
    base_url = execution_config.get("base_url", "")
    has_goto = any(s.get("action") == "goto" for s in (steps or []))
    if has_goto and not base_url:
        # Check if all goto use absolute URLs
        gotos = [s for s in (steps or []) if s.get("action") == "goto"]
        relative = [s for s in gotos if not s.get("target", "").startswith(("http://", "https://"))]
        if relative:
            warnings.append("存在相对路径 goto 但未配置 base_url，可能导致导航失败")

    # 5. base_url reachability (lightweight check)
    if base_url:
        try:
            import urllib.request
            urllib.request.urlopen(base_url, timeout=5)
        except Exception as e:
            warnings.append(f"base_url ({base_url}) 可能不可访问: {str(e)[:100]}")

    # 6. browser availability
    try:
        from services.playwright_engine import _is_playwright_available
        if not _is_playwright_available():
            errors.append("Playwright 未安装。请运行: pip install playwright && python -m playwright install chromium")
    except ImportError:
        errors.append("playwright_engine 模块不可用")

    # 7. trace directory writable
    enable_trace = execution_config.get("enable_trace", True)
    if enable_trace:
        trace_dir = os.path.join("data", "artifacts", "ui", "traces")
        try:
            os.makedirs(trace_dir, exist_ok=True)
            test_file = os.path.join(trace_dir, ".write_test")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
        except Exception:
            warnings.append(f"Trace 目录 ({trace_dir}) 不可写，trace 功能可能不可用")

    # 8. screenshot directory writable
    ss_dir = os.path.join("data", "artifacts", "ui", "screenshots")
    try:
        os.makedirs(ss_dir, exist_ok=True)
        test_file = os.path.join(ss_dir, ".write_test")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
    except Exception:
        warnings.append(f"截图目录 ({ss_dir}) 不可写，截图功能可能不可用")

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


# ── Retry / Flaky 辅助 ──

def categorize_failure(error_message: str) -> str:
    """将失败信息归类到可重试类别"""
    if not error_message:
        return "unknown"
    msg = error_message.lower()
    if any(k in msg for k in ("timeout", "超时", "timed out")):
        return "page_timeout"
    if any(k in msg for k in ("network", "net::", "err_connection", "dns", "fetch")):
        return "network_error"
    if any(k in msg for k in ("未找到", "not found", "no element", "not visible")):
        return "selector_not_found"
    if any(k in msg for k in ("crash", "context", "closed", "target closed")):
        return "browser_crash"
    if any(k in msg for k in ("navigation", "导航", "重定向", "redirect")):
        return "navigation_error"
    return "unknown"


def should_retry(failure_category: str, retry_on: List[str]) -> bool:
    """判断给定失败类别是否在 retry_on 列表中"""
    return failure_category in retry_on
