#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
D2-3A: 迭代需求 AI 解析服务

两层策略:
1. LLM 解析 — 调用已有 AIClient，提取功能点/业务规则/影响范围/风险点/测试点/待确认问题
2. 规则型 fallback — LLM 不可用时，用关键词提取生成结构化结果

输出结构始终稳定:
{
  "functional_points": [],
  "business_rules": [],
  "impact_scope": [],
  "risk_points": [],
  "test_points": [],
  "api_mappings": [],
  "confirm_questions": []
}
"""
import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Any

logger = logging.getLogger("iteration_ai_service")

EMPTY_RESULT = {
    "functional_points": [],
    "business_rules": [],
    "impact_scope": [],
    "risk_points": [],
    "test_points": [],
    "api_mappings": [],
    "confirm_questions": [],
}


def _empty_result() -> Dict[str, Any]:
    return {key: [] for key in EMPTY_RESULT}


_SYSTEM_PROMPT = """你是一位资深测试分析师。用户会给你一段或多段需求描述，以及从知识库检索到的 API、前端代码、后端代码、操作手册片段。请只围绕【本次需求文本】做解析，知识库上下文只能用于识别真实接口、影响模块和字段，不允许把知识库里的无关功能扩展成本次需求。

输出必须是 JSON，结构如下:

{
  "functional_points": ["功能点1", "功能点2"],
  "business_rules": ["业务规则1", "业务规则2"],
  "impact_scope": ["影响范围1"],
  "risk_points": ["风险点1"],
  "api_mappings": [
    {
      "feature": "功能点",
      "method": "POST",
      "url": "/recycle/xxx",
      "summary": "接口用途",
      "confidence": 0.85
    }
  ],
  "test_points": [
    {
      "test_point": "测试点描述",
      "priority": "high/medium/low",
      "test_type": "functional/api/performance/security",
      "risk_level": "P0/P1/P2",
      "module_name": "模块名",
      "requirement_trace": "对应的需求原文短句",
      "recommended_api": {"method": "POST", "url": "/recycle/xxx", "summary": "接口用途", "confidence": 0.85},
      "execution_config": {
        "method": "POST",
        "url": "/xxx",
        "headers": {"Content-Type": "application/json"},
        "body": {},
        "query_params": {},
        "timeout": 10
      }
    }
  ],
  "confirm_questions": ["需要和产品确认的问题1"]
}

硬性要求:
1. 只能解析【本次需求文本】中明确出现或能直接推导出的内容；不要补充通用测试模板，不要生成和原文无关的功能。
2. 每个 test_point 必须对应一个 requirement_trace，requirement_trace 必须摘自需求原文，不能杜撰。
3. 功能点必须是可独立验证的用户行为、系统规则或数据变化，不能只写“验证功能正常”。
4. 如果需求只描述 UI 行为，测试点就写 UI/功能验证；不要强行映射 API。
5. 只有知识库 API 与需求关键词、模块、动作高度匹配时，才填写 recommended_api 和 execution_config；不确定时填 null。
6. 测试点要优先覆盖需求原文里的正向路径、条件限制、异常提示、数据回填、状态变化、权限/边界；原文没提到的不要扩展。
7. 待确认问题只列需求中含糊、缺字段、缺规则、缺边界的点；不要泛泛写“需确认业务规则”。
8. execution_config.url 只填写接口路径，不要拼接环境域名；如果知识库路径包含 /recycle 前缀且环境 base_url 已包含 /recycle，应去掉开头 /recycle。
9. 输出数量要克制：每个明确功能点通常 1-3 个高质量测试点即可，宁少勿泛。

