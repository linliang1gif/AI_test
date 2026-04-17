"""
交互式文件验证工具
支持拖放文件路径
"""
import json
import yaml
from pathlib import Path


def clean_path(path_str):
    """清理路径字符串"""
    # 移除引号
    path_str = path_str.strip().strip('"').strip("'")
    return path_str


def validate_file(file_path):
    """验证文件"""
    print(f"\n{'='*60}")
    print(f"验证文件: {file_path}")
    print('='*60)
    
    p = Path(file_path)
    
    if not p.exists():
        print(f"❌ 文件不存在")
        print(f"\n尝试的路径: {p.absolute()}")
        return False
    
    print(f"✅ 文件存在")
    file_size = p.stat().st_size
    print(f"✅ 文件大小: {file_size} 字节")
    
    if file_size == 0:
        print("❌ 文件为空")
        return False
    
    # 读取文件
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='gbk') as f:
                content = f.read()
            print("⚠️ 文件编码: GBK (建议使用UTF-8)")
        except Exception as e:
            print(f"❌ 无法读取文件: {e}")
            return False
    except Exception as e:
        print(f"❌ 读取文件错误: {e}")
        return False
    
    print(f"✅ 文件读取成功")
    print(f"\n文件前200个字符:")
    print("-" * 60)
    print(content[:200])
    print("-" * 60)
    
    # 解析JSON
    data = None
    try:
        data = json.loads(content)
        print(f"\n✅ JSON格式有效")
    except json.JSONDecodeError as e:
        print(f"\n❌ JSON格式无效: {e}")
        
        # 尝试YAML
        try:
            data = yaml.safe_load(content)
            print(f"✅ YAML格式有效")
        except Exception as e:
            print(f"❌ YAML格式也无效: {e}")
            return False
    
    # 检查数据类型
    print(f"\n数据类型: {type(data).__name__}")
    
    if isinstance(data, list):
        print(f"❌ 文件内容是数组(列表) - 这就是问题所在!")
        print(f"   数组长度: {len(data)}")
        
        if data and isinstance(data[0], dict):
            print(f"\n   第一个元素的字段: {list(data[0].keys())[:10]}")
            print(f"\n💡 解决方案:")
            print(f"   这个文件是API列表，需要转换为Swagger格式")
            print(f"   是否需要我帮你转换? (输入 yes)")
        
        return False
    
    elif isinstance(data, dict):
        print(f"✅ 文件内容是对象(字典)")
        print(f"\n顶级字段: {list(data.keys())}")
        
        # 检查版本字段
        if 'swagger' in data:
            print(f"✅ Swagger版本: {data['swagger']}")
        elif 'openapi' in data:
            print(f"✅ OpenAPI版本: {data['openapi']}")
        else:
            print(f"❌ 缺少版本字段 (swagger 或 openapi)")
            print(f"   当前字段: {list(data.keys())}")
            return False
        
        # 检查paths
        if 'paths' in data:
            paths = data['paths']
            print(f"✅ 包含 paths 字段")
            print(f"   API数量: {len(paths)}")
        else:
            print(f"❌ 缺少 paths 字段")
            return False
        
        print(f"\n{'='*60}")
        print(f"✅ 文件验证通过！可以上传")
        print('='*60)
        return True
    
    else:
        print(f"❌ 未知的数据类型: {type(data)}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Swagger文件验证工具")
    print("=" * 60)
    print("\n请输入文件路径（可以直接拖放文件到这里）:")
    print("或按 Ctrl+C 退出\n")
    
    while True:
        try:
            file_path = input("文件路径: ").strip()
            
            if not file_path:
                print("请输入文件路径")
                continue
            
            # 清理路径
            file_path = clean_path(file_path)
            
            # 验证文件
            result = validate_file(file_path)
            
            if result:
                print("\n✅ 该文件可以上传到系统")
            else:
                print("\n❌ 该文件存在问题，无法上传")
            
            print("\n" + "=" * 60)
            print("继续验证其他文件? (输入文件路径，或按 Ctrl+C 退出)")
            print("=" * 60 + "\n")
            
        except KeyboardInterrupt:
            print("\n\n再见!")
            break
        except Exception as e:
            print(f"\n错误: {e}")
            print("请重试\n")
