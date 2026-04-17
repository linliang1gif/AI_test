"""
Error Analyzer - 错误分析器
分析测试失败的错误类型和严重程度
"""
import re
from typing import Dict, Any


def analyze_error(error: str, module: str = "", test_type: str = "") -> Dict[str, Any]:
    """
    分析错误信息
    
    Args:
        error: 错误信息
        module: 模块名称
        test_type: 测试类型
        
    Returns:
        错误分析结果 {
            "type": "assertion/timeout/server_error/connection/unknown",
            "severity": "high/medium/low",
            "fixable": bool,
            "details": str
        }
    """
    error_lower = error.lower()
    
    # 1. 断言错误
    if "assertionerror" in error_lower or "expected" in error_lower:
        return {
            "type": "assertion",
            "severity": "medium",
            "fixable": True,
            "details": "断言失败，可能是期望值不正确或响应格式变化"
        }
    
    # 2. 超时错误
    if "timeout" in error_lower or "timed out" in error_lower:
        return {
            "type": "timeout",
            "severity": "medium",
            "fixable": True,
            "details": "请求超时，可能需要增加等待时间或检查网络"
        }
    
    # 3. 服务器错误
    if "500" in error or "502" in error or "503" in error:
        return {
            "type": "server_error",
            "severity": "high",
            "fixable": True,
            "details": "服务器错误，可以尝试重试或调整请求"
        }
    
    # 4. 连接错误
    if "connection" in error_lower or "refused" in error_lower:
        return {
            "type": "connection",
            "severity": "high",
            "fixable": False,
            "details": "连接失败，需要检查服务是否启动"
        }
    
    # 5. 404 错误
    if "404" in error or "not found" in error_lower:
        return {
            "type": "not_found",
            "severity": "medium",
            "fixable": True,
            "details": "资源不存在，可能是路径错误"
        }
    
    # 6. 401/403 权限错误
    if "401" in error or "403" in error or "unauthorized" in error_lower:
        return {
            "type": "auth_error",
            "severity": "high",
            "fixable": True,
            "details": "认证失败，可能需要更新 token 或权限"
        }
    
    # 7. 默认：未知错误
    return {
        "type": "unknown",
        "severity": "low",
        "fixable": False,
        "details": "未知错误类型，需要人工介入"
    }


def extract_error_context(error: str) -> Dict[str, Any]:
    """
    提取错误上下文信息
    
    Args:
        error: 错误信息
        
    Returns:
        上下文信息
    """
    context = {
        "status_code": None,
        "expected_value": None,
        "actual_value": None,
        "error_message": error
    }
    
    # 提取状态码
    status_match = re.search(r'\b([45]\d{2})\b', error)
    if status_match:
        context["status_code"] = int(status_match.group(1))
    
    # 提取期望值和实际值
    expected_match = re.search(r'expected[:\s]+([^\s,]+)', error, re.IGNORECASE)
    if expected_match:
        context["expected_value"] = expected_match.group(1)
    
    actual_match = re.search(r'(?:but\s+)?(?:got|actual)[:\s]+([^\s,]+)', error, re.IGNORECASE)
    if actual_match:
        context["actual_value"] = actual_match.group(1)
    
    return context


def calculate_fix_confidence(error_type: str, severity: str) -> float:
    """
    计算修复置信度
    
    Args:
        error_type: 错误类型
        severity: 严重程度
        
    Returns:
        修复置信度 (0.0-1.0)
    """
    # 基础置信度
    base_confidence = {
        "assertion": 0.8,
        "timeout": 0.7,
        "server_error": 0.6,
        "not_found": 0.5,
        "auth_error": 0.4,
        "connection": 0.2,
        "unknown": 0.1
    }
    
    confidence = base_confidence.get(error_type, 0.1)
    
    # 根据严重程度调整
    if severity == "low":
        confidence += 0.1
    elif severity == "high":
        confidence -= 0.1
    
    return min(max(confidence, 0.0), 1.0)
