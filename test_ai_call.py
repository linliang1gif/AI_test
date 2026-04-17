#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 AI 调用是否正常工作
"""

import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent / 'ai-test-platform'))

def test_ai_config():
    """测试 AI 配置"""
    print("=" * 60)
    print("测试 1: AI 配置")
    print("=" * 60)
    
    from config.config import get_config
    
    config = get_config()
    print(f"✅ 默认 AI 提供商: {config.ai.default_provider}")
    print(f"✅ 默认 AI 模型: {config.ai.default_model}")
    print(f"✅ Ollama URL: {config.ai.ollama_base_url}")
    print(f"✅ Temperature: {config.ai.temperature}")
    print(f"✅ Max Tokens: {config.ai.max_tokens}")
    
    return True


def test_ai_client():
    """测试 AI 客户端"""
    print("\n" + "=" * 60)
    print("测试 2: AI 客户端调用")
    print("=" * 60)
    
    try:
        from ai.ai_client import AIClient
        
        # 创建客户端
        client = AIClient(provider="ollama")
        print(f"✅ AI 客户端创建成功")
        
        # 测试简单调用
        prompt = "请用一句话介绍什么是软件测试"
        print(f"\n📝 测试提示词: {prompt}")
        print(f"🤖 正在调用 AI...")
        
        response = client.generate_text(
            prompt=prompt,
            system_prompt="你是一个专业的软件测试工程师",
            temperature=0.2,
            max_tokens=100
        )
        
        print(f"\n✅ AI 响应成功!")
        print(f"📄 响应内容:\n{response}")
        
        return True
    except Exception as e:
        print(f"❌ AI 客户端调用失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_testcase_generation():
    """测试测试用例生成"""
    print("\n" + "=" * 60)
    print("测试 3: 测试用例生成（模拟）")
    print("=" * 60)
    
    try:
        from ai.ai_client import AIClient
        import json
        
        client = AIClient(provider="ollama")
        
        # 模拟需求文档
        requirement = """
        用户登录功能需求：
        1. 用户可以使用用户名和密码登录
        2. 登录成功后返回 JWT token
        3. 登录失败返回错误信息
        4. 支持记住密码功能
        """
        
        prompt = f"""请根据以下需求生成2个测试用例:

{requirement}

请以JSON数组格式返回,每个测试用例包含:
- title: 测试用例标题
- module: 所属模块
- priority: 优先级(high/medium/low)
- steps: 测试步骤列表
- expected: 预期结果

示例格式:
[
  {{
    "title": "用户登录-正常场景",
    "module": "用户管理",
    "priority": "high",
    "steps": ["打开登录页面", "输入用户名和密码", "点击登录按钮"],
    "expected": "登录成功,跳转到首页"
  }}
]
"""
        
        print(f"📝 需求文档:\n{requirement}")
        print(f"\n🤖 正在调用 AI 生成测试用例...")
        
        response = client.generate_text(
            prompt=prompt,
            system_prompt="你是一个专业的测试工程师,擅长根据需求生成测试用例",
            temperature=0.3,
            max_tokens=1000
        )
        
        print(f"\n✅ AI 响应成功!")
        print(f"📄 原始响应:\n{response[:500]}...")
        
        # 尝试解析 JSON
        try:
            # 提取 JSON 部分
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0].strip()
            elif '```' in response:
                response = response.split('```')[1].split('```')[0].strip()
            
            testcases = json.loads(response)
            print(f"\n✅ JSON 解析成功!")
            print(f"📊 生成了 {len(testcases)} 个测试用例:")
            
            for i, tc in enumerate(testcases, 1):
                print(f"\n  {i}. {tc.get('title', '未命名')}")
                print(f"     模块: {tc.get('module', '-')}")
                print(f"     优先级: {tc.get('priority', '-')}")
                print(f"     步骤数: {len(tc.get('steps', []))}")
            
            return True
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON 解析失败: {e}")
            print(f"这可能是因为 AI 返回的格式不是标准 JSON")
            return False
            
    except Exception as e:
        print(f"❌ 测试用例生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("AI 调用测试")
    print("=" * 60)
    
    tests = [
        ("AI 配置", test_ai_config),
        ("AI 客户端", test_ai_client),
        ("测试用例生成", test_testcase_generation),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} 测试异常: {e}")
            results.append((name, False))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print("=" * 60)
    print(f"总计: {passed}/{total} 通过")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 所有测试通过！AI 调用正常工作！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
