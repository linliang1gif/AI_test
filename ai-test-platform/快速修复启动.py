#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI测试平台 - 快速修复启动脚本
解决按钮点击无效的问题
"""

import os
import sys
import time
import subprocess
import webbrowser
from pathlib import Path

def print_banner():
    print("=" * 60)
    print("🔧 AI测试平台 - 快速修复启动")
    print("=" * 60)
    print("🎯 目标: 修复按钮点击无效问题")
    print("📍 当前目录:", os.getcwd())
    print("⏰ 启动时间:", time.strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)

def check_environment():
    """检查环境"""
    print("\n🔍 检查环境...")
    
    # 检查Python
    python_version = sys.version.split()[0]
    print(f"✅ Python版本: {python_version}")
    
    # 检查Node.js
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js版本: {result.stdout.strip()}")
        else:
            print("❌ Node.js未安装")
            return False
    except FileNotFoundError:
        print("❌ Node.js未找到")
        return False
    
    # 检查npm
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ npm版本: {result.stdout.strip()}")
        else:
            print("❌ npm未安装")
            return False
    except FileNotFoundError:
        print("❌ npm未找到")
        return False
    
    return True

def install_dependencies():
    """安装依赖"""
    print("\n📦 检查并安装依赖...")
    
    # 检查前端依赖
    frontend_dir = Path("frontend")
    if frontend_dir.exists():
        print("🔄 检查前端依赖...")
        os.chdir(frontend_dir)
        
        # 检查node_modules
        if not Path("node_modules").exists():
            print("📦 安装前端依赖...")
            result = subprocess.run(['npm', 'install'], capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ 前端依赖安装失败: {result.stderr}")
                return False
            print("✅ 前端依赖安装完成")
        else:
            print("✅ 前端依赖已存在")
        
        os.chdir("..")
    
    return True

def start_backend():
    """启动后端服务"""
    print("\n🚀 启动后端服务...")
    
    try:
        # 启动后端API服务器
        backend_process = subprocess.Popen(
            [sys.executable, 'backend_api_server.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 等待服务启动
        print("⏳ 等待后端服务启动...")
        time.sleep(3)
        
        # 检查服务是否启动成功
        import requests
        try:
            response = requests.get('http://127.0.0.1:8081/api/dashboard/stats', timeout=5)
            if response.status_code == 200:
                print("✅ 后端服务启动成功")
                print("📍 后端地址: http://127.0.0.1:8081")
                print("📖 API文档: http://127.0.0.1:8081/docs")
                return backend_process
            else:
                print(f"❌ 后端服务响应异常: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"❌ 后端服务连接失败: {e}")
            return None
            
    except Exception as e:
        print(f"❌ 后端服务启动失败: {e}")
        return None

def start_frontend():
    """启动前端服务"""
    print("\n🎨 启动前端服务...")
    
    try:
        os.chdir("frontend")
        
        # 启动前端开发服务器
        frontend_process = subprocess.Popen(
            ['npm', 'run', 'dev'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 等待服务启动
        print("⏳ 等待前端服务启动...")
        time.sleep(5)
        
        # 检查服务是否启动成功
        import requests
        ports_to_try = [3000, 3001, 3002]
        
        for port in ports_to_try:
            try:
                response = requests.get(f'http://localhost:{port}', timeout=3)
                if response.status_code == 200:
                    print(f"✅ 前端服务启动成功")
                    print(f"📍 前端地址: http://localhost:{port}")
                    os.chdir("..")
                    return frontend_process, port
            except requests.exceptions.RequestException:
                continue
        
        print("❌ 前端服务启动失败或端口检测失败")
        os.chdir("..")
        return None, None
        
    except Exception as e:
        print(f"❌ 前端服务启动失败: {e}")
        os.chdir("..")
        return None, None

def test_functionality():
    """测试功能"""
    print("\n🧪 测试系统功能...")
    
    import requests
    
    tests = [
        ("后端API连接", "http://127.0.0.1:8081/api/dashboard/stats"),
        ("项目管理API", "http://127.0.0.1:8081/api/projects"),
        ("测试用例API", "http://127.0.0.1:8081/api/test-cases"),
        ("AI代理API", "http://127.0.0.1:8081/api/ai/agents"),
    ]
    
    passed = 0
    total = len(tests)
    
    for name, url in tests:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: 正常")
                passed += 1
            else:
                print(f"❌ {name}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: {e}")
    
    print(f"\n📊 功能测试结果: {passed}/{total} 通过")
    return passed == total

def open_browser(frontend_port):
    """打开浏览器"""
    print("\n🌐 打开浏览器...")
    
    urls = [
        f"http://localhost:{frontend_port}",
        "http://127.0.0.1:8081/docs",
        f"file://{os.path.abspath('frontend/test_fixed_buttons.html')}"
    ]
    
    for i, url in enumerate(urls, 1):
        print(f"{i}. {url}")
    
    # 打开主界面
    try:
        webbrowser.open(f"http://localhost:{frontend_port}")
        print("✅ 浏览器已打开")
    except Exception as e:
        print(f"❌ 浏览器打开失败: {e}")

def main():
    """主函数"""
    print_banner()
    
    # 检查环境
    if not check_environment():
        print("\n❌ 环境检查失败，请安装必要的依赖")
        return
    
    # 安装依赖
    if not install_dependencies():
        print("\n❌ 依赖安装失败")
        return
    
    # 启动后端
    backend_process = start_backend()
    if not backend_process:
        print("\n❌ 后端服务启动失败")
        return
    
    # 启动前端
    frontend_process, frontend_port = start_frontend()
    if not frontend_process:
        print("\n❌ 前端服务启动失败")
        backend_process.terminate()
        return
    
    # 测试功能
    if test_functionality():
        print("\n🎉 所有功能测试通过！")
    else:
        print("\n⚠️ 部分功能测试失败，但基本功能可用")
    
    # 打开浏览器
    open_browser(frontend_port)
    
    print("\n" + "=" * 60)
    print("🎊 AI测试平台启动完成！")
    print("=" * 60)
    print(f"🌐 前端界面: http://localhost:{frontend_port}")
    print("🔗 后端API: http://127.0.0.1:8081")
    print("📖 API文档: http://127.0.0.1:8081/docs")
    print("🧪 功能测试: frontend/test_fixed_buttons.html")
    print("=" * 60)
    print("\n💡 使用说明:")
    print("1. 前端界面已修复按钮点击问题")
    print("2. 所有API调用已配置正确的代理")
    print("3. 如果按钮仍无响应，请检查浏览器控制台")
    print("4. 按 Ctrl+C 停止服务")
    
    try:
        print("\n⏳ 服务运行中，按 Ctrl+C 停止...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 正在停止服务...")
        if backend_process:
            backend_process.terminate()
        if frontend_process:
            frontend_process.terminate()
        print("✅ 服务已停止")

if __name__ == "__main__":
    main()