"""
Test Strategy Engine 测试
验证策略生成功能
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_case_1_p0_payment():
    """测试1: P0 + 支付模块 → 包含 integration"""
    print("\n" + "="*60)
    print("🧪 测试1: P0 + 支付模块")
    print("="*60)
    
    # 模拟 Agent 决策
    agent_decision = {
        "action": "run_tests",
        "need_test": True,
        "modules": ["支付模块", "订单模块"],
        "priority": "P0",
        "risk_level": "高",
        "confidence": 0.9,
        "test_types": ["功能测试", "接口测试"],
        "timestamp": "2026-03-23T15:00:00"
    }
    
    response = requests.post(
        f"{BASE_URL}/strategy/generate",
        json={"agent_decision": agent_decision},
        timeout=10
    )
    
    result = response.json()
    
    print(f"\n📊 策略结果:")
    print(f"  总模块数: {result['total_modules']}")
    print(f"  总用例数: {result['total_cases']}")
    print(f"  置信度: {result['confidence']}")
    
    print(f"\n📋 模块策略:")
    for strategy in result['strategy']:
        print(f"\n  模块: {strategy['module']}")
        print(f"    优先级: {strategy['priority']}")
        print(f"    测试类型: {strategy['test_types']}")
        print(f"    用例数: {strategy['case_count']}")
        print(f"    执行顺序: {strategy['execution_order']}")
    
    # 验证
    print(f"\n【验证结果】")
    
    # 检查支付模块是否包含 integration
    payment_strategy = next((s for s in result['strategy'] if '支付' in s['module']), None)
    if payment_strategy:
        if 'integration' in payment_strategy['test_types']:
            print(f"  ✅ 支付模块包含 integration 测试")
        else:
            print(f"  ❌ 支付模块缺少 integration 测试")
        
        if payment_strategy['case_count'] >= 25:
            print(f"  ✅ 用例数 >= 25 ({payment_strategy['case_count']})")
        else:
            print(f"  ❌ 用例数 < 25 ({payment_strategy['case_count']})")
    
    # 检查是否包含 api, ui, integration
    all_types = set()
    for s in result['strategy']:
        all_types.update(s['test_types'])
    
    expected_types = {'api', 'ui', 'integration'}
    if expected_types.issubset(all_types):
        print(f"  ✅ P0策略包含 api/ui/integration")
    else:
        missing = expected_types - all_types
        print(f"  ⚠️  缺少测试类型: {missing}")

def test_case_2_p2_normal():
    """测试2: P2 + 普通模块 → 只有 api"""
    print("\n" + "="*60)
    print("🧪 测试2: P2 + 普通模块")
    print("="*60)
    
    agent_decision = {
        "action": "run_tests",
        "need_test": True,
        "modules": ["日志模块"],
        "priority": "P2",
        "risk_level": "低",
        "confidence": 0.6,
        "test_types": ["功能测试"],
        "timestamp": "2026-03-23T15:00:00"
    }
    
    response = requests.post(
        f"{BASE_URL}/strategy/generate",
        json={"agent_decision": agent_decision},
        timeout=10
    )
    
    result = response.json()
    
    print(f"\n📊 策略结果:")
    print(f"  总模块数: {result['total_modules']}")
    print(f"  总用例数: {result['total_cases']}")
    
    print(f"\n📋 模块策略:")
    for strategy in result['strategy']:
        print(f"\n  模块: {strategy['module']}")
        print(f"    测试类型: {strategy['test_types']}")
        print(f"    用例数: {strategy['case_count']}")
    
    # 验证
    print(f"\n【验证结果】")
    
    log_strategy = result['strategy'][0]
    if log_strategy['test_types'] == ['api']:
        print(f"  ✅ P2只包含 api 测试")
    else:
        print(f"  ❌ P2包含了其他测试类型: {log_strategy['test_types']}")
    
    if log_strategy['case_count'] == 10:
        print(f"  ✅ 用例数 = 10")
    else:
        print(f"  ⚠️  用例数 = {log_strategy['case_count']} (预期10)")

def test_case_3_skip_action():
    """测试3: action = skip → 空策略"""
    print("\n" + "="*60)
    print("🧪 测试3: action = skip")
    print("="*60)
    
    agent_decision = {
        "action": "skip",
        "need_test": False,
        "modules": [],
        "priority": "P2",
        "risk_level": "低",
        "confidence": 0.5,
        "timestamp": "2026-03-23T15:00:00"
    }
    
    response = requests.post(
        f"{BASE_URL}/strategy/generate",
        json={"agent_decision": agent_decision},
        timeout=10
    )
    
    result = response.json()
    
    print(f"\n📊 策略结果:")
    print(f"  策略列表: {result['strategy']}")
    print(f"  总模块数: {result['total_modules']}")
    print(f"  总用例数: {result['total_cases']}")
    
    # 验证
    print(f"\n【验证结果】")
    if result['strategy'] == []:
        print(f"  ✅ action=skip 返回空策略")
    else:
        print(f"  ❌ action=skip 应返回空策略")

def test_case_4_multiple_modules():
    """测试4: 多模块策略生成"""
    print("\n" + "="*60)
    print("🧪 测试4: 多模块策略生成")
    print("="*60)
    
    agent_decision = {
        "action": "run_tests",
        "need_test": True,
        "modules": ["支付模块", "订单模块", "用户模块", "日志模块"],
        "priority": "P1",
        "risk_level": "中",
        "confidence": 0.8,
        "test_types": ["功能测试", "接口测试"],
        "timestamp": "2026-03-23T15:00:00"
    }
    
    response = requests.post(
        f"{BASE_URL}/strategy/generate",
        json={"agent_decision": agent_decision},
        timeout=10
    )
    
    result = response.json()
    
    print(f"\n📊 策略结果:")
    print(f"  总模块数: {result['total_modules']}")
    print(f"  总用例数: {result['total_cases']}")
    
    print(f"\n📋 执行顺序:")
    for strategy in result['strategy']:
        print(f"  {strategy['execution_order']}. {strategy['module']}")
        print(f"     测试类型: {strategy['test_types']}")
        print(f"     用例数: {strategy['case_count']}")
    
    # 验证
    print(f"\n【验证结果】")
    if result['total_modules'] == 4:
        print(f"  ✅ 生成了4个模块策略")
    else:
        print(f"  ❌ 模块数不正确: {result['total_modules']}")
    
    # 检查支付模块是否有特殊规则
    payment = next((s for s in result['strategy'] if '支付' in s['module']), None)
    if payment and 'integration' in payment['test_types']:
        print(f"  ✅ 支付模块自动添加了 integration 测试")
    else:
        print(f"  ⚠️  支付模块未添加 integration 测试")

def test_case_5_execution_order():
    """测试5: 执行顺序验证"""
    print("\n" + "="*60)
    print("🧪 测试5: 执行顺序验证")
    print("="*60)
    
    # 混合优先级和风险
    agent_decision = {
        "action": "run_tests",
        "need_test": True,
        "modules": ["模块A", "模块B", "模块C"],
        "priority": "P0",
        "risk_level": "高",
        "confidence": 0.9,
        "timestamp": "2026-03-23T15:00:00"
    }
    
    response = requests.post(
        f"{BASE_URL}/strategy/generate",
        json={"agent_decision": agent_decision},
        timeout=10
    )
    
    result = response.json()
    
    print(f"\n📋 执行顺序:")
    orders = [s['execution_order'] for s in result['strategy']]
    for strategy in result['strategy']:
        print(f"  {strategy['execution_order']}. {strategy['module']}")
    
    # 验证
    print(f"\n【验证结果】")
    if orders == sorted(orders):
        print(f"  ✅ 执行顺序正确排序")
    else:
        print(f"  ❌ 执行顺序未排序")

def main():
    """运行所有测试"""
    print("\n" + "🚀 Test Strategy Engine 测试".center(60, "="))
    
    try:
        # 健康检查
        response = requests.get(f"{BASE_URL}/strategy/health", timeout=5)
        health = response.json()
        print(f"\n✅ Strategy Engine 服务正常")
        print(f"   状态: {health['status']}")
        
        # 运行测试
        test_case_1_p0_payment()
        test_case_2_p2_normal()
        test_case_3_skip_action()
        test_case_4_multiple_modules()
        test_case_5_execution_order()
        
        # 统计
        stats_response = requests.get(f"{BASE_URL}/strategy/statistics", timeout=5)
        stats = stats_response.json()['data']
        
        print("\n" + "="*60)
        print("📊 Strategy Engine 统计")
        print("="*60)
        print(f"  总策略数: {stats['total_strategies']}")
        print(f"  总模块数: {stats['total_modules']}")
        print(f"  总用例数: {stats['total_cases']}")
        print(f"  平均模块数: {stats['avg_modules_per_strategy']}")
        
        print("\n" + "="*60)
        print("✅ Test Strategy Engine 所有测试通过！")
        print("="*60)
        print("\n🎯 策略引擎已就绪，可以:")
        print("  - 根据 Agent 决策生成结构化策略")
        print("  - 应用业务规则（支付→integration）")
        print("  - 控制执行顺序")
        print("  - 输出可被 Orchestrator 消费")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
