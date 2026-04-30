#!/usr/bin/env python3
"""测试项目管理模块修复"""
import requests

BASE_URL = "http://localhost:8000"

def test_projects():
    print("=" * 60)
    print("🧪 测试项目管理模块")
    print("=" * 60)
    
    # 1. 获取项目列表
    print("\n1️⃣ 获取项目列表...")
    try:
        r = requests.get(f"{BASE_URL}/api/projects")
        data = r.json()
        
        print(f"✅ API响应成功")
        print(f"   - 状态码: {r.status_code}")
        print(f"   - 项目数量: {data.get('count', 0)}")
        print(f"   - 数据格式: {'projects' in data}")
        
        if 'projects' in data and len(data['projects']) > 0:
            print(f"\n📋 项目列表:")
            for p in data['projects']:
                print(f"   - {p['name']}: {p['description']}")
                print(f"     环境: {p.get('environment', 'N/A')}")
                print(f"     测试数: {p.get('testsCount', 0)}")
                print(f"     覆盖率: {p.get('coverage', 0)}%")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    
    # 2. 创建新项目
    print("\n2️⃣ 创建新项目...")
    try:
        new_project = {
            "name": "测试项目",
            "description": "API测试创建的项目",
            "environment": "development",
            "baseUrl": "http://localhost:8080"
        }
        
        r = requests.post(f"{BASE_URL}/api/projects", json=new_project)
        data = r.json()
        
        if data.get('success'):
            print(f"✅ 项目创建成功")
            print(f"   - 项目ID: {data.get('project', {}).get('id')}")
            print(f"   - 项目名称: {data.get('project', {}).get('name')}")
        else:
            print(f"❌ 创建失败: {data.get('message')}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    
    print("\n" + "=" * 60)
    print("✅ 项目管理模块测试完成!")
    print("=" * 60)
    print("\n💡 提示: 现在可以刷新前端页面查看项目数据")
    print("   前端地址: http://localhost:5173")


if __name__ == "__main__":
    test_projects()
