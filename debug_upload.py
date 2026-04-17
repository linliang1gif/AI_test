"""
调试Swagger上传问题
模拟前端上传，查看详细错误
"""
import requests
import json


def test_upload_with_file(file_path):
    """测试上传指定文件"""
    print(f"\n=== 测试上传文件: {file_path} ===")
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path, f, 'application/json')}
            response = requests.post("http://localhost:8000/api/swagger/upload", files=files)
        
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        return result
    except Exception as e:
        print(f"错误: {e}")
        return None


def create_test_swagger():
    """创建一个测试用的Swagger文件"""
    swagger = {
        "swagger": "2.0",
        "info": {
            "title": "测试API",
            "version": "1.0.0"
        },
        "basePath": "/api",
        "paths": {
            "/users": {
                "get": {
                    "summary": "获取用户列表",
                    "responses": {
                        "200": {
                            "description": "成功"
                        }
                    }
                }
            }
        }
    }
    
    # 保存为文件
    with open("test_swagger_valid.json", "w", encoding="utf-8") as f:
        json.dump(swagger, f, ensure_ascii=False, indent=2)
    
    print("✅ 创建了测试文件: test_swagger_valid.json")
    return "test_swagger_valid.json"


if __name__ == "__main__":
    print("=" * 60)
    print("Swagger上传调试")
    print("=" * 60)
    
    # 创建测试文件
    test_file = create_test_swagger()
    
    # 测试上传
    result = test_upload_with_file(test_file)
    
    if result and result.get('success'):
        print("\n✅ 上传成功!")
        print(f"解析了 {result.get('count')} 个API")
    else:
        print("\n❌ 上传失败")
        if result:
            print(f"错误信息: {result.get('message')}")
        
        print("\n请检查:")
        print("1. 文件格式是否正确（必须是JSON或YAML）")
        print("2. 文件内容是否包含 'swagger' 或 'openapi' 字段")
        print("3. 文件是否为空")
        print("4. 后端服务是否正常运行")
