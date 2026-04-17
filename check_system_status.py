"""检查AI测试平台系统状态"""
import requests
import subprocess
import time

print("=" * 60)
print("AI测试平台系统状态检查")
print("=" * 60)
print()

# 检查后端服务
print("1. 检查后端服务 (端口8000)...")
try:
    response = requests.get("http://localhost:8000/health", timeout=3)
    if response.status_code == 200:
        print("✅ 后端服务正常运行")
        print(f"   响应: {response.json()}")
    else:
        print(f"⚠️  后端服务响应异常: {response.status_code}")
except requests.exceptions.ConnectionError:
    print("❌ 后端服务未运行")
    print("   请运行: cd ai-test-platform && py backend_api_server.py")
except Exception as e:
    print(f"❌ 后端检查失败: {e}")

print()

# 检查前端服务
print("2. 检查前端服务 (端口5173)...")
try:
    response = requests.get("http://localhost:5173", timeout=3)
    if response.status_code == 200:
        print("✅ 前端服务正常运行")
    else:
        print(f"⚠️  前端服务响应异常: {response.status_code}")
except requests.exceptions.ConnectionError:
    print("❌ 前端服务未运行")
    print("   请运行: cd ai-test-platform/frontend && npm run dev")
except Exception as e:
    print(f"❌ 前端检查失败: {e}")

print()

# 检查关键API端点
print("3. 检查关键API端点...")
endpoints = [
    ("项目列表", "GET", "http://localhost:8000/api/projects"),
    ("API列表", "GET", "http://localhost:8000/api/apis"),
    ("测试用例", "GET", "http://localhost:8000/api/test-cases"),
    ("自动化脚本", "GET", "http://localhost:8000/api/automation/scripts"),
]

for name, method, url in endpoints:
    try:
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            count = len(data.get('projects', data.get('apis', data.get('scripts', []))))
            print(f"✅ {name}: {count} 条数据")
        else:
            print(f"⚠️  {name}: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ {name}: {str(e)[:50]}")

print()

# 检查数据文件
print("4. 检查数据文件...")
import os
from pathlib import Path

data_file = Path("ai-test-platform/data/platform_data.json")
if data_file.exists():
    print(f"✅ 数据文件存在: {data_file}")
    size = data_file.stat().st_size / 1024
    print(f"   文件大小: {size:.1f} KB")
else:
    print(f"❌ 数据文件不存在: {data_file}")

print()

# 检查端口占用
print("5. 检查端口占用...")
try:
    result = subprocess.run(
        ["netstat", "-ano"],
        capture_output=True,
        text=True,
        timeout=5
    )
    
    lines = result.stdout.split('\n')
    
    # 检查8000端口
    port_8000 = [line for line in lines if ':8000' in line and 'LISTENING' in line]
    if port_8000:
        print("✅ 端口8000正在监听 (后端)")
    else:
        print("❌ 端口8000未监听")
    
    # 检查5173端口
    port_5173 = [line for line in lines if ':5173' in line and 'LISTENING' in line]
    if port_5173:
        print("✅ 端口5173正在监听 (前端)")
    else:
        print("❌ 端口5173未监听")
        
except Exception as e:
    print(f"⚠️  无法检查端口: {e}")

print()
print("=" * 60)
print("检查完成！")
print("=" * 60)
print()

# 给出建议
print("💡 下一步建议:")
print()

# 检查是否需要启动服务
try:
    backend_ok = requests.get("http://localhost:8000/health", timeout=2).status_code == 200
except:
    backend_ok = False

try:
    frontend_ok = requests.get("http://localhost:5173", timeout=2).status_code == 200
except:
    frontend_ok = False

if not backend_ok:
    print("1. 启动后端服务:")
    print("   cd ai-test-platform")
    print("   py backend_api_server.py")
    print()

if not frontend_ok:
    print("2. 启动前端服务:")
    print("   cd ai-test-platform/frontend")
    print("   npm run dev")
    print()

if backend_ok and frontend_ok:
    print("✅ 所有服务正常运行！")
    print()
    print("访问: http://localhost:5173")
    print()
    print("如果功能还是用不了，请告诉我:")
    print("- 哪个功能用不了？")
    print("- 点击后有什么反应？")
    print("- 浏览器控制台有什么错误？(按F12查看)")
