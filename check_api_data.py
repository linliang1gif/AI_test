"""
检查后端API数据存储
"""
import requests
import json


print("=" * 60)
print("检查API管理数据")
print("=" * 60)

# 检查APIs
try:
    response = requests.get("http://localhost:8000/api/swagger/apis", timeout=5)
    print(f"\n1. APIs数据 (/api/swagger/apis)")
    print(f"   状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list):
            print(f"   API数量: {len(data)}")
            if data:
                print(f"\n   前3个API:")
                for i, api in enumerate(data[:3], 1):
                    print(f"   {i}. {api.get('method', 'N/A')} {api.get('path', 'N/A')}")
        else:
            print(f"   数据: {data}")
    else:
        print(f"   错误: {response.text}")
except Exception as e:
    print(f"   请求失败: {e}")

# 检查测试用例
try:
    response = requests.get("http://localhost:8000/api/test-cases", timeout=5)
    print(f"\n2. 测试用例数据 (/api/test-cases)")
    print(f"   状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list):
            print(f"   测试用例数量: {len(data)}")
            if data:
                print(f"\n   前3个测试用例:")
                for i, tc in enumerate(data[:3], 1):
                    print(f"   {i}. {tc.get('title', 'N/A')}")
        else:
            print(f"   数据: {data}")
    else:
        print(f"   错误: {response.text}")
except Exception as e:
    print(f"   请求失败: {e}")

# 检查持久化存储文件
print(f"\n3. 持久化存储文件")
import os
from pathlib import Path

storage_dir = Path("ai-test-platform/data_storage")
if storage_dir.exists():
    print(f"   存储目录: {storage_dir}")
    files = list(storage_dir.glob("*.json"))
    print(f"   文件数量: {len(files)}")
    
    for f in files:
        size = f.stat().st_size
        print(f"   - {f.name}: {size} 字节")
        
        # 读取内容
        try:
            with open(f, 'r', encoding='utf-8') as file:
                data = json.load(file)
                if isinstance(data, list):
                    print(f"     内容: 列表，长度 {len(data)}")
                elif isinstance(data, dict):
                    print(f"     内容: 字典，字段 {list(data.keys())[:5]}")
        except Exception as e:
            print(f"     读取失败: {e}")
else:
    print(f"   存储目录不存在: {storage_dir}")

print("\n" + "=" * 60)
