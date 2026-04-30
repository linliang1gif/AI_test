"""详细测试智谱AI在系统中的调用"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai-test-platform'))

from config.config import get_config, reload_config
from ai.ai_client import AIClient

def test_config():
    """测试配置加载"""
    print("=" * 60)
    print("🔧 测试配置加载")
    print("=" * 60)
    
    # 重新加载配置
    config = reload_config()
    
    print(f"默认提供商: {config.ai.default_provider}")
    print(f"默认模型: {config.ai.default_model}")
    print(f"OpenAI Base URL: {config.ai.openai_base_url}")
    print(f"OpenAI API Key: {config.ai.openai_api_key[:20]}...")
    print()
    
    # 获取OpenAI提供商配置
    ai_config = config.get_ai_config_for_provider("openai")
    print("OpenAI提供商配置:")
    for key, value in ai_config.items():
        if key == "api_key":
            print(f"  {key}: {value[:20]}...")
        else:
            print(f"  {key}: {value}")
    print()
    
    return config

def test_ai_client_direct():
    """直接测试AI客户端"""
    print("=" * 60)
    print("🧪 测试AI客户端直接调用")
    print("=" * 60)
    
    try:
        client = AIClient(provider="openai")
        print(f"✅ AI客户端创建成功")
        print(f"   提供商: {client.provider}")
        print()
        
        print("📤 发送测试请求...")
        response = client.generate_text(
            prompt="请用一句话介绍什么是API测试",
            system_prompt="你是一个专业的测试工程师",
            temperature=0.3,
            max_tokens=100
        )
        
        print("✅ 请求成功!")
        print(f"💬 响应: {response}")
        print()
        return True
        
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ai_client_json():
    """测试JSON生成"""
    print("=" * 60)
    print("🧪 测试JSON生成")
    print("=" * 60)
    
    try:
        client = AIClient(provider="openai")
        
        prompt = """请生成一个简单的测试用例,格式如下:
{
  "title": "测试用例标题",
  "module": "模块名称",
  "priority": "high",
  "steps": ["步骤1", "步骤2"],
  "expected": "预期结果",
  "type": "功能测试"
}

只返回JSON,不要其他内容。"""
        
        print("📤 发送JSON生成请求...")
        response = client.generate_text(
            prompt=prompt,
            system_prompt="你是一个专业的测试工程师,只返回JSON格式的数据,不要任何其他文字说明。",
            temperature=0.3,
            max_tokens=500
        )
        
        print("✅ 请求成功!")
        print(f"📝 响应:\n{response}")
        print()
        
        # 尝试解析JSON
        import json
        response_clean = response.strip()
        if '```json' in response_clean:
            response_clean = response_clean.split('```json')[1].split('```')[0].strip()
        elif '```' in response_clean:
            response_clean = response_clean.split('```')[1].split('```')[0].strip()
        
        data = json.loads(response_clean)
        print("✅ JSON解析成功!")
        print(f"   标题: {data.get('title')}")
        print()
        return True
        
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n")
    print("🚀 开始智谱AI详细测试")
    print("\n")
    
    # 测试1: 配置加载
    config = test_config()
    
    # 测试2: 直接调用
    success1 = test_ai_client_direct()
    
    # 测试3: JSON生成
    success2 = test_ai_client_json()
    
    print("=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    print(f"配置加载: ✅")
    print(f"文本生成: {'✅' if success1 else '❌'}")
    print(f"JSON生成: {'✅' if success2 else '❌'}")
    print("=" * 60)
