#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""诊断Anthropic BASE_URL问题"""

import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("🔍 Anthropic BASE_URL 诊断")
print("=" * 60)

# 1. 检查.env文件内容
print("\n1️⃣ 检查.env文件内容:")
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            if 'ANTHROPIC' in line:
                print(f"   {line.strip()}")
else:
    print("   ❌ .env文件不存在")

# 2. 检查系统环境变量
print("\n2️⃣ 检查系统环境变量:")
for key in os.environ:
    if 'ANTHROPIC' in key or 'BASE_URL' in key:
        print(f"   {key}={os.environ[key]}")

# 3. 加载dotenv后检查
print("\n3️⃣ 加载dotenv后检查:")
from dotenv import load_dotenv
load_dotenv(override=True)

anthropic_base = os.getenv('ANTHROPIC_BASE_URL')
anthropic_key = os.getenv('ANTHROPIC_API_KEY')
default_provider = os.getenv('DEFAULT_AI_PROVIDER')
default_model = os.getenv('DEFAULT_AI_MODEL')

print(f"   ANTHROPIC_BASE_URL: {anthropic_base}")
print(f"   ANTHROPIC_API_KEY: {anthropic_key[:20]}..." if anthropic_key else "   ANTHROPIC_API_KEY: None")
print(f"   DEFAULT_AI_PROVIDER: {default_provider}")
print(f"   DEFAULT_AI_MODEL: {default_model}")

# 4. 测试AnthropicAIClient初始化
print("\n4️⃣ 测试AnthropicAIClient初始化:")
from ai.mock_ai_client import AnthropicAIClient

client = AnthropicAIClient(
    base_url=anthropic_base,
    model=default_model,
    api_key=anthropic_key
)

print(f"   client.base_url: {client.base_url}")
print(f"   client.model: {client.model}")
print(f"   client.api_key: {client.api_key[:20]}..." if client.api_key else "   client.api_key: None")

# 5. 测试get_ai_client函数
print("\n5️⃣ 测试get_ai_client函数:")
from ai.ai_client import get_ai_client

ai_client = get_ai_client(provider='anthropic')
print(f"   类型: {type(ai_client).__name__}")
if hasattr(ai_client, 'base_url'):
    print(f"   base_url: {ai_client.base_url}")
if hasattr(ai_client, 'model'):
    print(f"   model: {ai_client.model}")

# 6. 测试实际API调用
print("\n6️⃣ 测试实际API调用:")
try:
    import requests
    headers = {
        "Content-Type": "application/json",
        "x-api-key": anthropic_key,
        "anthropic-version": "2023-06-01"
    }
    
    payload = {
        "model": default_model,
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 10
    }
    
    url = f"{anthropic_base}/v1/messages"
    print(f"   请求URL: {url}")
    
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    print(f"   状态码: {response.status_code}")
    
    if response.status_code != 200:
        print(f"   错误: {response.text[:200]}")
    else:
        print(f"   ✅ API调用成功")
        
except Exception as e:
    print(f"   ❌ API调用失败: {str(e)}")

print("\n" + "=" * 60)
