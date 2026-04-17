#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI模块 - AI客户端和Prompt库
"""

from .ai_client import AIClient, get_ai_client
from .prompt_library import PromptLibrary

__all__ = ['AIClient', 'get_ai_client', 'PromptLibrary']