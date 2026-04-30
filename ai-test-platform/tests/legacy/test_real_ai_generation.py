#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试真实的AI测试用例生成功能
"""

import requests
import io

def test_real_ai_generation():
    """测试真实的AI生成"""
    print("=" * 60)
    print("🧪 测试真实AI测试用例生成")
    print("=" * 60)
    
    # 创建一个真实的需求文档
    requirement_content = """
# 电商平台用户管理系统需求文档

版本: v1.0.0

## 概述
电商平台用户管理系统负责处理用户注册、登录、个人信息管理等核心功能。

## 功能需求

### 1. 用户注册模块
用户可以通过以下方式注册:
- 手机号注册: 需要验证手机号有效性
- 邮箱注册: 需要验证邮箱格式
- 第三方登录: 支持微信、QQ登录

注册规则:
- 用户名长度3-20个字符
- 密码至少8位,包含字母和数字
- 手机号必须是有效的中国大陆手机号
- 邮箱格式必须正确

### 2. 用户登录模块
支持多种登录方式:
- 用户名/手机号/邮箱 + 密码登录
- 短信验证码登录
- 第三方账号登录

安全规则:
- 连续登录失败3次锁定账户30分钟
- 支持记住登录状态(7天)
- 登录成功后生成JWT token

### 3. 个人信息管理模块
用户可以管理以下信息:
- 基本信息: 昵称、头像、性别、生日
- 联系方式: 手机号、邮箱、地址
- 安全设置: 修改密码、绑定手机、绑定邮箱

操作规则:
- 修改手机号需要验证原手机号
- 修改密码需要验证原密码
- 头像文件大小不超过2MB

### 4. 收货地址管理模块
用户可以管理收货地址:
- 添加新地址
- 编辑已有地址
- 删除地址
- 设置默认地址

地址规则:
- 每个用户最多20个地址
- 必须有一个默认地址
- 地址信息包括: 收货人、手机号、省市区、详细地址

## 接口需求

### 用户注册接口
- POST /api/user/register
- 参数: username, password, phone, email, code
- 返回: 注册结果、用户ID、token

### 用户登录接口
- POST /api/user/login
- 参数: account, password, remember_me
- 返回: token、用户信息

### 获取用户信息接口
- GET /api/user/profile
- 参数: 无(需要token)
- 返回: 用户详细信息

### 更新用户信息接口
- PUT /api/user/profile
- 参数: nickname, avatar, gender, birthday
- 返回: 更新结果

### 修改密码接口
- POST /api/user/change-password
- 参数: old_password, new_password, confirm_password
- 返回: 修改结果

### 地址管理接口
- GET /api/user/addresses - 获取地址列表
- POST /api/user/addresses - 添加地址
- PUT /api/user/addresses/{id} - 更新地址
- DELETE /api/user/addresses/{id} - 删除地址
- POST /api/user/addresses/{id}/default - 设置默认地址

## 业务规则
1. 用户名必须唯一
2. 手机号和邮箱不能重复注册
3. 密码必须加密存储
4. 用户操作需要记录日志
5. 敏感操作需要二次验证

## 非功能需求
- 响应时间: 接口响应时间不超过2秒
- 并发支持: 支持1000+并发用户
- 数据安全: 敏感数据加密存储
- 可用性: 系统可用性99.9%
""".encode('utf-8')
    
    files = {
        'file': ('电商用户管理需求.txt', io.BytesIO(requirement_content), 'text/plain')
    }
    
    try:
        print("\n📤 发送请求到后端...")
        print("   文档大小:", len(requirement_content), "bytes")
        
        response = requests.post(
            "http://localhost:8000/api/testcases/generate",
            files=files,
            timeout=120  # AI生成可能需要较长时间
        )
        
        print(f"\n📥 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                print(f"\n✅ AI生成成功!")
                print(f"\n📊 生成统计:")
                print(f"  - 测试用例数量: {result.get('count')}")
                
                if 'stats' in result:
                    stats = result['stats']
                    print(f"  - 功能模块: {stats.get('modules')}")
                    print(f"  - 测试点: {stats.get('testpoints')}")
                    print(f"  - 测试场景: {stats.get('scenarios')}")
                
                print(f"\n📝 生成的测试用例示例:")
                testcases = result.get('testCases', [])
                for i, tc in enumerate(testcases[:3], 1):  # 显示前3个
                    print(f"\n  {i}. {tc.get('title')}")
                    print(f"     模块: {tc.get('module')}")
                    print(f"     优先级: {tc.get('priority')}")
                    print(f"     测试点: {tc.get('testpoint', 'N/A')}")
                    print(f"     步骤数: {len(tc.get('steps', []))}")
                
                if len(testcases) > 3:
                    print(f"\n  ... 还有 {len(testcases) - 3} 个测试用例")
                
                return True
            else:
                print(f"\n❌ 生成失败: {result.get('message')}")
                print(f"   错误: {result.get('error')}")
                return False
        else:
            print(f"\n❌ 请求失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n🚀 开始测试真实AI生成功能...\n")
    
    success = test_real_ai_generation()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 测试通过! AI生成功能正常工作!")
        print("\n💡 提示:")
        print("  - 现在可以在前端上传需求文档")
        print("  - AI会自动解析文档并生成测试用例")
        print("  - 生成的用例包含详细的测试步骤和预期结果")
    else:
        print("⚠️  测试失败,请检查:")
        print("  - 后端服务是否正常运行")
        print("  - AI模块是否正确导入")
        print("  - Ollama服务是否可用")
    print("=" * 60)
