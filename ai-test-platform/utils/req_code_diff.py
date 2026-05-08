#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
需求-代码对比引擎 (v2)

改进点:
- 扩展代码清单：functions / conditions / api_calls / fields / template_conditions
- 关键词召回：每条需求只把相关代码片段送进 AI，不再共享一份被截断的全局摘要
- 强化 prompt：四态判断（implemented / inconsistent / partial / missing），强制代码定位
- 新增 inconsistent finding 类型
- 携带代码证据片段（从源码读取 ±N 行，脱敏）
- 低置信度 finding 第二轮复核
"""

import json
import re
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path


# ── 配置项 ───────────────────────────────────────────
TOPK_PER_REQ = 12
SNIPPET_CTX = 8
REVIEW_CONFIDENCE = 0.55
REVIEW_TYPES = {"inconsistent", "partial", "uncertain"}

_SENSITIVE_RE = re.compile(
    r'(?i)(token|password|secret|authorization|cookie|api_key|access_key|private_key)\s*[:=]\s*[\"\']?[^\s\"\']{6,}'
)


def _redact(text: str) -> str:
    if not text:
        return text
    return _SENSITIVE_RE.sub('***REDACTED***', text)


def run_req_code_diff(
    requirement_data: Dict[str, Any],
    code_analysis: Dict[str, Any],
    ai_client=None,
    max_prompt_chars: int = 12000,
    code_dir: Optional[str] = None,
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

    # 2. 提取代码实现清单（扩展信号）
    code_items = _extract_code_items(code_analysis)

    # 3. 构建倒排索引以便按需求做召回
    code_index = _build_code_index(code_items)

    # 3.5 T1A: 确定性规则门禁层 — 拦截能用静态信号判定的需求点
    from utils.rule_gate import run_rule_gate
    gate_result = run_rule_gate(req_points, code_analysis, code_dir)
    gated_findings = gate_result["gated_findings"]
    remaining_points = gate_result["uncovered_points"]

    # 4. 对比（仅剩余需求点走 AI / rule-based）
    if ai_client and remaining_points:
        ai_result = _ai_diff(
            remaining_points, code_items, code_index, code_analysis,
            ai_client, max_prompt_chars, code_dir,
        )
    elif remaining_points:
        ai_result = _rule_based_diff(remaining_points, code_items, code_index)
        ai_result["_ai_fallback"] = False
    else:
        ai_result = _empty_result()

    # 5. 合并规则门禁 findings + AI/rule 结果
    result = _merge_gate_findings(gated_findings, ai_result, gate_result["stats"])
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
    """从代码分析结果中提取实现清单（扩展信号）。"""
    items: List[Dict] = []

    def _add(name, type_, file, line, detail, weight, source_obj=None):
        items.append({
            "id": f"CODE_{len(items)+1:04d}",
            "name": str(name or "")[:200],
            "type": type_,
            "file": file or "",
            "line": int(line or 0),
            "detail": str(detail or "")[:600],
            "weight": weight,
            "source_obj": source_obj,
        })

    for comp in code_data.get("components", []):
        methods = comp.get("methods", [])
        fields = comp.get("data_fields", [])
        conds = comp.get("template_conditions", [])
        cn_labels = comp.get("chinese_labels", [])
        java_fields = comp.get("fields", [])  # Java @ApiModelProperty 字段
        detail = f"组件 {comp.get('name','')}: 方法[{', '.join(methods[:15])}]; 字段[{', '.join(fields[:15])}]"
        if conds:
            detail += f"; 条件[{', '.join(c[:60] for c in conds[:8])}]"
        if cn_labels:
            detail += f"; 中文标签[{', '.join(cn_labels[:20])}]"
        comp_desc = comp.get("description", "")
        if comp_desc:
            detail += f"; 描述[{comp_desc}]"
        _add(comp.get("name", ""), comp.get("type", "component"),
             comp.get("file", ""), comp.get("line", 0), detail,
             weight=2.0, source_obj=comp)
        for fname in fields[:30]:
            _add(f"字段 {fname}", "field",
                 comp.get("file", ""), comp.get("line", 0),
                 f"{comp.get('name','')} 数据字段 {fname}", weight=1.2)
        for cond in conds[:20]:
            _add(f"v-if {cond[:60]}", "template_condition",
                 comp.get("file", ""), comp.get("line", 0),
                 f"{comp.get('name','')} 模板条件: {cond}", weight=1.4)
        # Java 字段（含中文标签）→ 每个字段一个 code_item
        for jf in java_fields[:50]:
            label = jf.get("label", "")
            fname = jf.get("field_name", "")
            validations = jf.get("validations", [])
            jf_detail = f"{comp.get('name','')}.{fname} @ApiModelProperty(\"{label}\")"
            if validations:
                jf_detail += f" 验证: {', '.join(validations)}"
            _add(f"{label} ({fname})" if fname else label, "java_field",
                 comp.get("file", ""), jf.get("line", 0),
                 jf_detail, weight=2.2, source_obj=jf)
        # Vue 中文标签 → 每个标签一个 code_item（权重稍低）
        if comp.get("type") == "vue_component" and cn_labels:
            for lb in cn_labels[:40]:
                _add(lb, "template_label",
                     comp.get("file", ""), 0,
                     f"{comp.get('name','')} 模板中文: {lb}",
                     weight=1.8)

    for route in code_data.get("routes", []):
        name = f"{route.get('method','GET')} {route.get('path','')}"
        _add(name, "api_route",
             route.get("file", ""), 0,
             f"API 路由 {name} → {route.get('handler','')}",
             weight=2.4, source_obj=route)

    for fn in code_data.get("functions", []):
        params = fn.get("params", [])
        decorators = fn.get("decorators", []) or fn.get("annotations", []) or []
        detail = f"函数 {fn.get('name','')}({', '.join(params[:8])})"
        if decorators:
            detail += f" 装饰器/注解: {', '.join(decorators[:4])}"
        _add(fn.get("name", ""), "function",
             fn.get("file", ""), fn.get("line", 0),
             detail, weight=1.6, source_obj=fn)

    for api in code_data.get("api_calls", []):
        url = api.get("url", "")
        method = api.get("method", "")
        _add(f"调用 {method} {url}", "api_call",
             api.get("file", ""), api.get("line", 0),
             f"代码内调用 {method} {url}", weight=1.3, source_obj=api)

    for cond in code_data.get("conditions", []):
        expr = (cond.get("expression") or "")[:120]
        if not expr:
            continue
        _add(f"if {expr[:60]}", "condition",
             cond.get("file", ""), cond.get("line", 0),
             f"条件: if {expr}", weight=0.9, source_obj=cond)

    return items


# ───────────── 关键词分词 / 倒排索引 ─────────────

_CN_RE = re.compile(r'[\u4e00-\u9fff]+')
_EN_RE = re.compile(r'[A-Za-z][A-Za-z0-9_]{2,}')
_PATH_RE = re.compile(r'/[A-Za-z][A-Za-z0-9_\-/]{2,}')

_STOPWORDS = {
    "the", "and", "for", "this", "that", "with", "from", "into",
    "返回", "需要", "实现", "支持", "提供", "进行", "如果", "并且",
    "或者", "可以", "应该", "必须", "页面", "接口", "功能", "用户", "数据",
}


def _tokenize(text: str) -> set:
    if not text:
        return set()
    s = text.lower()
    tokens: set = set()
    for w in _EN_RE.findall(s):
        if w not in _STOPWORDS:
            tokens.add(w)
    for path in _PATH_RE.findall(s):
        for seg in path.split('/'):
            seg = seg.strip()
            if len(seg) >= 3 and seg not in _STOPWORDS:
                tokens.add(seg)
    for chunk in _CN_RE.findall(s):
        if len(chunk) <= 1:
            continue
        if 2 <= len(chunk) <= 4:
            tokens.add(chunk)
        for i in range(len(chunk) - 1):
            bg = chunk[i:i + 2]
            if bg not in _STOPWORDS:
                tokens.add(bg)
        for i in range(len(chunk) - 2):
            tg = chunk[i:i + 3]
            if tg not in _STOPWORDS:
                tokens.add(tg)
    return tokens


def _build_code_index(code_items: List[Dict]) -> Dict[str, List[int]]:
    index: Dict[str, List[int]] = {}
    for idx, item in enumerate(code_items):
        bag = _tokenize(
            f"{item.get('name','')} {item.get('detail','')} {item.get('file','')}"
        )
        for tok in bag:
            index.setdefault(tok, []).append(idx)
        item["_tokens"] = bag
    return index


def _score_code_items(req_tokens: set, code_items: List[Dict],
                      index: Dict[str, List[int]],
                      top_k: int = TOPK_PER_REQ) -> List[Dict]:
    if not req_tokens or not code_items:
        return []
    score: Dict[int, float] = {}
    for tok in req_tokens:
        for idx in index.get(tok, ()):
            score[idx] = score.get(idx, 0.0) + 1.0
    if not score:
        return []
    ranked: List[Tuple[float, int]] = []
    for idx, base in score.items():
        w = code_items[idx].get("weight", 1.0)
        ranked.append((base * w, idx))
    ranked.sort(reverse=True)
    return [code_items[i] for _, i in ranked[:top_k]]


# ───────────── 代码证据片段 ─────────────

def _safe_join(code_dir: str, rel_path: str) -> Optional[Path]:
    if not code_dir or not rel_path:
        return None
    try:
        base = Path(code_dir).resolve()
        target = (base / rel_path).resolve()
        if str(target).startswith(str(base)):
            return target
    except Exception:
        return None
    return None


def _load_snippet(code_dir: Optional[str], rel_path: str, line: int,
                  ctx: int = SNIPPET_CTX) -> Optional[Dict[str, Any]]:
    if not code_dir or not rel_path:
        return None
    p = _safe_join(code_dir, rel_path)
    if not p or not p.exists() or not p.is_file():
        return None
    try:
        if p.stat().st_size > 1024 * 1024:
            return None
        text = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None
    lines = text.splitlines()
    line = max(1, int(line or 1))
    start = max(1, line - ctx)
    end = min(len(lines), line + ctx)
    snippet_lines = []
    for ln in range(start, end + 1):
        snippet_lines.append(f"{ln:>5} | {_redact(lines[ln-1])}")
    return {
        "file": rel_path,
        "line": line,
        "start": start,
        "end": end,
        "snippet": "\n".join(snippet_lines)[:4000],
    }


def _empty_result() -> Dict:
    """空结果模板（所有 req 都被 rule_gate 处理时使用）"""
    return {
        "summary": {
            "total_req_points": 0,
            "total_code_items": 0,
            "matched": 0,
            "unimplemented": 0,
            "extra_code": 0,
        },
        "matched": [],
        "unimplemented": [],
        "extra_code": [],
        "bugs": [],
        "test_suggestions": [],
    }


def _merge_gate_findings(
    gated: List[Dict], ai_result: Dict, gate_stats: Dict
) -> Dict:
    """
    合并规则门禁结果 + AI/rule-based 结果。

    规则门禁产出的 finding 按 status 分类：
      - implemented → matched
      - missing → unimplemented
      - inconsistent → bugs
    """
    merged = {k: list(v) if isinstance(v, list) else v
              for k, v in ai_result.items()}

    for gf in gated:
        req = gf.get("requirement", {})
        status = gf.get("status", "")
        note = gf.get("note", "")
        evidence = gf.get("evidence_quote", "")[:400]
        entry_base = {
            "requirement": req.get("name", ""),
            "req_id": req.get("id", ""),
            "file": gf.get("evidence_file", ""),
            "line": (gf.get("evidence_lines") or (0, 0))[0],
            "rule_type": gf.get("rule_type", ""),
            "rule_engine": gf.get("rule_engine", ""),
            "confidence": gf.get("confidence", 1.0),
        }
        if status == "implemented":
            merged.setdefault("matched", []).append({
                **entry_base,
                "code_item": f"[rule_gate] {note}",
                "status": "已实现（规则确认）",
                "notes": f"{note}\n{evidence}".strip(),
            })
        elif status == "missing":
            merged.setdefault("unimplemented", []).append({
                **entry_base,
                "severity": "high",
                "suggestion": note,
            })
        elif status == "inconsistent":
            merged.setdefault("bugs", []).append({
                "title": f"[规则检测] {req.get('name','')}: {note[:50]}",
                "severity": "medium",
                "requirement": req.get("name", ""),
                "rule_type": gf.get("rule_type", ""),
                "evidence_file": gf.get("evidence_file", ""),
                "evidence_quote": evidence,
                "notes": note,
            })

    # 更新 summary 计数
    summary = merged.get("summary", {})
    summary["rule_gate_stats"] = gate_stats
    summary["total_req_points"] = (
        summary.get("total_req_points", 0) + gate_stats.get("gated", 0)
    )
    summary["matched"] = len(merged.get("matched", []))
    summary["unimplemented"] = len(merged.get("unimplemented", []))
    merged["summary"] = summary
    return merged


def _rule_based_diff(req_points: List[Dict], code_items: List[Dict],
                     code_index: Optional[Dict[str, List[int]]] = None) -> Dict:
    """基于召回的规则对比（不用 AI）。"""
    matched: List[Dict] = []
    unimplemented: List[Dict] = []
    extra_code: List[Dict] = []

    if code_index is None:
        code_index = _build_code_index(code_items)
    matched_code_ids: set = set()

    for req in req_points:
        req_text = f"{req.get('name','')} {req.get('detail','')}"
        req_tokens = _tokenize(req_text)
        topk = _score_code_items(req_tokens, code_items, code_index, top_k=3)
        if topk:
            best = topk[0]
            overlap = len(req_tokens & best.get("_tokens", set()))
            denom = max(1, len(req_tokens))
            conf = min(overlap / denom + 0.2, 1.0) if denom else 0.4
            matched.append({
                "requirement": req["name"],
                "req_id": req["id"],
                "code_item": best["name"],
                "code_id": best["id"],
                "file": best.get("file", ""),
                "line": best.get("line", 0),
                "status": "可能已实现",
                "confidence": round(conf, 2),
                "notes": f"关键词召回 top1，命中 {overlap}/{denom}",
            })
            matched_code_ids.add(best["id"])
        else:
            unimplemented.append({
                "requirement": req["name"],
                "req_id": req["id"],
                "severity": "medium",
                "suggestion": f"需求 '{req['name']}' 在代码中未找到关键词匹配",
            })

    for ci in code_items:
        if ci["id"] not in matched_code_ids and ci["type"] == "api_route":
            extra_code.append({
                "code_item": ci["name"],
                "code_id": ci["id"],
                "file": ci.get("file", ""),
                "notes": "API 路由存在但需求文档中未提及",
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
        "extra_code": extra_code[:200],
        "bugs": [],
        "test_suggestions": [],
    }


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


_STATUS_MAP = {
    "已实现": "implemented",
    "implemented": "implemented",
    "已完成": "implemented",
    "部分实现": "partial",
    "partial": "partial",
    "实现不一致": "inconsistent",
    "实现有误": "inconsistent",
    "inconsistent": "inconsistent",
    "未实现": "missing",
    "missing": "missing",
    "未找到": "missing",
    "无法确认": "uncertain",
    "uncertain": "uncertain",
}


def _normalize_status(s: Any) -> str:
    if not s:
        return "uncertain"
    return _STATUS_MAP.get(str(s).strip(), "uncertain")


def _format_candidate_block(req_id: str, req: Dict, candidates: List[Dict]) -> str:
    """把单条需求的候选代码格式化成 prompt 内的小节。"""
    head = f"### {req_id} {req.get('source','')} 需求\n- 需求原文: {req.get('detail') or req.get('name','')}"
    if not candidates:
        return head + "\n- 候选代码: （未召回到相关代码）"
    lines = [head, f"- 候选代码（已按相关度排序，共 {len(candidates)} 条，仅供你定位，最终判断需基于这些线索）:"]
    for c in candidates:
        loc = f"{c.get('file','')}:{c.get('line',0)}" if c.get("line") else c.get("file", "")
        lines.append(f"  * [{c.get('type','')}] {c.get('name','')[:80]}  @ {loc}")
        detail = (c.get("detail") or "")[:160]
        if detail:
            lines.append(f"      detail: {detail}")
    return "\n".join(lines)


def _ai_diff(
    req_points: List[Dict],
    code_items: List[Dict],
    code_index: Dict[str, List[int]],
    code_analysis: Dict,
    ai_client,
    max_chars: int,
    code_dir: Optional[str] = None,
) -> Dict:
    """AI 深度对比 —— 按需求召回相关代码 + 四态判断 + 证据片段 + 低置信复核。"""

    system_prompt = """你是一位资深 QA 测试工程师，对需求文档与代码实现做逐条比对。

