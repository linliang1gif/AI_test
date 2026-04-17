"""
auth模块API自动化测试脚本
自动生成于：2026-03-13 13:12:13
"""
import pytest
import requests


# 测试配置
BASE_URL = "http://localhost:8080"  # 请根据实际情况修改
DEFAULT_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def get_full_url(endpoint: str) -> str:
    """获取完整的API URL"""
    return f"{BASE_URL.rstrip('/')}{endpoint}"

def test_user_login_success():
    """测试用户登录接口 - 验证用户登录功能"""
    # 测试数据准备
    url = "http://api.example.com/api/auth/login"
    login_data = {
        "username": "admin",
        "password": "123456"
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    # 发送登录请求
    response = requests.post(url, json=login_data, headers=headers)
    
    # 断言验证
    # 1. 验证状态码为200
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}"
    
    # 2. 验证响应包含token字段
    response_json = response.json()
    assert "token" in response_json, "Response should contain 'token' field"
    
    # 3. 验证token不为空
    assert response_json["token"], "Token should not be empty"
    
    # 4. 可选：验证响应结构
    assert isinstance(response_json["token"], str), "Token should be a string"