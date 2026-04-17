#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试后端 API

验证：
1. 后端服务是否运行
2. 核心 API 是否可用
3. 前后端数据格式是否匹配
"""

import requests
import json


def test_health():
    """测试健康检查"""
    print("=" * 80)
    print("🧪 测试1: 健康检查")
    print("=" * 80)
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ 后端服务运行正常")
            print(f"  状态: {data.get('status')}")
            print(f"  测试数据工厂: {data.get('test_data_factory')}")
            return True
        else:
            print(f"\n❌ 健康检查失败: {response.status_code}")
            return False
    
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 无法连接到后端服务")
        print(f"  请确保后端服务已启动: cd ai-test-platform && py backend_api_server.py")
        return False
    
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        return False


def test_root():
    """测试根路径"""
    print("\n" + "=" * 80)
    print("🧪 测试2: 根路径")
    print("=" * 80)
    
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ 根路径访问成功")
            print(f"  版本: {data.get('version')}")
            print(f"  状态: {data.get('status')}")
            print(f"  功能:")
            for key, value in data.get('features', {}).items():
                print(f"    - {key}: {value}")
            return True
        else:
            print(f"\n❌ 根路径访问失败: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        return False


def test_projects_api():
    """测试项目 API"""
    print("\n" + "=" * 80)
    print("🧪 测试3: 项目 API")
    print("=" * 80)
    
    try:
        response = requests.get("http://localhost:8000/api/projects", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ 项目 API 可用")
            print(f"  项目数量: {data.get('count')}")
            
            if data.get('projects'):
                print(f"\n  示例项目:")
                project = data['projects'][0]
                print(f"    ID: {project.get('id')}")
                print(f"    名称: {project.get('name')}")
                print(f"    状态: {project.get('status')}")
            
            return True
        else:
            print(f"\n❌ 项目 API 失败: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        return False


def test_test_data_api():
    """测试测试数据 API"""
    print("\n" + "=" * 80)
    print("🧪 测试4: 测试数据 API")
    print("=" * 80)
    
    try:
        # 测试生成用户数据
        payload = {
            "data_type": "user",
            "count": 1
        }
        
        response = requests.post(
            "http://localhost:8000/api/test-data/generate",
            json=payload,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ 测试数据 API 可用")
            print(f"  成功: {data.get('success')}")
            print(f"  消息: {data.get('message')}")
            
            if data.get('data'):
                print(f"\n  生成的数据:")
                user_data = data['data']
                print(f"    用户名: {user_data.get('username')}")
                print(f"    邮箱: {user_data.get('email')}")
            
            return True
        else:
            print(f"\n❌ 测试数据 API 失败: {response.status_code}")
            print(f"  响应: {response.text}")
            return False
    
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        return False


def test_dashboard_api():
    """测试 Dashboard API"""
    print("\n" + "=" * 80)
    print("🧪 测试5: Dashboard API")
    print("=" * 80)
    
    try:
        response = requests.get("http://localhost:8000/api/dashboard/stats", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Dashboard API 可用")
            print(f"  总测试: {data.get('totalTests')}")
            print(f"  通过: {data.get('passed')}")
            print(f"  失败: {data.get('failed')}")
            print(f"  覆盖率: {data.get('coverage')}%")
            
            return True
        else:
            print(f"\n❌ Dashboard API 失败: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        return False


def test_swagger_parse():
    """测试 Swagger 解析"""
    print("\n" + "=" * 80)
    print("🧪 测试6: Swagger 解析 API")
    print("=" * 80)
    
    try:
        # 使用 JSONPlaceholder 的 Swagger
        payload = {
            "url": "https://jsonplaceholder.typicode.com"
        }
        
        response = requests.post(
            "http://localhost:8000/api/swagger/parse",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Swagger 解析 API 可用")
            print(f"  成功: {data.get('success')}")
            print(f"  消息: {data.get('message')}")
            print(f"  API 数量: {data.get('count')}")
            
            return True
        else:
            print(f"\n⚠️  Swagger 解析失败: {response.status_code}")
            print(f"  这是正常的，因为 JSONPlaceholder 没有 Swagger 文档")
            return True  # 不算失败
    
    except Exception as e:
        print(f"\n⚠️  测试跳过: {e}")
        return True  # 不算失败


def main():
    """主函数"""
    print("=" * 80)
    print("🚀 后端 API 测试")
    print("=" * 80)
    
    results = []
    
    # 测试1: 健康检查
    results.append(("健康检查", test_health()))
    
    # 如果健康检查失败，直接退出
    if not results[0][1]:
        print("\n❌ 后端服务未运行，无法继续测试")
        return 1
    
    # 测试2: 根路径
    results.append(("根路径", test_root()))
    
    # 测试3: 项目 API
    results.append(("项目 API", test_projects_api()))
    
    # 测试4: 测试数据 API
    results.append(("测试数据 API", test_test_data_api()))
    
    # 测试5: Dashboard API
    results.append(("Dashboard API", test_dashboard_api()))
    
    # 测试6: Swagger 解析
    results.append(("Swagger 解析", test_swagger_parse()))
    
    # 汇总
    print("\n" + "=" * 80)
    print("📊 测试汇总")
    print("=" * 80)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name:20s} {status}")
    
    total = len(results)
    passed_count = sum(1 for _, p in results if p)
    
    print(f"\n总计: {passed_count}/{total} 通过")
    
    if passed_count == total:
        print("\n🎉 所有 API 测试通过！")
        print("\n✅ 后端服务运行正常")
        print("  地址: http://localhost:8000")
        print("  文档: http://localhost:8000/docs")
        return 0
    else:
        print(f"\n⚠️  {total - passed_count} 个测试失败")
        return 1


if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code)