强制规则：
1. 逐条覆盖：每条需求必须给出 status，且只能取其中之一：implemented / partial / inconsistent / missing
   - implemented：代码完整覆盖该需求
   - partial：核心功能存在，但缺少校验/边界/分支/文案等细节
   - inconsistent：代码与需求字面或行为不一致（例如校验范围不同、文案不同、状态流转不同）
   - missing：在候选代码中找不到对应实现
2. 强制定位：每条结论必须给出 file 与（如能给出）line；引用候选代码以外的"凭印象"判断不允许
3. 不一致细节：partial / inconsistent 必须在 inconsistencies 字段说明"需求要求 vs 代码实际"对比项
4. 不要发明：候选代码没出现的文件/函数不要捏造
5. 输出严格 JSON，不要解释文字"""

    BATCH_SIZE = 6
    all_matched: List[Dict] = []
    all_unimplemented: List[Dict] = []
    all_inconsistent: List[Dict] = []
    all_extra: List[Dict] = []
    all_bugs: List[Dict] = []
    all_test_suggestions: List[Dict] = []
    matched_code_ids: set = set()

    total_batches = (len(req_points) + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"📋 需求共 {len(req_points)} 条，分 {total_batches} 批对比（按需召回 v2）...")

    for batch_idx in range(0, len(req_points), BATCH_SIZE):
        batch = req_points[batch_idx:batch_idx + BATCH_SIZE]
        batch_num = batch_idx // BATCH_SIZE + 1

        # 为本批的每条需求做关键词召回
        candidate_blocks = []
        candidates_by_req: Dict[str, List[Dict]] = {}
        for p in batch:
            req_text = f"{p.get('name','')} {p.get('detail','')}"
            req_tokens = _tokenize(req_text)
            cand = _score_code_items(req_tokens, code_items, code_index, top_k=TOPK_PER_REQ)
            candidates_by_req[p["id"]] = cand
            for c in cand:
                matched_code_ids.add(c["id"])
            candidate_blocks.append(_format_candidate_block(p["id"], p, cand))

        prompt_body = "\n\n".join(candidate_blocks)

        prompt = f"""请对以下 {len(batch)} 条需求逐条做需求-代码比对（第 {batch_num}/{total_batches} 批）。

