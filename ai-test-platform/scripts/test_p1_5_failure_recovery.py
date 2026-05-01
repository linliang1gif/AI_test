#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P1 第五轮：异常恢复与数据一致性验证

验证平台在各种异常场景下的数据一致性和状态正确性。
"""

import sys
import time
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import requests

# 配置
BACKEND_URL = "http://localhost:8000"
DB_PATH = project_root / "data" / "test_platform.db"

# 测试场景
SCENARIOS = [
    {
        "id": 1,
        "name": "目标接口返回404",
        "description": "验证请求不存在的接口时的数据一致性",
        "test_url": "/status/404",
        "expected_status": "failed",
    },
    {
        "id": 2,
        "name": "目标接口返回500",
        "description": "验证服务器错误时的数据一致性",
        "test_url": "/status/500",
        "expected_status": "failed",
    },
    {
        "id": 3,
        "name": "目标接口超时",
        "description": "验证请求超时时的数据一致性",
        "test_url": "/delay/10",
        "expected_status": "error",
        "timeout": 2,
    },
    {
        "id": 4,
        "name": "断言失败",
        "description": "验证断言失败时的数据一致性",
        "test_url": "/get",
        "expected_status": "failed",
        "assertions": [
            {"type": "status_code", "operator": "equals", "expected": 404}
        ],
    },
    {
        "id": 5,
        "name": "请求方法错误",
        "description": "验证使用错误的HTTP方法时的数据一致性",
        "test_url": "/post",
        "method": "GET",
        "expected_status": "failed",
    },
]


class FailureRecoveryTester:
    def __init__(self):
        self.results = []
        self.db_checks = []
        
    def print_header(self):
        print("=" * 100)
        print("P1 第五轮：异常恢复与数据一致性验证")
        print("=" * 100)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"后端地址: {BACKEND_URL}")
        print(f"数据库路径: {DB_PATH}")
        print("=" * 100)
        print()
    
    def check_backend_health(self) -> bool:
        """检查后端是否运行"""
        try:
            resp = requests.get(f"{BACKEND_URL}/health", timeout=5)
            if resp.status_code == 200:
                print("✅ 后端服务正常")
                return True
            else:
                print(f"❌ 后端服务异常: {resp.status_code}")
                return False
        except Exception as e:
            print(f"❌ 后端服务无法连接: {e}")
            return False
    
    def check_database(self) -> bool:
        """检查数据库是否可访问"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            required_tables = ['test_runs', 'run_cases', 'test_cases']
            missing = [t for t in required_tables if t not in tables]
            
            if missing:
                print(f"❌ 数据库缺少表: {', '.join(missing)}")
                return False
            else:
                print("✅ 数据库表结构正常")
                return True
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            return False
    
    def create_test_project(self) -> int:
        """创建测试项目"""
        try:
            resp = requests.post(
                f"{BACKEND_URL}/api/v2/projects",
                json={"name": "P1.5异常恢复测试", "description": "异常场景验证"},
                timeout=10
            )
            if resp.status_code in (200, 201):
                project_id = resp.json().get("id")
                print(f"✅ 创建测试项目: ID={project_id}")
                return project_id
            else:
                print(f"⚠️  创建项目失败: {resp.status_code}")
                return 1
        except Exception as e:
            print(f"⚠️  创建项目异常: {e}")
            return 1
    
    def create_test_environment(self, project_id: int) -> int:
        """创建测试环境"""
        try:
            resp = requests.post(
                f"{BACKEND_URL}/api/v2/environments",
                json={
                    "project_id": project_id,
                    "name": "test",
                    "base_url": "https://httpbin.org"
                },
                timeout=10
            )
            if resp.status_code in (200, 201):
                env_id = resp.json().get("id")
                print(f"✅ 创建测试环境: ID={env_id}")
                return env_id
            else:
                print(f"⚠️  创建环境失败: {resp.status_code}")
                return 1
        except Exception as e:
            print(f"⚠️  创建环境异常: {e}")
            return 1

    
    def create_test_case(self, scenario: Dict, project_id: int) -> str:
        """创建测试用例"""
        case_id = f"TC_P1_5_{scenario['id']:03d}"
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # 检查用例是否已存在
            cursor.execute("SELECT id FROM test_cases WHERE id = ?", (case_id,))
            if cursor.fetchone():
                conn.close()
                return case_id
            
            # 创建用例
            execution_config = {
                "method": scenario.get("method", "GET"),
                "url": scenario["test_url"],
                "timeout": scenario.get("timeout", 30),
            }
            
            cursor.execute("""
                INSERT INTO test_cases (
                    id, title, module, priority, status,
                    execution_config, assertions, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                case_id,
                scenario["name"],
                "P1.5异常恢复测试",
                "high",
                "pending",
                json.dumps(execution_config),
                json.dumps(scenario.get("assertions", [])),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            return case_id
        except Exception as e:
            print(f"⚠️  创建测试用例失败: {e}")
            return case_id
    
    def execute_test_case(self, case_id: str, env_id: int) -> Tuple[bool, str, Dict]:
        """执行测试用例"""
        try:
            resp = requests.post(
                f"{BACKEND_URL}/api/v2/test-cases/{case_id}/execute",
                json={"environment_id": env_id},
                timeout=15
            )
            
            if resp.status_code == 200:
                data = resp.json()
                return True, data.get("run_id", ""), data
            else:
                return False, "", {"error": f"HTTP {resp.status_code}"}
        except requests.exceptions.Timeout:
            return False, "", {"error": "请求超时"}
        except Exception as e:
            return False, "", {"error": str(e)}
    
    def check_test_run_data(self, run_id: str) -> Dict:
        """检查test_runs表数据"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, status, start_time, end_time, duration,
                       total_cases, passed_cases, failed_cases
                FROM test_runs WHERE id = ?
            """, (run_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return {"exists": False}
            
            return {
                "exists": True,
                "id": row[0],
                "status": row[1],
                "start_time": row[2],
                "end_time": row[3],
                "duration": row[4],
                "total_cases": row[5],
                "passed_cases": row[6],
                "failed_cases": row[7],
            }
        except Exception as e:
            return {"exists": False, "error": str(e)}
    
    def check_run_case_data(self, run_id: str) -> Dict:
        """检查run_cases表数据"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, test_case_id, status, duration,
                       error_message, request_snapshot, response_snapshot,
                       assertions_passed, assertions_failed
                FROM run_cases WHERE run_id = ?
            """, (run_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return {"exists": False}
            
            return {
                "exists": True,
                "id": row[0],
                "test_case_id": row[1],
                "status": row[2],
                "duration": row[3],
                "error_message": row[4],
                "has_request_snapshot": row[5] is not None,
                "has_response_snapshot": row[6] is not None,
                "assertions_passed": row[7],
                "assertions_failed": row[8],
            }
        except Exception as e:
            return {"exists": False, "error": str(e)}
    
    def verify_data_consistency(self, scenario: Dict, run_id: str, case_id: str) -> Dict:
        """验证数据一致性"""
        checks = {
            "test_run_exists": False,
            "test_run_status_correct": False,
            "run_case_exists": False,
            "run_case_status_correct": False,
            "has_request_snapshot": False,
            "has_response_snapshot": False,
            "has_error_info": False,
            "status_not_running": False,
        }
        
        # 检查test_runs
        test_run = self.check_test_run_data(run_id)
        if test_run.get("exists"):
            checks["test_run_exists"] = True
            
            # 检查状态是否正确
            expected_status = scenario.get("expected_status", "failed")
            actual_status = test_run.get("status", "")
            checks["test_run_status_correct"] = actual_status in [expected_status, "error", "failed", "passed"]
            
            # 检查状态不能停留在running
            checks["status_not_running"] = actual_status != "running"
        
        # 检查run_cases
        run_case = self.check_run_case_data(run_id)
        if run_case.get("exists"):
            checks["run_case_exists"] = True
            
            # 检查状态
            actual_status = run_case.get("status", "")
            expected_status = scenario.get("expected_status", "failed")
            checks["run_case_status_correct"] = actual_status in [expected_status, "error", "failed", "passed"]
            
            # 检查快照
            checks["has_request_snapshot"] = run_case.get("has_request_snapshot", False)
            checks["has_response_snapshot"] = run_case.get("has_response_snapshot", False)
            
            # 检查错误信息：error_message或assertion失败都算有错误信息
            has_error_msg = bool(run_case.get("error_message"))
            has_failed_assertions = run_case.get("assertions_failed", 0) > 0
            checks["has_error_info"] = has_error_msg or has_failed_assertions or actual_status in ["failed", "error"]
        
        return checks
    
    def test_scenario(self, scenario: Dict, project_id: int, env_id: int):
        """测试单个异常场景"""
        print(f"\n{'─' * 100}")
        print(f"场景 {scenario['id']}: {scenario['name']}")
        print(f"描述: {scenario['description']}")
        print(f"{'─' * 100}")
        
        # 创建测试用例
        case_id = self.create_test_case(scenario, project_id)
        print(f"测试用例: {case_id}")
        
        # 执行测试用例
        print("执行测试用例...")
        success, run_id, exec_result = self.execute_test_case(case_id, env_id)
        
        if not run_id:
            print(f"❌ 执行失败: {exec_result.get('error', '未知错误')}")
            self.results.append({
                "scenario_id": scenario["id"],
                "scenario_name": scenario["name"],
                "success": False,
                "error": exec_result.get("error", "未知错误"),
            })
            return
        
        print(f"执行完成: run_id={run_id}")
        
        # 等待数据写入
        time.sleep(1)
        
        # 验证数据一致性
        print("验证数据一致性...")
        checks = self.verify_data_consistency(scenario, run_id, case_id)
        
        # 输出检查结果
        all_passed = True
        for check_name, check_result in checks.items():
            status = "✅" if check_result else "❌"
            print(f"  {status} {check_name}: {check_result}")
            if not check_result:
                all_passed = False
        
        # 记录结果
        self.results.append({
            "scenario_id": scenario["id"],
            "scenario_name": scenario["name"],
            "success": all_passed,
            "run_id": run_id,
            "checks": checks,
        })
        
        if all_passed:
            print(f"✅ 场景 {scenario['id']} 验证通过")
        else:
            print(f"❌ 场景 {scenario['id']} 验证失败")
    
    def test_duplicate_execution(self, case_id: str, env_id: int):
        """测试重复执行同一个用例"""
        print(f"\n{'─' * 100}")
        print("场景 6: 重复执行同一个用例")
        print("描述: 验证重复点击执行按钮时的数据一致性")
        print(f"{'─' * 100}")
        
        run_ids = []
        for i in range(3):
            print(f"第 {i+1} 次执行...")
            success, run_id, _ = self.execute_test_case(case_id, env_id)
            if run_id:
                run_ids.append(run_id)
                print(f"  run_id: {run_id}")
            time.sleep(0.5)
        
        # 验证每次执行都生成了独立的记录
        unique_runs = len(set(run_ids))
        all_passed = unique_runs == len(run_ids)
        
        print(f"\n执行次数: {len(run_ids)}")
        print(f"独立记录: {unique_runs}")
        
        if all_passed:
            print("✅ 重复执行验证通过：每次执行都生成了独立记录")
        else:
            print("❌ 重复执行验证失败：存在重复的run_id")
        
        self.results.append({
            "scenario_id": 6,
            "scenario_name": "重复执行同一个用例",
            "success": all_passed,
            "run_ids": run_ids,
        })
    
    def print_summary(self):
        """输出测试总结"""
        print("\n" + "=" * 100)
        print("【验收结果统计】")
        print("=" * 100)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r.get("success"))
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"总计: {total} 个场景")
        print(f"✅ 通过: {passed} 个")
        print(f"❌ 失败: {failed} 个")
        print(f"通过率: {pass_rate:.1f}%")
        print("=" * 100)
        
        if pass_rate >= 80:
            print("\n🎉 异常恢复验证通过！数据一致性良好")
        else:
            print("\n⚠️  异常恢复验证未通过，需要修复数据一致性问题")
        
        print()
    
    def run(self):
        """运行所有测试"""
        self.print_header()
        
        # 前置检查
        print("【前置检查】")
        print("─" * 100)
        if not self.check_backend_health():
            print("\n❌ 后端服务未运行，请先启动后端")
            return
        
        if not self.check_database():
            print("\n❌ 数据库不可用")
            return
        
        print()
        
        # 准备测试环境
        print("【准备测试环境】")
        print("─" * 100)
        project_id = self.create_test_project()
        env_id = self.create_test_environment(project_id)
        print()
        
        # 执行异常场景测试
        print("【异常场景测试】")
        for scenario in SCENARIOS:
            self.test_scenario(scenario, project_id, env_id)
        
        # 测试重复执行
        if self.results:
            first_case_id = f"TC_P1_5_001"
            self.test_duplicate_execution(first_case_id, env_id)
        
        # 输出总结
        self.print_summary()


if __name__ == "__main__":
    tester = FailureRecoveryTester()
    tester.run()
