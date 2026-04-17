"""
检查前端和后端服务状态
"""
import requests
import socket


def check_port(port, service_name):
    """检查端口是否被占用"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    
    if result == 0:
        print(f"✅ {service_name} (端口 {port}) - 端口已占用")
        return True
    else:
        print(f"❌ {service_name} (端口 {port}) - 端口未占用")
        return False


def check_backend():
    """检查后端服务"""
    print("\n=== 后端服务 (8000) ===")
    
    if not check_port(8000, "后端"):
        return False
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=3)
        if response.status_code == 200:
            print(f"✅ 后端健康检查通过")
            return True
        else:
            print(f"⚠️ 后端响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 后端无法访问: {e}")
        return False


def check_frontend():
    """检查前端服务"""
    print("\n=== 前端服务 (5173) ===")
    
    if not check_port(5173, "前端"):
        return False
    
    try:
        response = requests.get("http://localhost:5173", timeout=3)
        if response.status_code == 200:
            print(f"✅ 前端页面可访问")
            return True
        else:
            print(f"⚠️ 前端响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 前端无法访问: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("服务状态检查")
    print("=" * 60)
    
    backend_ok = check_backend()
    frontend_ok = check_frontend()
    
    print("\n" + "=" * 60)
    print("检查结果")
    print("=" * 60)
    
    if backend_ok and frontend_ok:
        print("✅ 所有服务正常运行")
        print("\n访问地址:")
        print("  前端: http://localhost:5173")
        print("  后端: http://localhost:8000")
    else:
        print("⚠️ 部分服务未运行\n")
        
        if not backend_ok:
            print("启动后端:")
            print("  cd ai-test-platform")
            print("  py backend_api_server.py")
            print()
        
        if not frontend_ok:
            print("启动前端:")
            print("  cd ai-test-platform/frontend")
            print("  npm run dev")
