"""
Phase 19: AI 报告分析服务

两层策略:
1. 规则分析兜底 (rule_based) — 不依赖外部 AI
2. LLM 分析增强 (llm) — 可选，失败自动回退 rule_based
"""

import logging

logger = logging.getLogger(__name__)

import json
import os
import math
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from sqlalchemy.orm import Session

from database.models import (
    TestRun, RunCase, TestCase, Project, Environment,
    AiReportAnalysis,
)


# ── 配置 ─────────────────────────────────────────────────────
AI_REPORT_ENABLED = os.getenv("AI_REPORT_ENABLED", "true").lower() == "true"
AI_REPORT_PROVIDER = os.getenv("AI_REPORT_PROVIDER", "nvidia")
AI_REPORT_MODEL = os.getenv("AI_REPORT_MODEL", "deepseek-ai/deepseek-v4-pro")
AI_REPORT_API_KEY = os.getenv("AI_REPORT_API_KEY", "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")
AI_REPORT_BASE_URL = os.getenv("AI_REPORT_BASE_URL", "https://integrate.api.nvidia.com")
AI_REPORT_TIMEOUT = int(os.getenv("AI_REPORT_TIMEOUT", "60"))

# ── 多模型路由 ── 按优先级尝试，第一个成功就返回 ────────────
_NVIDIA_KEY = AI_REPORT_API_KEY
_NVIDIA_BASE = "https://integrate.api.nvidia.com"

MODEL_ROUTES = [
    {"name": "deepseek-v4-pro", "model": "deepseek-ai/deepseek-v4-pro", "api_base": _NVIDIA_BASE, "api_key": _NVIDIA_KEY, "timeout": 30},
    {"name": "llama-70b",       "model": "meta/llama-3.1-70b-instruct", "api_base": _NVIDIA_BASE, "api_key": _NVIDIA_KEY, "timeout": 20},
    {"name": "llama-8b",        "model": "meta/llama-3.1-8b-instruct",  "api_base": _NVIDIA_BASE, "api_key": _NVIDIA_KEY, "timeout": 10},
]


# ── 失败分类中文分析模板 ─────────────────────────────────────
_FAILURE_ANALYSIS_TEMPLATES: Dict[str, Dict[str, str]] = {
    "auth_error": {
        "analysis": "认证失败，可能是 Token 未注入、Token 过期、Authorization Header 格式错误。",
        "suggestion": "检查环境认证配置、请求头注入逻辑、登录接口返回 token 是否正确。",
    },
    "env_error": {
        "analysis": "环境不可用，可能是 base_url 错误、服务未启动、网络连接失败。",
        "suggestion": "检查环境地址、后端服务端口、网络连通性。",
    },
    "request_error": {
        "analysis": "请求参数错误，可能是必填字段缺失、字段类型错误、请求体结构不符合接口要求。",
        "suggestion": "检查用例参数生成规则和 OpenAPI requestBody 定义。",
    },
    "response_error": {
        "analysis": "响应异常，可能是资源不存在、服务端错误或响应结构不符合预期。",
        "suggestion": "检查接口实现、Mock 数据、测试数据是否存在。",
    },
    "assertion_error": {
        "analysis": "接口已返回响应，但断言不通过。",
        "suggestion": "检查断言规则是否过严、响应字段是否变更、业务状态是否符合预期。",
    },
    "dependency_error": {
        "analysis": "前置依赖或业务状态不满足。",
        "suggestion": "检查用例执行顺序、前置数据准备、状态流转是否完整。",
    },
    "timeout_error": {
        "analysis": "接口响应超时。",
        "suggestion": "检查服务性能、超时时间配置、是否存在阻塞逻辑。",
    },
    "unknown_error": {
        "analysis": "失败原因未能归类。",
        "suggestion": "查看请求响应详情和后端日志，补充失败分类规则。",
    },
}


