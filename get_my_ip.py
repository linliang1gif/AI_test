"""
查看本机IP地址
用于配置GitLab Webhook
"""
import socket

def get_local_ip():
    """获取本机IP地址"""
    try:
        # 创建一个UDP socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 连接到外部地址（不会真正发送数据）
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def main():
    print("=" * 60)
    print("🔍 查看本机IP地址")
    print("=" * 60)
    
    ip = get_local_ip()
    
    print(f"\n你的本机IP地址: {ip}")
    print("\n" + "=" * 60)
    print("GitLab Webhook 配置")
    print("=" * 60)
    
    if ip == "127.0.0.1":
        print("\n如果GitLab在本机，使用:")
        print(f"  http://localhost:8001/webhook/gitlab")
        print(f"  或")
        print(f"  http://127.0.0.1:8001/webhook/gitlab")
    else:
        print("\n如果GitLab在其他机器，使用:")
        print(f"  http://{ip}:8001/webhook/gitlab")
        print("\n如果GitLab在本机，也可以使用:")
        print(f"  http://localhost:8001/webhook/gitlab")
    
    print("\n" + "=" * 60)
    print("测试连接")
    print("=" * 60)
    print("\n启动webhook服务后，在浏览器访问:")
    if ip == "127.0.0.1":
        print(f"  http://localhost:8001/webhook/gitlab/health")
    else:
        print(f"  http://{ip}:8001/webhook/gitlab/health")
    print("\n如果看到 'healthy' 说明服务正常运行")
    print("=" * 60)

if __name__ == "__main__":
    main()
