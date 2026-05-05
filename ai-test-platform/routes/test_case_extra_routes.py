#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase B1: TestCase 额外 V2 路由
- POST /api/v2/test-cases/{id}/generate-script
- POST /api/v2/test-cases/{id}/manual-execute
- GET  /api/v2/test-cases/export
- POST /api/v2/test-cases/{id}/bind-dataset

从 backend_api_server.py legacy 接口迁移，统一使用 DB TestCase 表。
"""

import io
import re
import json as _json
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from urllib.parse import quote

from database.session import get_db
from database.models import (
    TestCase, TestRun, RunCase, TestDataBinding, TestDataset,
)

router = APIRouter(prefix="/api/v2", tags=["TestCase扩展"])


# ── 1. 生成自动化脚本 ──

@router.post("/test-cases/{case_id}/generate-script")
def generate_script(case_id: str, db: Session = Depends(get_db)):
    tc = db.query(TestCase).filter(
        TestCase.id == case_id, TestCase.status != 'deleted'
    ).first()
    if not tc:
        raise HTTPException(status_code=404, detail=f"测试用例不存在: {case_id}")

    script = _build_script(tc)
    return {
        "success": True,
        "data": {"case_id": tc.id, "script": script, "language": "python", "framework": "pytest"},
        "script": script,
        "message": "脚本生成成功",
    }


# ── 2. 手工执行用例 ──

@router.post("/test-cases/{case_id}/manual-execute")
def manual_execute(case_id: str, data: Dict[str, Any], db: Session = Depends(get_db)):
    tc = db.query(TestCase).filter(
        TestCase.id == case_id, TestCase.status != 'deleted'
    ).first()
    if not tc:
        raise HTTPException(status_code=404, detail=f"测试用例不存在: {case_id}")

    status = data.get('status', 'passed')
    notes = data.get('notes', '')
    if status not in ('passed', 'failed', 'skipped'):
        raise HTTPException(status_code=400, detail=f"无效状态: {status}")

    tc.last_run_status = status
    tc.status = status
    tc.updated_at = datetime.now()

    run_id = f"MANUAL_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{case_id}"
    run = TestRun(
        id=run_id, trigger_type='manual', status=status,
        total_cases=1,
        passed_cases=1 if status == 'passed' else 0,
        failed_cases=1 if status == 'failed' else 0,
        skipped_cases=1 if status == 'skipped' else 0,
        start_time=datetime.now(), end_time=datetime.now(), duration=0,
        summary=_json.dumps({"manual": True, "notes": notes}),
        created_at=datetime.now(),
    )
    db.add(run)
    db.flush()
    rc = RunCase(
        run_id=run_id, test_case_id=case_id, status=status,
        start_time=datetime.now(), end_time=datetime.now(), duration=0,
        error_message=notes if status == 'failed' else None,
    )
    db.add(rc)
    db.commit()

    return {
        "success": True,
        "data": {"case_id": case_id, "status": status, "run_id": run_id, "message": "手工执行结果已记录"},
        "message": f"手动测试已记录: {status}",
        "status": status, "testcase_id": case_id,
    }


# ── 3. 导出 Excel ──

@router.get("/test-cases/export")
def export_test_cases(
    project_id: Optional[int] = Query(None),
    module: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    except ImportError:
        raise HTTPException(status_code=500, detail="openpyxl 未安装")

    q = db.query(TestCase).filter(TestCase.status != 'deleted')
    if module:
        q = q.filter(TestCase.module == module)
    if priority:
        q = q.filter(TestCase.priority == priority)
    if status:
        q = q.filter(TestCase.status == status)
    cases = q.order_by(TestCase.created_at.desc()).all()

    wb = Workbook()
    ws = wb.active
    ws.title = "测试用例"
    hdr_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    hdr_font = Font(bold=True, color="FFFFFF", size=11)
    hdr_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    bdr = Border(left=Side(style='thin'), right=Side(style='thin'),
                 top=Side(style='thin'), bottom=Side(style='thin'))

    headers = ['用例ID','项目ID','模块','用例标题','前置条件','操作步骤',
               '预期结果','优先级','类型','状态','来源','创建时间']
    for c, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=c, value=h)
        cell.fill, cell.font, cell.alignment, cell.border = hdr_fill, hdr_font, hdr_align, bdr

    for idx, tc in enumerate(cases, 2):
        steps = tc.steps or []
        steps_text = '\n'.join(steps) if isinstance(steps, list) else str(steps)
        pre = ''
        if isinstance(tc.execution_config, dict):
            pre = tc.execution_config.get('precondition', '')
        created = tc.created_at.strftime('%Y-%m-%d %H:%M') if tc.created_at else ''
        vals = [tc.id, tc.test_point_id or '', tc.module or '', tc.title or '',
                pre, steps_text, tc.expected or '', tc.priority or '',
                tc.case_type or '', tc.status or '', tc.source or '', created]
        for c, v in enumerate(vals, 1):
            cell = ws.cell(row=idx, column=c, value=v)
            cell.border = bdr

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    fname = f"test_cases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return StreamingResponse(
        buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={'Content-Disposition': f'attachment; filename="{fname}"'},
    )


# ── 4. 绑定数据集 ──

@router.post("/test-cases/{case_id}/bind-dataset")
def bind_dataset(case_id: str, request: Dict[str, Any], db: Session = Depends(get_db)):
    tc = db.query(TestCase).filter(
        TestCase.id == case_id, TestCase.status != 'deleted'
    ).first()
    if not tc:
        raise HTTPException(status_code=404, detail=f"测试用例不存在: {case_id}")

    dataset_id = request.get("dataset_id")
    if not dataset_id:
        raise HTTPException(status_code=400, detail="缺少 dataset_id")

    ds = db.query(TestDataset).filter(TestDataset.id == int(dataset_id)).first()
    if not ds:
        raise HTTPException(status_code=404, detail=f"数据集不存在: {dataset_id}")

    binding_type = request.get("binding_type", "input")
    existing = db.query(TestDataBinding).filter(
        TestDataBinding.case_id == case_id,
        TestDataBinding.dataset_id == int(dataset_id),
    ).first()
    if existing:
        existing.binding_type = binding_type
    else:
        db.add(TestDataBinding(
            dataset_id=int(dataset_id), case_id=case_id,
            binding_type=binding_type, created_at=datetime.now(),
        ))

    tc.dataset_id = str(dataset_id)
    tc.updated_at = datetime.now()
    db.commit()

    return {
        "success": True,
        "data": {"case_id": case_id, "dataset_id": dataset_id, "binding_type": binding_type},
        "message": f"测试用例 {case_id} 已绑定数据集 {dataset_id}",
        "test_case_id": case_id, "dataset_id": dataset_id,
    }


# ── 脚本生成辅助 (从 backend_api_server.py 迁移) ──

def _safe_name(title, default='test_case'):
    n = re.sub(r'[^\w\s]', '', title).replace(' ', '_')
    n = re.sub(r'_+', '_', n).strip('_')
    return n.lower() if n else default

def _safe_class(module):
    n = re.sub(r'[^\w\s]', '', module).replace(' ', '')
    return n if n else 'TestModule'

def _build_script(tc) -> str:
    title = tc.title or '测试用例'
    module = tc.module or '通用模块'
    steps = tc.steps or []
    expected = tc.expected or '测试通过'
    cfg = tc.execution_config or {}
    asserts = tc.assertions or []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mn = _safe_name(title)
    cn = _safe_class(module)
    has_api = bool(cfg.get('method') and cfg.get('url'))
    method = (cfg.get('method') or 'GET').upper()
    url = cfg.get('url') or ''
    body = cfg.get('body')
    qp = cfg.get('query_params')
    body_s = _json.dumps(body, ensure_ascii=False, indent=8) if body else 'None'
    qp_s = _json.dumps(qp, ensure_ascii=False, indent=8) if qp else 'None'
    ind = '        '
    alines = []
    for a in asserts:
        at = a.get('type','')
        ae = a.get('expected')
        ap = a.get('path','')
        if at == 'status_code':
            alines.append(f'{ind}assert resp.status_code == {ae}')
        elif at == 'status_code_in':
            alines.append(f'{ind}assert resp.status_code in {ae}')
        elif at == 'response_time':
            alines.append(f'{ind}assert resp.elapsed.total_seconds()*1000 < {ae}')
        elif at == 'field_exists':
            acc = 'data'
            for p in ap.split('.'):
                acc += f'["{p}"]'
            alines.append(f'{ind}assert {acc} is not None')
        elif at == 'field_equals':
            acc = 'data'
            for p in ap.split('.'):
                acc += f'["{p}"]'
            alines.append(f'{ind}assert {acc} == {repr(ae)}')
    if not alines and has_api:
        alines.append(f'{ind}assert resp.status_code == 200')
    acode = '\n'.join(alines) if alines else f'{ind}pass'
    sdoc = ''
    for i, s in enumerate(steps, 1):
        sdoc += f'        {i}. {s}\n'
    if not sdoc:
        sdoc = '        (无详细步骤)\n'
    if has_api:
        return (f'#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n'
            f'"""\n{module} - 自动化测试脚本\n用例: {title}\n生成时间: {now}\n"""\n\n'
            f'import os, pytest, requests\n\n'
            f'BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")\n'
            f'TOKEN = os.getenv("API_TOKEN", "")\n\n'
            f'class Test{cn}:\n'
            f'    def setup_method(self):\n'
            f'        self.session = requests.Session()\n'
            f'        if TOKEN:\n'
            f'            self.session.headers["Authorization"] = f"Bearer {{TOKEN}}"\n\n'
            f'    def teardown_method(self):\n'
            f'        self.session.close()\n\n'
            f'    def test_{mn}(self):\n'
            f'        """\n        {title}\n\n        测试步骤:\n{sdoc}'
            f'        预期结果: {expected}\n        """\n'
            f'        url = f"{{BASE_URL}}{url}"\n'
            f'        body = {body_s}\n        params = {qp_s}\n'
            f'        resp = self.session.request("{method}", url, json=body, params=params, timeout=30)\n'
            f'        data = None\n        try:\n            data = resp.json()\n'
            f'        except Exception:\n            pass\n'
            f'\n{acode}\n\n'
            f'if __name__ == "__main__":\n    pytest.main([__file__, "-v", "-s"])\n')
    else:
        sc = (f'#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n'
            f'"""\n{module} - 自动化测试脚本\n用例: {title}\n生成时间: {now}\n"""\n\n'
            f'import pytest\n\nclass Test{cn}:\n'
            f'    def test_{mn}(self):\n'
            f'        """\n        {title}\n\n        测试步骤:\n{sdoc}'
            f'        预期结果: {expected}\n        """\n')
        for i, s in enumerate(steps, 1):
            sc += f'        # 步骤{i}: {s}\n'
        sc += f'        assert True, "{expected}"\n\nif __name__ == "__main__":\n    pytest.main([__file__, "-v", "-s"])\n'
        return sc
