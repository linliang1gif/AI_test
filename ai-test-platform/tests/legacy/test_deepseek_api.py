#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试DeepSeek API连接和AI生成
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from ai.ai_client import get_ai_client
from test_design.module_splitter import ModuleSplitter

def test_deepseek_connection():
    """测试DeepSeek API连接"""
    print("=" * 60)
    print("测试 DeepSeek API 连接")
    print("=" * 60)
    
    try:
        # 获取AI客户端（强制使用真实API，不使用mock）
        ai_client = get_ai_client(use_mock=False)
        
        print(f"\n使用的AI提供商: {ai_client.provider}")
        print(f"使用的模型: {ai_client.ai_config['model']}")
        print(f"API地址: {ai_client.ai_config['base_url']}")
        
        # 测试简单的文本生成
        print("\n测试1: 简单文本生成...")
        response = ai_client.generate_text(
            prompt="请用一句话介绍什么是软件测试",
            temperature=0.3
        )
        print(f"✅ AI响应: {response[:100]}...")
        
        # 测试JSON生成
        print("\n测试2: JSON格式生成...")
        response = ai_client.generate_json(
            prompt="请生成一个包含3个功能模块的JSON，每个模块包含name和description字段",
            temperature=0.3
        )
        print(f"✅ AI响应类型: {type(response)}")
        print(f"✅ 响应内容: {response}")
        
        print("\n✅ DeepSeek API 连接测试成功!")
        return True
        
    except Exception as e:
        print(f"\n❌ DeepSeek API 连接失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_real_module_generation():
    """测试真实的模块生成"""
    print("\n" + "=" * 60)
    print("测试真实的AI模块生成")
    print("=" * 60)
    
    requirement = """
# 电商系统需求文档

## 功能需求

### 用户管理
- 用户注册和登录
- 个人信息管理
- 收货地址管理

### 商品管理
- 商品浏览和搜索
- 商品详情查看
- 商品分类管理

### 订单管理
- 购物车管理
- 订单创建和支付
- 订单查询和取消

### 支付管理
- 多种支付方式
- 支付状态查询
- 退款处理
"""
    
    try:
        print("\n正在调用DeepSeek API生成功能模块...")
        splitter = ModuleSplitter()
        modules = splitter.split_modules(requirement)
        
        print(f"\n✅ 成功识别 {len(modules)} 个功能模块:")
        for i, module in enumerate(modules, 1):
            print(f"\n模块{i}: {module['name']}")
            print(f"  描述: {module['description']}")
            print(f"  功能: {', '.join(module.get('functions', [])[:3])}")
            print(f"  优先级: {module.get('priority', 'N/A')}")
        
        print("\n✅ 真实AI模块生成测试成功!")
        return True
        
    except Exception as e:
        print(f"\n❌ 模块生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 DeepSeek API 测试")
    print("=" * 60)
    
    # 测试API连接
    if not test_deepseek_connection():
        print("\n❌ API连接测试失败，请检查:")
        print("  1. API Key是否正确")
        print("  2. 网络连接是否正常")
        print("  3. DeepSeek服务是否可用")
        return
    
    # 测试真实模块生成
    if not test_real_module_generation():
        print("\n❌ 模块生成测试失败")
        return
    
    print("\n" + "=" * 60)
    print("🎉 所有测试通过! DeepSeek API工作正常")
    print("=" * 60)
    print("\n现在可以:")
    print("  1. 启动后端服务: py backend_api_server.py")
    print("  2. 上传需求文档使用真实AI生成测试用例")

if __name__ == "__main__":
    main()
