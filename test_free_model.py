#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 OpenRouter 免费模型
"""

import requests
import json

api_key = "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"
base_url = "https://openrouter.ai/api/v1"

# 测试免费模型
free_model = "google/gemma-4-26b-a4b-it:free"

print(f"🧪 测试免费模型: {free_model}")
print("=" * 60)

payload = {
    "model": free_model,
    "messages": [
        {
            "role": "user",
            "content": "请用一句话介绍什么是软件测试"
        }
    ],
    "max_tokens": 100
}

try:
    response = requests.post(
        f"{base_url}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30
    )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
        print(f"\n✅ 成功!")
        print(f"📄 AI 响应:\n{content}")
        
        usage = result.get('usage', {})
        if usage:
            print(f"\n📊 Token 使用:")
            print(f"  输入: {usage.get('prompt_tokens', 0)}")
            print(f"  输出: {usage.get('completion_tokens', 0)}")
            print(f"  总计: {usage.get('total_tokens', 0)}")
    else:
        print(f"\n❌ 失败")
        print(f"响应: {response.text}")
        
except Exception as e:
    print(f"❌ 错误: {e}")
