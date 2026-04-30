#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试知识库集成效果
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def test_case_builder_integration():
    """测试Case Builder集成"""
    print("=" * 60)
    print("测试 Case Builder 知识库集成")
    print("=" * 60)
    
    try:
        from case_generator.case_builder import CaseBuilder
        
        builder = CaseBuilder()
        
        # 测试是否有helper属性
        if hasattr(builder, 'helper'):
            print("✅ Case Builder 已集成知识库")
            
            # 测试搜索API
            apis = builder.helper.search_related_apis("采购订单", top_k=3)
            print(f"✅ 搜索API功能正常,找到 {len(apis)} 个相关API")
            
            for i, api in enumerate(apis, 1):
                print(f"   {i}. {api['method']} {api['path']}")
            
            return True
        else:
            print("❌ Case Builder 未集成知识库")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_scenario_builder_integration():
    """测试Scenario Builder集成"""
    print("\n" + "=" * 60)
    print("测试 Scenario Builder 知识库集成")
    print("=" * 60)
    
    try:
        from case_generator.scenario_builder import ScenarioBuilder
        
        builder = ScenarioBuilder()
        
        if hasattr(builder, 'helper'):
            print("✅ Scenario Builder 已集成知识库")
            
            # 测试搜索代码
            code = builder.helper.search_related_code("PurchaseOrder", "backend", top_k=2)
            print(f"✅ 搜索代码功能正常,找到 {len(code)} 个相关文件")
            
            for i, file in enumerate(code, 1):
                print(f"   {i}. {file['filename']}")
            
            return True
        else:
            print("❌ Scenario Builder 未集成知识库")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_strategy_service_integration():
    """测试Strategy Service集成"""
    print("\n" + "=" * 60)
    print("测试 Strategy Service 知识库集成")
    print("=" * 60)
    
    try:
        from strategy.strategy_service import StrategyService
        
        service = StrategyService()
        
        if hasattr(service, 'helper'):
            print("✅ Strategy Service 已集成知识库")
            
            # 测试完整知识增强
            prompt = "生成采购订单测试策略"
            enhanced = service.helper.enhance_prompt_with_api_knowledge(
                prompt, "采购订单", top_k=3
            )
            
            print(f"✅ Prompt增强功能正常")
            print(f"   原始长度: {len(prompt)}")
            print(f"   增强后长度: {len(enhanced)}")
            
            return True
        else:
            print("❌ Strategy Service 未集成知识库")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🧪 知识库集成测试")
    print("=" * 60)
    
    results = []
    
    # 测试各个模块
    results.append(("Case Builder", test_case_builder_integration()))
    results.append(("Scenario Builder", test_scenario_builder_integration()))
    results.append(("Strategy Service", test_strategy_service_integration()))
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    
    success_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    print(f"\n总计: {success_count}/{total_count} 通过")
    
    if success_count == total_count:
        print("\n🎉 所有测试通过!知识库集成成功!")
    else:
        print("\n⚠️ 部分测试失败,请检查集成")
    
    print("=" * 60)
