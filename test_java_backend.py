"""测试Java后端服务连接"""
import requests

print("测试Java后端服务连接")
print("=" * 60)

# 测试不同的URL
urls = [
    "http://localhost:8194/recycle",
    "http://localhost:8194/recycle/basic/basicCurrency/page",
    "http://localhost:8194",
    "http://localhost:8194/recycle/swagger-ui.html",
    "http://localhost:8194/recycle/doc.html"
]

for url in urls:
    print(f"\n测试: {url}")
    try:
        response = requests.get(url, timeout=5)
        print(f"  ✅ 状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"  内容长度: {len(response.text)} 字节")
    except requests.exceptions.ConnectionError:
        print(f"  ❌ 连接失败 - 服务未启动或端口不对")
    except requests.exceptions.Timeout:
        print(f"  ❌ 请求超时")
    except Exception as e:
        print(f"  ❌ 错误: {e}")

print("\n" + "=" * 60)
print("检查端口占用情况:")
import subprocess
try:
    result = subprocess.run(
        ["netstat", "-ano"], 
        capture_output=True, 
        text=True,
        timeout=5
    )
    lines = result.stdout.split('\n')
    port_8194 = [line for line in lines if ':8194' in line and 'LISTENING' in line]
    
    if port_8194:
        print("✅ 端口8194正在监听:")
        for line in port_8194:
            print(f"  {line.strip()}")
    else:
        print("❌ 端口8194没有服务监听")
        print("\n可能的原因:")
        print("1. Java后端服务未启动")
        print("2. 服务启动失败")
        print("3. 端口配置不是8194")
except Exception as e:
    print(f"无法检查端口: {e}")
