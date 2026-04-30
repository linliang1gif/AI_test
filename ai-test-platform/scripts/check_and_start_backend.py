"""
检查后端服务状态并提供启动指导
"""

import requests
import subprocess
import sys
import os

def check_backend():
    """检查后端服务是否运行"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("✅ 后端服务正在运行")
            print(f"   状态: {response.json()}")
            return True
    except requests.exceptions.ConnectionError:
        print("❌ 后端服务未运行")
        return False
    except Exception as e:
        print(f"⚠️  检查失败: {e}")
        return False

def check_port_8000():
    """检查8000端口是否被占用"""
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8000))
        sock.close()
        
        if result == 0:
            print("⚠️  端口8000已被占用")
            return True
        else:
            print("✅ 端口8000可用")
            return False
    except Exception as e:
        print(f"⚠️  检查端口失败: {e}")
        return False

def main():
    print("="*60)
    print("  🔍 后端服务状态检查")
    print("="*60)
    print()
    
    # 检查后端服务
    if check_backend():
        print("\n✅ 后端服务运行正常,可以开始测试!")
        print("\n📝 下一步:")
        print("   1. 运行删除功能测试:")
        print("      python test_delete_fix_verification.py")
        print()
        print("   2. 或访问前端页面:")
        print("      http://localhost:5173/test-cases")
        return
    
    print()
    check_port_8000()
    
    print("\n" + "="*60)
    print("  🚀 启动后端服务")
    print("="*60)
    print()
    
    # 检查backend_api_server.py是否存在
    backend_file = "backend_api_server.py"
    if not os.path.exists(backend_file):
        print(f"❌ 找不到 {backend_file}")
        print("   请确保在 ai-test-platform 目录下运行此脚本")
        return
    
    print(f"✅ 找到后端文件: {backend_file}")
    print()
    
    # 提供启动命令
    print("📝 请在新的终端窗口中运行以下命令启动后端:")
    print()
    print("   方式1 - 直接启动:")
    print("   " + "="*50)
    print("   cd ai-test-platform")
    print("   python backend_api_server.py")
    print()
    
    print("   方式2 - 使用批处理文件 (如果存在):")
    print("   " + "="*50)
    print("   cd ai-test-platform")
    print("   start_backend.bat")
    print()
    
    print("⏱️  启动后等待几秒,然后重新运行此脚本验证")
    print()
    
    # 询问是否尝试自动启动
    try:
        choice = input("是否尝试在后台启动后端服务? (y/n): ").strip().lower()
        if choice == 'y':
            print("\n🚀 正在启动后端服务...")
            
            # Windows系统使用start命令在新窗口启动
            if sys.platform == 'win32':
                subprocess.Popen(
                    ['start', 'cmd', '/k', 'python', 'backend_api_server.py'],
                    shell=True,
                    cwd=os.getcwd()
                )
                print("✅ 已在新窗口启动后端服务")
                print("   请查看新打开的命令行窗口")
            else:
                # Linux/Mac
                subprocess.Popen(
                    ['python', 'backend_api_server.py'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                print("✅ 已在后台启动后端服务")
            
            print("\n⏱️  等待5秒后验证...")
            import time
            time.sleep(5)
            
            if check_backend():
                print("\n🎉 后端服务启动成功!")
            else:
                print("\n⚠️  后端服务可能还在启动中,请稍等片刻")
    except KeyboardInterrupt:
        print("\n\n已取消")

if __name__ == "__main__":
    main()
