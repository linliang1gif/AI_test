"""
Pipeline Module - 测试流程总调度器
打通 Agent → Strategy → Orchestrator → Self-Healing → Report
"""

from .pipeline_service import PipelineService, get_pipeline_service
from .report_generator import generate_report, generate_ai_summary

__all__ = [
    'PipelineService',
    'get_pipeline_service',
    'generate_report',
    'generate_ai_summary'
]
