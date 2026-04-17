#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试 AI 调用
"""

import sys
sys.path.insert(0, 'ai-test-platform')

from ai.ai_client import AIClient

print("🧪 测试 AI 客户端")
print("=" * 60)

# 创建 AI 客户端
client = AIClient(provider='openai')

print(f"提供商: {client.provider}")
print(f"配置: {client.ai_config}")

# 简单测试
prompt = "请用一句话描述什么是单元测试"

print(f"\n📝 提示词: {prompt}")
print(f"🔄 正在调用 AI...")

try:
    response = client.generate_text(prompt)
    print(f"\n✅ 成功!")
    print(f"📄 AI 响应:\n{response}")
except Exception as e:
    print(f"\n❌ 失败: {e}")

print("\n" + "=" * 60)
