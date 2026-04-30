#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试两个Ollama模型的性能和功能
"""

import requests
import time
import json

def test_model(model_name, test_prompt):
    """测试指定模型"""
    print(f"\n🔍 测试模型: {model_name}")
    print(f"📝 测试提示: {test_prompt}")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': model_name,
                'prompt': test_prompt,
                'stream': False,
                'options': {
                    'temperature': 0.2,
                    'num_predict': 500
                }
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            generated_text = result.get('response', '')
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"✅ 生成成功 (耗时: {duration:.2f}秒)")
            print(f"📄 生成内容: {generated_text[:200]}...")
            print(f"📊 内容长度: {len(generated_text)} 字符")
            
            return True, duration, len(generated_text)
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False, 0, 0
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False, 0, 0

def main():
    """主测试函数"""
    print("🚀 开始测试Ollama模型性能对比\n")
    
    # 测试用例
    test_cases = [
        {
            "name": "API测试用例生成",
            "prompt": "请生成一个用户登录API的测试用例，包括正常登录和异常情况"
        },
        {
            "name": "代码生成",
            "prompt": "请用Python写一个简单的HTTP客户端函数，用于发送POST请求"
        },
        {
            "name": "测试分析",
            "prompt": "分析这个测试失败的原因：AssertionError: Expected status code 200, got 401"
        }
    ]
    
    # 要测试的模型
    models = [
        "qwen2.5:1.5b",      # 轻量级模型
        "qwen2.5-coder:latest"  # 代码专用模型
    ]
    
    results = {}
    
    for model in models:
        print(f"\n{'='*60}")
        print(f"🤖 测试模型: {model}")
        print(f"{'='*60}")
        
        model_results = []
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n--- 测试用例 {i}: {test_case['name']} ---")
            
            success, duration, length = test_model(model, test_case['prompt'])
            
            model_results.append({
                'test_case': test_case['name'],
                'success': success,
                'duration': duration,
                'length': length
            })
            
            # 避免请求过于频繁
            time.sleep(1)
        
        results[model] = model_results
    
    # 性能对比总结
    print(f"\n{'='*60}")
    print("📊 性能对比总结")
    print(f"{'='*60}")
    
    for model, model_results in results.items():
        print(f"\n🤖 {model}:")
        
        successful_tests = [r for r in model_results if r['success']]
        if successful_tests:
            avg_duration = sum(r['duration'] for r in successful_tests) / len(successful_tests)
            avg_length = sum(r['length'] for r in successful_tests) / len(successful_tests)
            
            print(f"  ✅ 成功率: {len(successful_tests)}/{len(model_results)}")
            print(f"  ⏱️  平均响应时间: {avg_duration:.2f}秒")
            print(f"  📝 平均生成长度: {avg_length:.0f}字符")
        else:
            print(f"  ❌ 所有测试失败")
    
    # 推荐使用场景
    print(f"\n💡 使用建议:")
    print(f"  • qwen2.5:1.5b - 适合快速响应的简单任务")
    print(f"  • qwen2.5-coder:latest - 适合复杂的代码生成任务")

if __name__ == "__main__":
    main()