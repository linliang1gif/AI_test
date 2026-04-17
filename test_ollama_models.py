#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试本地 Ollama 模型
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'ai-test-platform'))

def test_ollama_model(model_name):
    """测试指定的 Ollama 模型"""
    print(f"\n{'='*60}")
    print(f"测试模型: {model_name}")
    print('='*60)
    
    try:
        from ai.ai_client import AIClient
        
        # 创建客户端
        client = AIClient(provider="ollama")
        print(f"✅ 客户端创建成功")
        
        # 测试简单调用
        prompt = "请用一句话介绍什么是软件测试"
        print(f"📝 提示词: {prompt}")
        print(f"🤖 正在调用 AI...")
        
        response = client.generate_text(
            prompt=prompt,
            system_prompt="你是一个专业的软件测试工程师",
            temperature=0.2,
            max_tokens=100,
            model=model_name  # 通过参数传递模型名称
        )
        
        print(f"\n✅ AI 响应成功!")
        print(f"📄 响应内容:\n{response}")
        
        return True
    except Exception as e:
        print(f"❌ 调用失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "="*60)
    print("本地 Ollama 模型测试")
    print("="*60)
    
    # 可用的模型列表
    models = [
        ("qwen2.5:1.5b", "轻量级模型，速度快"),
        ("qwen2.5-7b-instruct:latest", "通用指令模型，效果好"),
        ("qwen2.5-coder:latest", "代码专用模型"),
    ]
    
    results = []
    
    for model_name, description in models:
        print(f"\n💡 {description}")
        result = test_ollama_model(model_name)
        results.append((model_name, result))
    
    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    for model_name, result in results:
        status = "✅ 可用" if result else "❌ 失败"
        print(f"{status} - {model_name}")
    
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    if passed > 0:
        print(f"\n🎉 {passed}/{len(results)} 个模型可用!")
        print("\n💡 推荐使用:")
        print("  - qwen2.5-7b-instruct:latest (效果最好)")
        print("  - qwen2.5:1.5b (速度最快)")
        return 0
    else:
        print("\n⚠️ 所有模型测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
