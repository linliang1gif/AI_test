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
_MAX_REVIEW_CASES = 200


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
    original_total = len(cases)
    if original_total > _MAX_REVIEW_CASES:
        cases = cases[:_MAX_REVIEW_CASES]

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
        "truncated": original_total > _MAX_REVIEW_CASES,
        "original_total_cases": original_total,
        "reviewed_cases": len(cases),
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


# ── AI 自愈（P1-8A-Guard 安全加固版）──────────────────────

# 允许 AI 修改的字段白名单
HEAL_ALLOWED_FIELDS = {"steps", "expected", "assertions", "priority"}
# 需二次确认的高风险字段（AI 可建议但默认不自动应用）
HEAL_CONFIRM_FIELDS = {"title", "execution_config"}
# 绝对禁止修改的字段
HEAL_FORBIDDEN_FIELDS = {"id", "api_id", "dataset_id", "test_point_id", "source", "created_at", "created_by", "tags"}
# 敏感字段关键词 — 送 AI 前脱敏
SENSITIVE_KEYWORDS = {"authorization", "token", "access_token", "refresh_token",
                      "password", "secret", "cookie", "api_key", "api-key"}


class HealCaseRequest(BaseModel):
    case_id: str = Field(..., description="要自愈的用例 ID")
    issues: List[str] = Field(default=[], description="评审发现的问题列表")
    fix_suggestion: str = Field(default="", description="AI 给出的修复建议")


class HealBatchRequest(BaseModel):
    cases: List[HealCaseRequest] = Field(..., description="要自愈的用例列表")
    dry_run: bool = Field(True, description="true=仅预览不修改, false=确认应用修复")


@router.post("/test-cases/heal", summary="AI 用例自愈（安全加固版）")
def heal_test_cases(
    req: HealBatchRequest,
    db: Session = Depends(get_db),
):
    """
    AI 用例自愈，默认 dry_run=true 仅返回修复建议。
    前端展示 before/after 后，用户确认才以 dry_run=false 调用应用。
    """
    results = []

    for item in req.cases:
        result = _heal_one_case(item, db, dry_run=req.dry_run)
        results.append(result)

    applied = [r for r in results if r.get("applied")]
    failed = [r for r in results if r.get("error")]

    return {
        "success": True,
        "dry_run": req.dry_run,
        "total": len(results),
        "healed_count": len(applied),
        "failed_count": len(failed),
        "results": results,
    }


def _heal_one_case(item: HealCaseRequest, db: Session, dry_run: bool) -> Dict:
    """处理单条用例的自愈请求"""
    tc = db.query(TestCase).filter(TestCase.id == item.case_id).first()
    if not tc:
        return {"case_id": item.case_id, "error": "用例不存在", "applied": False}
    if tc.status == "deleted":
        return {"case_id": item.case_id, "error": "已删除的用例不允许自愈", "applied": False}

    # before 快照
    before = {
        "steps": tc.steps or [],
        "expected": tc.expected or "",
        "assertions": tc.assertions or [],
        "priority": tc.priority or "",
    }

    # 生成修复建议（AI 优先，降级到规则）
    fix_data, source = _generate_fix(tc, item.issues, item.fix_suggestion)
    if not fix_data:
        return {"case_id": item.case_id, "error": "生成修复建议失败", "applied": False}

    # 构建 after + changes（只保留白名单字段）
    after = dict(before)
    changes = []
    for field in HEAL_ALLOWED_FIELDS:
        new_val = fix_data.get(field)
        if new_val is not None and new_val != before.get(field):
            after[field] = new_val
            changes.append({
                "field": field,
                "before": before.get(field),
                "after": new_val,
                "reason": fix_data.get("change_summary", "AI 建议修改"),
            })

    # 检测 AI 是否试图修改高风险字段
    risk_warnings = []
    for field in HEAL_CONFIRM_FIELDS:
        if fix_data.get(field) is not None:
            risk_warnings.append(f"AI 建议修改 {field}（已忽略，需人工确认）")
    for field in HEAL_FORBIDDEN_FIELDS:
        if fix_data.get(field) is not None:
            risk_warnings.append(f"AI 试图修改禁止字段 {field}（已拦截）")

    result = {
        "case_id": item.case_id,
        "dry_run": dry_run,
        "source": source,
        "before": before,
        "after": after,
        "changes": changes,
        "risk_warnings": risk_warnings,
        "change_summary": fix_data.get("change_summary", ""),
        "applied": False,
    }

    if not changes:
        result["error"] = "无需修改"
        return result

    if dry_run:
        result["risk_warning"] = "AI 生成内容需要人工确认后再应用"
        return result

    # dry_run=false → 应用修改
    from services.test_case_service import TestCaseService
    svc = TestCaseService(db)

    # 再次校验（防止并发删除）
    tc_check = db.query(TestCase).filter(TestCase.id == item.case_id).first()
    if not tc_check or tc_check.status == "deleted":
        result["error"] = "用例已被删除，无法应用"
        return result

    update_data = {}
    for ch in changes:
        update_data[ch["field"]] = ch["after"]

    svc.update_test_case(item.case_id, update_data)
    result["applied"] = True
    result["updated_fields"] = list(update_data.keys())
    return result


def _sanitize_for_ai(data: dict) -> dict:
    """脱敏敏感字段，防止发送给 AI"""
    sanitized = {}
    for k, v in data.items():
        if k.lower() in SENSITIVE_KEYWORDS:
            sanitized[k] = "***REDACTED***"
        elif isinstance(v, dict):
            sanitized[k] = _sanitize_for_ai(v)
        elif isinstance(v, str) and any(kw in k.lower() for kw in SENSITIVE_KEYWORDS):
            sanitized[k] = "***REDACTED***"
        else:
            sanitized[k] = v
    return sanitized


