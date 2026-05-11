"""
测试报告生成路由 (Phase 15)

POST /api/v2/test-runs/{run_id}/report          生成报告
GET  /api/v2/test-runs/{run_id}/report/download  下载报告
"""

import os
import json
from datetime import datetime
from typing import Optional
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import sys
import logging

logger = logging.getLogger(__name__)
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.session import get_db
from database.models import TestRun, RunCase, TestCase, AiReportAnalysis, Report, Project, Environment

router = APIRouter(prefix="/api/v2/test-runs", tags=["TestReport"])
reports_router = APIRouter(prefix="/api/v2/reports", tags=["Reports"])

REPORTS_DIR = Path(__file__).parent.parent / "data" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# 敏感字段
_SENSITIVE = {'authorization','token','access_token','refresh_token','password','secret','cookie','session','x-token','api-key'}

def _sanitize(data):
    if isinstance(data, dict):
        return {k: ('******' if k.lower() in _SENSITIVE and v else _sanitize(v)) for k, v in data.items()}
    elif isinstance(data, list):
        return [_sanitize(i) for i in data]
    return data


class ReportRequest(BaseModel):
    format: str = Field("html", description="报告格式: html")


class ReportResponse(BaseModel):
    success: bool
    report_id: str = ""
    report_url: str = ""
    message: str = ""


@router.post("/{run_id}/report", response_model=ReportResponse)
def generate_report(
    run_id: str,
    req: ReportRequest = ReportRequest(),
    db: Session = Depends(get_db),
):
    """生成测试报告"""
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(404, detail=f"执行记录不存在: {run_id}")

    cases = db.query(RunCase).filter(RunCase.run_id == run_id).all()

    html = _build_html_report(run, cases, db)
    filename = f"{run_id}.html"
    filepath = REPORTS_DIR / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    # ── 写入 / 更新 reports 表 ──
    report_id = f"REPORT_{run_id}"
    existing = db.query(Report).filter(Report.run_id == run_id).first()
    total = run.total_cases or len(cases)
    passed = run.passed_cases or 0
    failed = run.failed_cases or 0
    skipped = run.skipped_cases or 0
    executed = total - skipped
    pass_rate = round(passed / max(executed, 1) * 100, 1)

    if existing:
        existing.title = f"测试报告 - {run_id}"
        existing.file_path = str(filepath)
        existing.file_size = filepath.stat().st_size
        existing.total_tests = total
        existing.passed = passed
        existing.failed = failed
        existing.skipped = skipped
        existing.pass_rate = pass_rate
        existing.created_at = datetime.now()
        report_id = existing.id
    else:
        new_report = Report(
            id=report_id,
            run_id=run_id,
            title=f"测试报告 - {run_id}",
            report_type="comprehensive",
            format="html",
            file_path=str(filepath),
            file_size=filepath.stat().st_size,
            total_tests=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            pass_rate=pass_rate,
        )
        db.add(new_report)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.info(f"⚠️  报告入库失败: {e}")

    return ReportResponse(
        success=True,
        report_id=report_id,
        report_url=f"/api/v2/test-runs/{run_id}/report/download?format=html",
        message="报告生成成功",
    )


@router.get("/{run_id}/report/download")
def download_report(
    run_id: str,
    format: str = Query("html"),
):
    """下载测试报告"""
    filename = f"{run_id}.html"
    filepath = REPORTS_DIR / filename

    if not filepath.exists():
        raise HTTPException(404, detail=f"报告不存在，请先生成报告。run_id={run_id}")

    return FileResponse(
        str(filepath),
        media_type="text/html",
        filename=filename,
    )


# ==================== HTML 报告模板 ====================

