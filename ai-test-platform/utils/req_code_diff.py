#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
需求-代码对比引擎

流程:
1. 解析需求文档 → 功能点清单 A
2. 解析代码仓库 → 实现清单 B
3. AI 交叉对比 → 差异报告 (A∩B, A-B, B-A)
4. 输出 Bug 清单 + 测试用例建议
"""

import json
from typing import Dict, Any, Optional, List
from pathlib import Path


def run_req_code_diff(
    requirement_data: Dict[str, Any],
    code_analysis: Dict[str, Any],
    ai_client=None,
    max_prompt_chars: int = 12000,
) -> Dict[str, Any]:
    """
    执行需求-代码对比分析

    Args:
        requirement_data: document_parser 的 structured 输出
        code_analysis: code_analyzer 的 scan 输出
        ai_client: AI 客户端实例，None 时走规则匹配
        max_prompt_chars: prompt 最大字符数

    Returns:
        {
            "summary": { "total_req_points", "total_code_items", "matched", "unimplemented", "extra_code" },
            "matched": [ { "requirement", "code_item", "status", "notes" } ],
            "unimplemented": [ { "requirement", "severity", "suggestion" } ],
            "extra_code": [ { "code_item", "file", "notes" } ],
            "bugs": [ { "title", "severity", "steps", "expected", "actual" } ],
            "test_suggestions": [ { "title", "priority", "test_points" } ],
        }
    """
    # 1. 提取需求功能点
    req_points = _extract_requirement_points(requirement_data)

    # 2. 提取代码实现清单
    code_items = _extract_code_items(code_analysis)

    # 3. 对比
    if ai_client:
        result = _ai_diff(req_points, code_items, code_analysis, ai_client, max_prompt_chars)
        return result
    else:
        result = _rule_based_diff(req_points, code_items)
        result["_ai_fallback"] = False
        return result


def _extract_requirement_points(req_data: Dict) -> List[Dict]:
    """从需求文档结构化数据中提取功能点清单"""
    points = []

    # 从 features 提取
    for feat in req_data.get("features", []):
        points.append({
            "id": f"REQ_{len(points)+1:03d}",
            "name": feat.get("name", ""),
            "source": "feature",
            "detail": feat.get("description", feat.get("name", "")),
        })

    # 从 axure_notes 提取
    for note in req_data.get("axure_notes", []):
        points.append({
            "id": f"REQ_{len(points)+1:03d}",
            "name": note[:60],
            "source": "axure_note",
            "detail": note,
        })

    # 从 rules 提取
    for rule in req_data.get("rules", []):
        points.append({
            "id": f"REQ_{len(points)+1:03d}",
            "name": rule[:60],
            "source": "business_rule",
            "detail": rule,
        })

    # 从 fields 提取
    for field in req_data.get("fields", []):
        name = field.get("name", "")
        ftype = field.get("type", "")
        required = "必填" if field.get("required") else "选填"
        points.append({
            "id": f"REQ_{len(points)+1:03d}",
            "name": f"表单字段: {name} ({ftype}, {required})",
            "source": "field",
            "detail": f"字段 {name}，类型 {ftype}，{required}",
        })

    return points


def _extract_code_items(code_data: Dict) -> List[Dict]:
    """从代码分析结果中提取实现清单"""
    items = []

    # 组件
    for comp in code_data.get("components", []):
        methods = comp.get("methods", [])
        fields = comp.get("data_fields", [])
        items.append({
            "id": f"CODE_{len(items)+1:03d}",
            "name": comp["name"],
            "type": comp.get("type", "component"),
            "file": comp.get("file", ""),
            "detail": f"组件 {comp['name']}，方法: {', '.join(methods[:10])}，字段: {', '.join(fields[:10])}",
            "methods": methods,
            "fields": fields,
            "conditions": comp.get("template_conditions", []),
        })

    # 路由
    for route in code_data.get("routes", []):
        items.append({
            "id": f"CODE_{len(items)+1:03d}",
            "name": f"{route['method']} {route['path']}",
            "type": "api_route",
            "file": route.get("file", ""),
            "detail": f"API 路由 {route['method']} {route['path']} → {route.get('handler', '')}",
        })

    return items


def _rule_based_diff(req_points: List[Dict], code_items: List[Dict]) -> Dict:
    """基于规则的简单对比（不用 AI）"""
    matched = []
    unimplemented = []
    extra_code = []

    code_names = {item["name"].lower() for item in code_items}
    code_details = " ".join(item.get("detail", "") for item in code_items).lower()
    req_matched_codes = set()

    for req in req_points:
        req_name = req["name"].lower()
        req_keywords = set(re.findall(r'[\u4e00-\u9fff]+|\w{3,}', req_name))

        found = False
        for ci in code_items:
            ci_text = (ci["name"] + " " + ci.get("detail", "")).lower()
            # 关键词匹配
            overlap = sum(1 for kw in req_keywords if kw in ci_text)
            if overlap >= max(1, len(req_keywords) // 3):
                matched.append({
                    "requirement": req["name"],
                    "req_id": req["id"],
                    "code_item": ci["name"],
                    "code_id": ci["id"],
                    "file": ci.get("file", ""),
                    "status": "可能已实现",
                    "confidence": min(overlap / max(len(req_keywords), 1), 1.0),
                    "notes": f"关键词匹配 {overlap}/{len(req_keywords)}",
                })
                req_matched_codes.add(ci["id"])
                found = True
                break

        if not found:
            unimplemented.append({
                "requirement": req["name"],
                "req_id": req["id"],
                "severity": "medium",
                "suggestion": f"需求 '{req['name']}' 在代码中未找到对应实现",
            })

    for ci in code_items:
        if ci["id"] not in req_matched_codes:
            extra_code.append({
                "code_item": ci["name"],
                "code_id": ci["id"],
                "file": ci.get("file", ""),
                "notes": "代码中存在但需求文档中未提及",
            })

    return {
        "summary": {
            "total_req_points": len(req_points),
            "total_code_items": len(code_items),
            "matched": len(matched),
            "unimplemented": len(unimplemented),
            "extra_code": len(extra_code),
        },
        "matched": matched,
        "unimplemented": unimplemented,
        "extra_code": extra_code,
        "bugs": [],
        "test_suggestions": [],
    }


import re


def _ai_call_with_timeout(ai_client, prompt, system_prompt, timeout=180, max_tokens=8000):
    """带超时的 AI 调用"""
    import threading
    ai_response = [None]
    ai_error = [None]

    def _call():
        try:
            ai_response[0] = ai_client.generate_text(
                prompt=prompt, system_prompt=system_prompt,
                temperature=0.1, max_tokens=max_tokens,
            )
        except Exception as ex:
            ai_error[0] = ex

    t = threading.Thread(target=_call, daemon=True)
    t.start()
    t.join(timeout=timeout)
    if t.is_alive():
        raise TimeoutError(f"AI 调用超时 ({timeout}s)")
    if ai_error[0]:
        raise ai_error[0]
    return ai_response[0]


def _parse_ai_json(response: str) -> dict:
    """从 AI 响应中提取 JSON"""
    if not response:
        raise ValueError("AI 返回空响应")
    if '```json' in response:
        response = response.split('```json')[1].split('```')[0].strip()
    elif '```' in response:
        parts = response.split('```')
        if len(parts) >= 3:
            response = parts[1].strip()
    start = response.find('{')
    end = response.rfind('}') + 1
    if start != -1 and end > start:
        return json.loads(response[start:end])
    # 尝试找数组
    start = response.find('[')
    end = response.rfind(']') + 1
    if start != -1 and end > start:
        return {"items": json.loads(response[start:end])}
    return json.loads(response)


def _ai_diff(
    req_points: List[Dict],
    code_items: List[Dict],
    code_analysis: Dict,
    ai_client,
    max_chars: int,
) -> Dict:
    """使用 AI 做深度对比分析 —— 分批逐组对比，确保每条需求都被仔细检查"""
    from utils.code_analyzer import summarize_code_analysis

    # ── 1. 构建完整的代码摘要 ──
    code_text = summarize_code_analysis(code_analysis)
    # 提高上限到 20000 字符，尽量保留更多代码信息
    code_char_limit = 20000
    if len(code_text) > code_char_limit:
        code_text = code_text[:code_char_limit] + "\n... (代码摘要已截断，共 {} 字符)".format(len(code_text))

    system_prompt = """你是一位资深 QA 测试工程师，正在做需求文档 vs 代码实现的逐条对比。

