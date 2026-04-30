#!/usr/bin/env python3
"""
查找正确的SSO地址
"""

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_url(url):
    """测试URL是否可访问"""
    print(f"\n→ 测试: {url}")
    try:
        response = requests.get(url, timeout=5, verify=False)
        print(f"  ✓ 可访问 (状态码: {response.status_code})")
        return True
    except Exception as e:
        print(f"  ✗ 不可访问 ({type(e).__name__})")
        return False

if __name__ == "__main__":
    print("="*60)
    print("查找正确的SSO地址")
    print("="*60)
    
    # 可能的SSO地址
    sso_urls = [
        "https://sit-sso.szhibu.com/oauth/token",
        "https://dev-sso.szhibu.com/oauth/token",
        "https://test-sso.szhibu.com/oauth/token",
        "https://sso.szhibu.com/oauth/token",
        "https://dev-recycle.szhibu.com/dev-api/oauth/token",
        "https://dev-recycle.szhibu.com/oauth/token",
    ]
    
    results = {}
    
    for url in sso_urls:
        results[url] = test_url(url)
    
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    accessible = [url for url, ok in results.items() if ok]
    
    if accessible:
        print(f"\n✓ 找到 {len(accessible)} 个可访问的地址:")
        for url in accessible:
            print(f"  - {url}")
        print(f"\n建议使用: {accessible[0]}")
    else:
        print("\n✗ 所有地址都不可访问")
        print("\n可能原因:")
        print("  1. VPN 未连接或已断开")
        print("  2. SSO 服务在不同的域名")
        print("  3. 需要联系管理员确认正确的SSO地址")
