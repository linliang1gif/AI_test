"""
检查文件并验证
"""
import sys
import json
from pathlib import Path


file_path = r"D:\360Downloads\蓝点 api.json"

print(f"检查文件: {file_path}")
print("=" * 60)

# 检查文件是否存在
p = Path(file_path)
print(f"文件存在: {p.exists()}")

if p.exists():
    print(f"文件大小: {p.stat().st_size} 字节")
    
    # 读取前100个字符
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"\n文件总长度: {len(content)} 字符")
            print(f"\n文件前200个字符:")
            print("-" * 60)
            print(content[:200])
            print("-" * 60)
            
            # 尝试解析JSON
            try:
                data = json.loads(content)
                print(f"\n✅ JSON格式有效")
                print(f"数据类型: {type(data).__name__}")
                
                if isinstance(data, dict):
                    print(f"✅ 是对象(字典)")
                    print(f"顶级字段: {list(data.keys())[:10]}")
                elif isinstance(data, list):
                    print(f"❌ 是数组(列表) - 这就是问题所在!")
                    print(f"数组长度: {len(data)}")
                    if data:
                        print(f"第一个元素类型: {type(data[0]).__name__}")
                        if isinstance(data[0], dict):
                            print(f"第一个元素的字段: {list(data[0].keys())[:10]}")
            except json.JSONDecodeError as e:
                print(f"\n❌ JSON格式无效: {e}")
                
    except Exception as e:
        print(f"读取文件错误: {e}")
else:
    print("文件不存在，可能的原因:")
    print("1. 路径错误")
    print("2. 文件名包含特殊字符")
    print("3. 文件已被移动或删除")
