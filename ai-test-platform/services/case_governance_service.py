"""
Phase 16: 用例治理服务

功能:
  1. 根据 method + path + operationId 推断 api_pattern
  2. 根据接口路径和方法推断 risk_level (P0/P1/P2)
  3. 标记 destructive / requires_dependency / requires_auth
  4. 标记 assertion_status
  5. 提取 module_name
  6. 推荐测试集查询 (smoke / regression / query-safe / failed-rerun / p0)
"""

import re
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from database.models import TestCase


# ── api_pattern 推断 ─────────────────────────────────────

_PATTERN_RULES = [
    (r'/(page)$',              'page'),
    (r'/(list|getList|findAll|selectAll)$', 'list'),
    (r'/(detail|get|info|query|getById|findById|getOne|view)$', 'detail'),
    (r'/(save|add|create|insert|register|submit|batchSave|batchAdd)$', 'save'),
    (r'/(update|edit|modify|patch|batchUpdate|batchEdit)$', 'modify'),
    (r'/(delete|remove|batchDelete|batchRemove|cancel|void|disable|destroy)$', 'delete'),
]

_METHOD_PATTERN_MAP = {
    'DELETE': 'delete',
}


def infer_api_pattern(method: str, url: str, operation_id: str = '') -> str:
    """根据 method + path + operationId 推断 api_pattern"""
    url_lower = (url or '').lower()
    op_lower = (operation_id or '').lower()

    # 先按 URL 后缀匹配
    for regex, pattern in _PATTERN_RULES:
        if re.search(regex, url_lower, re.I):
            return pattern

    # 再按 operationId 匹配
    for regex, pattern in _PATTERN_RULES:
        suffix = regex.replace(r'/(', '').replace(r')$', '').split('|')
        for s in suffix:
            if s in op_lower:
                return pattern

    # 按 HTTP method 推断
    m = (method or '').upper()
    if m in _METHOD_PATTERN_MAP:
        return _METHOD_PATTERN_MAP[m]
    if m in ('POST',) and any(k in url_lower for k in ('/save', '/add', '/create', '/insert')):
        return 'save'
    if m in ('PUT', 'PATCH'):
        return 'modify'

    return 'unknown'


# ── risk_level 推断 ──────────────────────────────────────

def infer_risk_level(method: str, url: str, api_pattern: str) -> str:
    """推断风险等级: P0(高) / P1(中) / P2(低)"""
    # P0: 删除/作废/取消 接口
    if api_pattern == 'delete':
        return 'P0'

    # P0: 核心写操作（涉及金额/支付/审批/权限）
    url_lower = (url or '').lower()
    p0_keywords = ('pay', 'refund', 'approve', 'permission', 'role', 'password', 'auth', 'login')
    if any(k in url_lower for k in p0_keywords):
        return 'P0'

    # P1: 一般写操作 (save/modify)
    if api_pattern in ('save', 'modify'):
        return 'P1'

    # P2: 查询操作
    return 'P2'


# ── 其他标记推断 ─────────────────────────────────────────

_DESTRUCTIVE_KEYWORDS = (
    'delete', 'remove', 'cancel', 'void', 'disable', 'destroy',
    'batchdelete', 'batchremove', '作废', '删除',
)


def infer_destructive(method: str, url: str, api_pattern: str) -> bool:
    url_lower = (url or '').lower()
    if api_pattern == 'delete':
        return True
    if (method or '').upper() == 'DELETE':
        return True
    return any(k in url_lower for k in _DESTRUCTIVE_KEYWORDS)


def infer_requires_dependency(method: str, api_pattern: str) -> bool:
    """POST/PUT/PATCH 或写类操作默认需要前置数据"""
    if (method or '').upper() in ('POST', 'PUT', 'PATCH'):
        return True
    return api_pattern in ('save', 'modify', 'delete')


def infer_requires_auth(url: str) -> bool:
    """大部分接口需要认证，仅 /login, /register, /health, /public 不需要"""
    url_lower = (url or '').lower()
    open_patterns = ('/login', '/register', '/health', '/public', '/captcha', '/sms/send')
    return not any(url_lower.endswith(p) or p in url_lower for p in open_patterns)


def infer_assertion_status(assertions) -> str:
    if not assertions:
        return 'no_assertion'
    if isinstance(assertions, list) and len(assertions) > 0:
        return 'has_assertion'
    return 'no_assertion'


def extract_module_name(url: str) -> str:
    """从 URL 路径提取模块名。/basic/basicCurrency/page → basicCurrency"""
    parts = (url or '').strip('/').split('/')
    if len(parts) >= 2:
        return parts[-2]  # 倒数第二段
    if len(parts) == 1:
        return parts[0]
    return ''


# ── 综合治理：给单条用例打标签 ────────────────────────────

