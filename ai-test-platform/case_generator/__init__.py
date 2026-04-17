#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Case Generator Module - 测试用例生成核心模块
整合传统流程的用例生成能力，提供统一的用例生成服务
"""

from .case_service import get_case_service

__all__ = ['get_case_service']
