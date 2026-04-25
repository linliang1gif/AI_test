#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
诊断OpenAI API Key
"""

import requests

def diagnose_openai_key():
    """诊断OpenAI API Key"""
    
    import os as _os
    api_key = _os.getenv("OPENAI_API_KEY", "")
    
    print("=" * 60)
    print("OpenAI API Key诊断")
    print("=" * 60)
    
    print(f"\nAPI Key: {api_key[:20]}...")
    print(f"Key长度: {len(api_key)}")
    print(f"Key前缀: {api_key[:3]}")
    
    # 测试不同的Base URL
    test_urls = [
        ("OpenAI官方", "https://api.openai.com/v1"),
        ("OpenAI代理1", "https://api.openai-proxy.com/v1"),
        ("OpenAI代理2", "https://api.chatanywhere.com.cn/v1"),
        ("OpenAI代理3", "https://api.chatanywhere.tech/v1"),
        ("OpenAI代理4", "https://api.openai-sb.com/v1"),
    ]
    
    print("\n🔍 测试不同的API端点...")
    
    for name, base_url in test_urls:
        print(f"\n测试 {name}: {base_url}")
        
        try:
            response = requests.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 10
                },
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"   ✅ 成功! 状态码: {response.status_code}")
                print(f"   响应: {response.json()}")
                print(f"\n🎉 找到可用的API端点: {base_url}")
                return base_url
            else:
                print(f"   ❌ 失败! 状态码: {response.status_code}")
                print(f"   错误: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print(f"   ⏱️  超时")
        except requests.exceptions.ConnectionError:
            print(f"   🔌 连接失败")
        except Exception as e:
            print(f"   ❌ 错误: {str(e)[:100]}")
    
    print("\n" + "=" * 60)
    print("❌ 未找到可用的API端点")
    print("=" * 60)
    
    print("\n💡 可能的原因:")
    print("   1. API Key无效或已过期")
    print("   2. API Key来自特定的服务商,需要使用对应的Base URL")
    print("   3. API Key需要特殊的认证方式")
    print("   4. 网络问题或防火墙限制")
    
    print("\n🔧 建议:")
    print("   1. 确认API Key来源(OpenAI官方/代理商)")
    print("   2. 检查API Key是否有效")
    print("   3. 联系API Key提供商获取正确的Base URL")
    print("   4. 或者使用DeepSeek (已配置,速度快)")
    
    return None

if __name__ == "__main__":
    diagnose_openai_key()
