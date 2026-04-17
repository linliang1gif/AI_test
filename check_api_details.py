"""检查API详细信息"""
import requests
import json

response = requests.get("http://localhost:8000/api/apis")
data = response.json()

print(f"总API数: {data['count']}")
print("\n检查前5个API的详细信息:")
print("=" * 80)

for i, api in enumerate(data['apis'][:5], 1):
    print(f"\n{i}. {api['method']} {api['path']}")
    print(f"   名称: {api.get('name', 'N/A')}")
    print(f"   参数数量: {len(api.get('parameters', []))}")
    print(f"   有requestBody: {api.get('requestBody') is not None}")
    
    if api.get('parameters'):
        print(f"   参数列表:")
        for param in api['parameters'][:3]:
            print(f"     - {param.get('name')} ({param.get('type')}) in {param.get('in')}")
    
    if api.get('requestBody'):
        rb = api['requestBody']
        print(f"   requestBody:")
        print(f"     - content_type: {rb.get('content_type')}")
        print(f"     - required: {rb.get('required')}")
        if rb.get('schema'):
            schema = rb['schema']
            if 'properties' in schema:
                print(f"     - properties: {len(schema['properties'])} 个字段")
                for prop_name in list(schema['properties'].keys())[:3]:
                    prop = schema['properties'][prop_name]
                    print(f"       * {prop_name}: {prop.get('type', 'unknown')}")
