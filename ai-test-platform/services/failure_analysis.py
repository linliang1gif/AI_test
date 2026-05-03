"""P2-8: UI Failure Analysis — rule-based + optional AI enhancement."""
import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from services.sanitize import sanitize_headers, sanitize_url, sanitize_text

logger = logging.getLogger(__name__)

# ── Failure categories ──────────────────────────────────────────
FAILURE_CATEGORIES = [
    "selector_not_found",
    "element_not_visible",
    "element_not_clickable",
    "page_timeout",
    "navigation_failed",
    "assertion_failed",
    "console_error",
    "network_error",
    "visual_diff",
    "auth_or_permission",
    "test_data_issue",
    "environment_issue",
    "app_bug_suspected",
    "script_or_case_design_issue",
    "unknown",
]


# ── Evidence builder ────────────────────────────────────────────
def _build_evidence(rc_data: Dict[str, Any]) -> Dict[str, Any]:
    """Build sanitized evidence dict from run_case data.

    Never includes raw Cookie / Authorization / Token.
    Does NOT read trace.zip content.
    """
    resp = rc_data.get("response_snapshot") or {}
    req = rc_data.get("request_snapshot") or {}

    console_logs = resp.get("console_logs") or []
    network_errors = resp.get("network_errors") or []

    # Sanitize network entries
    sanitized_network = []
    for ne in network_errors[:20]:
        entry: Dict[str, Any] = {}
        if "url" in ne:
            entry["url"] = sanitize_url(ne["url"])
        if "status" in ne:
            entry["status"] = ne["status"]
        if "method" in ne:
            entry["method"] = ne["method"]
        if "error" in ne:
            entry["error"] = sanitize_text(str(ne["error"]))
        sanitized_network.append(entry)

    # Sanitize console entries
    sanitized_console = []
    for ce in console_logs[:20]:
        text = ce.get("text", "") if isinstance(ce, dict) else str(ce)
        sanitized_console.append({"text": sanitize_text(text), "type": ce.get("type", "error") if isinstance(ce, dict) else "error"})

    assertion_details = rc_data.get("assertion_details") or []
    failed_assertions = [a for a in assertion_details if not a.get("passed")]

    visual_results = resp.get("visual_results") or []
    visual_failed = [v for v in visual_results if v.get("status") == "failed" or v.get("match_percentage", 100) < (v.get("threshold", 95))]

    return {
        "case_id": rc_data.get("test_case_id", ""),
        "error_message": sanitize_text(rc_data.get("error_message") or ""),
        "console_errors": sanitized_console,
        "network_errors": sanitized_network,
        "failed_assertions": failed_assertions,
        "visual_failed": visual_failed,
        "trace_path": resp.get("trace_path", ""),
        "failure_screenshot": resp.get("failure_screenshot", ""),
        "screenshots": resp.get("screenshots") or [],
    }


