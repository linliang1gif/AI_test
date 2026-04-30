"""测试配置热更新"""
import requests
import json

BASE_URL = "http://localhost:8000"

def get_current_config():
    """获取当前配置"""
    response = requests.get(f"{BASE_URL}/api/ai/config")
    return response.json()

def update_config(updates):
    """更新配置"""
    response = requests.post(
        f"{BASE_URL}/api/ai/config/update",
        json={"updates": updates}
    )
    return response.json()

if __name__ == "__main__":
    print("=== 测试配置热更新 ===\n")
    
    # 1. 获取当前配置
    print("1. 获取当前配置")
    config_before = get_current_config()
    print(f"   测试用例生成: {config_before['module_configs']['testcase_generation']}")
    
    # 2. 更新配置
    print("\n2. 更新配置（切换到 ollama）")
    updates = {
        "TESTCASE_GENERATION_AI_PROVIDER": "ollama",
        "TESTCASE_GENERATION_AI_MODEL": "qwen2.5-coder:latest"
    }
    result = update_config(updates)
    print(f"   结果: {result['message']}")
    
    # 3. 立即获取配置，验证是否生效
    print("\n3. 验证配置是否立即生效")
    config_after = get_current_config()
    print(f"   测试用例生成: {config_after['module_configs']['testcase_generation']}")
    
    # 4. 对比
    print("\n4. 对比结果")
    if config_after['module_configs']['testcase_generation'] == {
        'provider': 'ollama',
        'model': 'qwen2.5-coder:latest'
    }:
        print("   ✅ 配置热更新成功！无需重启服务")
    else:
        print("   ❌ 配置未生效，可能需要重启服务")
    
    # 5. 恢复原配置
    print("\n5. 恢复原配置")
    restore_updates = {
        "TESTCASE_GENERATION_AI_PROVIDER": config_before['module_configs']['testcase_generation']['provider'],
        "TESTCASE_GENERATION_AI_MODEL": config_before['module_configs']['testcase_generation']['model']
    }
    result = update_config(restore_updates)
    print(f"   结果: {result['message']}")
    
    config_restored = get_current_config()
    print(f"   测试用例生成: {config_restored['module_configs']['testcase_generation']}")
    
    print("\n" + "="*50)
    print("✅ 热更新测试完成")
