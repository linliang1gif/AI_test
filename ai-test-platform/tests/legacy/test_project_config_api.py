#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试项目配置API
验证P0-2功能
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_create_project():
    """测试创建项目"""
    print("\n" + "=" * 60)
    print("测试: 创建项目")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/v2/projects"
    data = {
        "name": "蓝点回收系统",
        "description": "蓝点回收系统后端API测试项目",
        "owner": "测试团队",
        "team": "QA团队"
    }
    
    response = requests.post(url, json=data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    if response.status_code == 201:
        print("✅ 创建项目成功")
        return response.json()['id']
    else:
        print("❌ 创建项目失败")
        return None


def test_get_projects():
    """测试获取项目列表"""
    print("\n" + "=" * 60)
    print("测试: 获取项目列表")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/v2/projects"
    response = requests.get(url)
    
    print(f"状态码: {response.status_code}")
    projects = response.json()
    print(f"项目数量: {len(projects)}")
    
    for proj in projects:
        print(f"  - {proj['name']} (ID: {proj['id']})")
    
    if response.status_code == 200:
        print("✅ 获取项目列表成功")
    else:
        print("❌ 获取项目列表失败")


def test_create_environment(project_id):
    """测试创建环境"""
    print("\n" + "=" * 60)
    print("测试: 创建环境")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/v2/environments"
    data = {
        "project_id": project_id,
        "name": "test",
        "base_url": "http://localhost:8080",
        "is_protected": False,
        "allow_write": True,
        "timeout_seconds": 30,
        "retry_count": 2
    }
    
    response = requests.post(url, json=data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    if response.status_code == 201:
        print("✅ 创建环境成功")
        return response.json()['id']
    else:
        print("❌ 创建环境失败")
        return None


def test_get_project_environments(project_id):
    """测试获取项目环境"""
    print("\n" + "=" * 60)
    print("测试: 获取项目环境")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/v2/projects/{project_id}/environments"
    response = requests.get(url)
    
    print(f"状态码: {response.status_code}")
    environments = response.json()
    print(f"环境数量: {len(environments)}")
    
    for env in environments:
        print(f"  - {env['name']}: {env['base_url']}")
    
    if response.status_code == 200:
        print("✅ 获取项目环境成功")
    else:
        print("❌ 获取项目环境失败")


def test_create_auth_profile(env_id):
    """测试创建鉴权配置"""
    print("\n" + "=" * 60)
    print("测试: 创建鉴权配置")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/v2/auth-profiles"
    data = {
        "environment_id": env_id,
        "auth_type": "bearer",
        "auth_config": {
            "token": "test_token_1234567890abcdef"
        },
        "default_headers": {
            "Content-Type": "application/json"
        }
    }
    
    response = requests.post(url, json=data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    if response.status_code == 201:
        print("✅ 创建鉴权配置成功")
        print("⚠️  注意: token已脱敏显示")
        return response.json()['id']
    else:
        print("❌ 创建鉴权配置失败")
        return None


def test_get_environment_auth(env_id):
    """测试获取环境鉴权配置"""
    print("\n" + "=" * 60)
    print("测试: 获取环境鉴权配置")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/v2/environments/{env_id}/auth-profile"
    response = requests.get(url)
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    if response.status_code == 200:
        print("✅ 获取鉴权配置成功")
        print("⚠️  注意: 敏感信息已脱敏")
    else:
        print("❌ 获取鉴权配置失败")


def main():
    """主测试流程"""
    print("=" * 60)
    print("P0-2 项目配置API测试")
    print("=" * 60)
    print(f"后端地址: {BASE_URL}")
    print("请确保后端服务已启动: python backend_api_server.py")
    
    input("\n按Enter键开始测试...")
    
    # 1. 创建项目
    project_id = test_create_project()
    if not project_id:
        print("\n❌ 测试中断: 创建项目失败")
        return
    
    # 2. 获取项目列表
    test_get_projects()
    
    # 3. 创建环境
    env_id = test_create_environment(project_id)
    if not env_id:
        print("\n❌ 测试中断: 创建环境失败")
        return
    
    # 4. 获取项目环境
    test_get_project_environments(project_id)
    
    # 5. 创建鉴权配置
    auth_id = test_create_auth_profile(env_id)
    if not auth_id:
        print("\n❌ 测试中断: 创建鉴权配置失败")
        return
    
    # 6. 获取环境鉴权配置
    test_get_environment_auth(env_id)
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成!")
    print("=" * 60)
    print(f"\n创建的资源:")
    print(f"  项目ID: {project_id}")
    print(f"  环境ID: {env_id}")
    print(f"  鉴权ID: {auth_id}")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到后端服务")
        print("请先启动后端: python backend_api_server.py")
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