class AiReportAnalysisService:
    """AI 报告分析服务"""

    def __init__(self, db: Session):
        self.db = db

    # ── 公开方法 ──────────────────────────────────────────

    def generate_analysis(self, run_id: str, report_id: int = None, force: bool = False) -> Dict[str, Any]:
        """
        生成 AI 分析。
        - force=False: 有缓存直接返回
        - force=True: 重新生成
        - LLM 失败自动回退 rule_based
        """
        # 0. 缓存检查
        if not force:
            cached = self.get_latest_analysis(run_id)
            if cached:
                return cached

        # 1. 收集执行数据
        metrics = self._collect_metrics(run_id)
        if not metrics:
            raise ValueError(f"未找到执行记录: {run_id}")

        # 2. 先生成 rule_based（秒出）
        rule_analysis = self._rule_based_analysis(metrics)
        rule_analysis["provider"] = "rule_based"
        rule_analysis["run_id"] = run_id

        # 3. 尝试 LLM 增强
        provider = self._resolve_provider()
        analysis = rule_analysis

        if provider == "llm":
            try:
                logger.info(f"🤖 调用 LLM 分析: {AI_REPORT_MODEL} ...")
                llm_result = self._llm_analysis(metrics)
                llm_result["provider"] = "llm"
                llm_result["run_id"] = run_id
                analysis = llm_result
                logger.info(f"✅ LLM 分析完成")
            except Exception as e:
                logger.info(f"⚠️ LLM 分析失败，使用 rule_based: {e}")
                analysis = rule_analysis

        # 4. 持久化
        record = self._save_analysis(run_id, report_id, analysis)
        analysis["analysis_id"] = record.id

        return analysis

    def get_latest_analysis(self, run_id: str) -> Optional[Dict[str, Any]]:
        """获取最近一次分析结果"""
        record = (
            self.db.query(AiReportAnalysis)
            .filter(AiReportAnalysis.run_id == run_id)
            .order_by(AiReportAnalysis.created_at.desc())
            .first()
        )
        if not record:
            return None
        return self._record_to_dict(record)

    # ── 数据收集 ──────────────────────────────────────────

    def _collect_metrics(self, run_id: str) -> Optional[Dict[str, Any]]:
        run = self.db.query(TestRun).filter(TestRun.id == run_id).first()
        if not run:
            return None

        run_cases = self.db.query(RunCase).filter(RunCase.run_id == run_id).all()

        # 项目 / 环境
        project = self.db.query(Project).filter(Project.id == run.project_id).first() if run.project_id else None
        env = self.db.query(Environment).filter(Environment.id == run.environment_id).first() if run.environment_id else None

        # 基础统计
        total = run.total_cases or len(run_cases) or 0
        passed = run.passed_cases or 0
        failed = run.failed_cases or 0
        skipped = run.skipped_cases or 0
        failed_rate = (failed / total * 100) if total > 0 else 0

        # 按 failure_category 统计
        failure_categories: Dict[str, int] = {}
        failed_case_details: List[Dict] = []
        slow_cases: List[Dict] = []

        # 按 risk_level 统计
        risk_stats: Dict[str, Dict[str, int]] = {"P0": {"total": 0, "failed": 0}, "P1": {"total": 0, "failed": 0}, "P2": {"total": 0, "failed": 0}}

        # destructive 跳过统计
        destructive_skipped = 0

        for rc in run_cases:
            tc = rc.test_case
            if not tc:
                tc = self.db.query(TestCase).filter(TestCase.id == rc.test_case_id).first()

            risk = (tc.risk_level if tc else None) or "P2"
            if risk in risk_stats:
                risk_stats[risk]["total"] += 1

            if rc.status == "failed" or rc.status == "error":
                cat = (tc.failure_category if tc else None) or "unknown_error"
                failure_categories[cat] = failure_categories.get(cat, 0) + 1
                if risk in risk_stats:
                    risk_stats[risk]["failed"] += 1

                failed_case_details.append({
                    "case_id": rc.test_case_id,
                    "case_name": tc.title if tc else rc.test_case_id,
                    "failure_category": cat,
                    "risk_level": risk,
                    "error_message": (rc.error_message or "")[:200],
                    "duration_ms": round((rc.duration or 0) * 1000),
                })

            if rc.status == "skipped":
                if tc and tc.destructive:
                    destructive_skipped += 1

            if rc.duration and rc.duration > 2.0:
                slow_cases.append({
                    "case_id": rc.test_case_id,
                    "case_name": tc.title if tc else rc.test_case_id,
                    "duration_ms": round(rc.duration * 1000),
                })

        slow_cases.sort(key=lambda x: x["duration_ms"], reverse=True)

        return {
            "run_id": run_id,
            "project_name": project.name if project else f"Project #{run.project_id}",
            "env_name": env.name if env else f"Env #{run.environment_id}",
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "failed_rate": round(failed_rate, 2),
            "pass_rate": round((passed / total * 100) if total > 0 else 0, 2),
            "duration_s": round(run.duration or 0, 2),
            "failure_categories": failure_categories,
            "risk_stats": risk_stats,
            "destructive_skipped": destructive_skipped,
            "failed_case_details": failed_case_details[:20],
            "slow_cases": slow_cases[:10],
        }

    # ── 规则分析 ──────────────────────────────────────────

    def _rule_based_analysis(self, m: Dict[str, Any]) -> Dict[str, Any]:
        health_score = self._calc_health_score(m)
        release_rec = self._calc_release_recommendation(health_score, m)

        summary = self._build_summary(m, health_score, release_rec)
        key_findings = self._build_key_findings(m)
        risk_points = self._build_risk_points(m)
        failure_analysis = self._build_failure_analysis(m)
        skipped_analysis = self._build_skipped_analysis(m)
        suggestions = self._build_suggestions(m)
        next_actions = self._build_next_actions(m, release_rec)

        return {
            "health_score": health_score,
            "release_recommendation": release_rec,
            "summary": summary,
            "key_findings": key_findings,
            "risk_points": risk_points,
            "failure_analysis": failure_analysis,
            "skipped_analysis": skipped_analysis,
            "suggestions": suggestions,
            "next_actions": next_actions,
        }

    def _calc_health_score(self, m: Dict) -> int:
        score = 100
        # 1. failed_rate 每 1% 扣 1 分, 最多 40
        score -= min(int(m["failed_rate"]), 40)
        # 2. P0 failed 每条扣 10, 最多 30
        p0_failed = m["risk_stats"].get("P0", {}).get("failed", 0)
        score -= min(p0_failed * 10, 30)
        # 3. auth_error 每条扣 3, 最多 15
        score -= min(m["failure_categories"].get("auth_error", 0) * 3, 15)
        # 4. env_error 每条扣 5, 最多 20
        score -= min(m["failure_categories"].get("env_error", 0) * 5, 20)
        # 5. assertion_error 每条扣 2, 最多 15
        score -= min(m["failure_categories"].get("assertion_error", 0) * 2, 15)
        # 6. destructive skipped 每条扣 1, 最多 10
        score -= min(m["destructive_skipped"] * 1, 10)
        # 7. unknown_error 每条扣 3, 最多 10
        score -= min(m["failure_categories"].get("unknown_error", 0) * 3, 10)
        return max(score, 0)

    def _calc_release_recommendation(self, score: int, m: Dict) -> str:
        p0_failed = m["risk_stats"].get("P0", {}).get("failed", 0)
        if p0_failed > 0:
            return "block"
        if score < 60:
            return "block"
        if score < 85:
            return "caution"
        if m["failed"] > 0:
            return "caution"
        return "pass"

    def _build_summary(self, m: Dict, score: int, rec: str) -> str:
        total, passed, failed, skipped = m["total"], m["passed"], m["failed"], m["skipped"]
        parts = [
            f"本次执行共 {total} 条用例，通过 {passed} 条，失败 {failed} 条，跳过 {skipped} 条，通过率 {m['pass_rate']}%。",
            f"健康评分 {score}/100。",
        ]
        if rec == "pass":
            parts.append("整体质量良好，建议可以发布。")
        elif rec == "caution":
            parts.append("存在部分风险项，建议谨慎发布，优先修复高风险失败。")
        else:
            parts.append("存在严重质量问题，不建议发布，请修复后重新回归。")
        return "".join(parts)

    def _build_key_findings(self, m: Dict) -> List[str]:
        findings = []
        if m["pass_rate"] == 100:
            findings.append("所有用例全部通过，质量优秀。")
        elif m["pass_rate"] >= 90:
            findings.append(f"通过率 {m['pass_rate']}%，整体质量较好。")
        elif m["pass_rate"] >= 70:
            findings.append(f"通过率 {m['pass_rate']}%，存在一定数量的失败用例需要关注。")
        else:
            findings.append(f"通过率仅 {m['pass_rate']}%，大量用例失败，质量堪忧。")

        p0_f = m["risk_stats"].get("P0", {}).get("failed", 0)
        if p0_f > 0:
            findings.append(f"P0 高优先级用例有 {p0_f} 条失败，需要立即处理。")

        top_cat = max(m["failure_categories"], key=m["failure_categories"].get) if m["failure_categories"] else None
        if top_cat:
            findings.append(f"最常见失败类型: {top_cat} ({m['failure_categories'][top_cat]} 条)。")

        if m["destructive_skipped"] > 0:
            findings.append(f"{m['destructive_skipped']} 条破坏性用例被跳过，需评估覆盖风险。")

        if m["slow_cases"]:
            findings.append(f"检测到 {len(m['slow_cases'])} 个慢接口 (>2s)。")

        return findings

    def _build_risk_points(self, m: Dict) -> List[Dict[str, str]]:
        points = []
        p0_f = m["risk_stats"].get("P0", {}).get("failed", 0)
        if p0_f > 0:
            points.append({"level": "high", "description": f"P0 用例失败 {p0_f} 条，核心业务可能受影响。"})

        if m["failure_categories"].get("env_error", 0) > 0:
            points.append({"level": "high", "description": f"环境错误 {m['failure_categories']['env_error']} 条，测试环境可能不稳定。"})

        if m["failure_categories"].get("auth_error", 0) > 0:
            points.append({"level": "medium", "description": f"认证错误 {m['failure_categories']['auth_error']} 条，Token 机制可能存在问题。"})

        if m["destructive_skipped"] > 0:
            points.append({"level": "medium", "description": f"{m['destructive_skipped']} 条破坏性用例被跳过，删除/取消类操作未被覆盖。"})

        p1_f = m["risk_stats"].get("P1", {}).get("failed", 0)
        if p1_f > 0:
            points.append({"level": "medium", "description": f"P1 用例失败 {p1_f} 条，部分功能可能不正常。"})

        if m["failure_categories"].get("timeout_error", 0) > 0:
            points.append({"level": "low", "description": f"超时错误 {m['failure_categories']['timeout_error']} 条，可能存在性能问题。"})

        return points

    def _build_failure_analysis(self, m: Dict) -> List[Dict[str, Any]]:
        items = []
        for cat, count in sorted(m["failure_categories"].items(), key=lambda x: -x[1]):
            tpl = _FAILURE_ANALYSIS_TEMPLATES.get(cat, _FAILURE_ANALYSIS_TEMPLATES["unknown_error"])
            cases = [c["case_name"] for c in m["failed_case_details"] if c["failure_category"] == cat][:5]
            items.append({
                "category": cat,
                "count": count,
                "analysis": tpl["analysis"],
                "suggestion": tpl["suggestion"],
                "affected_cases": cases,
            })
        return items

    def _build_skipped_analysis(self, m: Dict) -> List[Dict[str, Any]]:
        items = []
        if m["destructive_skipped"] > 0:
            items.append({
                "reason": "destructive",
                "count": m["destructive_skipped"],
                "risk_note": "破坏性接口（删除、取消等）在本次执行中被跳过。这些接口的正确性未被验证，发布后可能存在风险。",
                "recommendation": "在非生产环境单独执行破坏性用例验证，或使用数据回滚机制。",
            })
        other_skipped = m["skipped"] - m["destructive_skipped"]
        if other_skipped > 0:
            items.append({
                "reason": "other",
                "count": other_skipped,
                "risk_note": f"有 {other_skipped} 条用例因其他原因被跳过。",
                "recommendation": "检查跳过原因，确认是否为预期行为。",
            })
        return items

    def _build_suggestions(self, m: Dict) -> List[str]:
        suggestions = []
        if m["failure_categories"].get("auth_error", 0) > 0:
            suggestions.append("优先检查认证机制：确认 Token 获取和注入流程正确。")
        if m["failure_categories"].get("env_error", 0) > 0:
            suggestions.append("排查环境连通性：确认测试环境服务已启动且网络可达。")
        if m["failure_categories"].get("assertion_error", 0) > 0:
            suggestions.append("审查断言规则：确认期望值是否需要更新，响应字段是否有变更。")
        if m["failure_categories"].get("request_error", 0) > 0:
            suggestions.append("检查请求参数生成：确认必填字段、类型和格式与 API 规范一致。")
        if m["failure_categories"].get("timeout_error", 0) > 0:
            suggestions.append("排查接口性能：检查服务端是否有阻塞逻辑或资源瓶颈。")
        if m["destructive_skipped"] > 0:
            suggestions.append("规划破坏性用例验证：在隔离环境中单独执行 DELETE/CANCEL 类接口测试。")
        if m["slow_cases"]:
            suggestions.append(f"关注慢接口性能：{len(m['slow_cases'])} 个接口响应超过 2 秒。")
        if not suggestions:
            suggestions.append("当前无需特别处理，保持良好的测试覆盖。")
        return suggestions

    def _build_next_actions(self, m: Dict, rec: str) -> List[Dict[str, str]]:
        actions = []
        if rec == "block":
            actions.append({"priority": "high", "action": "修复所有 P0 失败用例，重新执行回归测试。"})
            if m["failure_categories"].get("env_error", 0) > 0:
                actions.append({"priority": "high", "action": "排查环境问题，确保测试环境可用。"})
            actions.append({"priority": "medium", "action": "修复后重新运行完整回归套件，确认通过率达标。"})
        elif rec == "caution":
            actions.append({"priority": "high", "action": "修复高风险失败用例（P0/P1）。"})
            actions.append({"priority": "medium", "action": "评估剩余失败是否影响核心业务流程。"})
            actions.append({"priority": "low", "action": "补充失败用例的断言和错误处理逻辑。"})
        else:
            actions.append({"priority": "low", "action": "保持当前质量水平，定期运行回归测试。"})
            if m["destructive_skipped"] > 0:
                actions.append({"priority": "medium", "action": "择机验证破坏性用例。"})
        return actions

    # ── LLM 分析 ──────────────────────────────────────────

    def _resolve_provider(self) -> str:
        if not AI_REPORT_ENABLED:
            return "rule_based"
        if AI_REPORT_PROVIDER == "rule_based":
            return "rule_based"
        if not AI_REPORT_API_KEY:
            return "rule_based"
        return "llm"

    def _llm_analysis(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """多模型路由: 按优先级尝试 MODEL_ROUTES，第一个成功就返回"""
        import httpx
        import re

        prompt = self._build_llm_prompt(metrics)
        system_msg = "你是一个专业的软件测试分析师。根据测试执行数据生成结构化分析报告。输出必须是纯 JSON，不要输出 Markdown。"

        last_error = None
        for route in MODEL_ROUTES:
            model_name = route["name"]
            try:
                logger.info(f"    🔄 尝试模型: {model_name} ({route['model']})")
                headers = {
                    "Authorization": f"Bearer {route['api_key']}",
                    "Content-Type": "application/json",
                }
                body = {
                    "model": route["model"],
                    "messages": [
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2000,
                }
                with httpx.Client(timeout=route.get("timeout", 60)) as client:
                    resp = client.post(
                        f"{route['api_base'].rstrip('/')}/v1/chat/completions",
                        headers=headers, json=body,
                    )
                    resp.raise_for_status()
                    data = resp.json()

                result = self._parse_llm_response(data, model_name)
                logger.info(f"    ✅ {model_name} 成功")
                return result

            except Exception as e:
                last_error = e
                logger.info(f"    ⚠️ {model_name} 失败: {e}")
                continue

        raise last_error or RuntimeError("所有模型均失败")

    def _parse_llm_response(self, data: dict, model_name: str) -> Dict[str, Any]:
        """解析 LLM 响应，提取 JSON"""
        import re
        content = data["choices"][0]["message"]["content"]
        # DeepSeek R1: 去掉 <think>...</think>
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        if not content.strip().startswith("{"):
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1:
                content = content[start:end + 1]

        result = json.loads(content.strip())
        result["_model_used"] = model_name

        required = ["health_score", "release_recommendation", "summary",
                     "key_findings", "risk_points", "failure_analysis",
                     "skipped_analysis", "suggestions", "next_actions"]
        for key in required:
            if key not in result:
                raise ValueError(f"LLM 输出缺少字段: {key}")
        return result

    def _build_llm_prompt(self, m: Dict[str, Any]) -> str:
        failed_summary = "\n".join(
            f"  - {c['case_name']} | {c['failure_category']} | {c['risk_level']} | {c['error_message'][:100]}"
            for c in m["failed_case_details"][:20]
        ) or "  (无失败用例)"

        slow_summary = "\n".join(
            f"  - {c['case_name']} | {c['duration_ms']}ms"
            for c in m["slow_cases"][:10]
        ) or "  (无慢接口)"

        return f"""以下是一次接口测试执行的结构化摘要，请生成分析报告。

## 执行概览
- 项目: {m['project_name']}
- 环境: {m['env_name']}
- 总用例: {m['total']}，通过: {m['passed']}，失败: {m['failed']}，跳过: {m['skipped']}
- 通过率: {m['pass_rate']}%
- 执行时长: {m['duration_s']}s

## 失败分类统计
{json.dumps(m['failure_categories'], ensure_ascii=False, indent=2)}

## 风险等级统计
- P0: 总 {m['risk_stats']['P0']['total']}，失败 {m['risk_stats']['P0']['failed']}
- P1: 总 {m['risk_stats']['P1']['total']}，失败 {m['risk_stats']['P1']['failed']}
- P2: 总 {m['risk_stats']['P2']['total']}，失败 {m['risk_stats']['P2']['failed']}

## Destructive 跳过
- 破坏性用例跳过: {m['destructive_skipped']} 条

## 失败用例摘要 (最多20条)
{failed_summary}

## 慢接口摘要 (最多10条)
{slow_summary}

请输出纯 JSON (不要 Markdown)，包含以下字段:
- health_score: 0-100 整数
- release_recommendation: "pass" / "caution" / "block"
- summary: 一段中文总结
- key_findings: 字符串数组
- risk_points: [{{"level": "high/medium/low", "description": "..."}}]
- failure_analysis: [{{"category": "...", "count": N, "analysis": "...", "suggestion": "...", "affected_cases": [...]}}]
- skipped_analysis: [{{"reason": "...", "count": N, "risk_note": "...", "recommendation": "..."}}]
- suggestions: 字符串数组
- next_actions: [{{"priority": "high/medium/low", "action": "..."}}]
"""

    # ── 持久化 ────────────────────────────────────────────

    def _save_analysis(self, run_id: str, report_id: int, analysis: Dict) -> AiReportAnalysis:
        record = AiReportAnalysis(
            run_id=run_id,
            report_id=report_id,
            health_score=analysis.get("health_score", 0),
            release_recommendation=analysis.get("release_recommendation", "caution"),
            summary=analysis.get("summary", ""),
            key_findings_json=analysis.get("key_findings", []),
            risk_points_json=analysis.get("risk_points", []),
            failure_analysis_json=analysis.get("failure_analysis", []),
            skipped_analysis_json=analysis.get("skipped_analysis", []),
            suggestions_json=analysis.get("suggestions", []),
            next_actions_json=analysis.get("next_actions", []),
            provider=analysis.get("provider", "rule_based"),
            created_at=datetime.now(),
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    @staticmethod
    def _record_to_dict(record: AiReportAnalysis) -> Dict[str, Any]:
        return {
            "analysis_id": record.id,
            "run_id": record.run_id,
            "report_id": record.report_id,
            "health_score": record.health_score,
            "release_recommendation": record.release_recommendation,
            "summary": record.summary,
            "key_findings": record.key_findings_json or [],
            "risk_points": record.risk_points_json or [],
            "failure_analysis": record.failure_analysis_json or [],
            "skipped_analysis": record.skipped_analysis_json or [],
            "suggestions": record.suggestions_json or [],
            "next_actions": record.next_actions_json or [],
            "provider": record.provider,
            "created_at": record.created_at.isoformat() if record.created_at else None,
        }
