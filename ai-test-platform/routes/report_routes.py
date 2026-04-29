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
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.session import get_db
from database.models import TestRun, RunCase

router = APIRouter(prefix="/api/v2/test-runs", tags=["TestReport"])

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

    html = _build_html_report(run, cases)
    filename = f"{run_id}.html"
    filepath = REPORTS_DIR / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    return ReportResponse(
        success=True,
        report_id=run_id,
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

def _build_html_report(run: TestRun, cases: list) -> str:
    total = run.total_cases or len(cases) or 0
    passed = run.passed_cases or 0
    failed = run.failed_cases or 0
    no_assertion = sum(1 for c in cases if c.status == 'no_assertion')
    error_count = sum(1 for c in cases if c.status == 'error')
    pass_rate = f"{(passed / total * 100):.1f}" if total > 0 else "0"
    duration = run.duration or 0

    # 用例明细
    rows = []
    failed_details = []
    slow_cases = []
    five_xx = []

    for c in cases:
        req_snap = _sanitize(c.request_snapshot or {})
        resp_snap = _sanitize(c.response_snapshot or {})
        method = req_snap.get('method', '')
        url = req_snap.get('url', '')
        status_code = resp_snap.get('status_code', 0)
        elapsed = resp_snap.get('elapsed_ms', (c.duration or 0) * 1000)
        a_passed = c.assertions_passed or 0
        a_failed = c.assertions_failed or 0
        assertion_text = f"{a_passed}通过 / {a_failed}失败" if (a_passed + a_failed) > 0 else "无断言"

        status_label = {'passed':'通过','failed':'失败','no_assertion':'无断言','error':'错误'}.get(c.status, c.status)
        status_class = {'passed':'passed','failed':'failed','no_assertion':'warning','error':'failed'}.get(c.status, '')

        rows.append(f"""<tr>
            <td>{c.test_case_id}</td>
            <td><code>{method}</code></td>
            <td class="url-cell">{_esc(url)}</td>
            <td>{status_code}</td>
            <td class="status-{status_class}">{status_label}</td>
            <td>{elapsed:.0f}ms</td>
            <td>{assertion_text}</td>
            <td>{_esc(c.error_message or '')}</td>
        </tr>""")

        if c.status in ('failed', 'error'):
            details_html = _build_failure_detail(c, req_snap, resp_snap)
            failed_details.append(details_html)

        if elapsed > 3000:
            slow_cases.append(c.test_case_id)
        if status_code >= 500:
            five_xx.append(c.test_case_id)

    rows_html = "\n".join(rows)
    failed_html = "\n".join(failed_details) if failed_details else "<p>无失败用例</p>"

    # 风险提示
    risks = []
    if no_assertion > 0:
        risks.append(f"<li>⚠️ 无断言用例 <strong>{no_assertion}</strong> 个，无法验证接口正确性</li>")
    if failed > 0:
        risks.append(f"<li>❌ 执行失败用例 <strong>{failed}</strong> 个</li>")
    if error_count > 0:
        risks.append(f"<li>🔴 执行错误用例 <strong>{error_count}</strong> 个</li>")
    if slow_cases:
        risks.append(f"<li>🐢 响应超3秒用例 <strong>{len(slow_cases)}</strong> 个: {', '.join(slow_cases[:5])}</li>")
    if five_xx:
        risks.append(f"<li>🔥 5xx响应 <strong>{len(five_xx)}</strong> 个: {', '.join(five_xx[:5])}</li>")
    risks_html = "<ul>" + "\n".join(risks) + "</ul>" if risks else "<p style='color:green'>✅ 无风险提示</p>"

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
.container {{ max-width:1200px; margin:0 auto; }}
.header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color:white; padding:30px; border-radius:12px; margin-bottom:20px; }}
.header h1 {{ font-size:24px; margin-bottom:8px; }}
.header .meta {{ font-size:13px; opacity:0.9; }}
.card {{ background:white; border-radius:8px; box-shadow:0 1px 3px rgba(0,0,0,0.1); padding:20px; margin-bottom:16px; }}
.card h2 {{ font-size:16px; color:#333; margin-bottom:12px; padding-bottom:8px; border-bottom:1px solid #eee; }}
.stats {{ display:grid; grid-template-columns:repeat(7,1fr); gap:12px; text-align:center; }}
.stat {{ padding:16px 8px; background:#f9fafb; border-radius:8px; }}
.stat .value {{ font-size:28px; font-weight:bold; }}
.stat .label {{ font-size:12px; color:#666; margin-top:4px; }}
.stat .value.green {{ color:#16a34a; }}
.stat .value.red {{ color:#dc2626; }}
.stat .value.yellow {{ color:#ca8a04; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; }}
th {{ background:#f3f4f6; padding:10px 8px; text-align:left; font-weight:600; }}
td {{ padding:8px; border-top:1px solid #e5e7eb; }}
tr:hover {{ background:#f9fafb; }}
.url-cell {{ max-width:300px; word-break:break-all; font-size:12px; font-family:monospace; }}
.status-passed {{ color:#16a34a; font-weight:bold; }}
.status-failed {{ color:#dc2626; font-weight:bold; }}
.status-warning {{ color:#ca8a04; font-weight:bold; }}
code {{ background:#f3f4f6; padding:2px 6px; border-radius:4px; font-size:12px; }}
.failure-block {{ border-left:4px solid #dc2626; background:#fef2f2; padding:16px; margin-bottom:12px; border-radius:0 8px 8px 0; }}
.failure-block h3 {{ color:#dc2626; font-size:14px; margin-bottom:8px; }}
.failure-block pre {{ background:#1f2937; color:#a3e635; padding:12px; border-radius:6px; font-size:11px; overflow-x:auto; max-height:200px; }}
.risk-list li {{ padding:6px 0; font-size:14px; }}
.footer {{ text-align:center; font-size:12px; color:#999; padding:20px 0; }}
</style>
</head>
<body>
<div class="container">

<div class="header">
    <h1>接口测试报告</h1>
    <div class="meta">
        Run ID: {run.id} &nbsp;|&nbsp; 执行时间: {created} &nbsp;|&nbsp; 报告生成: {now}
    </div>
</div>

<div class="card">
    <h2>执行概览</h2>
    <div class="stats">
        <div class="stat"><div class="value">{total}</div><div class="label">总用例</div></div>
        <div class="stat"><div class="value green">{passed}</div><div class="label">通过</div></div>
        <div class="stat"><div class="value red">{failed}</div><div class="label">失败</div></div>
        <div class="stat"><div class="value red">{error_count}</div><div class="label">错误</div></div>
        <div class="stat"><div class="value yellow">{no_assertion}</div><div class="label">无断言</div></div>
        <div class="stat"><div class="value">{pass_rate}%</div><div class="label">通过率</div></div>
        <div class="stat"><div class="value">{duration:.2f}s</div><div class="label">总耗时</div></div>
    </div>
</div>

<div class="card">
    <h2>用例明细</h2>
    <table>
        <thead><tr>
            <th>用例ID</th><th>方法</th><th>URL</th><th>HTTP</th><th>状态</th><th>耗时</th><th>断言</th><th>错误信息</th>
        </tr></thead>
        <tbody>{rows_html}</tbody>
    </table>
</div>

<div class="card">
    <h2>失败详情</h2>
    {failed_html}
</div>

<div class="card">
    <h2>风险提示</h2>
    {risks_html}
</div>

<div class="footer">
    AI Test Platform - 测试报告 &copy; {datetime.now().year}
</div>

</div>
</body>
</html>"""


def _build_failure_detail(c, req_snap, resp_snap):
    """构建单个失败用例的详情"""
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
        assertion_table = f"""<table style="width:100%;font-size:12px;margin-top:8px;">
            <tr><th>类型</th><th>期望</th><th>实际</th><th>原因</th></tr>
            {assertion_rows}
        </table>"""

    req_body = req_snap.get('body', '')
    if isinstance(req_body, dict):
        req_body = json.dumps(req_body, ensure_ascii=False, indent=2)

    resp_body = resp_snap.get('body', '')
    if isinstance(resp_body, dict):
        resp_body = json.dumps(resp_body, ensure_ascii=False, indent=2)
    if isinstance(resp_body, str) and len(resp_body) > 500:
        resp_body = resp_body[:500] + '...'

    return f"""<div class="failure-block">
        <h3>❌ {c.test_case_id}</h3>
        <p><strong>请求:</strong> <code>{req_snap.get('method','')}</code> {_esc(req_snap.get('url',''))}</p>
        {f'<p><strong>错误:</strong> {_esc(c.error_message)}</p>' if c.error_message else ''}
        {f'<details><summary>请求Body</summary><pre>{_esc(str(req_body))}</pre></details>' if req_body else ''}
        {f'<details><summary>响应Body (HTTP {resp_snap.get("status_code","")})</summary><pre>{_esc(str(resp_body))}</pre></details>' if resp_body else ''}
        {assertion_table}
    </div>"""


def _esc(text):
    """HTML转义"""
    if not text:
        return ''
    return str(text).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')
