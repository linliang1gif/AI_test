"""
添加示例API数据
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# 示例API数据
sample_apis = [
    {
        "method": "POST",
        "path": "/api/users",
        "summary": "创建用户",
        "description": "创建一个新用户账号",
        "tags": ["用户管理"],
        "parameters": [
            {"name": "username", "type": "string", "required": True},
            {"name": "email", "type": "string", "required": True},
            {"name": "password", "type": "string", "required": True},
            {"name": "age", "type": "integer", "required": False}
        ]
    },
    {
        "method": "GET",
        "path": "/api/users/{id}",
        "summary": "获取用户信息",
        "description": "根据用户ID获取用户详细信息",
        "tags": ["用户管理"],
        "parameters": [
            {"name": "id", "type": "integer", "required": True, "in": "path"}
        ]
    },
    {
        "method": "POST",
        "path": "/api/orders",
        "summary": "创建订单",
        "description": "创建一个新订单",
        "tags": ["订单管理"],
        "parameters": [
            {"name": "user_id", "type": "integer", "required": True},
            {"name": "product_id", "type": "integer", "required": True},
            {"name": "quantity", "type": "integer", "required": True},
            {"name": "total_price", "type": "number", "required": True}
        ]
    },
    {
        "method": "GET",
        "path": "/api/products",
        "summary": "获取产品列表",
        "description": "获取所有产品列表",
        "tags": ["产品管理"],
        "parameters": [
            {"name": "page", "type": "integer", "required": False},
            {"name": "page_size", "type": "integer", "required": False},
            {"name": "category", "type": "string", "required": False}
        ]
    }
]

def add_apis():
    """添加示例API"""
    print("添加示例API数据...")
    print("=" * 60)
    
    for api in sample_apis:
        print(f"\n添加: {api['method']} {api['path']}")
        
        # 这里我们直接通过后端的数据管理器添加
        # 因为没有专门的添加API的接口,我们需要模拟Swagger解析的结果
        
    print("\n" + "=" * 60)
    print("提示: 由于没有直接添加API的接口,")
    print("请使用以下方法之一添加API:")
    print("\n方法1: 上传Swagger文档")
    print("  - 在前端 'API管理' 页面")
    print("  - 点击 '文件上传' 或 'URL导入'")
    print("  - 上传Swagger JSON/YAML文件")
    print("\n方法2: 手动创建测试Swagger文件")
    print("  - 我可以帮你创建一个示例Swagger文件")
    print("  - 然后在前端上传这个文件")
    
    return sample_apis

def create_swagger_file():
    """创建示例Swagger文件"""
    swagger_doc = {
        "swagger": "2.0",
        "info": {
            "title": "示例API",
            "version": "1.0.0",
            "description": "用于测试的示例API文档"
        },
        "host": "api.example.com",
        "basePath": "/v1",
        "schemes": ["https"],
        "paths": {}
    }
    
    # 添加API路径
    for api in sample_apis:
        path = api['path']
        method = api['method'].lower()
        
        if path not in swagger_doc['paths']:
            swagger_doc['paths'][path] = {}
        
        # 构建参数
        parameters = []
        for param in api.get('parameters', []):
            param_def = {
                "name": param['name'],
                "in": param.get('in', 'query'),
                "required": param.get('required', False),
                "type": param['type']
            }
            parameters.append(param_def)
        
        swagger_doc['paths'][path][method] = {
            "summary": api['summary'],
            "description": api['description'],
            "tags": api.get('tags', []),
            "parameters": parameters,
            "responses": {
                "200": {
                    "description": "成功"
                }
            }
        }
    
    # 保存文件
    filename = "sample_swagger.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(swagger_doc, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 已创建Swagger文件: {filename}")
    print(f"\n📝 使用方法:")
    print(f"1. 打开浏览器: http://localhost:5174/")
    print(f"2. 进入 'API管理' 页面")
    print(f"3. 点击 '📁 文件上传' 标签")
    print(f"4. 上传文件: {filename}")
    print(f"5. 等待解析完成")
    print(f"6. 在API列表中查看 '🏭 测试数据' 按钮")
    
    return filename

def main():
    print("=" * 60)
    print("示例API数据准备")
    print("=" * 60)
    
    apis = add_apis()
    filename = create_swagger_file()
    
    print("\n" + "=" * 60)
    print("准备完成!")
    print("=" * 60)

if __name__ == "__main__":
    main()
