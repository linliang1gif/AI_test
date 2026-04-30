#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SVN 配置文件
"""

import os
from pathlib import Path

# SVN 配置
SVN_CONFIG = {
    # 默认用户名（可选）
    "default_username": os.getenv("SVN_USERNAME", ""),
    
    # 默认密码（可选，建议使用环境变量）
    "default_password": os.getenv("SVN_PASSWORD", ""),
    
    # 临时文件目录
    "temp_dir": Path(__file__).parent.parent / "temp" / "svn",
    
    # 支持的文件类型
    "supported_extensions": [".docx", ".txt", ".md", ".pdf", ".doc"],
    
    # 文件大小限制（MB）
    "max_file_size_mb": 50,
    
    # 超时时间（秒）
    "timeout": 300,
}

# 创建临时目录
SVN_CONFIG["temp_dir"].mkdir(parents=True, exist_ok=True)
