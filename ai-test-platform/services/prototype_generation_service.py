"""Product Studio high-fidelity HTML prototype generation.

The MVP stores prototypes as ProductArtifact rows with artifact_type
``high_fidelity_prototype`` and keeps the generated HTML inert: no scripts,
iframes, event handlers, or external runtime dependencies.
"""

from __future__ import annotations

import html
import json
import logging
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.trace_middleware import current_trace_id
from database.models import (
    ProductArtifact,
    ProductArtifactTraceLink,
    ProductIdea,
    ProductStudioRun,
    RequirementPoint,
    TestCase,
)
from services.sanitize import sanitize_text

logger = logging.getLogger("prototype_generation")

PROTOTYPE_ARTIFACT_TYPE = "high_fidelity_prototype"
PAGE_TYPES = {"dashboard", "form", "list", "detail", "workflow"}


def _uid() -> str:
    return uuid.uuid4().hex[:16]


def _now() -> datetime:
    return datetime.now()


def _safe_text(value: Any, default: str = "") -> str:
    text = str(value or default).strip()
    return sanitize_text(text)


def _safe_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def sanitize_prototype_html(raw_html: str) -> str:
    """Remove active content while keeping simple HTML and CSS previewable."""
    cleaned = raw_html or ""
    cleaned = re.sub(r"<\s*script\b[^>]*>.*?<\s*/\s*script\s*>", "", cleaned, flags=re.I | re.S)
    cleaned = re.sub(r"<\s*script\b[^>]*?/?>", "", cleaned, flags=re.I | re.S)
    cleaned = re.sub(r"<\s*iframe\b[^>]*>.*?<\s*/\s*iframe\s*>", "", cleaned, flags=re.I | re.S)
    cleaned = re.sub(r"<\s*iframe\b[^>]*?/?>", "", cleaned, flags=re.I | re.S)
    cleaned = re.sub(r"<\s*(object|embed|applet|base|link)\b[^>]*>.*?<\s*/\s*\1\s*>", "", cleaned, flags=re.I | re.S)
    cleaned = re.sub(r"<\s*(object|embed|applet|base|link)\b[^>]*?/?>", "", cleaned, flags=re.I | re.S)
    cleaned = re.sub(r"\s+on[a-zA-Z]+\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)", "", cleaned, flags=re.I)
    cleaned = re.sub(r"(href|src)\s*=\s*(\"|')\s*javascript:[^\"']*(\"|')", r"\1=\"#\"", cleaned, flags=re.I)
    cleaned = re.sub(r"(href|src)\s*=\s*(\"|')\s*https?://[^\"']*(\"|')", r"\1=\"#\"", cleaned, flags=re.I)
    cleaned = re.sub(r"@import\s+[^;]+;", "", cleaned, flags=re.I)
    cleaned = re.sub(r"url\(\s*(['\"]?)https?://.*?\1\s*\)", "none", cleaned, flags=re.I)
    cleaned = re.sub(r"<\s*meta\b[^>]*http-equiv\s*=\s*(\"|')?refresh[^>]*>", "", cleaned, flags=re.I)
    return cleaned.strip()


def _parse_json_object(text: str) -> Dict[str, Any]:
    if not text:
        return {}
    stripped = text.strip()
    if stripped.startswith("```"):
        match = re.search(r"```(?:json|html)?\s*(.*?)\s*```", stripped, flags=re.I | re.S)
        if match:
            stripped = match.group(1).strip()
    if stripped.startswith("{"):
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(stripped[start:end + 1])
        except json.JSONDecodeError:
            return {}
    return {}


def _latest_artifact(db: Session, idea_id: str, artifact_type: str) -> Optional[ProductArtifact]:
    return (
        db.query(ProductArtifact)
        .filter(ProductArtifact.idea_id == idea_id, ProductArtifact.artifact_type == artifact_type)
        .order_by(ProductArtifact.created_at.desc())
        .first()
    )


