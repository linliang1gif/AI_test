# FROZEN MODULE — 仅允许 bug fix 和必要 shim
# 新功能请进入主线，参见 docs/architecture/SYSTEM_MAINLINE.md
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置模块 - 平台配置管理
"""

from .config import Config, get_config, reload_config

__all__ = ['Config', 'get_config', 'reload_config']