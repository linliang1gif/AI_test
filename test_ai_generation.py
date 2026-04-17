#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 AI 生成测试用例功能
"""

import requests
import json
import os

base_url = "http://localhost:8000"

print("🧪 测试 AI 生成测试用例功能")
print("=" * 60)

# 测试需求
requirement = """
用户登录功能需求文档

1. 功能概述
用户登录是系统的核心功能，允许用户通过用户名和密码进行身份验证。

2. 功能流程
2.1 正常流程
- 用户在登录页面输入用户名和密码
- 点击"登录"按钮
- 系统验证用户名和密码是否正确
- 验证成功后，生成JWT token并返回
- 前端保存token，跳转到首页

2.2 异常流程
- 用户名或密码为空：提示"用户名和密码不能为空"
- 用户名不存在：提示"用户名或密码错误"
- 密码错误：提示"用户名或密码错误"
- 账号被锁定：提示"账号已被锁定，请联系管理员"

3. 接口规范
- 接口路径：POST /api/auth/login
- 请求参数：
  * username: 用户名（必填，长度3-20）
  * password: 密码（必填，长度6-20）
- 响应格式：
  * 成功：{"code": 200, "token": "xxx", "message": "登录成功"}
  * 失败：{"code": 400, "message": "错误信息"}

4. 安全要求
- 密码需要加密传输
- 连续登录失败5次后锁定账号30分钟
- Token有效期为24小时
"""

# 创建临时需求文件
temp_file = "temp_requirement.txt"
with open(temp_file, 'w', encoding='utf-8') as f:
    f.write(requirement)

print(f"📝 需求文档已创建: {temp_file}")
print(f"\n🔄 正在调用 AI 生成测试用例...")

try:
    # 上传文件
    with open(temp_file, 'rb') as f:
        files = {'file': (temp_file, f, 'text/plain')}
        response = requests.post(
            f"{base_url}/api/testcases/generate",
            files=files,
            timeout=60
        )
    
    print(f"\n状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ 生成成功!")
        print(f"📊 生成了 {result.get('count', 0)} 个测试用例")
        
        test_cases = result.get('testCases', [])
        for i, tc in enumerate(test_cases[:5], 1):  # 只显示前5个
            print(f"\n--- 测试用例 {i} ---")
            print(f"标题: {tc.get('title', 'N/A')}")
            print(f"模块: {tc.get('module', 'N/A')}")
            print(f"优先级: {tc.get('priority', 'N/A')}")
            print(f"类型: {tc.get('type', 'N/A')}")
            print(f"数据类型: {tc.get('data_type', 'N/A')}")
            print(f"预期行为: {tc.get('expected_behavior', 'N/A')}")
            
            steps = tc.get('steps', [])
            if steps:
                print(f"步骤数: {len(steps)}")
                for j, step in enumerate(steps[:2], 1):  # 只显示前2个步骤
                    print(f"  {j}. {step}")
                if len(steps) > 2:
                    print(f"  ... 还有 {len(steps) - 2} 个步骤")
        
        if len(test_cases) > 5:
            print(f"\n... 还有 {len(test_cases) - 5} 个测试用例")
    else:
        print(f"\n❌ 失败")
        print(f"响应: {response.text}")
        
except Exception as e:
    print(f"❌ 错误: {e}")
finally:
    # 清理临时文件
    if os.path.exists(temp_file):
        os.remove(temp_file)
        print(f"\n🗑️  已删除临时文件: {temp_file}")

print("\n" + "=" * 60)
