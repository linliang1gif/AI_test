#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Test Platform - 完整流程测试
演示从需求到测试报告的完整流程
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from config.config import get_config
from ai.ai_client import get_ai_client
from ai_core.skills.pytest_skill import PytestSkill

def test_ai_client():
    """测试AI客户端"""
    print("\n🧠 测试AI客户端...")

    client = get_ai_client(use_mock=True)
    response = client.generate_text("生成测试策略")

    print(f"✅ AI响应: {response[:100]}...")
    return True

def test_pytest_skill():
    """测试Pytest技能"""
    print("\n🧪 测试Pytest技能...")

    skill = PytestSkill()

    # 创建测试文件
    test_dir = Path(__file__).parent / "output" / "tests"
    test_dir.mkdir(parents=True, exist_ok=True)

    test_file = test_dir / "test_sample.py"
    test_file.write_text("""
def test_addition():
    assert 1 + 1 == 2

def test_subtraction():
    assert 5 - 3 == 2
""")

    result = skill.run(str(test_file))

    print(f"✅ 测试执行: {'成功' if result['success'] else '失败'}")
    return result['success']

def test_config():
    """测试配置"""
    print("\n⚙️  测试配置...")

    config = get_config()
    print(f"  输出目录: {config.paths.output_dir}")
    print(f"  测试目录: {config.paths.tests_dir}")
    print(f"  AI提供商: {config.ai.default_provider}")

    print("✅ 配置加载成功")
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("🚀 AI Test Platform - 完整流程测试")
    print("=" * 60)

    tests = [
        ("配置测试", test_config),
        ("AI客户端测试", test_ai_client),
        ("Pytest技能测试", test_pytest_skill),
    ]

    results = {}

    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"❌ {name}失败: {e}")
            results[name] = False

    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)

    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name}: {status}")

    total = len(results)
    passed = sum(1 for r in results.values() if r)

    print(f"\n总计: {passed}/{total} 通过")
    print("=" * 60)

if __name__ == "__main__":
    main()