def _generate_fix(tc: TestCase, issues: List[str], fix_suggestion: str) -> tuple:
    """生成修复建议。返回 (fix_data, source)。AI 不可用时降级到规则。"""
    # 先尝试 AI
    fix_data = _ai_heal_one(tc, issues, fix_suggestion)
    if fix_data:
        return fix_data, "ai"

    # AI 不可用 → 规则降级
    return _rule_based_fix(tc, issues), "rule_based"


def _rule_based_fix(tc: TestCase, issues: List[str]) -> Dict:
    """规则降级：根据问题类型生成基础修复建议"""
    fix = {}
    issues_lower = " ".join(issues).lower()

    if not tc.steps or len(tc.steps) == 0 or "步骤" in issues_lower or "steps" in issues_lower:
        is_api = tc.source in ('swagger', 'demo_swagger', 'demo_seed')
        cfg = tc.execution_config or {}
        if is_api and cfg.get("url"):
            fix["steps"] = [
                f"步骤1: 构造请求参数",
                f"步骤2: 发送 {(cfg.get('method') or 'GET').upper()} 请求到 {cfg.get('url', '')}",
                f"步骤3: 验证响应状态码",
                f"步骤4: 验证响应体关键字段",
            ]
        else:
            fix["steps"] = [
                f"步骤1: 准备测试数据和前置条件",
                f"步骤2: 执行测试操作 - {tc.title}",
                f"步骤3: 验证操作结果符合预期",
            ]

    if not tc.expected or tc.expected.strip() == "" or "预期" in issues_lower or "expected" in issues_lower:
        fix["expected"] = f"预期: {tc.title} 操作成功完成，返回正确结果"

    if (not tc.assertions or len(tc.assertions) == 0) and ("断言" in issues_lower or "assertion" in issues_lower):
        is_api = tc.source in ('swagger', 'demo_swagger', 'demo_seed')
        if is_api:
            fix["assertions"] = [
                {"type": "status_code", "expected": 200},
            ]

    if fix:
        fix["change_summary"] = "规则降级: " + ", ".join(fix.keys())

    return fix


def _ai_heal_one(tc: TestCase, issues: List[str], fix_suggestion: str) -> Optional[Dict]:
    """用 AI 为单条用例生成修复内容"""
    try:
        from ai.ai_client import get_ai_client
        client = get_ai_client(module="case_review")

        cfg = _sanitize_for_ai(tc.execution_config or {})
        method = (cfg.get("method") or "").upper()
        path = cfg.get("url") or cfg.get("path") or ""

        is_api = tc.source in ('swagger', 'demo_swagger', 'demo_seed')

        current_info = _sanitize_for_ai({
            "id": tc.id,
            "title": tc.title,
            "method": method if is_api else "",
            "path": path if is_api else "",
            "current_steps": tc.steps or [],
            "current_expected": tc.expected or "",
            "current_assertions": tc.assertions or [],
            "priority": tc.priority,
            "data_type": tc.data_type,
            "source": tc.source,
        })

        issues_text = "\n".join(f"- {i}" for i in issues)

        if is_api:
            prompt = f"""你是测试专家。请修复以下接口测试用例的问题。

## 当前用例
{json.dumps(current_info, ensure_ascii=False, indent=2)}

## 发现的问题
{issues_text}

## 修复建议
{fix_suggestion}

## 修复要求
1. 补充完整的测试步骤（steps），每步包含具体操作
2. 补充明确的预期结果（expected）
3. 补充断言（assertions），至少包含状态码断言和关键字段断言
4. 如果优先级不合理，给出合理的优先级
5. 禁止修改 id, execution_config, tags 等字段

请直接输出 JSON（不要 markdown）：
{{
  "steps": ["步骤1: 发送请求...", "步骤2: 验证响应..."],
  "expected": "预期: 返回200, 响应体包含...",
  "assertions": [
    {{"type": "status_code", "expected": 200}},
    {{"type": "json_field", "field": "字段名", "operator": "exists"}}
  ],
  "priority": "high/medium/low",
  "change_summary": "一句话说明修改了什么"
}}"""
        else:
            prompt = f"""你是测试专家。请修复以下功能测试用例的问题。

## 当前用例
{json.dumps(current_info, ensure_ascii=False, indent=2)}

## 发现的问题
{issues_text}

## 修复建议
{fix_suggestion}

## 修复要求
1. 补充详细可执行的测试步骤（steps），每步包含操作和验证点
2. 补充明确可验证的预期结果（expected）
3. 如果优先级不合理，给出合理的优先级
4. 禁止修改 id, execution_config, tags 等字段

请直接输出 JSON（不要 markdown）：
{{
  "steps": ["步骤1: 操作描述", "步骤2: 验证描述"],
  "expected": "预期结果的详细描述",
  "priority": "high/medium/low",
  "change_summary": "一句话说明修改了什么"
}}"""

        # 日志只打印摘要，不打印完整 prompt
        print(f"🔧 AI 自愈 [{tc.id}]: 发送 prompt ({len(prompt)} chars)")
        response = client.generate_text(prompt)
        text = response.strip()
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            return json.loads(json_match.group())

    except Exception as e:
        print(f"⚠️  AI 自愈失败 [{tc.id}]: {type(e).__name__}: {str(e)[:200]}")

    return None
