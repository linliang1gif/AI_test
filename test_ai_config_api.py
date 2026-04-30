"""测试 AI 配置 API"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_get_providers():
    """测试获取提供商列表"""
    print("\n=== 测试获取提供商列表 ===")
    response = requests.get(f"{BASE_URL}/api/ai/providers")
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"提供商数量: {len(data.get('providers', []))}")
    print(f"默认提供商: {data.get('default')}")
    for provider in data.get('providers', []):
        print(f"  - {provider['name']}: {provider['status']} ({len(provider.get('models', []))} 个模型)")
    return data

def test_get_config():
    """测试获取配置"""
    print("\n=== 测试获取配置 ===")
    response = requests.get(f"{BASE_URL}/api/ai/config")
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"默认提供商: {data.get('default_provider')}")
    print(f"默认模型: {data.get('default_model')}")
    print(f"模块配置:")
    for module_id, config in data.get('module_configs', {}).items():
        print(f"  - {module_id}: {config.get('provider')} / {config.get('model')}")
    print(f"可用模块数量: {len(data.get('available_modules', []))}")
    return data

def test_update_config():
    """测试更新配置"""
    print("\n=== 测试更新配置 ===")
    
    # 测试更新数据
    updates = {
        "TESTCASE_GENERATION_AI_PROVIDER": "deepseek",
        "TESTCASE_GENERATION_AI_MODEL": "deepseek-chat",
        "SCRIPT_GENERATION_AI_PROVIDER": "deepseek",
        "SCRIPT_GENERATION_AI_MODEL": "deepseek-coder"
    }
    
    print(f"更新数据: {json.dumps(updates, indent=2, ensure_ascii=False)}")
    
    response = requests.post(
        f"{BASE_URL}/api/ai/config/update",
        json={"updates": updates}
    )
    
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"结果: {json.dumps(data, indent=2, ensure_ascii=False)}")
    return data

if __name__ == "__main__":
    try:
        # 测试获取提供商
        providers_data = test_get_providers()
        
        # 测试获取配置
        config_data = test_get_config()
        
        # 测试更新配置
        update_result = test_update_config()
        
        print("\n" + "="*50)
        print("✅ 所有测试完成")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
