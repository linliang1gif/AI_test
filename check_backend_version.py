"""
检查后端是否使用了最新代码
"""
import requests
import json
import tempfile
from pathlib import Path


BASE_URL = "http://localhost:8000"


def check_backend_running():
    """检查后端是否运行"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def check_error_handling():
    """检查错误处理是否已更新"""
    print("\n=== 检查错误处理是否已更新 ===")
    
    # 创建一个缺少版本键的无效文件
    invalid_doc = {
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {"/test": {"get": {"responses": {"200": {"description": "OK"}}}}}
    }
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as f:
        json.dump(invalid_doc, f)
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as f:
            files = {'file': ('test.json', f, 'application/json')}
            response = requests.post(f"{BASE_URL}/api/swagger/upload", files=files)
        
        result = response.json()
        error_msg = result.get('message', '')
        
        print(f"状态码: {response.status_code}")
        print(f"错误信息: {error_msg}")
        
        # 检查是否包含详细的错误信息
        if response.status_code == 400 and ("版本" in error_msg or "Available keys" in error_msg):
            print("\n✅ 后端已更新 - 返回详细的错误信息")
            return True
        elif response.status_code == 500 and error_msg == "上传失败: Unknown spec version":
            print("\n❌ 后端未更新 - 仍返回旧的错误信息")
            print("请重启后端服务:")
            print("  1. 停止当前后端 (Ctrl+C)")
            print("  2. cd ai-test-platform")
            print("  3. py backend_api_server.py")
            return False
        else:
            print(f"\n⚠️ 未知状态 - 状态码: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False
    finally:
        Path(temp_path).unlink()


if __name__ == "__main__":
    print("=" * 60)
    print("后端版本检查")
    print("=" * 60)
    
    if not check_backend_running():
        print("❌ 后端服务未运行")
        print("请启动后端: cd ai-test-platform && py backend_api_server.py")
        exit(1)
    
    print("✅ 后端服务运行中")
    
    if check_error_handling():
        print("\n" + "=" * 60)
        print("🎉 后端已使用最新代码!")
        print("=" * 60)
        print("\n可以继续测试:")
        print("  py test_swagger_upload_endpoint.py")
    else:
        print("\n" + "=" * 60)
        print("⚠️ 需要重启后端服务")
        print("=" * 60)
