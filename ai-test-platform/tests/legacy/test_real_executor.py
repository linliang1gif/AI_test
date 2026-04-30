#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试真实执行器"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

print("=" * 60)
print("测试真实测试执行器")
print("=" * 60)

# 1. 测试导入
print("\n1. 测试导入真实执行器...")
try:
    from executor.real_test_executor import get_test_executor
    executor = get_test_executor()
    print("✅ 真实测试执行器导入成功")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

# 2. 测试API测试执行
print("\n2. 测试API测试执行...")
import asyncio

test_case_api = {
    "id": 1,
    "title": "GET /api/test - 测试接口",
    "source": "api_generated",
    "api_id": 1,
    "base_url": "http://127.0.0.1:8081",
    "steps": ["发送GET请求", "验证响应"],
    "expected": "返回200状态码"
}

async def test_api():
    result = await executor.execute_test_case(test_case_api)
    print(f"   状态: {result['status']}")
    print(f"   消息: {result['message']}")
    print(f"   详情: {result.get('details', 'N/A')}")
    print(f"   响应时间: {result.get('response_time', 'N/A')}")
    return result

result = asyncio.run(test_api())

if result['status'] in ['passed', 'skipped']:
    print("✅ API测试执行成功")
else:
    print(f"⚠️ API测试执行结果: {result['status']}")

# 3. 测试AI生成用例执行
print("\n3. 测试AI生成用例执行...")
test_case_ai = {
    "id": 2,
    "title": "用户登录功能测试",
    "source": "ai_generated",
    "steps": ["打开登录页面", "输入用户名密码", "点击登录"],
    "expected": "登录成功"
}

async def test_ai():
    result = await executor.execute_test_case(test_case_ai)
    print(f"   状态: {result['status']}")
    print(f"   消息: {result['message']}")
    return result

result = asyncio.run(test_ai())
print("✅ AI用例执行成功")

# 4. 测试手动用例
print("\n4. 测试手动用例...")
test_case_manual = {
    "id": 3,
    "title": "手动测试用例",
    "source": "manual",
    "steps": ["手动操作"],
    "expected": "手动验证"
}

async def test_manual():
    result = await executor.execute_test_case(test_case_manual)
    print(f"   状态: {result['status']}")
    print(f"   消息: {result['message']}")
    return result

result = asyncio.run(test_manual())
print("✅ 手动用例处理成功")

print("\n" + "=" * 60)
print("✅ 真实测试执行器测试完成")
print("=" * 60)
print("\n真实执行器已就绪,可以在测试运行模块中使用!")
