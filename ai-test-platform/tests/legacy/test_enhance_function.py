"""
直接测试 enhance_decision 函数
"""
import sys
sys.path.insert(0, '.')

from agent.test_agent_service import enhance_decision

# 测试数据
test_result = {
    "need_test": True,
    "modules": ["支付模块"],
    "priority": "P0",
    "reason": "核心支付逻辑变更",
    "test_types": ["功能测试", "接口测试"],
    "estimated_effort": "2小时",
    "risk_level": "高"
}

print("原始结果:")
print(test_result)

# 调用增强函数
enhanced = enhance_decision(test_result)

print("\n增强后结果:")
for key, value in enhanced.items():
    print(f"  {key}: {value}")

# 验证新字段
print("\n验证V2字段:")
v2_fields = ['action', 'confidence', 'test_scope', 'execution_hint', 'timestamp']
for field in v2_fields:
    if field in enhanced:
        print(f"  ✅ {field}: {enhanced[field]}")
    else:
        print(f"  ❌ {field}: 缺失")
