#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DeepSeek API 连接诊断工具
"""

import os
import sys
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_basic_connection():
    """测试基本网络连接"""
    print("=" * 60)
    print("1. 测试基本网络连接")
    print("=" * 60)
    
    try:
        response = requests.get("https://www.baidu.com", timeout=5)
        print("✅ 基本网络连接正常")
        return True
    except Exception as e:
        print(f"❌ 基本网络连接失败: {e}")
        return False

def test_deepseek_connection():
    """测试DeepSeek API连接"""
    print("\n" + "=" * 60)
    print("2. 测试DeepSeek API连接")
    print("=" * 60)
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ 未配置DEEPSEEK_API_KEY")
        return False
    
    print(f"API Key: {api_key[:10]}...{api_key[-4:]}")
    
    try:
        # 测试简单请求
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": "你好"}
            ],
            "max_tokens": 10
        }
        
        print("\n发送测试请求...")
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers=headers,
            json=payload,
            timeout=(10, 30),  # 连接超时10秒,读取超时30秒
            verify=True
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            print(f"✅ DeepSeek API连接成功!")
            print(f"响应内容: {content}")
            return True
        else:
            print(f"❌ DeepSeek API返回错误: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
            
    except requests.exceptions.SSLError as e:
        print(f"❌ SSL错误: {e}")
        print("\n可能的解决方案:")
        print("1. 检查系统时间是否正确")
        print("2. 更新Python的certifi包: pip install --upgrade certifi")
        print("3. 检查防火墙或代理设置")
        return False
    except requests.exceptions.Timeout as e:
        print(f"❌ 请求超时: {e}")
        print("\n可能的解决方案:")
        print("1. 检查网络连接速度")
        print("2. 尝试使用VPN或代理")
        print("3. 增加超时时间")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ 连接错误: {e}")
        print("\n可能的解决方案:")
        print("1. 检查DNS设置")
        print("2. 检查是否需要代理")
        print("3. 检查防火墙设置")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False

def test_with_proxy():
    """测试使用代理连接"""
    print("\n" + "=" * 60)
    print("3. 测试代理连接(如果配置了代理)")
    print("=" * 60)
    
    http_proxy = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
    https_proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
    
    if not http_proxy and not https_proxy:
        print("⚠️  未配置代理,跳过此测试")
        return None
    
    print(f"HTTP代理: {http_proxy}")
    print(f"HTTPS代理: {https_proxy}")
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ 未配置DEEPSEEK_API_KEY")
        return False
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": "你好"}
            ],
            "max_tokens": 10
        }
        
        proxies = {
            "http": http_proxy,
            "https": https_proxy
        }
        
        print("\n通过代理发送测试请求...")
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers=headers,
            json=payload,
            proxies=proxies,
            timeout=(10, 30),
            verify=True
        )
        
        if response.status_code == 200:
            print("✅ 通过代理连接成功!")
            return True
        else:
            print(f"❌ 代理连接失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 代理连接错误: {e}")
        return False

def check_environment():
    """检查环境配置"""
    print("\n" + "=" * 60)
    print("4. 检查环境配置")
    print("=" * 60)
    
    print(f"Python版本: {sys.version}")
    print(f"Requests版本: {requests.__version__}")
    
    try:
        import certifi
        print(f"Certifi版本: {certifi.__version__}")
        print(f"证书路径: {certifi.where()}")
    except ImportError:
        print("⚠️  未安装certifi包")
    
    print(f"\n环境变量:")
    print(f"  DEEPSEEK_API_KEY: {'已配置' if os.getenv('DEEPSEEK_API_KEY') else '未配置'}")
    print(f"  DEFAULT_AI_PROVIDER: {os.getenv('DEFAULT_AI_PROVIDER', '未设置')}")
    print(f"  HTTP_PROXY: {os.getenv('HTTP_PROXY', '未设置')}")
    print(f"  HTTPS_PROXY: {os.getenv('HTTPS_PROXY', '未设置')}")

def main():
    """主函数"""
    print("\n🔍 DeepSeek API 连接诊断工具\n")
    
    # 检查环境
    check_environment()
    
    # 测试基本连接
    basic_ok = test_basic_connection()
    
    if not basic_ok:
        print("\n❌ 基本网络连接失败,请先解决网络问题")
        return
    
    # 测试DeepSeek连接
    deepseek_ok = test_deepseek_connection()
    
    # 测试代理连接
    test_with_proxy()
    
    # 总结
    print("\n" + "=" * 60)
    print("诊断总结")
    print("=" * 60)
    
    if deepseek_ok:
        print("✅ DeepSeek API连接正常,可以正常使用")
        print("\n建议:")
        print("1. 如果仍然遇到问题,可能是间歇性网络问题")
        print("2. 建议在.env中设置更长的超时时间: AI_TIMEOUT=120")
    else:
        print("❌ DeepSeek API连接失败")
        print("\n建议:")
        print("1. 切换到Mock模式进行测试: DEFAULT_AI_PROVIDER=mock")
        print("2. 或者使用本地Ollama: DEFAULT_AI_PROVIDER=ollama")
        print("3. 检查网络连接和防火墙设置")
        print("4. 如果在国内,可能需要配置代理")

if __name__ == "__main__":
    main()
