#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试Mock模式是否正常工作
"""

from ai.ai_client import get_ai_client
from config.config import get_config

def test_mock_mode():
    """测试Mock模式"""
    print("=" * 60)
    print("测试Mock模式")
    print("=" * 60)
    
    # 获取配置
    config = get_config()
    print(f"\n当前AI提供商: {config.ai.default_provider}")
    print(f"当前AI模型: {config.ai.default_model}")
    
    # 获取AI客户端
    ai_client = get_ai_client()
    print(f"\nAI客户端类型: {type(ai_client).__name__}")
    
    # 测试文本生成
    print("\n1. 测试文本生成...")
    try:
        response = ai_client.generate_text("你好")
        print(f"✅ 文本生成成功: {response[:100]}...")
    except Exception as e:
        print(f"❌ 文本生成失败: {e}")
        return False
    
    # 测试JSON生成
    print("\n2. 测试JSON生成...")
    try:
        response = ai_client.generate_json("生成一个测试模块")
        print(f"✅ JSON生成成功")
        print(f"   返回类型: {type(response)}")
        print(f"   包含键: {list(response.keys())}")
    except Exception as e:
        print(f"❌ JSON生成失败: {e}")
        return False
    
    # 测试场景生成
    print("\n3. 测试场景生成...")
    try:
        from test_design.scenario_matrix_generator import ScenarioMatrixGenerator
        
        # 模拟测试点
        testpoints = {
            "测试模块": [
                {
                    "id": "tp_001",
                    "name": "用户登录",
                    "category": "功能测试",
                    "description": "验证用户登录功能",
                    "priority": "高"
                }
            ]
        }
        
        generator = ScenarioMatrixGenerator()
        scenarios = generator.generate_scenario_matrix(testpoints)
        
        total_scenarios = sum(len(s) for s in scenarios.values())
        print(f"✅ 场景生成成功: {total_scenarios} 个场景")
        
        # 显示第一个场景
        if scenarios and list(scenarios.values())[0]:
            first_scenario = list(scenarios.values())[0][0]
            print(f"\n示例场景:")
            print(f"  名称: {first_scenario['name']}")
            print(f"  输入数据: {first_scenario['input_data']}")
            print(f"  用户状态: {first_scenario['user_state']}")
            
    except Exception as e:
        print(f"❌ 场景生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("✅ Mock模式测试全部通过!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    test_mock_mode()
