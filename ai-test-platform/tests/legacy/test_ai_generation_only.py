#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""只测试AI生成功能"""

import requests
from pathlib import Path

BASE_URL = "http://127.0.0.1:8081"

def test_ai_generation():
    """测试AI生成测试用例"""
    print("🧪 测试AI生成功能\n")
    
    # 创建测试文档
    test_doc_path = Path("uploads/ai_test.txt")
    test_doc_path.parent.mkdir(exist_ok=True)
    
    test_content = """
    电商平台用户管理需求:
    1. 用户可以注册新账号
    2. 用户可以登录系统
    3. 用户可以修改个人信息
    4. 用户可以重置密码
    """
    
    with open(test_doc_path, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print("📤 上传文档并生成测试用例...")
    
    with open(test_doc_path, 'rb') as f:
        files = {'file': ('ai_test.txt', f, 'text/plain')}
        response = requests.post(f"{BASE_URL}/api/testcases/generate", files=files)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print(f"✅ 生成成功: {data.get('count')} 个测试用例\n")
            
            # 显示生成的测试用例
            for case in data.get('testCases', [])[:3]:
                print(f"📋 {case['title']}")
                print(f"   模块: {case['module']}")
                print(f"   优先级: {case['priority']}")
                print(f"   步骤: {', '.join(case['steps'][:2])}...")
                print()
        else:
            print(f"❌ 生成失败: {data.get('error')}")
    else:
        print(f"❌ 请求失败: {response.status_code}")

if __name__ == "__main__":
    test_ai_generation()
