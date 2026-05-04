#!/usr/bin/env python3
"""
P3-2 测试数据服务 — 变量替换引擎 + 敏感数据脱敏
"""
import re
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("test_data_service")

SENSITIVE_KEYS = {"password", "token", "cookie", "authorization", "secret", "api_key", "apikey", "access_token"}


def mask_sensitive(key: str, value) -> str:
    """对敏感 key 的值进行脱敏"""
    if not value:
        return ""
    s = str(value)
    if key.lower() in SENSITIVE_KEYS or any(sk in key.lower() for sk in SENSITIVE_KEYS):
        if len(s) <= 4:
            return "****"
        return s[:2] + "****" + s[-2:]
    return s


def is_sensitive_key(key: str) -> bool:
    k = key.lower()
    return k in SENSITIVE_KEYS or any(sk in k for sk in SENSITIVE_KEYS)


def resolve_variables(case_id: str, db) -> Tuple[Dict[str, any], List[str]]:
    """
    解析用例绑定的数据集，返回 (变量字典, 警告列表)
    优先级: binding sort_order → dataset sort_order → item sort_order
    """
    from database.models import TestDataBinding, TestDataset, TestDatasetItem
    warnings = []
    variables = {}

    bindings = (
        db.query(TestDataBinding)
        .filter(TestDataBinding.case_id == case_id)
        .order_by(TestDataBinding.id)
        .all()
    )

    for binding in bindings:
        dataset = db.query(TestDataset).filter(
            TestDataset.id == binding.dataset_id,
            TestDataset.status == "active"
        ).first()
        if not dataset:
            warnings.append(f"dataset {binding.dataset_id} not found or archived")
            continue
        items = (
            db.query(TestDatasetItem)
            .filter(TestDatasetItem.dataset_id == dataset.id, TestDatasetItem.enabled == True)
            .order_by(TestDatasetItem.sort_order)
            .all()
        )
        for item in items:
            variables[item.key] = item.value_json

    return variables, warnings


def substitute(template, variables: Dict[str, any]) -> Tuple[any, List[str], List[str]]:
    """
    在模板中替换 ${key} 变量。
    返回 (替换后结果, 替换的key列表, 未找到的key列表)
    支持: str, dict, list 递归替换
    """
    replaced = []
    missing = []

    def _sub_str(s: str) -> str:
        def _replacer(m):
            key = m.group(1)
            if key in variables:
                replaced.append(key)
                val = variables[key]
                # 如果整个字符串就是单个变量引用，返回原始类型
                if m.group(0) == s:
                    return str(val) if not isinstance(val, str) else val
                return str(val)
            else:
                missing.append(key)
                return m.group(0)  # 保留原值
        return re.sub(r'\$\{(\w+)\}', _replacer, s)

    def _sub(obj):
        if isinstance(obj, str):
            result = _sub_str(obj)
            # 如果整个字符串就是 ${key} 且值不是字符串，返回原始类型
            if isinstance(obj, str) and re.fullmatch(r'\$\{(\w+)\}', obj):
                key = re.fullmatch(r'\$\{(\w+)\}', obj).group(1)
                if key in variables:
                    return variables[key]
            return result
        elif isinstance(obj, dict):
            return {k: _sub(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_sub(v) for v in obj]
        return obj

    result = _sub(template)
    return result, replaced, missing


def build_data_summary(datasets_used: int, missing_vars: List[str], binding_errors: List[str]) -> dict:
    """构建 data_summary 给 suite_summary"""
    return {
        "datasets_used": datasets_used,
        "missing_variables": len(missing_vars),
        "missing_variable_names": missing_vars[:10],
        "data_binding_errors": len(binding_errors),
    }
