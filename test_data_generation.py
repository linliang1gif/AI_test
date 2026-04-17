"""测试数据生成功能"""
import requests
import json

print("=" * 80)
print("测试数据生成功能")
print("=" * 80)

# 1. 获取一个API
print("\n1. 获取API列表...")
response = requests.get("http://localhost:8000/api/apis")
data = response.json()
print(f"   总共 {data['count']} 个API")

# 选择第一个有requestBody的API
api = None
for a in data['apis']:
    if a.get('requestBody') and a['requestBody'].get('schema', {}).get('properties'):
        api = a
        break

if not api:
    print("❌ 没有找到带requestBody的API")
    exit(1)

print(f"\n2. 选择的API:")
print(f"   {api['method']} {api['path']}")
print(f"   名称: {api['name']}")

# 3. 提取schema
print(f"\n3. 提取参数schema...")
schema = {}
if api.get('requestBody') and api['requestBody'].get('schema'):
    rb_schema = api['requestBody']['schema']
    if rb_schema.get('properties'):
        for key, prop in rb_schema['properties'].items():
            schema[key] = prop.get('type', 'string')

print(f"   Schema: {json.dumps(schema, indent=2, ensure_ascii=False)}")

if not schema:
    print("❌ 无法提取schema")
    exit(1)

# 4. 调用生成接口
print(f"\n4. 调用测试数据生成接口...")
gen_response = requests.post(
    "http://localhost:8000/api/test-data/smart-object",
    json={
        "data_schema": schema,
        "context": {
            "api_path": api['path'],
            "api_method": api['method']
        }
    }
)

print(f"   状态码: {gen_response.status_code}")

if gen_response.status_code == 200:
    result = gen_response.json()
    print(f"   成功: {result.get('success')}")
    print(f"\n5. 生成的数据:")
    print(json.dumps(result.get('data'), indent=2, ensure_ascii=False))
else:
    print(f"❌ 生成失败")
    print(f"   响应: {gen_response.text}")
