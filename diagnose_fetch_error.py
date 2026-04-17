"""诊断 Failed to fetch 错误"""
import requests
import subprocess
import time

print("=" * 60)
print("诊断 'Failed to fetch' 错误")
print("=" * 60)
print()

# 1. 检查后端是否真的在运行
print("1. 检查后端服务...")
try:
    response = requests.get("http://localhost:8000/health", timeout=3)
    print(f"✅ 后端响应正常: {response.status_code}")
    print(f"   数据: {response.json()}")
except requests.exceptions.ConnectionError:
    print("❌ 后端服务未运行或无法连接")
    print()
    print("解决方案:")
    print("1. 打开新的命令行窗口")
    print("2. 运行: cd ai-test-platform")
    print("3. 运行: py backend_api_server.py")
    exit(1)
except Exception as e:
    print(f"❌ 后端检查失败: {e}")
    exit(1)

print()

# 2. 检查CORS配置
print("2. 检查CORS配置...")
try:
    response = requests.options(
        "http://localhost:8000/api/projects",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET"
        }
    )
    
    cors_headers = {
        "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
        "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
        "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
    }
    
    if cors_headers["Access-Control-Allow-Origin"]:
        print("✅ CORS配置正常")
        for key, value in cors_headers.items():
            if value:
                print(f"   {key}: {value}")
    else:
        print("⚠️  CORS配置可能有问题")
        
except Exception as e:
    print(f"⚠️  CORS检查失败: {e}")

print()

# 3. 测试关键API端点
print("3. 测试关键API端点...")

endpoints = [
    ("GET", "/api/projects", "项目列表"),
    ("GET", "/api/apis", "API列表"),
    ("GET", "/api/test-cases", "测试用例"),
    ("GET", "/api/automation/scripts", "自动化脚本"),
]

all_ok = True
for method, path, name in endpoints:
    url = f"http://localhost:8000{path}"
    try:
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            print(f"✅ {name}: {response.status_code}")
        else:
            print(f"⚠️  {name}: {response.status_code}")
            all_ok = False
    except Exception as e:
        print(f"❌ {name}: {str(e)[:50]}")
        all_ok = False

print()

# 4. 检查前端配置
print("4. 检查前端API配置...")
import os
from pathlib import Path

# 检查前端API配置文件
api_files = [
    "ai-test-platform/frontend/src/services/api.js",
    "ai-test-platform/frontend/src/services/api.ts",
    "ai-test-platform/frontend/src/config.js",
    "ai-test-platform/frontend/src/config.ts",
]

found_config = False
for api_file in api_files:
    if Path(api_file).exists():
        print(f"✅ 找到配置文件: {api_file}")
        found_config = True
        
        # 读取并检查API_BASE_URL
        try:
            content = Path(api_file).read_text(encoding='utf-8')
            if 'localhost:8000' in content or '127.0.0.1:8000' in content:
                print("   ✅ API地址配置正确")
            else:
                print("   ⚠️  API地址可能配置错误")
                print("   应该是: http://localhost:8000")
        except:
            pass

if not found_config:
    print("⚠️  未找到前端API配置文件")

print()

# 5. 检查网络连接
print("5. 检查网络连接...")
try:
    # 测试本地回环
    response = requests.get("http://127.0.0.1:8000/health", timeout=3)
    print("✅ 127.0.0.1:8000 可访问")
    
    response = requests.get("http://localhost:8000/health", timeout=3)
    print("✅ localhost:8000 可访问")
    
except Exception as e:
    print(f"❌ 网络连接问题: {e}")

print()

# 6. 检查防火墙/代理
print("6. 检查可能的阻塞...")
print("   如果使用了代理或VPN，可能会影响本地连接")
print("   建议临时关闭代理/VPN测试")

print()
print("=" * 60)
print("诊断完成")
print("=" * 60)
print()

if all_ok:
    print("✅ 后端API全部正常！")
    print()
    print("'Failed to fetch' 可能的原因:")
    print()
    print("1. 浏览器缓存问题")
    print("   解决: 按 Ctrl+Shift+R 硬刷新页面")
    print()
    print("2. 浏览器扩展干扰")
    print("   解决: 使用无痕模式测试 (Ctrl+Shift+N)")
    print()
    print("3. 前端代码错误")
    print("   解决: 按F12打开控制台，查看详细错误信息")
    print()
    print("4. 后端刚重启")
    print("   解决: 等待5-10秒后刷新页面")
    print()
else:
    print("❌ 发现问题！")
    print()
    print("请确保:")
    print("1. 后端服务正在运行")
    print("2. 后端运行在端口8000")
    print("3. 没有防火墙阻止连接")
    print()
    print("重启后端:")
    print("cd ai-test-platform")
    print("py backend_api_server.py")
