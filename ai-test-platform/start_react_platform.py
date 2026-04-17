#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Test Platform - React平台启动器

启动完整的React + FastAPI平台
"""

import os
import sys
import subprocess
import time
import threading
from pathlib import Path

def check_node_npm():
    """检查Node.js和npm是否安装"""
    try:
        # 检查Node.js
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js版本: {result.stdout.strip()}")
        else:
            print("❌ Node.js未安装")
            return False
        
        # 检查npm
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ npm版本: {result.stdout.strip()}")
        else:
            print("❌ npm未安装")
            return False
        
        return True
    except FileNotFoundError:
        print("❌ Node.js或npm未找到，请先安装Node.js")
        return False

def install_frontend_dependencies():
    """安装前端依赖"""
    frontend_dir = Path(__file__).parent / "frontend"
    
    if not frontend_dir.exists():
        print("❌ frontend目录不存在")
        return False
    
    print("📦 安装前端依赖...")
    try:
        result = subprocess.run(
            ['npm', 'install'],
            cwd=frontend_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ 前端依赖安装成功")
            return True
        else:
            print(f"❌ 前端依赖安装失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 安装依赖时出错: {e}")
        return False

def start_backend():
    """启动后端API服务器"""
    print("🚀 启动后端API服务器...")
    backend_script = Path(__file__).parent / "backend_api_server.py"
    
    try:
        subprocess.run([sys.executable, str(backend_script)])
    except KeyboardInterrupt:
        print("\n👋 后端服务器已停止")
    except Exception as e:
        print(f"❌ 后端启动失败: {e}")

def start_frontend():
    """启动前端开发服务器"""
    print("🚀 启动前端开发服务器...")
    frontend_dir = Path(__file__).parent / "frontend"
    
    try:
        subprocess.run(['npm', 'run', 'dev'], cwd=frontend_dir)
    except KeyboardInterrupt:
        print("\n👋 前端服务器已停止")
    except Exception as e:
        print(f"❌ 前端启动失败: {e}")

def main():
    """主函数"""
    print("🚀 AI Test Platform React版启动器")
    print("=" * 60)
    
    # 检查Node.js环境
    if not check_node_npm():
        print("\n💡 请先安装Node.js:")
        print("   1. 访问 https://nodejs.org/")
        print("   2. 下载并安装LTS版本")
        print("   3. 重新运行此脚本")
        return
    
    # 检查前端目录
    frontend_dir = Path(__file__).parent / "frontend"
    if not frontend_dir.exists():
        print("❌ frontend目录不存在，请先运行完整的React项目创建")
        return
    
    # 检查package.json
    package_json = frontend_dir / "package.json"
    if not package_json.exists():
        print("❌ package.json不存在")
        return
    
    # 检查node_modules
    node_modules = frontend_dir / "node_modules"
    if not node_modules.exists():
        print("📦 首次运行，需要安装依赖...")
        if not install_frontend_dependencies():
            return
    
    print("\n🎯 启动模式选择:")
    print("1. 启动完整平台 (后端API + 前端React)")
    print("2. 仅启动后端API服务器")
    print("3. 仅启动前端React开发服务器")
    
    choice = input("\n请选择启动模式 (1-3): ").strip()
    
    if choice == "1":
        print("\n🚀 启动完整平台...")
        print("📍 后端API: http://127.0.0.1:8080")
        print("📍 前端React: http://localhost:3000")
        print("📖 API文档: http://127.0.0.1:8080/docs")
        print("\n⚠️  请在两个终端中分别运行:")
        print("   终端1: python backend_api_server.py")
        print("   终端2: cd frontend && npm run dev")
        print("\n或者手动启动:")
        
        # 启动后端 (在新线程中)
        backend_thread = threading.Thread(target=start_backend, daemon=True)
        backend_thread.start()
        
        # 等待后端启动
        time.sleep(3)
        
        # 启动前端
        start_frontend()
        
    elif choice == "2":
        print("\n🚀 启动后端API服务器...")
        start_backend()
        
    elif choice == "3":
        print("\n🚀 启动前端React开发服务器...")
        print("⚠️  请确保后端API服务器已在 http://127.0.0.1:8080 运行")
        start_frontend()
        
    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 启动器已停止")
    except Exception as e:
        print(f"❌ 启动器异常: {e}")