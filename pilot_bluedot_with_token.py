#!/usr/bin/env python3
"""
蓝点项目第一轮真实试点脚本 - 使用固定Token
使用方法：
1. 登录 https://dev-recycle.szhibu.com/index (商户号1014, 账号ldsit, 密码654321)
2. F12开发者工具 → Network → 找到任意API请求
3. 复制请求头中的 Authorization: Bearer xxx
4. 修改下面的 YOUR_TOKEN_HERE 为实际Token
5. 执行: py pilot_bluedot_with_token.py
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path
import urllib3

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================
# 在这里填入你从浏览器获取的Token
# ============================================================
YOUR_TOKEN_HERE = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdXBwbGllcklkIjoiIiwidXNlcl9uYW1lIjoibGRzaXQiLCJtb2JpbGUiOiIxMzU0MjY1ODk2MyIsImF2YXRhciI6bnVsbCwidXNlcklkIjoiMTE2ZDMyYTY0MGIwNGE1NWJkMTViMWI5MTBmY2Y3NzgiLCJ1dWlkIjoiZDkxOWY3NmQ5YmRiNGEwZDk0ODNjNjA0N2ZhYzJlZjIiLCJjbGllbnRfaWQiOiJkZXZfYmx1ZV9yZWN5Y2xlIiwidXJsIjpudWxsLCJyZWFsTmFtZSI6Imxkc2l0IiwiYXVkIjpbIkRFRkFVTFRfUkVTT1VSQ0VfSUQiXSwicGluIjoiMTAxNCIsInNjb3BlIjpbImFsbCJdLCJ3c3QiOiJ3c0xBQWN6TEFzREJ5QXZJd1FMS3lnc0J3c29Md2d2RHdzZ0FEQUROemNmT3dzakN3YzRQQWR3RDBjNEJDdENwQ3cvYUNxbmJDZ3pUREE4S3pnSER3c01BemNBQnd3c0JDOEVDeUFIRHdjZk1ETURJd2MwQUFnekxDZ0RMIiwiaWQiOjE5OTMxMzE3MjI5MTY4OTI2NzQsImV4cCI6MTc3NzM1NTA4NSwianRpIjoiYzE3NjMyMzUtNjA3OS00NGY4LWFmNjQtN2I3MWNmMDE5MDkwIiwiZW1haWwiOiIxMzU0MjY1ODk2M0BxcS5jb20ifQ.SJ22Ceqz_oZFagfjxgPHvG_9Lb4PVcgo8HgtVqwPfu8nRBtSocITCrROt5VGx2sPK7-6f38xKh9KGx_wLzVEYG3KvzvwT4wOJtaPVAGcJlckP_8VS4b0Rm6wMPh1aTTIrzaAgh35MB6ESBXztpO7ZA8QizxhT_NVNSNIG2RIo4g"  # 替换为实际Token
# ============================================================


class BluedotPilotWithToken:
    """蓝点项目试点类（使用固定Token）"""
    
    def __init__(self, token):
        self.base_url = "https://dev-recycle.szhibu.com/dev-api/recycle"
        self.token = token
        self.timeout = 30
        self.verify_ssl = False
        
        # 测试数据
        self.test_currency_uuid = None
        
        # 结果统计
        self.results = {}
        self.api_calls = []
    
    def check_token(self):
        """检查Token是否有效"""
        print("\n" + "=" * 60)
        print("试点前检查: Token验证")
        print("=" * 60)
        
        if not self.token or self.token == "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ7XCJtZXJjaGFudE5vXCI6XCIxMDE0XCIsXCJ1c2VySWRcIjpcIjE3NzI1NTI5NTI5NTI4MzgxNDVcIixcInVzZXJuYW1lXCI6XCJsZHNpdFwifSIsImV4cCI6MTc0NTIxNzY5Mn0.xxx":
            print("✗ Token未设置或使用默认值")
            print("\n请按以下步骤获取Token:")
            print("1. 登录 https://dev-recycle.szhibu.com/index")
            print("   商户号: 1014")
            print("   账号: ldsit")
            print("   密码: 654321")
            print("2. F12开发者工具 → Network")
            print("3. 点击任意菜单触发API请求")
            print("4. 找到请求，查看Headers")
            print("5. 复制 Authorization: Bearer xxx 中的Token")
            print("6. 修改脚本中的 YOUR_TOKEN_HERE")
            return False
        
        print(f"→ Token: {self.token[:50]}...")
        
        # 测试Token是否有效
        try:
            response = self._request("POST", "/basic/basicCurrency/list", {})
            if response and response.status_code == 200:
                data = response.json()
                if data.get("code") == 200:
                    print(f"✓ Token有效")
                    return True
                else:
                    print(f"✗ Token无效或已过期: {data.get('message')}")
                    return False
            elif response and response.status_code == 401:
                print(f"✗ Token无效或已过期")
                return False
            else:
                print(f"✗ 验证失败")
                return False
        except Exception as e:
            print(f"✗ 验证异常: {type(e).__name__}")
            return False
    
    def _request(self, method, path, data=None):
        """统一请求方法"""
        url = f"{self.base_url}{path}"
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
        
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
                "elapsed": f"{elapsed:.2f}s"
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
    
    def run_currency_chain(self):
        """执行币别管理业务链"""
        print("\n" + "=" * 80)
        print(" " * 20 + "币别管理业务链试点")
        print("=" * 80)
        
        # 1. 查询列表
        print("\n→ 步骤 1: 查询币别列表")
        response = self._request("POST", "/basic/basicCurrency/list", {})
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
        
        response = self._request("POST", "/basic/basicCurrency/add", test_data)
        if response and response.status_code == 200:
            data = response.json()
            if data.get("code") == 200 and data.get("data") == True:
                print(f"✓ 新增成功: {test_data['currencyName']}")
                self.results["新增币别"] = True
                
                # 获取 UUID
                time.sleep(1)
                list_response = self._request("POST", "/basic/basicCurrency/list", {})
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
        response = self._request("POST", "/basic/basicCurrency/info", {"uuid": self.test_currency_uuid})
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
        
        response = self._request("POST", "/basic/basicCurrency/update", update_data)
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
        response = self._request("POST", "/basic/basicCurrency/enabled", {"uuid": self.test_currency_uuid})
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
        response = self._request("POST", "/basic/basicCurrency/delete", {"uuid": self.test_currency_uuid})
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
        
        print(f"\nAPI 调用统计:")
        print(f"  总调用次数: {len(self.api_calls)}")
        success_calls = sum(1 for call in self.api_calls if isinstance(call.get('status'), int) and call['status'] == 200)
        print(f"  成功调用: {success_calls}")
        print(f"  失败调用: {len(self.api_calls) - success_calls}")
        
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
            "pilot_name": "蓝点项目第一轮试点 - 币别管理（固定Token）",
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
        print(" " * 22 + "(使用固定Token)")
        print("=" * 80)
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 检查Token
        if not self.check_token():
            print("\n✗ Token验证失败，终止试点")
            return False
        
        # 执行业务链
        self.run_currency_chain()
        
        # 打印总结
        passed = self.print_summary()
        
        # 保存报告
        self.save_report()
        
        print(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return passed


if __name__ == "__main__":
    pilot = BluedotPilotWithToken(YOUR_TOKEN_HERE)
    success = pilot.run()
    exit(0 if success else 1)
