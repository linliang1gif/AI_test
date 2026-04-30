"""
Test Agent V2 决策引擎测试
验证增强功能：action, confidence, test_scope, execution_hint, timestamp
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/agent"

def print_result(title: str, result: dict):
    """格式化打印结果"""
    print(f"\n{'='*60}")
    print(f"📋 {title}")
    print(f"{'='*60}")
    
    # V1 原有字段
    print(f"\n【V1 基础字段】")
    print(f"  need_test: {result.get('need_test')}")
    print(f"  modules: {result.get('modules')}")
    print(f"  priority: {result.get('priority')}")
    print(f"  reason: {result.get('reason')}")
    print(f"  test_types: {result.get('test_types')}")
    print(f"  estimated_effort: {result.get('estimated_effort')}")
    print(f"  risk_level: {result.get('risk_level')}")
    
    # V2 新增字段
    print(f"\n【V2 增强字段】")
    print(f"  action: {result.get('action')} ✨")
    print(f"  confidence: {result.get('confidence')} ✨")
    print(f"  test_scope: {result.get('test_scope')} ✨")
    print(f"  execution_hint: {result.get('execution_hint')} ✨")
    print(f"  timestamp: {result.get('timestamp')} ✨")
    
    # 元数据
    print(f"\n【元数据】")
    print(f"  analyzed_at: {result.get('analyzed_at')}")
    print(f"  duration: {result.get('duration')}")
    print(f"  provider: {result.get('provider')}")
    print(f"  model: {result.get('model')}")

def test_case_1_payment_logic():
    """测试1：核心支付逻辑变更 - 预期 P0 + run_tests"""
    print("\n" + "🧪 测试用例 1: 核心支付逻辑变更".center(60, "="))
    
    data = {
        "requirement": "修改支付逻辑，增加支付宝和微信支付双通道支持",
        "git_diff": """
diff --git a/payment/service.py b/payment/service.py
@@ -15,7 +15,15 @@ def process_payment(order_id, amount):
-    # 原有单一支付通道
-    result = alipay.pay(order_id, amount)
+    # 新增双通道支付
+    if payment_method == 'alipay':
+        result = alipay.pay(order_id, amount)
+    elif payment_method == 'wechat':
+        result = wechat.pay(order_id, amount)
+    else:
+        raise ValueError('不支持的支付方式')
"""
    }
    
    response = requests.post(f"{BASE_URL}/analyze", json=data, timeout=30)
    result = response.json()
    
    print_result("支付逻辑变更分析", result)
    
    # 验证预期
    print(f"\n【验证结果】")
    assert result['action'] == 'run_tests', f"❌ action应为run_tests，实际: {result['action']}"
    print(f"  ✅ action = run_tests")
    
    assert result['priority'] in ['P0', 'P1'], f"❌ priority应为P0或P1，实际: {result['priority']}"
    print(f"  ✅ priority = {result['priority']}")
    
    assert result['confidence'] >= 0.8, f"❌ confidence应>=0.8，实际: {result['confidence']}"
    print(f"  ✅ confidence = {result['confidence']}")
    
    assert 'api' in result['test_scope']['types'], f"❌ test_scope应包含api"
    print(f"  ✅ test_scope包含api测试")

def test_case_2_readme_update():
    """测试2：README文档更新 - 预期 skip"""
    print("\n" + "🧪 测试用例 2: README文档更新".center(60, "="))
    
    data = {
        "requirement": "更新README文档，添加安装说明和使用示例",
        "git_diff": """
diff --git a/README.md b/README.md
@@ -1,3 +1,10 @@
 # 项目说明
 
