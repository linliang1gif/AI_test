"""
Swagger/OpenAPI集成模块
从Swagger规范自动生成高质量测试用例
"""

from .swagger_testcase_generator import SwaggerTestCaseGenerator
from .api_spec_loader import ApiSpecLoader

__all__ = [
    'SwaggerTestCaseGenerator',
    'ApiSpecLoader'
]
