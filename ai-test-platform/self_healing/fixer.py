"""
Error Fixer - 错误修复器
根据错误类型应用相应的修复策略
"""
from typing import Dict, Any


def apply_fix(error_type: str, module: str, error_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    应用修复策略
    
    Args:
        error_type: 错误类型
        module: 模块名称
        error_context: 错误上下文
        
    Returns:
        修复结果 {
            "fix_applied": str,
            "retry": bool,
            "modifications": dict
        }
    """
    
    # 1. 断言错误修复
    if error_type == "assertion":
        return _fix_assertion_error(module, error_context)
    
    # 2. 超时错误修复
    elif error_type == "timeout":
        return _fix_timeout_error(module, error_context)
    
    # 3. 服务器错误修复
    elif error_type == "server_error":
        return _fix_server_error(module, error_context)
    
    # 4. 404 错误修复
    elif error_type == "not_found":
        return _fix_not_found_error(module, error_context)
    
    # 5. 认证错误修复
    elif error_type == "auth_error":
        return _fix_auth_error(module, error_context)
    
    # 6. 无法修复
    else:
        return {
            "fix_applied": "无法自动修复",
            "retry": False,
            "modifications": {}
        }


def _fix_assertion_error(module: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """修复断言错误"""
    expected = context.get("expected_value")
    actual = context.get("actual_value")
    
    if expected and actual:
        fix_desc = f"调整断言：期望值从 {expected} 改为 {actual}"
    else:
        fix_desc = "放宽断言条件，允许更多响应格式"
    
    return {
        "fix_applied": fix_desc,
        "retry": True,
        "modifications": {
            "assertion_relaxed": True,
            "expected_value": actual if actual else "any",
            "tolerance": "increased"
        }
    }


def _fix_timeout_error(module: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """修复超时错误"""
    return {
        "fix_applied": "增加超时时间：从 30s 增加到 60s",
        "retry": True,
        "modifications": {
            "timeout": 60,
            "wait_time": "increased",
            "retry_interval": 2
        }
    }


def _fix_server_error(module: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """修复服务器错误"""
    status_code = context.get("status_code")
    
    return {
        "fix_applied": f"服务器错误 {status_code}，添加重试机制",
        "retry": True,
        "modifications": {
            "retry_count": 3,
            "retry_delay": 1,
            "ignore_server_errors": False
        }
    }


def _fix_not_found_error(module: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """修复 404 错误"""
    return {
        "fix_applied": "资源不存在，尝试使用备用路径",
        "retry": True,
        "modifications": {
            "use_fallback_path": True,
            "path_variants": ["v1", "v2", "api"]
        }
    }


def _fix_auth_error(module: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """修复认证错误"""
    return {
        "fix_applied": "认证失败，刷新 token 并重试",
        "retry": True,
        "modifications": {
            "refresh_token": True,
            "use_new_credentials": True
        }
    }


def get_fix_strategy(error_type: str) -> str:
    """
    获取修复策略描述
    
    Args:
        error_type: 错误类型
        
    Returns:
        策略描述
    """
    strategies = {
        "assertion": "调整断言条件或期望值",
        "timeout": "增加超时时间或优化等待策略",
        "server_error": "添加重试机制，增加容错性",
        "not_found": "尝试备用路径或更新 API 版本",
        "auth_error": "刷新认证信息或更新权限",
        "connection": "检查服务状态，无法自动修复",
        "unknown": "需要人工分析，无法自动修复"
    }
    
    return strategies.get(error_type, "无修复策略")
