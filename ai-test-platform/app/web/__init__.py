#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Web可视化平台模块
"""

from .web_server import WebServer
from .api_routes import setup_routes

__all__ = ['WebServer', 'setup_routes']