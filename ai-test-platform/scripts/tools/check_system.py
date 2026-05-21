"""
系统状态检查 - 一键检查所有服务
"""
import requests
import sys


def check_backend():
    """检查后端服务"""
    try:
        r = requests.get("http://localhost:8000/api/pipeline/health", timeout=3)
        return r.json().get('status') == 'healthy'
    except:
        return False


def check_frontend():
    """检查前端服务"""
    try:
        r = requests.get("http://localhost:5173", timeout=3)
        return r.status_code == 200
    except:
        return False


def check_ollama():
    """检查Ollama服务"""
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        return r.status_code == 200
    except:
        return False


def main():
    """主检查流程"""
    print("\n" + "="*50)
    print("🔍 系统状态检查")
    print("="*50 + "\n")
    
    # 检查各服务
    backend_ok = check_backend()
    frontend_ok = check_frontend()
    ollama_ok = check_ollama()
    
    # 显示结果
    print(f"后端服务:  {'🟢 运行中' if backend_ok else '🔴 未运行'}")
    print(f"前端服务:  {'🟢 运行中' if frontend_ok else '🔴 未运行'}")
    print(f"Ollama:   {'🟢 运行中' if ollama_ok else '🟡 未运行 (可选)'}")
    
    print("\n" + "="*50)
    
    # 判断状态
    if backend_ok and frontend_ok:
        print("✅ 系统正常！可以使用")
        print("="*50)
        print("\n📍 访问地址:")
        print("   http://localhost:5173/ai-test-console")
        print("\n💡 快速测试:")
        print("   python quick_test.py\n")
        return True
    else:
        print("❌ 系统异常！需要启动服务")
        print("="*50)
        
        if not backend_ok:
            print("\n启动后端:")
            print("   python backend_api_server.py")
        
        if not frontend_ok:
            print("\n启动前端:")
            print("   cd frontend")
            print("   npm run dev")
        
        if not ollama_ok:
            print("\n启动Ollama (可选):")
            print("   ollama serve")
        
        print()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
