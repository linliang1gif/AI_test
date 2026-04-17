#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Test Platform - 统一日志系统

提供结构化日志记录，支持不同级别的日志输出和文件记录。
"""

import os
import sys
import logging
import traceback
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from logging.handlers import RotatingFileHandler

class PlatformLogger:
    """平台统一日志器"""
    
    def __init__(self, name: str = "ai_test_platform", log_dir: str = "logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # 创建logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # 避免重复添加handler
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """设置日志处理器"""
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # 文件处理器 - 详细日志
        file_handler = RotatingFileHandler(
            self.log_dir / f"{self.name}.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        # 错误日志文件
        error_handler = RotatingFileHandler(
            self.log_dir / f"{self.name}_error.log",
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        
        # 添加处理器
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
    
    def debug(self, message: str, extra: Dict[str, Any] = None):
        """调试日志"""
        self._log(logging.DEBUG, message, extra)
    
    def info(self, message: str, extra: Dict[str, Any] = None):
        """信息日志"""
        self._log(logging.INFO, message, extra)
    
    def warning(self, message: str, extra: Dict[str, Any] = None):
        """警告日志"""
        self._log(logging.WARNING, message, extra)
    
    def error(self, message: str, exception: Exception = None, extra: Dict[str, Any] = None):
        """错误日志"""
        if exception:
            message = f"{message} - Exception: {str(exception)}"
            if extra is None:
                extra = {}
            extra['traceback'] = traceback.format_exc()
        self._log(logging.ERROR, message, extra)
    
    def critical(self, message: str, exception: Exception = None, extra: Dict[str, Any] = None):
        """严重错误日志"""
        if exception:
            message = f"{message} - Exception: {str(exception)}"
            if extra is None:
                extra = {}
            extra['traceback'] = traceback.format_exc()
        self._log(logging.CRITICAL, message, extra)
    
    def _log(self, level: int, message: str, extra: Dict[str, Any] = None):
        """内部日志方法"""
        if extra:
            # 将额外信息添加到消息中
            extra_str = " | ".join([f"{k}={v}" for k, v in extra.items() if k != 'traceback'])
            if extra_str:
                message = f"{message} | {extra_str}"
            
            # 如果有traceback，单独记录
            if 'traceback' in extra:
                self.logger.log(level, f"{message}\nTraceback:\n{extra['traceback']}")
            else:
                self.logger.log(level, message)
        else:
            self.logger.log(level, message)
    
    def log_api_call(self, provider: str, model: str, prompt_length: int, 
                    response_length: int = None, duration: float = None, 
                    success: bool = True, error: str = None):
        """记录AI API调用"""
        extra = {
            'provider': provider,
            'model': model,
            'prompt_length': prompt_length,
            'response_length': response_length or 0,
            'duration': duration or 0,
            'success': success
        }
        
        if success:
            self.info(f"AI API调用成功 - {provider}/{model}", extra)
        else:
            extra['error'] = error
            self.error(f"AI API调用失败 - {provider}/{model}", extra=extra)
    
    def log_test_execution(self, test_name: str, status: str, duration: float = None, 
                          details: Dict[str, Any] = None):
        """记录测试执行"""
        extra = {
            'test_name': test_name,
            'status': status,
            'duration': duration or 0
        }
        if details:
            extra.update(details)
        
        if status == 'passed':
            self.info(f"测试执行成功 - {test_name}", extra)
        elif status == 'failed':
            self.error(f"测试执行失败 - {test_name}", extra=extra)
        else:
            self.warning(f"测试执行状态未知 - {test_name}", extra)

# 全局日志器实例
_logger_instances = {}

def get_logger(name: str = "ai_test_platform") -> PlatformLogger:
    """获取日志器实例"""
    if name not in _logger_instances:
        _logger_instances[name] = PlatformLogger(name)
    return _logger_instances[name]

# 便捷函数
def log_info(message: str, extra: Dict[str, Any] = None):
    """记录信息日志"""
    get_logger().info(message, extra)

def log_error(message: str, exception: Exception = None, extra: Dict[str, Any] = None):
    """记录错误日志"""
    get_logger().error(message, exception, extra)

def log_warning(message: str, extra: Dict[str, Any] = None):
    """记录警告日志"""
    get_logger().warning(message, extra)

def log_debug(message: str, extra: Dict[str, Any] = None):
    """记录调试日志"""
    get_logger().debug(message, extra)