{prompt_body}

请严格返回如下 JSON：
{{
  "results": [
    {{
      "req_id": "REQ_xxx",
      "status": "implemented|partial|inconsistent|missing",
      "confidence": 0.0-1.0,
      "code_item": "命中的组件/函数/路由名（必须来自候选代码）",
      "file": "文件相对路径（必须来自候选代码）",
      "line": 整数行号或 0,
      "notes": "结论依据，引用候选代码片段",
      "inconsistencies": [
        {{ "aspect": "校验/文案/状态流转/字段/边界", "expected": "需求要求", "actual": "代码实际" }}
      ],
      "test_points": ["针对该需求的关键测试点"]
    }}
  ]
}}

要求：
- 候选代码为空 → 直接 status=missing
- partial 或 inconsistent 必须填 inconsistencies 至少一条
- 只返回 JSON"""

        try:
            response = _ai_call_with_timeout(ai_client, prompt, system_prompt, timeout=180, max_tokens=8000)
            parsed = _parse_ai_json(response)
            results = parsed.get("results") or parsed.get("items") or []
        except Exception as e:
            print(f"  ⚠️ 第 {batch_num} 批 AI 分析失败: {e}，回退规则匹配")
            rule = _rule_based_diff(batch, code_items, code_index)
            all_matched.extend(rule.get("matched", []))
            all_unimplemented.extend(rule.get("unimplemented", []))
            continue

        # 把 AI 结果分类到 matched / unimplemented / inconsistent / bugs
        for r in results:
            req_id = r.get("req_id") or ""
            req = next((p for p in batch if p["id"] == req_id), None) or (batch[0] if batch else None)
            if not req:
                continue
            status = _normalize_status(r.get("status"))
            confidence = r.get("confidence")
            try:
                confidence = float(confidence)
            except Exception:
                confidence = 0.6
            confidence = max(0.0, min(1.0, confidence))

            file_ = r.get("file") or ""
            line_ = r.get("line") or 0
            try:
                line_ = int(line_)
            except Exception:
                line_ = 0
            evidence_snippet = _load_snippet(code_dir, file_, line_) if file_ else None
            notes = r.get("notes", "")
            incs = r.get("inconsistencies") or []
            test_points = r.get("test_points") or []

            common = {
                "req_id": req_id,
                "requirement": req.get("name", ""),
                "code_item": r.get("code_item", ""),
                "file": file_,
                "line": line_,
                "confidence": round(confidence, 2),
                "notes": notes,
                "status_raw": r.get("status"),
                "status_norm": status,
                "inconsistencies": incs,
                "test_points": test_points,
                "evidence_snippet": evidence_snippet,
            }

            if status == "implemented":
                all_matched.append({**common, "status": "已实现"})
            elif status == "partial":
                all_matched.append({**common, "status": "部分实现"})
            elif status == "inconsistent":
                all_inconsistent.append(common)
                # 同步生成一个 bug 提示
                bug_steps = []
                for it in incs[:3]:
                    bug_steps.append(
                        f"{it.get('aspect','')}: 需求={it.get('expected','')}, 代码={it.get('actual','')}"
                    )
                all_bugs.append({
                    "title": f"[实现不一致] {req.get('name','')[:60]}",
                    "severity": "medium",
                    "req_id": req_id,
                    "steps": "\n".join(bug_steps) or notes,
                    "expected": "; ".join(it.get("expected", "") for it in incs[:3]),
                    "actual": "; ".join(it.get("actual", "") for it in incs[:3]),
                    "code_evidence": f"{file_}:{line_}" if file_ else "",
                })
            else:  # missing / uncertain → unimplemented
                severity = "high" if status == "missing" else "medium"
                all_unimplemented.append({
                    "req_id": req_id,
                    "requirement": req.get("name", ""),
                    "severity": severity,
                    "suggestion": notes or f"需求 '{req.get('name','')}' 在代码中未找到对应实现",
                    "status_norm": status,
                    "confidence": round(confidence, 2),
                })

            if test_points:
                all_test_suggestions.append({
                    "title": f"验证 {req.get('name','')[:40]}",
                    "priority": "high" if status in ("missing", "inconsistent") else "medium",
                    "req_id": req_id,
                    "test_points": test_points,
                })

    # ── 低置信度 / 不一致 二次复核（B3） ──
    review_targets = []
    for item in list(all_matched):
        if item.get("status") == "部分实现" or item.get("confidence", 1.0) < REVIEW_CONFIDENCE:
            review_targets.append(("matched", item))
    for item in list(all_inconsistent):
        if item.get("confidence", 1.0) < REVIEW_CONFIDENCE + 0.15:
            review_targets.append(("inconsistent", item))

    if review_targets:
        print(f"🔁 低置信度复核 {len(review_targets)} 条 ...")
        # 单批最多 4 条
        for i in range(0, len(review_targets), 4):
            chunk = review_targets[i:i + 4]
            blocks = []
            for kind, it in chunk:
                req_id = it.get("req_id") or ""
                req = next((p for p in req_points if p["id"] == req_id), None)
                if not req:
                    continue
                cand = _score_code_items(_tokenize(f"{req.get('name','')} {req.get('detail','')}"),
                                          code_items, code_index, top_k=8)
                snippets = []
                for c in cand[:5]:
                    snip = _load_snippet(code_dir, c.get("file", ""), c.get("line", 0))
                    if snip:
                        snippets.append(f"-- {c.get('file','')} ({c.get('type','')}) --\n{snip['snippet']}")
                blocks.append(
                    f"### {req_id} 当前判断: {it.get('status') or it.get('status_norm')} "
                    f"confidence={it.get('confidence')}\n"
                    f"需求: {req.get('detail') or req.get('name','')}\n"
                    f"前次结论: {it.get('notes','')}\n"
                    f"参考代码片段:\n" + ("\n\n".join(snippets) if snippets else "(无代码片段)")
                )
            review_prompt = (
                "请对以下需求复核，判断之前的结论是否准确。\n\n"
                + "\n\n".join(blocks)
                + "\n\n返回 JSON：\n"
                "{ \"reviews\": ["
                "{ \"req_id\": \"REQ_xxx\", \"final_status\": \"implemented|partial|inconsistent|missing\","
                " \"confidence\": 0.0-1.0, \"notes\": \"复核结论\","
                " \"inconsistencies\": [ {\"aspect\":\"\", \"expected\":\"\", \"actual\":\"\"} ] }"
                "] }\n只返回 JSON"
            )
            try:
                rresp = _ai_call_with_timeout(ai_client, review_prompt, system_prompt, timeout=120, max_tokens=4000)
                rparsed = _parse_ai_json(rresp)
                for rev in (rparsed.get("reviews") or []):
                    rid = rev.get("req_id")
                    if not rid:
                        continue
                    final = _normalize_status(rev.get("final_status"))
                    new_conf = rev.get("confidence")
                    try:
                        new_conf = float(new_conf)
                    except Exception:
                        new_conf = None
                    notes = rev.get("notes", "")
                    incs = rev.get("inconsistencies") or []

                    # 在三个池子中找到该 req 并更新（最多更新一处）
                    found = False
                    for pool, ftype in ((all_matched, "matched"), (all_inconsistent, "inconsistent"),
                                          (all_unimplemented, "unimplemented")):
                        for it in pool:
                            if it.get("req_id") == rid and not found:
                                if new_conf is not None:
                                    it["confidence"] = round(max(0.0, min(1.0, new_conf)), 2)
                                it["notes"] = (it.get("notes", "") + "\n[复核] " + notes).strip()
                                if incs:
                                    it["inconsistencies"] = incs
                                it["reviewed"] = True
                                found = True
                                break
                        if found:
                            break

                    # 如果 final 与原分类不一致，做迁移
                    if final == "missing":
                        for pool in (all_matched, all_inconsistent):
                            tgt = next((x for x in pool if x.get("req_id") == rid), None)
                            if tgt:
                                pool.remove(tgt)
                                all_unimplemented.append({
                                    "req_id": rid,
                                    "requirement": tgt.get("requirement", ""),
                                    "severity": "high",
                                    "suggestion": notes or "复核后判断为未实现",
                                    "status_norm": "missing",
                                    "confidence": tgt.get("confidence", 0.6),
                                })
                                break
                    elif final == "inconsistent":
                        for pool in (all_matched, all_unimplemented):
                            tgt = next((x for x in pool if x.get("req_id") == rid), None)
                            if tgt:
                                pool.remove(tgt)
                                tgt["status_norm"] = "inconsistent"
                                tgt["inconsistencies"] = incs or tgt.get("inconsistencies", [])
                                all_inconsistent.append(tgt)
                                break
                    elif final == "implemented":
                        for pool in (all_inconsistent, all_unimplemented):
                            tgt = next((x for x in pool if x.get("req_id") == rid), None)
                            if tgt:
                                pool.remove(tgt)
                                tgt["status"] = "已实现"
                                tgt["status_norm"] = "implemented"
                                all_matched.append(tgt)
                                break
            except Exception as e:
                print(f"  ⚠️ 复核失败: {e}")

    # ── 额外代码（在召回中没被任何需求命中的） ──
    # 只报告 api_route 为真正"超范围"；function/component 多为技术内部实现，不报告
    _EXTRA_EXCLUDE_NAMES = {
        "main", "init", "setup", "created", "mounted", "onload", "onshow",
        "onready", "onhide", "onunload", "destroyed", "beforecreate",
        "beforemount", "beforedestroy", "updated", "tostring", "hashcode",
        "equals", "getset", "builder",
    }
    extra_candidates = [
        ci for ci in code_items
        if ci["id"] not in matched_code_ids
        and ci["type"] == "api_route"
        and ci.get("name")
        and ci.get("name", "").lower() not in _EXTRA_EXCLUDE_NAMES
    ]
    for ci in extra_candidates[:30]:
        all_extra.append({
            "code_item": ci["name"],
            "code_id": ci["id"],
            "file": ci.get("file", ""),
            "line": ci.get("line", 0),
            "notes": "API 路由存在但未被需求文档中任何功能点覆盖",
        })

    summary = {
        "total_req_points": len(req_points),
        "total_code_items": len(code_items),
        "matched": len(all_matched),
        "unimplemented": len(all_unimplemented),
        "inconsistent": len(all_inconsistent),
        "extra_code": len(all_extra),
        "bugs_found": len(all_bugs),
    }
    print(
        f"✅ 对比完成: implemented/partial={len(all_matched)}, "
        f"missing={len(all_unimplemented)}, inconsistent={len(all_inconsistent)}, "
        f"extra={len(all_extra)}, bugs={len(all_bugs)}"
    )
    return {
        "summary": summary,
        "matched": all_matched,
        "unimplemented": all_unimplemented,
        "inconsistent": all_inconsistent,
        "extra_code": all_extra,
        "bugs": all_bugs,
        "test_suggestions": all_test_suggestions,
        "_ai_fallback": False,
        "_batch_count": total_batches,
        "_engine_version": "v2",
    }
