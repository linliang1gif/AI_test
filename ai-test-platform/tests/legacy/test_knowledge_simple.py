#!/usr/bin/env python3
"""简单测试知识库"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from knowledge.decision_rag import get_decision_rag


def test_knowledge():
    print("=" * 60)
    print("🧪 测试知识库")
    print("=" * 60)
    
    # 1. 初始化
    rag = get_decision_rag()
    print(f"✅ 决策级RAG已加载")
    
    # 2. 测试检索
    print(f"\n🔍 测试知识检索...")
    
    test_cases = [
        {
            "query": "采购订单管理",
            "context_type": "agent_decision"
        },
        {
            "query": "用户登录功能",
            "context_type": "case_generation"
        },
        {
            "query": "库存管理系统",
            "context_type": "strategy_planning"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test['query']}")
        print("-" * 60)
        
        try:
            result = rag.retrieve_knowledge_v2(
                query=test['query'],
                context_type=test['context_type']
            )
            
            print(f"✅ 检索成功:")
            print(f"   - APIs: {len(result.get('apis', []))}")
            print(f"   - 模块: {result.get('modules', [])}")
            print(f"   - 优先级: {result.get('priority', 'unknown')}")
            print(f"   - 风险: {result.get('risk_level', 'unknown')}")
            print(f"   - Token: {result.get('token_count', 0)}")
            
            # 显示前3个API
            apis = result.get('apis', [])
            if apis:
                print(f"\n   前3个相关API:")
                for j, api in enumerate(apis[:3], 1):
                    print(f"      {j}. {api.get('method', '')} {api.get('path', '')}")
                    print(f"         {api.get('summary', '')}")
            
        except Exception as e:
            print(f"❌ 检索失败: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n" + "=" * 60)
    print("🎉 测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    test_knowledge()
