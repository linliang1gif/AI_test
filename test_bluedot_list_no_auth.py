#!/usr/bin/env python3
"""
测试蓝点币别列表接口是否需要鉴权
"""

import requests
import json
import urllib3

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_list_no_auth():
    """测试不带鉴权的列表接口"""
    
    base_url = "https://dev-recycle.szhibu.com/dev-api/recycle"
    
    print("=" * 60)
    print("测试币别列表接口（不带鉴权）")
    print("=" * 60)
    
    # 测试 list 接口
    print("\n→ 测试 /basic/basicCurrency/list")
    try:
        response = requests.post(
            f"{base_url}/basic/basicCurrency/list",
            json={},
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            timeout=10,
            verify=False
        )
        
        print(f"  状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  响应: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
            
            if data.get("code") == 200:
                currency_list = data.get("data", [])
                print(f"\n✓ 列表接口无需鉴权")
                print(f"  返回 {len(currency_list)} 条币别")
                if currency_list:
                    print(f"  示例: {currency_list[0].get('currencyName')}")
                return True
            else:
                print(f"\n⚠ 接口返回错误: {data.get('message')}")
                return False
        elif response.status_code == 401:
            print(f"\n✓ 列表接口需要鉴权")
            print(f"  响应: {response.text[:200]}")
            return False
        else:
            print(f"\n⚠ 未知状态码: {response.status_code}")
            print(f"  响应: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"\n✗ 请求失败: {type(e).__name__}: {str(e)}")
        return False

def test_page_no_auth():
    """测试不带鉴权的分页接口"""
    
    base_url = "https://dev-recycle.szhibu.com/dev-api/recycle"
    
    print("\n→ 测试 /basic/basicCurrency/page")
    try:
        response = requests.post(
            f"{base_url}/basic/basicCurrency/page",
            json={"pageNum": 1, "pageSize": 10},
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            timeout=10,
            verify=False
        )
        
        print(f"  状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                page_data = data.get("data", {})
                total = page_data.get("total", 0)
                print(f"\n✓ 分页接口无需鉴权")
                print(f"  总记录数: {total}")
                return True
            else:
                print(f"\n⚠ 接口返回错误: {data.get('message')}")
                return False
        elif response.status_code == 401:
            print(f"\n✓ 分页接口需要鉴权")
            return False
        else:
            print(f"\n⚠ 未知状态码: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n✗ 请求失败: {type(e).__name__}: {str(e)}")
        return False

def test_base_no_auth():
    """测试不带鉴权的基准币别接口"""
    
    base_url = "https://dev-recycle.szhibu.com/dev-api/recycle"
    
    print("\n→ 测试 /basic/basicCurrency/base")
    try:
        response = requests.post(
            f"{base_url}/basic/basicCurrency/base",
            json={},
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            timeout=10,
            verify=False
        )
        
        print(f"  状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                base_currency = data.get("data", {})
                print(f"\n✓ 基准币别接口无需鉴权")
                print(f"  基准币别: {base_currency.get('currencyName')}")
                return True
            else:
                print(f"\n⚠ 接口返回错误: {data.get('message')}")
                return False
        elif response.status_code == 401:
            print(f"\n✓ 基准币别接口需要鉴权")
            return False
        else:
            print(f"\n⚠ 未知状态码: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n✗ 请求失败: {type(e).__name__}: {str(e)}")
        return False

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("蓝点项目 - 查询接口鉴权验证")
    print("=" * 60)
    
    results = {
        "list": test_list_no_auth(),
        "page": test_page_no_auth(),
        "base": test_base_no_auth()
    }
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    for api, result in results.items():
        status = "✓ 无需鉴权" if result else "✗ 需要鉴权或失败"
        print(f"  {api}: {status}")
    
    no_auth_count = sum(1 for v in results.values() if v)
    print(f"\n无需鉴权的接口: {no_auth_count}/3")
    
    if no_auth_count > 0:
        print("\n✓ 可以先测试查询功能")
        print("  建议：先在平台导入 OpenAPI，配置项目和环境")
        print("  等待正确凭证后再测试完整业务链")
    else:
        print("\n✗ 所有接口都需要鉴权")
        print("  必须先解决 PILOT-001 鉴权问题")
