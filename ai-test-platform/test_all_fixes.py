#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整测试修复的功能:
1. 批量删除功能
2. Ollama超时修复 (180秒)
"""

import requests
import json
import time

def test_batch_delete():
    """测试批量删除功能"""
    base_url = "http://localhost:8000"
    
    print("\n" + "=" * 60)
    print("【测试1】批量删除功能")
    print("=" * 60)
    
    # 1. 获取当前测试用例
    print("\n1️⃣ 获取当前测试用例...")
    response = requests.get(f"{base_url}/api/test-cases")
    result = response.json()
    test_cases = result.get('data', [])
    print(f"   ✅ 当前有 {len(test_cases)} 个测试用例")
    
    if len(test_cases) < 2:
        print("   ⚠️  测试用例数量不足，跳过删除测试")
        return True
    
    # 2. 选择前2个测试用例进行删除
    ids_to_delete = [test_cases[0]['id'], test_cases[1]['id']]
    print(f"\n2️⃣ 准备删除测试用例 ID: {ids_to_delete}")
    print(f"   标题: {test_cases[0].get('title', 'N/A')}")
    print(f"   标题: {test_cases[1].get('title', 'N/A')}")
    
    # 3. 调用批量删除API
    print("\n3️⃣ 调用批量删除API...")
    delete_response = requests.post(
        f"{base_url}/api/testcases/batch-delete",
        headers={"Content-Type": "application/json"},
        json={"ids": ids_to_delete}
    )
    
    delete_result = delete_response.json()
    
    if delete_result.get('success'):
        print(f"   ✅ {delete_result.get('message')}")
        
        # 4. 验证删除结果
        print("\n4️⃣ 验证删除结果...")
        response = requests.get(f"{base_url}/api/test-cases")
        result = response.json()
        remaining_cases = result.get('data', [])
        print(f"   ✅ 剩余 {len(remaining_cases)} 个测试用例")
        
        # 检查被删除的ID是否还存在
        remaining_ids = [tc['id'] for tc in remaining_cases]
        still_exists = [id for id in ids_to_delete if id in remaining_ids]
        
        if len(still_exists) == 0:
            print("   ✅ 批量删除功能正常!")
            return True
        else:
            print(f"   ❌ 删除失败，以下ID仍然存在: {still_exists}")
            return False
    else:
        print(f"   ❌ 删除失败: {delete_result.get('error')}")
        return False

def check_ollama_timeout():
    """检查Ollama超时配置"""
    print("\n" + "=" * 60)
    print("【测试2】Ollama超时配置检查")
    print("=" * 60)
    
    # 读取mock_ai_client.py文件
    with open('ai/mock_ai_client.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查timeout配置
    if 'timeout=180' in content:
        print("   ✅ generate_text方法: timeout=180秒")
        timeout_count = content.count('timeout=180')
        print(f"   ✅ 找到 {timeout_count} 处 timeout=180 配置")
        return True
    else:
        print("   ❌ 未找到 timeout=180 配置")
        if 'timeout=60' in content:
            print("   ⚠️  仍然使用 timeout=60")
        return False

def test_ollama_connection():
    """测试Ollama连接"""
    print("\n" + "=" * 60)
    print("【测试3】Ollama连接测试")
    print("=" * 60)
    
    try:
        print("\n1️⃣ 测试Ollama服务...")
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"   ✅ Ollama服务正常运行")
            print(f"   ✅ 可用模型: {[m['name'] for m in models]}")
            return True
        else:
            print(f"   ❌ Ollama响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Ollama连接失败: {str(e)}")
        print("   💡 请确保Ollama服务正在运行: ollama serve")
        return False

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🔧 AI测试平台 - 功能修复验证")
    print("=" * 60)
    
    results = []
    
    # 测试1: 批量删除
    results.append(("批量删除功能", test_batch_delete()))
    
    # 测试2: Ollama超时配置
    results.append(("Ollama超时配置", check_ollama_timeout()))
    
    # 测试3: Ollama连接
    results.append(("Ollama连接", test_ollama_connection()))
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"   {status} - {name}")
    
    all_passed = all(r[1] for r in results)
    if all_passed:
        print("\n🎉 所有测试通过!")
    else:
        print("\n⚠️  部分测试失败，请检查上述输出")