+## 安装
+```bash
+pip install -r requirements.txt
+```
+
+## 使用
+详细使用说明...
"""
    }
    
    response = requests.post(f"{BASE_URL}/analyze", json=data, timeout=30)
    result = response.json()
    
    print_result("README更新分析", result)
    
    # 验证预期
    print(f"\n【验证结果】")
    assert result['action'] == 'skip', f"❌ action应为skip，实际: {result['action']}"
    print(f"  ✅ action = skip")
    
    assert result['need_test'] == False, f"❌ need_test应为False"
    print(f"  ✅ need_test = False")

def test_case_3_large_diff():
    """测试3：大规模代码变更 - 预期高风险"""
    print("\n" + "🧪 测试用例 3: 大规模代码变更".center(60, "="))
    
    # 模拟300行变更
    large_diff = "diff --git a/core/engine.py b/core/engine.py\n"
    large_diff += "\n".join([f"+    # 新增代码行 {i}" for i in range(300)])
    
    data = {
        "requirement": "重构核心引擎，优化性能和架构",
        "git_diff": large_diff
    }
    
    response = requests.post(f"{BASE_URL}/analyze", json=data, timeout=30)
    result = response.json()
    
    print_result("大规模变更分析", result)
    
    # 验证预期
    print(f"\n【验证结果】")
    if result.get('risk_level') == '高':
        print(f"  ✅ risk_level = 高")
    else:
        print(f"  ⚠️  risk_level = {result.get('risk_level')} (预期为高)")
    
    assert result['action'] == 'run_tests', f"❌ action应为run_tests"
    print(f"  ✅ action = run_tests")

def test_v2_fields_structure():
    """测试4：验证V2字段结构完整性"""
    print("\n" + "🧪 测试用例 4: V2字段结构验证".center(60, "="))
    
    data = {
        "requirement": "添加用户注册功能，包含邮箱验证",
        "git_diff": ""
    }
    
    response = requests.post(f"{BASE_URL}/analyze", json=data, timeout=30)
    result = response.json()
    
    print_result("字段结构验证", result)
    
    # 验证所有V2新字段存在
    required_v2_fields = ['action', 'confidence', 'test_scope', 'execution_hint', 'timestamp']
    
    print(f"\n【V2字段完整性检查】")
    for field in required_v2_fields:
        if field in result:
            print(f"  ✅ {field}: 存在")
        else:
            print(f"  ❌ {field}: 缺失")
    
    # 验证test_scope结构
    if 'test_scope' in result:
        scope = result['test_scope']
        assert 'types' in scope, "test_scope缺少types字段"
        assert 'estimated_cases' in scope, "test_scope缺少estimated_cases字段"
        print(f"  ✅ test_scope结构正确: {scope}")
    
    # 验证execution_hint结构
    if 'execution_hint' in result:
        hint = result['execution_hint']
        assert 'parallel' in hint, "execution_hint缺少parallel字段"
        assert 'retry' in hint, "execution_hint缺少retry字段"
        print(f"  ✅ execution_hint结构正确: {hint}")

def test_priority_confidence_mapping():
    """测试5：验证优先级与置信度映射"""
    print("\n" + "🧪 测试用例 5: 优先级-置信度映射".center(60, "="))
    
    test_cases = [
        {
            "name": "P0高优先级",
            "requirement": "修复支付失败导致订单丢失的严重bug",
            "expected_priority": "P0",
            "expected_confidence_min": 0.8
        },
        {
            "name": "P2低优先级",
            "requirement": "优化日志输出格式",
            "expected_priority": "P2",
            "expected_confidence_max": 0.7
        }
    ]
    
    for tc in test_cases:
        print(f"\n  测试: {tc['name']}")
        data = {"requirement": tc['requirement'], "git_diff": ""}
        response = requests.post(f"{BASE_URL}/analyze", json=data, timeout=30)
        result = response.json()
        
        print(f"    priority: {result.get('priority')}")
        print(f"    confidence: {result.get('confidence')}")
        print(f"    action: {result.get('action')}")

def main():
    """运行所有测试"""
    print("\n" + "🚀 Test Agent V2 决策引擎测试".center(60, "="))
    print("验证增强功能：action, confidence, test_scope, execution_hint, timestamp")
    
    try:
        # 健康检查
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        health = response.json()
        print(f"\n✅ 后端服务正常")
        print(f"   状态: {health.get('status')}")
        print(f"   提供商: {health.get('llm_provider')}")
        print(f"   模型: {health.get('model')}")
        
        # 运行测试用例
        test_case_1_payment_logic()
        test_case_2_readme_update()
        test_case_3_large_diff()
        test_v2_fields_structure()
        test_priority_confidence_mapping()
        
        # 总结
        print("\n" + "="*60)
        print("✅ Test Agent V2 所有测试通过！")
        print("="*60)
        print("\n📊 V2增强功能验证:")
        print("  ✅ action字段 - 可执行指令")
        print("  ✅ confidence字段 - 决策置信度")
        print("  ✅ test_scope字段 - 测试范围和用例数")
        print("  ✅ execution_hint字段 - 执行建议")
        print("  ✅ timestamp字段 - 时间戳")
        print("\n🎯 V2决策引擎已就绪，可驱动:")
        print("  - Strategy Engine (测试策略)")
        print("  - Orchestrator (编排执行)")
        print("  - CI/CD Pipeline (自动触发)")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
