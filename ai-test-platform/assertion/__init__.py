#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
断言模块 - 完整的断言系统

提供:
- 断言引擎 (AssertionEngine)
- 断言类型定义 (AssertionConfig, AssertionOperator等)
- 断言构建器 (AssertionBuilder)
- AI辅助断言生成 (AIAssertionGenerator)
- 断言验证器 (AssertionValidator)
- 知识库集成 (AssertionKnowledgeIntegration)
"""

from .assertion_engine import (
    AssertionEngine,
    AssertionResult,
    AssertionType,
    get_assertion_engine
)

from .assertion_types import (
    AssertionConfig,
    AssertionOperator,
    AssertionSeverity,
    AssertionTemplate,
    AssertionTemplates
)

from .assertion_builder import (
    AssertionBuilder,
    create_assertion,
    quick_assertions
)

from .ai_assertion_generator import AIAssertionGenerator

from .assertion_validator import AssertionValidator

from .assertion_knowledge_integration import AssertionKnowledgeIntegration


__all__ = [
    # 引擎
    'AssertionEngine',
    'AssertionResult',
    'AssertionType',
    'get_assertion_engine',
    
    # 类型
    'AssertionConfig',
    'AssertionOperator',
    'AssertionSeverity',
    'AssertionTemplate',
    'AssertionTemplates',
    
    # 构建器
    'AssertionBuilder',
    'create_assertion',
    'quick_assertions',
    
    # AI生成
    'AIAssertionGenerator',
    
    # 验证器
    'AssertionValidator',
    
    # 知识库
    'AssertionKnowledgeIntegration'
]


__version__ = '1.0.0'
