#!/usr/bin/env python3
"""
蓝点项目平台接入脚本
完成从导入OpenAPI到平台内执行的完整流程
"""

import requests
import json
import time
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
env_file = Path(__file__).parent / ".env.bluedot"
if env_file.exists():
    load_dotenv(env_file)
    print(f"✓ 已加载环境变量: {env_file}")
else:
    print(f"⚠ 环境变量文件不存在: {env_file}")

# 平台配置
BACKEND_URL = "http://localhost:8000"  # 后端实际运行在8000端口
OPENAPI_FILE = Path(__file__).parent / "蓝点" / "bluedot_openapi.json"

# 蓝点项目配置
BLUEDOT_TOKEN = os.getenv("BLUEDOT_TOKEN", "")
BLUEDOT_BASE_URL = "https://dev-recycle.szhibu.com/dev-api/recycle"


class BluedotPlatformIntegration:
    """蓝点项目平台接入"""
    
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.project_id = None
        self.env_id = None
        self.auth_profile_id = None
        self.swagger_id = None
        self.test_case_ids = []
        self.test_run_id = None
        
        self.results = {}
    
    def _request(self, method, path, data=None, files=None):
        """统一请求方法"""
        url = f"{self.backend_url}{path}"
        
        try:
            if method.upper() == "POST":
                if files:
                    response = requests.post(url, files=files, data=data, timeout=30)
                else:
                    response = requests.post(url, json=data, timeout=30)
            elif method.upper() == "GET":
                response = requests.get(url, params=data, timeout=30)
            else:
                response = requests.request(method, url, json=data, timeout=30)
            
            return response
        except Exception as e:
            print(f"✗ 请求失败: {type(e).__name__}: {str(e)}")
            return None
    
    def step1_create_project(self):
        """步骤1: 创建蓝点项目"""
        print("\n" + "="*60)
        print("步骤 1: 创建蓝点项目")
        print("="*60)
        
        project_name = "蓝点回收系统"
        
        # 先检查项目是否已存在
        print(f"  检查项目 '{project_name}' 是否存在...")
        list_response = self._request("GET", "/api/v2/projects")
        
        if list_response and list_response.status_code in [200, 201]:
            result = list_response.json()
            projects = result.get("projects", [])  # API返回的是 {"projects": [...]}
            for project in projects:
                if project.get("name") == project_name:
                    self.project_id = project.get("id")
                    print(f"✓ 项目已存在，使用现有项目")
                    print(f"  项目ID: {self.project_id}")
                    print(f"  项目名称: {project.get('name')}")
                    self.results["创建项目"] = True
                    return True
        
        # 项目不存在，创建新项目
        print(f"  项目不存在，创建新项目...")
        data = {
            "name": project_name,
            "description": "蓝点新生废品回收B2B平台 v1.2.2",
            "version": "1.2.2"
        }
        
        response = self._request("POST", "/api/v2/projects", data)
        
        if response and response.status_code in [200, 201]:  # 201 Created 也是成功
            result = response.json()
            self.project_id = result.get("id")
            print(f"✓ 项目创建成功")
            print(f"  项目ID: {self.project_id}")
            print(f"  项目名称: {result.get('name')}")
            self.results["创建项目"] = True
            return True
        else:
            print(f"✗ 项目创建失败")
            if response:
                print(f"  状态码: {response.status_code}")
                print(f"  响应: {response.text[:200]}")
            self.results["创建项目"] = False
            return False
    
    def step2_create_environment(self):
        """步骤2: 创建测试环境"""
        print("\n" + "="*60)
        print("步骤 2: 创建测试环境")
        print("="*60)
        
        env_name = "test"  # 必须是枚举值: dev, test, staging, prod
        
        # 先检查环境是否已存在
        print(f"  检查项目 {self.project_id} 的环境是否存在...")
        list_response = self._request("GET", f"/api/v2/projects/{self.project_id}/environments")
        
        if list_response and list_response.status_code in [200, 201]:
            environments = list_response.json()  # API直接返回列表
            for env in environments:
                if env.get("name") == env_name and env.get("project_id") == self.project_id:
                    self.env_id = env.get("id")
                    print(f"✓ 环境已存在，使用现有环境")
                    print(f"  环境ID: {self.env_id}")
                    print(f"  环境名称: {env.get('name')}")
                    print(f"  Base URL: {env.get('base_url')}")
                    self.results["创建环境"] = True
                    return True
        
        # 环境不存在，创建新环境
        print(f"  环境不存在，创建新环境...")
        data = {
            "project_id": self.project_id,
            "name": env_name,
            "base_url": BLUEDOT_BASE_URL,
            "description": "蓝点项目测试环境"
        }
        
        response = self._request("POST", "/api/v2/environments", data)
        
        if response and response.status_code in [200, 201]:  # 201 Created 也是成功
            result = response.json()
            self.env_id = result.get("id")
            print(f"✓ 环境创建成功")
            print(f"  环境ID: {self.env_id}")
            print(f"  环境名称: {result.get('name')}")
            print(f"  Base URL: {result.get('base_url')}")
            self.results["创建环境"] = True
            return True
        else:
            print(f"✗ 环境创建失败")
            if response:
                print(f"  状态码: {response.status_code}")
                print(f"  响应: {response.text[:500]}")
            self.results["创建环境"] = False
            return False
    
    def step3_create_auth_profile(self):
        """步骤3: 创建鉴权配置"""
        print("\n" + "="*60)
        print("步骤 3: 创建Bearer Token鉴权")
        print("="*60)
        
        auth_name = "蓝点Bearer Token"
        
        # 先检查鉴权配置是否已存在
        print(f"  检查环境 {self.env_id} 的鉴权配置是否存在...")
        list_response = self._request("GET", f"/api/v2/environments/{self.env_id}/auth-profile")
        
        if list_response and list_response.status_code in [200, 201]:
            auth_profile = list_response.json()
            self.auth_profile_id = auth_profile.get("id")
            print(f"✓ 鉴权配置已存在，使用现有配置")
            print(f"  鉴权ID: {self.auth_profile_id}")
            print(f"  鉴权类型: {auth_profile.get('auth_type')}")
            self.results["创建鉴权"] = True
            return True
        
        # 鉴权配置不存在，创建新配置
        print(f"  鉴权配置不存在，创建新配置...")
        data = {
            "project_id": self.project_id,
            "environment_id": self.env_id,  # 必需字段
            "name": auth_name,
            "auth_type": "bearer",
            "config": {
                "token": BLUEDOT_TOKEN
            }
        }
        
        response = self._request("POST", "/api/v2/auth-profiles", data)
        
        if response and response.status_code in [200, 201]:  # 201 Created 也是成功
            result = response.json()
            self.auth_profile_id = result.get("id")
            print(f"✓ 鉴权配置创建成功")
            print(f"  鉴权ID: {self.auth_profile_id}")
            print(f"  鉴权类型: Bearer Token")
            self.results["创建鉴权"] = True
            return True
        else:
            print(f"✗ 鉴权配置创建失败")
            if response:
                print(f"  状态码: {response.status_code}")
                print(f"  响应: {response.text[:500]}")
            self.results["创建鉴权"] = False
            return False
    
    def step4_import_openapi(self):
        """步骤4: 导入OpenAPI文件"""
        print("\n" + "="*60)
        print("步骤 4: 导入OpenAPI文件")
        print("="*60)
        
        if not OPENAPI_FILE.exists():
            print(f"✗ OpenAPI文件不存在: {OPENAPI_FILE}")
            self.results["导入OpenAPI"] = False
            return False
        
        print(f"  文件路径: {OPENAPI_FILE}")
        
        # 使用正确的API端点: /api/v2/swagger/import-file
        url = f"{self.backend_url}/api/v2/swagger/import-file?project_id={self.project_id}&generate_cases=false"
        
        try:
            with open(OPENAPI_FILE, 'rb') as f:
                files = {'file': ('bluedot_openapi.json', f, 'application/json')}
                response = requests.post(url, files=files, timeout=60)
            
            if response and response.status_code in [200, 201]:  # 201 Created 也是成功
                result = response.json()
                self.swagger_id = result.get("api_spec_id")
                api_count = result.get("api_count", 0)
                print(f"✓ OpenAPI导入成功")
                print(f"  API Spec ID: {self.swagger_id}")
                print(f"  接口数量: {api_count}")
                self.results["导入OpenAPI"] = True
                return True
            else:
                print(f"✗ OpenAPI导入失败")
                if response:
                    print(f"  状态码: {response.status_code}")
                    print(f"  响应: {response.text[:200]}")
                self.results["导入OpenAPI"] = False
                return False
        except Exception as e:
            print(f"✗ OpenAPI导入异常: {type(e).__name__}: {str(e)}")
            self.results["导入OpenAPI"] = False
            return False
    
    def step5_generate_test_cases(self):
        """步骤5: 生成币别管理测试用例"""
        print("\n" + "="*60)
        print("步骤 5: 生成币别管理测试用例")
        print("="*60)
        
        # 使用正确的API端点: /api/v2/swagger/generate-test-cases
        data = {
            "api_spec_id": self.swagger_id
        }
        
        response = self._request("POST", "/api/v2/swagger/generate-test-cases", data)
        
        if response and response.status_code in [200, 201]:  # 201 Created 也是成功
            result = response.json()
            self.test_case_ids = result.get("test_case_ids", [])
            print(f"✓ 测试用例生成成功")
            print(f"  生成数量: {len(self.test_case_ids)}")
            
            # 查询币别管理相关的测试用例
            print(f"  正在查询测试用例...")
            query_response = self._request("GET", f"/api/v2/test-cases?project_id={self.project_id}&source=swagger&limit=1000")
            if query_response and query_response.status_code in [200, 201]:
                query_result = query_response.json()
                all_cases = query_result.get("test_cases", [])
                
                # 筛选币别管理相关用例，如果没有就取前8个
                currency_cases = [
                    tc for tc in all_cases 
                    if "basicCurrency" in tc.get("title", "") or "币别" in tc.get("title", "") or "currency" in tc.get("title", "").lower()
                ]
                
                if currency_cases:
                    self.test_case_ids = [tc["id"] for tc in currency_cases[:8]]
                    print(f"  币别管理用例数: {len(self.test_case_ids)}")
                else:
                    # 没有币别管理用例，取前8个
                    self.test_case_ids = [tc["id"] for tc in all_cases[:8]]
                    print(f"  未找到币别管理用例，使用前8个测试用例")
            
            self.results["生成用例"] = True
            return True
        else:
            print(f"✗ 测试用例生成失败")
            if response:
                print(f"  状态码: {response.status_code}")
                print(f"  响应: {response.text[:200]}")
            self.results["生成用例"] = False
            return False
    
    def step6_execute_test_cases(self):
        """步骤6: 在平台内执行测试用例"""
        print("\n" + "="*60)
        print("步骤 6: 执行测试用例")
        print("="*60)
        
        if not self.test_case_ids:
            print("✗ 没有可执行的测试用例")
            self.results["执行用例"] = False
            return False
        
        # 获取测试用例详情
        print(f"  正在获取测试用例详情...")
        test_cases_data = []
        for tc_id in self.test_case_ids[:8]:  # 只执行前8个币别管理用例
            tc_response = self._request("GET", f"/api/v2/test-cases/{tc_id}")
            if tc_response and tc_response.status_code in [200, 201]:  # 201 Created 也是成功
                test_cases_data.append(tc_response.json())
        
        if not test_cases_data:
            print("✗ 无法获取测试用例详情")
            self.results["执行用例"] = False
            return False
        
        print(f"  已获取 {len(test_cases_data)} 个测试用例")
        
        # 构造执行请求
        data = {
            "project_id": self.project_id,
            "environment_id": self.env_id,
            "test_cases": test_cases_data,
            "trigger_type": "manual",
            "created_by": "bluedot_integration",
            "max_workers": 1,
            "parallel": False
        }
        
        response = self._request("POST", "/api/v2/execution/trigger", data)
        
        if response and response.status_code in [200, 201]:
            result = response.json()
            self.test_run_id = result.get("run_id")
            print(f"✓ 测试执行已触发")
            print(f"  TestRun ID: {self.test_run_id}")
            print(f"  执行用例数: {len(test_cases_data)}")
            self.results["执行用例"] = True
            return True
        else:
            print(f"✗ 测试执行失败")
            if response:
                print(f"  状态码: {response.status_code}")
                print(f"  响应: {response.text[:500]}")
            self.results["执行用例"] = False
            return False
    
    def step7_wait_and_check_results(self):
        """步骤7: 等待执行完成并查看结果"""
        print("\n" + "="*60)
        print("步骤 7: 查看执行结果")
        print("="*60)
        
        if not self.test_run_id:
            print("✗ 没有TestRun ID")
            self.results["查看结果"] = False
            return False
        
        # 等待执行完成
        print("  等待执行完成...")
        max_wait = 60  # 最多等待60秒
        for i in range(max_wait):
            time.sleep(1)
            
            response = self._request("GET", f"/api/v2/test-runs/{self.test_run_id}")
            
            if response and response.status_code in [200, 201]:  # 201 Created 也是成功
                result = response.json()
                status = result.get("status")
                
                if status in ["completed", "failed"]:
                    print(f"\n✓ 执行完成")
                    print(f"  状态: {status}")
                    print(f"  总用例数: {result.get('total_cases', 0)}")
                    print(f"  通过数: {result.get('passed_cases', 0)}")
                    print(f"  失败数: {result.get('failed_cases', 0)}")
                    self.results["查看结果"] = True
                    return True
            
            if (i + 1) % 10 == 0:
                print(f"  已等待 {i + 1} 秒...")
        
        print(f"✗ 等待超时")
        self.results["查看结果"] = False
        return False
    
    def print_summary(self):
        """打印接入总结"""
        print("\n" + "="*80)
        print(" " * 25 + "接入总结")
        print("="*80)
        
        total = len(self.results)
        passed = sum(1 for v in self.results.values() if v)
        failed = total - passed
        
        print(f"\n总步骤: {total}")
        print(f"成功: {passed} ✓")
        print(f"失败: {failed} ✗")
        if total > 0:
            print(f"成功率: {passed / total * 100:.1f}%")
        
        print("\n详细结果:")
        for step, result in self.results.items():
            status = "✓ 成功" if result else "✗ 失败"
            print(f"  {step}: {status}")
        
        print("\n平台访问:")
        print(f"  前端地址: http://localhost:5173")
        print(f"  后端地址: http://localhost:8000")
        print(f"  项目ID: {self.project_id}")
        print(f"  环境ID: {self.env_id}")
        print(f"  API Spec ID: {self.swagger_id}")
        print(f"  TestRun ID: {self.test_run_id}")
        
        print("\n生成的资源:")
        print(f"  测试用例数: {len(self.test_case_ids)}")
        print(f"  币别管理用例: {min(len(self.test_case_ids), 8)}")
        
        success = passed == total and total > 0
        
        print("\n" + "="*80)
        if success:
            print(" " * 25 + "✓ 接入成功")
            print("\n下一步:")
            print("  1. 访问前端查看蓝点项目")
            print("  2. 查看生成的测试用例")
            print("  3. 查看执行结果和详情")
            print("  4. 验证 RunCase/RunStep/快照/状态历史")
        else:
            print(" " * 25 + "✗ 接入未完成")
            print("\n失败步骤:")
            for step, result in self.results.items():
                if not result:
                    print(f"  - {step}")
        print("="*80)
        
        return success
    
    def run(self):
        """执行完整接入流程"""
        print("\n" + "="*80)
        print(" " * 20 + "蓝点项目平台接入")
        print("="*80)
        
        # 检查Token
        if not BLUEDOT_TOKEN or BLUEDOT_TOKEN == "YOUR_TOKEN_HERE":
            print("\n✗ 请先设置BLUEDOT_TOKEN")
            print("  方式1: 在 .env.bluedot 文件中设置 BLUEDOT_TOKEN=xxx")
            print("  方式2: 设置环境变量 export BLUEDOT_TOKEN=xxx")
            print("\n获取Token步骤:")
            print("  1. 登录 https://dev-recycle.szhibu.com/index")
            print("  2. F12 → Network → 复制 Bearer Token")
            print("  3. 添加到 .env.bluedot 文件")
            return False
        
        # 执行接入步骤
        if not self.step1_create_project():
            return False
        
        if not self.step2_create_environment():
            return False
        
        if not self.step3_create_auth_profile():
            return False
        
        if not self.step4_import_openapi():
            return False
        
        if not self.step5_generate_test_cases():
            return False
        
        if not self.step6_execute_test_cases():
            return False
        
        if not self.step7_wait_and_check_results():
            return False
        
        # 打印总结
        success = self.print_summary()
        
        return success


if __name__ == "__main__":
    integration = BluedotPlatformIntegration()
    success = integration.run()
    exit(0 if success else 1)
