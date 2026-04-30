#!/usr/bin/env python3
"""
OAuth2 鉴权诊断脚本
测试不同的凭证和配置组合
"""

import requests
import base64
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_oauth2(client_id, client_secret, username, password, token_url):
    """测试 OAuth2 Token 获取"""
    
    print(f"\n{'='*60}")
    print(f"测试配置:")
    print(f"  Token URL: {token_url}")
    print(f"  Client ID: {client_id}")
    print(f"  Client Secret: {client_secret}")
    print(f"  Username: {username}")
    print(f"  Password: {'*' * len(password)}")
    print(f"{'='*60}")
    
    # 方式1: Basic Auth
    print("\n→ 方式1: Basic Auth (标准方式)")
    try:
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
        
        print(f"  Headers: {headers}")
        print(f"  Data: grant_type=password&username={username}&password=***&scope=all")
        
        response = requests.post(
            token_url,
            headers=headers,
            data=data,
            timeout=10,
            verify=False
        )
        
        print(f"  状态码: {response.status_code}")
        print(f"  响应: {response.text[:500]}")
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"\n✓ 成功获取 Token")
            print(f"  Access Token: {token_data.get('access_token', '')[:50]}...")
            print(f"  Token Type: {token_data.get('token_type')}")
            print(f"  Expires In: {token_data.get('expires_in')} 秒")
            return True, token_data.get('access_token')
        else:
            print(f"\n✗ 失败")
            return False, None
            
    except Exception as e:
        print(f"\n✗ 异常: {type(e).__name__}: {str(e)}")
        return False, None
    
    # 方式2: 在 Body 中传递 client_id 和 client_secret
    print("\n→ 方式2: Client 凭证在 Body 中")
    try:
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "password",
            "client_id": client_id,
            "client_secret": client_secret,
            "username": username,
            "password": password,
            "scope": "all"
        }
        
        response = requests.post(
            token_url,
            headers=headers,
            data=data,
            timeout=10,
            verify=False
        )
        
        print(f"  状态码: {response.status_code}")
        print(f"  响应: {response.text[:500]}")
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"\n✓ 成功获取 Token")
            return True, token_data.get('access_token')
        else:
            print(f"\n✗ 失败")
            return False, None
            
    except Exception as e:
        print(f"\n✗ 异常: {type(e).__name__}: {str(e)}")
        return False, None

def test_with_token(token, base_url):
    """使用 Token 测试接口"""
    
    print(f"\n{'='*60}")
    print(f"使用 Token 测试接口")
    print(f"{'='*60}")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # 测试列表接口
    print(f"\n→ 测试币别列表接口")
    try:
        response = requests.post(
            f"{base_url}/basic/basicCurrency/list",
            json={},
            headers=headers,
            timeout=10,
            verify=False
        )
        
        print(f"  状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                currency_list = data.get("data", [])
                print(f"✓ 成功，返回 {len(currency_list)} 条币别")
                return True
            else:
                print(f"✗ 接口返回错误: {data.get('message')}")
                return False
        else:
            print(f"✗ 失败: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"✗ 异常: {type(e).__name__}: {str(e)}")
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print(" " * 15 + "OAuth2 鉴权诊断")
    print("="*60)
    
    # 配置
    token_url = "https://sit-sso.szhibu.com/oauth/token"
    base_url = "https://dev-recycle.szhibu.com/dev-api/recycle"
    
    # 测试配置1: 新账号
    print("\n\n" + "#"*60)
    print("# 测试配置 1: ldsit / 654321")
    print("#"*60)
    
    success, token = test_oauth2(
        client_id="sit_user_center",
        client_secret="123456",
        username="ldsit",
        password="654321",
        token_url=token_url
    )
    
    if success and token:
        test_with_token(token, base_url)
    
    # 测试配置2: 旧账号（对比）
    print("\n\n" + "#"*60)
    print("# 测试配置 2: blueRecycle / 123456 (对比)")
    print("#"*60)
    
    success2, token2 = test_oauth2(
        client_id="sit_user_center",
        client_secret="123456",
        username="blueRecycle",
        password="123456",
        token_url=token_url
    )
    
    if success2 and token2:
        test_with_token(token2, base_url)
    
    # 总结
    print("\n\n" + "="*60)
    print(" " * 20 + "诊断总结")
    print("="*60)
    
    if success:
        print("\n✓ 配置1 (ldsit) 可用")
    else:
        print("\n✗ 配置1 (ldsit) 不可用")
    
    if success2:
        print("✓ 配置2 (blueRecycle) 可用")
    else:
        print("✗ 配置2 (blueRecycle) 不可用")
    
    if not success and not success2:
        print("\n建议:")
        print("  1. 确认用户名和密码是否正确")
        print("  2. 确认账号是否已激活")
        print("  3. 确认 Client ID 和 Secret 是否正确")
        print("  4. 联系管理员确认账号状态")
