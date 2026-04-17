#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""测试Ollama修复"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from ai.ai_client import get_ai_client

def test_ollama():
    """测试Ollama客户端"""
    print("🧪 测试Ollama AI客户端...")
    
    # 获取Ollama客户端
    client = get_ai_client(provider='ollama')
    print(f"✅ 客户端类型: {type(client).__name__}")
    
    # 测试文本生成
    print("\n📝 测试文本生成...")
    response = client.generate_text("请用一句话介绍Python编程语言")
    print(f"响应: {response[:100]}...")
    
    # 测试JSON生成
    print("\n📋 测试JSON生成...")
    json_response = client.generate_json(
        "请生成一个包含3个测试场景的JSON,格式为: {\"scenarios\": [{\"name\": \"场景名\", \"description\": \"描述\"}]}"
    )
    print(f"JSON响应: {json_response}")
    
    print("\n✅ Ollama测试完成!")

if __name__ == "__main__":
    test_ollama()
