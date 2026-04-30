"""
AI测试控制台集成测试
验证前端页面和后端API的完整集成
"""
import requests
import json
import time


def test_pipeline_api():
    """测试Pipeline API"""
    print("\n" + "="*60)
    print("测试 1: Pipeline API 基础功能")
    print("="*60)
    
    url = "http://localhost:8000/api/pipeline/run"
    
    # 测试数据
    test_data = {
        "requirement": "支付模块需要支持微信支付和支付宝支付",
        "git_diff": "+def wechat_pay():\n+    return process_payment('wechat')",
        "context": {
            "priority": "P0"
        }
    }
    
    print(f"\n📤 发送请求到: {url}")
    print(f"📝 需求: {test_data['requirement']}")
    print(f"🔧 优先级: {test_data['context']['priority']}")
    
    try:
        response = requests.post(url, json=test_data, timeout=30)
        
        print(f"\n📥 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n✅ API调用成功！")
            print(f"\n🔍 Trace ID: {result.get('trace_id', 'N/A')}")
            print(f"⏱️  总耗时: {result.get('total_duration', 0):.2f}s")
            
            # 检查各阶段结果
            print("\n📊 各阶段结果:")
            
            # 1. AI决策
            decision = result.get('decision', {})
            print(f"\n  🤖 AI决策:")
            print(f"     - 是否测试: {decision.get('need_test', False)}")
            print(f"     - 优先级: {decision.get('priority', 'N/A')}")
            print(f"     - 风险等级: {decision.get('risk_level', 'N/A')}")
            print(f"     - 置信度: {decision.get('confidence', 0)*100:.0f}%")
            
            # 2. 测试策略
            strategy = result.get('strategy')
            if strategy:
                print(f"\n  📋 测试策略:")
                strategy_list = strategy.get('strategy', [])
                print(f"     - 模块数量: {len(strategy_list)}")
                for module in strategy_list[:3]:  # 只显示前3个
                    module_info = module.get('module', {})
                    module_name = module_info.get('name') if isinstance(module_info, dict) else module_info
                    print(f"     - {module_name}: {', '.join(module.get('test_types', []))}")
            
            # 3. 执行结果
            execution = result.get('execution')
            if execution:
                summary = execution.get('summary', {})
                print(f"\n  ⚡ 执行结果:")
                print(f"     - 总数: {summary.get('total', 0)}")
                print(f"     - 通过: {summary.get('passed', 0)}")
                print(f"     - 失败: {summary.get('failed', 0)}")
            
            # 4. 自愈过程
            healing = result.get('healing')
            if healing:
                stats = healing.get('statistics', {})
                print(f"\n  🔧 自愈过程:")
                print(f"     - 修复次数: {stats.get('total_healings', 0)}")
                print(f"     - 成功修复: {stats.get('successful_fixes', 0)}")
            
            # 5. 最终报告
            report = result.get('report', {})
            summary = report.get('summary', {})
            print(f"\n  📊 最终报告:")
            print(f"     - 状态: {summary.get('status', 'N/A')}")
            print(f"     - 通过率: {summary.get('pass_rate', 0):.1f}%")
            print(f"     - AI分析: {report.get('ai_analysis', 'N/A')[:50]}...")
            
            # Timeline
            timeline = result.get('timeline', [])
            if timeline:
                print(f"\n  ⏱️  时间线:")
                for step in timeline:
                    print(f"     - {step.get('stage')}: {step.get('duration')}s")
            
            return True
            
        else:
            print(f"\n❌ API调用失败")
            print(f"错误信息: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("\n⏰ 请求超时（30秒）")
        return False
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        return False


def test_frontend_access():
    """测试前端页面访问"""
    print("\n" + "="*60)
    print("测试 2: 前端页面访问")
    print("="*60)
    
    url = "http://localhost:5173"
    
    try:
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            print(f"\n✅ 前端服务正常运行")
            print(f"📍 访问地址: {url}")
            print(f"🎯 AI测试控制台: {url}/ai-test-console")
            return True
        else:
            print(f"\n❌ 前端访问失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ 前端访问失败: {str(e)}")
        return False


def test_backend_health():
    """测试后端健康状态"""
    print("\n" + "="*60)
    print("测试 3: 后端服务健康检查")
    print("="*60)
    
    endpoints = [
        "/api/agent/health",
        "/api/strategy/health",
        "/api/orchestrator/health",
        "/api/healing/health",
        "/api/pipeline/health"
    ]
    
    all_healthy = True
    
    for endpoint in endpoints:
        url = f"http://localhost:8000{endpoint}"
        try:
            response = requests.get(url, timeout=5)
            data = response.json()
            
            status = data.get('status', 'unknown')
            module_name = endpoint.split('/')[2]
            
            if status == 'healthy':
                print(f"  ✅ {module_name.upper()}: 健康")
            else:
                print(f"  ❌ {module_name.upper()}: {status}")
                all_healthy = False
                
        except Exception as e:
            print(f"  ❌ {endpoint}: 无法访问 ({str(e)})")
            all_healthy = False
    
    return all_healthy


def main():
    """主测试流程"""
    print("\n" + "="*60)
    print("🚀 AI测试控制台集成测试")
    print("="*60)
    
    results = []
    
    # 测试1: 后端健康检查
    results.append(("后端健康检查", test_backend_health()))
    
    # 测试2: 前端访问
    results.append(("前端页面访问", test_frontend_access()))
    
    # 测试3: Pipeline API
    results.append(("Pipeline API", test_pipeline_api()))
    
    # 汇总结果
    print("\n" + "="*60)
    print("📊 测试结果汇总")
    print("="*60)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {status} - {name}")
    
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("\n" + "="*60)
        print("🎉 所有测试通过！AI测试控制台已就绪")
        print("="*60)
        print("\n📍 访问地址:")
        print("   前端: http://localhost:5173/ai-test-console")
        print("   后端: http://localhost:8000/docs")
        print("\n💡 使用说明:")
        print("   1. 打开浏览器访问前端地址")
        print("   2. 输入需求描述（必填）")
        print("   3. 可选输入Git Diff")
        print("   4. 选择优先级（P0/P1/P2）")
        print("   5. 点击'Run AI Test'按钮")
        print("   6. 查看实时执行进度和结果")
    else:
        print("\n⚠️ 部分测试失败，请检查服务状态")
    
    return all_passed


if __name__ == "__main__":
    main()