只返回 JSON，不要有其他文字。"""


def _strip_recycle_prefix(path: str) -> str:
    if not path:
        return path
    return re.sub(r"^/recycle(?=/)", "", path)


def _compact_items(items: List[Dict[str, Any]], allowed: List[str], limit: int = 8) -> List[Dict[str, Any]]:
    compact = []
    for item in (items or [])[:limit]:
        if isinstance(item, dict):
            compact.append({k: item.get(k) for k in allowed if item.get(k) is not None})
    return compact


_QUERY_API_HINTS = {
    "摄像头": ["device", "basicdevice", "stream", "ptz", "camera"],
    "云台": ["ptz", "device", "camera"],
    "设备": ["device", "basicdevice"],
    "播放": ["stream", "play"],
    "列表": ["page", "list"],
    "分页": ["page", "list"],
    "监控": ["monitor", "camera", "device", "stream"],
    "磅秤": ["pound", "bound", "weight"],
    "过磅": ["pound", "bound", "weight"],
    "称重": ["pound", "bound", "weight"],
}


def _query_tokens(query: str) -> List[str]:
    tokens = re.findall(r"[\u4e00-\u9fff]{2,}|\w{3,}", (query or "").lower())
    for zh, hints in _QUERY_API_HINTS.items():
        if zh in query:
            tokens.extend(hints)
    return list(dict.fromkeys(tokens))


def _extract_local_frontend_apis(query: str, limit: int = 12) -> List[Dict[str, Any]]:
    root = Path(__file__).resolve().parent.parent
    tokens = _query_tokens(query)
    candidates = []
    patterns = [
        "**/src/views/**/api/*.js",
        "**/src/**/api/*.js",
    ]
    seen_files = set()
    for pattern in patterns:
        for path in root.glob(pattern):
            path_key = str(path)
            if path_key in seen_files or "node_modules" in path_key or path.stat().st_size > 500000:
                continue
            seen_files.add(path_key)
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            haystack = f"{path_key}\n{text}".lower()
            score = sum(1 for token in tokens if token and token.lower() in haystack)
            if score <= 0:
                continue
            urls = re.findall(r"""url\s*:\s*['"]([^'"]+)['"]|request\.\w+\(\s*['"]([^'"]+)['"]|['"](/recycle/[^'"]+|/[^'"]*(?:device|pound|bound|stream|ptz|wms)[^'"]*)['"]""", text, re.I)
            for groups in urls:
                url = next((g for g in groups if g), "")
                if not url or url.startswith("http"):
                    continue
                near = text[max(0, text.find(url) - 180): text.find(url) + 220] if url in text else ""
                method_match = re.search(r"""method\s*:\s*['"](\w+)['"]""", near, re.I)
                method = method_match.group(1).upper() if method_match else "GET"
                url_hits = sum(1 for token in tokens if token and token.lower() in url.lower())
                candidates.append({
                    "method": method,
                    "path": url,
                    "url": _strip_recycle_prefix(url),
                    "summary": f"前端代码接口 {url}",
                    "tags": Path(path).parent.parent.name,
                    "similarity": min(0.9, 0.5 + score * 0.02 + url_hits * 0.12),
                    "source": "local_frontend_code",
                })
    unique = {}
    for item in candidates:
        key = (item["method"], item["url"])
        if key not in unique or item["similarity"] > unique[key]["similarity"]:
            unique[key] = item
    return sorted(unique.values(), key=lambda x: x["similarity"], reverse=True)[:limit]


def retrieve_iteration_rag_context(query: str) -> Dict[str, Any]:
    context = {"apis": [], "frontend_code": [], "backend_code": [], "manual": "", "decision": {}}
    if not query or not query.strip():
        return context

    decision_apis = []
    try:
        from knowledge.decision_rag import get_decision_rag
        decision = get_decision_rag().retrieve_knowledge_v2(
            query=query,
            context_type="case_generation",
            max_tokens=2000,
        )
        context["decision"] = {
            "modules": decision.get("modules", []),
            "priority": decision.get("priority"),
            "risk_level": decision.get("risk_level"),
            "confidence": decision.get("confidence"),
            "fallback": decision.get("fallback", False),
        }
        decision_apis = _compact_items(
            decision.get("apis", []),
            ["method", "path", "summary", "tags", "similarity"],
            limit=10,
        )
    except Exception as e:
        logger.warning("决策级 RAG 检索失败: %s", e)

    try:
        from utils.knowledge_prompt_helper import get_knowledge_helper
        helper = get_knowledge_helper()
        vector_apis = _compact_items(
            helper.search_related_apis(query, top_k=10),
            ["method", "path", "summary", "tags", "similarity"],
            limit=10,
        )
        local_apis = _extract_local_frontend_apis(query, limit=12)
        merged = {}
        for api in local_apis + decision_apis + vector_apis:
            api_url = api.get("url") or api.get("path") or ""
            if not api_url:
                continue
            api["url"] = _strip_recycle_prefix(api_url)
            key = (api.get("method", "GET"), api["url"])
            if key not in merged or float(api.get("similarity") or 0) > float(merged[key].get("similarity") or 0):
                merged[key] = api
        context["apis"] = sorted(merged.values(), key=lambda x: float(x.get("similarity") or 0), reverse=True)[:12]
        context["frontend_code"] = _compact_items(
            helper.search_related_code(query, "frontend", top_k=5),
            ["filename", "path", "language", "functions", "similarity"],
            limit=5,
        )
        context["backend_code"] = _compact_items(
            helper.search_related_code(query, "backend", top_k=5),
            ["filename", "path", "language", "functions", "similarity"],
            limit=5,
        )
    except Exception as e:
        logger.warning("知识库 API/代码检索失败: %s", e)

    try:
        from knowledge.manual_retriever import retrieve_manual_context
        manual = retrieve_manual_context(query, n_results=5)
        if manual:
            context["manual"] = manual[:6000]
    except Exception as e:
        logger.warning("操作手册检索失败: %s", e)

    return context


def _format_rag_context(context: Dict[str, Any]) -> str:
    return json.dumps(context or {}, ensure_ascii=False, indent=2)


def _normalize_execution_config(config: Any) -> Any:
    if not isinstance(config, dict):
        return None
    method = (config.get("method") or "").upper()
    url = config.get("url") or config.get("path") or ""
    if not method or not url:
        return None
    normalized = {
        "method": method,
        "url": _strip_recycle_prefix(url),
        "headers": config.get("headers") if isinstance(config.get("headers"), dict) else {"Content-Type": "application/json"},
        "body": config.get("body") if isinstance(config.get("body"), (dict, list, str)) else {},
        "query_params": config.get("query_params") if isinstance(config.get("query_params"), dict) else {},
        "timeout": config.get("timeout") or 10,
    }
    return normalized


def _requirement_trace_candidates(requirements_text: str) -> List[str]:
    candidates = _split_requirement_sentences(requirements_text)
    return sorted(set(candidates), key=len, reverse=True)


def _point_has_requirement_trace(point: Dict[str, Any], trace_candidates: List[str]) -> bool:
    trace = str(point.get("requirement_trace") or "").strip()
    if not trace:
        return False
    return any(trace in candidate or candidate in trace for candidate in trace_candidates)


def _normalize_llm_result(parsed: Dict[str, Any], rag_context: Dict[str, Any], requirements_text: str = "") -> Dict[str, Any]:
    result = _empty_result()
    trace_candidates = _requirement_trace_candidates(requirements_text)
    for key in EMPTY_RESULT:
        if key in parsed and isinstance(parsed[key], list):
            result[key] = parsed[key]

    normalized_points = []
    for item in result["test_points"]:
        if not isinstance(item, dict):
            continue
        point = dict(item)
        if trace_candidates and not _point_has_requirement_trace(point, trace_candidates):
            point_text = str(point.get("test_point") or "")
            matched_trace = next((trace for trace in trace_candidates if trace and trace in point_text), "")
            if not matched_trace:
                continue
            point["requirement_trace"] = matched_trace[:120]
        rec_api = point.get("recommended_api")
        if isinstance(rec_api, dict) and rec_api.get("url") and not rec_api.get("path"):
            rec_api["path"] = rec_api.get("url")
        if isinstance(rec_api, dict):
            api_url = rec_api.get("url") or rec_api.get("path")
            if api_url:
                rec_api["url"] = _strip_recycle_prefix(api_url)
            point["recommended_api"] = rec_api

        point["execution_config"] = _normalize_execution_config(point.get("execution_config"))
        if not point["execution_config"] and isinstance(rec_api, dict):
            api_url = rec_api.get("url") or rec_api.get("path")
            api_method = rec_api.get("method")
            point["execution_config"] = _normalize_execution_config({
                "method": api_method,
                "url": api_url,
                "headers": {"Content-Type": "application/json"},
                "body": {},
                "query_params": {},
                "timeout": 10,
            })
        normalized_points.append(point)
    result["test_points"] = normalized_points
    result["_rag_context"] = rag_context
    return result


def _select_api_for_text(text: str, rag_context: Dict[str, Any]) -> Any:
    apis = rag_context.get("apis", []) if isinstance(rag_context, dict) else []
    if not apis:
        return None
    tokens = _query_tokens(text or "")
    scored = []
    for api in apis:
        if not isinstance(api, dict):
            continue
        haystack = " ".join([
            str(api.get("path", "")),
            str(api.get("url", "")),
            str(api.get("summary", "")),
            str(api.get("tags", "")),
        ]).lower()
        score = float(api.get("similarity") or 0)
        matched_tokens = 0
        for token in tokens:
            if token in haystack:
                score += 0.1
                matched_tokens += 1
        url_text = f"{api.get('url', '')} {api.get('path', '')}".lower()
        if "云台" in (text or "") and "ptz" in url_text:
            score += 0.35
        if "播放" in (text or "") and "stream" in url_text:
            score += 0.35
        if "列表" in (text or "") and ("page" in url_text or "list" in url_text):
            score += 0.35
        if api.get("source") != "local_frontend_code" and score < 0.6 and matched_tokens == 0:
            continue
        if api.get("source") == "local_frontend_code" and score < 0.55:
            continue
        scored.append((score, api))
    if not scored:
        return None
    scored.sort(key=lambda x: x[0], reverse=True)
    best = dict(scored[0][1])
    api_url = best.get("url") or best.get("path")
    if api_url:
        best["url"] = _strip_recycle_prefix(api_url)
    best["confidence"] = round(min(scored[0][0], 0.99), 4)
    return best


def analyze_requirements_with_llm(requirements: List[Dict[str, str]]) -> Dict[str, Any]:
    """尝试用 LLM 解析需求"""
    try:
        from ai.ai_client import AIClient
        client = AIClient()

        combined = "\n\n".join([
            f"需求标题: {r.get('title', '')}\n需求内容: {r.get('content', '')}"
            for r in requirements
        ])

        rag_context = retrieve_iteration_rag_context(combined)
        prompt = (
            "请解析下面这一次用户选中的需求。必须以【需求文本】为唯一事实来源；"
            "知识库检索上下文只允许用于辅助匹配 API、模块和字段，不能扩展出需求原文没有提到的功能。\n\n"
            "【需求文本】\n"
            f"{combined}\n\n"
            "【知识库检索上下文】\n"
            f"{_format_rag_context(rag_context)}\n\n"
            "输出要求：\n"
            "1. 每个 test_point 必须带 requirement_trace，值必须是需求原文里的短句。\n"
            "2. 如果某个 API 只是模块相似但动作不匹配，recommended_api 和 execution_config 必须为 null。\n"
            "3. 不要生成通用的正向/异常/边界三件套，除非需求原文本身包含对应条件。\n"
            "4. 优先少量、准确、可执行的测试点。"
        )
        raw = client.generate_text(prompt, system_prompt=_SYSTEM_PROMPT, temperature=0.3)

        # 提取 JSON
        start = raw.find('{')
        end = raw.rfind('}') + 1
        if start >= 0 and end > start:
            parsed = json.loads(raw[start:end])
            result = _normalize_llm_result(parsed, rag_context, combined)
            result["_source"] = "llm"
            logger.info("LLM 需求解析成功, test_points=%d", len(result["test_points"]))
            return result
        else:
            logger.warning("LLM 返回无法解析为 JSON，回退到 fallback")
            return None
    except Exception as e:
        logger.warning("LLM 调用失败: %s, 回退到 fallback", e)
        return None


def _extract_sub_features(content: str) -> List[str]:
    """从需求内容中提取子功能点（按编号、标题、分号等拆分）"""
    features = []
    # 匹配编号开头的行: "1." "1、" "1)" "(1)" "①" 或 "需求1:" 等
    numbered = re.findall(
        r'(?:^|\n)\s*(?:\d+[.、)）]|\(\d+\)|[①②③④⑤⑥⑦⑧⑨⑩]|需求\d+[：:]?)\s*(.+?)(?=\n|$)',
        content
    )
    if numbered:
        features.extend([s.strip() for s in numbered if len(s.strip()) > 4])

    # 匹配【xxx】标题格式
    bracketed = re.findall(r'【([^】]{2,50})】', content)
    features.extend(bracketed)

    # 匹配"支持xxx"、"新增xxx"、"展示xxx"开头的短句
    action_phrases = re.findall(
        r'(?:支持|新增|展示|实现|提供|增加|优化|修复|调整|设置|配置|绑定|对接|获取|控制|录像|拍摄|播放|打印|导出|上传|下载|监控|刷新|保存|删除|编辑|查看)[\u4e00-\u9fff\w]{4,40}',
        content
    )
    features.extend(action_phrases)

    # 去重并保持顺序
    seen = set()
    unique = []
    for f in features:
        f_clean = f.strip().rstrip('。，,;；')
        if f_clean and f_clean not in seen and len(f_clean) > 3:
            seen.add(f_clean)
            unique.append(f_clean)
    return unique


def _split_requirement_sentences(content: str) -> List[str]:
    sentences = []
    for raw in re.split(r'[。；;\n]+', content or ""):
        sentence = re.sub(r'^\s*(?:\d+[.、)）]|\(\d+\)|[①②③④⑤⑥⑦⑧⑨⑩]|[-*])\s*', '', raw).strip()
        sentence = sentence.strip('，, ')
        if len(sentence) >= 4:
            sentences.append(sentence)
    return sentences


def _is_actionable_requirement_sentence(sentence: str) -> bool:
    action_keywords = [
        "支持", "新增", "展示", "显示", "实现", "提供", "增加", "优化", "修复", "调整",
        "设置", "配置", "绑定", "对接", "获取", "控制", "播放", "打印", "导出", "上传",
        "下载", "监控", "刷新", "保存", "删除", "编辑", "查看", "选择", "录入", "解析",
        "回填", "带出", "校验", "提示", "生成", "同步", "筛选", "查询", "排序", "分页",
    ]
    rule_keywords = ["必须", "不允许", "不能", "需要", "应该", "至少", "最多", "不超过", "默认", "自动", "手动"]
    return any(kw in sentence for kw in action_keywords + rule_keywords)


def _make_requirement_test_point(sentence: str, title: str, rag_context: Dict[str, Any]) -> Dict[str, Any]:
    trace = sentence[:120]
    recommended_api = _select_api_for_text(sentence, rag_context)
    execution_config = None
    if recommended_api:
        execution_config = _normalize_execution_config({
            "method": recommended_api.get("method"),
            "url": recommended_api.get("url") or recommended_api.get("path"),
            "headers": {"Content-Type": "application/json"},
            "body": {},
            "query_params": {},
            "timeout": 10,
        })
    return {
        "test_point": f"验证{trace}",
        "priority": "high" if any(kw in sentence for kw in ["必须", "不能", "不允许", "自动", "回填", "校验"]) else "medium",
        "test_type": "api" if execution_config else "functional",
        "risk_level": "P1" if any(kw in sentence for kw in ["必须", "不能", "不允许", "异常", "失败", "权限", "数据"]) else "P2",
        "module_name": title[:40],
        "requirement_trace": trace,
        "recommended_api": recommended_api,
        "execution_config": execution_config,
    }


def analyze_requirements_fallback(requirements: List[Dict[str, str]]) -> Dict[str, Any]:
    """规则型 fallback: 只按需求原文生成可追溯测试点，避免泛化模板。"""
    result = {**_empty_result(), "_source": "fallback"}
    combined = "\n\n".join([
        f"需求标题: {r.get('title', '')}\n需求内容: {r.get('content', '')}"
        for r in requirements
    ])
    rag_context = retrieve_iteration_rag_context(combined)
    result["_rag_context"] = rag_context

    for req in requirements:
        title = (req.get("title") or "").strip()
        content = (req.get("content") or "").strip()
        sentences = _split_requirement_sentences(content)
        sub_features = _extract_sub_features(content)

        if title:
            result["functional_points"].append(title)
        result["functional_points"].extend(sub_features)

        rule_keywords = ["必须", "不允许", "不能", "需要", "应该", "至少", "最多", "不超过",
                         "范围", "格式", "限制", "校验", "默认", "有效", "自动", "手动"]
        scope_keywords = ["模块", "页面", "接口", "数据库", "表", "字段", "关联", "依赖",
                          "上游", "下游", "组件", "弹窗", "对话框", "列表", "摄像头", "设备"]
        risk_keywords = ["安全", "性能", "并发", "权限", "敏感", "数据丢失", "兼容", "回滚",
                         "异常", "超时", "断开", "离线", "失败", "重连", "冲突"]

        actionable_sentences = []
        for sentence in sentences:
            if any(kw in sentence for kw in rule_keywords):
                result["business_rules"].append(sentence)
            if any(kw in sentence for kw in scope_keywords):
                result["impact_scope"].append(sentence)
            if any(kw in sentence for kw in risk_keywords):
                result["risk_points"].append(sentence)
            if _is_actionable_requirement_sentence(sentence):
                actionable_sentences.append(sentence)

        if not actionable_sentences:
            if sentences:
                actionable_sentences = sentences[:2]
            elif title:
                actionable_sentences = [title]

        for sentence in actionable_sentences[:8]:
            result["test_points"].append(_make_requirement_test_point(sentence, title, rag_context))

        question_keywords = ["是否", "还是", "或者", "待定", "TBD", "?", "？"]
        for sentence in sentences:
            if any(kw in sentence for kw in question_keywords):
                result["confirm_questions"].append(sentence)

    for key in ["functional_points", "business_rules", "impact_scope", "risk_points", "confirm_questions"]:
        seen = set()
        unique = []
        for item in result[key]:
            if item and item not in seen:
                seen.add(item)
                unique.append(item)
        result[key] = unique

    result["api_mappings"] = [
        {
            "feature": api.get("summary") or api.get("path"),
            "method": api.get("method"),
            "url": _strip_recycle_prefix(api.get("path") or api.get("url") or ""),
            "summary": api.get("summary", ""),
            "confidence": api.get("similarity", 0),
        }
        for api in rag_context.get("apis", [])
        if isinstance(api, dict) and float(api.get("similarity") or 0) >= 0.65
    ]

    return result


def analyze_requirements(requirements: List[Dict[str, str]]) -> Dict[str, Any]:
    """主入口: LLM 优先，失败自动回退 fallback"""
    if not requirements:
        return {**_empty_result(), "_source": "empty"}

    # 检查是否有 AI 配置（支持多种环境变量名，排除 none/false/空值）
    ai_provider = (
        os.getenv("AI_PROVIDER", "")
        or os.getenv("DEFAULT_AI_PROVIDER", "")
        or os.getenv("TESTCASE_GENERATION_AI_PROVIDER", "")
    ).strip().lower()
    if ai_provider and ai_provider not in ("none", "false", "off", "0"):
        llm_result = analyze_requirements_with_llm(requirements)
        if llm_result:
            return llm_result

    # fallback
    return analyze_requirements_fallback(requirements)


def generate_test_cases_from_points(test_points: List[Dict[str, Any]], iteration_name: str = "") -> List[Dict[str, Any]]:
    """根据测试点生成测试用例结构（规则型，不依赖LLM）"""
    cases = []
    for tp in test_points:
        point_text = tp.get("test_point", "") if isinstance(tp, dict) else str(tp)
        priority = tp.get("priority", "medium") if isinstance(tp, dict) else "medium"
        test_type = tp.get("test_type", "functional") if isinstance(tp, dict) else "functional"
        execution_config = tp.get("execution_config") if isinstance(tp, dict) else None
        recommended_api = tp.get("recommended_api") if isinstance(tp, dict) else None

        case = {
            "name": point_text[:200],
            "description": f"[AI生成] 基于测试点: {point_text}",
            "method": execution_config.get("method", "GET") if isinstance(execution_config, dict) else "GET",
            "path": execution_config.get("url", "/") if isinstance(execution_config, dict) else "/",
            "headers": "{}",
            "body": "{}",
            "expected_status": 200,
            "priority": priority,
            "case_type": "api" if isinstance(execution_config, dict) else test_type,
            "source": "ai_generated",
            "module_name": tp.get("module_name", "") if isinstance(tp, dict) else "",
            "risk_level": tp.get("risk_level", "P1") if isinstance(tp, dict) else "P1",
            "test_point_id": tp.get("id") if isinstance(tp, dict) else None,
            "recommended_api": recommended_api,
            "execution_config": execution_config,
            "ai_generated": True,
        }
        cases.append(case)
    return cases
