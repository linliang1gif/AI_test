#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Petstore API 试点脚本
模拟用户通过前端完成完整试点流程
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"
PETSTORE_SWAGGER_URL = "https://petstore.swagger.io/v2/swagger.json"

class PilotLogger:
    def __init__(self):
        self.logs = []
        self.issues = []
        
    def log(self, step, message, status="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{status}] {step}: {message}"
        print(log_entry)
        self.logs.append(log_entry)
        
    def issue(self, level, description, impact):
        issue = {
            "level": level,
            "description": description,
            "impact": impact,
            "timestamp": datetime.now().isoformat()
        }
        self.issues.append(issue)
        self.log("ISSUE", f"[{level}] {description}", "WARN")

logger = PilotLogger()

def step_1_check_backend():
    """步骤1: 检查后端服务"""
    logger.log("步骤1", "检查后端服务状态")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            logger.log("步骤1", "✅ 后端服务正常", "SUCCESS")
            return True
        else:
            logger.issue("P0", "后端服务异常", "阻塞试点")
            return False
    except Exception as e:
        logger.issue("P0", f"后端服务无法访问: {e}", "阻塞试点")
        return False

def step_2_get_projects():
    """步骤2: 获取项目列表"""
    logger.log("步骤2", "获取项目列表")
    try:
        response = requests.get(f"{BASE_URL}/api/v2/projects", timeout=10)
        if response.status_code == 200:
            data = response.json()
            # API 可能返回 list 或 dict
            if isinstance(data, list):
                projects = data
            else:
                projects = data.get('projects', data.get('data', []))
            logger.log("步骤2", f"✅ 获取到 {len(projects)} 个项目", "SUCCESS")
            return projects
        else:
            logger.issue("P1", f"获取项目列表失败: {response.status_code}", "影响试点")
            return []
    except Exception as e:
        logger.issue("P1", f"获取项目列表异常: {e}", "影响试点")
        return []

def step_3_select_or_create_project(projects):
    """步骤3: 选择或创建项目"""
    logger.log("步骤3", "选择/创建试点项目")
    
    # 查找是否已有 Petstore 项目
    petstore_project = None
    for p in projects:
        if 'petstore' in p.get('name', '').lower():
            petstore_project = p
            break
    
    if petstore_project:
        logger.log("步骤3", f"✅ 使用现有项目: {petstore_project['name']} (ID: {petstore_project['id']})", "SUCCESS")
        return petstore_project['id']
    elif projects:
        # 使用第一个项目
        project_id = projects[0]['id']
        logger.log("步骤3", f"✅ 使用现有项目: {projects[0]['name']} (ID: {project_id})", "SUCCESS")
        return project_id
    else:
        # 创建新项目
        logger.log("步骤3", "没有现有项目，创建新项目...")
        try:
            payload = {
                "name": "Petstore API Pilot",
                "description": "Petstore API 试点项目",
                "base_url": "https://petstore.swagger.io/v2"
            }
            response = requests.post(
                f"{BASE_URL}/api/v2/projects",
                json=payload,
                timeout=10
            )
            if response.status_code in [200, 201]:
                project = response.json()
                project_id = project.get('id')
                logger.log("步骤3", f"✅ 创建项目成功 (ID: {project_id})", "SUCCESS")
                return project_id
            else:
                logger.issue("P0", f"创建项目失败: {response.status_code} - {response.text}", "阻塞试点")
                return None
        except Exception as e:
            logger.issue("P0", f"创建项目异常: {e}", "阻塞试点")
            return None

def step_4_import_swagger(project_id):
    """步骤4: 导入 Swagger"""
    logger.log("步骤4", f"导入 Petstore Swagger: {PETSTORE_SWAGGER_URL}")
    
    try:
        payload = {
            "project_id": project_id,
            "url": PETSTORE_SWAGGER_URL,
            "generate_cases": True
        }
        
        logger.log("步骤4", "发送导入请求...")
        response = requests.post(
            f"{BASE_URL}/api/v2/swagger/import-url",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.log("步骤4", f"✅ Swagger 导入成功", "SUCCESS")
            logger.log("步骤4", f"  - API 规范 ID: {result.get('api_spec_id')}")
            logger.log("步骤4", f"  - API 数量: {result.get('api_count')}")
            logger.log("步骤4", f"  - 生成用例数: {result.get('test_cases_generated')}")
            logger.log("步骤4", f"  - 用例 ID 数量: {len(result.get('test_case_ids', []))}")
            return result
        else:
            error_msg = response.text
            logger.issue("P0", f"Swagger 导入失败: {response.status_code} - {error_msg}", "阻塞试点")
            return None
            
    except requests.Timeout:
        logger.issue("P0", "Swagger 导入超时（60秒）", "阻塞试点")
        return None
    except Exception as e:
        logger.issue("P0", f"Swagger 导入异常: {e}", "阻塞试点")
        return None

def step_5_get_test_cases(project_id):
    """步骤5: 获取生成的测试用例"""
    logger.log("步骤5", "获取生成的测试用例")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v2/test-cases",
            params={"source": "swagger", "limit": 100},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            test_cases = data.get('test_cases', [])
            logger.log("步骤5", f"✅ 获取到 {len(test_cases)} 个测试用例", "SUCCESS")
            
            # 分析用例分布
            if test_cases:
                priorities = {}
                data_types = {}
                for tc in test_cases:
                    p = tc.get('priority', 'unknown')
                    priorities[p] = priorities.get(p, 0) + 1
                    dt = tc.get('data_type', 'unknown')
                    data_types[dt] = data_types.get(dt, 0) + 1
                
                logger.log("步骤5", f"  - 优先级分布: {priorities}")
                logger.log("步骤5", f"  - 数据类型分布: {data_types}")
            
            return test_cases
        else:
            logger.issue("P1", f"获取测试用例失败: {response.status_code}", "影响试点")
            return []
            
    except Exception as e:
        logger.issue("P1", f"获取测试用例异常: {e}", "影响试点")
        return []

def step_6_trigger_execution(test_case_ids, project_id):
    """步骤6: 触发测试执行"""
    logger.log("步骤6", f"触发测试执行（前 10 个用例）")
    
    if not test_case_ids:
        logger.issue("P0", "没有可执行的测试用例", "阻塞试点")
        return None
    
    try:
        # 限制执行前 10 个
        execution_ids = test_case_ids[:10]
        
        # 先获取或创建默认环境
        env_response = requests.get(
            f"{BASE_URL}/api/v2/projects/{project_id}/environments",
            timeout=10
        )
        
        environment_id = 1  # 默认环境ID
        if env_response.status_code == 200:
            envs = env_response.json()
            if envs and len(envs) > 0:
                environment_id = envs[0]['id']
                logger.log("步骤6", f"使用环境 ID: {environment_id}")
        
        # 使用简化的触发接口
        params = {
            "project_id": project_id,
            "environment_id": environment_id,
            "test_case_ids": execution_ids
        }
        
        logger.log("步骤6", f"发送执行请求（{len(execution_ids)} 个用例）...")
        response = requests.post(
            f"{BASE_URL}/api/v2/execution/trigger-simple",
            params=params,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            run_id = result.get('run_id')
            logger.log("步骤6", f"✅ 执行触发成功", "SUCCESS")
            logger.log("步骤6", f"  - Run ID: {run_id}")
            return run_id
        else:
            error_msg = response.text
            logger.issue("P0", f"执行触发失败: {response.status_code} - {error_msg}", "阻塞试点")
            return None
            
    except Exception as e:
        logger.issue("P0", f"执行触发异常: {e}", "阻塞试点")
        return None

def step_7_check_execution_status(run_id):
    """步骤7: 查看执行状态"""
    logger.log("步骤7", f"查看执行状态 (Run ID: {run_id})")
    
    try:
        # 等待执行开始
        time.sleep(2)
        
        response = requests.get(
            f"{BASE_URL}/api/v2/test-runs/{run_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.log("步骤7", f"✅ 获取执行状态成功", "SUCCESS")
            logger.log("步骤7", f"  - 状态: {data.get('status')}")
            logger.log("步骤7", f"  - 总用例数: {data.get('total_cases')}")
            logger.log("步骤7", f"  - 通过数: {data.get('passed_cases')}")
            logger.log("步骤7", f"  - 失败数: {data.get('failed_cases')}")
            return data
        else:
            logger.issue("P1", f"获取执行状态失败: {response.status_code}", "影响试点")
            return None
            
    except Exception as e:
        logger.issue("P1", f"获取执行状态异常: {e}", "影响试点")
        return None

def step_8_check_run_cases(run_id):
    """步骤8: 查看 RunCase"""
    logger.log("步骤8", f"查看 RunCase 详情")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v2/test-runs/{run_id}/cases",
            timeout=10
        )
        
        if response.status_code == 200:
            cases = response.json()
            logger.log("步骤8", f"✅ 获取到 {len(cases)} 个 RunCase", "SUCCESS")
            
            # 分析状态分布
            if cases:
                statuses = {}
                for case in cases:
                    status = case.get('status', 'unknown')
                    statuses[status] = statuses.get(status, 0) + 1
                logger.log("步骤8", f"  - 状态分布: {statuses}")
            
            return cases
        else:
            logger.issue("P1", f"获取 RunCase 失败: {response.status_code}", "影响试点")
            return []
            
    except Exception as e:
        logger.issue("P1", f"获取 RunCase 异常: {e}", "影响试点")
        return []

def step_9_check_snapshots(run_id, run_cases):
    """步骤9: 检查快照记录"""
    logger.log("步骤9", "检查请求/响应快照")
    
    if not run_cases:
        logger.issue("P1", "没有 RunCase，无法检查快照", "影响试点")
        return False
    
    # 检查第一个 RunCase 的快照
    first_case = run_cases[0]
    case_id = first_case.get('id')
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v2/test-runs/{run_id}/cases/{case_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            case_detail = response.json()
            has_request = 'request_snapshot' in case_detail
            has_response = 'response_snapshot' in case_detail
            
            logger.log("步骤9", f"✅ 快照检查完成", "SUCCESS")
            logger.log("步骤9", f"  - 请求快照: {'有' if has_request else '无'}")
            logger.log("步骤9", f"  - 响应快照: {'有' if has_response else '无'}")
            
            if not has_request or not has_response:
                logger.issue("P1", "快照记录不完整", "影响问题定位")
            
            return has_request and has_response
        else:
            logger.issue("P1", f"获取快照失败: {response.status_code}", "影响试点")
            return False
            
    except Exception as e:
        logger.issue("P1", f"获取快照异常: {e}", "影响试点")
        return False

def generate_report():
    """生成试点报告"""
    print("\n" + "=" * 60)
    print("试点报告")
    print("=" * 60)
    
    print("\n执行日志:")
    for log in logger.logs:
        print(log)
    
    print("\n" + "=" * 60)
    print("问题清单")
    print("=" * 60)
    
    if not logger.issues:
        print("✅ 未发现问题")
    else:
        p0_issues = [i for i in logger.issues if i['level'] == 'P0']
        p1_issues = [i for i in logger.issues if i['level'] == 'P1']
        p2_issues = [i for i in logger.issues if i['level'] == 'P2']
        
        if p0_issues:
            print(f"\nP0 阻塞性问题 ({len(p0_issues)} 个):")
            for i, issue in enumerate(p0_issues, 1):
                print(f"  {i}. {issue['description']}")
                print(f"     影响: {issue['impact']}")
        
        if p1_issues:
            print(f"\nP1 严重问题 ({len(p1_issues)} 个):")
            for i, issue in enumerate(p1_issues, 1):
                print(f"  {i}. {issue['description']}")
                print(f"     影响: {issue['impact']}")
        
        if p2_issues:
            print(f"\nP2 体验问题 ({len(p2_issues)} 个):")
            for i, issue in enumerate(p2_issues, 1):
                print(f"  {i}. {issue['description']}")
                print(f"     影响: {issue['impact']}")
    
    print("\n" + "=" * 60)
    print("试点结论")
    print("=" * 60)
    
    p0_count = len([i for i in logger.issues if i['level'] == 'P0'])
    
    if p0_count == 0:
        print("✅ 试点通过 - 基础链路打通")
        print("建议: 可以扩大到第二个项目试点")
    else:
        print(f"❌ 试点失败 - 存在 {p0_count} 个阻塞性问题")
        print("建议: 修复 P0 问题后重新试点")

def main():
    """主流程"""
    print("=" * 60)
    print("Petstore API 试点开始")
    print("=" * 60)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"后端: {BASE_URL}")
    print(f"Swagger: {PETSTORE_SWAGGER_URL}")
    print("=" * 60)
    print()
    
    # 步骤1: 检查后端
    if not step_1_check_backend():
        generate_report()
        return
    
    # 步骤2: 获取项目列表
    projects = step_2_get_projects()
    
    # 步骤3: 选择项目
    project_id = step_3_select_or_create_project(projects)
    if not project_id:
        generate_report()
        return
    
    # 步骤4: 导入 Swagger
    import_result = step_4_import_swagger(project_id)
    if not import_result:
        generate_report()
        return
    
    # 步骤5: 获取测试用例
    test_cases = step_5_get_test_cases(project_id)
    # 使用查询到的测试用例 ID，而不是导入返回的 ID（导入可能因去重返回空列表）
    test_case_ids = [tc['id'] for tc in test_cases] if test_cases else []
    
    # 步骤6: 触发执行
    run_id = step_6_trigger_execution(test_case_ids, project_id)
    if not run_id:
        generate_report()
        return
    
    # 步骤7: 查看执行状态
    execution_status = step_7_check_execution_status(run_id)
    
    # 步骤8: 查看 RunCase
    run_cases = step_8_check_run_cases(run_id)
    
    # 步骤9: 检查快照
    step_9_check_snapshots(run_id, run_cases)
    
    # 生成报告
    generate_report()

if __name__ == "__main__":
    main()
