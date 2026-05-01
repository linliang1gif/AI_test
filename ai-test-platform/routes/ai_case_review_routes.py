#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P1-8 AI 用例评审路由

POST /api/v2/ai/test-cases/review
- 规则评审（始终执行）
- AI 增强评审（可选，降级安全）
"""

import json
import os
import re
import sys
import traceback
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.session import get_db
from database.models import TestCase

router = APIRouter(prefix="/api/v2/ai", tags=["AI用例评审"])

# ── 敏感字段 ──
_SENSITIVE = {
    'authorization', 'token', 'access_token', 'refresh_token',
    'password', 'secret', 'cookie', 'session', 'x-token', 'api-key',
    'api_key', 'apikey', 'x-api-key',
}

# ── 高风险路径关键词 ──
_HIGH_RISK_KEYWORDS = {'delete', 'remove', 'pay', 'submit', 'approve', 'refund', 'transfer', 'cancel'}

# ── 写操作方法 ──
_WRITE_METHODS = {'POST', 'PUT', 'PATCH', 'DELETE'}


# ── 请求/响应模型 ──
class ReviewRequest(BaseModel):
    project_id: Optional[int] = None
    api_spec_id: Optional[int] = None
    case_ids: Optional[List[str]] = []
    review_mode: str = Field(default="rule_first", description="rule_first | rule_only | ai_only")


class CaseIssue(BaseModel):
    case_id: str
    title: str
    issues: List[str]
    risk_level: str = "low"
    score: int = 100


# ── 脱敏工具 ──
def _sanitize(obj):
    """递归脱敏字典中的敏感字段"""
    if isinstance(obj, dict):
        return {k: ('******' if k.lower() in _SENSITIVE and v else _sanitize(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(i) for i in obj]
    return obj


# ── 查询用例 ──
def _load_cases(db: Session, req: ReviewRequest) -> List[TestCase]:
    q = db.query(TestCase)

    # 排除软删除
    if hasattr(TestCase, 'status'):
        q = q.filter(TestCase.status != 'deleted')

    if req.case_ids:
        q = q.filter(TestCase.id.in_(req.case_ids))
    elif req.project_id:
        q = q.filter(TestCase.tags.like(f'%"project:{req.project_id}"%'))
    elif req.api_spec_id:
        q = q.filter(TestCase.tags.like(f'%"api_spec:{req.api_spec_id}"%'))

    return q.all()


# ── 规则评审引擎 ──
def _rule_review(cases: List[TestCase]) -> Dict[str, Any]:
    """纯规则评审，不依赖 AI"""
    case_results = []
    total = len(cases)
    missing_assertion_count = 0
    missing_expected_count = 0
    missing_steps_count = 0
    high_risk_count = 0
    write_op_count = 0
    automatable_count = 0
    duplicate_groups = []

    # 检测重复: (method, path)
    sig_map = defaultdict(list)

    for tc in cases:
        issues = []
        penalty = 0
        cfg = tc.execution_config or {}
        method = (cfg.get('method') or '').upper()
        url = cfg.get('url') or ''
        path = cfg.get('path') or url

        # 1. 标题
        if not tc.title or len(tc.title.strip()) < 3:
            issues.append("缺少清晰标题")
            penalty += 10

        # 2. 前置条件 (steps 里第一个或 preconditions)
        steps = tc.steps or []
        if not steps:
            issues.append("缺少操作步骤")
            missing_steps_count += 1
            penalty += 10

        # 3. 预期结果
        if not tc.expected or len(str(tc.expected).strip()) < 2:
            issues.append("缺少预期结果")
            missing_expected_count += 1
            penalty += 10

        # 4. 断言
        assertions = tc.assertions or []
        if not assertions:
            issues.append("缺少断言规则")
            missing_assertion_count += 1
            penalty += 15

        # 5. 关联接口
        if not url and not tc.api_id:
            issues.append("未关联接口")
            penalty += 5

        # 6. 写操作风险
        if method in _WRITE_METHODS:
            write_op_count += 1
            penalty += 2

        # 7. 高风险路径
        path_lower = path.lower()
        matched_risk = [kw for kw in _HIGH_RISK_KEYWORDS if kw in path_lower]
        if matched_risk:
            issues.append(f"高风险接口({', '.join(matched_risk)})")
            high_risk_count += 1
            penalty += 5

        # 8. 可自动化
        if url and method:
            automatable_count += 1

        # 9. 重复检测 key
        if method and path:
            sig = f"{method}:{re.sub(r'/[0-9]+', '/{id}', path)}"
            sig_map[sig].append(tc.id)

        # 10. 优先级
        if tc.priority and tc.priority.lower() not in ('critical', 'high', 'medium', 'low'):
            issues.append(f"优先级值异常: {tc.priority}")
            penalty += 3

        score = max(0, 100 - penalty)
        risk = 'high' if penalty >= 25 else ('medium' if penalty >= 10 else 'low')
        case_results.append(CaseIssue(case_id=tc.id, title=tc.title or '', issues=issues, risk_level=risk, score=score))

    # 重复组
    duplicate_count = 0
    for sig, ids in sig_map.items():
        if len(ids) > 1:
            duplicate_groups.append({"signature": sig, "case_ids": ids, "count": len(ids)})
            duplicate_count += len(ids)

    # 总评分
    if case_results:
        avg_score = round(sum(c.score for c in case_results) / len(case_results), 1)
    else:
        avg_score = 0

    return {
        "review_type": "rule",
        "total_cases": total,
        "automatable_cases": automatable_count,
        "missing_assertion_count": missing_assertion_count,
        "missing_expected_count": missing_expected_count,
        "missing_steps_count": missing_steps_count,
        "high_risk_count": high_risk_count,
        "write_operation_count": write_op_count,
        "duplicate_count": duplicate_count,
        "duplicate_groups": duplicate_groups[:10],
        "quality_score": avg_score,
        "case_details": [c.dict() for c in case_results],
        "risk_summary": _build_risk_summary(case_results),
        "improvement_suggestions": _build_suggestions(missing_assertion_count, missing_expected_count, missing_steps_count, high_risk_count, duplicate_count, total),
        "priority_recommendations": _build_priority_recs(case_results),
    }


def _build_risk_summary(results: List[CaseIssue]) -> Dict[str, int]:
    counter = Counter(r.risk_level for r in results)
    return {"high": counter.get("high", 0), "medium": counter.get("medium", 0), "low": counter.get("low", 0)}


def _build_suggestions(no_assert, no_expected, no_steps, high_risk, dup, total) -> List[str]:
    suggestions = []
    if no_assert > 0:
        suggestions.append(f"有 {no_assert} 条用例缺少断言，建议补充断言规则以保证测试有效性。")
    if no_expected > 0:
        suggestions.append(f"有 {no_expected} 条用例缺少预期结果，建议完善。")
    if no_steps > 0:
        suggestions.append(f"有 {no_steps} 条用例缺少操作步骤，建议补充。")
    if high_risk > 0:
        suggestions.append(f"发现 {high_risk} 个高风险接口用例，建议优先评审并增加防护断言。")
    if dup > 0:
        suggestions.append(f"发现 {dup} 条疑似重复用例，建议合并或标记。")
    if total > 0 and no_assert / max(total, 1) > 0.5:
        suggestions.append("超过半数用例缺少断言，建议全面补充断言覆盖。")
    return suggestions


def _build_priority_recs(results: List[CaseIssue]) -> List[Dict]:
    high_risk = [r for r in results if r.risk_level == 'high']
    return [{"case_id": r.case_id, "title": r.title, "reason": "; ".join(r.issues)} for r in high_risk[:10]]


# ── AI 增强评审 ──
def _try_ai_review(cases: List[TestCase], rule_result: Dict) -> Optional[Dict]:
    """尝试 AI 增强评审，失败返回 None"""
    try:
        from ai.ai_client import get_ai_client
        client = get_ai_client(module="case_review")

        # 构建精简上下文（脱敏）
        api_sources = {'swagger', 'demo_swagger', 'demo_seed'}
        case_summaries = []
        api_count = 0
        func_count = 0
        for tc in cases[:50]:  # 限制发送量
            cfg = _sanitize(tc.execution_config or {})
            method = (cfg.get("method") or "").upper()
            path = cfg.get("url") or cfg.get("path") or ""
            is_api = tc.source in api_sources
            if is_api:
                api_count += 1
            else:
                func_count += 1
            summary = {
                "id": tc.id,
                "title": tc.title,
                "has_assertions": bool(tc.assertions),
                "has_expected": bool(tc.expected),
                "has_steps": bool(tc.steps),
                "priority": tc.priority,
                "data_type": tc.data_type,
                "source": tc.source,
            }
            if is_api:
                summary["method"] = method
                summary["path"] = path
            case_summaries.append(summary)

        # 判断评审类型
        review_type = "api" if api_count > func_count else "functional" if func_count > api_count else "mixed"

        # 提取接口列表用于覆盖率分析
        api_paths = list(set(f"{c.get('method','')} {c.get('path','')}" for c in case_summaries if c.get('method') and c.get('path')))

        # 共用头部
        common_header = f"""你是一位拥有10年经验的测试架构师，精通接口测试、功能测试和测试用例设计。
