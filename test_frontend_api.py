"""测试前端API调用"""
import requests

print("测试前端API调用")
print("=" * 60)

# 测试后端API
print("\n1. 测试后端 /api/apis 接口:")
response = requests.get("http://localhost:8000/api/apis")
print(f"   状态码: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   API数量: {data.get('count')}")
    print(f"   ✅ 后端接口正常")
else:
    print(f"   ❌ 后端接口异常")

# 测试前端代理
print("\n2. 测试前端代理 /api/apis:")
try:
    response = requests.get("http://localhost:5173/api/apis")
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   API数量: {data.get('count')}")
        print(f"   ✅ 前端代理正常")
    else:
        print(f"   ❌ 前端代理异常")
except Exception as e:
    print(f"   ❌ 错误: {e}")

# 测试旧的api-explorer路由（应该404）
print("\n3. 测试旧路由 /api-explorer (应该404):")
try:
    response = requests.get("http://localhost:8000/api-explorer")
    print(f"   状态码: {response.status_code}")
    if response.status_code == 404:
        print(f"   ✅ 旧路由已删除")
    else:
        print(f"   ⚠️  旧路由仍然存在")
except Exception as e:
    print(f"   错误: {e}")

# 测试新的api-explorer路由
print("\n4. 测试新路由 /api/api-explorer:")
try:
    response = requests.get("http://localhost:8000/api/api-explorer")
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   API数量: {data.get('count')}")
        print(f"   ✅ 新路由正常")
    else:
        print(f"   ❌ 新路由异常")
except Exception as e:
    print(f"   错误: {e}")
