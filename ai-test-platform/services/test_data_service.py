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


def build_data_summary(datasets_used: int, missing_vars: List[str], binding_errors: List[str],
                       validation_errors: Optional[List[str]] = None,
                       cleanup_results: Optional[List[dict]] = None) -> dict:
    """构建 data_summary 给 suite_summary"""
    summary = {
        "datasets_used": datasets_used,
        "missing_variables": len(missing_vars),
        "missing_variable_names": missing_vars[:10],
        "data_binding_errors": len(binding_errors),
    }
    if validation_errors is not None:
        summary["data_validation_errors"] = len(validation_errors)
        summary["data_validation_messages"] = validation_errors[:10]
    if cleanup_results is not None:
        summary["cleanup_results"] = cleanup_results[:10]
        summary["cleanup_failed"] = sum(1 for r in cleanup_results if r.get("status") == "failed")
    return summary


def validate_dataset(dataset_id: int, db) -> dict:
    """
    P3-3A: 数据集健康检查
    返回 {valid, warnings, errors, missing_variables, sensitive_fields, suggestions}
    """
    from database.models import TestDataset, TestDatasetItem, TestDataBinding, TestCase
    warnings = []
    errors = []
    missing_variables = []
    sensitive_fields = []
    suggestions = []

    ds = db.query(TestDataset).filter(TestDataset.id == dataset_id).first()
    if not ds:
        return {"valid": False, "errors": ["dataset not found"], "warnings": [], "missing_variables": [], "sensitive_fields": [], "suggestions": []}

    # 1. 数据集是否为空
    items = db.query(TestDatasetItem).filter(TestDatasetItem.dataset_id == dataset_id).all()
    if not items:
        warnings.append("数据集无数据项")
        suggestions.append("请添加至少一个数据项")

    # 2. 数据项是否 enabled
    enabled_items = [i for i in items if i.enabled]
    disabled_count = len(items) - len(enabled_items)
    if disabled_count > 0:
        warnings.append(f"{disabled_count} 个数据项已禁用")

    # 3. 敏感字段未识别
    for item in items:
        if is_sensitive_key(item.key) and not item.is_sensitive:
            sensitive_fields.append(item.key)
            warnings.append(f"字段 '{item.key}' 疑似敏感但未标记 is_sensitive")

    # 4. 已标记敏感字段
    for item in items:
        if item.is_sensitive or is_sensitive_key(item.key):
            if item.key not in sensitive_fields:
                sensitive_fields.append(item.key)

    # 5. account 类型检查
    if ds.dataset_type == "account":
        keys = {i.key.lower() for i in enabled_items}
        if "username" not in keys and "user" not in keys:
            warnings.append("account 类型缺少 username/user 字段")
            suggestions.append("建议添加 username 或 user 数据项")
        if "password" not in keys and "pass" not in keys:
            warnings.append("account 类型缺少 password/pass 字段")
            suggestions.append("建议添加 password 数据项")

    # 6. api_payload 类型检查
    if ds.dataset_type == "api_payload":
        for item in enabled_items:
            if isinstance(item.value_json, str):
                import json as _json
                try:
                    _json.loads(item.value_json)
                except (ValueError, TypeError):
                    pass  # value_json 可以是普通字符串

    # 7. ui_form 类型检查
    if ds.dataset_type == "ui_form":
        if not enabled_items:
            warnings.append("ui_form 类型无可用数据项")

    # 8. performance_pool 数据量检查
    if ds.dataset_type == "performance_pool":
        if len(enabled_items) < 3:
            warnings.append(f"performance_pool 数据量不足: {len(enabled_items)} 项 (建议 ≥ 3)")
            suggestions.append("建议增加更多数据项以支撑性能测试")

    # 9. 绑定的 case_id 是否存在
    bindings = db.query(TestDataBinding).filter(TestDataBinding.dataset_id == dataset_id).all()
    for b in bindings:
        tc = db.query(TestCase).filter(TestCase.id == b.case_id).first()
        if not tc:
            errors.append(f"绑定用例 {b.case_id} 不存在")
        elif getattr(tc, "status", "active") == "deleted":
            errors.append(f"绑定用例 {b.case_id} 已删除")

    valid = len(errors) == 0
    return {
        "valid": valid,
        "warnings": warnings,
        "errors": errors,
        "missing_variables": missing_variables,
        "sensitive_fields": sensitive_fields,
        "suggestions": suggestions,
    }


