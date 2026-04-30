#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试httpbin测试失败原因
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core import create_test_case
from modules.executor import ExecutionEngine


def test_httpbin_direct():
    """直接测试httpbin"""
    print("测试httpbin GET请求...")
    
    tc = create_test_case(
        id="TC_DEBUG_001",
        title="Debug GET",
        module="test",
        priority="high",
        steps=[],
        expected="200",
        data_type="valid",
        expected_behavior="success",
        execution_config={
            "method": "GET",
            "url": "https://httpbin.org/get",
            "headers": {"User-Agent": "Test"},
            "params": {"test": "value"}
        },
        assertions=[
            {"type": "status_code", "expected": 200}
        ]
    )
    
    engine = ExecutionEngine()
    result = engine._run_single(tc)
    
    print(f"\n结果:")
    print(f"  状态: {result.status}")
    print(f"  错误: {result.error}")
    print(f"  响应: {result.response}")
    print(f"  状态码: {result.status_code}")
    print(f"  断言通过: {result.assertions_passed}")
    print(f"  断言失败: {result.assertions_failed}")
    print(f"  断言详情: {result.assertion_details}")


if __name__ == '__main__':
    test_httpbin_direct()
