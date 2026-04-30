#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Test Platform - 平台测试脚本

测试前后端是否正常运行
"""

import requests
import time

def test_backend_api():
    """测试后端API"""
    print("🔍 测试后端API...")
    
    try:
        # 测试仪表板API
        response = requests.get("http://127.0.0.1:8081/api/dashboard/stats")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 仪表板API正常 - 总测试数: {data['totalTests']}")
        else:
            print(f"❌ 仪表板API异常 - 状态码: {response.status_code}")
            return False
        
        # 测试项目API
        response = requests.get("http://127.0.0.1:8081/api/projects")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 项目API正常 - 项目数: {len(data['projects'])}")
        else:
            print(f"❌ 项目API异常 - 状态码: {response.status_code}")
            return False
        
        # 测试AI代理API
        response = requests.get("http://127.0.0.1:8081/api/ai/agents")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ AI代理API正常 - 代理数: {len(data['agents'])}")
        else:
            print(f"❌ AI代理API异常 - 状态码: {response.status_code}")
            return False
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端API服务器")
        return False
    except Exception as e:
        print(f"❌ 后端API测试异常: {e}")
        return False

def test_frontend():
    """测试前端服务器"""
    print("🔍 测试前端服务器...")
    
    try:
        response = requests.get("http://localhost:3000")
        if response.status_code == 200:
            print("✅ 前端服务器正常响应")
            return True
        else:
            print(f"❌ 前端服务器异常 - 状态码: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到前端服务器")
        return False
    except Exception as e:
        print(f"❌ 前端服务器测试异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 AI Test Platform 平台测试")
    print("=" * 50)
    
    # 测试后端
    backend_ok = test_backend_api()
    
    print()
    
    # 测试前端
    frontend_ok = test_frontend()
    
    print()
    print("📊 测试结果:")
    print(f"   后端API: {'✅ 正常' if backend_ok else '❌ 异常'}")
    print(f"   前端服务器: {'✅ 正常' if frontend_ok else '❌ 异常'}")
    
    if backend_ok and frontend_ok:
        print("\n🎉 平台运行正常！")
        print("📍 访问地址:")
        print("   前端界面: http://localhost:3000")
        print("   后端API: http://127.0.0.1:8081")
        print("   API文档: http://127.0.0.1:8081/docs")
    else:
        print("\n⚠️  平台存在问题，请检查服务器状态")

if __name__ == "__main__":
    main()