你必须严格遵循以下原则：
1. **逐条检查**：每一条需求都必须给出明确结论（已实现/部分实现/未实现/实现有误）
2. **不要遗漏**：即使看起来已实现，也要检查边界条件、异常处理、文案是否一致
3. **关注细节**：表单校验规则、字段类型、必填/选填、提示文案、状态流转、条件显示/隐藏
4. **具体引用**：引用具体的代码文件名、函数名、行为来佐证你的结论
5. **Bug 格式**：发现问题必须给出操作步骤、预期结果、实际结果
6. 只返回 JSON，不要其他文字"""

    # ── 2. 分批：每批最多 8 条需求，确保 AI 有足够 token 仔细分析 ──
    BATCH_SIZE = 8
    all_matched = []
    all_unimplemented = []
    all_extra = []
    all_bugs = []
    all_test_suggestions = []

    total_batches = (len(req_points) + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"📋 需求共 {len(req_points)} 条，分 {total_batches} 批对比...")

    for batch_idx in range(0, len(req_points), BATCH_SIZE):
        batch = req_points[batch_idx:batch_idx + BATCH_SIZE]
        batch_num = batch_idx // BATCH_SIZE + 1
        print(f"  🔍 对比第 {batch_num}/{total_batches} 批 ({len(batch)} 条需求)...")

        # 构建需求详情（发送完整 detail，不仅仅是名称）
        req_text_parts = []
        for p in batch:
            detail = p.get('detail', '') or p.get('name', '')
            source = p.get('source', '')
            req_text_parts.append(f"  {p['id']} [{source}]: {detail}")
        req_text = "\n".join(req_text_parts)

        prompt = f"""请严格逐条对比以下 {len(batch)} 条需求与代码实现。

