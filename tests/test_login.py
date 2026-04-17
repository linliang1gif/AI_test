"""
login模块API自动化测试脚本
自动生成于：2026-03-13 15:46:15
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

def test_unauthorized_access_order_details():
    """TC021-验证未登录及无权限用户尝试访问或操作订单的拦截"""
    
    # 测试数据准备
    base_url = "http://api.example.com"
    order_id = "ORD123456"  # 假设存在的订单ID
    
    # 场景1: 未登录状态下访问订单详情
    url_without_auth = f"{base_url}/api/orders/{order_id}"
    
    # 发送请求（未添加认证头）
    response_unauth = requests.get(url_without_auth)
    
    # 断言验证：未登录应被拦截
    # 通常返回401未授权或403禁止访问，或重定向到登录页
    assert response_unauth.status_code in [401, 403, 302], \
        f"未登录访问应被拦截，实际状态码: {response_unauth.status_code}"
    
    # 如果返回302重定向，检查是否重定向到登录页
    if response_unauth.status_code == 302:
        location = response_unauth.headers.get('Location', '')
        assert 'login' in location.lower(), \
            f"未登录应重定向到登录页，实际重定向到: {location}"
    
    # 场景2: 使用无权限账号访问订单详情
    # 准备无权限账号的认证信息
    unauthorized_user_credentials = {
        "username": "no_permission_user",
        "password": "test123"
    }
    
    # 先登录获取token（假设系统使用token认证）
    login_url = f"{base_url}/api/auth/login"
    login_response = requests.post(login_url, json=unauthorized_user_credentials)
    
    # 假设登录成功但用户无权限
    if login_response.status_code == 200:
        auth_token = login_response.json().get('token', '')
        
        # 使用无权限token访问订单详情
        headers_with_unauth_token = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
        
        response_no_permission = requests.get(
            url_without_auth, 
            headers=headers_with_unauth_token
        )
        
        # 断言验证：无权限用户应被拦截
        assert response_no_permission.status_code in [403, 404], \
            f"无权限用户访问应被拦截，实际状态码: {response_no_permission.status_code}"
        
        # 验证响应内容不包含订单详情
        response_data = response_no_permission.json()
        assert 'order_id' not in response_data, \
            "无权限用户不应看到订单ID"
        assert 'order_details' not in response_data, \
            "无权限用户不应看到订单详情"
        
        # 验证错误信息
        if 'error' in response_data:
            assert 'permission' in response_data['error'].lower() or \
                   'access' in response_data['error'].lower() or \
                   'unauthorized' in response_data['error'].lower(), \
                f"错误信息应包含权限相关提示，实际: {response_data['error']}"
    
    # 场景3: 尝试修改操作（如果意外进入页面）
    # 假设订单更新接口
    update_url = f"{base_url}/api/orders/{order_id}"
    update_data = {
        "status": "cancelled",
        "notes": "尝试无权限修改"
    }
    
    # 使用无权限token尝试更新
    update_response = requests.put(
        update_url,
        json=update_data,
        headers=headers_with_unauth_token
    )
    
    # 断言验证：无权限修改应被拒绝
    assert update_response.status_code in [403, 401], \
        f"无权限修改应被拒绝，实际状态码: {update_response.status_code}"
    
    # 验证修改未成功
    if update_response.status_code == 403:
        error_data = update_response.json()
        assert 'error' in error_data or 'message' in error_data, \
            "权限错误应返回错误信息"