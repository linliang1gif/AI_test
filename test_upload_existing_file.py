"""
测试上传已存在的Swagger文件
"""
import requests
import json


file_path = r"ai-test-platform\swaggerApi (1).json"

print("=" * 60)
print("测试上传已存在的Swagger文件")
print("=" * 60)
print(f"\n文件: {file_path}")

try:
    with open(file_path, 'rb') as f:
        files = {'file': ('swagger.json', f, 'application/json')}
        print("\n正在上传...")
        response = requests.post("http://localhost:8000/api/swagger/upload", files=files, timeout=60)
    
    print(f"\n状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 上传成功!")
        print(f"\n响应:")
        print(f"  成功: {result.get('success')}")
        print(f"  消息: {result.get('message')}")
        print(f"  API数量: {result.get('count')}")
        
        if result.get('apis'):
            print(f"\n前3个API:")
            for i, api in enumerate(result['apis'][:3], 1):
                print(f"  {i}. {api.get('title', 'N/A')}")
    else:
        result = response.json()
        print(f"❌ 上传失败")
        print(f"\n错误信息: {result.get('message')}")
        
except requests.exceptions.Timeout:
    print("❌ 请求超时（文件太大，处理时间较长）")
    print("   建议: 使用较小的Swagger文件测试")
except Exception as e:
    print(f"❌ 错误: {e}")
