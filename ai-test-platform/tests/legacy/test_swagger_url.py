"""
测试Swagger URL解析
"""
import requests

# SwaggerHub的正确API URL格式
# 文档页面: https://app.swaggerhub.com/apis-docs/JSONPlaceholder/JSONPlaceholder/1.0.0
# 实际API: https://api.swaggerhub.com/apis/JSONPlaceholder/JSONPlaceholder/1.0.0

test_urls = [
    # 正确的API URL
    "https://api.swaggerhub.com/apis/JSONPlaceholder/JSONPlaceholder/1.0.0",
    
    # 其他常见的Swagger示例
    "https://petstore.swagger.io/v2/swagger.json",
    "https://petstore3.swagger.io/api/v3/openapi.json",
]

print("=" * 60)
print("测试Swagger URL")
print("=" * 60)

for url in test_urls:
    print(f"\n测试URL: {url}")
    print("-" * 60)
    
    try:
        response = requests.get(url, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # 检测Swagger版本
            if 'swagger' in data:
                print(f"✅ Swagger 2.0 文档")
                print(f"   标题: {data.get('info', {}).get('title', 'N/A')}")
                print(f"   版本: {data.get('info', {}).get('version', 'N/A')}")
                print(f"   路径数量: {len(data.get('paths', {}))}")
            elif 'openapi' in data:
                print(f"✅ OpenAPI {data['openapi']} 文档")
                print(f"   标题: {data.get('info', {}).get('title', 'N/A')}")
                print(f"   版本: {data.get('info', {}).get('version', 'N/A')}")
                print(f"   路径数量: {len(data.get('paths', {}))}")
            else:
                print("❌ 无法识别的格式")
        else:
            print(f"❌ 请求失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 错误: {e}")

print("\n" + "=" * 60)
print("正确的URL格式说明:")
print("=" * 60)
print("\n1. SwaggerHub:")
print("   文档页面: https://app.swaggerhub.com/apis-docs/{owner}/{api}/{version}")
print("   API地址:  https://api.swaggerhub.com/apis/{owner}/{api}/{version}")
print("\n2. 本地Swagger:")
print("   http://localhost:8080/v2/api-docs")
print("   http://localhost:8080/v3/api-docs")
print("\n3. 在线示例:")
print("   https://petstore.swagger.io/v2/swagger.json")
print("   https://petstore3.swagger.io/api/v3/openapi.json")

print("\n" + "=" * 60)
print("推荐使用:")
print("=" * 60)
print("\n✅ Petstore示例 (Swagger 2.0):")
print("   https://petstore.swagger.io/v2/swagger.json")
print("\n✅ Petstore示例 (OpenAPI 3.0):")
print("   https://petstore3.swagger.io/api/v3/openapi.json")
