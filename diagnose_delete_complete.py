"""
完整诊断删除功能问题
"""
import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("删除功能完整诊断")
print("=" * 60)

# 1. 检查后端是否有batch-delete API
print("\n1. 检查批量删除API是否存在...")
try:
    response = requests.post(
        f"{BASE_URL}/api/testcases/batch-delete",
        json={"ids": [999]},  # 使用不存在的ID测试
        headers={"Content-Type": "application/json"}
    )
    print(f"   状态码: {response.status_code}")
    if response.status_code == 404:
        print("   ❌ API不存在 - 需要实现批量删除API")
    elif response.status_code == 422:
        print("   ⚠️ API存在但参数验证失败")
        print(f"   响应: {response.text}")
    else:
        print(f"   ✅ API存在")
        print(f"   响应: {response.json()}")
except Exception as e:
    print(f"   ❌ 请求失败: {e}")

# 2. 检查测试用例数据
print("\n2. 检查测试用例数据...")
try:
    response = requests.get(f"{BASE_URL}/api/test-cases")
    if response.status_code == 200:
        data = response.json()
        test_cases = data.get('data', [])
        print(f"   ✅ 共有 {len(test_cases)} 个测试用例")
        
        if test_cases:
            # 检查ID类型
            id_types = {}
            for tc in test_cases[:10]:  # 只检查前10个
                tc_id = tc.get('id')
                id_type = type(tc_id).__name__
                id_types[id_type] = id_types.get(id_type, 0) + 1
            
            print(f"   ID类型分布: {id_types}")
            
            # 显示前3个测试用例
            print("\n   前3个测试用例:")
            for tc in test_cases[:3]:
                print(f"   - ID: {tc.get('id')} ({type(tc.get('id')).__name__})")
                print(f"     标题: {tc.get('title', 'N/A')[:50]}")
    else:
        print(f"   ❌ 获取失败: {response.status_code}")
except Exception as e:
    print(f"   ❌ 请求失败: {e}")

# 3. 检查前端API配置
print("\n3. 检查前端API配置...")
api_js_path = "ai-test-platform/frontend/src/services/api.js"
try:
    with open(api_js_path, 'r', encoding='utf-8') as f:
        content = f.read()
        if 'batchDelete' in content:
            print("   ✅ 前端有batchDelete方法")
            # 提取batchDelete的URL
            import re
            match = re.search(r'batchDelete.*?request\(`([^`]+)`', content, re.DOTALL)
            if match:
                url = match.group(1)
                print(f"   调用URL: {url}")
        else:
            print("   ❌ 前端没有batchDelete方法")
except Exception as e:
    print(f"   ⚠️ 无法读取文件: {e}")

# 4. 检查后端是否有其他删除API
print("\n4. 检查其他可能的删除API...")
possible_endpoints = [
    "/api/test-cases/delete",
    "/api/testcases/delete",
    "/api/test-cases/batch-delete",
    "/api/testcases/batch-delete",
]

for endpoint in possible_endpoints:
    try:
        response = requests.post(
            f"{BASE_URL}{endpoint}",
            json={"ids": [999]},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code != 404:
            print(f"   ✅ 找到: {endpoint} (状态码: {response.status_code})")
    except:
        pass

print("\n" + "=" * 60)
print("诊断总结")
print("=" * 60)

print("""
根据诊断结果:

问题1: 后端批量删除API
  - 如果返回404: 需要在backend_api_server.py中实现批量删除API
  - 如果返回422: 需要修复参数验证(支持Union[int, str])
  - 如果返回200: API正常,问题在前端

问题2: 前端缓存
  - 即使代码已修改,浏览器可能还在使用旧代码
  - 解决方案: Ctrl + Shift + R 强制刷新

问题3: ID类型不一致
  - 如果同时有int和str类型的ID,需要统一处理
  - 后端应该支持 List[Union[int, str]]

下一步操作:
1. 如果API不存在 → 实现批量删除API
2. 如果API存在 → 清除浏览器缓存测试
3. 如果还有问题 → 检查后端日志
""")
