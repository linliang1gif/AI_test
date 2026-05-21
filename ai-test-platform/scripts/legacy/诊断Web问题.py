#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Test Platform Web服务器问题诊断工具

帮助诊断和解决Web服务器启动问题
"""

import sys
import socket
import subprocess
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    print("🔍 检查Python版本...")
    version = sys.version_info
    print(f"   Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version < (3, 7):
        print("   ❌ Python版本过低，需要3.7+")
        return False
    else:
        print("   ✅ Python版本符合要求")
        return True

def check_dependencies():
    """检查依赖包"""
    print("\n🔍 检查依赖包...")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'jinja2',
        'python-multipart'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - 未安装")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 需要安装的包:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    else:
        print("   ✅ 所有依赖包已安装")
        return True

def check_port_availability(port=8080):
    """检查端口可用性"""
    print(f"\n🔍 检查端口 {port} 可用性...")
    
    try:
        # 尝试绑定端口
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        
        if result == 0:
            print(f"   ❌ 端口 {port} 已被占用")
            
            # 尝试找出占用进程
            try:
                if sys.platform == "win32":
                    result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if f':{port}' in line and 'LISTENING' in line:
                            parts = line.split()
                            if len(parts) > 4:
                                pid = parts[-1]
                                print(f"   占用进程PID: {pid}")
                                break
                else:
                    result = subprocess.run(['lsof', '-i', f':{port}'], capture_output=True, text=True)
                    if result.stdout:
                        print(f"   占用进程信息:\n{result.stdout}")
            except:
                pass
            
            return False
        else:
            print(f"   ✅ 端口 {port} 可用")
            return True
            
    except Exception as e:
        print(f"   ⚠️  端口检查异常: {e}")
        return True

def check_file_permissions():
    """检查文件权限"""
    print("\n🔍 检查文件权限...")
    
    current_dir = Path.cwd()
    print(f"   当前目录: {current_dir}")
    
    # 检查是否可以创建文件
    try:
        test_file = current_dir / "test_permission.tmp"
        test_file.write_text("test")
        test_file.unlink()
        print("   ✅ 文件写入权限正常")
        return True
    except Exception as e:
        print(f"   ❌ 文件写入权限异常: {e}")
        return False

def check_network():
    """检查网络连接"""
    print("\n🔍 检查网络连接...")
    
    try:
        # 测试本地回环
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', 80))
        sock.close()
        print("   ✅ 本地网络正常")
        return True
    except Exception as e:
        print(f"   ⚠️  网络检查异常: {e}")
        return True

def suggest_solutions():
    """提供解决方案建议"""
    print("\n🔧 解决方案建议:")
    print("   1. 安装缺失的依赖包:")
    print("      pip install fastapi uvicorn jinja2 python-multipart")
    print()
    print("   2. 如果端口被占用，尝试:")
    print("      - 关闭占用端口的程序")
    print("      - 使用其他端口 (修改web_server.py中的port参数)")
    print()
    print("   3. 使用简化版启动:")
    print("      python simple_web_server.py")
    print()
    print("   4. 检查防火墙设置:")
    print("      - Windows: 允许Python通过防火墙")
    print("      - Linux: sudo ufw allow 8080")
    print()
    print("   5. 尝试管理员权限运行")

def run_simple_test():
    """运行简单测试"""
    print("\n🧪 运行简单Web服务器测试...")
    
    try:
        from fastapi import FastAPI
        import uvicorn
        
        app = FastAPI()
        
        @app.get("/")
        def read_root():
            return {"message": "测试成功"}
        
        print("   ✅ FastAPI应用创建成功")
        print("   🚀 尝试启动测试服务器...")
        print("   📍 如果成功，请访问: http://127.0.0.1:8081")
        print("   ⏹️  按 Ctrl+C 停止测试服务器")
        
        uvicorn.run(app, host="127.0.0.1", port=8081, log_level="error")
        
    except KeyboardInterrupt:
        print("\n   ✅ 测试服务器正常停止")
        return True
    except Exception as e:
        print(f"   ❌ 测试服务器启动失败: {e}")
        return False

def main():
    """主诊断函数"""
    print("🔍 AI Test Platform Web服务器问题诊断")
    print("=" * 50)
    
    all_checks_passed = True
    
    # 执行各项检查
    checks = [
        check_python_version,
        check_dependencies,
        lambda: check_port_availability(8080),
        check_file_permissions,
        check_network
    ]
    
    for check in checks:
        if not check():
            all_checks_passed = False
    
    print("\n" + "=" * 50)
    
    if all_checks_passed:
        print("✅ 所有检查通过，Web服务器应该可以正常启动")
        print("\n🚀 尝试启动方式:")
        print("   1. python app/web/web_server.py")
        print("   2. python simple_web_server.py")
        print("   3. 双击 启动简化版Web.bat")
        
        # 询问是否运行测试
        try:
            response = input("\n是否运行简单测试? (y/n): ").lower()
            if response == 'y':
                run_simple_test()
        except KeyboardInterrupt:
            print("\n👋 诊断结束")
    else:
        print("❌ 发现问题，请根据建议解决")
        suggest_solutions()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 诊断中断")