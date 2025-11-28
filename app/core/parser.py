from __future__ import annotations

import re
from typing import Dict, List


def _strip_markup(text: str) -> str:
    text = text.replace("：**", "：").replace("**：", "：").replace("**", "")
    text = text.replace("__", "")
    text = re.sub(r"`([^`]*)`", r"\1", text)
    return text.strip()


def _normalize_markdown_blocks(lines: List[str]) -> List[str]:
    normalized: List[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        stripped = stripped.lstrip("-•").strip()
        heading_match = re.match(r"^#{2,4}\s*(TC-[0-9]+)", stripped)
        if heading_match:
            normalized.append(f"用例编号：{heading_match.group(1)}")
            continue
        normalized.append(stripped)
    return normalized


def normalize_output(ai_output: str) -> str:
    """Ensure numbering/labels exist to simplify downstream parsing."""
    fixed_lines: List[str] = []
    raw_lines = ai_output.splitlines()
    lines = _normalize_markdown_blocks(raw_lines)
    case_id = 1

    for raw in lines:
        line = _strip_markup(raw)
        if not line:
            continue
        if re.match(r"^用例编号", line):
            if "TC-" not in line:
                fixed_lines.append(f"用例编号：TC-{case_id:03d}")
            else:
                fixed_lines.append(line)
            case_id += 1
        elif line.startswith("功能点") and "：" not in line:
            fixed_lines.append("功能点：" + line.replace("功能点", "").strip())
        elif line.startswith("功能点"):
            fixed_lines.append(line)
        elif line.startswith("用例标题") and "：" not in line:
            fixed_lines.append("用例标题：" + line.replace("用例标题", "").strip())
        elif line.startswith("用例标题"):
            fixed_lines.append(line)
        elif line.startswith("前置条件") and "：" not in line:
            fixed_lines.append("前置条件：" + line.replace("前置条件", "").strip())
        elif line.startswith("前置条件"):
            fixed_lines.append(line)
        elif line.startswith("测试步骤") and "：" not in line:
            fixed_lines.append("测试步骤：")
        elif line.startswith("测试步骤"):
            fixed_lines.append(line)
        elif line.startswith("预期结果") and "：" not in line:
            fixed_lines.append("预期结果：" + line.replace("预期结果", "").strip())
        elif line.startswith("预期结果"):
            fixed_lines.append(line)
        elif line.startswith("优先级") and "：" not in line:
            fixed_lines.append("优先级：" + line.replace("优先级", "").strip())
        elif line.startswith("优先级"):
            fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    return "\n".join(fixed_lines)


def parse_cases(ai_output: str) -> List[Dict[str, str]]:
    """Parse normalized AI output into structured test cases."""
    cases: List[Dict[str, str]] = []
    current: Dict[str, str] = {}
    in_expected_result = False

    lines = ai_output.splitlines()
    i = 0
    while i < len(lines):
        raw = lines[i]
        line = _strip_markup(raw)
        if not line:
            i += 1
            continue
        
        if line.startswith("用例编号"):
            if current:
                cases.append(current)
                current = {}
            in_expected_result = False
            current["用例编号"] = line.split("：", 1)[-1].strip()
        elif line.startswith("功能点"):
            in_expected_result = False
            current["功能点"] = line.split("：", 1)[-1].strip().lstrip(":")
        elif line.startswith("用例标题"):
            in_expected_result = False
            current["用例标题"] = line.split("：", 1)[-1].strip().lstrip(":")
        elif line.startswith("前置条件"):
            in_expected_result = False
            content = line.split("：", 1)[-1].strip().lstrip(":")
            if content:
                current["前置条件"] = content
            else:
                current["前置条件"] = ""
        elif re.match(r"^[0-9]+\.", line) and "前置条件" in current and "测试步骤" not in current:
            in_expected_result = False
            current["前置条件"] = current.get("前置条件", "") + "\n" + line
        elif line.startswith("测试步骤"):
            in_expected_result = False
            current["测试步骤"] = ""
        elif line.startswith("Step"):
            in_expected_result = False
            current["测试步骤"] = current.get("测试步骤", "") + line + "\n"
        elif line.startswith("预期结果"):
            in_expected_result = True
            content = line.split("：", 1)[-1].strip().lstrip(":")
            if content:
                current["预期结果"] = content
            else:
                current["预期结果"] = ""
        elif in_expected_result:
            if line.startswith("用例编号"):
                in_expected_result = False
                if current:
                    cases.append(current)
                    current = {}
                current["用例编号"] = line.split("：", 1)[-1].strip()
            elif line.startswith("优先级"):
                in_expected_result = False
                current["优先级"] = line.split("：", 1)[-1].strip()
            else:
                line_stripped = line.strip()
                if line_stripped:
                    if current.get("预期结果"):
                        current["预期结果"] += "\n" + line_stripped
                    else:
                        current["预期结果"] = line_stripped
        elif line.startswith("优先级"):
            in_expected_result = False
            current["优先级"] = line.split("：", 1)[-1].strip()
        i += 1
    
    if current:
        cases.append(current)
    return cases


