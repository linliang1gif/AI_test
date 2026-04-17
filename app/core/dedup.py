from __future__ import annotations

import re
from collections import Counter
from typing import Dict, List, Set, Tuple


# ── Stopwords for Chinese test case titles ──────────────────────────────────
_STOPWORDS: Set[str] = {
    "验证", "测试", "检查", "确认", "的", "了", "在", "是", "和", "与",
    "进行", "操作", "功能", "系统", "用户", "页面", "界面", "模块",
    "能否", "是否", "正确", "正常", "成功", "失败",
}


def _tokenize(text: str) -> List[str]:
    """Simple tokenization: split Chinese text into meaningful segments."""
    if not text:
        return []
    # Remove punctuation
    text = re.sub(r"[，。、；：！？\s\-—·\"\"''（）()\[\]【】{}]", " ", text)
    # Split into segments (Chinese chars individually, English words together)
    tokens = []
    for segment in text.split():
        segment = segment.strip()
        if not segment:
            continue
        # For mixed text, extract Chinese bigrams + English words
        if any("\u4e00" <= c <= "\u9fff" for c in segment):
            chars = [c for c in segment if "\u4e00" <= c <= "\u9fff"]
            # Use bigrams for Chinese
            for i in range(len(chars)):
                if chars[i] not in _STOPWORDS:
                    tokens.append(chars[i])
            for i in range(len(chars) - 1):
                bigram = chars[i] + chars[i + 1]
                tokens.append(bigram)
        else:
            tokens.append(segment.lower())
    return tokens


def _keyword_similarity(a: str, b: str) -> float:
    """Keyword-based similarity using token overlap (better than char Jaccard)."""
    tokens_a = _tokenize(a)
    tokens_b = _tokenize(b)
    if not tokens_a or not tokens_b:
        return 0.0

    counter_a = Counter(tokens_a)
    counter_b = Counter(tokens_b)

    # Weighted intersection
    intersection = sum((counter_a & counter_b).values())
    union = sum((counter_a | counter_b).values())

    return intersection / union if union else 0.0


def deduplicate_cases(
    cases: List[Dict[str, str]], threshold: float = 0.75
) -> List[Dict[str, str]]:
    """Remove near-duplicate test cases based on title + steps similarity.

    Uses keyword-based similarity which is more accurate than character Jaccard.
    Considers both title and steps to catch cases with different titles but same content.
    """
    if not cases:
        return cases

    unique: List[Dict[str, str]] = []
    seen: List[Tuple[str, str]] = []  # (title, steps) pairs

    for case in cases:
        title = case.get("用例标题", "").strip()
        steps = case.get("测试步骤", "").strip()
        if not title:
            unique.append(case)
            continue

        is_dup = False
        for seen_title, seen_steps in seen:
            title_sim = _keyword_similarity(title, seen_title)
            if title_sim >= threshold:
                is_dup = True
                break
            # Also check if steps are nearly identical (different title, same test)
            if steps and seen_steps:
                steps_sim = _keyword_similarity(steps, seen_steps)
                if steps_sim >= 0.85:
                    is_dup = True
                    break

        if not is_dup:
            unique.append(case)
            seen.append((title, steps))

    return unique


def validate_cases(cases: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Validate and fix common issues in parsed test cases."""
    validated: List[Dict[str, str]] = []
    for case in cases:
        cleaned: Dict[str, str] = {}
        cleaned["功能点"] = case.get("功能点", "").strip() or _extract_function_point(
            case.get("用例标题", "")
        )
        cleaned["用例标题"] = case.get("用例标题", "").strip()
        cleaned["前置条件"] = case.get("前置条件", "").strip() or "无"
        cleaned["测试步骤"] = _clean_steps(case.get("测试步骤", ""))
        cleaned["预期结果"] = case.get("预期结果", "").strip()
        cleaned["优先级"] = _normalize_priority(case.get("优先级", "中"))
        cleaned["覆盖维度"] = case.get("覆盖维度", "").strip()

        if not cleaned["用例标题"]:
            continue

        validated.append(cleaned)
    return validated


def analyze_coverage(cases: List[Dict[str, str]]) -> Dict[str, object]:
    """Analyze test coverage dimensions and generate a quality report."""
    total = len(cases)
    if total == 0:
        return {"total": 0, "dimensions": {}, "priority_dist": {}, "quality_score": 0}

    # Count by dimension
    dim_counts: Counter = Counter()
    for case in cases:
        dim = case.get("覆盖维度", "").strip() or "未分类"
        dim_counts[dim] += 1

    # Count by priority
    pri_counts: Counter = Counter()
    for case in cases:
        pri = case.get("优先级", "中").strip()
        pri_counts[pri] += 1

    # Expected dimensions for a thorough test suite
    expected_dims = {
        "正向流程", "字段校验", "边界值", "状态流转",
        "权限控制", "批量操作", "数据一致性", "异常处理",
    }
    covered_dims = set(dim_counts.keys()) - {"未分类"}
    missing_dims = expected_dims - covered_dims

    # Quality score (0-100)
    dim_coverage = len(covered_dims & expected_dims) / len(expected_dims) * 40
    quantity_score = min(total / 15, 1.0) * 30  # 15+ cases = full score
    priority_balance = min(pri_counts.get("高", 0) / max(total * 0.2, 1), 1.0) * 15
    has_steps = sum(1 for c in cases if c.get("测试步骤", "").strip()) / total * 15
    quality_score = round(dim_coverage + quantity_score + priority_balance + has_steps)

    return {
        "total": total,
        "dimensions": dict(dim_counts),
        "priority_dist": dict(pri_counts),
        "missing_dimensions": sorted(missing_dims),
        "quality_score": min(quality_score, 100),
    }


def _extract_function_point(title: str) -> str:
    """Extract a short function point from the case title."""
    if not title:
        return "功能验证"
    title = title.strip()
    if title.startswith("验证"):
        title = title[2:].strip()
    for sep in ["时", "后", "，", ","]:
        if sep in title:
            title = title.split(sep, 1)[0].strip()
            break
    if len(title) > 20:
        title = title[:20]
    return title or "功能验证"


def _clean_steps(steps: str) -> str:
    """Ensure steps are properly formatted with Step numbering."""
    if not steps or not steps.strip():
        return ""
    lines = steps.strip().splitlines()
    cleaned = []
    step_num = 1
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if not re.match(r"^[Ss]tep\s*\d", line):
            line = f"Step{step_num}. {line}"
        step_num += 1
        cleaned.append(line)
    return "\n".join(cleaned)


def _normalize_priority(raw: str) -> str:
    """Normalize priority to 高/中/低."""
    raw = raw.strip()
    if raw in ("高", "高优先级", "P0", "P1", "critical", "high"):
        return "高"
    if raw in ("低", "低优先级", "P3", "P4", "low"):
        return "低"
    return "中"
