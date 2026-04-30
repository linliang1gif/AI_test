#!/usr/bin/env python3
"""
蓝点项目第一轮真实试点脚本
仅测试币别管理业务链（8个接口）
使用环境变量读取敏感配置
"""

import requests
import json
import time
import os
from datetime import datetime
from pathlib import Path
import urllib3

# 禁用 SSL 警告（仅用于测试环境）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def load_env():
    """加载环境变量"""
    env_file = Path(__file__).parent / ".env.bluedot"
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value


class BluedotPilotSecure:
    """蓝点项目试点类（安全版本）"""
    
    def __init__(self):
        # 从环境变量加载配置
        load_env()
        
        self.sso_url = os.getenv('BLUEDOT_SSO_URL')
        self.base_url = os.getenv('BLUEDOT_BASE_URL')
        self.client_id = os.getenv('BLUEDOT_CLIENT_ID')
        self.client_secret = os.getenv('BLUEDOT_CLIENT_SECRET')
        self.username = os.getenv('BLUEDOT_USERNAME')
        self.password = os.getenv('BLUEDOT_PASSWORD')
        self.timeout = int(os.getenv('BLUEDOT_TIMEOUT', '30'))
        self.verify_ssl = os.getenv('BLUEDOT_VERIFY_SSL', 'false').lower() == 'true'
        
        # Token
        self.access_token = None
        
        # 测试数据
        self.test_currency_uuid = None
        
        # 结果统计
        self.results = {}
        self.api_calls = []
    
    def _mask_sensitive(self, text, show_chars=4):
        """脱敏显示"""
        if not text or len(text) <= show_chars * 2:
            return "***"
        return f"{text[:show_chars]}...{text[-show_chars:]}"
    
    def check_network(self):
        """检查网络连通性"""
        print("\n" + "=" * 60)
        print("试点前检查 1: 网络连通性")
        print("=" * 60)
        
        # 检查 SSO
        print(f"→ 检查 SSO 服务: {self.sso_url}")
        try:
            response = requests.get(
                self.sso_url.replace('/oauth/token', '/actuator/health'),
                timeout=5,
                verify=self.verify_ssl
            )
            print(f"✓ SSO 服务可访问")
        except Exception as e:
            print(f"✗ SSO 服务不可访问: {type(e).__name__}")
            return False
        
        # 检查 API
        print(f"→ 检查 API 服务: {self.base_url}")
        try:
            response = requests.get(
                f"{self.base_url}/actuator/health",
                timeout=5,
                verify=self.verify_ssl
            )
            if response.status_code == 200:
                print(f"✓ API 服务可访问")
                return True
            else:
                print(f"⚠ API 服务返回: {response.status_code}")
                return True  # 可能需要鉴权，但服务可访问
        except Exception as e:
            print(f"✗ API 服务不可访问: {type(e).__name__}")
            return False
    
    def get_token(self):
        """获取 OAuth2 Token"""
        print("\n" + "=" * 60)
        print("试点前检查 2: OAuth2 鉴权")
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
        
        print(f"→ 请求 Token")
        print(f"  URL: {self.sso_url}")
        print(f"  Client ID: {self._mask_sensitive(self.client_id)}")
        print(f"  Username: {self._mask_sensitive(self.username)}")
        
        try:
            start_time = time.time()
            response = requests.post(
                self.sso_url,
                headers=headers,
                data=data,
                timeout=self.timeout,
                verify=self.verify_ssl
            )
            elapsed = time.time() - start_time
            
            self.api_calls.append({
                "step": "获取Token",
                "method": "POST",
                "url": self.sso_url,
                "status": response.status_code,
                "elapsed": f"{elapsed:.2f}s"
            })
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                expires_in = token_data.get("expires_in", 0)
                
                print(f"✓ Token 获取成功")
                print(f"  - Token: {self._mask_sensitive(self.access_token, 10)}")
                print(f"  - 有效期: {expires_in}秒 ({expires_in // 86400}天)")
                print(f"  - 响应时间: {elapsed:.2f}秒")
                return True
            else:
                print(f"✗ Token 获取失败: {response.status_code}")
                print(f"  响应: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"✗ Token 获取异常: {type(e).__name__}: {str(e)[:100]}")
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
            start_time = time.time()
            if method.upper() == "POST":
                response = requests.post(
                    url,
                    json=data or {},
                    headers=headers,
                    timeout=self.timeout,
                    verify=self.verify_ssl
                )
            else:
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=self.timeout,
                    verify=self.verify_ssl
                )
            elapsed = time.time() - start_time
            
            self.api_calls.append({
                "method": method.upper(),
                "path": path,
                "status": response.status_code,
                "elapsed": f"{elapsed:.2f}s",
                "need_auth": need_auth
            })
            
            return response
        except Exception as e:
            print(f"✗ 请求异常: {type(e).__name__}: {str(e)[:100]}")
            self.api_calls.append({
                "method": method.upper(),
                "path": path,
                "status": "ERROR",
                "error": type(e).__name__
            })
            return None
    
    def test_list_currency_no_auth(self):
        """测试查询币别列表（不带鉴权）"""
        print("\n" + "=" * 60)
        print("试点前检查 3: 币别列表接口鉴权验证")
        print("=" * 60)
        
        print("→ 测试不带 Token 的请求...")
        response = self._request("POST", "/basic/basicCurrency/list", {}, need_auth=False)
        
        if response:
            print(f"  状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200:
                    currency_list = data.get("data", [])
                    print(f"✓ 列表接口无需鉴权")
                    print(f"  - 返回 {len(currency_list)} 条币别")
                    return "no_auth"
                else:
                    print(f"⚠ 接口返回错误: {data.get('message')}")
                    return "error"
            elif response.status_code == 401:
                print(f"✓ 列表接口需要鉴权")
                return "need_auth"
            else:
                print(f"⚠ 未知状态码: {response.status_code}")
                return "unknown"
        else:
            print(f"✗ 请求失败")
            return "failed"
    
    def run_currency_chain(self):
        """执行币别管理业务链"""
        print("\n" + "=" * 80)
        print(" " * 20 + "币别管理业务链试点")
        print("=" * 80)
        
        # 1. 查询列表
        print("\n→ 步骤 1: 查询币别列表")
        response = self._request("POST", "/basic/basicCurrency/list", {}, need_auth=True)
        if response and response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                currency_list = data.get("data", [])
                print(f"✓ 查询成功，共 {len(currency_list)} 条币别")
                self.results["查询列表"] = True
            else:
                print(f"✗ 查询失败: {data.get('message')}")
                self.results["查询列表"] = False
        else:
            print(f"✗ 查询失败")
            self.results["查询列表"] = False
        
        # 2. 新增币别
        print("\n→ 步骤 2: 新增币别")
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
        
        response = self._request("POST", "/basic/basicCurrency/add", test_data, need_auth=True)
        if response and response.status_code == 200:
            data = response.json()
            if data.get("code") == 200 and data.get("data") == True:
                print(f"✓ 新增成功: {test_data['currencyName']}")
                self.results["新增币别"] = True
                
                # 获取 UUID
                time.sleep(1)
                list_response = self._request("POST", "/basic/basicCurrency/list", {}, need_auth=True)
                if list_response and list_response.status_code == 200:
                    list_data = list_response.json()
                    currency_list = list_data.get("data", [])
                    for currency in currency_list:
                        if currency.get("currencyName") == test_data["currencyName"]:
                            self.test_currency_uuid = currency.get("uuid")
                            print(f"  UUID: {self.test_currency_uuid}")
                            break
            else:
                print(f"✗ 新增失败: {data.get('message')}")
                self.results["新增币别"] = False
        else:
            print(f"✗ 新增失败")
            self.results["新增币别"] = False
        
        if not self.test_currency_uuid:
            print("\n⚠ 未获取到测试币别 UUID，后续步骤跳过")
            return
        
        # 3. 查询详情
        print("\n→ 步骤 3: 查询币别详情")
        response = self._request("POST", "/basic/basicCurrency/info", {"uuid": self.test_currency_uuid}, need_auth=True)
        if response and response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                info = data.get("data", {})
                print(f"✓ 查询成功: {info.get('currencyName')}")
                self.results["查询详情"] = True
            else:
                print(f"✗ 查询失败: {data.get('message')}")
                self.results["查询详情"] = False
        else:
            print(f"✗ 查询失败")
            self.results["查询详情"] = False
        
        # 4. 编辑币别
        print("\n→ 步骤 4: 编辑币别")
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
        
        response = self._request("POST", "/basic/basicCurrency/update", update_data, need_auth=True)
        if response and response.status_code == 200:
            data = response.json()
            if data.get("code") == 200 and data.get("data") == True:
                print(f"✓ 编辑成功")
                self.results["编辑币别"] = True
            else:
                print(f"✗ 编辑失败: {data.get('message')}")
                self.results["编辑币别"] = False
        else:
            print(f"✗ 编辑失败")
            self.results["编辑币别"] = False
        
        # 5. 启用/禁用
        print("\n→ 步骤 5: 启用/禁用币别")
        response = self._request("POST", "/basic/basicCurrency/enabled", {"uuid": self.test_currency_uuid}, need_auth=True)
        if response and response.status_code == 200:
            data = response.json()
            if data.get("code") == 200 and data.get("data") == True:
                print(f"✓ 状态切换成功")
                self.results["启用禁用"] = True
            else:
                print(f"✗ 状态切换失败: {data.get('message')}")
                self.results["启用禁用"] = False
        else:
            print(f"✗ 状态切换失败")
            self.results["启用禁用"] = False
        
        # 6. 删除币别
        print("\n→ 步骤 6: 删除币别")
        response = self._request("POST", "/basic/basicCurrency/delete", {"uuid": self.test_currency_uuid}, need_auth=True)
        if response and response.status_code == 200:
            data = response.json()
            if data.get("code") == 200 and data.get("data") == True:
                print(f"✓ 删除成功")
                self.results["删除币别"] = True
            else:
                print(f"✗ 删除失败: {data.get('message')}")
                self.results["删除币别"] = False
        else:
            print(f"✗ 删除失败")
            self.results["删除币别"] = False
    
    def print_summary(self):
        """打印试点总结"""
        print("\n" + "=" * 80)
        print(" " * 25 + "试点总结")
        print("=" * 80)
        
        # 统计
        total = len(self.results)
        passed = sum(1 for v in self.results.values() if v)
        failed = total - passed
        
        print(f"\n总计: {total} 项")
        print(f"通过: {passed} 项 ✓")
        print(f"失败: {failed} 项 ✗")
        if total > 0:
            print(f"成功率: {passed / total * 100:.1f}%")
        
        print("\n详细结果:")
        for step, result in self.results.items():
            status = "✓ 通过" if result else "✗ 失败"
            print(f"  {step}: {status}")
        
        # API 调用统计
        print(f"\nAPI 调用统计:")
        print(f"  总调用次数: {len(self.api_calls)}")
        success_calls = sum(1 for call in self.api_calls if isinstance(call.get('status'), int) and call['status'] == 200)
        print(f"  成功调用: {success_calls}")
        print(f"  失败调用: {len(self.api_calls) - success_calls}")
        
        # 判断是否通过
        passed_pilot = passed == total and total > 0
        
        print("\n" + "=" * 80)
        if passed_pilot:
            print(" " * 25 + "✓ 试点通过")
        else:
            print(" " * 25 + "✗ 试点未通过")
        print("=" * 80)
        
        return passed_pilot
    
    def save_report(self):
        """保存试点报告"""
        report = {
            "pilot_name": "蓝点项目第一轮试点 - 币别管理",
            "timestamp": datetime.now().isoformat(),
            "results": self.results,
            "api_calls": self.api_calls,
            "summary": {
                "total": len(self.results),
                "passed": sum(1 for v in self.results.values() if v),
                "failed": sum(1 for v in self.results.values() if not v)
            }
        }
        
        report_file = Path(__file__).parent / "bluedot_pilot_result.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n试点报告已保存: {report_file}")
    
    def run(self):
        """运行完整试点"""
        print("\n" + "=" * 80)
        print(" " * 15 + "蓝点项目第一轮真实试点")
        print(" " * 20 + "币别管理业务链")
        print("=" * 80)
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 试点前检查
        if not self.check_network():
            print("\n✗ 网络连通性检查失败，终止试点")
            print("\n建议：")
            print("  1. 检查是否连接 VPN")
            print("  2. 检查内网访问权限")
            print("  3. 检查防火墙设置")
            return False
        
        if not self.get_token():
            print("\n✗ OAuth2 鉴权失败，终止试点")
            return False
        
        # 检查列表接口鉴权
        auth_status = self.test_list_currency_no_auth()
        print(f"\n列表接口鉴权状态: {auth_status}")
        
        # 执行业务链
        self.run_currency_chain()
        
        # 打印总结
        passed = self.print_summary()
        
        # 保存报告
        self.save_report()
        
        print(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return passed


if __name__ == "__main__":
    pilot = BluedotPilotSecure()
    success = pilot.run()
    exit(0 if success else 1)
