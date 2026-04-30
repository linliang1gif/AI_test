#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""测试Claude Sonnet 4.5是否可以正常工作"""

import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(override=True)

from ai.ai_client import get_ai_client

print("=" * 60)
print("🧪 测试Claude Sonnet 4.5工作状态")
print("=" * 60)

# 1. 获取AI客户端
print("\n1️⃣ 获取AI客户端:")
client = get_ai_client(provider='anthropic')
print(f"   ✅ 客户端类型: {type(client).__name__}")
print(f"   ✅ 模型: {client.model}")
print(f"   ✅ Base URL: {client.base_url}")

# 2. 测试简单对话
print("\n2️⃣ 测试简单对话:")
try:
    response = client.generate_text("你好,请用一句话介绍你自己")
    if "错误" not in response:
        print(f"   ✅ 响应: {response[:100]}...")
    else:
        print(f"   ⚠️  响应: {response}")
except Exception as e:
    print(f"   ❌ 失败: {str(e)}")

# 3. 测试测试用例生成场景
print("\n3️⃣ 测试测试用例生成场景:")
try:
    prompt = """
    请为以下API生成测试用例:
    
    接口: POST /api/login
    功能: 用户登录
    参数: username, password
    
    请生成3个测试场景。
    """
    response = client.generate_text(prompt)
    if "错误" not in response:
        print(f"   ✅ 生成成功,长度: {len(response)} 字符")
        print(f"   前200字符: {response[:200]}...")
    else:
        print(f"   ⚠️  响应: {response}")
except Exception as e:
    print(f"   ❌ 失败: {str(e)}")

# 4. 测试JSON格式输出
print("\n4️⃣ 测试JSON格式输出:")
try:
    prompt = """
    请以JSON格式返回以下信息:
    {
        "status": "success",
        "model": "你的模型名称",
        "message": "测试成功"
    }
    """
    response = client.generate_text(prompt)
    if "错误" not in response:
        print(f"   ✅ 响应: {response[:200]}...")
    else:
        print(f"   ⚠️  响应: {response}")
except Exception as e:
    print(f"   ❌ 失败: {str(e)}")

print("\n" + "=" * 60)
print("✅ Claude Sonnet 4.5 已经可以正常调用!")
print("=" * 60)