请对以下 {len(case_summaries)} 条测试用例进行专业质量评审。

## 项目背景
总用例数: {rule_result['total_cases']}，功能用例: {func_count}，接口用例: {api_count}
可自动化: {rule_result.get('automatable_cases', 0)}，涉及接口: {len(api_paths)} 个

## 规则评审已发现的问题
- 缺少断言: {rule_result['missing_assertion_count']} 条
- 缺少预期结果: {rule_result['missing_expected_count']} 条
- 缺少操作步骤: {rule_result['missing_steps_count']} 条
- 高风险接口: {rule_result['high_risk_count']} 个
- 写操作接口: {rule_result.get('write_operation_count', 0)} 个
- 疑似重复: {rule_result['duplicate_count']} 条
- 当前规则评分: {rule_result['quality_score']}/100

## 用例摘要（已脱敏）
{json.dumps(case_summaries, ensure_ascii=False, indent=1)}"""

        # 评审维度 — 按类型区分
        if review_type == "api":
            review_dims = """
## 评审要求（接口测试维度）
请从以下维度深度分析：
1. **接口覆盖**: 同一接口是否覆盖了正常、异常(400/401/403/404/500)、边界参数场景
2. **参数校验**: 必填参数缺失、类型错误、空值、超长、特殊字符是否覆盖
3. **安全测试**: 高风险接口(DELETE/PUT)是否有鉴权、越权、SQL注入、XSS 用例
4. **数据依赖**: 有前后依赖的接口是否有串联测试(如先创建再删除)
5. **幂等性**: POST/PUT 重复提交是否有测试
6. **断言质量**: 仅检查 status_code 是否够用，是否需要校验响应体字段和结构
7. **优先级合理性**: 高风险写操作的用例优先级是否偏低
8. **并发/性能**: 是否缺少并发、超时、限流场景"""
        elif review_type == "functional":
            review_dims = """
