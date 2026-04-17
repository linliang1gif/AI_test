"""
验证测试数据按钮功能
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_api_list():
    """测试API列表是否有数据"""
    print("1. 测试API列表...")
    response = requests.get(f"{BASE_URL}/api/apis")
    data = response.json()
    
    if data.get('success'):
        apis = data.get('apis', [])
        print(f"   ✅ 成功获取 {len(apis)} 个API")
        if apis:
            print(f"   示例API: {apis[0].get('method')} {apis[0].get('path')}")
        return apis
    else:
        print(f"   ❌ 失败: {data.get('message')}")
        return []

def test_smart_object_generation():
    """测试智能对象生成"""
    print("\n2. 测试智能对象生成...")
    
    # 模拟API参数schema
    test_schema = {
        "username": "string",
        "email": "string",
        "age": "integer",
        "is_active": "boolean"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/test-data/smart-object",
        json={
            "data_schema": test_schema,
            "context": {
                "api_path": "/api/users",
                "api_method": "POST"
            }
        }
    )
    
    data = response.json()
    
    if data.get('success'):
        print("   ✅ 成功生成测试数据")
        print(f"   生成的数据: {json.dumps(data.get('data'), indent=2, ensure_ascii=False)}")
        return True
    else:
        print(f"   ❌ 失败: {data.get('message')}")
        return False

def test_frontend_access():
    """测试前端是否可访问"""
    print("\n3. 测试前端访问...")
    try:
        response = requests.get("http://localhost:5174/", timeout=5)
        if response.status_code == 200:
            print("   ✅ 前端服务器运行正常")
            return True
        else:
            print(f"   ❌ 前端返回状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 无法访问前端: {e}")
        return False

def main():
    print("=" * 60)
    print("测试数据按钮功能验证")
    print("=" * 60)
    
    # 测试后端API
    apis = test_api_list()
    smart_ok = test_smart_object_generation()
    frontend_ok = test_frontend_access()
    
    print("\n" + "=" * 60)
    print("验证结果:")
    print("=" * 60)
    print(f"✅ 后端API列表: {'正常' if apis else '异常'}")
    print(f"✅ 智能数据生成: {'正常' if smart_ok else '异常'}")
    print(f"✅ 前端服务器: {'正常' if frontend_ok else '异常'}")
    
    if apis and smart_ok and frontend_ok:
        print("\n🎉 所有功能正常!")
        print("\n📝 使用说明:")
        print("1. 打开浏览器访问: http://localhost:5174/")
        print("2. 进入 'API管理' 页面")
        print("3. 在API列表中,每个API右侧有 '🏭 测试数据' 按钮")
        print("4. 点击按钮打开测试数据生成器")
        print("5. 点击 '🎲 生成数据' 自动生成测试数据")
        print("6. 点击 '✅ 使用此数据' 将数据填充到API测试中")
    else:
        print("\n⚠️ 部分功能异常,请检查日志")

if __name__ == "__main__":
    main()
