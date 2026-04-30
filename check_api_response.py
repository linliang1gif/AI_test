"""检查API响应结构"""
import requests
import json

response = requests.get("http://localhost:8000/api/test-cases")
print(f"状态码: {response.status_code}")
print(f"响应类型: {type(response.json())}")

data = response.json()
print(f"\n响应的键: {data.keys() if isinstance(data, dict) else 'Not a dict'}")

if isinstance(data, dict):
    for key in data.keys():
        value = data[key]
        print(f"\n{key}: {type(value)}")
        if isinstance(value, list):
            print(f"  列表长度: {len(value)}")
            if len(value) > 0:
                print(f"  第一个元素: {type(value[0])}")
                if isinstance(value[0], dict):
                    print(f"  第一个元素的键: {list(value[0].keys())[:5]}")