def _build_html_report(run: TestRun, cases: list, db: Session) -> str:
    """Phase 18: 增强版 HTML 报告"""
    from database.models import Project, Environment

    # ── 基础统计 ──
    total = run.total_cases or len(cases) or 0
    passed = run.passed_cases or 0
    failed = run.failed_cases or 0
    skipped = run.skipped_cases or sum(1 for c in cases if c.status == 'skipped')
    no_assertion = sum(1 for c in cases if c.status == 'no_assertion')
    error_count = sum(1 for c in cases if c.status == 'error')
    executed = total - skipped
    pass_rate = f"{(passed / max(executed, 1) * 100):.1f}"
    duration = run.duration or 0
    summary_data = json.loads(run.summary or '{}')
    preset_name = summary_data.get('preset') or ''

    # ── 项目 / 环境 ──
    proj = db.query(Project).filter(Project.id == run.project_id).first() if run.project_id else None
    env = db.query(Environment).filter(Environment.id == run.environment_id).first() if run.environment_id else None
    project_name = proj.name if proj else f'Project #{run.project_id}'
    env_name = env.name if env else f'Env #{run.environment_id}'

    # ── TestCase 治理字段 map ──
    all_tc_ids = [c.test_case_id for c in cases]
    tc_map = {}
    if all_tc_ids:
        for tc in db.query(TestCase).filter(TestCase.id.in_(all_tc_ids)).all():
            tc_map[tc.id] = tc

    # ── 失败分类统计 ──
    failure_cats = {}
    for c in cases:
        if c.status in ('failed', 'error'):
            tc = tc_map.get(c.test_case_id)
            cat = (tc.failure_category if tc else None) or c.error_type or 'unknown_error'
            failure_cats[cat] = failure_cats.get(cat, 0) + 1

    # ── 跳过统计 ──
    skipped_reasons = {}
    for c in cases:
        if c.status == 'skipped':
            reason = c.error_type or 'other'
            skipped_reasons[reason] = skipped_reasons.get(reason, 0) + 1

    # ── 风险统计 ──
    risk_counts = {'P0': 0, 'P1': 0, 'P2': 0}
    destructive_total = 0
    skipped_destructive = skipped_reasons.get('destructive', 0)
    for tc in tc_map.values():
        rl = getattr(tc, 'risk_level', '') or ''
        if rl in risk_counts:
            risk_counts[rl] += 1
        if getattr(tc, 'destructive', False):
            destructive_total += 1

    # ── 用例明细表 ──
    rows = []
    failed_details = []
    skipped_details = []

    for c in cases:
        req_snap = _sanitize(c.request_snapshot or {})
        resp_snap = _sanitize(c.response_snapshot or {})
        tc = tc_map.get(c.test_case_id)
        method = req_snap.get('method', '')
        url = req_snap.get('url', '')
        status_code = resp_snap.get('status_code', '-')
        elapsed = resp_snap.get('elapsed_ms', (c.duration or 0) * 1000)

        risk_level = (tc.risk_level if tc else '') or ''
        api_pattern = (tc.api_pattern if tc else '') or ''
        is_destructive = getattr(tc, 'destructive', False) if tc else False
        fc = (tc.failure_category if tc else None) or c.error_type or ''

        status_map = {'passed': ('通过', 'passed'), 'failed': ('失败', 'failed'),
                      'no_assertion': ('无断言', 'warning'), 'error': ('错误', 'failed'),
                      'skipped': ('跳过', 'skipped')}
        status_label, status_class = status_map.get(c.status, (c.status, ''))

        skipped_reason = c.error_type if c.status == 'skipped' else ''

        rows.append(f"""<tr>
            <td title="{_esc(c.test_case_id)}">{_esc((tc.title if tc else c.test_case_id) or c.test_case_id)}</td>
            <td><code>{method}</code></td>
            <td class="url-cell">{_esc(url)}</td>
            <td class="risk-{risk_level.lower()}">{risk_level}</td>
            <td>{api_pattern}</td>
            <td>{'<span class="tag-destructive">destructive</span>' if is_destructive else ''}</td>
            <td class="status-{status_class}">{status_label}</td>
            <td>{_esc(fc)}</td>
            <td>{_esc(skipped_reason)}</td>
            <td>{status_code}</td>
            <td>{elapsed:.0f}ms</td>
        </tr>""")

        if c.status in ('failed', 'error'):
            failed_details.append(_build_failure_detail_v2(c, req_snap, resp_snap, tc, fc))
        if c.status == 'skipped':
            skipped_details.append(f"""<tr>
                <td>{_esc((tc.title if tc else '') or c.test_case_id)}</td>
                <td>{_esc(c.error_type or '')}</td>
                <td>{_esc(c.error_message or '')}</td>
                <td>{'是' if is_destructive else '否'}</td>
            </tr>""")

    rows_html = "\n".join(rows)
    failed_html = "\n".join(failed_details) if failed_details else "<p>无失败用例</p>"

    # ── 失败分类表 ──
    fc_label_map = {
        'auth_error': '认证失败', 'env_error': '环境/网络错误',
        'request_error': '请求错误', 'response_error': '响应/服务端错误',
        'assertion_error': '断言失败', 'dependency_error': '依赖/业务状态错误',
        'timeout_error': '超时', 'unknown_error': '未知错误',
    }
    fc_suggest_map = {
        'auth_error': '检查 Token / Authorization 配置',
        'env_error': '检查 base_url 是否可达，网络是否通畅',
        'request_error': '检查请求参数、Body 格式是否正确',
        'response_error': '确认接口存在且服务端正常运行',
        'assertion_error': '检查期望值与实际返回值',
        'dependency_error': '确认前置数据或业务状态是否满足',
        'timeout_error': '接口超时，考虑增大超时或优化后端',
        'unknown_error': '查看错误日志，进一步排查',
    }
    fc_rows = ''.join(
        f'<tr><td>{fc_label_map.get(k,k)}</td><td><code>{k}</code></td><td>{v}</td><td>{fc_suggest_map.get(k,"")}</td></tr>'
        for k, v in sorted(failure_cats.items(), key=lambda x: -x[1])
    ) if failure_cats else ''
    fc_html = f'<table class="data-table"><thead><tr><th>分类</th><th>编码</th><th>数量</th><th>排查建议</th></tr></thead><tbody>{fc_rows}</tbody></table>' if fc_rows else '<p style="color:#16a34a;">无失败用例</p>'

    # ── 跳过详情表 ──
    sk_table = ''
    if skipped_details:
        sk_table = f"""<table class="data-table"><thead><tr><th>用例名称</th><th>跳过原因</th><th>说明</th><th>destructive</th></tr></thead>
        <tbody>{"".join(skipped_details)}</tbody></table>"""
    else:
        sk_table = '<p>无跳过用例</p>'

    # ── 风险提示 ──
    risks = []
    if failed > 0:
        risks.append(f'<li class="risk-item red">执行失败 <strong>{failed}</strong> 个</li>')
    if error_count > 0:
        risks.append(f'<li class="risk-item red">执行错误 <strong>{error_count}</strong> 个</li>')
    if no_assertion > 0:
        risks.append(f'<li class="risk-item yellow">无断言用例 <strong>{no_assertion}</strong> 个</li>')
    if destructive_total > 0:
        risks.append(f'<li class="risk-item orange">破坏性接口 <strong>{destructive_total}</strong> 个（跳过 {skipped_destructive} 个）</li>')
    risks_html = "<ul>" + "\n".join(risks) + "</ul>" if risks else '<p style="color:#16a34a;">无风险提示</p>'

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    created = run.created_at.strftime('%Y-%m-%d %H:%M:%S') if run.created_at else now

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>测试报告 - {run.id}</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background:#f5f5f5; color:#333; padding:20px; }}
.container {{ max-width:1280px; margin:0 auto; }}
.header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color:white; padding:30px; border-radius:12px; margin-bottom:20px; }}
.header h1 {{ font-size:24px; margin-bottom:8px; }}
.header .meta {{ font-size:13px; opacity:0.9; line-height:1.8; }}
.card {{ background:white; border-radius:8px; box-shadow:0 1px 3px rgba(0,0,0,0.1); padding:20px; margin-bottom:16px; }}
.card h2 {{ font-size:16px; color:#333; margin-bottom:12px; padding-bottom:8px; border-bottom:1px solid #eee; }}
.stats {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; text-align:center; }}
.stats-8 {{ grid-template-columns:repeat(8,1fr); }}
.stat {{ padding:16px 8px; background:#f9fafb; border-radius:8px; }}
.stat .value {{ font-size:28px; font-weight:bold; }}
.stat .label {{ font-size:12px; color:#666; margin-top:4px; }}
.stat .value.green {{ color:#16a34a; }}
.stat .value.red {{ color:#dc2626; }}
.stat .value.yellow {{ color:#ca8a04; }}
.stat .value.blue {{ color:#2563eb; }}
.stat .value.orange {{ color:#ea580c; }}
.data-table {{ width:100%; border-collapse:collapse; font-size:13px; }}
.data-table th {{ background:#f3f4f6; padding:10px 8px; text-align:left; font-weight:600; white-space:nowrap; }}
.data-table td {{ padding:8px; border-top:1px solid #e5e7eb; }}
.data-table tr:hover {{ background:#f9fafb; }}
.url-cell {{ max-width:260px; word-break:break-all; font-size:12px; font-family:monospace; }}
.status-passed {{ color:#16a34a; font-weight:bold; }}
.status-failed {{ color:#dc2626; font-weight:bold; }}
.status-warning {{ color:#ca8a04; font-weight:bold; }}
.status-skipped {{ color:#6b7280; font-weight:bold; }}
.risk-p0 {{ color:#dc2626; font-weight:bold; }}
.risk-p1 {{ color:#ea580c; font-weight:bold; }}
.risk-p2 {{ color:#2563eb; }}
.tag-destructive {{ background:#fef2f2; color:#dc2626; font-size:11px; padding:2px 6px; border-radius:4px; border:1px solid #fecaca; }}
code {{ background:#f3f4f6; padding:2px 6px; border-radius:4px; font-size:12px; }}
.failure-block {{ border-left:4px solid #dc2626; background:#fef2f2; padding:16px; margin-bottom:12px; border-radius:0 8px 8px 0; }}
.failure-block h3 {{ color:#dc2626; font-size:14px; margin-bottom:8px; }}
.failure-block pre {{ background:#1f2937; color:#a3e635; padding:12px; border-radius:6px; font-size:11px; overflow-x:auto; max-height:200px; white-space:pre-wrap; word-break:break-all; }}
.failure-block .suggest {{ background:#fffbeb; border:1px solid #fde68a; padding:8px 12px; border-radius:6px; margin-top:8px; font-size:13px; color:#92400e; }}
.risk-item {{ padding:6px 0; font-size:14px; list-style:none; }}
.risk-item.red::before {{ content:'\\274C '; }}
.risk-item.yellow::before {{ content:'\\26A0 '; }}
.risk-item.orange::before {{ content:'\\1F525 '; }}
details {{ margin-top:6px; }}
details summary {{ cursor:pointer; color:#2563eb; font-size:13px; }}
.footer {{ text-align:center; font-size:12px; color:#999; padding:20px 0; }}
</style>
</head>
<body>
<div class="container">

<div class="header">
    <h1>接口测试报告</h1>
    <div class="meta">
        项目: {_esc(project_name)} &nbsp;|&nbsp; 环境: {_esc(env_name)}<br>
        Run ID: {run.id} {f'&nbsp;|&nbsp; Preset: {_esc(preset_name)}' if preset_name else ''}<br>
        执行时间: {created} &nbsp;|&nbsp; 报告生成: {now}
    </div>
</div>

<div class="card">
    <h2>执行概览</h2>
    <div class="stats stats-8">
        <div class="stat"><div class="value">{total}</div><div class="label">总用例</div></div>
        <div class="stat"><div class="value">{executed}</div><div class="label">实际执行</div></div>
        <div class="stat"><div class="value green">{passed}</div><div class="label">通过</div></div>
        <div class="stat"><div class="value red">{failed}</div><div class="label">失败</div></div>
        <div class="stat"><div class="value red">{error_count}</div><div class="label">错误</div></div>
        <div class="stat"><div class="value yellow">{no_assertion}</div><div class="label">无断言</div></div>
        <div class="stat"><div class="value orange">{skipped}</div><div class="label">跳过</div></div>
        <div class="stat"><div class="value blue">{pass_rate}%</div><div class="label">通过率</div></div>
    </div>
    <p style="font-size:12px;color:#999;margin-top:8px;text-align:right;">通过率 = 通过数 / 实际执行数，跳过用例不计入 &nbsp;|&nbsp; 总耗时 {duration:.2f}s</p>
</div>

<div class="card">
    <h2>失败分类统计</h2>
    {fc_html}
</div>

<div class="card">
    <h2>风险等级统计</h2>
    <div class="stats">
        <div class="stat"><div class="value red">{risk_counts['P0']}</div><div class="label">P0 (最高)</div></div>
        <div class="stat"><div class="value orange">{risk_counts['P1']}</div><div class="label">P1 (高)</div></div>
        <div class="stat"><div class="value blue">{risk_counts['P2']}</div><div class="label">P2 (中)</div></div>
        <div class="stat"><div class="value">{destructive_total}</div><div class="label">destructive</div></div>
    </div>
    {risks_html}
</div>

<div class="card">
    <h2>用例明细</h2>
    <table class="data-table">
        <thead><tr>
            <th>用例名称</th><th>方法</th><th>URL</th><th>风险</th><th>类型</th><th>destructive</th><th>状态</th><th>失败分类</th><th>跳过原因</th><th>HTTP</th><th>耗时</th>
        </tr></thead>
        <tbody>{rows_html}</tbody>
    </table>
</div>

<div class="card">
    <h2>失败详情</h2>
    {failed_html}
</div>

<div class="card">
    <h2>跳过详情</h2>
    {sk_table}
</div>

{_build_ai_analysis_html(run.id, db)}

<div class="footer">
    AI Test Platform - Phase 19 AI 分析增强报告 &copy; {datetime.now().year}
</div>

</div>
</body>
</html>"""


def _build_failure_detail_v2(c, req_snap, resp_snap, tc, fc):
    """Phase 18: 增强版单个失败用例详情"""
    fc_suggest_map = {
        'auth_error': '检查 Token / Authorization 配置是否正确',
        'env_error': '检查 base_url 是否可达，网络是否通畅',
        'request_error': '检查请求参数、Body 格式是否完整正确',
        'response_error': '确认接口路径是否存在，服务端是否正常运行',
        'assertion_error': '核对期望值与实际返回值的差异',
        'dependency_error': '确认前置数据或业务状态是否满足（如需先创建再修改）',
        'timeout_error': '接口响应超时，考虑增大超时时间或排查后端性能',
        'unknown_error': '查看错误日志，进一步排查原因',
    }

    assertions = c.assertion_details or []
    assertion_rows = ""
    for a in assertions:
        if isinstance(a, dict) and not a.get('passed', True):
            assertion_rows += f"""<tr>
                <td>{a.get('type','')}</td>
                <td>{_esc(str(a.get('expected','')))}</td>
                <td>{_esc(str(a.get('actual','')))}</td>
                <td>{_esc(a.get('message',''))}</td>
            </tr>"""

    assertion_table = ""
    if assertion_rows:
        assertion_table = f"""<table style="width:100%;font-size:12px;margin-top:8px;border-collapse:collapse;">
            <tr style="background:#f3f4f6;"><th style="padding:6px;">类型</th><th style="padding:6px;">期望</th><th style="padding:6px;">实际</th><th style="padding:6px;">原因</th></tr>
            {assertion_rows}
        </table>"""

    req_body = req_snap.get('body', '')
    if isinstance(req_body, dict):
        req_body = json.dumps(req_body, ensure_ascii=False, indent=2)

    resp_body = resp_snap.get('body', '')
    if isinstance(resp_body, dict):
        resp_body = json.dumps(resp_body, ensure_ascii=False, indent=2)
    if isinstance(resp_body, str) and len(resp_body) > 800:
        resp_body = resp_body[:800] + '...'

    tc_name = (tc.title if tc else '') or c.test_case_id
    suggest = fc_suggest_map.get(fc, '')

    return f"""<div class="failure-block">
        <h3>{_esc(tc_name)}</h3>
        <p><strong>请求:</strong> <code>{req_snap.get('method','')}</code> {_esc(req_snap.get('url',''))}</p>
        <p><strong>失败分类:</strong> <code>{_esc(fc)}</code></p>
        {f'<p><strong>错误信息:</strong> {_esc(c.error_message)}</p>' if c.error_message else ''}
        {f'<details><summary>请求 Body</summary><pre>{_esc(str(req_body))}</pre></details>' if req_body else ''}
        {f'<details><summary>响应 Body (HTTP {resp_snap.get("status_code","")})</summary><pre>{_esc(str(resp_body))}</pre></details>' if resp_body else ''}
        {assertion_table}
        {f'<div class="suggest"><strong>排查建议:</strong> {suggest}</div>' if suggest else ''}
    </div>"""


def _esc(text):
    """HTML转义"""
    if not text:
        return ''
    return str(text).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')


def _build_ai_analysis_html(run_id: str, db: Session) -> str:
    """Phase 19: 生成 AI 分析 HTML 区块"""
    try:
        record = (
            db.query(AiReportAnalysis)
            .filter(AiReportAnalysis.run_id == run_id)
            .order_by(AiReportAnalysis.created_at.desc())
            .first()
        )
    except Exception:
        record = None

    if not record:
        return '<div class="card"><h2>AI 质量分析</h2><p style="color:#999;">当前报告尚未生成 AI 分析。可通过 API 或前端触发生成。</p></div>'

    rec = record.release_recommendation or "caution"
    rec_color = {"pass": "#16a34a", "caution": "#f59e0b", "block": "#ef4444"}.get(rec, "#999")
    rec_label = {"pass": "✅ 可发布", "caution": "⚠️ 谨慎发布", "block": "🚫 不建议发布"}.get(rec, rec)

    # 健康分
    score = record.health_score or 0
    score_color = "#16a34a" if score >= 85 else ("#f59e0b" if score >= 60 else "#ef4444")

    # key_findings
    findings = record.key_findings_json or []
    findings_html = "".join(f"<li>{_esc(f)}</li>" for f in findings) if findings else "<li>无</li>"

    # risk_points
    risks = record.risk_points_json or []
    risk_html = ""
    for r in risks:
        lvl = r.get("level", "low")
        clr = {"high": "#ef4444", "medium": "#f59e0b", "low": "#3b82f6"}.get(lvl, "#999")
        risk_html += f'<li><span style="color:{clr};font-weight:bold;">[{lvl.upper()}]</span> {_esc(r.get("description", ""))}</li>'
    if not risk_html:
        risk_html = "<li>无风险点</li>"

    # failure_analysis
    fa = record.failure_analysis_json or []
    fa_rows = ""
    for item in fa:
        cases_str = ", ".join(item.get("affected_cases", [])[:3])
        fa_rows += f"""<tr>
            <td><code>{_esc(item.get('category', ''))}</code></td>
            <td>{item.get('count', 0)}</td>
            <td>{_esc(item.get('analysis', ''))}</td>
            <td>{_esc(item.get('suggestion', ''))}</td>
            <td style="font-size:11px;">{_esc(cases_str)}</td>
        </tr>"""
    fa_table = f"""<table class="data-table"><thead><tr><th>分类</th><th>数量</th><th>分析</th><th>建议</th><th>相关用例</th></tr></thead>
        <tbody>{fa_rows}</tbody></table>""" if fa_rows else "<p>无失败分析</p>"

    # suggestions
    suggestions = record.suggestions_json or []
    sugg_html = "".join(f"<li>{_esc(s)}</li>" for s in suggestions) if suggestions else "<li>无</li>"

    # next_actions
    actions = record.next_actions_json or []
    act_html = ""
    for a in actions:
        pri = a.get("priority", "low")
        clr = {"high": "#ef4444", "medium": "#f59e0b", "low": "#3b82f6"}.get(pri, "#999")
        act_html += f'<li><span style="color:{clr};font-weight:bold;">[{pri.upper()}]</span> {_esc(a.get("action", ""))}</li>'
    if not act_html:
        act_html = "<li>无</li>"

    provider_label = "规则分析" if record.provider == "rule_based" else "AI 大模型"

    return f"""<div class="card">
    <h2>AI 质量分析 <span style="font-size:12px;color:#999;">({provider_label})</span></h2>

    <div style="display:flex;gap:24px;margin-bottom:16px;">
        <div style="text-align:center;padding:12px 24px;background:#f9fafb;border-radius:8px;">
            <div style="font-size:36px;font-weight:bold;color:{score_color};">{score}</div>
            <div style="font-size:12px;color:#666;">健康评分</div>
        </div>
        <div style="text-align:center;padding:12px 24px;background:#f9fafb;border-radius:8px;">
            <div style="font-size:24px;font-weight:bold;color:{rec_color};">{rec_label}</div>
            <div style="font-size:12px;color:#666;">发布建议</div>
        </div>
    </div>

    <p><strong>总结:</strong> {_esc(record.summary or '')}</p>

    <h3>关键发现</h3>
    <ul>{findings_html}</ul>

    <h3>风险点</h3>
    <ul>{risk_html}</ul>

    <h3>失败原因分析</h3>
    {fa_table}

    <h3>修复建议</h3>
    <ul>{sugg_html}</ul>

    <h3>下一步行动</h3>
    <ul>{act_html}</ul>
</div>"""


# ==================== Reports 独立路由 ====================

@reports_router.get("", summary="报告列表")
def list_reports(
    project_id: Optional[int] = Query(None),
    run_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """获取报告列表"""
    q = db.query(Report).join(TestRun, Report.run_id == TestRun.id)

    if run_id:
        q = q.filter(Report.run_id == run_id)
    if project_id:
        q = q.filter(TestRun.project_id == project_id)

    total = q.count()
    reports = q.order_by(Report.created_at.desc()).offset(offset).limit(limit).all()

    items = []
    for r in reports:
        run = r.test_run
        summary_data = json.loads(run.summary or '{}') if run and run.summary else {}
        items.append({
            "report_id": r.id,
            "run_id": r.run_id,
            "project_id": run.project_id if run else None,
            "title": r.title,
            "report_type": r.report_type,
            "format": r.format,
            "status": "completed",
            "pass_rate": r.pass_rate,
            "total_tests": r.total_tests,
            "passed": r.passed,
            "failed": r.failed,
            "skipped": r.skipped,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "app_mode": summary_data.get("app_mode"),
            "allow_unsafe_methods": summary_data.get("allow_unsafe_methods"),
            "download_url": f"/api/v2/test-runs/{r.run_id}/report/download?format=html",
        })

    return {"total": total, "items": items}


@reports_router.get("/{report_id}", summary="报告详情")
def get_report_detail(
    report_id: str,
    db: Session = Depends(get_db),
):
    """获取报告详情"""
    r = db.query(Report).filter(Report.id == report_id).first()
    if not r:
        raise HTTPException(404, detail=f"报告不存在: {report_id}")

    run = r.test_run
    summary_data = json.loads(run.summary or '{}') if run and run.summary else {}

    proj = db.query(Project).filter(Project.id == run.project_id).first() if run and run.project_id else None
    env = db.query(Environment).filter(Environment.id == run.environment_id).first() if run and run.environment_id else None

    # 失败摘要
    failure_summary = []
    if run:
        cases = db.query(RunCase).filter(RunCase.run_id == run.id).all()
        fc_map = {}
        for c in cases:
            if c.status in ('failed', 'error'):
                cat = c.error_type or 'unknown_error'
                fc_map[cat] = fc_map.get(cat, 0) + 1
        failure_summary = [{"category": k, "count": v} for k, v in fc_map.items()]

    # 风险提示
    risk_warnings = []
    app_mode = summary_data.get("app_mode")
    allow_unsafe = summary_data.get("allow_unsafe_methods")
    if app_mode == "real":
        if allow_unsafe:
            risk_warnings.append("本次执行包含真实项目写操作，请确认测试环境数据影响。")
        else:
            risk_warnings.append("本次在真实项目模式下执行（仅读操作）。")

    # P2-5: visual regression summary
    visual_summary = None
    if run:
        vr_total = vr_passed = vr_failed = vr_baseline = 0
        max_diff = 0.0
        for c in cases:
            resp = c.response_snapshot or {}
            if isinstance(resp, str):
                try:
                    resp = json.loads(resp)
                except Exception:
                    resp = {}
            for vr in (resp.get("visual_results") or []):
                vr_total += 1
                st = vr.get("status", "")
                if st == "passed":
                    vr_passed += 1
                elif st == "baseline_created":
                    vr_baseline += 1
                elif st == "failed":
                    vr_failed += 1
                dr = vr.get("diff_ratio", 0) or 0
                if dr > max_diff:
                    max_diff = dr
        if vr_total > 0:
            visual_summary = {
                "total": vr_total, "passed": vr_passed,
                "failed": vr_failed, "baseline_created": vr_baseline,
                "max_diff_ratio": round(max_diff, 6),
            }

    return {
        "report_id": r.id,
        "run_id": r.run_id,
        "project_id": run.project_id if run else None,
        "project_name": proj.name if proj else None,
        "environment_name": env.name if env else None,
        "title": r.title,
        "report_type": r.report_type,
        "format": r.format,
        "status": "completed",
        "pass_rate": r.pass_rate,
        "total_tests": r.total_tests,
        "passed": r.passed,
        "failed": r.failed,
        "skipped": r.skipped,
        "file_path": r.file_path,
        "file_size": r.file_size,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "app_mode": app_mode,
        "allow_unsafe_methods": allow_unsafe,
        "risk_warnings": risk_warnings,
        "failure_summary": failure_summary,
        "visual_summary": visual_summary,
        "download_url": f"/api/v2/test-runs/{r.run_id}/report/download?format=html",
        "run": {
            "id": run.id,
            "status": run.status,
            "trigger_type": run.trigger_type,
            "total_cases": run.total_cases,
            "passed_cases": run.passed_cases,
            "failed_cases": run.failed_cases,
            "skipped_cases": run.skipped_cases,
            "duration": run.duration,
            "start_time": run.start_time.isoformat() if run.start_time else None,
            "end_time": run.end_time.isoformat() if run.end_time else None,
        } if run else None,
    }