def govern_single_case(tc: TestCase) -> Dict:
    """分析一条用例，返回需要更新的字段字典"""
    exec_config = tc.execution_config or {}
    method = (exec_config.get('method') or '').upper()
    url = exec_config.get('url') or ''
    operation_id = exec_config.get('operationId') or exec_config.get('operation_id') or ''

    api_pattern = infer_api_pattern(method, url, operation_id)
    risk_level = infer_risk_level(method, url, api_pattern)

    updates = {
        'module_name': extract_module_name(url),
        'api_pattern': api_pattern,
        'risk_level': risk_level,
        'executable': bool(method and url),
        'requires_auth': infer_requires_auth(url),
        'requires_dependency': infer_requires_dependency(method, api_pattern),
        'destructive': infer_destructive(method, url, api_pattern),
        'assertion_status': infer_assertion_status(tc.assertions),
    }
    return updates


# ── 批量治理 ─────────────────────────────────────────────

class CaseGovernanceService:
    """用例治理服务"""

    def __init__(self, db: Session):
        self.db = db

    def govern_all(self, force: bool = False) -> Dict:
        """批量治理所有用例。force=True 时覆盖已有标签。"""
        query = self.db.query(TestCase)
        if not force:
            # 仅治理未打标签的用例
            query = query.filter(
                or_(TestCase.api_pattern == None, TestCase.api_pattern == '')
            )
        cases = query.all()

        stats = {'total': len(cases), 'updated': 0, 'patterns': {}, 'risk_levels': {}}
        for tc in cases:
            updates = govern_single_case(tc)
            for k, v in updates.items():
                setattr(tc, k, v)
            stats['updated'] += 1
            p = updates['api_pattern']
            stats['patterns'][p] = stats['patterns'].get(p, 0) + 1
            r = updates['risk_level']
            stats['risk_levels'][r] = stats['risk_levels'].get(r, 0) + 1

        self.db.commit()
        return stats

    def get_governance_summary(self) -> Dict:
        """获取治理概况统计"""
        total = self.db.query(TestCase).count()
        governed = self.db.query(TestCase).filter(TestCase.api_pattern != None, TestCase.api_pattern != '').count()

        pattern_counts = {}
        for row in self.db.query(TestCase.api_pattern, TestCase.id).all():
            p = row[0] or 'unknown'
            pattern_counts[p] = pattern_counts.get(p, 0) + 1

        risk_counts = {}
        for row in self.db.query(TestCase.risk_level, TestCase.id).all():
            r = row[0] or 'unset'
            risk_counts[r] = risk_counts.get(r, 0) + 1

        destructive_count = self.db.query(TestCase).filter(TestCase.destructive == True).count()
        no_assertion_count = self.db.query(TestCase).filter(TestCase.assertion_status == 'no_assertion').count()
        failed_count = self.db.query(TestCase).filter(TestCase.last_run_status == 'failed').count()

        return {
            'total': total,
            'governed': governed,
            'ungoverned': total - governed,
            'pattern_counts': pattern_counts,
            'risk_counts': risk_counts,
            'destructive_count': destructive_count,
            'no_assertion_count': no_assertion_count,
            'failed_count': failed_count,
        }

    # ── 推荐测试集 ────────────────────────────────────────

    def recommend_smoke(self, limit: int = 200) -> List[TestCase]:
        """冒烟测试集: P0 + P1 中的 list/page/detail + 非破坏性"""
        return self.db.query(TestCase).filter(
            and_(
                TestCase.risk_level.in_(['P0', 'P1']),
                TestCase.destructive == False,
                TestCase.executable == True,
            )
        ).limit(limit).all()

    def recommend_regression(self, limit: int = 500) -> List[TestCase]:
        """回归测试集: 所有可执行 + 非破坏性"""
        return self.db.query(TestCase).filter(
            and_(
                TestCase.executable == True,
                TestCase.destructive == False,
            )
        ).limit(limit).all()

    def recommend_query_safe(self, limit: int = 500) -> List[TestCase]:
        """查询安全集: api_pattern 为 list/page/detail/unknown 且非破坏性"""
        return self.db.query(TestCase).filter(
            and_(
                TestCase.api_pattern.in_(['list', 'page', 'detail']),
                TestCase.executable == True,
            )
        ).limit(limit).all()

    def recommend_failed_rerun(self, limit: int = 500) -> List[TestCase]:
        """失败重跑集: last_run_status == failed"""
        return self.db.query(TestCase).filter(
            and_(
                TestCase.last_run_status == 'failed',
                TestCase.executable == True,
            )
        ).limit(limit).all()

    def recommend_p0(self, limit: int = 200) -> List[TestCase]:
        """P0 测试集"""
        return self.db.query(TestCase).filter(
            and_(
                TestCase.risk_level == 'P0',
                TestCase.executable == True,
            )
        ).limit(limit).all()
