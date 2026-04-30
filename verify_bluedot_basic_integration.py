#!/usr/bin/env python3
"""
验证蓝点基础接入（步骤1-3）
"""

import requests
import json

BACKEND_URL = "http://localhost:8000"
PROJECT_ID = 8

print("="*80)
print(" " * 25 + "蓝点基础接入验证")
print("="*80)

success_count = 0
total_count = 3

# 验证1: 项目存在
print("\n[1/3] 验证项目...")
try:
    response = requests.get(f"{BACKEND_URL}/api/v2/projects/{PROJECT_ID}", timeout=10)
    if response.status_code == 200:
        project = response.json()
        if project.get("name") == "蓝点回收系统":
            print(f"✓ 项目验证成功")
            print(f"  项目ID: {project.get('id')}")
            print(f"  项目名称: {project.get('name')}")
            print(f"  项目描述: {project.get('description')}")
            success_count += 1
        else:
            print(f"✗ 项目名称不匹配: {project.get('name')}")
    else:
        print(f"✗ 项目查询失败: {response.status_code}")
except Exception as e:
    print(f"✗ 项目验证异常: {e}")

# 验证2: 环境存在
print("\n[2/3] 验证环境...")
try:
    response = requests.get(f"{BACKEND_URL}/api/v2/projects/{PROJECT_ID}/environments", timeout=10)
    if response.status_code == 200:
        environments = response.json()
        test_env = next((env for env in environments if env.get("name") == "test"), None)
        if test_env:
            print(f"✓ 环境验证成功")
            print(f"  环境ID: {test_env.get('id')}")
            print(f"  环境名称: {test_env.get('name')}")
            print(f"  Base URL: {test_env.get('base_url')}")
            success_count += 1
        else:
            print(f"✗ 未找到test环境")
    else:
        print(f"✗ 环境查询失败: {response.status_code}")
except Exception as e:
    print(f"✗ 环境验证异常: {e}")

# 验证3: 鉴权配置存在
print("\n[3/3] 验证鉴权配置...")
try:
    # 先获取环境ID
    env_response = requests.get(f"{BACKEND_URL}/api/v2/projects/{PROJECT_ID}/environments", timeout=10)
    if env_response.status_code == 200:
        environments = env_response.json()
        test_env = next((env for env in environments if env.get("name") == "test"), None)
        if test_env:
            env_id = test_env.get('id')
            # 查询该环境的鉴权配置
            response = requests.get(f"{BACKEND_URL}/api/v2/environments/{env_id}/auth-profile", timeout=10)
            if response.status_code == 200:
                auth_profile = response.json()
                print(f"✓ 鉴权配置验证成功")
                print(f"  鉴权ID: {auth_profile.get('id')}")
                print(f"  鉴权名称: {auth_profile.get('name')}")
                print(f"  鉴权类型: {auth_profile.get('auth_type')}")
                success_count += 1
            else:
                print(f"✗ 鉴权配置查询失败: {response.status_code}")
        else:
            print(f"✗ 未找到test环境")
    else:
        print(f"✗ 环境查询失败: {env_response.status_code}")
except Exception as e:
    print(f"✗ 鉴权配置验证异常: {e}")

# 总结
print("\n" + "="*80)
print(" " * 30 + "验证总结")
print("="*80)
print(f"\n总验证项: {total_count}")
print(f"成功: {success_count} ✓")
print(f"失败: {total_count - success_count} ✗")
print(f"成功率: {success_count / total_count * 100:.1f}%")

if success_count == total_count:
    print("\n" + "="*80)
    print(" " * 25 + "✓ 基础接入验证成功")
    print("="*80)
    print("\n蓝点项目的基础架构已在平台中建立！")
    print("\n下一步:")
    print("  1. 访问前端查看项目: http://localhost:5173")
    print("  2. 获取OpenAPI文件继续完整接入")
    print("  3. 或手动创建API和测试用例")
    print("="*80)
else:
    print("\n" + "="*80)
    print(" " * 25 + "✗ 验证未完全通过")
    print("="*80)
    print("\n请检查失败的验证项")
    print("="*80)

exit(0 if success_count == total_count else 1)
