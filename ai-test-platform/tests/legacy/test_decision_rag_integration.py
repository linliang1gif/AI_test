#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试决策级RAG集成效果
验证Agent/Strategy/CaseGenerator是否正确使用决策级RAG
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def test_agent_integration():
    """测试Agent集成决策级RAG"""
    print("=" * 70)
    print("测试1: Agent Service 集成决策级RAG")
    print("=" * 70)
    
    try:
        from agent.test_agent_service import get_test_agent_service
        
        agent = get_test_agent_service()
        
        # 检查是否有decision_rag属性
        if hasattr(agent, 'decision_rag') and agent.decision_rag:
            print("✅ Agent已集成决策级RAG")
            
            # 测试分析功能
            requirement = "采购订单管理功能优化"
            result = agent.analyze(requirement)
            
            print(f"\n📊 分析结果:")
            print(f"   - 需要测试: {result.get('need_test')}")
            print(f"   - 模块: {result.get('modules')}")
            print(f"   - 优先级: {result.get('priority')}")
            print(f"   - 风险: {result.get('risk_level')}")
            print(f"   - 版本: {result.get('version')}")
            
            # 检查是否有知识库信息
            if 'knowledge' in result:
                print(f"\n🧠 知识库信息:")
                knowledge = result['knowledge']
                print(f"   - APIs: {len(knowledge.get('apis', []))}")
                print(f"   - 模块: {knowledge.get('modules')}")
                print(f"   - 建议优先级: {knowledge.get('priority')}")
                print(f"   - 建议风险: {knowledge.get('risk_level')}")
                print(f"   - 置信度: {knowledge.get('confidence')}")
                print("✅ 知识库信息已正确集成")
            else:
                print("⚠️  结果中未包含知识库信息")
            
            return True
        else:
            print("❌ Agent未集成决策级RAG")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_strategy_integration():
    """测试Strategy Service集成决策级RAG"""
    print("\n" + "=" * 70)
    print("测试2: Strategy Service 集成决策级RAG")
    print("=" * 70)
    
    try:
        # 注意: Strategy Service可能需要单独集成
        # 这里先检查文件是否存在
        strategy_file = Path("strategy/strategy_service.py")
        if not strategy_file.exists():
            print("⚠️  Strategy Service文件不存在，跳过测试")
            return None
        
        print("📝 Strategy Service文件存在")
        print("⚠️  需要手动集成决策级RAG")
        print("   建议: 在__init__中添加 self.decision_rag = get_decision_rag()")
        
        return None
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_case_builder_integration():
    """测试Case Builder集成决策级RAG"""
    print("\n" + "=" * 70)
    print("测试3: Case Builder 集成决策级RAG")
    print("=" * 70)
    
    try:
        # 注意: Case Builder可能需要单独集成
        case_builder_file = Path("case_generator/case_builder.py")
        if not case_builder_file.exists():
            print("⚠️  Case Builder文件不存在，跳过测试")
            return None
        
        print("📝 Case Builder文件存在")
        print("⚠️  需要手动集成决策级RAG")
        print("   建议: 在__init__中添加 self.decision_rag = get_decision_rag()")
        
        return None
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_decision_rag_availability():
    """测试决策级RAG是否可用"""
    print("\n" + "=" * 70)
    print("测试0: 决策级RAG可用性")
    print("=" * 70)
    
    try:
        from knowledge.decision_rag import get_decision_rag
        
        rag = get_decision_rag()
        print("✅ 决策级RAG模块加载成功")
        
        # 测试基本功能
        knowledge = rag.retrieve_knowledge_v2(
            query="采购订单",
            context_type="agent_decision",
            max_tokens=2000
        )
        
        print(f"\n📊 测试检索结果:")
        print(f"   - APIs: {len(knowledge.get('apis', []))}")
        print(f"   - 模块: {knowledge.get('modules')}")
        print(f"   - 优先级: {knowledge.get('priority')}")
        print(f"   - 风险: {knowledge.get('risk_level')}")
        print(f"   - Token: {knowledge.get('token_count')}")
        print(f"   - Fallback: {knowledge.get('fallback')}")
        
        if not knowledge.get('fallback'):
            print("✅ 决策级RAG功能正常")
            return True
        else:
            print("⚠️  决策级RAG使用了fallback")
            return False
            
    except Exception as e:
        print(f"❌ 决策级RAG不可用: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🧪 决策级RAG集成测试")
    print("=" * 70)
    
    results = []
    
    # 测试决策级RAG可用性
    results.append(("决策级RAG可用性", test_decision_rag_availability()))
    
    # 测试各个模块
    results.append(("Agent Service", test_agent_integration()))
    results.append(("Strategy Service", test_strategy_integration()))
    results.append(("Case Builder", test_case_builder_integration()))
    
    # 总结
    print("\n" + "=" * 70)
    print("📊 测试总结")
    print("=" * 70)
    
    success_count = sum(1 for _, result in results if result is True)
    fail_count = sum(1 for _, result in results if result is False)
    skip_count = sum(1 for _, result in results if result is None)
    total_count = len(results)
    
    for name, result in results:
        if result is True:
            status = "✅ 通过"
        elif result is False:
            status = "❌ 失败"
        else:
            status = "⚠️  跳过"
        print(f"{name}: {status}")
    
    print(f"\n总计: {success_count} 通过, {fail_count} 失败, {skip_count} 跳过 (共{total_count}项)")
    
    if success_count > 0:
        print("\n🎉 部分模块已成功集成决策级RAG!")
    
    if fail_count > 0 or skip_count > 0:
        print("\n💡 下一步:")
        print("   1. 手动集成Strategy Service和Case Builder")
        print("   2. 在各模块的__init__中添加: self.decision_rag = get_decision_rag()")
        print("   3. 在生成方法中调用: knowledge = self.decision_rag.retrieve_knowledge_v2(...)")
    
    print("=" * 70)