# ── Rule engine ─────────────────────────────────────────────────
def _rule_analyze(evidence: Dict[str, Any]) -> Dict[str, Any]:
    """Rule-based failure analysis. Works without AI provider."""

    error_msg = (evidence.get("error_message") or "").lower()
    console_errors = evidence.get("console_errors") or []
    network_errors = evidence.get("network_errors") or []
    failed_assertions = evidence.get("failed_assertions") or []
    visual_failed = evidence.get("visual_failed") or []

    category = "unknown"
    confidence = 0.5
    root_cause = ""
    evidence_list: List[str] = []
    suggested_action = ""
    should_retry = False
    should_create_bug = False
    should_update_selector = False
    should_update_baseline = False

    # ── Rule 1: selector / timeout ──
    if any(kw in error_msg for kw in ("waiting for selector", "waiting for locator", "selector", "locator")):
        category = "selector_not_found"
        confidence = 0.9
        root_cause = "Playwright 等待元素超时，目标 selector 在页面上未找到。"
        evidence_list.append(f"error: {evidence.get('error_message', '')[:200]}")
        suggested_action = "检查 selector 是否正确，页面是否加载完成。"
        should_update_selector = True
    elif any(kw in error_msg for kw in ("timeout", "timed out", "navigation timeout")):
        category = "page_timeout"
        confidence = 0.85
        root_cause = "页面操作超时，可能网络慢或页面加载异常。"
        evidence_list.append(f"error: {evidence.get('error_message', '')[:200]}")
        suggested_action = "检查网络环境和页面加载性能，考虑增加 timeout。"
        should_retry = True

    # ── Rule 2: element not visible ──
    elif "not visible" in error_msg or "element is not visible" in error_msg:
        category = "element_not_visible"
        confidence = 0.88
        root_cause = "目标元素存在但不可见（display:none/visibility:hidden 或被遮挡）。"
        evidence_list.append(f"error: {evidence.get('error_message', '')[:200]}")
        suggested_action = "检查页面样式，确认元素在交互时是否可见。"

    # ── Rule 3: element not clickable ──
    elif any(kw in error_msg for kw in ("not clickable", "intercepted", "click intercepted")):
        category = "element_not_clickable"
        confidence = 0.85
        root_cause = "元素被其他元素遮挡或不可点击。"
        evidence_list.append(f"error: {evidence.get('error_message', '')[:200]}")
        suggested_action = "检查是否有弹窗、遮罩覆盖目标元素。"

    # ── Rule 4: navigation ──
    elif any(kw in error_msg for kw in ("navigation", "net::err_", "refused", "dns")):
        category = "navigation_failed"
        confidence = 0.85
        root_cause = "页面导航失败，目标地址不可达。"
        evidence_list.append(f"error: {evidence.get('error_message', '')[:200]}")
        suggested_action = "检查目标 URL 和网络连通性。"
        should_retry = True

    # ── Rule 5: network 500 → app_bug_suspected ──
    elif any(ne.get("status", 0) >= 500 for ne in network_errors):
        category = "app_bug_suspected"
        confidence = 0.8
        err_urls = [sanitize_url(ne.get("url", "")) for ne in network_errors if ne.get("status", 0) >= 500]
        root_cause = f"后端接口返回 5xx 错误。"
        evidence_list.extend([f"{ne.get('method','?')} {ne.get('url','?')} → {ne.get('status','?')}" for ne in network_errors if ne.get("status", 0) >= 500][:5])
        suggested_action = "检查后端服务日志，确认接口是否有 Bug。"
        should_create_bug = True

    # ── Rule 6: network 401/403 → auth ──
    elif any(ne.get("status") in (401, 403) for ne in network_errors):
        category = "auth_or_permission"
        confidence = 0.85
        root_cause = "接口返回 401/403，登录态或权限不足。"
        evidence_list.extend([f"{ne.get('method','?')} {ne.get('url','?')} → {ne.get('status','?')}" for ne in network_errors if ne.get("status") in (401, 403)][:5])
        suggested_action = "检查测试用例的登录配置和 Cookie/Token 有效性。"

    # ── Rule 7: visual diff ──
    elif visual_failed:
        category = "visual_diff"
        confidence = 0.9
        root_cause = "视觉对比失败，页面外观与基线不一致。"
        for vf in visual_failed[:3]:
            evidence_list.append(f"visual: match={vf.get('match_percentage', '?')}%, threshold={vf.get('threshold', '?')}%")
        suggested_action = "检查 UI 变更是否预期，如预期则更新 baseline。"
        should_update_baseline = True

    # ── Rule 8: assertion failed ──
    elif failed_assertions:
        category = "assertion_failed"
        confidence = 0.88
        root_cause = "断言检查失败。"
        for fa in failed_assertions[:5]:
            evidence_list.append(f"assert:{fa.get('type','')} expected={fa.get('value','')}, actual={fa.get('actual','')}")
        suggested_action = "检查页面是否符合预期，或断言条件是否需要更新。"

    # ── Rule 9: console error ──
    elif console_errors:
        category = "console_error"
        confidence = 0.6
        root_cause = "页面存在 console 错误。"
        for ce in console_errors[:5]:
            evidence_list.append(f"console: {ce.get('text', '')[:150]}")
        suggested_action = "检查前端代码是否有 JS 异常。"

    # ── Rule 10: test data ──
    elif any(kw in error_msg for kw in ("not found", "no data", "empty", "no record", "记录不存在", "数据为空")):
        category = "test_data_issue"
        confidence = 0.65
        root_cause = "测试数据缺失或查询不到。"
        evidence_list.append(f"error: {evidence.get('error_message', '')[:200]}")
        suggested_action = "检查测试数据是否已准备好。"

    # ── Fallback ──
    else:
        category = "unknown"
        confidence = 0.3
        root_cause = evidence.get("error_message", "未知错误")[:300]
        if evidence.get("error_message"):
            evidence_list.append(f"error: {evidence.get('error_message', '')[:200]}")
        suggested_action = "人工检查截图和 trace 文件以确定根因。"

    return {
        "failure_category": category,
        "confidence": round(confidence, 2),
        "root_cause_summary": root_cause,
        "evidence": evidence_list[:10],
        "suggested_action": suggested_action,
        "should_retry": should_retry,
        "should_create_bug": should_create_bug,
        "should_update_selector": should_update_selector,
        "should_update_baseline": should_update_baseline,
        "analysis_mode": "rule",
    }


