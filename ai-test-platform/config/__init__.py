#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置模块 - 平台配置管理
"""

from .config import Config, get_config, reload_config

__all__ = ['Config', 'get_config', 'reload_config']