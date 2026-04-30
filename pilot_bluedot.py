#!/usr/bin/env python3
"""
蓝点项目试点脚本
测试币别管理业务链
"""

import requests
import json
import time
from datetime import datetime
import urllib3

# 禁用 SSL 警告（仅用于测试环境）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class BluedotPilot:
    """蓝点项目试点类"""
    
    def __init__(self):
        # 测试环境配置
        self.base_url = "https://dev-recycle.szhibu.com/dev-api/recycle"
        self.sso_url = "https://sit-sso.szhibu.com/oauth/token"
        
        # OAuth2 配置
        self.client_id = "sit_user_center"
        self.client_secret = "123456"
        self.username = "blueRecycle"
        self.password = "123456"
        
        # Token
        self.access_token = None
        
        # 测试数据
        self.test_currency_uuid = None
        
    def get_token(self):
        """获取 OAuth2 Token"""
        print("\n" + "=" * 60)
        print("步骤 1: 获取 OAuth2 Token")
        print("=" * 60)
        
        import base64
        auth_str = f"{self.client_id}:{self.client_secret}"
        auth_b64 = base64.b64encode(auth_str.encode()).decode()
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {auth_b64}"
        }
        
        data = {
            "grant_type": "password",
            "username": self.username,
            "password": self.password,
            "scope": "all"
        }
        
        try:
            print(f"→ 请求 Token: {self.sso_url}")
            response = requests.post(self.sso_url, headers=headers, data=data, timeout=10, verify=False)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                expires_in = token_data.get("expires_in", 0)
                
                print(f"✓ Token 获取成功")
                print(f"  - Token: {self.access_token[:20]}...")
                print(f"  - 有效期: {expires_in}秒 ({expires_in // 86400}天)")
                return True
            else:
                print(f"✗ Token 获取失败: {response.status_code}")
                print(f"  响应: {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ Token 获取异常: {e}")
            return False
    
    def _request(self, method, path, data=None, need_auth=True):
        """统一请求方法"""
        url = f"{self.base_url}{path}"
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if need_auth and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        
        try:
            if method.upper() == "POST":
                response = requests.post(url, json=data or {}, headers=headers, timeout=30, verify=False)
            else:
                response = requests.get(url, headers=headers, timeout=30, verify=False)
            
            return response
        except Exception as e:
            print(f"✗ 请求异常: {e}")
            return None
    
    def test_list_currency(self):
        """测试查询币别列表"""
        print("\n" + "=" * 60)
        print("步骤 2: 查询币别列表")
        print("=" * 60)
        
        # 先测试不带 token
        print("→ 测试不带 Token 的请求...")
        response = self._request("POST", "/basic/basicCurrency/list", {}, need_auth=False)
        
        if response and response.status_code == 200:
            print("✓ 不需要鉴权即可访问")
            data = response.json()
            if data.get("code") == 200:
                currency_list = data.get("data", [])
                print(f"✓ 查询成功，共 {len(currency_list)} 条币别")
                if currency_list:
                    print(f"  示例: {currency_list[0].get('currencyName')} ({currency_list[0].get('currencySymbol')})")
                return True
        else:
            print(f"✗ 需要鉴权，状态码: {response.status_code if response else 'None'}")
            
            # 使用 token 重试
            print("→ 使用 Token 重试...")
            response = self._request("POST", "/basic/basicCurrency/list", {}, need_auth=True)
            
            if response and response.status_code == 200:
                data = response.json()
                if data.get("code") == 200:
                    currency_list = data.get("data", [])
                    print(f"✓ 查询成功，共 {len(currency_list)} 条币别")
                    if currency_list:
                        print(f"  示例: {currency_list[0].get('currencyName')} ({currency_list[0].get('currencySymbol')})")
                    return True
            
            print(f"✗ 查询失败")
            return False
    
    def test_add_currency(self):
        """测试新增币别"""
        print("\n" + "=" * 60)
        print("步骤 3: 新增币别")
        print("=" * 60)
        
        timestamp = int(time.time())
        test_data = {
            "currencyName": f"测试币别_{timestamp}",
            "currencySymbol": f"TEST{timestamp % 10000}",
            "currencyNameEn": f"Test Currency {timestamp}",
            "baseCurrency": 0,
            "remark": "自动化测试创建",
            "unitPriceDecimalPlace": 2,
            "totalPriceDecimalPlace": 2
        }
        
        print(f"→ 新增币别: {test_data['currencyName']}")
        response = self._request("POST", "/basic/basicCurrency/add", test_data, need_auth=True)
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get("code") == 200 and data.get("data") == True:
                print(f"✓ 新增成功")
                
                # 查询刚创建的币别获取 UUID
                time.sleep(1)
                list_response = self._request("POST", "/basic/basicCurrency/list", {}, need_auth=True)
                if list_response and list_response.status_code == 200:
                    list_data = list_response.json()
                    currency_list = list_data.get("data", [])
                    for currency in currency_list:
                        if currency.get("currencyName") == test_data["currencyName"]:
                            self.test_currency_uuid = currency.get("uuid")
                            print(f"  - UUID: {self.test_currency_uuid}")
                            break
                
                return True
            else:
                print(f"✗ 新增失败: {data.get('message', '未知错误')}")
                return False
        else:
            print(f"✗ 新增失败，状态码: {response.status_code if response else 'None'}")
            if response:
                print(f"  响应: {response.text}")
            return False
    
    def test_get_currency_info(self):
        """测试查询币别详情"""
        print("\n" + "=" * 60)
        print("步骤 4: 查询币别详情")
        print("=" * 60)
        
        if not self.test_currency_uuid:
            print("✗ 跳过：未获取到测试币别 UUID")
            return False
        
        data = {"uuid": self.test_currency_uuid}
        
        print(f"→ 查询币别详情: {self.test_currency_uuid}")
        response = self._request("POST", "/basic/basicCurrency/info", data, need_auth=True)
        
        if response and response.status_code == 200:
            result = response.json()
            if result.get("code") == 200:
                currency_info = result.get("data", {})
                print(f"✓ 查询成功")
                print(f"  - 名称: {currency_info.get('currencyName')}")
                print(f"  - 符号: {currency_info.get('currencySymbol')}")
                print(f"  - 启用状态: {'启用' if currency_info.get('enabled') == 1 else '禁用'}")
                return True
            else:
                print(f"✗ 查询失败: {result.get('message')}")
                return False
        else:
            print(f"✗ 查询失败，状态码: {response.status_code if response else 'None'}")
            return False
    
    def test_update_currency(self):
        """测试编辑币别"""
        print("\n" + "=" * 60)
        print("步骤 5: 编辑币别")
        print("=" * 60)
        
        if not self.test_currency_uuid:
            print("✗ 跳过：未获取到测试币别 UUID")
            return False
        
        update_data = {
            "uuid": self.test_currency_uuid,
            "currencyName": f"测试币别_已编辑_{int(time.time())}",
            "currencySymbol": "EDITED",
            "currencyNameEn": "Edited Test Currency",
            "baseCurrency": 0,
            "remark": "自动化测试编辑",
            "unitPriceDecimalPlace": 4,
            "totalPriceDecimalPlace": 4
        }
        
        print(f"→ 编辑币别: {update_data['currencyName']}")
        response = self._request("POST", "/basic/basicCurrency/update", update_data, need_auth=True)
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get("code") == 200 and data.get("data") == True:
                print(f"✓ 编辑成功")
                return True
            else:
                print(f"✗ 编辑失败: {data.get('message')}")
                return False
        else:
            print(f"✗ 编辑失败，状态码: {response.status_code if response else 'None'}")
            return False
    
    def test_toggle_currency(self):
        """测试启用/禁用币别"""
        print("\n" + "=" * 60)
        print("步骤 6: 启用/禁用币别")
        print("=" * 60)
        
        if not self.test_currency_uuid:
            print("✗ 跳过：未获取到测试币别 UUID")
            return False
        
        data = {"uuid": self.test_currency_uuid}
        
        print(f"→ 切换币别状态")
        response = self._request("POST", "/basic/basicCurrency/enabled", data, need_auth=True)
        
        if response and response.status_code == 200:
            result = response.json()
            if result.get("code") == 200 and result.get("data") == True:
                print(f"✓ 状态切换成功")
                return True
            else:
                print(f"✗ 状态切换失败: {result.get('message')}")
                return False
        else:
            print(f"✗ 状态切换失败，状态码: {response.status_code if response else 'None'}")
            return False
    
    def test_delete_currency(self):
        """测试删除币别"""
        print("\n" + "=" * 60)
        print("步骤 7: 删除币别")
        print("=" * 60)
        
        if not self.test_currency_uuid:
            print("✗ 跳过：未获取到测试币别 UUID")
            return False
        
        data = {"uuid": self.test_currency_uuid}
        
        print(f"→ 删除币别: {self.test_currency_uuid}")
        response = self._request("POST", "/basic/basicCurrency/delete", data, need_auth=True)
        
        if response and response.status_code == 200:
            result = response.json()
            if result.get("code") == 200 and result.get("data") == True:
                print(f"✓ 删除成功")
                return True
            else:
                print(f"✗ 删除失败: {result.get('message')}")
                return False
        else:
            print(f"✗ 删除失败，状态码: {response.status_code if response else 'None'}")
            return False
    
    def run(self):
        """运行完整试点"""
        print("\n" + "=" * 80)
        print(" " * 20 + "蓝点项目试点 - 币别管理业务链")
        print("=" * 80)
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        results = {}
        
        # 执行测试步骤
        results["获取Token"] = self.get_token()
        
        if results["获取Token"]:
            results["查询列表"] = self.test_list_currency()
            results["新增币别"] = self.test_add_currency()
            results["查询详情"] = self.test_get_currency_info()
            results["编辑币别"] = self.test_update_currency()
            results["启用禁用"] = self.test_toggle_currency()
            results["删除币别"] = self.test_delete_currency()
        else:
            print("\n✗ Token 获取失败，终止试点")
        
        # 输出总结
        print("\n" + "=" * 80)
        print(" " * 30 + "试点总结")
        print("=" * 80)
        
        total = len(results)
        passed = sum(1 for v in results.values() if v)
        failed = total - passed
        
        print(f"\n总计: {total} 项")
        print(f"通过: {passed} 项 ✓")
        print(f"失败: {failed} 项 ✗")
        print(f"成功率: {passed / total * 100:.1f}%")
        
        print("\n详细结果:")
        for step, result in results.items():
            status = "✓ 通过" if result else "✗ 失败"
            print(f"  {step}: {status}")
        
        print(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        return passed == total


if __name__ == "__main__":
    pilot = BluedotPilot()
    success = pilot.run()
    exit(0 if success else 1)
