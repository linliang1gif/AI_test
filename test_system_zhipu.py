"""测试系统中的智谱AI集成"""
import sys
import os

# 添加ai-test-platform到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai-test-platform'))

from ai.ai_client import AIClient

def test_system_ai():
    """测试系统AI客户端"""
    print("=" * 60)
    print("🧪 测试系统AI客户端 (智谱AI)")
    print("=" * 60)
    
    # 创建AI客户端
    client = AIClient()
    
    print(f"📍 当前提供商: {client.provider}")
    print()
    
    # 测试文本生成
    print("📤 测试文本生成...")
    try:
        response = client.generate_text(
            prompt="请用一句话介绍什么是API测试",
            max_tokens=100
        )
        print("✅ 文本生成成功!")
        print(f"💬 回复: {response}")
        print()
    except Exception as e:
        print(f"❌ 文本生成失败: {e}")
        print()
        return False
    
    # 测试JSON生成
    print("📤 测试JSON生成...")
    try:
        response = client.generate_json(
            prompt="生成一个简单的测试用例,包含title和steps字段",
            max_tokens=200
        )
        print("✅ JSON生成成功!")
        print(f"📝 结果: {response}")
        print()
    except Exception as e:
        print(f"❌ JSON生成失败: {e}")
        print()
        return False
    
    return True

if __name__ == "__main__":
    success = test_system_ai()
    print("=" * 60)
    if success:
        print("✅ 系统AI集成测试通过")
    else:
        print("❌ 系统AI集成测试失败")
    print("=" * 60)
