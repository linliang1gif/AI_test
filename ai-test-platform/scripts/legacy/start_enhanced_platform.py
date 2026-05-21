#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
启动增强版AI测试平台 - 现代SaaS风格界面

包含：
1. React前端 (现代SaaS设计)
2. FastAPI后端
3. 自动安装依赖
"""

import os
import sys
import subprocess
import time
import threading
from pathlib import Path

def print_banner():
    """打印启动横幅"""
    print("=" * 80)
    print("🚀 AI测试平台 - 现代SaaS风格界面")
    print("=" * 80)
    print("📋 功能特性:")
    print("   • 现代Postman/Linear/Notion风格设计")
    print("   • 增强的表格和数据可视化")
    print("   • 实时状态监控和进度跟踪")
    print("   • 智能搜索和筛选功能")
    print("   • 响应式布局和动画效果")
    print("=" * 80)

def install_frontend_dependencies():
    """安装前端依赖"""
    print("📦 安装前端依赖...")
    frontend_dir = Path(__file__).parent / "frontend"
    
    try:
        # 检查是否已安装依赖
        if not (frontend_dir / "node_modules").exists():
            print("   正在安装npm依赖...")
            result = subprocess.run(
                ["npm", "install"], 
                cwd=frontend_dir, 
                capture_output=True, 
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                print("   ✅ 前端依赖安装成功")
            else:
                print(f"   ❌ 前端依赖安装失败: {result.stderr}")
                return False
        else:
            print("   ✅ 前端依赖已存在")
        return True
    except subprocess.TimeoutExpired:
        print("   ⚠️  依赖安装超时，但可能已部分完成")
        return True
    except Exception as e:
        print(f"   ❌ 安装依赖时出错: {e}")
        return False

def start_backend():
    """启动后端服务"""
    print("🔧 启动后端API服务...")
    try:
        backend_script = Path(__file__).parent / "backend_api_server.py"
        subprocess.Popen([sys.executable, str(backend_script)])
        print("   ✅ 后端服务启动成功 (端口: 8081)")
        return True
    except Exception as e:
        print(f"   ❌ 后端服务启动失败: {e}")
        return False

def start_frontend():
    """启动前端服务"""
    print("🎨 启动前端开发服务...")
    frontend_dir = Path(__file__).parent / "frontend"
    
    try:
        # 启动Vite开发服务器
        subprocess.Popen(
            ["npm", "run", "dev"], 
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("   ✅ 前端服务启动成功 (端口: 3000)")
        return True
    except Exception as e:
        print(f"   ❌ 前端服务启动失败: {e}")
        return False

def wait_for_services():
    """等待服务启动"""
    print("⏳ 等待服务启动...")
    time.sleep(3)
    
    # 检查服务状态
    try:
        import requests
        
        # 检查后端
        try:
            response = requests.get("http://127.0.0.1:8081/api/dashboard/stats", timeout=5)
            if response.status_code == 200:
                print("   ✅ 后端API服务正常")
            else:
                print("   ⚠️  后端API响应异常")
        except:
            print("   ⚠️  后端API连接失败")
        
        # 检查前端
        try:
            response = requests.get("http://localhost:3000", timeout=5)
            if response.status_code == 200:
                print("   ✅ 前端服务正常")
            else:
                print("   ⚠️  前端服务响应异常")
        except:
            print("   ⚠️  前端服务连接失败")
            
    except ImportError:
        print("   ℹ️  无法检查服务状态 (缺少requests库)")

def show_access_info():
    """显示访问信息"""
    print("\n" + "=" * 80)
    print("🌐 服务访问地址:")
    print("=" * 80)
    print("📱 前端界面: http://localhost:3000")
    print("   • 现代SaaS风格设计")
    print("   • 仪表板、项目管理、API探索等功能")
    print("   • 实时数据监控和可视化")
    print()
    print("🔧 后端API: http://127.0.0.1:8081")
    print("   • RESTful API接口")
    print("   • 实时数据处理")
    print("   • API文档: http://127.0.0.1:8081/docs")
    print()
    print("🎯 主要功能:")
    print("   • 智能测试用例生成")
    print("   • 自动化脚本生成")
    print("   • 实时测试执行监控")
    print("   • AI驱动的错误分析")
    print("   • 测试报告和数据可视化")
    print("=" * 80)

def main():
    """主函数"""
    print_banner()
    
    # 检查环境
    frontend_dir = Path(__file__).parent / "frontend"
    if not frontend_dir.exists():
        print("❌ 前端目录不存在，请确保项目结构完整")
        return
    
    # 安装依赖
    if not install_frontend_dependencies():
        print("❌ 依赖安装失败，但尝试继续启动...")
    
    # 启动服务
    print("\n🚀 启动服务...")
    
    backend_success = start_backend()
    time.sleep(2)  # 等待后端启动
    
    frontend_success = start_frontend()
    
    if backend_success or frontend_success:
        wait_for_services()
        show_access_info()
        
        print("\n💡 使用提示:")
        print("   • 按 Ctrl+C 停止服务")
        print("   • 前端支持热重载，修改代码会自动刷新")
        print("   • 后端API支持跨域请求")
        print("   • 建议使用Chrome或Edge浏览器获得最佳体验")
        
        try:
            print("\n⌨️  按 Ctrl+C 停止所有服务...")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 正在停止服务...")
            print("   服务已停止")
    else:
        print("❌ 服务启动失败")

if __name__ == "__main__":
    main()