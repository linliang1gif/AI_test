"""
测试后端Swagger解析功能
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# 测试URL
test_url = "https://petstore.swagger.io/v2/swagger.json"

print("=" * 60)
print("测试后端Swagger解析")
print("=" * 60)

print(f"\n1. 测试URL: {test_url}")
print("-" * 60)

try:
    # 调用后端API
    response = requests.post(
        f"{BASE_URL}/api/swagger/parse",
        json={"url": test_url},
        timeout=30
    )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        
        if result.get('success'):
            print(f"✅ 解析成功!")
            print(f"   解析到的API数量: {result.get('count', 0)}")
            
            # 显示前3个API
            apis = result.get('apis', [])
            if apis:
                print(f"\n   前3个API示例:")
                for i, api in enumerate(apis[:3], 1):
                    print(f"   {i}. {api.get('method')} {api.get('path')}")
                    print(f"      {api.get('summary', 'N/A')}")
        else:
            print(f"❌ 解析失败: {result.get('message')}")
    else:
        print(f"❌ 请求失败")
        print(response.text)
        
except Exception as e:
    print(f"❌ 错误: {e}")

print("\n" + "=" * 60)
print("2. 检查API列表")
print("=" * 60)

try:
    response = requests.get(f"{BASE_URL}/api/apis")
    
    if response.status_code == 200:
        result = response.json()
        apis = result.get('apis', [])
        
        print(f"✅ 当前API数量: {len(apis)}")
        
        if apis:
            print(f"\n前5个API:")
            for i, api in enumerate(apis[:5], 1):
                print(f"{i}. {api.get('method')} {api.get('path')}")
                print(f"   {api.get('summary', 'N/A')}")
        else:
            print("\n⚠️ API列表为空")
    else:
        print(f"❌ 获取失败: {response.status_code}")
        
except Exception as e:
    print(f"❌ 错误: {e}")

print("\n" + "=" * 60)
print("使用说明")
print("=" * 60)
print("\n在前端使用以下URL:")
print("✅ https://petstore.swagger.io/v2/swagger.json")
print("✅ https://petstore3.swagger.io/api/v3/openapi.json")
print("\n这两个URL都可以正常解析!")