## 本批需求功能点（第 {batch_num} 批，共 {total_batches} 批）
{req_text}

## 代码实现摘要
{code_text}

请以 JSON 格式返回本批对比结果:
{{
  "matched": [
    {{ "req_id": "REQ_xxx", "requirement": "需求原文", "code_item": "对应的组件/函数/文件", "file": "文件路径",
       "status": "已实现|部分实现|实现有误", "notes": "具体说明实现情况，引用代码证据", "confidence": 0.9 }}
  ],
  "unimplemented": [
    {{ "req_id": "REQ_xxx", "requirement": "需求原文", "severity": "high|medium|low",
       "suggestion": "具体说明为什么判断未实现，以及建议" }}
  ],
  "bugs": [
    {{ "title": "[模块] 问题简述", "severity": "high|medium|low", "req_id": "REQ_xxx",
       "steps": "1. xxx\\n2. xxx", "expected": "预期结果", "actual": "实际代码行为",
       "code_evidence": "文件名:行号 或 函数名" }}
  ],
  "test_suggestions": [
    {{ "title": "测试建议标题", "priority": "high|medium|low", "req_id": "REQ_xxx",
       "test_points": ["测试点1", "测试点2"] }}
  ]
}}

关键要求：
- 每条需求必须出现在 matched 或 unimplemented 中，不允许遗漏
- "部分实现"和"实现有误"的必须在 bugs 里给出具体 Bug
- 仔细检查：文案是否一致、校验规则是否完整、边界条件是否处理
- 只返回 JSON"""

        try:
            response = _ai_call_with_timeout(ai_client, prompt, system_prompt, timeout=180, max_tokens=8000)
            batch_result = _parse_ai_json(response)

            all_matched.extend(batch_result.get("matched", []))
            all_unimplemented.extend(batch_result.get("unimplemented", []))
            all_bugs.extend(batch_result.get("bugs", []))
            all_test_suggestions.extend(batch_result.get("test_suggestions", []))

        except Exception as e:
            print(f"  ⚠️ 第 {batch_num} 批 AI 分析失败: {e}，对该批使用规则匹配")
            # 该批降级为规则匹配
            batch_code_items = code_items
            batch_rule = _rule_based_diff(batch, batch_code_items)
            all_matched.extend(batch_rule.get("matched", []))
            all_unimplemented.extend(batch_rule.get("unimplemented", []))

    # ── 3. 额外代码检查（单独一次调用） ──
    try:
        extra_prompt = f"""以下是代码中存在的组件/路由/函数，请找出需求文档中没有提及但代码中存在的额外功能。

## 代码实现清单
{chr(10).join(f"  {ci['id']}: {ci['name']} ({ci.get('type','')}) - {ci.get('file','')}" for ci in code_items[:40])}

## 需求功能点清单
{chr(10).join(f"  {p['id']}: {p['name']}" for p in req_points[:60])}

返回 JSON:
{{ "extra_code": [ {{ "code_item": "名称", "file": "文件路径", "notes": "说明" }} ] }}
只返回 JSON"""
        extra_resp = _ai_call_with_timeout(ai_client, extra_prompt, system_prompt, timeout=60, max_tokens=4000)
        extra_result = _parse_ai_json(extra_resp)
        all_extra.extend(extra_result.get("extra_code", []))
    except Exception as e:
        print(f"  ⚠️ 额外代码检查失败: {e}")

    # ── 4. 汇总结果 ──
    result = {
        "summary": {
            "total_req_points": len(req_points),
            "total_code_items": len(code_items),
            "matched": len(all_matched),
            "unimplemented": len(all_unimplemented),
            "extra_code": len(all_extra),
            "bugs_found": len(all_bugs),
        },
        "matched": all_matched,
        "unimplemented": all_unimplemented,
        "extra_code": all_extra,
        "bugs": all_bugs,
        "test_suggestions": all_test_suggestions,
        "_ai_fallback": False,
        "_batch_count": total_batches,
    }

    print(f"✅ 对比完成: {len(all_matched)} 已实现, {len(all_unimplemented)} 未实现, {len(all_bugs)} 个Bug")
    return result
