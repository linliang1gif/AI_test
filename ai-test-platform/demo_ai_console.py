"""
AI测试控制台演示脚本
展示三种典型使用场景
"""
import requests
import json
import time


def demo_scenario_1():
    """场景1: P0核心功能 - 支付模块"""
    print("\n" + "="*60)
    print("场景 1: P0核心功能 - 支付模块")
    print("="*60)
    
    data = {
        "requirement": "支付模块需要支持微信支付和支付宝支付，包含支付、退款、查询功能",
        "git_diff": """
+def wechat_pay(order_id, amount):
+    return process_payment('wechat', order_id, amount)
+
+def alipay_pay(order_id, amount):
+    return process_payment('alipay', order_id, amount)
        """.strip(),
        "context": {
            "priority": "P0"
        }
    }
    
    print(f"\n📝 需求: {data['requirement']}")
    print(f"🔧 优先级: P0")
    print(f"📊 预期: 需要测试，高风险，全面覆盖（API+UI+集成）")
    
    return call_pipeline(data)


def demo_scenario_2():
    """场景2: P2一般功能 - 日志查询"""
    print("\n" + "="*60)
    print("场景 2: P2一般功能 - 日志查询")
    print("="*60)
    
    data = {
        "requirement": "添加系统日志查询功能，支持按时间和关键词筛选",
        "git_diff": "+def query_logs(start_time, end_time, keyword):\n+    return db.query_logs(start_time, end_time, keyword)",
        "context": {
            "priority": "P2"
        }
    }
    
    print(f"\n📝 需求: {data['requirement']}")
    print(f"🔧 优先级: P2")
    print(f"📊 预期: 需要测试，低风险，仅API测试")
    
    return call_pipeline(data)


def demo_scenario_3():
    """场景3: 文档修改 - 应该跳过"""
    print("\n" + "="*60)
    print("场景 3: 文档修改 - 应该跳过")
    print("="*60)
    
    data = {
        "requirement": "更新README文档，添加安装说明",
        "git_diff": "+## 安装\n+\n+```bash\n+npm install\n+```",
        "context": {
            "priority": "P2"
        }
    }
    
    print(f"\n📝 需求: {data['requirement']}")
    print(f"🔧 优先级: P2")
    print(f"📊 预期: 跳过测试（仅文档修改）")
    
    return call_pipeline(data)


def call_pipeline(data):
    """调用Pipeline API"""
    url = "http://localhost:8000/api/pipeline/run"
    
    print(f"\n⏳ 执行中...")
    start_time = time.time()
    
    try:
        response = requests.post(url, json=data, timeout=30)
        duration = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n✅ 执行完成 (耗时: {duration:.2f}s)")
            print(f"\n📊 结果:")
            
            # AI决策
            decision = result.get('decision', {})
            print(f"\n  🤖 AI决策:")
            print(f"     - 是否测试: {'✅ 是' if decision.get('need_test') else '⏭️ 否'}")
            print(f"     - 优先级: {decision.get('priority', 'N/A')}")
            print(f"     - 风险等级: {decision.get('risk_level', 'N/A')}")
            print(f"     - 置信度: {decision.get('confidence', 0)*100:.0f}%")
            print(f"     - 建议: {decision.get('action', 'N/A')}")
            
            # 测试策略
            strategy = result.get('strategy')
            if strategy:
                strategy_list = strategy.get('strategy', [])
                print(f"\n  📋 测试策略: {len(strategy_list)} 个模块")
                for module in strategy_list[:2]:
                    module_info = module.get('module', {})
                    module_name = module_info.get('name') if isinstance(module_info, dict) else module_info
                    print(f"     - {module_name}: {', '.join(module.get('test_types', []))}")
            
            # 执行结果
            execution = result.get('execution')
            if execution:
                summary = execution.get('summary', {})
                print(f"\n  ⚡ 执行结果:")
                print(f"     - 通过: {summary.get('passed', 0)}/{summary.get('total', 0)}")
                print(f"     - 失败: {summary.get('failed', 0)}")
            
            # 自愈
            healing = result.get('healing')
            if healing:
                stats = healing.get('statistics', {})
                if stats.get('total_healings', 0) > 0:
                    print(f"\n  🔧 自愈过程:")
                    print(f"     - 修复次数: {stats.get('total_healings', 0)}")
                    print(f"     - 成功修复: {stats.get('successful_fixes', 0)}")
            
            # 最终报告
            report = result.get('report', {})
            summary = report.get('summary', {})
            print(f"\n  📊 最终状态: {summary.get('status', 'N/A').upper()}")
            print(f"  🎯 通过率: {summary.get('pass_rate', 0):.1f}%")
            print(f"\n  🤖 AI分析:")
            print(f"     {report.get('ai_analysis', 'N/A')}")
            
            print(f"\n  🔍 Trace ID: {result.get('trace_id', 'N/A')}")
            
            return True
            
        else:
            print(f"\n❌ 执行失败: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        return False


def main():
    """主演示流程"""
    print("\n" + "="*60)
    print("🚀 AI测试控制台演示")
    print("="*60)
    print("\n本演示将展示三种典型使用场景:")
    print("  1. P0核心功能 - 支付模块（高风险，全面测试）")
    print("  2. P2一般功能 - 日志查询（低风险，仅API测试）")
    print("  3. 文档修改 - README更新（应跳过测试）")
    
    input("\n按Enter键开始演示...")
    
    # 场景1
    result1 = demo_scenario_1()
    input("\n按Enter键继续下一个场景...")
    
    # 场景2
    result2 = demo_scenario_2()
    input("\n按Enter键继续下一个场景...")
    
    # 场景3
    result3 = demo_scenario_3()
    
    # 总结
    print("\n" + "="*60)
    print("📊 演示总结")
    print("="*60)
    
    scenarios = [
        ("P0核心功能", result1),
        ("P2一般功能", result2),
        ("文档修改", result3)
    ]
    
    for name, passed in scenarios:
        status = "✅" if passed else "❌"
        print(f"  {status} {name}")
    
    if all(r[1] for r in scenarios):
        print("\n🎉 所有场景演示成功！")
        print("\n💡 现在可以打开浏览器体验Web界面:")
        print("   http://localhost:5173/ai-test-console")
    else:
        print("\n⚠️ 部分场景失败，请检查服务状态")


if __name__ == "__main__":
    main()
