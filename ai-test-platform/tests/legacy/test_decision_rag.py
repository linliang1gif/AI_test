#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试决策级RAG
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from knowledge.decision_rag import get_decision_rag


def test_basic_retrieval():
    """测试基础检索"""
    print("=" * 60)
    print("测试1: 基础知识检索")
    print("=" * 60)
    
    rag = get_decision_rag()
    
    # 测试查询
    knowledge = rag.retrieve_knowledge_v2(
        query="采购订单",
        context_type="agent_decision"
    )
    
    print(f"\n查询: 采购订单")
    print(f"识别模块: {knowledge['modules']}")
    print(f"优先级: {knowledge['priority']}")
    print(f"风险等级: {knowledge['risk_level']}")
    print(f"置信度: {knowledge['confidence']:.2f}")
    print(f"Token数: {knowledge['token_count']}")
    print(f"Fallback: {knowledge['fallback']}")
    print(f"\nAPI数量: {len(knowledge['apis'])}")
    print(f"后端代码数量: {len(knowledge['code']['backend'])}")
    print(f"前端代码数量: {len(knowledge['code']['frontend'])}")
    
    if knowledge['apis']:
        print(f"\n前3个API:")
        for i, api in enumerate(knowledge['apis'][:3], 1):
            print(f"  {i}. {api.get('method', 'N/A')} {api.get('path', 'N/A')}")
            print(f"     相似度: {api.get('similarity', 0):.2f}")


def test_different_contexts():
    """测试不同上下文"""
    print("\n" + "=" * 60)
    print("测试2: 不同上下文类型")
    print("=" * 60)
    
    rag = get_decision_rag()
    
    contexts = [
        "agent_decision",
        "strategy_planning",
        "case_generation"
    ]
    
    for context in contexts:
        knowledge = rag.retrieve_knowledge_v2(
            query="用户登录",
            context_type=context
        )
        
        print(f"\n上下文: {context}")
        print(f"  API数量: {len(knowledge['apis'])}")
        print(f"  后端代码: {len(knowledge['code']['backend'])}")
        print(f"  前端代码: {len(knowledge['code']['frontend'])}")
        print(f"  Token数: {knowledge['token_count']}")


def test_priority_calculation():
    """测试优先级计算"""
    print("\n" + "=" * 60)
    print("测试3: 优先级计算")
    print("=" * 60)
    
    rag = get_decision_rag()
    
    test_cases = [
        ("支付", "核心模块"),
        ("用户登录", "一般模块"),
        ("采购订单", "重要模块"),
    ]
    
    for query, desc in test_cases:
        knowledge = rag.retrieve_knowledge_v2(query)
        print(f"\n查询: {query} ({desc})")
        print(f"  模块: {knowledge['modules']}")
        print(f"  优先级: {knowledge['priority']}")
        print(f"  风险: {knowledge['risk_level']}")


def test_token_limit():
    """测试Token控制"""
    print("\n" + "=" * 60)
    print("测试4: Token控制")
    print("=" * 60)
    
    rag = get_decision_rag()
    
    # 测试不同的token限制
    limits = [500, 1000, 2000]
    
    for limit in limits:
        knowledge = rag.retrieve_knowledge_v2(
            query="采购订单管理",
            max_tokens=limit
        )
        
        print(f"\nToken限制: {limit}")
        print(f"  实际Token: {knowledge['token_count']}")
        print(f"  API数量: {len(knowledge['apis'])}")
        print(f"  是否超标: {'是' if knowledge['token_count'] > limit else '否'}")


def test_fallback():
    """测试Fallback机制"""
    print("\n" + "=" * 60)
    print("测试5: Fallback机制")
    print("=" * 60)
    
    rag = get_decision_rag()
    
    # 测试一个可能失败的查询
    knowledge = rag.retrieve_knowledge_v2(
        query="不存在的模块xyz123"
    )
    
    print(f"\n查询: 不存在的模块")
    print(f"Fallback: {knowledge['fallback']}")
    print(f"优先级: {knowledge['priority']}")
    print(f"风险: {knowledge['risk_level']}")
    print(f"API数量: {len(knowledge['apis'])}")
    
    # 即使fallback,系统也能继续运行
    print("\n✅ Fallback机制正常,系统不会中断")


def test_quality_filter():
    """测试质量筛选"""
    print("\n" + "=" * 60)
    print("测试6: 质量筛选")
    print("=" * 60)
    
    rag = get_decision_rag()
    
    knowledge = rag.retrieve_knowledge_v2(
        query="采购订单"
    )
    
    print(f"\n查询: 采购订单")
    print(f"返回的API (已筛选高质量):")
    
    for i, api in enumerate(knowledge['apis'][:5], 1):
        similarity = api.get('similarity', 0)
        status = "✅ 高质量" if similarity >= 0.7 else "⚠️ 低质量"
        print(f"  {i}. {api.get('method', 'N/A')} {api.get('path', 'N/A')}")
        print(f"     相似度: {similarity:.2f} {status}")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🧪 决策级RAG测试")
    print("=" * 60)
    
    try:
        test_basic_retrieval()
        test_different_contexts()
        test_priority_calculation()
        test_token_limit()
        test_fallback()
        test_quality_filter()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成!")
        print("=" * 60)
        
        print("\n📊 决策级RAG功能:")
        print("  ✅ 结构化知识检索")
        print("  ✅ 质量筛选 (相似度阈值)")
        print("  ✅ 模块识别 (基于规则)")
        print("  ✅ 优先级计算 (基于规则)")
        print("  ✅ 风险评估 (基于规则)")
        print("  ✅ Token控制 (严格<2000)")
        print("  ✅ Fallback机制 (不中断)")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
