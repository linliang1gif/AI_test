#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase C1: code_compare DB 持久化服务

职责:
1. 保存/查询代码快照元数据 (CodeSnapshot)
2. 保存/查询需求点 (RequirementPoint)
3. 保存/查询对比报告 (CodeCompareReport + CodeCompareFinding)
4. 更新 Finding 人工确认状态 / 流转结果
5. 兼容读取旧 JSON 报告 (source=legacy_json)
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

from database.models import (
    CodeSnapshot,
    RequirementPoint,
    CodeCompareReport,
    CodeCompareFinding,
    RequirementConfirmQuestion,
)

logger = logging.getLogger(__name__)

# Legacy JSON 报告目录
LEGACY_REPORTS_DIR = Path("data/code_compare/reports")


class CodeCompareStorageService:
    """code_compare DB 持久化服务"""

    def __init__(self, db: Session):
        self.db = db

    # ── CodeSnapshot ──

    def save_snapshot(self, snapshot_id: str, name: str,
                      source_type: str = 'zip_upload',
                      source_path: str = '',
                      file_count: int = 0,
                      language_stats: dict = None,
                      ignored_dirs: list = None,
                      project_id: int = None) -> CodeSnapshot:
        snap = CodeSnapshot(
            id=snapshot_id,
            project_id=project_id,
            name=name,
            source_type=source_type,
            source_path=source_path,
            file_count=file_count,
            language_stats_json=language_stats or {},
            ignored_dirs_json=ignored_dirs or [],
            created_at=datetime.now(),
        )
        self.db.merge(snap)
        self.db.commit()
        return snap

    def get_snapshot(self, snapshot_id: str) -> Optional[CodeSnapshot]:
        return self.db.query(CodeSnapshot).filter(CodeSnapshot.id == snapshot_id).first()

    # ── RequirementPoint ──

    def save_requirement_points(self, points: List[Dict[str, Any]]) -> List[RequirementPoint]:
        saved = []
        for p in points:
            rp = RequirementPoint(
                id=p['id'],
                project_id=p.get('project_id'),
                source_type=p.get('source_type', 'manual'),
                source_id=p.get('source_id'),
                point_type=p.get('point_type', 'feature'),
                title=p.get('title', ''),
                description=p.get('description', ''),
                keywords_json=p.get('keywords', []),
                priority=p.get('priority', 'medium'),
                module_name=p.get('module_name', ''),
                created_at=datetime.now(),
            )
            self.db.merge(rp)
            saved.append(rp)
        self.db.commit()
        return saved

    # ── CodeCompareReport + Findings ──

    def save_report(self, report_dict: dict, findings_list: list) -> CodeCompareReport:
        summary = report_dict.get('summary', {})
        rpt = CodeCompareReport(
            id=report_dict['report_id'],
            project_id=int(report_dict['project_id']) if report_dict.get('project_id') else None,
            requirement_source_id=report_dict.get('requirement_source'),
            code_snapshot_id=report_dict.get('code_snapshot_id'),
            analysis_mode=report_dict.get('ai_mode', 'rule_based'),
            total_requirement_points=summary.get('total_req_points', 0),
            implemented_count=summary.get('implemented', 0),
            missing_count=summary.get('missing', 0),
            extra_count=summary.get('extra', 0),
            uncertain_count=summary.get('uncertain', 0),
            risk_count=summary.get('risk', 0),
            summary=json.dumps(summary, ensure_ascii=False),
            code_summary=report_dict.get('code_summary', ''),
            created_at=datetime.now(),
        )
        self.db.merge(rpt)
        self.db.flush()

        for f in findings_list:
            dbf = CodeCompareFinding(
                id=f['finding_id'],
                report_id=rpt.id,
                finding_type=f.get('type', 'implemented'),
                requirement_point_json={'requirement': f.get('requirement', '')},
                confidence=f.get('confidence', 0.0),
                risk_level=f.get('risk_level', 'medium'),
                evidence_json=f.get('code_evidence') or {},
                analysis=f.get('analysis', ''),
                suggested_test_cases_json=f.get('test_suggestion') or {},
                manual_status=f.get('manual_status'),
                target_type=f.get('target_type'),
                target_id=str(f['target_id']) if f.get('target_id') else None,
                reviewer=f.get('reviewer'),
                review_comment=f.get('review_comment'),
                converted_at=datetime.fromisoformat(f['converted_at']) if f.get('converted_at') else None,
                created_at=datetime.now(),
            )
            self.db.merge(dbf)

        self.db.commit()
        logger.info(f"Report {rpt.id} saved to DB with {len(findings_list)} findings")
        return rpt

    def list_reports(self) -> List[Dict[str, Any]]:
        """DB 报告列表 + legacy JSON 报告"""
        items = []

        # DB reports
        db_reports = self.db.query(CodeCompareReport).order_by(
            CodeCompareReport.created_at.desc()
        ).all()
        for r in db_reports:
            items.append(self._report_to_list_item(r, source='db'))

        # Legacy JSON (不重复)
        db_ids = {r.id for r in db_reports}
        for legacy in self._load_legacy_reports():
            rid = legacy.get('report_id', '')
            if rid not in db_ids:
                items.append({
                    'report_id': rid,
                    'requirement_source': legacy.get('requirement_source', ''),
                    'code_snapshot_name': legacy.get('code_snapshot_name', ''),
                    'summary': legacy.get('summary', {}),
                    'ai_mode': legacy.get('ai_mode', 'unknown'),
                    'created_at': legacy.get('created_at', ''),
                    'source': 'legacy_json',
                })

        items.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return items

    def get_report_detail(self, report_id: str) -> Optional[Dict[str, Any]]:
        """查询报告详情，优先 DB，fallback legacy JSON"""
        rpt = self.db.query(CodeCompareReport).filter(CodeCompareReport.id == report_id).first()
        if rpt:
            return self._report_to_detail(rpt, source='db')

        # fallback: legacy JSON
        legacy = self._load_legacy_report(report_id)
        if legacy:
            legacy['source'] = 'legacy_json'
            return legacy

        return None

    def get_finding(self, finding_id: str) -> Optional[CodeCompareFinding]:
        return self.db.query(CodeCompareFinding).filter(CodeCompareFinding.id == finding_id).first()

    def update_finding_status(self, finding_id: str, manual_status: str,
                              reviewer: str = None,
                              review_comment: str = None,
                              target_type: str = None,
                              target_id: str = None,
                              converted_at: datetime = None) -> Optional[CodeCompareFinding]:
        f = self.get_finding(finding_id)
        if not f:
            return None
        f.manual_status = manual_status
        if reviewer is not None:
            f.reviewer = reviewer
        if review_comment is not None:
            f.review_comment = review_comment
        if target_type is not None:
            f.target_type = target_type
        if target_id is not None:
            f.target_id = target_id
        if converted_at is not None:
            f.converted_at = converted_at
        f.updated_at = datetime.now()
        self.db.commit()
        return f

    def save_question(self, q_dict: dict) -> RequirementConfirmQuestion:
        q = RequirementConfirmQuestion(
            id=q_dict['question_id'],
            project_id=q_dict.get('project_id'),
            finding_id=q_dict.get('finding_id'),
            title=q_dict.get('title', ''),
            question=q_dict.get('question', ''),
            context=q_dict.get('requirement_context', ''),
            evidence_json=q_dict.get('code_evidence') or {},
            status=q_dict.get('status', 'open'),
            owner=q_dict.get('owner', 'product'),
            created_at=datetime.now(),
        )
        self.db.merge(q)
        self.db.commit()
        return q

    # ── 内部辅助 ──

    def _report_to_list_item(self, r: CodeCompareReport, source: str = 'db') -> dict:
        snap = self.db.query(CodeSnapshot).filter(CodeSnapshot.id == r.code_snapshot_id).first()
        return {
            'report_id': r.id,
            'requirement_source': r.requirement_source_id or '',
            'code_snapshot_name': snap.name if snap else '',
            'summary': {
                'total_req_points': r.total_requirement_points,
                'implemented': r.implemented_count,
                'missing': r.missing_count,
                'extra': r.extra_count,
                'uncertain': r.uncertain_count,
                'risk': r.risk_count,
            },
            'ai_mode': r.analysis_mode,
            'created_at': r.created_at.isoformat() if r.created_at else '',
            'source': source,
        }

    def _report_to_detail(self, r: CodeCompareReport, source: str = 'db') -> dict:
        snap = self.db.query(CodeSnapshot).filter(CodeSnapshot.id == r.code_snapshot_id).first()
        findings_db = self.db.query(CodeCompareFinding).filter(
            CodeCompareFinding.report_id == r.id
        ).all()

        findings_out = []
        for f in findings_db:
            findings_out.append({
                'finding_id': f.id,
                'type': f.finding_type,
                'requirement': (f.requirement_point_json or {}).get('requirement', ''),
                'confidence': f.confidence,
                'risk_level': f.risk_level,
                'analysis': f.analysis,
                'code_evidence': f.evidence_json,
                'test_suggestion': f.suggested_test_cases_json,
                'manual_status': f.manual_status,
                'target_type': f.target_type,
                'target_id': f.target_id,
                'reviewer': f.reviewer,
                'review_comment': f.review_comment,
                'converted_at': f.converted_at.isoformat() if f.converted_at else None,
                'confirmed_at': f.updated_at.isoformat() if f.manual_status else None,
            })

        return {
            'report_id': r.id,
            'requirement_source': r.requirement_source_id or '',
            'code_snapshot_id': r.code_snapshot_id or '',
            'code_snapshot_name': snap.name if snap else '',
            'project_id': str(r.project_id) if r.project_id else None,
            'created_at': r.created_at.isoformat() if r.created_at else '',
            'ai_mode': r.analysis_mode,
            'summary': {
                'total_req_points': r.total_requirement_points,
                'implemented': r.implemented_count,
                'missing': r.missing_count,
                'extra': r.extra_count,
                'uncertain': r.uncertain_count,
                'risk': r.risk_count,
            },
            'findings': findings_out,
            'code_summary': r.code_summary or '',
            'source': source,
        }

    def _load_legacy_reports(self) -> List[dict]:
        results = []
        if not LEGACY_REPORTS_DIR.exists():
            return results
        for f in LEGACY_REPORTS_DIR.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                results.append(data)
            except Exception:
                pass
        return results

    def _load_legacy_report(self, report_id: str) -> Optional[dict]:
        path = LEGACY_REPORTS_DIR / f"{report_id}.json"
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                pass
        # scan all
        for f in LEGACY_REPORTS_DIR.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if data.get('report_id') == report_id:
                    return data
            except Exception:
                pass
        return None
