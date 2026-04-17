#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Test Platform - 配置管理模块

负责管理平台的所有配置项，包括AI模型配置、测试配置、路径配置等。
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

@dataclass
class AIConfig:
    """AI模型配置"""
    deepseek_api_key: str
    openai_api_key: str
    anthropic_api_key: str
    deepseek_base_url: str
    openai_base_url: str
    anthropic_base_url: str
    ollama_base_url: str
    default_model: str
    default_provider: str
    temperature: float = 0.2
    max_tokens: int = 4000
    timeout: int = 60
    # Ollama支持的模型列表
    ollama_models: list = None

@dataclass
class TestConfig:
    """测试配置"""
    base_url: str
    timeout: int
    max_retries: int
    parallel_workers: int = 4
    test_data_size: str = "medium"  # small, medium, large

@dataclass
class PathConfig:
    """路径配置"""
    data_dir: Path
    output_dir: Path
    tests_dir: Path
    reports_dir: Path
    templates_dir: Path

@dataclass
class ReportConfig:
    """报告配置"""
    title: str
    company_name: str
    author: str = "AI Test Platform"
    version: str = "1.0.0"

class Config:
    """主配置类"""
    
    def __init__(self):
        self.ai = self._load_ai_config()
        self.test = self._load_test_config()
        self.paths = self._load_path_config()
        self.report = self._load_report_config()
        
        # 确保目录存在
        self._ensure_directories()
    
    def _load_ai_config(self) -> AIConfig:
        """加载AI配置"""
        return AIConfig(
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            anthropic_base_url=os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            default_model=os.getenv("DEFAULT_AI_MODEL", "deepseek-chat"),
            default_provider=os.getenv("DEFAULT_AI_PROVIDER", "deepseek"),
            temperature=float(os.getenv("AI_TEMPERATURE", "0.2")),
            max_tokens=int(os.getenv("AI_MAX_TOKENS", "4000")),
            timeout=int(os.getenv("AI_TIMEOUT", "60")),
            ollama_models=os.getenv("OLLAMA_MODELS", "deepseek-coder,qwen2.5,llama3").split(",")
        )
    
    def _load_test_config(self) -> TestConfig:
        """加载测试配置"""
        return TestConfig(
            base_url=os.getenv("BASE_TEST_URL", "http://localhost:8000"),
            timeout=int(os.getenv("TEST_TIMEOUT", "30")),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            parallel_workers=int(os.getenv("PARALLEL_WORKERS", "4")),
            test_data_size=os.getenv("TEST_DATA_SIZE", "medium")
        )
    
    def _load_path_config(self) -> PathConfig:
        """加载路径配置"""
        base_dir = Path(__file__).parent.parent
        
        return PathConfig(
            data_dir=Path(os.getenv("DATA_DIR", base_dir / "data")),
            output_dir=Path(os.getenv("OUTPUT_DIR", base_dir / "output")),
            tests_dir=Path(os.getenv("TESTS_DIR", base_dir / "output" / "tests")),
            reports_dir=Path(os.getenv("REPORTS_DIR", base_dir / "output" / "reports")),
            templates_dir=base_dir / "templates"
        )
    
    def _load_report_config(self) -> ReportConfig:
        """加载报告配置"""
        return ReportConfig(
            title=os.getenv("REPORT_TITLE", "AI Test Platform Report"),
            company_name=os.getenv("COMPANY_NAME", "Your Company Name"),
            author=os.getenv("REPORT_AUTHOR", "AI Test Platform"),
            version=os.getenv("PLATFORM_VERSION", "1.0.0")
        )
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            self.paths.data_dir,
            self.paths.output_dir,
            self.paths.tests_dir,
            self.paths.reports_dir,
            self.paths.templates_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_ai_config_for_provider(self, provider: str = None) -> Dict[str, Any]:
        """获取指定AI提供商的配置"""
        provider = provider or self.ai.default_provider
        
        if provider == "deepseek":
            return {
                "api_key": self.ai.deepseek_api_key,
                "base_url": self.ai.deepseek_base_url,
                "model": self.ai.default_model,
                "temperature": self.ai.temperature,
                "max_tokens": self.ai.max_tokens,
                "timeout": self.ai.timeout
            }
        elif provider == "openai":
            return {
                "api_key": self.ai.openai_api_key,
                "base_url": self.ai.openai_base_url,
                "model": self.ai.default_model,  # 使用环境变量配置的模型
                "temperature": self.ai.temperature,
                "max_tokens": self.ai.max_tokens,
                "timeout": self.ai.timeout
            }
        elif provider == "anthropic":
            return {
                "api_key": self.ai.anthropic_api_key,
                "base_url": self.ai.anthropic_base_url,
                "model": self.ai.default_model,
                "temperature": self.ai.temperature,
                "max_tokens": self.ai.max_tokens,
                "timeout": self.ai.timeout
            }
        elif provider == "ollama":
            return {
                "api_key": "",  # Ollama不需要API Key
                "base_url": self.ai.ollama_base_url,
                "model": self.ai.default_model if self.ai.default_model in self.ai.ollama_models else self.ai.ollama_models[0],
                "temperature": self.ai.temperature,
                "max_tokens": self.ai.max_tokens,
                "timeout": self.ai.timeout,
                "available_models": self.ai.ollama_models
            }
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")
    
    def get_available_models(self, provider: str = None) -> list:
        """获取可用的模型列表"""
        provider = provider or self.ai.default_provider
        
        if provider == "ollama":
            return self.ai.ollama_models
        elif provider == "deepseek":
            return ["deepseek-chat", "deepseek-coder"]
        elif provider == "openai":
            return ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
        else:
            return []
    
    def validate(self) -> bool:
        """验证配置是否完整"""
        errors = []
        
        # 检查AI配置
        if not self.ai.deepseek_api_key and not self.ai.openai_api_key:
            errors.append("至少需要配置一个AI API Key")
        
        # 检查路径
        if not self.paths.data_dir.exists():
            errors.append(f"数据目录不存在: {self.paths.data_dir}")
        
        if errors:
            print("配置验证失败:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True

# 全局配置实例
config = Config()

def get_config() -> Config:
    """获取全局配置实例"""
    return config

def reload_config():
    """重新加载配置"""
    global config
    load_dotenv(override=True)
    config = Config()
    return config