#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 OpenRouter 免费模型
"""

import requests
import json

def test_free_models():
    """测试多个免费模型"""
    
    api_key = "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"
    base_url = "https://openrouter.ai/api/v1"
    
    # 常见的免费模型列表
    free_models = [
        "meta-llama/llama-3.2-3b-instruct:free",
        "meta-llama/llama-3.2-1b-instruct:free",
        "google/gemma-2-9b-it:free",
        "mistralai/mistral-7b-instruct:free",
        "nousresearch/hermes-3-llama-3.1-405b:free",
        "qwen/qwen-2-7b-instruct:free",
    ]
    
    print("=" * 60)
    print("测试 OpenRouter 免费模型")
    print("=" * 60)
    
    test_prompt = "请用一句话介绍什么是软件测试"
    
    for model in free_models:
        print(f"\n测试模型: {model}")
        print("-" * 60)
        
        try:
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": test_prompt
                    }
                ],
                "temperature": 0.2,
                "max_tokens": 100
            }
            
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
                
                print(f"✅ 成功!")
                print(f"📄 响应: {content[:200]}...")
                
                # 显示使用情况
                usage = result.get('usage', {})
                if usage:
                    print(f"📊 Tokens: {usage.get('total_tokens', 0)}")
                
                # 找到可用模型就返回
                return model, content
                
            else:
                print(f"❌ 失败: {response.status_code}")
                error_msg = response.json().get('error', {}).get('message', '')
                if error_msg:
                    print(f"   错误: {error_msg[:100]}")
                    
        except Exception as e:
            print(f"❌ 异常: {str(e)[:100]}")
    
    return None, None


def update_config(model_name):
    """更新配置文件"""
    print("\n" + "=" * 60)
    print("更新配置文件")
    print("=" * 60)
    
    env_path = "ai-test-platform/.env"
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 更新配置
        lines = content.split('\n')
        new_lines = []
        
        for line in lines:
            if line.startswith('DEFAULT_AI_MODEL='):
                new_lines.append(f'DEFAULT_AI_MODEL={model_name}')
                print(f"✅ 更新模型: {model_name}")
            elif line.startswith('DEFAULT_AI_PROVIDER='):
                new_lines.append('DEFAULT_AI_PROVIDER=openai')
                print(f"✅ 更新提供商: openai")
            else:
                new_lines.append(line)
        
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        
        print(f"✅ 配置文件已更新: {env_path}")
        return True
        
    except Exception as e:
        print(f"❌ 更新配置失败: {e}")
        return False


if __name__ == "__main__":
    print("\n🚀 寻找可用的免费模型\n")
    
    model, response = test_free_models()
    
    if model:
        print("\n" + "=" * 60)
        print("找到可用模型!")
        print("=" * 60)
        print(f"模型: {model}")
        print(f"响应示例: {response[:200]}")
        
        # 更新配置
        if update_config(model):
            print("\n🎉 配置已更新，现在可以使用 AI 功能了！")
            print("\n💡 下一步:")
            print("  1. 重启后端服务")
            print("  2. 在前端使用 AI 生成功能")
    else:
        print("\n⚠️  未找到可用的免费模型")
        print("建议:")
        print("  1. 检查网络连接")
        print("  2. 稍后重试（可能是速率限制）")
        print("  3. 考虑充值 API 额度")
