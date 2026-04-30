"""测试所有配置的 AI 提供商是否可用"""
import os
import requests
from dotenv import load_dotenv

load_dotenv('ai-test-platform/.env')

def test_deepseek():
    """测试 DeepSeek API"""
    api_key = os.getenv('DEEPSEEK_API_KEY')
    base_url = os.getenv('DEEPSEEK_BASE_URL')
    
    print("\n=== 测试 DeepSeek ===")
    print(f"API Key: {api_key[:20]}...")
    print(f"Base URL: {base_url}")
    
    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ DeepSeek 可用")
            return True
        else:
            print(f"❌ DeepSeek 失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ DeepSeek 连接失败: {e}")
        return False

def test_openai_bigmodel():
    """测试智谱 BigModel API"""
    api_key = os.getenv('OPENAI_API_KEY')
    base_url = os.getenv('OPENAI_BASE_URL')
    
    print("\n=== 测试智谱 BigModel ===")
    print(f"API Key: {api_key[:20]}...")
    print(f"Base URL: {base_url}")
    
    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "glm-4-flash",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ 智谱 BigModel 可用")
            return True
        else:
            print(f"❌ 智谱 BigModel 失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 智谱 BigModel 连接失败: {e}")
        return False

def test_anthropic():
    """测试 Anthropic API"""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    base_url = os.getenv('ANTHROPIC_BASE_URL')
    
    print("\n=== 测试 Anthropic ===")
    print(f"API Key: {api_key[:20]}...")
    print(f"Base URL: {base_url}")
    
    try:
        response = requests.post(
            f"{base_url}/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            },
            json={
                "model": "claude-3-sonnet-20240229",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Anthropic 可用")
            return True
        else:
            print(f"❌ Anthropic 失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Anthropic 连接失败: {e}")
        return False

def test_ollama():
    """测试 Ollama 本地服务"""
    base_url = os.getenv('OLLAMA_BASE_URL')
    
    print("\n=== 测试 Ollama ===")
    print(f"Base URL: {base_url}")
    
    try:
        # 先测试服务是否运行
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✅ Ollama 可用，已安装模型: {[m['name'] for m in models]}")
            return True
        else:
            print(f"❌ Ollama 失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ollama 未运行或连接失败: {e}")
        return False

if __name__ == "__main__":
    print("开始测试所有 AI 提供商...")
    
    results = {
        "deepseek": test_deepseek(),
        "bigmodel": test_openai_bigmodel(),
        "anthropic": test_anthropic(),
        "ollama": test_ollama()
    }
    
    print("\n" + "="*50)
    print("测试结果汇总:")
    print("="*50)
    for provider, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {provider}: {'可用' if status else '不可用'}")
    
    available = [k for k, v in results.items() if v]
    print(f"\n可用的提供商: {', '.join(available) if available else '无'}")
