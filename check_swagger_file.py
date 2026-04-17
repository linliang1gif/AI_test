"""
检查已上传的Swagger文件
"""
import json
from pathlib import Path


file_path = r"ai-test-platform\swaggerApi (1).json"

print(f"检查文件: {file_path}")
print("=" * 60)

p = Path(file_path)
if not p.exists():
    print("文件不存在")
    exit(1)

print(f"文件大小: {p.stat().st_size / 1024 / 1024:.2f} MB")

# 读取文件
print("\n正在读取文件...")
with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"✅ JSON格式有效")
print(f"\n数据类型: {type(data).__name__}")

if isinstance(data, list):
    print(f"❌ 这是一个数组(列表)")
    print(f"   数组长度: {len(data)}")
    
    if data:
        print(f"\n第一个元素:")
        print(f"   类型: {type(data[0]).__name__}")
        if isinstance(data[0], dict):
            print(f"   字段: {list(data[0].keys())}")
            print(f"\n   内容示例:")
            for key, value in list(data[0].items())[:5]:
                print(f"      {key}: {str(value)[:50]}")
    
    print(f"\n💡 问题诊断:")
    print(f"   这个文件是API列表格式，不是标准的Swagger/OpenAPI格式")
    print(f"   需要转换为Swagger格式才能上传")
    
elif isinstance(data, dict):
    print(f"✅ 这是一个对象(字典)")
    print(f"\n顶级字段: {list(data.keys())}")
    
    if 'swagger' in data:
        print(f"✅ Swagger版本: {data['swagger']}")
    elif 'openapi' in data:
        print(f"✅ OpenAPI版本: {data['openapi']}")
    else:
        print(f"❌ 缺少版本字段")
    
    if 'paths' in data:
        print(f"✅ 包含paths字段")
        print(f"   API数量: {len(data['paths'])}")
