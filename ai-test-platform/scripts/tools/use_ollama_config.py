#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置系统使用Ollama作为AI提供商
"""

import os

# 设置环境变量强制使用Ollama
os.environ['USE_OLLAMA'] = '1'
os.environ['AI_PROVIDER'] = 'ollama'

print("✅ 已配置使用Ollama作为AI提供商")
