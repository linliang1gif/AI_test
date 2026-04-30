#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""测试Ollama本地模型"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import requests
import json

def test_ollama_connection():
    """测试Ollama连接"""
    print("🔍 测试Ollama连接...")

    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])
            print(f"✅ Ollama运行正常，可用模型: {len(models)}个")
            for model in models:
                print(f"  - {model['name']}")
            return True, models
        else:
            print(f"❌ Ollama响应异常: {response.status_code}")
            return False, []
    except Exception as e:
        print(f"❌ Ollama连接失败: {e}")
        return False, []

def test_ollama_generate(model_name):
    """测试Ollama生成"""
    print(f"\n🧪 测试模型: {model_name}")

    try:
        payload = {
            "model": model_name,
            "messages": [
                {"role": "user", "content": "用一句话介绍Python"}
            ],
            "stream": False
        }

        response = requests.post(
            "http://localhost:11434/api/chat",
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            content = result.get("message", {}).get("content", "")
            print(f"✅ 生成成功:")
            print(f"  {content[:100]}...")
            return True
        else:
            print(f"❌ 生成失败: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 生成异常: {e}")
        return False

def test_ai_client_ollama():
    """测试AI客户端的Ollama支持"""
    print("\n🔧 测试AI客户端...")

    try:
        from ai.enhanced_ai_client import OllamaClient

        client = OllamaClient(
            base_url="http://localhost:11434",
            model="qwen2.5:1.5b"
        )

        response = client.generate("写一个Python函数计算斐波那契数列")
        print(f"✅ AI客户端测试成功:")
        print(f"  {response[:100]}...")
        return True

    except Exception as e:
        print(f"❌ AI客户端测试失败: {e}")
        return False

def main():
    print("=" * 60)
    print("🚀 Ollama本地模型测试")
    print("=" * 60)

    # 测试连接
    success, models = test_ollama_connection()
    if not success or not models:
        print("\n❌ Ollama未运行或无可用模型")
        print("\n💡 启动Ollama:")
        print("  1. 打开Ollama应用")
        print("  2. 或运行: ollama serve")
        return

    # 测试生成
    test_model = models[0]["name"]
    if test_ollama_generate(test_model):
        print(f"\n✅ 模型 {test_model} 工作正常")

    # 测试AI客户端
    test_ai_client_ollama()

    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    print(f"✅ Ollama状态: 运行中")
    print(f"✅ 可用模型: {len(models)}个")
    print(f"✅ 推荐使用: {models[0]['name']}")
    print("\n💡 在项目中使用:")
    print("  from ai.enhanced_ai_client import OllamaClient")
    print(f"  client = OllamaClient('http://localhost:11434', '{models[0]['name']}')")
    print("  response = client.generate('你的提示词')")
    print("=" * 60)

if __name__ == "__main__":
    main()
