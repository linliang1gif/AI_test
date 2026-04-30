"""测试智谱AI API Key是否可用"""
import requests
import json

# 智谱AI配置
API_KEY = "0b6a065c64024224b3407095cd0458f5.419DGCPourJnP8F8"
BASE_URL = "https://open.bigmodel.cn/api/paas/v4"

def test_zhipu_api():
    """测试智谱AI API"""
    print("=" * 60)
    print("🧪 测试智谱AI API Key")
    print("=" * 60)
    print(f"📍 Base URL: {BASE_URL}")
    print(f"🔑 API Key: {API_KEY[:20]}...")
    print()
    
    # 测试请求
    url = f"{BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "glm-4-flash",
        "messages": [
            {
                "role": "user",
                "content": "你好,请用一句话介绍你自己"
            }
        ],
        "temperature": 0.7,
        "max_tokens": 100
    }
    
    print("📤 发送测试请求...")
    print(f"   模型: {payload['model']}")
    print(f"   消息: {payload['messages'][0]['content']}")
    print()
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"📥 响应状态码: {response.status_code}")
        print()
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API Key 可用!")
            print()
            print("📝 响应内容:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                print()
                print("💬 AI回复:")
                print(f"   {content}")
            
            return True
        else:
            print("❌ API Key 不可用!")
            print()
            print("错误信息:")
            print(response.text)
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        return False

if __name__ == "__main__":
    success = test_zhipu_api()
    print()
    print("=" * 60)
    if success:
        print("✅ 测试通过 - API Key可以正常使用")
    else:
        print("❌ 测试失败 - API Key无法使用")
    print("=" * 60)
