"""初始化测试数据"""
import requests
import json
import time

print("=" * 60)
print("初始化AI测试平台数据")
print("=" * 60)
print()

base_url = "http://localhost:8000"

# 1. 检查现有数据
print("1. 检查现有数据...")
try:
    # 检查测试用例
    response = requests.get(f"{base_url}/api/test-cases")
    test_cases = response.json().get('test_cases', [])
    print(f"   当前测试用例数: {len(test_cases)}")
    
    # 检查自动化脚本
    response = requests.get(f"{base_url}/api/automation/scripts")
    scripts = response.json().get('scripts', [])
    print(f"   当前自动化脚本数: {len(scripts)}")
    
    # 检查API
    response = requests.get(f"{base_url}/api/apis")
    apis = response.json().get('apis', [])
    print(f"   当前API数: {len(apis)}")
    
except Exception as e:
    print(f"❌ 检查失败: {e}")
    exit(1)

print()

# 2. 如果没有测试用例，创建示例测试用例
if len(test_cases) == 0:
    print("2. 创建示例测试用例...")
    
    sample_testcases = [
        {
            "title": "用户登录功能测试",
            "module": "用户认证",
            "priority": "high",
            "status": "passed",
            "type": "API测试",
            "steps": [
                "发送POST请求到 /api/auth/login",
                "传入用户名和密码",
                "验证返回token"
            ],
            "expected": "返回状态码200，包含token",
            "data_type": "valid",
            "expected_behavior": "success"
        },
        {
            "title": "获取用户信息测试",
            "module": "用户管理",
            "priority": "medium",
            "status": "passed",
            "type": "API测试",
            "steps": [
                "发送GET请求到 /api/user/info",
                "携带认证token",
                "验证返回用户信息"
            ],
            "expected": "返回状态码200，包含用户信息",
            "data_type": "valid",
            "expected_behavior": "success"
        },
        {
            "title": "创建订单测试",
            "module": "订单管理",
            "priority": "high",
            "status": "passed",
            "type": "API测试",
            "steps": [
                "发送POST请求到 /api/orders",
                "传入订单信息",
                "验证订单创建成功"
            ],
            "expected": "返回状态码201，包含订单ID",
            "data_type": "valid",
            "expected_behavior": "success"
        }
    ]
    
    for tc in sample_testcases:
        try:
            response = requests.post(
                f"{base_url}/api/test-cases",
                json=tc,
                timeout=10
            )
            if response.status_code == 200:
                print(f"   ✅ 创建测试用例: {tc['title']}")
            else:
                print(f"   ⚠️  创建失败: {tc['title']} - {response.status_code}")
        except Exception as e:
            print(f"   ❌ 创建失败: {tc['title']} - {e}")
    
    print()

# 3. 如果没有自动化脚本，创建示例脚本
if len(scripts) == 0:
    print("3. 创建示例自动化脚本...")
    
    # 方法1: 直接创建脚本数据
    sample_scripts = [
        {
            "name": "test_user_authentication.py",
            "description": "用户认证功能自动化测试脚本",
            "framework": "pytest",
            "language": "Python",
            "status": "ready",
            "testCount": 5,
            "content": '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用户认证功能自动化测试脚本"""

import pytest
import requests

class TestUserAuthentication:
    def setup_method(self):
        self.base_url = "http://localhost:8000"
        
    def test_user_login(self):
        """测试用户登录"""
        response = requests.post(f"{self.base_url}/api/auth/login")
        assert response.status_code in [200, 404]
        
    def test_get_user_info(self):
        """测试获取用户信息"""
        response = requests.get(f"{self.base_url}/api/user/info")
        assert response.status_code in [200, 404]
'''
        },
        {
            "name": "test_api_endpoints.py",
            "description": "API接口自动化测试脚本",
            "framework": "pytest",
            "language": "Python",
            "status": "ready",
            "testCount": 8,
            "content": '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""API接口自动化测试脚本"""

import pytest
import requests

class TestApiEndpoints:
    def setup_method(self):
        self.base_url = "http://localhost:8000"
        
    def test_health_check(self):
        """测试健康检查"""
        response = requests.get(f"{self.base_url}/health")
        assert response.status_code == 200
'''
        }
    ]
    
    # 直接写入数据文件
    try:
        import json
        from pathlib import Path
        
        data_file = Path("ai-test-platform/data/platform_data.json")
        if data_file.exists():
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 添加脚本数据
            if 'scripts' not in data:
                data['scripts'] = []
            
            for i, script in enumerate(sample_scripts, 1):
                script['id'] = i
                script['lastGenerated'] = "2024-03-24"
                data['scripts'].append(script)
            
            # 保存
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"   ✅ 创建了 {len(sample_scripts)} 个示例脚本")
        else:
            print("   ❌ 数据文件不存在")
    except Exception as e:
        print(f"   ❌ 创建脚本失败: {e}")
    
    print()

# 4. 验证数据
print("4. 验证数据...")
try:
    # 重新检查
    response = requests.get(f"{base_url}/api/test-cases")
    test_cases = response.json().get('test_cases', [])
    print(f"   ✅ 测试用例数: {len(test_cases)}")
    
    response = requests.get(f"{base_url}/api/automation/scripts")
    scripts = response.json().get('scripts', [])
    print(f"   ✅ 自动化脚本数: {len(scripts)}")
    
except Exception as e:
    print(f"   ❌ 验证失败: {e}")

print()
print("=" * 60)
print("初始化完成！")
print("=" * 60)
print()
print("现在可以:")
print("1. 访问 http://localhost:5173")
print("2. 进入'测试用例'页面查看测试用例")
print("3. 进入'自动化脚本'页面查看脚本")
print("4. 尝试生成新的测试用例和脚本")
print()
print("如果还有问题，请告诉我具体哪个功能用不了！")
