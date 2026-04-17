"""
Test Agent V2 快速验证
只验证V2字段存在性和结构，不验证AI判断准确性
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/agent"

def test_v2_fields():
    """验证V2字段完整性"""
    print("="*60)
    print("🧪 Test Agent V2 字段验证")
    print("="*60)
    
    # 测试数据
    data = {
        "requirement": "修改支付逻辑，增加支付宝支持",
        "git_diff": "diff --git a/payment.py\n+    alipay.pay()"
    }
    
    response = requests.post(f"{BASE_URL}/analyze", json=data, timeout=30)
    result = response.json()
    
    print("\n【V1 基础字段】")
    v1_fields = ['need_test', 'modules', 'priority', 'reason', 'test_types', 'estimated_effort', 'risk_level']
    for field in v1_fields:
        value = result.get(field)
        print(f"  ✅ {field}: {value}")
    
    print("\n【V2 增强字段】")
    v2_fields = {
        'action': str,
        'confidence': float,
        'test_scope': dict,
        'execution_hint': dict,
        'timestamp': str
    }
    
    all_passed = True
    for field, expected_type in v2_fields.items():
        if field in result:
            value = result[field]
            if isinstance(value, expected_type):
                print(f"  ✅ {field}: {value} (类型: {type(value).__name__})")
            else:
                print(f"  ❌ {field}: 类型错误，期望{expected_type.__name__}，实际{type(value).__name__}")
                all_passed = False
        else:
            print(f"  ❌ {field}: 缺失")
            all_passed = False
    
    # 验证test_scope结构
    if 'test_scope' in result:
        scope = result['test_scope']
        print(f"\n【test_scope 结构验证】")
        if 'types' in scope and isinstance(scope['types'], list):
            print(f"  ✅ types: {scope['types']}")
        else:
            print(f"  ❌ types字段缺失或类型错误")
            all_passed = False
        
        if 'estimated_cases' in scope and isinstance(scope['estimated_cases'], int):
            print(f"  ✅ estimated_cases: {scope['estimated_cases']}")
        else:
            print(f"  ❌ estimated_cases字段缺失或类型错误")
            all_passed = False
    
    # 验证execution_hint结构
    if 'execution_hint' in result:
        hint = result['execution_hint']
        print(f"\n【execution_hint 结构验证】")
        if 'parallel' in hint and isinstance(hint['parallel'], bool):
            print(f"  ✅ parallel: {hint['parallel']}")
        else:
            print(f"  ❌ parallel字段缺失或类型错误")
            all_passed = False
        
        if 'retry' in hint and isinstance(hint['retry'], int):
            print(f"  ✅ retry: {hint['retry']}")
        else:
            print(f"  ❌ retry字段缺失或类型错误")
            all_passed = False
    
    # 验证action值
    if 'action' in result:
        action = result['action']
        if action in ['run_tests', 'skip']:
            print(f"\n【action 值验证】")
            print(f"  ✅ action值合法: {action}")
        else:
            print(f"\n【action 值验证】")
            print(f"  ❌ action值非法: {action} (应为run_tests或skip)")
            all_passed = False
    
    # 验证confidence范围
    if 'confidence' in result:
        conf = result['confidence']
        if 0 <= conf <= 1:
            print(f"\n【confidence 范围验证】")
            print(f"  ✅ confidence在合理范围: {conf}")
        else:
            print(f"\n【confidence 范围验证】")
            print(f"  ❌ confidence超出范围: {conf} (应在0-1之间)")
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ Test Agent V2 所有字段验证通过！")
        print("="*60)
        print("\n🎯 V2决策引擎已就绪，输出包含:")
        print("  ✅ action - 可执行指令 (run_tests/skip)")
        print("  ✅ confidence - 决策置信度 (0-1)")
        print("  ✅ test_scope - 测试范围 (types + estimated_cases)")
        print("  ✅ execution_hint - 执行建议 (parallel + retry)")
        print("  ✅ timestamp - ISO时间戳")
        print("\n📦 可被以下系统消费:")
        print("  - Strategy Engine (测试策略制定)")
        print("  - Orchestrator (测试编排执行)")
        print("  - CI/CD Pipeline (自动化触发)")
    else:
        print("❌ 部分字段验证失败")
        print("="*60)
    
    return all_passed

if __name__ == "__main__":
    try:
        success = test_v2_fields()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