## 评审要求（功能测试维度）
请从以下维度深度分析：
1. **业务流程**: 主流程(正向)和异常流程(反向)是否都覆盖
2. **等价类划分**: 输入数据的有效/无效等价类是否充分
3. **边界值**: 数值范围边界、字符串长度上下限、日期边界是否覆盖
4. **用户角色**: 不同角色/权限下的操作是否有对应用例
5. **状态转换**: 业务对象的状态流转是否完整测试(如 待审核→已通过→已拒绝)
6. **异常处理**: 网络断开、数据库异常、第三方超时等容错场景
7. **预期结果**: 每条用例是否有明确可验证的预期结果
8. **步骤完整性**: 操作步骤是否清晰、可复现、无歧义"""
        else:
            review_dims = """
## 评审要求（混合评审维度）
用例中包含功能测试和接口测试，请分别从对应维度分析：

**功能测试维度：**
1. **业务流程**: 主流程和异常流程是否覆盖
2. **等价类/边界值**: 输入数据划分是否充分
3. **状态转换**: 业务状态流转是否完整
4. **预期结果**: 是否有明确可验证的预期

**接口测试维度：**
5. **接口覆盖**: 正常、异常、边界参数场景
6. **安全测试**: 鉴权、越权、注入
7. **断言质量**: 响应体字段校验
8. **数据依赖**: 串联测试覆盖"""

        # 共用输出格式
        output_format = """