def _requirement_points_for_idea(db: Session, idea_id: str, prd: Optional[ProductArtifact]) -> List[RequirementPoint]:
    source_ids = [a.artifact_id for a in db.query(ProductArtifact).filter(ProductArtifact.idea_id == idea_id).all()]
    if prd and prd.artifact_id not in source_ids:
        source_ids.append(prd.artifact_id)
    if not source_ids:
        return []
    return (
        db.query(RequirementPoint)
        .filter(RequirementPoint.source_id.in_(source_ids))
        .order_by(RequirementPoint.created_at.asc())
        .all()
    )


def _test_cases_for_rps(db: Session, rps: List[RequirementPoint]) -> List[TestCase]:
    rp_ids = [rp.id for rp in rps]
    if not rp_ids:
        return []
    return db.query(TestCase).filter(TestCase.test_point_id.in_(rp_ids)).limit(20).all()


def _choose_page_type(text: str) -> str:
    normalized = text.lower()
    if any(k in normalized for k in ("dashboard", "看板", "驾驶舱", "统计", "报表", "指标")):
        return "dashboard"
    if any(k in normalized for k in ("表单", "录入", "创建", "提交", "申请", "编辑")):
        return "form"
    if any(k in normalized for k in ("详情", "明细", "记录详情", "detail")):
        return "detail"
    if any(k in normalized for k in ("流程", "审批", "闭环", "workflow", "步骤")):
        return "workflow"
    return "list"


def _fallback_components(page_type: str) -> List[Dict[str, str]]:
    common = [
        {"name": "顶部标题栏", "purpose": "展示页面名称、主操作和状态概览"},
        {"name": "统计卡片", "purpose": "展示核心业务指标和风险提示"},
    ]
    by_type = {
        "dashboard": [
            {"name": "趋势摘要区", "purpose": "承载关键指标、分布和待处理事项"},
            {"name": "风险列表", "purpose": "展示需要人工关注的异常项"},
        ],
        "form": [
            {"name": "分组表单", "purpose": "收集必填字段、业务字段和附件信息"},
            {"name": "提交操作区", "purpose": "提供保存、提交、重置等动作"},
        ],
        "list": [
            {"name": "筛选查询区", "purpose": "支持关键词、状态和时间条件筛选"},
            {"name": "数据表格", "purpose": "展示列表字段、状态标签和行操作"},
        ],
        "detail": [
            {"name": "详情摘要", "purpose": "展示核心字段与状态"},
            {"name": "时间线", "purpose": "展示关键节点、处理记录和异常信息"},
        ],
        "workflow": [
            {"name": "流程进度条", "purpose": "展示当前步骤和后续动作"},
            {"name": "任务处理区", "purpose": "展示待办、处理意见和流转动作"},
        ],
    }
    return common + by_type.get(page_type, by_type["list"])


