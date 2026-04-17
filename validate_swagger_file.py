"""
验证Swagger文件格式
在上传前检查文件是否符合要求
"""
import json
import yaml
import sys
from pathlib import Path


def validate_swagger_file(file_path):
    """验证Swagger文件"""
    print(f"\n{'='*60}")
    print(f"验证文件: {file_path}")
    print('='*60)
    
    # 检查文件是否存在
    if not Path(file_path).exists():
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    # 检查文件大小
    file_size = Path(file_path).stat().st_size
    print(f"✅ 文件大小: {file_size} 字节")
    
    if file_size == 0:
        print("❌ 文件为空")
        return False
    
    # 读取文件内容
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        print("❌ 文件编码错误，请使用UTF-8编码")
        return False
    
    print(f"✅ 文件编码: UTF-8")
    
    # 尝试解析JSON
    data = None
    is_json = False
    is_yaml = False
    
    try:
        data = json.loads(content)
        is_json = True
        print("✅ 文件格式: JSON")
    except json.JSONDecodeError as e:
        print(f"⚠️ 不是有效的JSON: {e}")
        
        # 尝试YAML
        try:
            data = yaml.safe_load(content)
            is_yaml = True
            print("✅ 文件格式: YAML")
        except yaml.YAMLError as e:
            print(f"❌ 也不是有效的YAML: {e}")
            return False
    
    # 检查是否为字典
    if not isinstance(data, dict):
        print(f"❌ 文件内容必须是对象(字典)，当前是: {type(data).__name__}")
        if isinstance(data, list):
            print("   提示: 文件内容是数组，请确保根元素是对象")
        return False
    
    print("✅ 文件内容: 对象(字典)")
    
    # 检查必需的字段
    print(f"\n可用的顶级字段: {list(data.keys())}")
    
    has_swagger = 'swagger' in data
    has_openapi = 'openapi' in data
    
    if has_swagger:
        version = data.get('swagger')
        print(f"✅ Swagger版本: {version}")
    elif has_openapi:
        version = data.get('openapi')
        print(f"✅ OpenAPI版本: {version}")
    else:
        print("❌ 缺少版本字段")
        print("   必须包含 'swagger' 或 'openapi' 字段")
        print(f"   当前字段: {list(data.keys())}")
        return False
    
    # 检查info字段
    if 'info' not in data:
        print("⚠️ 缺少 'info' 字段（建议包含）")
    else:
        info = data.get('info', {})
        print(f"✅ API标题: {info.get('title', 'N/A')}")
        print(f"✅ API版本: {info.get('version', 'N/A')}")
    
    # 检查paths字段
    if 'paths' not in data:
        print("❌ 缺少 'paths' 字段")
        print("   Swagger文件必须包含API路径定义")
        return False
    
    paths = data.get('paths', {})
    api_count = sum(len([m for m in methods.keys() if m.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']]) 
                    for methods in paths.values() if isinstance(methods, dict))
    print(f"✅ API路径数量: {len(paths)}")
    print(f"✅ API方法数量: {api_count}")
    
    # 显示前3个API
    if paths:
        print(f"\n前3个API路径:")
        for i, (path, methods) in enumerate(list(paths.items())[:3]):
            if isinstance(methods, dict):
                method_list = [m.upper() for m in methods.keys() if m.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']]
                print(f"  {i+1}. {path} - {', '.join(method_list)}")
    
    print(f"\n{'='*60}")
    print("✅ 文件验证通过！可以上传")
    print('='*60)
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: py validate_swagger_file.py <swagger文件路径>")
        print("\n示例:")
        print("  py validate_swagger_file.py swagger.json")
        print("  py validate_swagger_file.py openapi.yaml")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if validate_swagger_file(file_path):
        print("\n✅ 该文件可以上传到系统")
    else:
        print("\n❌ 该文件存在问题，请修复后再上传")
        print("\n常见问题:")
        print("1. 文件必须是有效的JSON或YAML格式")
        print("2. 文件内容必须是对象({}), 不能是数组([])")
        print("3. 必须包含 'swagger' 或 'openapi' 字段")
        print("4. 必须包含 'paths' 字段定义API")
        print("5. 文件编码必须是UTF-8")
