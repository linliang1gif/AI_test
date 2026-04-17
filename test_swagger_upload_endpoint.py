"""
测试Swagger上传API端点
"""
import requests
import json
import tempfile
from pathlib import Path


BASE_URL = "http://localhost:8000"


def test_upload_valid_swagger():
    """测试上传有效的Swagger文件"""
    print("\n=== 测试1: 上传有效的Swagger 2.0文件 ===")
    
    swagger_doc = {
        "swagger": "2.0",
        "info": {
            "title": "测试API",
            "version": "1.0.0",
            "description": "这是一个测试API"
        },
        "basePath": "/api/v1",
        "paths": {
            "/users": {
                "get": {
                    "summary": "获取用户列表",
                    "description": "返回所有用户",
                    "tags": ["用户管理"],
                    "responses": {
                        "200": {
                            "description": "成功"
                        }
                    }
                },
                "post": {
                    "summary": "创建用户",
                    "description": "创建新用户",
                    "tags": ["用户管理"],
                    "parameters": [
                        {
                            "name": "body",
                            "in": "body",
                            "required": True,
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "email": {"type": "string"}
                                }
                            }
                        }
                    ],
                    "responses": {
                        "201": {
                            "description": "创建成功"
                        }
                    }
                }
            }
        }
    }
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as f:
        json.dump(swagger_doc, f, ensure_ascii=False, indent=2)
        temp_path = f.name
    
    try:
        # 上传文件
        with open(temp_path, 'rb') as f:
            files = {'file': ('swagger.json', f, 'application/json')}
            response = requests.post(f"{BASE_URL}/api/swagger/upload", files=files)
        
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result.get('success'):
            print(f"✅ 成功: 解析了 {result.get('count')} 个API")
            return True
        else:
            print(f"❌ 失败: {result.get('message')}")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False
    finally:
        Path(temp_path).unlink()


def test_upload_invalid_swagger():
    """测试上传无效的Swagger文件（缺少版本键）"""
    print("\n=== 测试2: 上传无效的Swagger文件 ===")
    
    invalid_doc = {
        "info": {"title": "测试API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {
                    "summary": "获取用户",
                    "responses": {"200": {"description": "成功"}}
                }
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as f:
        json.dump(invalid_doc, f, ensure_ascii=False, indent=2)
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as f:
            files = {'file': ('invalid.json', f, 'application/json')}
            response = requests.post(f"{BASE_URL}/api/swagger/upload", files=files)
        
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if not result.get('success') and "版本" in result.get('message', ''):
            print(f"✅ 正确返回错误: {result.get('message')}")
            return True
        else:
            print(f"❌ 未正确处理错误")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False
    finally:
        Path(temp_path).unlink()


def test_upload_openapi_3():
    """测试上传OpenAPI 3.0文件"""
    print("\n=== 测试3: 上传OpenAPI 3.0文件 ===")
    
    openapi_doc = {
        "openapi": "3.0.0",
        "info": {
            "title": "测试API",
            "version": "1.0.0"
        },
        "servers": [
            {"url": "http://localhost:8080/api"}
        ],
        "paths": {
            "/products": {
                "get": {
                    "summary": "获取产品列表",
                    "responses": {
                        "200": {
                            "description": "成功",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "id": {"type": "integer"},
                                                "name": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as f:
        json.dump(openapi_doc, f, ensure_ascii=False, indent=2)
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as f:
            files = {'file': ('openapi.json', f, 'application/json')}
            response = requests.post(f"{BASE_URL}/api/swagger/upload", files=files)
        
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result.get('success'):
            print(f"✅ 成功: 解析了 {result.get('count')} 个API")
            return True
        else:
            print(f"❌ 失败: {result.get('message')}")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False
    finally:
        Path(temp_path).unlink()


def test_upload_empty_file():
    """测试上传空文件"""
    print("\n=== 测试4: 上传空文件 ===")
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        f.write("")
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as f:
            files = {'file': ('empty.json', f, 'application/json')}
            response = requests.post(f"{BASE_URL}/api/swagger/upload", files=files)
        
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if not result.get('success'):
            print(f"✅ 正确返回错误: {result.get('message')}")
            return True
        else:
            print(f"❌ 应该返回错误但没有")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False
    finally:
        Path(temp_path).unlink()


if __name__ == "__main__":
    print("=" * 60)
    print("Swagger上传API端点测试")
    print("=" * 60)
    
    # 检查后端是否运行
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        print(f"✅ 后端服务运行中 (状态码: {response.status_code})")
    except Exception as e:
        print(f"❌ 后端服务未运行: {e}")
        print("请先启动后端服务: cd ai-test-platform && py backend_api_server.py")
        exit(1)
    
    results = []
    
    # 运行所有测试
    results.append(("上传有效Swagger 2.0", test_upload_valid_swagger()))
    results.append(("上传无效Swagger", test_upload_invalid_swagger()))
    results.append(("上传OpenAPI 3.0", test_upload_openapi_3()))
    results.append(("上传空文件", test_upload_empty_file()))
    
    # 统计结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过!")
    else:
        print(f"\n⚠️ {total - passed} 个测试失败")
