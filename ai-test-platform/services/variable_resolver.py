"""
变量替换服务 (Phase 12)

支持在 headers、query_params、body、url 中使用 {{variable_name}} 变量。
执行时从数据集中读取变量值并替换。
"""

import re
import json
from typing import Any, Dict, List, Tuple, Optional

# 敏感字段名（保存时脱敏）
SENSITIVE_FIELDS = {
    'authorization', 'token', 'password', 'secret',
    'access_token', 'refresh_token', 'api_key', 'apikey',
    'x-token', 'x-auth-token', 'cookie',
}

# 变量匹配正则
VARIABLE_PATTERN = re.compile(r'\{\{(\w+)\}\}')


def resolve_variables(
    template_data: Any,
    variables: Dict[str, Any],
) -> Tuple[Any, List[str]]:
    """
    递归替换模板中的 {{variable_name}} 变量。

    Args:
        template_data: 待替换的数据（dict/list/str/其他）
        variables: 变量字典 {"pay_amount": 100.25, "name": "test"}

    Returns:
        (替换后的数据, 缺失变量列表)
    """
    missing = []
    result = _resolve_recursive(template_data, variables, missing)
    # 去重
    missing = list(dict.fromkeys(missing))
    return result, missing


def _resolve_recursive(data: Any, variables: Dict[str, Any], missing: List[str]) -> Any:
    """递归遍历并替换变量"""
    if isinstance(data, str):
        return _resolve_string(data, variables, missing)
    elif isinstance(data, dict):
        return {k: _resolve_recursive(v, variables, missing) for k, v in data.items()}
    elif isinstance(data, list):
        return [_resolve_recursive(item, variables, missing) for item in data]
    else:
        return data


def _resolve_string(text: str, variables: Dict[str, Any], missing: List[str]) -> Any:
    """
    替换字符串中的变量。
    如果整个字符串就是一个变量（如 "{{pay_amount}}"），直接返回原始类型。
    如果是混合字符串（如 "金额:{{amount}}元"），返回替换后的字符串。
    """
    # 检查是否整个字符串就是一个变量
    full_match = re.fullmatch(r'\{\{(\w+)\}\}', text)
    if full_match:
        var_name = full_match.group(1)
        if var_name in variables:
            return variables[var_name]  # 保持原始类型（int/float/bool/None）
        else:
            missing.append(var_name)
            return text  # 保留原样

    # 混合替换
    def replacer(match):
        var_name = match.group(1)
        if var_name in variables:
            return str(variables[var_name])
        else:
            missing.append(var_name)
            return match.group(0)  # 保留 {{xxx}}

    return VARIABLE_PATTERN.sub(replacer, text)


def extract_variables(template_data: Any) -> List[str]:
    """提取模板中所有变量名"""
    variables = []
    _extract_recursive(template_data, variables)
    return list(dict.fromkeys(variables))


def _extract_recursive(data: Any, variables: List[str]):
    if isinstance(data, str):
        for match in VARIABLE_PATTERN.finditer(data):
            variables.append(match.group(1))
    elif isinstance(data, dict):
        for v in data.values():
            _extract_recursive(v, variables)
    elif isinstance(data, list):
        for item in data:
            _extract_recursive(item, variables)


def has_unresolved_variables(data: Any) -> List[str]:
    """检查数据中是否还有未替换的 {{xxx}} 变量"""
    return extract_variables(data)


def sanitize_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """对敏感字段脱敏（用于保存到执行记录）"""
    if not isinstance(data, dict):
        return data
    sanitized = {}
    for k, v in data.items():
        if k.lower() in SENSITIVE_FIELDS:
            if isinstance(v, str) and len(v) > 8:
                sanitized[k] = v[:4] + "****" + v[-4:]
            else:
                sanitized[k] = "****"
        elif isinstance(v, dict):
            sanitized[k] = sanitize_sensitive_data(v)
        else:
            sanitized[k] = v
    return sanitized