def _build_fallback_html(idea: ProductIdea, prd: Optional[ProductArtifact], rps: List[RequirementPoint], page_type: str) -> str:
    title = html.escape(idea.title or "高保真原型")
    subtitle = html.escape(idea.product_direction or idea.pain_points or "Product Studio 生成的企业级后台原型")
    rp_items = rps[:6] or []
    requirement_rows = "\n".join(
        f"<tr><td>{html.escape(rp.title or rp.id)}</td><td><span class='tag'>{html.escape(rp.priority or 'medium')}</span></td><td>{html.escape(rp.module_name or 'P1')}</td></tr>"
        for rp in rp_items
    ) or "<tr><td>暂无需求点</td><td><span class='tag muted'>待补充</span></td><td>-</td></tr>"

    if page_type == "form":
        main = """
        <section class="panel">
          <h2>业务信息录入</h2>
          <div class="form-grid">
            <label>业务名称<input value="示例业务单据" /></label>
            <label>业务类型<select><option>标准流程</option><option>异常处理</option></select></label>
            <label>金额/数量<input value="12800" /></label>
            <label>状态<select><option>待提交</option><option>审核中</option></select></label>
            <label class="wide">说明<textarea>请输入补充说明和验收关注点</textarea></label>
          </div>
          <div class="actions"><button class="secondary">保存草稿</button><button>提交审核</button></div>
        </section>
        """
    elif page_type == "detail":
        main = """
        <section class="panel">
          <h2>详情摘要</h2>
          <div class="detail-grid">
            <div><b>单据编号</b><span>REQ-2026-001</span></div>
            <div><b>当前状态</b><span class="status">待确认</span></div>
            <div><b>负责人</b><span>产品 / 测试协同</span></div>
            <div><b>风险等级</b><span>P1</span></div>
          </div>
          <h3>处理记录</h3>
          <ol class="timeline"><li>需求录入</li><li>AI 解析</li><li>测试点确认</li><li>用例生成</li></ol>
        </section>
        """
    elif page_type == "dashboard":
        main = """
        <section class="panel split">
          <div><h2>趋势摘要</h2><div class="chart"><span style="height:42%"></span><span style="height:58%"></span><span style="height:72%"></span><span style="height:64%"></span><span style="height:86%"></span></div></div>
          <div><h2>风险提醒</h2><ul class="notice"><li>2 条需求缺少验收口径</li><li>1 个关键流程未覆盖异常态</li><li>建议补充边界值用例</li></ul></div>
        </section>
        """
    elif page_type == "workflow":
        main = """
        <section class="panel">
          <h2>流程进度</h2>
          <div class="steps"><span class="done">创建</span><span class="done">解析</span><span>确认</span><span>执行</span><span>报告</span></div>
          <div class="workflow-box"><b>当前待办</b><p>请确认 AI 生成的需求点和测试用例覆盖范围。</p><button>确认并进入执行</button></div>
        </section>
        """
    else:
        main = """
        <section class="panel">
          <h2>业务列表</h2>
          <div class="filters"><input placeholder="搜索名称/编号" /><select><option>全部状态</option><option>待确认</option></select><button>查询</button></div>
          <table><thead><tr><th>名称</th><th>优先级</th><th>状态</th><th>负责人</th><th>操作</th></tr></thead><tbody>
            <tr><td>需求追踪链路</td><td><span class="tag">high</span></td><td><span class="status">待确认</span></td><td>QA</td><td>查看</td></tr>
            <tr><td>质量评分展示</td><td><span class="tag">medium</span></td><td><span class="status ok">已生成</span></td><td>Product</td><td>查看</td></tr>
          </tbody></table>
        </section>
        """

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: Inter, "Microsoft YaHei", Arial, sans-serif; background: #f6f8fb; color: #172033; }}
    .shell {{ min-height: 100vh; padding: 28px; }}
    .topbar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }}
    .topbar h1 {{ margin: 0; font-size: 24px; letter-spacing: 0; }}
    .topbar p {{ margin: 6px 0 0; color: #64748b; font-size: 13px; }}
    button {{ border: 0; background: #2563eb; color: #fff; border-radius: 6px; padding: 10px 14px; font-weight: 600; }}
    .secondary {{ background: #e2e8f0; color: #334155; }}
    .cards {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-bottom: 16px; }}
    .card, .panel {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; box-shadow: 0 1px 2px rgba(15,23,42,.04); }}
    .card span {{ display:block; color:#64748b; font-size:12px; }} .card b {{ display:block; margin-top:6px; font-size:24px; }}
    .panel h2 {{ margin: 0 0 14px; font-size: 16px; }} .panel h3 {{ margin: 16px 0 8px; font-size: 14px; }}
    .split {{ display:grid; grid-template-columns: 1.4fr .8fr; gap:16px; }}
    .filters, .actions {{ display:flex; gap:10px; margin-bottom:14px; }}
    input, select, textarea {{ width:100%; border:1px solid #cbd5e1; border-radius:6px; padding:10px; background:#fff; color:#172033; }}
    textarea {{ min-height: 90px; resize: vertical; }}
    .form-grid {{ display:grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap:14px; }}
    label {{ display:flex; flex-direction:column; gap:6px; font-size:13px; color:#475569; }} .wide {{ grid-column: 1 / -1; }}
    table {{ width:100%; border-collapse: collapse; font-size:13px; }} th, td {{ padding:12px; border-bottom:1px solid #e2e8f0; text-align:left; }} th {{ color:#64748b; background:#f8fafc; }}
    .tag, .status {{ display:inline-flex; border-radius:999px; padding:3px 8px; background:#dbeafe; color:#1d4ed8; font-size:12px; }} .muted {{ background:#f1f5f9; color:#64748b; }} .ok {{ background:#dcfce7; color:#15803d; }}
    .detail-grid {{ display:grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap:12px; }} .detail-grid div {{ background:#f8fafc; border-radius:6px; padding:12px; }} .detail-grid span {{ display:block; margin-top:6px; color:#475569; }}
    .timeline, .notice {{ margin:0; padding-left:20px; color:#475569; line-height:1.9; }}
    .steps {{ display:grid; grid-template-columns: repeat(5,1fr); gap:8px; margin-bottom:14px; }} .steps span {{ text-align:center; border:1px solid #cbd5e1; border-radius:999px; padding:8px; color:#64748b; }} .steps .done {{ background:#eff6ff; border-color:#93c5fd; color:#1d4ed8; }}
    .workflow-box {{ border:1px dashed #93c5fd; border-radius:8px; padding:16px; background:#f8fbff; }}
    .chart {{ height:180px; display:flex; align-items:end; gap:12px; padding:12px; background:#f8fafc; border-radius:8px; }} .chart span {{ flex:1; background:linear-gradient(180deg,#60a5fa,#2563eb); border-radius:6px 6px 0 0; }}
    .requirements {{ margin-top:16px; }}
    @media (max-width: 760px) {{ .cards, .detail-grid, .form-grid, .split {{ grid-template-columns: 1fr; }} .shell {{ padding:16px; }} }}
  </style>
</head>
<body>
  <main class="shell">
    <header class="topbar"><div><h1>{title}</h1><p>{subtitle}</p></div><button>主操作</button></header>
    <section class="cards"><div class="card"><span>需求点</span><b>{len(rps)}</b></div><div class="card"><span>覆盖用例</span><b>{max(1, len(rps))}</b></div><div class="card"><span>风险</span><b>P1</b></div><div class="card"><span>状态</span><b>Draft</b></div></section>
    {main}
    <section class="panel requirements">
      <h2>覆盖需求点</h2>
      <table><thead><tr><th>需求点</th><th>优先级</th><th>风险</th></tr></thead><tbody>{requirement_rows}</tbody></table>
    </section>
  </main>
</body>
</html>"""


def _build_fallback_payload(idea: ProductIdea, prd: Optional[ProductArtifact], rps: List[RequirementPoint]) -> Dict[str, Any]:
    context = " ".join([
        idea.title or "",
        idea.product_direction or "",
        idea.pain_points or "",
        prd.content_markdown[:1000] if prd and prd.content_markdown else "",
        " ".join(rp.title or "" for rp in rps[:8]),
    ])
    page_type = _choose_page_type(context)
    html_text = sanitize_prototype_html(_build_fallback_html(idea, prd, rps, page_type))
    return {
        "page_name": idea.title or "高保真原型",
        "page_type": page_type,
        "design_goal": idea.pain_points or idea.product_direction or "支撑核心业务流程的高保真后台页面原型",
        "layout_description": "顶部标题与主操作、关键指标卡片、主体业务区域、需求点覆盖表。",
        "components": _fallback_components(page_type),
        "interactions": ["筛选查询", "查看详情", "保存草稿", "提交确认"],
        "empty_states": ["暂无数据时展示空态说明和创建入口", "需求点为空时提示先生成需求点"],
        "error_states": ["接口异常时展示重试入口", "字段校验失败时在表单项下方展示错误提示"],
        "html": html_text,
        "covered_requirement_points": [rp.id for rp in rps[:12]],
        "quality_notes": ["规则型 fallback 已生成基础可预览 HTML", "HTML 已移除脚本、iframe 与事件属性"],
    }


def _build_prompt(idea: ProductIdea, prd: Optional[ProductArtifact], rps: List[RequirementPoint], test_cases: List[TestCase]) -> str:
    rp_lines = "\n".join(
        f"- {rp.id}: {rp.title} | priority={rp.priority or 'medium'} | risk={rp.module_name or 'P1'} | {(rp.description or '')[:220]}"
        for rp in rps[:20]
    ) or "暂无 RequirementPoint，可基于 PRD 推断页面结构。"
    tc_lines = "\n".join(
        f"- {tc.id}: {tc.title} | rp={tc.test_point_id or '-'} | priority={tc.priority}"
        for tc in test_cases[:12]
    ) or "暂无测试用例。"
    return f"""你是资深企业级后台系统产品设计师，请基于 Product Studio 的 idea、PRD、需求点，生成一个可预览的高保真 HTML 原型。

## Idea
名称：{idea.title}
产品方向：{idea.product_direction}
目标用户：{idea.target_users}
痛点：{idea.pain_points}
约束：{idea.constraints}

## PRD
{(prd.content_markdown if prd else '')[:7000]}

## RequirementPoint
{rp_lines}

## 可选测试用例
{tc_lines}

## 输出格式
只输出 JSON 对象，不要输出 Markdown，不要解释。字段必须包含：
{{
  "page_name": "",
  "page_type": "dashboard|form|list|detail|workflow",
  "design_goal": "",
  "layout_description": "",
  "components": [],
  "interactions": [],
  "empty_states": [],
  "error_states": [],
  "html": "",
  "covered_requirement_points": [],
  "quality_notes": []
}}

## 设计内容要求
1. 页面名称
2. 页面类型
3. 用户目标
4. 信息架构
5. 页面布局
6. 核心组件
7. 表单字段
8. 表格字段
9. 操作按钮
10. 状态标签
11. 空态
12. 错误态
13. 加载态
14. 交互说明
15. HTML + CSS

## HTML 风格要求
- 企业级后台系统
- 简洁、专业
- 卡片式布局，卡片半径不超过 8px
- 顶部统计卡片
- 表格 / 表单 / 详情区域清晰
- 不使用外部依赖
- 不使用 script
- 不使用 iframe
- 不使用外链 JS、外部 CDN、图片
- 不使用 onerror/onload/onmouseover 等事件属性
- html 字段必须是完整可预览 HTML，包含内联 CSS
"""


def _call_llm(prompt: str, provider: Optional[str], model: Optional[str]) -> tuple[str, str]:
    from agent.llm_client import get_llm_client

    client = get_llm_client(provider=provider, model=model)
    model_name = f"{client.provider}/{client.model}"
    text = client.generate(
        prompt=prompt,
        system_prompt="你是 Product Studio 的高保真 HTML 原型生成助手，只输出安全 JSON。",
        temperature=0.25,
        max_tokens=12000,
    )
    return text, model_name


def _normalize_payload(payload: Dict[str, Any], fallback: Dict[str, Any], rps: List[RequirementPoint]) -> Dict[str, Any]:
    result = dict(fallback)
    for key in ("page_name", "page_type", "design_goal", "layout_description", "html"):
        if payload.get(key):
            result[key] = _safe_text(payload.get(key))
    for key in ("components", "interactions", "empty_states", "error_states", "covered_requirement_points", "quality_notes"):
        if isinstance(payload.get(key), list):
            result[key] = payload[key]
    if result["page_type"] not in PAGE_TYPES:
        result["page_type"] = fallback["page_type"]

    valid_rp_ids = {rp.id for rp in rps}
    covered = [str(x) for x in _safe_list(result.get("covered_requirement_points")) if str(x) in valid_rp_ids]
    if not covered and rps:
        covered = [rp.id for rp in rps[:12]]
    result["covered_requirement_points"] = covered

    html_text = sanitize_prototype_html(str(payload.get("html") or fallback.get("html") or ""))
    if not html_text:
        html_text = fallback["html"]
    result["html"] = html_text
    return result


def _payload_markdown(payload: Dict[str, Any]) -> str:
    components = "\n".join(f"- {c.get('name', c) if isinstance(c, dict) else c}" for c in _safe_list(payload.get("components")))
    interactions = "\n".join(f"- {x}" for x in _safe_list(payload.get("interactions")))
    return f"""# {payload.get('page_name') or '高保真原型'}

类型：{payload.get('page_type')}

## 设计目标
{payload.get('design_goal')}

## 布局说明
{payload.get('layout_description')}

## 组件清单
{components}

## 交互说明
{interactions}

## HTML
```html
{payload.get('html') or ''}
```
"""


def _trace_dict(link: ProductArtifactTraceLink, prototype_artifact_id: str) -> Dict[str, Any]:
    if link.target_type == PROTOTYPE_ARTIFACT_TYPE:
        return {
            "link_id": link.link_id,
            "source_type": "product_artifact",
            "source_id": link.artifact_id,
            "target_type": PROTOTYPE_ARTIFACT_TYPE,
            "target_id": prototype_artifact_id,
            "relation_type": "prd_to_high_fidelity_prototype",
            "status": link.status,
            "created_at": link.created_at.isoformat() if link.created_at else None,
        }
    if link.source_artifact_type == "requirement_point" and link.target_type == "requirement_point":
        return {
            "link_id": link.link_id,
            "source_type": "requirement_point",
            "source_id": link.target_id,
            "target_type": PROTOTYPE_ARTIFACT_TYPE,
            "target_id": prototype_artifact_id,
            "relation_type": "requirement_point_to_high_fidelity_prototype",
            "status": link.status,
            "created_at": link.created_at.isoformat() if link.created_at else None,
        }
    return {
        "link_id": link.link_id,
        "source_type": link.source_artifact_type,
        "source_id": link.artifact_id,
        "target_type": link.target_type,
        "target_id": link.target_id,
        "relation_type": f"{link.source_artifact_type}_to_{link.target_type}",
        "status": link.status,
        "created_at": link.created_at.isoformat() if link.created_at else None,
    }


def _links_for_prototype(db: Session, prototype_artifact_id: str) -> List[ProductArtifactTraceLink]:
    return (
        db.query(ProductArtifactTraceLink)
        .filter(
            or_(
                ProductArtifactTraceLink.artifact_id == prototype_artifact_id,
                ProductArtifactTraceLink.target_id == prototype_artifact_id,
            )
        )
        .order_by(ProductArtifactTraceLink.created_at.asc())
        .all()
    )


def get_latest_high_fidelity_prototype(db: Session, idea_id: str) -> Dict[str, Any]:
    idea = db.query(ProductIdea).filter(ProductIdea.idea_id == idea_id).first()
    if not idea:
        raise ValueError(f"产品想法不存在: {idea_id}")
    artifact = _latest_artifact(db, idea_id, PROTOTYPE_ARTIFACT_TYPE)
    if not artifact:
        return {
            "exists": False,
            "message": "暂无高保真原型，请先生成",
            "trace_id": current_trace_id(),
        }
    links = _links_for_prototype(db, artifact.artifact_id)
    return {
        "exists": True,
        "artifact_id": artifact.artifact_id,
        "artifact_type": artifact.artifact_type,
        "title": artifact.title,
        "content": artifact.content_json or {},
        "trace_links": [_trace_dict(link, artifact.artifact_id) for link in links],
        "trace_id": current_trace_id(),
        "created_at": artifact.created_at.isoformat() if artifact.created_at else None,
        "updated_at": artifact.updated_at.isoformat() if artifact.updated_at else None,
    }


def generate_high_fidelity_prototype(
    db: Session,
    idea_id: str,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    idea = db.query(ProductIdea).filter(ProductIdea.idea_id == idea_id).first()
    if not idea:
        raise ValueError(f"产品想法不存在: {idea_id}")

    prd = _latest_artifact(db, idea_id, "prd")
    rps = _requirement_points_for_idea(db, idea_id, prd)
    test_cases = _test_cases_for_rps(db, rps)
    fallback = _build_fallback_payload(idea, prd, rps)

    run_id = f"run_{_uid()}"
    trace_id = current_trace_id() if current_trace_id() != "-" else f"trace_{_uid()}"
    run = ProductStudioRun(
        run_id=run_id,
        idea_id=idea_id,
        run_type=PROTOTYPE_ARTIFACT_TYPE,
        input_payload={
            "idea_id": idea_id,
            "prd_artifact_id": prd.artifact_id if prd else None,
            "requirement_point_count": len(rps),
            "test_case_count": len(test_cases),
        },
        status="running",
        trace_id=trace_id,
        started_at=_now(),
    )
    db.add(run)
    db.commit()

    payload = fallback
    llm_error = None
    try:
        prompt = _build_prompt(idea, prd, rps, test_cases)
        text, model_name = _call_llm(prompt, provider=provider, model=model)
        run.model_name = model_name
        run.output_text = text
        parsed = _parse_json_object(text)
        if parsed:
            payload = _normalize_payload(parsed, fallback, rps)
        else:
            llm_error = "LLM 未返回有效 JSON 对象，已使用规则 fallback"
    except Exception as exc:
        llm_error = sanitize_text(str(exc))[:500]
        run.model_name = "fallback/rule_based"
        run.output_text = json.dumps(fallback, ensure_ascii=False)
        logger.warning("high fidelity prototype fallback used: %s", llm_error)

    if llm_error:
        payload = dict(payload)
        notes = _safe_list(payload.get("quality_notes"))
        notes.append(f"LLM 不可用或输出无效，已使用规则 fallback：{llm_error}")
        payload["quality_notes"] = notes

    artifact_id = f"art_{_uid()}"
    artifact = ProductArtifact(
        artifact_id=artifact_id,
        idea_id=idea_id,
        run_id=run_id,
        artifact_type=PROTOTYPE_ARTIFACT_TYPE,
        title=f"高保真原型 - {payload.get('page_name') or idea.title}",
        content_markdown=_payload_markdown(payload),
        content_json=payload,
        status="draft",
    )
    db.add(artifact)

    links: List[ProductArtifactTraceLink] = []
    if prd:
        link = ProductArtifactTraceLink(
            link_id=f"link_{_uid()}",
            artifact_id=prd.artifact_id,
            source_artifact_type="prd",
            target_type=PROTOTYPE_ARTIFACT_TYPE,
            target_id=artifact_id,
            generation_run_id=run_id,
            confidence_score=0.86,
            status="draft",
        )
        db.add(link)
        links.append(link)

    covered_ids = set(payload.get("covered_requirement_points") or [])
    covered_rps = [rp for rp in rps if rp.id in covered_ids] or rps[:12]
    for rp in covered_rps:
        link = ProductArtifactTraceLink(
            link_id=f"link_{_uid()}",
            artifact_id=artifact_id,
            source_artifact_type="requirement_point",
            target_type="requirement_point",
            target_id=rp.id,
            generation_run_id=run_id,
            confidence_score=0.78,
            status="draft",
        )
        db.add(link)
        links.append(link)

    run.status = "succeeded"
    run.finished_at = _now()
    if llm_error:
        run.error_message = llm_error
    db.commit()
    db.refresh(artifact)

    trace_links = [_trace_dict(link, artifact_id) for link in links]
    return {
        "artifact_id": artifact_id,
        "artifact_type": PROTOTYPE_ARTIFACT_TYPE,
        "title": artifact.title,
        "content": payload,
        "trace_links": trace_links,
        "trace_id": trace_id,
        "run_id": run_id,
        "fallback_used": bool(llm_error),
    }
