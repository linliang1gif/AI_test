#!/usr/bin/env python3
"""
测试不同的凭证组合
"""

import requests
import base64
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_token(client_id, client_secret, username, password):
    """测试获取 Token"""
    
    token_url = "https://sit-sso.szhibu.com/oauth/token"
    
    auth_str = f"{client_id}:{client_secret}"
    auth_b64 = base64.b64encode(auth_str.encode()).decode()
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {auth_b64}"
    }
    
    data = {
        "grant_type": "password",
        "username": username,
        "password": password,
        "scope": "all"
    }
    
    print(f"\n→ 测试: {username} / {'*' * len(password)}")
    
    try:
        response = requests.post(
            token_url,
            headers=headers,
            data=data,
            timeout=10,
            verify=False
        )
        
        print(f"  状态码: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("access_token", "")
            print(f"  ✓ 成功!")
            print(f"  Token: {token[:50]}...")
            return True, token
        else:
            error_data = response.json()
            print(f"  ✗ 失败: {error_data.get('error')}")
            print(f"  描述: {error_data.get('error_description')}")
            return False, None
            
    except Exception as e:
        print(f"  ✗ 异常: {type(e).__name__}")
        return False, None

if __name__ == "__main__":
    print("="*60)
    print("测试不同的凭证组合")
    print("="*60)
    
    client_id = "sit_user_center"
    client_secret = "123456"
    
    # 测试不同的用户名/密码组合
    credentials = [
        ("ldsit", "654321"),
        ("blueRecycle", "123456"),
        ("admin", "123456"),
        ("test", "123456"),
    ]
    
    results = {}
    
    for username, password in credentials:
        success, token = test_token(client_id, client_secret, username, password)
        results[username] = success
        if success:
            break  # 找到有效凭证就停止
    
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    for username, success in results.items():
        status = "✓ 有效" if success else "✗ 无效"
        print(f"  {username}: {status}")
    
    valid_count = sum(1 for v in results.values() if v)
    
    if valid_count == 0:
        print("\n✗ 所有测试凭证都无效")
        print("\n建议:")
        print("  1. 联系蓝点项目管理员确认正确的测试账号")
        print("  2. 确认账号是否已激活")
        print("  3. 确认账号是否有权限")
        print("  4. 确认密码是否正确")
    else:
        print(f"\n✓ 找到 {valid_count} 个有效凭证")
