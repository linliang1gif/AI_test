#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""使用Ollama本地模型的完整流程演示"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from ai.ai_client import get_ai_client

def demo_ollama():
    """演示Ollama功能"""
    print("=" * 60)
    print("🚀 Ollama本地模型演示")
    print("=" * 60)

    # 获取Ollama客户端
    print("\n📡 连接Ollama...")
    client = get_ai_client(use_ollama=True)
    print("✅ 连接成功")

    # 测试1: 生成测试策略
    print("\n📝 测试1: 生成测试策略")
    print("-" * 60)
    prompt = """
请为一个用户管理系统生成测试策略，包括：
1. 测试范围
2. 测试方法
3. 测试重点
"""
    response = client.generate_text(prompt)
    print(response)

    # 测试2: 生成测试用例
    print("\n📝 测试2: 生成测试用例")
    print("-" * 60)
    prompt = """
为用户登录功能生成3个测试用例，包括：
- 正常登录
- 密码错误
- 用户不存在
"""
    response = client.generate_text(prompt)
    print(response)

    # 测试3: 代码生成
    print("\n📝 测试3: 生成Python代码")
    print("-" * 60)
    prompt = "写一个Python函数，实现快速排序算法"
    response = client.generate_text(prompt)
    print(response)

    print("\n" + "=" * 60)
    print("✅ Ollama演示完成")
    print("=" * 60)

if __name__ == "__main__":
    demo_ollama()
