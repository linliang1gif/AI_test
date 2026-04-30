#!/usr/bin/env python3
"""
蓝点项目平台接入验证脚本
在执行 bluedot_platform_integration.py 后运行此脚本验证结果
"""

import requests
import json
from datetime import datetime
from pathlib import Path


class BluedotIntegrationVerifier:
    """蓝点项目平台接入验证器"""
    
    def __init__(self):
        self.backend_url = "http://localhost:8000"  # 后端实际运行在8000端口
        self.frontend_url = "http://localhost:5173"  # 前端运行在5173端口(Vite)
        self.results = {}
        self.project_id = None
        self.api_spec_id = None
        self.test_run_id = None
    
    def _request(self, method, path, data=None):
        """统一请求方法"""
        url = f"{self.backend_url}{path}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, params=data, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, timeout=10)
            else:
                response = requests.request(method, url, json=data, timeout=10)
            
            return response
        except Exception as e:
            print(f"✗ 请求失败: {type(e).__name__}: {str(e)}")
            return None
    
    def verify_backend_health(self):
        """验证后端健康状态"""
        print("\n" + "="*60)
        print("验证 1: 后端健康状态")
        print("="*60)
        
        response = self._request("GET", "/health")
        
        if response and response.status_code == 200:
            result = response.json()
            status = result.get("status")
            db_connected = result.get("database", {}).get("connected", False)
            tables_ready = result.get("database", {}).get("tables_ready", False)
            
            if status == "healthy" and db_connected and tables_ready:
                print(f"✓ 后端健康")
                print(f"  状态: {status}")
                print(f"  数据库连接: {'正常' if db_connected else '异常'}")
                print(f"  数据表: {'就绪' if tables_ready else '未就绪'}")
                self.results["后端健康"] = True
                return True
            else:
                print(f"✗ 后端状态异常")
                print(f"  状态: {status}")
                self.results["后端健康"] = False
                return False
        else:
            print(f"✗ 后端无响应")
            self.results["后端健康"] = False
            return False
    
    def verify_project_exists(self):
        """验证蓝点项目存在"""
        print("\n" + "="*60)
        print("验证 2: 蓝点项目存在")
        print("="*60)
        
        response = self._request("GET", "/api/v2/projects")
        
        if response and response.status_code == 200:
            projects = response.json()
            
            # 查找蓝点项目
            bluedot_project = None
            for project in projects:
                if "蓝点" in project.get("name", ""):
                    bluedot_project = project
                    self.project_id = project.get("id")
                    break
            
            if bluedot_project:
                print(f"✓ 蓝点项目存在")
                print(f"  项目ID: {self.project_id}")
                print(f"  项目名称: {bluedot_project.get('name')}")
                print(f"  版本: {bluedot_project.get('version', 'N/A')}")
                self.results["项目存在"] = True
                return True
            else:
                print(f"✗ 未找到蓝点项目")
                self.results["项目存在"] = False
                return False
        else:
            print(f"✗ 查询项目失败")
            self.results["项目存在"] = False
            return False
    
    def verify_api_spec_imported(self):
        """验证 OpenAPI 已导入"""
        print("\n" + "="*60)
        print("验证 3: OpenAPI 已导入")
        print("="*60)
        
        if not self.project_id:
            print(f"✗ 项目ID未知，跳过验证")
            self.results["OpenAPI导入"] = False
            return False
        
        response = self._request("GET", f"/api/v2/swagger/api-specs?project_id={self.project_id}")
        
        if response and response.status_code == 200:
            api_specs = response.json()
            
            if api_specs and len(api_specs) > 0:
                api_spec = api_specs[0]
                self.api_spec_id = api_spec.get("id")
                api_count = api_spec.get("api_count", 0)
                
                print(f"✓ OpenAPI 已导入")
                print(f"  API Spec ID: {self.api_spec_id}")
                print(f"  接口数量: {api_count}")
                print(f"  导入时间: {api_spec.get('imported_at', 'N/A')}")
                
                if api_count >= 800:
                    print(f"  ✓ 接口数量符合预期 (>= 800)")
                    self.results["OpenAPI导入"] = True
                    return True
                else:
                    print(f"  ⚠ 接口数量偏少 (< 800)")
                    self.results["OpenAPI导入"] = True
                    return True
            else:
                print(f"✗ 未找到 API 规范")
                self.results["OpenAPI导入"] = False
                return False
        else:
            print(f"✗ 查询 API 规范失败")
            self.results["OpenAPI导入"] = False
            return False
    
    def verify_test_cases_generated(self):
        """验证测试用例已生成"""
        print("\n" + "="*60)
        print("验证 4: 测试用例已生成")
        print("="*60)
        
        if not self.project_id:
            print(f"✗ 项目ID未知，跳过验证")
            self.results["用例生成"] = False
            return False
        
        response = self._request("GET", f"/api/v2/test-cases?project_id={self.project_id}&source=swagger&limit=1000")
        
        if response and response.status_code == 200:
            result = response.json()
            total = result.get("total", 0)
            test_cases = result.get("test_cases", [])
            
            # 筛选币别管理相关用例
            currency_cases = [
                tc for tc in test_cases 
                if "basicCurrency" in tc.get("title", "") or "币别" in tc.get("title", "")
            ]
            
            print(f"✓ 测试用例已生成")
            print(f"  总用例数: {total}")
            print(f"  币别管理用例: {len(currency_cases)}")
            
            if len(currency_cases) >= 5:
                print(f"  ✓ 币别管理用例数量符合预期 (>= 5)")
                self.results["用例生成"] = True
                return True
            else:
                print(f"  ⚠ 币别管理用例数量偏少 (< 5)")
                self.results["用例生成"] = True
                return True
        else:
            print(f"✗ 查询测试用例失败")
            self.results["用例生成"] = False
            return False
    
    def verify_test_run_exists(self):
        """验证测试执行记录存在"""
        print("\n" + "="*60)
        print("验证 5: 测试执行记录存在")
        print("="*60)
        
        if not self.project_id:
            print(f"✗ 项目ID未知，跳过验证")
            self.results["执行记录"] = False
            return False
        
        response = self._request("GET", f"/api/v2/test-runs?project_id={self.project_id}&limit=10")
        
        if response and response.status_code == 200:
            test_runs = response.json()
            
            if test_runs and len(test_runs) > 0:
                test_run = test_runs[0]
                self.test_run_id = test_run.get("run_id")
                
                print(f"✓ 测试执行记录存在")
                print(f"  TestRun ID: {self.test_run_id}")
                print(f"  状态: {test_run.get('status')}")
                print(f"  总用例数: {test_run.get('total_cases', 0)}")
                print(f"  通过数: {test_run.get('passed_cases', 0)}")
                print(f"  失败数: {test_run.get('failed_cases', 0)}")
                self.results["执行记录"] = True
                return True
            else:
                print(f"✗ 未找到测试执行记录")
                self.results["执行记录"] = False
                return False
        else:
            print(f"✗ 查询测试执行记录失败")
            self.results["执行记录"] = False
            return False
    
    def verify_run_cases_exist(self):
        """验证 RunCase 记录存在"""
        print("\n" + "="*60)
        print("验证 6: RunCase 记录存在")
        print("="*60)
        
        if not self.test_run_id:
            print(f"✗ TestRun ID未知，跳过验证")
            self.results["RunCase记录"] = False
            return False
        
        response = self._request("GET", f"/api/v2/test-runs/{self.test_run_id}/cases")
        
        if response and response.status_code == 200:
            run_cases = response.json()
            
            if run_cases and len(run_cases) > 0:
                print(f"✓ RunCase 记录存在")
                print(f"  RunCase 数量: {len(run_cases)}")
                
                # 检查第一个 RunCase 的详情
                first_case = run_cases[0]
                has_snapshot = first_case.get("request_snapshot") or first_case.get("response_snapshot")
                
                print(f"  示例 RunCase ID: {first_case.get('id')}")
                print(f"  状态: {first_case.get('status')}")
                print(f"  快照: {'有' if has_snapshot else '无'}")
                
                self.results["RunCase记录"] = True
                return True
            else:
                print(f"✗ 未找到 RunCase 记录")
                self.results["RunCase记录"] = False
                return False
        else:
            print(f"✗ 查询 RunCase 失败")
            self.results["RunCase记录"] = False
            return False
    
    def verify_status_history_exists(self):
        """验证状态历史存在"""
        print("\n" + "="*60)
        print("验证 7: 状态历史存在")
        print("="*60)
        
        if not self.test_run_id:
            print(f"✗ TestRun ID未知，跳过验证")
            self.results["状态历史"] = False
            return False
        
        response = self._request("GET", f"/api/v2/test-runs/{self.test_run_id}/history")
        
        if response and response.status_code == 200:
            history = response.json()
            
            if history and len(history) > 0:
                print(f"✓ 状态历史存在")
                print(f"  历史记录数: {len(history)}")
                print(f"  状态流转:")
                for record in history[:5]:  # 显示前5条
                    print(f"    {record.get('from_status')} → {record.get('to_status')} ({record.get('changed_at')})")
                
                self.results["状态历史"] = True
                return True
            else:
                print(f"✗ 未找到状态历史")
                self.results["状态历史"] = False
                return False
        else:
            print(f"✗ 查询状态历史失败")
            self.results["状态历史"] = False
            return False
    
    def print_summary(self):
        """打印验证总结"""
        print("\n" + "="*80)
        print(" " * 25 + "验证总结")
        print("="*80)
        
        total = len(self.results)
        passed = sum(1 for v in self.results.values() if v)
        failed = total - passed
        
        print(f"\n总验证项: {total}")
        print(f"通过: {passed} ✓")
        print(f"失败: {failed} ✗")
        if total > 0:
            print(f"通过率: {passed / total * 100:.1f}%")
        
        print("\n详细结果:")
        for item, result in self.results.items():
            status = "✓ 通过" if result else "✗ 失败"
            print(f"  {item}: {status}")
        
        print("\n平台访问:")
        print(f"  前端地址: {self.frontend_url}")
        print(f"  后端地址: {self.backend_url}")
        if self.project_id:
            print(f"  项目ID: {self.project_id}")
        if self.test_run_id:
            print(f"  TestRun ID: {self.test_run_id}")
        
        success = passed == total and total > 0
        
        print("\n" + "="*80)
        if success:
            print(" " * 25 + "✓ 验证通过")
            print("\n蓝点项目已成功接入平台！")
            print("\n下一步:")
            print("  1. 访问前端查看蓝点项目详情")
            print("  2. 查看测试用例列表")
            print("  3. 查看执行结果和详情")
            print("  4. 验证 RunCase 快照和断言结果")
        else:
            print(" " * 25 + "✗ 验证未通过")
            print("\n失败项:")
            for item, result in self.results.items():
                if not result:
                    print(f"  - {item}")
            print("\n请检查:")
            print("  1. 平台是否正常运行")
            print("  2. bluedot_platform_integration.py 是否执行成功")
            print("  3. 后端日志中的错误信息")
        print("="*80)
        
        return success
    
    def save_report(self):
        """保存验证报告"""
        report = {
            "verification_time": datetime.now().isoformat(),
            "results": self.results,
            "project_id": self.project_id,
            "api_spec_id": self.api_spec_id,
            "test_run_id": self.test_run_id,
            "summary": {
                "total": len(self.results),
                "passed": sum(1 for v in self.results.values() if v),
                "failed": sum(1 for v in self.results.values() if not v)
            }
        }
        
        report_file = Path(__file__).parent.parent / "蓝点" / "bluedot_integration_verification.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n验证报告已保存: {report_file}")
    
    def run(self):
        """运行完整验证"""
        print("\n" + "="*80)
        print(" " * 20 + "蓝点项目平台接入验证")
        print("="*80)
        print(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 执行验证
        self.verify_backend_health()
        self.verify_project_exists()
        self.verify_api_spec_imported()
        self.verify_test_cases_generated()
        self.verify_test_run_exists()
        self.verify_run_cases_exist()
        self.verify_status_history_exists()
        
        # 打印总结
        success = self.print_summary()
        
        # 保存报告
        self.save_report()
        
        return success


if __name__ == "__main__":
    verifier = BluedotIntegrationVerifier()
    success = verifier.run()
    exit(0 if success else 1)
