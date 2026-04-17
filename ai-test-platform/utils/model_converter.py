#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模型转换器
在 core 模型和 API 响应格式之间转换
"""

from typing import Dict, Any, List
from datetime import datetime

# 导入 core 模型
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core import (
    TestCase,
    ExecutionResult,
    TestCaseStatus,
    TestCasePriority,
    DataType,
    ExpectedBehavior,
    HealingLevel
)


def testcase_to_dict(tc: TestCase) -> Dict[str, Any]:
    """
    将 TestCase 对象转换为 API 响应格式
    
    Args:
        tc: TestCase 对象
        
    Returns:
        字典格式的测试用例
    """
    return {
        "id": tc.id,
        "title": tc.title,
        "module": tc.module,
        "priority": tc.priority.value,  # 枚举转字符串
        "status": tc.status.value,
        "steps": tc.steps,
        "expected": tc.expected,
        "data_type": tc.data_type.value,  # 🆕 新字段
        "expected_behavior": tc.expected_behavior.value,  # 🆕 新字段
        "execution_config": tc.execution_config,
        "assertions": tc.assertions,
        "tags": tc.tags,
        "created_at": tc.created_at.isoformat() if tc.created_at else None,
        "updated_at": tc.updated_at.isoformat() if tc.updated_at else None,
        "created_by": tc.created_by,
        "test_point_id": tc.test_point_id,
        "api_id": tc.api_id,
        "dataset_id": tc.dataset_id
    }


def dict_to_testcase(data: Dict[str, Any]) -> TestCase:
    """
    将字典转换为 TestCase 对象
    
    Args:
        data: 字典格式的测试用例
        
    Returns:
        TestCase 对象
    """
    from core import create_test_case
    
    return create_test_case(
        id=str(data.get("id", "")),
        title=data.get("title", ""),
        module=data.get("module", ""),
        priority=data.get("priority", "medium"),
        status=data.get("status", "pending"),
        steps=data.get("steps", []),
        expected=data.get("expected", ""),
        data_type=data.get("data_type", "valid"),
        expected_behavior=data.get("expected_behavior", "success"),
        execution_config=data.get("execution_config"),
        assertions=data.get("assertions", []),
        tags=data.get("tags", []),
        created_by=data.get("created_by", "system"),
        test_point_id=data.get("test_point_id"),
        api_id=data.get("api_id"),
        dataset_id=data.get("dataset_id")
    )


def execution_result_to_dict(result: ExecutionResult) -> Dict[str, Any]:
    """
    将 ExecutionResult 对象转换为 API 响应格式
    
    Args:
        result: ExecutionResult 对象
        
    Returns:
        字典格式的执行结果
    """
    return {
        "test_case_id": result.test_case_id,
        "status": result.status.value,
        "duration": result.duration,
        "start_time": result.start_time.isoformat(),
        "end_time": result.end_time.isoformat(),
        "error": result.error,
        "error_type": result.error_type,
        "stack_trace": result.stack_trace,
        "request": result.request,
        "response": result.response,
        "status_code": result.status_code,
        "assertions_passed": result.assertions_passed,
        "assertions_failed": result.assertions_failed,
        "assertion_details": result.assertion_details,
        # 🆕 修复信息
        "healing_applied": result.healing_applied,
        "healing_level": result.healing_level.value if result.healing_level else None,
        "healing_details": result.healing_details
    }


def testcases_to_list(test_cases: List[TestCase]) -> List[Dict[str, Any]]:
    """
    批量转换 TestCase 列表
    
    Args:
        test_cases: TestCase 对象列表
        
    Returns:
        字典列表
    """
    return [testcase_to_dict(tc) for tc in test_cases]


def execution_results_to_list(results: List[ExecutionResult]) -> List[Dict[str, Any]]:
    """
    批量转换 ExecutionResult 列表
    
    Args:
        results: ExecutionResult 对象列表
        
    Returns:
        字典列表
    """
    return [execution_result_to_dict(r) for r in results]


def dict_list_to_testcases(data_list: List[Dict[str, Any]]) -> List[TestCase]:
    """
    批量转换字典列表为 TestCase 对象
    
    Args:
        data_list: 字典列表
        
    Returns:
        TestCase 对象列表
    """
    return [dict_to_testcase(data) for data in data_list]


def enrich_testcase_dict(tc_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    为旧格式的测试用例字典添加新字段（向后兼容）
    
    Args:
        tc_dict: 测试用例字典
        
    Returns:
        增强后的字典
    """
    # 如果已有新字段，直接返回
    if "data_type" in tc_dict and "expected_behavior" in tc_dict:
        return tc_dict
    
    # 根据测试类型推断 data_type
    test_type = tc_dict.get('type', '功能测试')
    title = tc_dict.get('title', '')
    
    if '异常' in test_type or '参数校验' in title or '非法' in title:
        data_type = 'invalid'
    elif '边界' in test_type or '边界' in title or '临界' in title:
        data_type = 'boundary'
    else:
        data_type = 'valid'
    
    # 根据 data_type 推断 expected_behavior
    if data_type == 'invalid':
        expected_behavior = 'client_error'
    else:
        expected_behavior = 'success'
    
    # 添加新字段
    tc_dict['data_type'] = tc_dict.get('data_type', data_type)
    tc_dict['expected_behavior'] = tc_dict.get('expected_behavior', expected_behavior)
    
    return tc_dict


def enrich_testcase_list(tc_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    批量为测试用例列表添加新字段
    
    Args:
        tc_list: 测试用例字典列表
        
    Returns:
        增强后的列表
    """
    return [enrich_testcase_dict(tc) for tc in tc_list]
