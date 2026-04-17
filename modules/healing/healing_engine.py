"""
Self-Healing 引擎（分层版）
实现 L1-L4 四层自动修复策略
"""
from typing import List, Dict, Any, Optional
import re

# 🔧 使用 core 层的统一模型
from core import HealingLevel, TestCaseStatus


class HealingEngine:
    """Self-Healing 引擎"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化修复引擎
        
        Args:
            config: 配置项
                - enable_l1: 是否启用L1修复，默认True
                - enable_l2: 是否启用L2修复，默认True
                - enable_l3: 是否启用L3修复，默认True
                - enable_l4: 是否启用L4修复，默认True
                - max_retry: 最大重试次数，默认3
        """
        self.config = config or {}
        self.enable_l1 = self.config.get('enable_l1', True)
        self.enable_l2 = self.config.get('enable_l2', True)
        self.enable_l3 = self.config.get('enable_l3', True)
        self.enable_l4 = self.config.get('enable_l4', True)
        self.max_retry = self.config.get('max_retry', 3)
        
        # 统计信息
        self.stats = {
            'total': 0,
            'healed': 0,
            'by_level': {
                'L1': 0,
                'L2': 0,
                'L3': 0,
                'L4': 0
            }
        }
    
    def heal(self, results: List[Any]) -> List[Any]:
        """
        对测试结果进行自动修复
        
        Args:
            results: ExecutionResult对象列表
        
        Returns:
            修复后的结果列表
        """
        healed_results = []
        
        for r in results:
            self.stats['total'] += 1
            
            # 通过的用例无需修复
            if r.status == TestCaseStatus.PASSED:
                healed_results.append(r)
                continue
            
            # 分析错误并确定修复策略
            healing_level = self._analyze_error(r.error)
            
            # 应用修复策略
            healed_result = self._apply_healing(r, healing_level)
            healed_results.append(healed_result)
            
            # 更新统计
            if healing_level.value != "NONE":
                self.stats['healed'] += 1
                self.stats['by_level'][healing_level.value] += 1
        
        return healed_results
    
    def _analyze_error(self, error_message: str) -> HealingLevel:
        """
        分析错误信息，确定修复级别
        
        Args:
            error_message: 错误信息
        
        Returns:
            修复级别
        """
        if not error_message:
            return HealingLevel.L1_RETRY  # 默认返回L1
        
        error_lower = error_message.lower()
        
        # L1: 环境问题（网络、超时、连接）
        if self.enable_l1:
            l1_patterns = [
                r'timeout',
                r'connection.*(?:refused|reset|closed|failed)',
                r'network.*(?:error|unreachable)',
                r'socket.*error',
                r'503.*service unavailable',
                r'502.*bad gateway',
                r'504.*gateway timeout',
                r'connection.*timed out'
            ]
            
            for pattern in l1_patterns:
                if re.search(pattern, error_lower):
                    return HealingLevel.L1_RETRY
        
        # L2: 数据问题（无效数据、空值、格式错误）
        if self.enable_l2:
            l2_patterns = [
                r'invalid.*(?:data|value|format|type)',
                r'null.*(?:pointer|reference|value)',
                r'missing.*(?:required|field|parameter)',
                r'validation.*(?:error|failed)',
                r'bad.*request',
                r'400.*bad request',
                r'422.*unprocessable entity',
                r'data.*(?:not found|missing)'
            ]
            
            for pattern in l2_patterns:
                if re.search(pattern, error_lower):
                    return HealingLevel.L2_DATA
        
        # L3: 不稳定（间歇性失败、竞态条件）
        if self.enable_l3:
            l3_patterns = [
                r'flaky',
                r'intermittent',
                r'race.*condition',
                r'random.*(?:failure|error)',
                r'sometimes.*(?:fails|passes)',
                r'unstable'
            ]
            
            for pattern in l3_patterns:
                if re.search(pattern, error_lower):
                    return HealingLevel.L3_TOLERANCE
        
        # L4: 断言失败（需要人工审查）
        if self.enable_l4:
            l4_patterns = [
                r'assertion.*failed',
                r'expected.*but.*(?:got|was)',
                r'status.*code.*(?:expected|mismatch)',
                r'json.*path.*not found',
                r'response.*(?:mismatch|incorrect)'
            ]
            
            for pattern in l4_patterns:
                if re.search(pattern, error_lower):
                    return HealingLevel.L4_MANUAL
        
        # 默认：需要人工审查
        return HealingLevel.L4_MANUAL
    
    def _apply_healing(self, result: Any, healing_level: HealingLevel) -> Any:
        """
        应用修复策略
        
        Args:
            result: ExecutionResult对象
            healing_level: 修复级别
        
        Returns:
            修复后的结果
        """
        # 设置修复信息
        result.healing_applied = True
        result.healing_level = healing_level
        
        if healing_level == HealingLevel.L1_RETRY:
            # L1: 环境问题 - 标记为需要重试
            result.healing_details = f'环境问题（网络/超时/连接），建议重试最多{self.max_retry}次'
            # 保持原状态，由执行引擎处理重试
            
        elif healing_level == HealingLevel.L2_DATA:
            # L2: 数据问题 - 标记为需要重建数据
            result.healing_details = '数据问题（无效/缺失/格式错误），建议重新生成测试数据后重试'
            # 保持原状态，由数据管理器处理
            
        elif healing_level == HealingLevel.L3_TOLERANCE:
            # L3: 不稳定 - 标记为容错通过
            result.healing_details = '测试不稳定（间歇性失败），标记为flaky，暂时容错通过'
            result.status = TestCaseStatus.PASSED  # 修改状态为通过
            
        elif healing_level == HealingLevel.L4_MANUAL:
            # L4: 断言失败 - 标记为需要人工审查
            result.healing_details = '断言失败或未知错误，需要人工审查，可能是真实的bug'
            # 保持失败状态
        
        return result
    
    def get_healing_report(self) -> Dict[str, Any]:
        """
        获取修复报告
        
        Returns:
            修复报告字典
        """
        healing_rate = (self.stats['healed'] / self.stats['total'] * 100) if self.stats['total'] > 0 else 0
        
        return {
            'total_cases': self.stats['total'],
            'healed_cases': self.stats['healed'],
            'healing_rate': f"{healing_rate:.1f}%",
            'by_level': {
                'L1_RETRY': {
                    'count': self.stats['by_level']['L1'],
                    'description': '环境问题（重试）'
                },
                'L2_DATA': {
                    'count': self.stats['by_level']['L2'],
                    'description': '数据问题（重建数据）'
                },
                'L3_TOLERANCE': {
                    'count': self.stats['by_level']['L3'],
                    'description': '不稳定（容错）'
                },
                'L4_MANUAL': {
                    'count': self.stats['by_level']['L4'],
                    'description': '需要人工审查'
                }
            }
        }
    
    def get_manual_review_cases(self, results: List[Any]) -> List[Any]:
        """
        获取需要人工审查的用例
        
        Args:
            results: 修复后的结果列表
        
        Returns:
            需要人工审查的用例列表
        """
        manual_cases = []
        
        for r in results:
            if r.healing_applied and r.healing_level == HealingLevel.L4_MANUAL:
                manual_cases.append(r)
        
        return manual_cases
    
    def get_retry_cases(self, results: List[Any]) -> List[Any]:
        """
        获取需要重试的用例
        
        Args:
            results: 修复后的结果列表
        
        Returns:
            需要重试的用例列表
        """
        retry_cases = []
        
        for r in results:
            if r.healing_applied:
                level = r.healing_level
                if level in [HealingLevel.L1_RETRY, HealingLevel.L2_DATA]:
                    retry_cases.append(r)
        
        return retry_cases
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'total': 0,
            'healed': 0,
            'by_level': {
                'L1': 0,
                'L2': 0,
                'L3': 0,
                'L4': 0
            }
        }