def validate_case_data(case_id: str, db) -> Tuple[bool, List[str], List[str]]:
    """
    P3-3A: 测试集执行前，校验单个用例的数据绑定
    返回 (is_valid, errors, warnings)
    """
    from database.models import TestDataBinding, TestDataset, TestDatasetItem
    errors = []
    warnings = []

    bindings = db.query(TestDataBinding).filter(TestDataBinding.case_id == case_id).all()
    if not bindings:
        return True, errors, warnings  # 无绑定 = 通过

    for binding in bindings:
        ds = db.query(TestDataset).filter(
            TestDataset.id == binding.dataset_id,
            TestDataset.status == "active"
        ).first()
        if not ds:
            errors.append(f"绑定数据集 {binding.dataset_id} 不存在或已归档")
            continue
        items = db.query(TestDatasetItem).filter(
            TestDatasetItem.dataset_id == ds.id,
            TestDatasetItem.enabled == True
        ).all()
        if not items:
            warnings.append(f"数据集 '{ds.name}' (id={ds.id}) 无启用数据项")
        if ds.dataset_type == "performance_pool" and len(items) < 3:
            warnings.append(f"性能数据池 '{ds.name}' 数据量不足: {len(items)}")

    is_valid = len(errors) == 0
    return is_valid, errors, warnings


CLEANUP_FORBIDDEN_PATTERNS = [
    "baseline", "trace", ".db", ".sqlite", ".env", ".git",
    "data/test_platform", "screenshots", "reports",
]

def execute_cleanup(dataset_id: int, case_id: str, allow_cleanup: bool, db) -> dict:
    """
    P3-3A: 执行 cleanup_rule 类型数据集的清理动作
    MVP: 仅支持 API 清理 (HTTP DELETE/POST)
    """
    import os
    import json as _json
    from database.models import TestDataset, TestDatasetItem

    ds = db.query(TestDataset).filter(TestDataset.id == dataset_id).first()
    if not ds:
        return {"status": "skipped", "reason": "dataset not found"}
    if ds.dataset_type != "cleanup_rule":
        return {"status": "skipped", "reason": f"dataset type is {ds.dataset_type}, not cleanup_rule"}

    items = db.query(TestDatasetItem).filter(
        TestDatasetItem.dataset_id == dataset_id,
        TestDatasetItem.enabled == True
    ).all()

    if not items:
        return {"status": "skipped", "reason": "no cleanup items"}

    # dry-run 模式
    if not allow_cleanup:
        return {
            "status": "dry_run",
            "items_count": len(items),
            "message": "allow_cleanup=false, 清理未执行",
        }

    # real 模式安全拦截
    app_mode = os.getenv("APP_MODE", "mock")
    if app_mode == "real":
        return {
            "status": "blocked",
            "reason": "real 模式下默认拦截清理操作",
        }

    results = []
    for item in items:
        rule = item.value_json
        if not isinstance(rule, dict):
            results.append({"key": item.key, "status": "skipped", "reason": "value_json is not a dict"})
            continue

        method = rule.get("method", "DELETE").upper()
        url = rule.get("url", "")

        # 安全检查: 禁止清理关键路径
        if any(pat in url.lower() for pat in CLEANUP_FORBIDDEN_PATTERNS):
            results.append({"key": item.key, "status": "blocked", "reason": f"url contains forbidden pattern"})
            continue

        # 变量替换
        if case_id:
            variables, _ = resolve_variables(case_id, db)
            if variables:
                url_sub, _, _ = substitute(url, variables)
                url = url_sub

        try:
            import requests
            resp = requests.request(
                method=method,
                url=url if url.startswith("http") else f"http://localhost:8000{url}",
                headers=rule.get("headers", {}),
                json=rule.get("body"),
                timeout=10,
            )
            results.append({
                "key": item.key,
                "status": "success" if resp.status_code < 400 else "failed",
                "http_status": resp.status_code,
                "url": url,
            })
        except Exception as e:
            results.append({"key": item.key, "status": "failed", "error": str(e)[:200]})

    failed_count = sum(1 for r in results if r.get("status") == "failed")
    return {
        "status": "completed",
        "total": len(results),
        "failed": failed_count,
        "results": results,
    }
