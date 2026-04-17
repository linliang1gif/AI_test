#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
解析JWT Token并创建基于token的API测试
"""

import json
import base64
import requests
from datetime import datetime

def decode_jwt_payload(token):
    """解析JWT token的payload部分"""
    try:
        # JWT格式: header.payload.signature
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        # 解码payload (第二部分)
        payload = parts[1]
        # 添加padding如果需要
        payload += '=' * (4 - len(payload) % 4)
        
        # Base64解码
        decoded_bytes = base64.urlsafe_b64decode(payload)
        decoded_str = decoded_bytes.decode('utf-8')
        
        # 解析JSON
        payload_data = json.loads(decoded_str)
        return payload_data
        
    except Exception as e:
        print(f"解析JWT失败: {e}")
        return None

def test_api_with_token():
    """使用token测试API接口"""
    token = "yJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdXBwbGllcklkIjoiIiwidXNlcl9uYW1lIjoibGRzaXQiLCJtb2JpbGUiOiIxMzU0MjY1ODk2MyIsImF2YXRhciI6bnVsbCwidXNlcklkIjoiMTE2ZDMyYTY0MGIwNGE1NWJkMTViMWI5MTBmY2Y3NzgiLCJ1dWlkIjoiMDg4ZWU1YjcwY2EyNDdiN2FiMWEyNDNlYTQ2NGM5MmEiLCJjbGllbnRfaWQiOiJkZXZfYmx1ZV9yZWN5Y2xlIiwidXJsIjpudWxsLCJyZWFsTmFtZSI6Imxkc2l0IiwiYXVkIjpbIkRFRkFVTFRfUkVTT1VSQ0VfSUQiXSwicGluIjoiMTAxNCIsInNjb3BlIjpbImFsbCJdLCJ3c3QiOiJ3c0xBQWN6TEFzREJ5QXZJd1FMS3lnc0J3c29Md2d2RHdzZ0FEQUROemNmT3dzakN3YzRQQWR3RDBjNEJDdENwQ3cvYUNxbmJDZ3pUREE4S3pzakh4d29LeWd2TnlBd0N5OEhOQzgwQ0M4SUN5OEhNQ2dMQndNRU13OHNDIiwiaWQiOjE5OTMxMzE3MjI5MTY4OTI2NzQsImV4cCI6MTc3NDI0NjgxOCwianRpIjoiMzc3MGM5MGEtMDZmOS00Y2E1LWJjZWYtMmU2ZTY4N2ZmNDUxIiwiZW1haWwiOiIxMzU0MjY1ODk2M0BxcS5jb20ifQ.vAnbvo_pUUfkmQcFUf8lpmktp6ZdY9mIYqqVc6M-4TrgllPsuREak8yMfC81Mvt5pL9nOu5PYMW0Idh7QIVZ-nGs-958__dTHLZ13RFjkPdt21_wIdxrj1pzfkAtuFyd-pETWiIIBIjsN0TmEFunODmy5zIAKQ5PBeTQbkOPNZU"
    
    print("🔍 解析JWT Token")
    print("=" * 50)
    
    payload = decode_jwt_payload(token)
    if payload:
        print("Token信息:")
        print(f"  用户名: {payload.get('user_name')}")
        print(f"  真实姓名: {payload.get('realName')}")
        print(f"  用户ID: {payload.get('userId')}")
        print(f"  商户号: {payload.get('pin')}")
        print(f"  手机号: {payload.get('mobile')}")
        print(f"  邮箱: {payload.get('email')}")
        print(f"  过期时间: {datetime.fromtimestamp(payload.get('exp', 0))}")
        print(f"  客户端ID: {payload.get('client_id')}")
    
    # 测试API接口
    base_url = "https://dev-recycle.szhibu.com"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "AI-Test-Platform/1.0"
    }
    
    print("\n🧪 测试API接口")
    print("=" * 50)
    
    # 常见的API端点
    test_endpoints = [
        "/api/user/info",
        "/api/user/profile", 
        "/api/dashboard",
        "/api/menu",
        "/api/recycle/orders",
        "/api/warehouse/inventory",
        "/api/materials",
        "/api/system/info"
    ]
    
    for endpoint in test_endpoints:
        try:
            url = f"{base_url}{endpoint}"
            print(f"\n测试: {endpoint}")
            
            response = requests.get(
                url,
                headers=headers,
                timeout=10,
                verify=False
            )
            
            print(f"  状态码: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"  ✅ 成功获取数据")
                    print(f"  响应长度: {len(str(data))} 字符")
                    if isinstance(data, dict):
                        keys = list(data.keys())[:5]  # 只显示前5个key
                        print(f"  主要字段: {keys}")
                except:
                    print(f"  ✅ 成功访问 (非JSON响应)")
                    print(f"  响应长度: {len(response.text)} 字符")
            elif response.status_code == 401:
                print(f"  ❌ 认证失败 - Token可能已过期")
            elif response.status_code == 403:
                print(f"  ❌ 权限不足")
            elif response.status_code == 404:
                print(f"  ⚠️  接口不存在")
            else:
                print(f"  ❌ 请求失败")
                
        except Exception as e:
            print(f"  ❌ 请求异常: {e}")

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    test_api_with_token()