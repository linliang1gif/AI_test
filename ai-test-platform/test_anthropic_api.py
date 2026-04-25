"""测试 Anthropic API"""
import requests
import json

url = "http://1.95.142.151:3000/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {__import__('os').getenv('ANTHROPIC_API_KEY', '')}"
}

payload = {
    "model": "openclaw-default-api-KWJxLGWf",
    "messages": [
        {"role": "user", "content": "你好,请回复'测试成功'"}
    ],
    "temperature": 0.2,
    "max_tokens": 100
}

print("🔍 测试 Anthropic API...")
print(f"URL: {url}")
print(f"Model: {payload['model']}")
print()

try:
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    print(f"Status Code: {response.status_code}")
    print(f"\nResponse Headers:")
    for key, value in response.headers.items():
        print(f"  {key}: {value}")
    
    print(f"\nResponse Body:")
    print(response.text[:1000])  # 只显示前1000字符
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"\n✅ JSON解析成功:")
            print(json.dumps(data, indent=2, ensure_ascii=False)[:500])
        except:
            print(f"\n❌ JSON解析失败,返回的不是有效JSON")
    else:
        print(f"\n❌ API调用失败")
        
except Exception as e:
    print(f"\n❌ 请求异常: {e}")
