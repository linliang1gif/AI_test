#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI测试平台 - 项目状态检查

检查整个AI测试平台的运行状态
"""

import requests
import time
from datetime import datetime

def print_banner():
    """打印检查横幅"""
    print("=" * 80)
    print("🔍 AI测试平台 - 项目状态检查")
    print("=" * 80)
    print(f"⏰ 检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def check_backend():
    """检查后端服务"""
    print("🔧 检查后端API服务...")
    try:
        # 检查基本连接
        response = requests.get("http://127.0.0.1:8081/api/dashboard/stats", timeout=5)
        if response.status_code == 200:
            print("   ✅ 后端API服务正常运行")
            print(f"   📍 地址: http://127.0.0.1:8081")
            
            # 检查API响应数据
            data = response.json()
            print(f"   📊 统计数据: 总测试 {data.get('totalTests', 0)}, 通过 {data.get('passed', 0)}, 失败 {data.get('failed', 0)}")
            
            # 检查其他API端点
            endpoints = [
                ("/api/projects", "项目管理"),
                ("/api/apis", "接口管理"),
                ("/api/test-cases", "测试用例"),
                ("/api/test-runs", "测试执行"),
                ("/api/reports", "测试报告"),
                ("/api/ai/agents", "AI代理")
            ]
            
            print("   🔗 API端点检查:")
            for endpoint, name in endpoints:
                try:
                    resp = requests.get(f"http://127.0.0.1:8081{endpoint}", timeout=3)
                    if resp.status_code == 200:
                        print(f"      ✅ {name}: {endpoint}")
                    else:
                        print(f"      ⚠️  {name}: {endpoint} (状态码: {resp.status_code})")
                except Exception as e:
                    print(f"      ❌ {name}: {endpoint} (错误: {str(e)[:30]}...)")
            
            return True
        else:
            print(f"   ❌ 后端API服务响应异常 (状态码: {response.status_code})")
            return False
    except requests.exceptions.ConnectionError:
        print("   ❌ 后端API服务连接失败 - 服务可能未启动")
        return False
    except Exception as e:
        print(f"   ❌ 后端API服务检查失败: {e}")
        return False

def check_frontend():
    """检查前端服务"""
    print("\n🎨 检查前端开发服务...")
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("   ✅ 前端服务正常运行")
            print(f"   🌐 地址: http://localhost:3000")
            
            # 检查页面内容
            content = response.text
            if "AI测试平台" in content:
                print("   📱 页面内容正常加载")
            else:
                print("   ⚠️  页面内容可能异常")
            
            return True
        else:
            print(f"   ❌ 前端服务响应异常 (状态码: {response.status_code})")
            return False
    except requests.exceptions.ConnectionError:
        print("   ❌ 前端服务连接失败 - 服务可能未启动")
        return False
    except Exception as e:
        print(f"   ❌ 前端服务检查失败: {e}")
        return False

def check_api_docs():
    """检查API文档"""
    print("\n📖 检查API文档...")
    try:
        response = requests.get("http://127.0.0.1:8081/docs", timeout=5)
        if response.status_code == 200:
            print("   ✅ Swagger API文档可访问")
            print("   📍 地址: http://127.0.0.1:8081/docs")
            return True
        else:
            print(f"   ❌ API文档响应异常 (状态码: {response.status_code})")
            return False
    except Exception as e:
        print(f"   ❌ API文档检查失败: {e}")
        return False

def show_summary(backend_ok, frontend_ok, docs_ok):
    """显示检查总结"""
    print("\n" + "=" * 80)
    print("📋 检查总结")
    print("=" * 80)
    
    total_checks = 3
    passed_checks = sum([backend_ok, frontend_ok, docs_ok])
    
    print(f"✅ 通过检查: {passed_checks}/{total_checks}")
    
    if passed_checks == total_checks:
        print("🎉 所有服务运行正常！")
        print("\n🚀 您可以开始使用AI测试平台:")
        print("   1. 访问前端界面: http://localhost:3000")
        print("   2. 查看API文档: http://127.0.0.1:8081/docs")
        print("   3. 探索8个核心功能模块")
        print("   4. 体验AI驱动的测试生成")
    elif passed_checks >= 2:
        print("⚠️  大部分服务正常，但有部分问题需要关注")
    else:
        print("❌ 多个服务存在问题，请检查服务启动状态")
    
    print("\n💡 如果服务未启动，请运行:")
    print("   • Windows: 双击 '快速启动.bat'")
    print("   • 或手动启动: py backend_api_server.py 和 npm run dev")
    
    print("=" * 80)

def main():
    """主函数"""
    print_banner()
    
    # 检查各个服务
    backend_ok = check_backend()
    frontend_ok = check_frontend()
    docs_ok = check_api_docs()
    
    # 显示总结
    show_summary(backend_ok, frontend_ok, docs_ok)

if __name__ == "__main__":
    main()