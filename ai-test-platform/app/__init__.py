#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
应用模块 - 主流程和API服务器
"""

__all__ = ['AITestPlatform']

def __getattr__(name):
    if name == 'AITestPlatform':
        from .main import AITestPlatform
        return AITestPlatform
    raise AttributeError(name)