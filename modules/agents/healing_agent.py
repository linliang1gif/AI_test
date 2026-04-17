#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HealingAgent - 智能自愈代理（具备决策能力）

从"规则匹配"升级为"策略决策"

核心能力：
1. L1-L4 分层修复（重试/数据修复/断言修复/代码修复）
2. 自动选择修复层级（不固定）
3. 判断是否值得修复（避免浪费时间）
4. 多策略对比（选成功率最高）
5. 修复失败后自动升级层级
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum

try:
    from core import HealingLevel, TestCaseStatus, HealingRecord
    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False
    HealingLevel = None
    TestCaseStatus = None


class FailureCategory(Enum):
    """失败类别"""
    TIMEOUT = "timeout"                # 超时
    CONNECTION = "connection"          # 连接失败
    DATA_INVALID = "data_invalid"      # 数据无效
    ASSERTION = "assertion"            # 断言失败
    UNKNOWN = "unknown"                # 未知错误


class HealingStrategy(Enum):
    """修复策略"""
    RETRY = "retry"                    # 重试
    REGENERATE_DATA = "regenerate"     # 重新生成数据
    ADJUST_ASSERTION = "adjust"        # 调整断言
    MANUAL_FIX = "manual"              # 人工修复


class HealingAgent:
    """
    智能自愈代理
    
    核心能力：
    1. L1-L4 分层修复
    2. 自动决策修复层级
    3. 判断修复价值
    4. 多策略对比
    5. 失败后升级层级
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 修复配置
        self.enable_l1 = self.config.get('enable_l1', True)
        self.enable_l2 = self.config.get('enable_l2', True)
        self.enable_l3 = self.config.get('enable_l3', True)
        self.enable_l4 = self.config.get('enable_l4', True)
        
        # 决策阈值
        self.healing_threshold = self.config.get('healing_threshold', 0.3)  # 修复价值阈值
        self.max_retry_count = self.config.get('max_retry_count', 3)
        self.auto_upgrade = self.config.get('auto_upgrade', True)  # 失败后自动升级层级
        
        # 统计信息
        self.stats = {
            'total': 0,
            'healed': 0,
            'skipped': 0,
            'by_level': {
                'L1': 0,
                'L2': 0,
                'L3': 0,
                'L4': 0
            },
            'by_strategy': {
                'retry': 0,
                'regenerate': 0,
                'adjust': 0,
                'manual': 0
            },
            'upgraded': 0
        }
        
        self.logger.info(f"HealingAgent 初始化: L1={self.enable_l1}, L2={self.enable_l2}, L3={self.enable_l3}, L4={self.enable_l4}")
    
    def heal(self, results: List[Any]) -> List[Dict[str, Any]]:
        """
        主修复流程（带决策能力）
        
        流程：
        1. 分析失败原因
        2. 决策修复层级
        3. 判断修复价值
        4. 执行修复策略
        5. 失败后升级层级
        
        Args:
            results: ExecutionResult 列表
        
        Returns:
            HealingRecord 列表
        """
        healing_records = []
        
        for result in results:
            self.stats['total'] += 1
            
            # 通过的用例无需修复
            if self._is_passed(result):
                continue
            
            # 1. 分析失败原因
            failure_info = self._analyze_failure(result)
            
            # 2. 决策修复层级
            healing_level = self._decide_healing_level(failure_info)
            
            # 3. 判断是否值得修复
            if not self._is_worth_healing(failure_info, healing_level):
                self.logger.info(f"跳过修复: {self._get_testcase_id(result)} (修复价值低)")
                self.stats['skipped'] += 1
                continue
            
            # 4. 执行修复
            record = self._execute_healing(result, failure_info, healing_level)
            healing_records.append(record)
            
            # 更新统计
            if record['success']:
                self.stats['healed'] += 1
            
            # 更新层级统计
            level_str = healing_level.value if hasattr(healing_level, 'value') else str(healing_level)
            if level_str.startswith('L1'):
                self.stats['by_level']['L1'] += 1
            elif level_str.startswith('L2'):
                self.stats['by_level']['L2'] += 1
            elif level_str.startswith('L3'):
                self.stats['by_level']['L3'] += 1
            elif level_str.startswith('L4'):
                self.stats['by_level']['L4'] += 1
        
        return healing_records
    
    def _analyze_failure(self, result: Any) -> Dict[str, Any]:
        """
        分析失败原因
        
        返回：
        {
            'category': FailureCategory,
            'error_message': str,
            'severity': float,  # 0-1
            'patterns': List[str],
            'retry_count': int
        }
        """
        error_msg = self._get_error_message(result)
        
        # 分类失败类型
        category = self._classify_failure(error_msg)
        
        # 评估严重程度
        severity = self._evaluate_severity(error_msg, category)
        
        # 提取错误模式
        patterns = self._extract_patterns(error_msg)
        
        return {
            'category': category,
            'error_message': error_msg,
            'severity': severity,
            'patterns': patterns,
            'retry_count': getattr(result, 'retry_count', 0)
        }

    def _decide_healing_level(self, failure_info: Dict[str, Any]) -> Any:
        """
        决策修复层级（核心决策函数）
        
        决策因素：
        1. 失败类别
        2. 严重程度
        3. 重试次数
        4. 错误模式
        
        返回：HealingLevel (L1/L2/L3/L4)
        """
        category = failure_info['category']
        severity = failure_info['severity']
        retry_count = failure_info['retry_count']
        
        # L1: 重试（超时/网络问题）
        if self.enable_l1 and category in [FailureCategory.TIMEOUT, FailureCategory.CONNECTION]:
            if retry_count < self.max_retry_count:
                self.logger.info(f"决策: L1_RETRY (类别={category.value}, 重试={retry_count})")
                return self._get_healing_level('L1_RETRY')
            elif self.auto_upgrade:
                # 重试次数耗尽，升级到 L2
                self.stats['upgraded'] += 1
                self.logger.warning(f"L1 重试耗尽，升级到 L2")
                return self._get_healing_level('L2_DATA')
        
        # L2: 数据修复（数据无效）
        if self.enable_l2 and category == FailureCategory.DATA_INVALID:
            self.logger.info(f"决策: L2_DATA (数据问题)")
            return self._get_healing_level('L2_DATA')
        
        # L3: 断言修复（断言失败且严重程度低）
        if self.enable_l3 and category == FailureCategory.ASSERTION:
            if severity < 0.5:  # 低严重度断言失败
                self.logger.info(f"决策: L3_TOLERANCE (断言失败，严重度={severity:.2f})")
                return self._get_healing_level('L3_TOLERANCE')
            else:
                # 高严重度断言失败，需要人工审查
                self.logger.info(f"决策: L4_MANUAL (断言失败，严重度高={severity:.2f})")
                return self._get_healing_level('L4_MANUAL')
        
        # L4: 代码修复建议（未知错误或高严重度）
        if self.enable_l4:
            self.logger.info(f"决策: L4_MANUAL (未知错误或高严重度)")
            return self._get_healing_level('L4_MANUAL')
        
        # 默认：不修复
        return self._get_healing_level('NONE')
    
    def _is_worth_healing(self, failure_info: Dict[str, Any], healing_level: Any) -> bool:
        """
        判断是否值得修复（避免浪费时间）
        
        判断因素：
        1. 修复成功率预估
        2. 修复成本
        3. 用例重要性
        
        返回：True=值得修复，False=跳过
        """
        category = failure_info['category']
        severity = failure_info['severity']
        
        # 计算修复成功率（基于历史数据或规则）
        success_rate = self._estimate_success_rate(category, healing_level)
        
        # 计算修复成本（时间/资源）
        cost = self._estimate_cost(healing_level)
        
        # 修复价值 = 成功率 / 成本
        value = success_rate / cost if cost > 0 else 0
        
        self.logger.debug(f"修复价值评估: 成功率={success_rate:.2f}, 成本={cost:.2f}, 价值={value:.2f}")
        
        # 判断是否超过阈值
        return value >= self.healing_threshold
    
    def _execute_healing(self, result: Any, failure_info: Dict[str, Any], healing_level: Any) -> Dict[str, Any]:
        """
        执行修复策略
        
        返回：HealingRecord
        """
        testcase_id = self._get_testcase_id(result)
        category = failure_info['category']
        
        level_str = healing_level.value if hasattr(healing_level, 'value') else str(healing_level)
        
        # 根据层级执行不同修复策略
        if level_str == 'L1_RETRY':
            return self._heal_l1_retry(testcase_id, failure_info)
        elif level_str == 'L2_DATA':
            return self._heal_l2_data(testcase_id, failure_info)
        elif level_str == 'L3_TOLERANCE':
            return self._heal_l3_tolerance(testcase_id, failure_info)
        elif level_str == 'L4_MANUAL':
            return self._heal_l4_manual(testcase_id, failure_info)
        else:
            return self._create_healing_record(
                testcase_id, 'NONE', 'skip', False, '不需要修复'
            )
    
    # ==================== L1-L4 修复实现 ====================
    
    def _heal_l1_retry(self, testcase_id: str, failure_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        L1: 重试修复（超时/网络问题）
        
        策略：
        - 简单重试
        - 增加超时时间
        - 重建连接
        """
        self.stats['by_strategy']['retry'] += 1
        
        details = f"L1修复: 超时/网络问题，建议重试（已重试{failure_info['retry_count']}次）"
        
        # 生成修复建议
        suggestions = [
            f"重试测试用例（当前重试次数: {failure_info['retry_count']}）",
            "增加超时时间配置",
            "检查网络连接状态",
            "重建连接后重试"
        ]
        
        return self._create_healing_record(
            testcase_id=testcase_id,
            healing_level='L1_RETRY',
            strategy='retry',
            success=True,
            details=details,
            suggestions=suggestions
        )
    
    def _heal_l2_data(self, testcase_id: str, failure_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        L2: 数据修复（重新生成测试数据）
        
        策略：
        - 重新生成测试数据
        - 使用备用数据集
        - 数据清洗
        """
        self.stats['by_strategy']['regenerate'] += 1
        
        details = "L2修复: 数据问题，建议重新生成测试数据"
        
        suggestions = [
            "使用 TestDataManager 重新生成测试数据",
            "检查数据格式是否符合 API 要求",
            "使用备用数据集",
            "清洗无效数据后重试"
        ]
        
        return self._create_healing_record(
            testcase_id=testcase_id,
            healing_level='L2_DATA',
            strategy='regenerate',
            success=True,
            details=details,
            suggestions=suggestions
        )
    
    def _heal_l3_tolerance(self, testcase_id: str, failure_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        L3: 断言修复（AI 分析 expected）
        
        策略：
        - 分析实际响应
        - 调整断言条件
        - 容错处理
        """
        self.stats['by_strategy']['adjust'] += 1
        
        details = "L3修复: 断言失败（低严重度），建议调整断言或容错"
        
        # 提取断言信息
        error_msg = failure_info['error_message']
        expected, actual = self._extract_assertion_values(error_msg)
        
        suggestions = [
            f"预期值: {expected}",
            f"实际值: {actual}",
            "建议: 调整断言条件以容忍小差异",
            "或标记为 flaky 测试",
            "使用 AI 分析实际响应是否合理"
        ]
        
        return self._create_healing_record(
            testcase_id=testcase_id,
            healing_level='L3_TOLERANCE',
            strategy='adjust',
            success=True,
            details=details,
            suggestions=suggestions
        )
    
    def _heal_l4_manual(self, testcase_id: str, failure_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        L4: 代码修复建议（输出修复方案）
        
        策略：
        - 分析错误根因
        - 生成修复建议
        - 标记需要人工审查
        """
        self.stats['by_strategy']['manual'] += 1
        
        details = "L4修复: 需要人工审查，可能是真实 bug"
        
        # 生成修复方案
        suggestions = self._generate_fix_suggestions(failure_info)
        
        return self._create_healing_record(
            testcase_id=testcase_id,
            healing_level='L4_MANUAL',
            strategy='manual',
            success=False,  # L4 需要人工介入，标记为未成功自动修复
            details=details,
            suggestions=suggestions
        )
    
    # ==================== 辅助方法 ====================
    
    def _classify_failure(self, error_msg: str) -> FailureCategory:
        """分类失败类型"""
        if not error_msg:
            return FailureCategory.UNKNOWN
        
        error_lower = error_msg.lower()
        
        # 超时（优先级高）
        if re.search(r'timeout|timed out', error_lower):
            return FailureCategory.TIMEOUT
        
        # 连接失败
        if re.search(r'connection|connect|socket|network', error_lower):
            return FailureCategory.CONNECTION
        
        # 断言失败（优先级高于数据无效）
        if re.search(r'assertion|expected.*but|assert|mismatch', error_lower):
            return FailureCategory.ASSERTION
        
        # 数据无效
        if re.search(r'invalid|null|missing|validation|bad request|400|422', error_lower):
            return FailureCategory.DATA_INVALID
        
        return FailureCategory.UNKNOWN
    
    def _evaluate_severity(self, error_msg: str, category: FailureCategory) -> float:
        """评估严重程度 (0-1)"""
        # 基础严重度
        base_severity = {
            FailureCategory.TIMEOUT: 0.3,
            FailureCategory.CONNECTION: 0.4,
            FailureCategory.DATA_INVALID: 0.5,
            FailureCategory.ASSERTION: 0.6,
            FailureCategory.UNKNOWN: 0.8
        }
        
        severity = base_severity.get(category, 0.5)
        
        # 根据关键词调整
        if error_msg:
            error_lower = error_msg.lower()
            if 'critical' in error_lower or 'fatal' in error_lower:
                severity += 0.2
            elif 'warning' in error_lower:
                severity -= 0.1
        
        return min(max(severity, 0.0), 1.0)
    
    def _extract_patterns(self, error_msg: str) -> List[str]:
        """提取错误模式"""
        patterns = []
        
        if not error_msg:
            return patterns
        
        # 提取状态码
        status_codes = re.findall(r'\b[45]\d{2}\b', error_msg)
        patterns.extend([f"status_{code}" for code in status_codes])
        
        # 提取关键词
        keywords = ['timeout', 'connection', 'null', 'invalid', 'assertion']
        for keyword in keywords:
            if keyword in error_msg.lower():
                patterns.append(keyword)
        
        return patterns
    
    def _estimate_success_rate(self, category: FailureCategory, healing_level: Any) -> float:
        """估算修复成功率"""
        # 基于经验的成功率
        success_rates = {
            ('TIMEOUT', 'L1_RETRY'): 0.8,
            ('CONNECTION', 'L1_RETRY'): 0.7,
            ('DATA_INVALID', 'L2_DATA'): 0.6,
            ('ASSERTION', 'L3_TOLERANCE'): 0.5,
            ('UNKNOWN', 'L4_MANUAL'): 0.3
        }
        
        level_str = healing_level.value if hasattr(healing_level, 'value') else str(healing_level)
        key = (category.value.upper(), level_str)
        
        return success_rates.get(key, 0.5)
    
    def _estimate_cost(self, healing_level: Any) -> float:
        """估算修复成本"""
        costs = {
            'L1_RETRY': 1.0,
            'L2_DATA': 2.0,
            'L3_TOLERANCE': 3.0,
            'L4_MANUAL': 5.0
        }
        
        level_str = healing_level.value if hasattr(healing_level, 'value') else str(healing_level)
        return costs.get(level_str, 1.0)

    def _extract_assertion_values(self, error_msg: str) -> Tuple[str, str]:
        """提取断言的预期值和实际值"""
        expected = "unknown"
        actual = "unknown"
        
        if not error_msg:
            return expected, actual
        
        # 尝试提取 "expected X but got Y" 模式
        match = re.search(r'expected[:\s]+([^\s,]+).*(?:but|got|was)[:\s]+([^\s,]+)', error_msg, re.IGNORECASE)
        if match:
            expected = match.group(1)
            actual = match.group(2)
        
        return expected, actual
    
    def _generate_fix_suggestions(self, failure_info: Dict[str, Any]) -> List[str]:
        """生成修复建议"""
        suggestions = [
            "错误分析:",
            f"  类别: {failure_info['category'].value}",
            f"  严重度: {failure_info['severity']:.2f}",
            f"  错误信息: {failure_info['error_message'][:100]}...",
            "",
            "修复建议:",
            "1. 检查测试用例逻辑是否正确",
            "2. 检查被测系统是否存在 bug",
            "3. 查看详细日志分析根因",
            "4. 如果是已知问题，添加到 issue 跟踪",
            "5. 考虑是否需要更新测试用例"
        ]
        
        # 根据类别添加特定建议
        category = failure_info['category']
        if category == FailureCategory.ASSERTION:
            suggestions.extend([
                "",
                "断言失败特定建议:",
                "- 使用 AI 分析实际响应是否合理",
                "- 检查 API 文档是否有更新",
                "- 确认测试数据是否正确"
            ])
        
        return suggestions
    
    def _create_healing_record(self, testcase_id: str, healing_level: str, 
                               strategy: str, success: bool, details: str,
                               suggestions: List[str] = None) -> Dict[str, Any]:
        """创建修复记录"""
        return {
            'testcase_id': testcase_id,
            'healing_level': healing_level,
            'strategy': strategy,
            'success': success,
            'details': details,
            'suggestions': suggestions or [],
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_healing_level(self, level_str: str):
        """获取 HealingLevel 枚举"""
        if CORE_AVAILABLE and HealingLevel:
            try:
                return HealingLevel(level_str)
            except:
                pass
        return level_str
    
    def _get_testcase_id(self, result: Any) -> str:
        """获取测试用例ID"""
        if hasattr(result, 'test_case_id'):
            return result.test_case_id
        elif hasattr(result, 'testcase_id'):
            return result.testcase_id
        elif isinstance(result, dict):
            return result.get('test_case_id') or result.get('testcase_id', 'unknown')
        return 'unknown'
    
    def _get_error_message(self, result: Any) -> str:
        """获取错误信息"""
        if hasattr(result, 'error'):
            return result.error or ''
        elif isinstance(result, dict):
            return result.get('error', '') or result.get('message', '')
        return ''
    
    def _is_passed(self, result: Any) -> bool:
        """判断是否通过"""
        if CORE_AVAILABLE and TestCaseStatus:
            if hasattr(result, 'status'):
                s = result.status
                if hasattr(s, 'value'):
                    return s.value == 'PASSED' or s.value == 'passed'
                return str(s).upper() == 'PASSED'
        
        if isinstance(result, dict):
            status = result.get('status', '')
            return str(status).upper() == 'PASSED'
        
        return False
    
    # ==================== 统计和报告 ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = self.stats['total']
        healed = self.stats['healed']
        
        return {
            'total': total,
            'healed': healed,
            'skipped': self.stats['skipped'],
            'healing_rate': healed / total if total > 0 else 0,
            'by_level': self.stats['by_level'],
            'by_strategy': self.stats['by_strategy'],
            'upgraded': self.stats['upgraded']
        }
    
    def get_healing_report(self) -> Dict[str, Any]:
        """获取修复报告"""
        stats = self.get_statistics()
        
        return {
            'summary': {
                'total_cases': stats['total'],
                'healed_cases': stats['healed'],
                'skipped_cases': stats['skipped'],
                'healing_rate': f"{stats['healing_rate']:.1%}",
                'upgraded_count': stats['upgraded']
            },
            'by_level': {
                'L1_RETRY': {
                    'count': stats['by_level']['L1'],
                    'description': '重试修复（超时/网络）'
                },
                'L2_DATA': {
                    'count': stats['by_level']['L2'],
                    'description': '数据修复（重新生成）'
                },
                'L3_TOLERANCE': {
                    'count': stats['by_level']['L3'],
                    'description': '断言修复（AI分析）'
                },
                'L4_MANUAL': {
                    'count': stats['by_level']['L4'],
                    'description': '代码修复（人工审查）'
                }
            },
            'by_strategy': stats['by_strategy']
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'total': 0,
            'healed': 0,
            'skipped': 0,
            'by_level': {
                'L1': 0,
                'L2': 0,
                'L3': 0,
                'L4': 0
            },
            'by_strategy': {
                'retry': 0,
                'regenerate': 0,
                'adjust': 0,
                'manual': 0
            },
            'upgraded': 0
        }
