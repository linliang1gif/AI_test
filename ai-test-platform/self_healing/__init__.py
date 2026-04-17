"""
Self-Healing Module - 自动修复模块
当测试失败时，自动分析错误原因并尝试修复，然后重新执行测试
"""

from .healing_service import HealingService, get_healing_service
from .analyzer import analyze_error, extract_error_context, calculate_fix_confidence
from .fixer import apply_fix, get_fix_strategy

__all__ = [
    'HealingService',
    'get_healing_service',
    'analyze_error',
    'extract_error_context',
    'calculate_fix_confidence',
    'apply_fix',
    'get_fix_strategy'
]
