"""
快速验证三阶段系统
一键检查所有模块是否正常工作
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))


def verify_imports():
    """验证所有模块可以正常导入"""
    print("\n" + "="*60)
    print("📦 验证模块导入")
    print("="*60)
    
    modules = []
    
    # Test Agent
    try:
        from agent.test_agent_service import get_test_agent_service
        from agent.llm_client import LLMClient
        modules.append(("Test Agent", True))
        print("✅ Test Agent 导入成功")
    except Exception as e:
        modules.append(("Test Agent", False))
        print(f"❌ Test Agent 导入失败: {e}")
    
    # Strategy Engine
    try:
        from strategy.strategy_service import get_strategy_service
        from strategy.rules import apply_strategy_rules
        modules.append(("Strategy Engine", True))
        print("✅ Strategy Engine 导入成功")
    except Exception as e:
        modules.append(("Strategy Engine", False))
        print(f"❌ Strategy Engine 导入失败: {e}")
    
    # Orchestrator
    try:
        from orchestrator.orchestrator_service import get_orchestrator_service
        from orchestrator.base_runner import get_runner
        modules.append(("Orchestrator", True))
        print("✅ Orchestrator 导入成功")
    except Exception as e:
        modules.append(("Orchestrator", False))
        print(f"❌ Orchestrator 导入失败: {e}")
    
    return all(status for _, status in modules)


def verify_services():
    """验证服务实例化"""
    print("\n" + "="*60)
    print("🔧 验证服务实例化")
    print("="*60)
    
    try:
        from agent.test_agent_service import get_test_agent_service
        agent = get_test_agent_service()
        print(f"✅ Test Agent 服务: {type(agent).__name__}")
    except Exception as e:
        print(f"❌ Test Agent 服务失败: {e}")
        return False
    
    try:
        from strategy.strategy_service import get_strategy_service
        strategy = get_strategy_service()
        print(f"✅ Strategy Engine 服务: {type(strategy).__name__}")
    except Exception as e:
        print(f"❌ Strategy Engine 服务失败: {e}")
        return False
    
    try:
        from orchestrator.orchestrator_service import get_orchestrator_service
        orchestrator = get_orchestrator_service()
        print(f"✅ Orchestrator 服务: {type(orchestrator).__name__}")
    except Exception as e:
        print(f"❌ Orchestrator 服务失败: {e}")
        return False
    
    return True


def verify_pipeline():
    """验证完整流程"""
    print("\n" + "="*60)
    print("🔗 验证完整流程")
    print("="*60)
    
    try:
        from agent.test_agent_service import get_test_agent_service
        from strategy.strategy_service import get_strategy_service
        from orchestrator.orchestrator_service import get_orchestrator_service
        
        # 简单测试
        agent = get_test_agent_service()
        strategy = get_strategy_service()
        orchestrator = get_orchestrator_service()
        
        # Agent
        print("\n  🤖 Test Agent...")
        agent_result = agent.analyze("测试需求", "测试diff")
        assert "action" in agent_result
        print(f"     ✅ action: {agent_result['action']}")
        
        # Strategy
        print("\n  📋 Strategy Engine...")
        strategy_result = strategy.generate_strategy(agent_result)
        assert "strategy" in strategy_result
        assert "summary" in strategy_result
        print(f"     ✅ modules: {strategy_result['summary']['total_modules']}")
        
        # Orchestrator
        print("\n  ⚡ Orchestrator...")
        execution_result = orchestrator.run(strategy_result)
        assert "results" in execution_result
        assert "summary" in execution_result
        print(f"     ✅ passed: {execution_result['summary']['passed']}/{execution_result['summary']['total']}")
        
        print("\n✅ 完整流程验证通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 流程验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_api_routes():
    """验证 API 路由注册"""
    print("\n" + "="*60)
    print("🌐 验证 API 路由")
    print("="*60)
    
    try:
        from agent.controller import router as agent_router
        print(f"✅ Agent 路由: {agent_router.prefix}")
    except Exception as e:
        print(f"❌ Agent 路由失败: {e}")
        return False
    
    try:
        from strategy.controller import router as strategy_router
        print(f"✅ Strategy 路由: {strategy_router.prefix}")
    except Exception as e:
        print(f"❌ Strategy 路由失败: {e}")
        return False
    
    try:
        from orchestrator.controller import router as orchestrator_router
        print(f"✅ Orchestrator 路由: {orchestrator_router.prefix}")
    except Exception as e:
        print(f"❌ Orchestrator 路由失败: {e}")
        return False
    
    return True


def main():
    """运行所有验证"""
    print("\n" + "🔍 " + "="*58)
    print("🔍  三阶段系统快速验证")
    print("🔍 " + "="*58)
    
    checks = [
        ("模块导入", verify_imports),
        ("服务实例化", verify_services),
        ("API 路由", verify_api_routes),
        ("完整流程", verify_pipeline)
    ]
    
    results = []
    
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ 验证异常: {name}")
            print(f"   错误: {e}")
            results.append((name, False))
    
    # 总结
    print("\n" + "="*60)
    print("📊 验证总结")
    print("="*60)
    
    passed = sum(1 for _, status in results if status)
    total = len(results)
    
    for name, status in results:
        icon = "✅" if status else "❌"
        print(f"{icon} {name}")
    
    print(f"\n通过: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 所有验证通过！系统就绪。")
        print("\n可以运行:")
        print("  - python demo_three_stage_pipeline.py  (演示)")
        print("  - python backend_api_server.py         (启动后端)")
        return True
    else:
        print(f"\n⚠️  有 {total - passed} 项验证失败")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
