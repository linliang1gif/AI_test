#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 OpenRouter API 密钥
"""

import requests
import json

def test_openrouter_api():
    """测试 OpenRouter API"""
    
    api_key = "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"
    base_url = "https://openrouter.ai/api/v1"
    
    print("=" * 60)
    print("测试 OpenRouter API")
    print("=" * 60)
    
    # 测试 1: 获取可用模型列表
    print("\n测试 1: 获取可用模型")
    print("-" * 60)
    
    try:
        response = requests.get(
            f"{base_url}/models",
            headers={
                "Authorization": f"Bearer {api_key}",
            },
            timeout=10
        )
        
        if response.status_code == 200:
            models = response.json()
            print(f"✅ 成功获取模型列表")
            print(f"📊 可用模型数量: {len(models.get('data', []))}")
            
            # 显示前 5 个模型
            print("\n前 5 个可用模型:")
            for i, model in enumerate(models.get('data', [])[:5], 1):
                model_id = model.get('id', 'unknown')
                print(f"  {i}. {model_id}")
        else:
            print(f"❌ 获取模型列表失败: {response.status_code}")
            print(f"响应: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False
    
    # 测试 2: 简单的文本生成
    print("\n\n测试 2: 文本生成")
    print("-" * 60)
    
    try:
        payload = {
            "model": "google/gemma-4-26b-a4b-it:free",  # 使用免费的 Gemma 模型
            "messages": [
                {
                    "role": "user",
                    "content": "请用一句话介绍什么是软件测试"
                }
            ],
            "temperature": 0.2,
            "max_tokens": 100
        }
        
        print(f"🤖 使用模型: {payload['model']}")
        print(f"📝 提示词: {payload['messages'][0]['content']}")
        print(f"⏳ 正在调用 API...")
        
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            print(f"\n✅ API 调用成功!")
            print(f"📄 AI 响应:\n{content}")
            
            # 显示使用情况
            usage = result.get('usage', {})
            if usage:
                print(f"\n📊 Token 使用:")
                print(f"  - 输入: {usage.get('prompt_tokens', 0)}")
                print(f"  - 输出: {usage.get('completion_tokens', 0)}")
                print(f"  - 总计: {usage.get('total_tokens', 0)}")
            
            return True
        else:
            print(f"❌ API 调用失败: {response.status_code}")
            print(f"响应: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_with_ai_client():
    """使用项目的 AI 客户端测试"""
    print("\n\n" + "=" * 60)
    print("测试 3: 使用项目 AI 客户端")
    print("=" * 60)
    
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent / 'ai-test-platform'))
    
    try:
        from ai.ai_client import AIClient
        
        # 创建客户端（使用 openai 提供商，因为 OpenRouter 兼容 OpenAI API）
        client = AIClient(provider="openai")
        
        print(f"✅ AI 客户端创建成功")
        print(f"📝 提示词: 请用一句话介绍什么是自动化测试")
        print(f"🤖 正在调用 AI...")
        
        response = client.generate_text(
            prompt="请用一句话介绍什么是自动化测试",
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


if __name__ == "__main__":
    print("\n🚀 OpenRouter API 密钥测试\n")
    
    # 测试原始 API
    result1 = test_openrouter_api()
    
    # 测试项目集成
    result2 = test_with_ai_client()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)
    print(f"{'✅' if result1 else '❌'} OpenRouter API 直接调用")
    print(f"{'✅' if result2 else '❌'} 项目 AI 客户端集成")
    print("=" * 60)
    
    if result1 and result2:
        print("\n🎉 所有测试通过！API 密钥可以正常使用！")
        print("\n💡 建议:")
        print("  1. 已将配置更新到 .env 文件")
        print("  2. 重启后端服务以应用新配置")
        print("  3. 现在可以使用 AI 生成测试用例了")
    else:
        print("\n⚠️  部分测试失败，请检查:")
        print("  1. API 密钥是否有效")
        print("  2. 网络连接是否正常")
        print("  3. OpenRouter 账户是否有余额")
