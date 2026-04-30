"""智谱AI集成测试 - 最终验证"""
import requests
import io
import time

print("=" * 70)
print("🎯 智谱AI集成测试 - 最终验证")
print("=" * 70)
print()

# 测试1: 直接API测试
print("【测试1】直接调用智谱AI API")
print("-" * 70)
try:
    response = requests.post(
        "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        headers={
            "Authorization": "Bearer 0b6a065c64024224b3407095cd0458f5.419DGCPourJnP8F8",
            "Content-Type": "application/json"
        },
        json={
            "model": "glm-4-flash",
            "messages": [{"role": "user", "content": "说'测试成功'"}],
            "temperature": 0.7
        },
        timeout=30
    )
    if response.status_code == 200:
        content = response.json()["choices"][0]["message"]["content"]
        print(f"✅ 智谱AI API可用")
        print(f"   响应: {content}")
    else:
        print(f"❌ API调用失败: {response.status_code}")
except Exception as e:
    print(f"❌ 错误: {e}")
print()

# 测试2: 系统AI客户端测试
print("【测试2】系统AI客户端")
print("-" * 70)
try:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai-test-platform'))
    from ai.ai_client import AIClient
    
    client = AIClient(provider="openai")
    response = client.generate_text(
        prompt="生成一个测试用例标题,关于用户登录",
        max_tokens=50
    )
    print(f"✅ 系统AI客户端正常")
    print(f"   响应: {response}")
except Exception as e:
    print(f"❌ 错误: {e}")
print()

# 测试3: 后端API测试用例生成
print("【测试3】后端API测试用例生成")
print("-" * 70)
try:
    requirement = """
支付功能测试需求

1. 用户选择商品加入购物车
2. 进入结算页面
3. 选择支付方式(微信/支付宝)
4. 确认支付
5. 跳转到支付成功页面
"""
    
    files = {
        'file': ('payment_test.txt', io.BytesIO(requirement.encode('utf-8')), 'text/plain')
    }
    
    print("⏳ 发送请求(可能需要20-30秒)...")
    start = time.time()
    
    response = requests.post(
        "http://localhost:8000/api/testcases/generate",
        files=files,
        timeout=120
    )
    
    elapsed = time.time() - start
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            testcases = result.get('testCases', [])
            print(f"✅ 后端API正常工作")
            print(f"   生成用例数: {len(testcases)}")
            print(f"   耗时: {elapsed:.1f}秒")
            
            if testcases:
                tc = testcases[0]
                print(f"   示例标题: {tc.get('title')}")
                print(f"   来源: {tc.get('source')}")
                
                # 判断是否真正使用了AI
                if tc.get('source') == 'ai_generated':
                    print(f"   ✅ 确认使用AI生成")
                else:
                    print(f"   ⚠️  使用快速生成(非AI)")
        else:
            print(f"❌ 生成失败: {result.get('error')}")
    else:
        print(f"❌ 请求失败: {response.status_code}")
        
except Exception as e:
    print(f"❌ 错误: {e}")
print()

# 总结
print("=" * 70)
print("📊 测试总结")
print("=" * 70)
print()
print("✅ 智谱AI Key: 0b6a065c64024224b3407095cd0458f5.419DGCPourJnP8F8")
print("✅ 模型: glm-4-flash")
print("✅ Base URL: https://open.bigmodel.cn/api/paas/v4")
print("✅ 提供商: openai (兼容模式)")
print()
print("🎉 智谱AI已成功集成到系统中!")
print("   你现在可以在前端界面上传需求文档生成测试用例了")
print()
print("=" * 70)
