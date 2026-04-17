"""
Strategy Rules Engine - 策略规则引擎
定义测试策略生成规则
"""
from typing import Dict, List, Any


def apply_strategy_rules(module: str, priority: str, risk_level: str = "中") -> Dict[str, Any]:
    """
    应用策略规则
    
    Args:
        module: 模块名称
        priority: 优先级 (P0/P1/P2)
        risk_level: 风险等级 (高/中/低)
        
    Returns:
        策略规则字典
    """
    # 1. 根据优先级决定测试类型
    test_types = get_test_types_by_priority(priority)
    
    # 2. 根据风险等级决定用例数
    case_count = get_case_count_by_risk(risk_level, priority)
    
    # 3. 特殊模块规则
    test_types = apply_module_specific_rules(module, test_types)
    
    # 4. 风险等级规则
    case_count = apply_risk_rules(risk_level, case_count)
    
    # 5. 优先级规则
    if priority == "P2":
        # P2只保留api测试
        test_types = ["api"]
    
    return {
        "test_types": test_types,
        "case_count": case_count
    }


def get_test_types_by_priority(priority: str) -> List[str]:
    """
    根据优先级决定测试类型
    
    规则：
    - P0: api + ui + integration
    - P1: api + ui
    - P2: api
    """
    priority_map = {
        "P0": ["api", "ui", "integration"],
        "P1": ["api", "ui"],
        "P2": ["api"]
    }
    return priority_map.get(priority, ["api"])


def get_case_count_by_risk(risk_level: str, priority: str) -> int:
    """
    根据风险等级和优先级决定用例数
    
    规则：
    - 高风险: 30
    - 中风险: 20
    - 低风险: 10
    """
    # 基础用例数
    risk_map = {
        "高": 30,
        "中": 20,
        "低": 10
    }
    base_count = risk_map.get(risk_level, 20)
    
    # 优先级调整
    priority_multiplier = {
        "P0": 1.0,
        "P1": 0.8,
        "P2": 0.5
    }
    multiplier = priority_multiplier.get(priority, 1.0)
    
    return max(10, int(base_count * multiplier))


def apply_module_specific_rules(module: str, test_types: List[str]) -> List[str]:
    """
    应用模块特定规则
    
    规则：
    1. 支付模块 → 强制添加 integration 测试
    2. 登录/认证模块 → 强制添加 security 测试
    3. 数据库模块 → 强制添加 data 测试
    """
    module_lower = module.lower()
    
    # 支付模块规则
    if any(keyword in module_lower for keyword in ["支付", "payment", "pay"]):
        if "integration" not in test_types:
            test_types.append("integration")
    
    # 认证模块规则
    if any(keyword in module_lower for keyword in ["登录", "认证", "授权", "auth", "login"]):
        if "security" not in test_types:
            test_types.append("security")
    
    # 数据库模块规则
    if any(keyword in module_lower for keyword in ["数据库", "database", "db", "存储", "storage"]):
        if "data" not in test_types:
            test_types.append("data")
    
    return test_types


def apply_risk_rules(risk_level: str, case_count: int) -> int:
    """
    应用风险规则
    
    规则：
    - 高风险 → case_count >= 25
    - 中风险 → case_count >= 15
    - 低风险 → case_count >= 10
    """
    min_cases = {
        "高": 25,
        "中": 15,
        "低": 10
    }
    
    min_count = min_cases.get(risk_level, 15)
    return max(case_count, min_count)


def calculate_execution_order(priority: str, risk_level: str) -> int:
    """
    计算执行顺序
    
    规则：
    - P0 + 高风险 → 1
    - P0 + 中风险 → 2
    - P1 + 高风险 → 3
    - P1 + 中风险 → 4
    - P2 → 5+
    """
    priority_score = {"P0": 0, "P1": 10, "P2": 20}.get(priority, 10)
    risk_score = {"高": 0, "中": 1, "低": 2}.get(risk_level, 1)
    
    return priority_score + risk_score + 1
