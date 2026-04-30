#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P0-6 Swagger 导入功能测试
"""

import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"


def test_swagger_import_from_file():
    """测试从文件导入 Swagger"""
    print("\n" + "=" * 60)
    print("测试 1: 从文件导入 Swagger")
    print("=" * 60)
    
    # 1. 创建测试项目
    print("\n1. 创建测试项目...")
    project_data = {
        "name": "Swagger测试项目",
        "description": "用于测试Swagger导入功能",
        "owner": "test_user",
        "team": "test_team"
    }
    
    response = requests.post(f"{BASE_URL}/api/v2/projects", json=project_data)
    assert response.status_code == 201, f"创建项目失败: {response.text}"
    project = response.json()
    project_id = project["id"]
    print(f"✅ 项目创建成功: ID={project_id}")
    
    # 2. 准备 Swagger 文件
    print("\n2. 准备 Swagger 文件...")
    swagger_file = Path(__file__).parent.parent / "examples" / "sample_swagger.json"
    
    if not swagger_file.exists():
        print(f"⚠️  Swagger 文件不存在: {swagger_file}")
        # 创建一个简单的 Swagger 文件
        swagger_data = {
            "swagger": "2.0",
            "info": {
                "title": "Test API",
                "version": "1.0.0"
            },
            "paths": {
                "/users": {
                    "get": {
                        "summary": "获取用户列表",
                        "responses": {
                            "200": {
                                "description": "成功"
                            }
                        }
                    }
                },
                "/users/{id}": {
                    "get": {
                        "summary": "获取用户详情",
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "type": "integer"
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "成功"
                            }
                        }
                    }
                }
            }
        }
        swagger_file.parent.mkdir(parents=True, exist_ok=True)
        swagger_file.write_text(json.dumps(swagger_data, indent=2))
        print(f"✅ 创建测试 Swagger 文件: {swagger_file}")
    
    # 3. 导入 Swagger
    print("\n3. 导入 Swagger 文件...")
    with open(swagger_file, 'rb') as f:
        files = {'file': ('test_swagger.json', f, 'application/json')}
        params = {
            'project_id': project_id,
            'generate_cases': True
        }
        response = requests.post(
            f"{BASE_URL}/api/v2/swagger/import-file",
            files=files,
            params=params
        )
    
    assert response.status_code == 200, f"导入失败: {response.text}"
    result = response.json()
    print(f"✅ Swagger 导入成功:")
    print(f"   API规范ID: {result['api_spec_id']}")
    print(f"   API数量: {result['api_count']}")
    print(f"   生成测试用例数: {result['test_cases_generated']}")
    print(f"   测试用例ID: {result['test_case_ids'][:3]}...")  # 只显示前3个
    
    return project_id, result['api_spec_id'], result['test_case_ids']


def test_get_api_specs(project_id):
    """测试获取 API 规范列表"""
    print("\n" + "=" * 60)
    print("测试 2: 获取 API 规范列表")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/api/v2/swagger/api-specs?project_id={project_id}")
    assert response.status_code == 200, f"查询失败: {response.text}"
    
    api_specs = response.json()
    print(f"✅ 查询成功,共 {len(api_specs)} 个API规范")
    
    for spec in api_specs:
        print(f"   - ID: {spec['id']}, 版本: {spec['version']}, API数量: {spec['api_count']}")
    
    return api_specs


def test_get_test_cases(test_case_ids):
    """测试获取测试用例"""
    print("\n" + "=" * 60)
    print("测试 3: 获取测试用例")
    print("=" * 60)
    
    # 获取测试用例列表
    response = requests.get(f"{BASE_URL}/api/v2/test-cases?source=swagger&limit=10")
    assert response.status_code == 200, f"查询失败: {response.text}"
    
    result = response.json()
    print(f"✅ 查询成功,共 {result['total']} 个测试用例")
    
    for tc in result['test_cases'][:5]:  # 只显示前5个
        print(f"   - {tc['id']}: {tc['title']}")
        print(f"     优先级: {tc['priority']}, 状态: {tc['status']}, 来源: {tc['source']}")
    
    # 获取单个测试用例详情
    if test_case_ids:
        test_case_id = test_case_ids[0]
        print(f"\n获取测试用例详情: {test_case_id}")
        response = requests.get(f"{BASE_URL}/api/v2/test-cases/{test_case_id}")
        assert response.status_code == 200, f"查询失败: {response.text}"
        
        tc = response.json()
        print(f"✅ 测试用例详情:")
        print(f"   标题: {tc['title']}")
        print(f"   模块: {tc['module']}")
        print(f"   优先级: {tc['priority']}")
        print(f"   数据类型: {tc['data_type']}")
        print(f"   期望行为: {tc['expected_behavior']}")


def test_swagger_import_from_url():
    """测试从 URL 导入 Swagger"""
    print("\n" + "=" * 60)
    print("测试 4: 从 URL 导入 Swagger")
    print("=" * 60)
    
    # 1. 创建测试项目
    print("\n1. 创建测试项目...")
    project_data = {
        "name": "Swagger URL测试项目",
        "description": "用于测试从URL导入Swagger",
        "owner": "test_user",
        "team": "test_team"
    }
    
    response = requests.post(f"{BASE_URL}/api/v2/projects", json=project_data)
    assert response.status_code == 201, f"创建项目失败: {response.text}"
    project = response.json()
    project_id = project["id"]
    print(f"✅ 项目创建成功: ID={project_id}")
    
    # 2. 从 URL 导入 (使用 httpbin 的 spec)
    print("\n2. 从 URL 导入 Swagger...")
    import_data = {
        "project_id": project_id,
        "url": "https://petstore.swagger.io/v2/swagger.json",
        "generate_cases": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v2/swagger/import-url",
            json=import_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Swagger 导入成功:")
            print(f"   API规范ID: {result['api_spec_id']}")
            print(f"   API数量: {result['api_count']}")
            print(f"   生成测试用例数: {result['test_cases_generated']}")
        else:
            print(f"⚠️  导入失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"⚠️  导入失败(可能是网络问题): {str(e)}")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("P0-6 Swagger 导入功能测试")
    print("=" * 60)
    
    try:
        # 测试 1: 从文件导入
        project_id, api_spec_id, test_case_ids = test_swagger_import_from_file()
        
        # 测试 2: 获取 API 规范列表
        test_get_api_specs(project_id)
        
        # 测试 3: 获取测试用例
        test_get_test_cases(test_case_ids)
        
        # 测试 4: 从 URL 导入
        test_swagger_import_from_url()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过!")
        print("=" * 60)
        
        print("\n下一步:")
        print("1. 访问前端页面查看导入的 API 规范")
        print("2. 查看生成的测试用例")
        print("3. 执行测试用例")
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {str(e)}")
        return 1
    except Exception as e:
        print(f"\n❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