# ── AI enhanced analysis ────────────────────────────────────────
def _ai_analyze(evidence: Dict[str, Any], rule_result: Dict[str, Any]) -> Dict[str, Any]:
    """AI-enhanced failure analysis. Falls back to rule_result on error."""
    ai_provider = os.getenv("AI_PROVIDER", "none")
    if ai_provider == "none":
        return rule_result

    try:
        from services.ai_service import get_ai_service
        ai_svc = get_ai_service()
        if not ai_svc:
            logger.info("AI service not available, falling back to rule analysis")
            return rule_result

        # Build sanitized prompt — never include Cookie/Token/Authorization
        prompt = _build_ai_prompt(evidence, rule_result)

        response = ai_svc.chat(prompt, system_prompt=(
            "You are a test failure analysis expert. Analyze the given UI test failure evidence and provide structured analysis. "
            "Response must be valid JSON with keys: failure_category, confidence, root_cause_summary, evidence, suggested_action, "
            "should_retry, should_create_bug, should_update_selector, should_update_baseline."
        ))

        if response:
            import json
            try:
                ai_result = json.loads(response)
                # Validate category
                if ai_result.get("failure_category") not in FAILURE_CATEGORIES:
                    ai_result["failure_category"] = rule_result["failure_category"]
                ai_result["analysis_mode"] = "ai"
                # Ensure all required keys
                for key in ("confidence", "root_cause_summary", "evidence", "suggested_action",
                            "should_retry", "should_create_bug", "should_update_selector", "should_update_baseline"):
                    if key not in ai_result:
                        ai_result[key] = rule_result[key]
                return ai_result
            except (json.JSONDecodeError, TypeError):
                logger.warning("AI response not valid JSON, falling back to rule")
                return rule_result

    except Exception as e:
        logger.warning(f"AI analysis failed, falling back to rule: {e}")

    return rule_result


def _build_ai_prompt(evidence: Dict[str, Any], rule_result: Dict[str, Any]) -> str:
    """Build AI prompt from sanitized evidence. No Cookie/Token/Auth."""
    parts = [
        "Analyze this UI test failure:",
        f"Error: {evidence.get('error_message', '')[:500]}",
    ]
    if evidence.get("console_errors"):
        console_texts = [ce.get("text", "")[:100] for ce in evidence["console_errors"][:5]]
        parts.append(f"Console errors: {console_texts}")
    if evidence.get("network_errors"):
        net_summary = [f"{ne.get('method','?')} {ne.get('url','?')[:80]} → {ne.get('status','?')}" for ne in evidence["network_errors"][:5]]
        parts.append(f"Network errors: {net_summary}")
    if evidence.get("failed_assertions"):
        parts.append(f"Failed assertions: {evidence['failed_assertions'][:5]}")
    if evidence.get("visual_failed"):
        parts.append(f"Visual diffs: {evidence['visual_failed'][:3]}")
    parts.append(f"Rule analysis suggests: {rule_result['failure_category']} (confidence={rule_result['confidence']})")
    parts.append(f"Provide your analysis as JSON.")
    return "\n".join(parts)


# ── Public API ──────────────────────────────────────────────────
def analyze_failure(rc_data: Dict[str, Any], run_id: str = "") -> Dict[str, Any]:
    """Analyze a single failed RunCase.

    Args:
        rc_data: Dict with keys from RunCase (test_case_id, error_message, response_snapshot, etc.)
        run_id: The run ID for context

    Returns:
        Analysis result dict
    """
    evidence = _build_evidence(rc_data)
    rule_result = _rule_analyze(evidence)

    # Try AI enhancement
    result = _ai_analyze(evidence, rule_result)

    result["case_id"] = rc_data.get("test_case_id", "")
    result["run_id"] = run_id
    result["created_at"] = datetime.now().isoformat()

    return result


def analyze_run_failures(run_cases_data: List[Dict[str, Any]], run_id: str = "") -> List[Dict[str, Any]]:
    """Analyze all failed/skipped cases in a run.

    Args:
        run_cases_data: List of RunCase dicts (with response_snapshot, error_message, etc.)
        run_id: Run ID

    Returns:
        List of analysis results
    """
    results = []
    for rc in run_cases_data:
        status = rc.get("status", "")
        if status in ("failed", "skipped", "error"):
            analysis = analyze_failure(rc, run_id)
            results.append(analysis)
        # Also check for visual failures in passed cases
        elif status == "passed":
            resp = rc.get("response_snapshot") or {}
            visual_results = resp.get("visual_results") or []
            if any(v.get("status") == "failed" for v in visual_results):
                analysis = analyze_failure(rc, run_id)
                results.append(analysis)
    return results


def build_failure_summary(analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build summary statistics from analysis results."""
    if not analyses:
        return {}

    category_counts: Dict[str, int] = {}
    high_confidence = 0
    bug_count = 0
    retry_count = 0
    selector_count = 0
    baseline_count = 0

    for a in analyses:
        cat = a.get("failure_category", "unknown")
        category_counts[cat] = category_counts.get(cat, 0) + 1
        if a.get("confidence", 0) >= 0.8:
            high_confidence += 1
        if a.get("should_create_bug"):
            bug_count += 1
        if a.get("should_retry"):
            retry_count += 1
        if a.get("should_update_selector"):
            selector_count += 1
        if a.get("should_update_baseline"):
            baseline_count += 1

    return {
        "total_analyzed": len(analyses),
        "category_distribution": category_counts,
        "high_confidence_count": high_confidence,
        "should_create_bug_count": bug_count,
        "should_retry_count": retry_count,
        "should_update_selector_count": selector_count,
        "should_update_baseline_count": baseline_count,
    }
