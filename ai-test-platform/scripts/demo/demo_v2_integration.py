"""
Test Agent V2 集成演示
展示V2决策如何驱动 Strategy / Orchestrator / CI
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/agent"

def demo_strategy_engine_integration():
    """演示1: Strategy Engine 集成"""
    print("\n" + "="*60)
    print("📋 演示1: Strategy Engine 集成")
    print("="*60)
    
    # 获取决策
    decision = requests.post(f"{BASE_URL}/analyze", json={
        "requirement": "新增订单退款功能",
        "git_diff": "diff --git a/order/refund.py\n+def process_refund()..."
    }, timeout=30).json()
    
    print(f"\n🤖 AI决策:")
    print(f"  action: {decision['action']}")
    print(f"  confidence: {decision['confidence']}")
    print(f"  priority: {decision['priority']}")
    
    # Strategy Engine 消费决策
    print(f"\n🎯 Strategy Engine 处理:")
    
    if decision['action'] == 'run_tests':
        # 检查置信度
        if decision['confidence'] < 0.7:
            print(f"  ⚠️  低置信度 ({decision['confidence']})，触发人工审核")
            print(f"  📧 已发送审核通知给测试负责人")
        else:
            print(f"  ✅ 高置信度 ({decision['confidence']})，自动执行")
            
            # 创建测试策略
            strategy = {
                'priority': decision['priority'],
                'test_types': decision['test_scope']['types'],
                'case_count': decision['test_scope']['estimated_cases'],
                'parallel': decision['execution_hint']['parallel'],
                'retry': decision['execution_hint']['retry']
            }
            
            print(f"  📝 生成测试策略:")
            print(f"     - 优先级: {strategy['priority']}")
            print(f"     - 测试类型: {strategy['test_types']}")
            print(f"     - 预估用例: {strategy['case_count']}")
            print(f"     - 并行执行: {strategy['parallel']}")
            print(f"     - 重试次数: {strategy['retry']}")
    else:
        print(f"  ⏭️  跳过测试")

def demo_orchestrator_integration():
    """演示2: Orchestrator 集成"""
    print("\n" + "="*60)
    print("📋 演示2: Orchestrator 集成")
    print("="*60)
    
    # 获取决策
    decision = requests.post(f"{BASE_URL}/analyze", json={
        "requirement": "优化商品搜索接口性能",
        "git_diff": "diff --git a/search/api.py\n+@cache\n+def search()..."
    }, timeout=30).json()
    
    print(f"\n🤖 AI决策:")
    print(f"  action: {decision['action']}")
    print(f"  test_scope: {decision['test_scope']}")
    print(f"  execution_hint: {decision['execution_hint']}")
    
    # Orchestrator 编排执行
    print(f"\n🎭 Orchestrator 编排:")
    
    if decision['action'] == 'run_tests':
        scope = decision['test_scope']
        hint = decision['execution_hint']
        
        # 选择执行器
        print(f"  📦 选择执行器:")
        executors = []
        if 'api' in scope['types']:
            executors.append('ApiTestExecutor')
            print(f"     - ApiTestExecutor (接口测试)")
        if 'ui' in scope['types']:
            executors.append('UiTestExecutor')
            print(f"     - UiTestExecutor (UI测试)")
        
        # 配置执行参数
        print(f"\n  ⚙️  执行配置:")
        print(f"     - 并行执行: {hint['parallel']}")
        print(f"     - 重试次数: {hint['retry']}")
        print(f"     - 预估用例: {scope['estimated_cases']}")
        
        # 模拟执行
        print(f"\n  ▶️  开始执行:")
        for executor in executors:
            print(f"     - 启动 {executor}...")
        
        print(f"  ✅ 测试执行完成")

def demo_cicd_integration():
    """演示3: CI/CD Pipeline 集成"""
    print("\n" + "="*60)
    print("📋 演示3: CI/CD Pipeline 集成")
    print("="*60)
    
    # 模拟Git提交
    commit_msg = "fix: 修复用户登录验证码校验bug"
    git_diff = """
diff --git a/auth/login.py b/auth/login.py
@@ -20,7 +20,7 @@ def verify_captcha(code):
-    if code == session.get('captcha'):
+    if code.lower() == session.get('captcha').lower():
         return True
