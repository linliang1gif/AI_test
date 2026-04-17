#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI测试平台 - 完整项目启动脚本

启动整个AI测试平台，包括：
1. 后端API服务器 (FastAPI)
2. 前端开发服务器 (React + Vite)
3. 系统健康检查
4. 完整功能演示
"""

import os
import sys
import subprocess
import time
import threading
import webbrowser
from pathlib import Path

def print_banner():
    """打印启动横幅"""
    print("=" * 100)
    print("🚀 AI测试平台 - 完整项目启动")
    print("=" * 100)
    print("📋 平台特性:")
    print("   🎨 现代SaaS风格界面 (Postman/Linear/Notion设计)")
    print("   🧠 AI驱动的测试生成和分析")
    print("   📊 实时数据监控和可视化")
    print("   🔄 完整的测试生命周期管理")
    print("   🛠️ 自动化脚本生成和执行")
    print("   📈 智能测试报告和分析")
    print("   🔍 API接口探索和测试")
    print("   ⚡ 实时测试执行监控")
    print("=" * 100)

def check_dependencies():
    """检查依赖环境"""
    print("🔍 检查系统依赖...")
    
    # 检查Python
    try:
        python_version = sys.version.split()[0]
        print(f"   ✅ Python {python_version}")
    except Exception as e:
        print(f"   ❌ Python检查失败: {e}")
        return False
    
    # 检查Node.js和npm
    try:
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            npm_version = result.stdout.strip()
            print(f"   ✅ npm {npm_version}")
        else:
            print("   ❌ npm未安装或不可用")
            return False
    except Exception as e:
        print(f"   ❌ npm检查失败: {e}")
        return False
    
    # 检查必要的Python包
    required_packages = ['fastapi', 'uvicorn', 'requests']
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ⚠️  {package} 未安装，尝试安装...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", package], 
                             capture_output=True, timeout=60)
                print(f"   ✅ {package} 安装成功")
            except Exception as e:
                print(f"   ❌ {package} 安装失败: {e}")
                return False
    
    return True

def install_frontend_dependencies():
    """安装前端依赖"""
    print("📦 检查前端依赖...")
    frontend_dir = Path(__file__).parent / "frontend"
    
    if not frontend_dir.exists():
        print("   ❌ 前端目录不存在")
        return False
    
    node_modules = frontend_dir / "node_modules"
    if not node_modules.exists():
        print("   📥 安装前端依赖...")
        try:
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
        except subprocess.TimeoutExpired:
            print("   ⚠️  依赖安装超时，但可能已部分完成")
        except Exception as e:
            print(f"   ❌ 安装依赖时出错: {e}")
            return False
    else:
        print("   ✅ 前端依赖已存在")
    
    return True

def start_backend():
    """启动后端服务"""
    print("🔧 启动后端API服务...")
    try:
        backend_script = Path(__file__).parent / "backend_api_server.py"
        process = subprocess.Popen(
            [sys.executable, str(backend_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("   ✅ 后端服务启动成功 (PID: {})".format(process.pid))
        print("   📍 API地址: http://127.0.0.1:8081")
        print("   📖 API文档: http://127.0.0.1:8081/docs")
        return process
    except Exception as e:
        print(f"   ❌ 后端服务启动失败: {e}")
        return None

def start_frontend():
    """启动前端服务"""
    print("🎨 启动前端开发服务...")
    frontend_dir = Path(__file__).parent / "frontend"
    
    try:
        process = subprocess.Popen(
            ["npm", "run", "dev"], 
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("   ✅ 前端服务启动成功 (PID: {})".format(process.pid))
        print("   🌐 前端地址: http://localhost:3000")
        return process
    except Exception as e:
        print(f"   ❌ 前端服务启动失败: {e}")
        return None

def wait_for_services():
    """等待服务启动并检查健康状态"""
    print("⏳ 等待服务启动...")
    time.sleep(5)
    
    # 检查服务状态
    try:
        import requests
        
        # 检查后端
        backend_healthy = False
        for i in range(10):  # 最多等待10秒
            try:
                response = requests.get("http://127.0.0.1:8081/api/dashboard/stats", timeout=2)
                if response.status_code == 200:
                    print("   ✅ 后端API服务健康检查通过")
                    backend_healthy = True
                    break
            except:
                time.sleep(1)
        
        if not backend_healthy:
            print("   ⚠️  后端API服务健康检查失败")
        
        # 检查前端
        frontend_healthy = False
        for i in range(10):  # 最多等待10秒
            try:
                response = requests.get("http://localhost:3000", timeout=2)
                if response.status_code == 200:
                    print("   ✅ 前端服务健康检查通过")
                    frontend_healthy = True
                    break
            except:
                time.sleep(1)
        
        if not frontend_healthy:
            print("   ⚠️  前端服务健康检查失败")
        
        return backend_healthy and frontend_healthy
            
    except ImportError:
        print("   ℹ️  无法进行健康检查 (缺少requests库)")
        return True

def show_project_info():
    """显示项目信息"""
    print("\n" + "=" * 100)
    print("🌟 AI测试平台 - 项目启动完成")
    print("=" * 100)
    
    print("🌐 访问地址:")
    print("   📱 前端界面: http://localhost:3000")
    print("      • 现代SaaS风格设计")
    print("      • 8个核心功能模块")
    print("      • 实时数据监控")
    print("      • 中文本地化界面")
    print()
    print("   🔧 后端API: http://127.0.0.1:8081")
    print("      • RESTful API接口")
    print("      • 实时数据处理")
    print("      • Swagger文档: http://127.0.0.1:8081/docs")
    print()
    
    print("🎯 核心功能模块:")
    modules = [
        ("仪表板", "实时统计、测试趋势、系统状态监控"),
        ("项目管理", "项目创建、配置管理、测试覆盖率"),
        ("接口管理", "Swagger解析、API测试、接口文档"),
        ("测试用例", "AI生成用例、用例管理、执行跟踪"),
        ("自动化脚本", "pytest脚本生成、代码查看、执行管理"),
        ("测试执行", "实时监控、进度跟踪、结果统计"),
        ("测试报告", "报告生成、数据可视化、导出功能"),
        ("AI分析中心", "智能分析、AI代理工作流、错误诊断")
    ]
    
    for i, (name, desc) in enumerate(modules, 1):
        print(f"   {i}. {name}: {desc}")
    
    print()
    print("🚀 AI驱动特性:")
    print("   🧠 智能测试用例生成")
    print("   🔄 自动化脚本生成")
    print("   📊 实时测试分析")
    print("   🛠️ 自动错误修复建议")
    print("   📈 智能测试报告")
    print("   🔍 API接口智能探索")
    
    print()
    print("💡 使用指南:")
    print("   1. 访问 http://localhost:3000 开始使用")
    print("   2. 点击侧边栏菜单探索不同功能")
    print("   3. 在项目管理中创建新项目")
    print("   4. 使用接口管理导入Swagger文档")
    print("   5. 通过AI生成测试用例和脚本")
    print("   6. 监控测试执行和查看报告")
    
    print("=" * 100)

def open_browser():
    """自动打开浏览器"""
    print("🌐 自动打开浏览器...")
    time.sleep(2)
    try:
        webbrowser.open("http://localhost:3000")
        print("   ✅ 浏览器已打开")
    except Exception as e:
        print(f"   ⚠️  无法自动打开浏览器: {e}")
        print("   💡 请手动访问: http://localhost:3000")

def main():
    """主函数"""
    print_banner()
    
    # 检查依赖
    if not check_dependencies():
        print("❌ 依赖检查失败，请解决依赖问题后重试")
        return
    
    # 安装前端依赖
    if not install_frontend_dependencies():
        print("❌ 前端依赖安装失败")
        return
    
    print("\n🚀 启动服务...")
    
    # 启动后端
    backend_process = start_backend()
    if not backend_process:
        print("❌ 后端服务启动失败")
        return
    
    # 等待后端启动
    time.sleep(3)
    
    # 启动前端
    frontend_process = start_frontend()
    if not frontend_process:
        print("❌ 前端服务启动失败")
        if backend_process:
            backend_process.terminate()
        return
    
    # 等待服务启动并检查健康状态
    services_healthy = wait_for_services()
    
    # 显示项目信息
    show_project_info()
    
    if services_healthy:
        # 自动打开浏览器
        threading.Thread(target=open_browser, daemon=True).start()
        
        print("\n⌨️  按 Ctrl+C 停止所有服务...")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 正在停止服务...")
            
            # 停止服务
            if frontend_process:
                frontend_process.terminate()
                print("   ✅ 前端服务已停止")
            
            if backend_process:
                backend_process.terminate()
                print("   ✅ 后端服务已停止")
            
            print("   🎉 所有服务已停止，感谢使用AI测试平台！")
    else:
        print("⚠️  部分服务启动异常，请检查日志")

if __name__ == "__main__":
    main()