## 输出格式
请直接输出 JSON（不要 markdown 代码块）：
{
  "missing_scenarios": [
    {"scenario": "场景描述", "category": "功能/接口/安全/性能", "priority": "high/medium/low", "reason": "为什么需要"}
  ],
  "improvement_suggestions": [
    {"suggestion": "具体建议", "affected_cases": ["TC_001"], "impact": "high/medium/low"}
  ],
  "risk_summary": "一段话总结整体测试风险",
  "priority_recommendations": [
    {"case_id": "TC_xxx", "current_priority": "low", "suggested_priority": "high", "reason": "理由"}
  ],
  "case_issues": [
    {"case_id": "TC_xxx", "issues": ["具体问题1"], "fix_suggestion": "修复建议"}
  ],
  "coverage_gaps": ["未覆盖的场景1", "场景2"],
  "overall_assessment": "一句话总评"
}"""

        prompt = common_header + review_dims + output_format

        response = client.generate_text(prompt)

        # 解析 JSON
        text = response.strip()
        # 提取 JSON
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            ai_data = json.loads(json_match.group())
            return ai_data

    except Exception as e:
        print(f"⚠️  AI 评审失败（降级规则评审）: {e}")
        traceback.print_exc()

    return None


# ── 路由 ──
@router.post("/test-cases/review", summary="AI 用例评审")
def review_test_cases(
    req: ReviewRequest,
    db: Session = Depends(get_db),
):
    """
    对测试用例进行规则 + AI 评审。
    AI 不可用时自动降级为纯规则评审。
    """
    cases = _load_cases(db, req)

    if not cases:
        return {
            "success": True,
            "review_type": "rule",
            "total_cases": 0,
            "quality_score": 0,
            "message": "未找到符合条件的测试用例",
            "case_details": [],
            "risk_summary": {"high": 0, "medium": 0, "low": 0},
            "improvement_suggestions": ["当前无用例，建议先导入 Swagger 或手动创建用例。"],
            "priority_recommendations": [],
            "missing_scenarios": [],
            "missing_assertion_count": 0,
            "missing_expected_count": 0,
            "missing_steps_count": 0,
            "high_risk_count": 0,
            "write_operation_count": 0,
            "duplicate_count": 0,
            "duplicate_groups": [],
            "automatable_cases": 0,
        }

    # 1. 规则评审（始终执行）
    rule_result = _rule_review(cases)

    # 2. AI 增强（可选）
    ai_enhanced = False
    ai_data = None
    if req.review_mode in ("rule_first", "ai_only"):
        ai_data = _try_ai_review(cases, rule_result)
        if ai_data:
            ai_enhanced = True

    # 3. 合并结果
    result = {
        "success": True,
        "review_type": "rule+ai" if ai_enhanced else "rule",
        "ai_enhanced": ai_enhanced,
        **rule_result,
    }

    # 合并 AI 输出（补充，不覆盖规则结果）
    if ai_data:
        if ai_data.get("missing_scenarios"):
            result["missing_scenarios"] = ai_data["missing_scenarios"]
        if ai_data.get("improvement_suggestions"):
            result["ai_suggestions"] = ai_data["improvement_suggestions"]
        if ai_data.get("risk_summary") and isinstance(ai_data["risk_summary"], str):
            result["ai_risk_summary"] = ai_data["risk_summary"]
        if ai_data.get("priority_recommendations"):
            result["ai_priority_recommendations"] = ai_data["priority_recommendations"]
        if ai_data.get("case_issues"):
            result["ai_case_issues"] = ai_data["case_issues"]
        if ai_data.get("coverage_gaps"):
            result["coverage_gaps"] = ai_data["coverage_gaps"]
        if ai_data.get("overall_assessment"):
            result["overall_assessment"] = ai_data["overall_assessment"]
    else:
        result["missing_scenarios"] = []

    return result