"""
    
    # 获取决策
    decision = requests.post(f"{BASE_URL}/analyze", json={
        "requirement": commit_msg,
        "git_diff": git_diff
    }, timeout=30).json()
    
    print(f"\n🔄 CI/CD Pipeline 流程:")
    print(f"  📝 Commit: {commit_msg}")
    print(f"  🤖 调用 Test Agent 分析...")
    
    print(f"\n  📊 决策结果:")
    print(f"     action: {decision['action']}")
    print(f"     priority: {decision['priority']}")
    print(f"     confidence: {decision['confidence']}")
    
    # CI/CD 执行逻辑
    if decision['action'] == 'run_tests':
        print(f"\n  ▶️  触发测试流程:")
        
        # 根据优先级设置超时
        timeout_map = {'P0': 30, 'P1': 60, 'P2': 120}
        timeout = timeout_map.get(decision['priority'], 60)
        print(f"     - 设置超时: {timeout}分钟")
        
        # 根据test_scope配置测试
        scope = decision['test_scope']
        print(f"     - 测试类型: {scope['types']}")
        print(f"     - 预估用例: {scope['estimated_cases']}")
        
        # 根据execution_hint配置执行
        hint = decision['execution_hint']
        if hint['parallel']:
            print(f"     - 并行执行: pytest -n auto")
        else:
            print(f"     - 串行执行: pytest")
        
        if hint['retry'] > 0:
            print(f"     - 失败重试: --reruns {hint['retry']}")
        
        print(f"\n  ✅ 测试通过，允许合并")
    else:
        print(f"\n  ⏭️  跳过测试，直接合并")

def demo_complete_workflow():
    """演示4: 完整工作流"""
    print("\n" + "="*60)
    print("📋 演示4: 完整工作流（需求→决策→执行）")
    print("="*60)
    
    # 模拟多个需求
    requirements = [
        {
            "name": "核心功能",
            "requirement": "修改支付接口，增加微信支付",
            "git_diff": "diff --git a/payment/wechat.py..."
        },
        {
            "name": "文档更新",
            "requirement": "更新API文档",
            "git_diff": "diff --git a/docs/api.md..."
        },
        {
            "name": "Bug修复",
            "requirement": "修复订单状态更新bug",
            "git_diff": "diff --git a/order/status.py..."
        }
    ]
    
    print(f"\n📦 待分析需求: {len(requirements)}个")
    
    decisions = []
    for req in requirements:
        print(f"\n  分析: {req['name']}")
        decision = requests.post(f"{BASE_URL}/analyze", json={
            "requirement": req['requirement'],
            "git_diff": req['git_diff']
        }, timeout=30).json()
        
        decisions.append({
            'name': req['name'],
            'decision': decision
        })
        
        print(f"    action: {decision['action']}")
        print(f"    priority: {decision['priority']}")
        print(f"    confidence: {decision['confidence']}")
    
    # 按优先级排序
    print(f"\n🎯 执行计划（按优先级排序）:")
    test_queue = [d for d in decisions if d['decision']['action'] == 'run_tests']
    test_queue.sort(key=lambda x: {'P0': 0, 'P1': 1, 'P2': 2}[x['decision']['priority']])
    
    for idx, item in enumerate(test_queue, 1):
        dec = item['decision']
        print(f"\n  {idx}. {item['name']}")
        print(f"     优先级: {dec['priority']}")
        print(f"     测试类型: {dec['test_scope']['types']}")
        print(f"     预估用例: {dec['test_scope']['estimated_cases']}")
        print(f"     并行执行: {dec['execution_hint']['parallel']}")
    
    # 统计
    total_cases = sum(d['decision']['test_scope']['estimated_cases'] for d in test_queue)
    print(f"\n📊 资源规划:")
    print(f"  - 需要测试的需求: {len(test_queue)}/{len(requirements)}")
    print(f"  - 总预估用例数: {total_cases}")
    print(f"  - 建议测试人员: {max(1, total_cases // 20)}")

def main():
    """运行所有演示"""
    print("\n" + "🚀 Test Agent V2 集成演示".center(60, "="))
    
    try:
        # 健康检查
        health = requests.get(f"{BASE_URL}/health", timeout=5).json()
        print(f"\n✅ 服务状态: {health['status']}")
        print(f"   Provider: {health.get('llm_provider', 'N/A')}")
        print(f"   Model: {health['model']}")
        
        # 运行演示
        demo_strategy_engine_integration()
        demo_orchestrator_integration()
        demo_cicd_integration()
        demo_complete_workflow()
        
        # 总结
        print("\n" + "="*60)
        print("✅ Test Agent V2 集成演示完成")
        print("="*60)
        print("\n🎯 V2决策引擎可驱动:")
        print("  1. Strategy Engine - 根据action和confidence制定策略")
        print("  2. Orchestrator - 根据test_scope选择执行器")
        print("  3. CI/CD Pipeline - 根据execution_hint配置执行")
        print("\n📚 详细文档: agent/V2_USAGE.md")
        
    except Exception as e:
        print(f"\n❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
