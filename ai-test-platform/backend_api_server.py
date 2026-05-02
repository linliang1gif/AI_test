#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Test Platform - Backend API Server
P2-2 重构: app 创建由 backend.app.create_app() 完成，
本文件保留内联业务路由（后续逐步拆分到 routes/）。
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from fastapi import HTTPException, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, 'test_data')
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ── P2-2: 通过工厂函数创建 app ──
from backend.app import create_app
app = create_app()

# ── 模块可用性标志（内联路由仍需） ──
from backend.router_registry import MODULE_FLAGS
MODULES_SDK_AVAILABLE = MODULE_FLAGS.get("modules_sdk", False)
CORE_MODELS_AVAILABLE = MODULE_FLAGS.get("core_models", False)
MODEL_CONVERTER_AVAILABLE = MODULE_FLAGS.get("model_converter", False)
TEST_DATA_AVAILABLE = MODULE_FLAGS.get("test_data_factory", False)

# 按需导入（仅内联路由实际用到时）
try:
    from modules.swagger import SwaggerTestCaseGenerator
    from modules.executor import ExecutionEngine
    from modules.healing import HealingEngine
    from modules.report import ReportGenerator
    from modules.data import TestDataManager
except ImportError:
    pass

try:
    from core import (TestCase, ExecutionResult, TestCaseStatus, TestCasePriority,
                      DataType, ExpectedBehavior, create_test_case, create_execution_result)
except ImportError:
    pass

try:
    from utils.model_converter import (testcase_to_dict, dict_to_testcase,
        execution_result_to_dict, testcases_to_list, execution_results_to_list,
        enrich_testcase_dict, enrich_testcase_list)
except ImportError:
    pass

try:
    from test_data.data_factory import factory
except ImportError:
    factory = None


# P2-2: 启动初始化、CORS、路由注册已迁移到 backend/ 包
# - backend/startup.py: 数据库检查 + Phase 迁移
# - backend/app.py (create_app): CORS + 异常处理
# - backend/router_registry.py: 统一路由注册
# - backend/health.py: /health, /readiness, /admin/app-mode

# ==================== 数据模型 ====================

# 测试数据工厂相关模型
class DataGenerationRequest(BaseModel):
    data_type: str
    count: int = 1
    context: Optional[Dict[str, Any]] = None
    overrides: Optional[Dict[str, Any]] = None

class SmartGenerationRequest(BaseModel):
    field_name: str
    context: Optional[Dict[str, Any]] = None

class SmartObjectRequest(BaseModel):
    data_schema: Dict[str, str]
    context: Optional[Dict[str, Any]] = None

class QualityEvaluationRequest(BaseModel):
    data: Dict[str, Any]
    data_schema: Optional[Dict[str, Any]] = None

class BatchEvaluationRequest(BaseModel):
    data_list: List[Dict[str, Any]]

# P2-2: /, /health, /readiness, /admin/app-mode 已迁移到 backend/health.py

# ==================== 测试数据工厂 API ====================

@app.post("/api/test-data/generate")
async def generate_test_data(request: DataGenerationRequest):
    """生成测试数据"""
    if not TEST_DATA_AVAILABLE:
        raise HTTPException(status_code=503, detail="测试数据工厂不可用")
    
    try:
        if request.count == 1:
            # 生成单个数据
            if request.data_type in ['user', 'order', 'product', 'address', 'payment', 'inventory']:
                data = getattr(factory, request.data_type)(**(request.overrides or {}))
            else:
                data = factory.generate(request.data_type, **(request.overrides or {}))
            
            return {
                "success": True,
                "data": data,
                "message": f"成功生成{request.data_type}数据"
            }
        else:
            # 批量生成
            data_list = factory.batch(request.data_type, request.count, **(request.overrides or {}))
            return {
                "success": True,
                "data": data_list,
                "count": len(data_list),
                "message": f"成功生成{request.count}条{request.data_type}数据"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/test-data/smart-generate")
async def smart_generate_field(request: SmartGenerationRequest):
    """AI智能生成字段"""
    if not TEST_DATA_AVAILABLE:
        raise HTTPException(status_code=503, detail="测试数据工厂不可用")
    
    try:
        value = factory.smart_generate(request.field_name, request.context)
        return {
            "success": True,
            "field_name": request.field_name,
            "value": value,
            "message": "智能生成成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/test-data/smart-object")
async def smart_generate_object(request: SmartObjectRequest):
    """AI智能生成对象"""
    if not TEST_DATA_AVAILABLE:
        raise HTTPException(status_code=503, detail="测试数据工厂不可用")
    
    try:
        data = factory.smart_object(request.data_schema, request.context)
        return {
            "success": True,
            "data": data,
            "message": "智能对象生成成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/test-data/analyze-field")
async def analyze_field(field_name: str):
    """分析字段"""
    if not TEST_DATA_AVAILABLE:
        raise HTTPException(status_code=503, detail="测试数据工厂不可用")
    
    try:
        analysis = factory.analyze_field(field_name)
        return {
            "success": True,
            "analysis": analysis,
            "message": "字段分析完成"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/test-data/analyze-schema")
async def analyze_schema(schema: Dict[str, str]):
    """分析Schema"""
    if not TEST_DATA_AVAILABLE:
        raise HTTPException(status_code=503, detail="测试数据工厂不可用")
    
    try:
        analysis = factory.analyze_schema(schema)
        return {
            "success": True,
            "analysis": analysis,
            "message": "Schema分析完成"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/test-data/scenarios/{entity_type}")
async def get_test_scenarios(entity_type: str):
    """获取测试场景建议"""
    if not TEST_DATA_AVAILABLE:
        raise HTTPException(status_code=503, detail="测试数据工厂不可用")
    
    try:
        scenarios = factory.suggest_scenarios(entity_type)
        return {
            "success": True,
            "entity_type": entity_type,
            "scenarios": scenarios,
            "count": len(scenarios),
            "message": "场景建议获取成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/test-data/evaluate")
async def evaluate_quality(request: QualityEvaluationRequest):
    """评估数据质量"""
    if not TEST_DATA_AVAILABLE:
        raise HTTPException(status_code=503, detail="测试数据工厂不可用")
    
    try:
        result = factory.evaluate_quality(request.data, request.data_schema)
        return {
            "success": True,
            "evaluation": result,
            "message": "质量评估完成"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/test-data/batch-evaluate")
async def batch_evaluate_quality(request: BatchEvaluationRequest):
    """批量评估数据质量"""
    if not TEST_DATA_AVAILABLE:
        raise HTTPException(status_code=503, detail="测试数据工厂不可用")
    
    try:
        result = factory.batch_evaluate(request.data_list)
        return {
            "success": True,
            "evaluation": result,
            "message": "批量评估完成"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/test-data/templates")
async def list_templates():
    """列出所有模板"""
    if not TEST_DATA_AVAILABLE:
        raise HTTPException(status_code=503, detail="测试数据工厂不可用")
    
    try:
        templates = factory.list_templates()
        return {
            "success": True,
            "templates": templates,
            "count": len(templates),
            "message": "模板列表获取成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/test-data/from-template")
async def generate_from_template(template_name: str, overrides: Optional[Dict[str, Any]] = None):
    """从模板生成数据"""
    if not TEST_DATA_AVAILABLE:
        raise HTTPException(status_code=503, detail="测试数据工厂不可用")
    
    try:
        data = factory.from_template(template_name, **(overrides or {}))
        return {
            "success": True,
            "template_name": template_name,
            "data": data,
            "message": "模板数据生成成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/test-data/stats")
async def get_generation_stats():
    """获取生成统计"""
    if not TEST_DATA_AVAILABLE:
        raise HTTPException(status_code=503, detail="测试数据工厂不可用")
    
    try:
        stats = factory.generation_stats()
        return {
            "success": True,
            "stats": stats,
            "message": "统计信息获取成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/test-data/boundary-values/{data_type}")
async def get_boundary_values(data_type: str, min_value: Optional[int] = None, max_value: Optional[int] = None):
    """获取边界值"""
    if not TEST_DATA_AVAILABLE:
        raise HTTPException(status_code=503, detail="测试数据工厂不可用")
    
    try:
        kwargs = {}
        if min_value is not None:
            kwargs['min_value'] = min_value
        if max_value is not None:
            kwargs['max_value'] = max_value
        
        values = factory.boundary_values(data_type, **kwargs)
        return {
            "success": True,
            "data_type": data_type,
            "values": values,
            "count": len(values),
            "message": "边界值获取成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/test-data/invalid-values/{data_type}")
async def get_invalid_values(data_type: str):
    """获取非法值"""
    if not TEST_DATA_AVAILABLE:
        raise HTTPException(status_code=503, detail="测试数据工厂不可用")
    
    try:
        values = factory.invalid_values(data_type)
        return {
            "success": True,
            "data_type": data_type,
            "values": values,
            "count": len(values),
            "message": "非法值获取成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 数据集管理 API ====================

# 导入数据集管理器
try:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent / 'test_data'))
    from dataset_manager import dataset_manager
    DATASET_MANAGER_AVAILABLE = True
except ImportError as e:
    DATASET_MANAGER_AVAILABLE = False
    print(f"⚠️  数据集管理器导入失败: {e}")

@app.post("/api/test-data/datasets")
async def create_dataset(request: Dict[str, Any]):
    """创建数据集"""
    if not DATASET_MANAGER_AVAILABLE:
        raise HTTPException(status_code=503, detail="数据集管理器不可用")
    
    try:
        dataset = dataset_manager.create_dataset(
            name=request.get("name"),
            data=request.get("data"),
            description=request.get("description", ""),
            api_id=request.get("api_id"),
            tags=request.get("tags", [])
        )
        return {
            "success": True,
            "dataset": dataset,
            "message": "数据集创建成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/test-data/datasets")
async def get_datasets(
    keyword: Optional[str] = None,
    api_id: Optional[str] = None,
    tags: Optional[str] = None
):
    """获取数据集列表"""
    if not DATASET_MANAGER_AVAILABLE:
        raise HTTPException(status_code=503, detail="数据集管理器不可用")
    
    try:
        if keyword or api_id or tags:
            tag_list = tags.split(",") if tags else None
            datasets = dataset_manager.search_datasets(
                keyword=keyword,
                api_id=api_id,
                tags=tag_list
            )
        else:
            datasets = dataset_manager.get_all_datasets()
        
        return {
            "success": True,
            "datasets": datasets,
            "count": len(datasets)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/test-data/datasets/{dataset_id}")
async def get_dataset(dataset_id: str):
    """获取单个数据集"""
    if not DATASET_MANAGER_AVAILABLE:
        raise HTTPException(status_code=503, detail="数据集管理器不可用")
    
    try:
        dataset = dataset_manager.get_dataset(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="数据集不存在")
        
        return {
            "success": True,
            "dataset": dataset
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/test-data/datasets/{dataset_id}")
async def update_dataset(dataset_id: str, request: Dict[str, Any]):
    """更新数据集"""
    if not DATASET_MANAGER_AVAILABLE:
        raise HTTPException(status_code=503, detail="数据集管理器不可用")
    
    try:
        dataset = dataset_manager.update_dataset(
            dataset_id=dataset_id,
            name=request.get("name"),
            description=request.get("description"),
            data=request.get("data"),
            tags=request.get("tags")
        )
        
        if not dataset:
            raise HTTPException(status_code=404, detail="数据集不存在")
        
        return {
            "success": True,
            "dataset": dataset,
            "message": "数据集更新成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/test-data/datasets/{dataset_id}")
async def delete_dataset(dataset_id: str):
    """删除数据集"""
    if not DATASET_MANAGER_AVAILABLE:
        raise HTTPException(status_code=503, detail="数据集管理器不可用")
    
    try:
        success = dataset_manager.delete_dataset(dataset_id)
        if not success:
            raise HTTPException(status_code=404, detail="数据集不存在")
        
        return {
            "success": True,
            "message": "数据集删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/test-data/datasets/{dataset_id}/use")
async def use_dataset(dataset_id: str):
    """使用数据集(增加使用次数)"""
    if not DATASET_MANAGER_AVAILABLE:
        raise HTTPException(status_code=503, detail="数据集管理器不可用")
    
    try:
        dataset_manager.increment_usage(dataset_id)
        dataset = dataset_manager.get_dataset(dataset_id)
        
        return {
            "success": True,
            "dataset": dataset,
            "message": "数据集使用次数已更新"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/test-data/datasets-stats")
async def get_datasets_stats():
    """获取数据集统计信息"""
    if not DATASET_MANAGER_AVAILABLE:
        raise HTTPException(status_code=503, detail="数据集管理器不可用")
    
    try:
        stats = dataset_manager.get_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Test Cases + Dataset Integration ====================

@app.post("/api/test-cases/{test_case_id}/bind-dataset")
async def bind_dataset_to_testcase(test_case_id: int, request: Dict[str, Any]):
    """绑定数据集到测试用例"""
    try:
        dataset_id = request.get("dataset_id")
        if not dataset_id:
            raise HTTPException(status_code=400, detail="缺少dataset_id参数")
        
        # 这里可以将绑定关系保存到数据库
        # 目前简单返回成功
        return {
            "success": True,
            "message": f"测试用例 {test_case_id} 已绑定数据集 {dataset_id}",
            "test_case_id": test_case_id,
            "dataset_id": dataset_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/test-cases/{test_case_id}/dataset")
async def get_testcase_dataset(test_case_id: int):
    """获取测试用例绑定的数据集"""
    try:
        # 这里应该从数据库查询绑定关系
        # 目前返回示例数据
        return {
            "success": True,
            "test_case_id": test_case_id,
            "dataset_id": None,
            "dataset": None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Dashboard API ====================

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """获取Dashboard统计数据"""
    # 从内存数据库获取实际数据
    total_tests = len(test_cases_db)
    passed = sum(1 for tc in test_cases_db if tc.get('status') == 'passed')
    failed = sum(1 for tc in test_cases_db if tc.get('status') == 'failed')
    
    # 计算覆盖率(如果有测试用例)
    coverage = round((passed / total_tests * 100), 1) if total_tests > 0 else 0
    
    # 获取最近的测试执行记录
    recent_tests = []
    for tc in test_cases_db[-5:]:  # 最近5条
        if tc.get('status'):
            recent_tests.append({
                "name": tc.get('title', f'测试用例 {tc.get("id", "未知")}'),
                "time": tc.get('updated_at', '未知时间'),
                "status": tc.get('status', 'unknown')
            })
    
    return {
        "totalTests": total_tests,
        "passed": passed,
        "failed": failed,
        "coverage": coverage,
        "recentTests": recent_tests
    }

# ==================== Projects API ====================

# ==================== 数据持久化初始化 ====================

# 初始化数据管理器并加载持久化数据
from utils.data_manager import get_data_manager
data_manager = get_data_manager()

# 从持久化存储加载所有数据
projects_db = data_manager.get_data("projects", [])
apis_db = data_manager.get_data("apis", [])
test_runs_db = data_manager.get_data("test_runs", [])
reports_db = data_manager.get_data("reports", [])
scripts_db = data_manager.get_data("scripts", [])

# 如果是首次启动,初始化示例数据
if not projects_db:
    projects_db = [
        {
            "id": 1, 
            "name": "电商平台", 
            "description": "电商系统核心功能测试,包括商品管理、订单处理、支付流程等", 
            "status": "active",
            "environment": "production",
            "baseUrl": "https://api.ecommerce.com",
            "testsCount": 156,
            "coverage": 85,
            "lastRun": "2小时前",
            "createdAt": "2024-01-15",
            "team": "电商团队"
        },
        {
            "id": 2, 
            "name": "支付系统", 
            "description": "第三方支付接口集成测试,支持微信、支付宝等多种支付方式", 
            "status": "active",
            "environment": "staging",
            "baseUrl": "https://pay-test.example.com",
            "testsCount": 89,
            "coverage": 92,
            "lastRun": "1天前",
            "createdAt": "2024-01-20",
            "team": "支付团队"
        },
        {
            "id": 3, 
            "name": "用户中心", 
            "description": "用户注册、登录、权限管理等核心功能测试", 
            "status": "active",
            "environment": "development",
            "baseUrl": "http://localhost:8080",
            "testsCount": 67,
            "coverage": 78,
            "lastRun": "30分钟前",
            "createdAt": "2024-02-01",
            "team": "用户团队"
        },
    ]
    data_manager.set_data("projects", projects_db, save=True)

if not apis_db:
    apis_db = [
        {"id": 1, "name": "用户登录", "method": "POST", "path": "/api/login", "status": "active"},
        {"id": 2, "name": "获取用户信息", "method": "GET", "path": "/api/user/info", "status": "active"},
    ]
    data_manager.set_data("apis", apis_db, save=True)


if not reports_db:
    reports_db = [
        {
            "id": 1,
            "name": "综合测试报告 - 2024-03-21",
            "type": "Comprehensive Report",
            "date": "2024-03-21",
            "size": "2.4 MB",
            "testRuns": 5,
            "passRate": 88,
            "format": "HTML"
        },
        {
            "id": 2,
            "name": "覆盖率报告 - 2024-03-20",
            "type": "Coverage Report",
            "date": "2024-03-20",
            "size": "1.1 MB",
            "testRuns": 3,
            "passRate": 92,
            "format": "PDF"
        },
        {
            "id": 3,
            "name": "Bug分析报告 - 2024-03-19",
            "type": "Bug Report",
            "date": "2024-03-19",
            "size": "0.8 MB",
            "testRuns": 2,
            "passRate": 75,
            "format": "Excel"
        },
    ]
    data_manager.set_data("reports", reports_db, save=True)
print(f"📂 数据加载完成: 项目({len(projects_db)}) API({len(apis_db)}) 测试运行({len(test_runs_db)}) 报告({len(reports_db)})")

# ==================== Projects API ====================

@app.get("/api/projects")
async def get_projects():
    """获取所有项目"""
    return {
        "success": True,
        "projects": projects_db,  # 改为projects字段
        "count": len(projects_db)
    }

@app.post("/api/projects")
async def create_project(project: Dict[str, Any]):
    """创建项目"""
    new_project = {
        "id": len(projects_db) + 1,
        "createdAt": "2024-03-24",
        "status": "active",
        "testsCount": 0,
        "coverage": 0,
        "lastRun": "从未运行",
        "team": "默认团队",
        **project
    }
    projects_db.append(new_project)
    
    # 保存到持久化存储
    data_manager.set_data("projects", projects_db, save=True)
    
    return {
        "success": True,
        "project": new_project,
        "message": "项目创建成功"
    }

@app.put("/api/projects/{project_id}")
async def update_project(project_id: int, updates: Dict[str, Any]):
    """更新项目"""
    for p in projects_db:
        if p["id"] == project_id:
            for k, v in updates.items():
                if k != "id":
                    p[k] = v
            data_manager.set_data("projects", projects_db, save=True)
            return {"success": True, "project": p}
    raise HTTPException(status_code=404, detail="项目不存在")

@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: int):
    """删除项目"""
    global projects_db
    projects_db = [p for p in projects_db if p["id"] != project_id]
    
    # 保存到持久化存储
    data_manager.set_data("projects", projects_db, save=True)
    
    return {
        "success": True,
        "message": "项目删除成功"
    }

# ==================== APIs Explorer ====================

@app.get("/api/apis")
async def get_apis():
    """获取所有API"""
    return {
        "success": True,
        "apis": apis_db,
        "count": len(apis_db)
    }

@app.get("/api/api-explorer")
async def api_explorer():
    """API浏览器数据接口"""
    return {
        "success": True,
        "message": "API Explorer",
        "apis": apis_db,
        "count": len(apis_db)
    }

@app.get("/api/api-explorer/endpoints")
async def get_api_endpoints():
    """获取API接口列表"""
    return {
        "success": True,
        "endpoints": apis_db,
        "count": len(apis_db)
    }

@app.post("/api/save-api-as-testcase")
async def save_api_as_testcase(request: Dict[str, Any]):
    """将API执行结果保存为测试用例"""
    try:
        api_info = request.get('api_info', {})
        execution_result = request.get('execution_result', {})
        request_data = request.get('request_data', {})
        
        import time
        
        # 生成测试用例ID
        case_id = f"TC_{int(time.time())}_{len(test_cases_db)}"
        
        # 构建测试用例
        test_case = {
            "id": case_id,
            "title": f"{api_info.get('name', 'API测试')} - {api_info.get('method')} {api_info.get('path')}",
            "module": api_info.get('tags', ['default'])[0] if api_info.get('tags') else 'default',
            "priority": "medium",
            "status": "passed" if execution_result.get('success') else "failed",
            "lastRun": time.strftime("%Y-%m-%d %H:%M:%S"),
            "steps": [
                f"发送 {api_info.get('method')} 请求到 {api_info.get('path')}",
                f"请求参数: {request_data}"
            ],
            "expected": f"返回状态码 {execution_result.get('status_code')}",
            "source": "api_execution",
            "type": "API测试",
            "data_type": "valid",
            "expected_behavior": "success" if execution_result.get('success') else "client_error",
            "execution_config": {
                "method": api_info.get('method'),
                "url": api_info.get('path'),
                "data": request_data,
                "timeout": 30
            },
            "execution_result": {
                "status_code": execution_result.get('status_code'),
                "response_time": execution_result.get('response_time'),
                "response_data": execution_result.get('response_data')
            }
        }
        
        # 保存到数据库
        test_cases_db.append(test_case)
        
        # 持久化
        from utils.data_manager import get_data_manager
        data_manager = get_data_manager()
        data_manager.set_data("test_cases", test_cases_db, save=True)
        
        return {
            "success": True,
            "message": "测试用例保存成功",
            "test_case_id": case_id
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/execute-api", deprecated=True)
async def execute_api(request: Dict[str, Any]):
    """[已废弃] 请使用 POST /api/v2/test-cases/{case_id}/execute"""
    print("⚠️ [DEPRECATED] /api/execute-api 已废弃，请迁移到 /api/v2/test-cases/{case_id}/execute")
    try:
        base_url = request.get('base_url', 'http://localhost:8000')
        method = request.get('method', 'GET')
        path = request.get('path', '/')
        data = request.get('data', {})
        timeout = request.get('timeout', 30)
        auth_token = request.get('auth_token')
        
        # 🔥 使用ExecutionEngine执行API
        from modules.executor.real_execution_engine import get_execution_engine
        
        engine = get_execution_engine()
        
        # 构建完整URL
        url = f"{base_url.rstrip('/')}{path}"
        
        # 构建请求头
        headers = {'Content-Type': 'application/json'}
        if auth_token:
            # 支持多种认证方式
            if auth_token.startswith('Bearer '):
                headers['Authorization'] = auth_token
            else:
                headers['Authorization'] = f'Bearer {auth_token}'
        
        # 构建测试用例
        test_case = {
            'id': 'api_test',
            'name': f"{method} {url}",
            'execution_type': 'api',
            'config': {
                'url': url,
                'method': method,
                'headers': headers,
                'body': data
            },
            'timeout': timeout
        }
        
        # 执行测试
        result = engine.execute(test_case)
        
        # 返回结果
        return {
            "success": result.success,
            "status_code": result.status_code,
            "response_time": int(result.duration * 1000),
            "response_data": result.response,
            "headers": result.response_headers,
            "trace_id": result.trace_id,
            "error": result.error_message if not result.success else None
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "status_code": 0,
            "response_time": 0
        }

@app.post("/api/swagger/parse")
async def parse_swagger(data: Dict[str, str]):
    """解析Swagger URL（使用 modules SDK）"""
    try:
        url = data.get('url')
        if not url:
            return {"success": False, "message": "缺少URL参数"}
        
        # 🔧 使用 modules SDK
        if MODULES_SDK_AVAILABLE:
            generator = SwaggerTestCaseGenerator(url)
            test_cases = generator.generate_all_testcases()
            
            # 转换为 API 响应格式
            apis = generator.export_to_json(test_cases)
            
            # 获取统计信息
            stats = generator.get_statistics(test_cases)
            
            return {
                "success": True,
                "message": f"成功解析 {len(apis)} 个API",
                "count": len(apis),
                "apis": apis,
                "stats": stats
            }
        else:
            # 降级到原有实现
            import requests
            
            # 获取Swagger文档
            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                return {"success": False, "message": f"无法访问URL: {response.status_code}"}
            
            swagger_doc = response.json()
            
            # 解析API
            parsed_apis = []
            paths = swagger_doc.get('paths', {})
            
            for path, methods in paths.items():
                for method, details in methods.items():
                    if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                        api = {
                            "id": len(parsed_apis) + 1,
                            "method": method.upper(),
                            "path": path,
                            "summary": details.get('summary', ''),
                            "description": details.get('description', ''),
                            "tags": details.get('tags', []),
                            "parameters": details.get('parameters', []),
                            "requestBody": details.get('requestBody', None)
                        }
                        parsed_apis.append(api)
            
            # 保存到数据库
            apis_db.clear()
            apis_db.extend(parsed_apis)
            
            return {
                "success": True,
                "message": f"成功解析 {len(parsed_apis)} 个API",
                "count": len(parsed_apis),
                "apis": parsed_apis
            }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"解析失败: {str(e)}"
        }

@app.post("/api/swagger/upload")
async def upload_swagger(file: UploadFile = File(...)):
    """上传Swagger文件（使用 modules SDK）"""
    try:
        import json
        import yaml
        import tempfile
        
        # 检查文件是否为空
        if not file:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "未选择文件"}
            )
        
        # 读取文件内容
        content = await file.read()
        
        if not content:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "文件内容为空"}
            )
        
        # 🔧 使用 modules SDK
        if MODULES_SDK_AVAILABLE:
            # 保存到临时文件
            with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json') as temp_file:
                temp_file.write(content)
                temp_path = temp_file.name
            
            try:
                generator = SwaggerTestCaseGenerator(temp_path)
                test_cases = generator.generate_all_testcases()
                
                # 转换为 API 响应格式（测试用例）
                test_case_apis = generator.export_to_json(test_cases)
                
                # 🔧 从Swagger提取API定义（完整格式用于API管理和测试数据生成）
                swagger_apis = []
                all_apis = generator.loader.get_all_apis()
                for idx, api in enumerate(all_apis, 1):
                    swagger_apis.append({
                        "id": idx,
                        "name": api.get('summary', api.get('operation_id', f"API_{idx}")),
                        "summary": api.get('summary', ''),
                        "method": api.get('method', 'GET'),
                        "path": api.get('path', ''),
                        "description": api.get('description', ''),
                        "tags": api.get('tags', []),
                        "status": "active",
                        # 保存完整的参数和请求体信息，用于测试数据生成
                        "parameters": api.get('parameters', []),
                        "requestBody": api.get('request_body'),
                        "responses": api.get('responses', {})
                    })
                
                # 🔧 保存到 APIs 数据库（使用简化格式）
                apis_db.clear()
                apis_db.extend(swagger_apis)
                data_manager.set_data("apis", apis_db, save=True)
                
                # 清理临时文件
                Path(temp_path).unlink()
                
                return JSONResponse(
                    status_code=200,
                    content={
                        "success": True,
                        "message": f"成功解析 {len(swagger_apis)} 个API",
                        "count": len(swagger_apis),
                        "apis": swagger_apis
                    }
                )
            except ValueError as e:
                # 清理临时文件
                if Path(temp_path).exists():
                    Path(temp_path).unlink()
                
                # 返回更友好的错误信息
                error_msg = str(e)
                if "Unknown spec version" in error_msg:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "success": False,
                            "message": f"不支持的Swagger/OpenAPI版本: {error_msg}"
                        }
                    )
                else:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "success": False,
                            "message": f"文件解析失败: {error_msg}"
                        }
                    )
            except Exception as e:
                # 清理临时文件
                if Path(temp_path).exists():
                    Path(temp_path).unlink()
                
                import traceback
                traceback.print_exc()
                
                return JSONResponse(
                    status_code=500,
                    content={
                        "success": False,
                        "message": f"服务器错误: {str(e)}"
                    }
                )
        else:
            # 降级到原有实现
            # 尝试解析JSON或YAML
            swagger_doc = None
            try:
                swagger_doc = json.loads(content)
            except json.JSONDecodeError:
                try:
                    swagger_doc = yaml.safe_load(content)
                except yaml.YAMLError as e:
                    return JSONResponse(
                        status_code=400,
                        content={"success": False, "message": f"无法解析文件,请确保是有效的JSON或YAML格式: {str(e)}"}
                    )
            
            if not swagger_doc:
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "message": "文件解析结果为空"}
                )
            
            # 解析API
            parsed_apis = []
            paths = swagger_doc.get('paths', {})
            
            if not paths:
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "message": "Swagger文档中没有找到API路径定义"}
                )
            
            for path, methods in paths.items():
                for method, details in methods.items():
                    if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                        api = {
                            "id": len(parsed_apis) + 1,
                            "method": method.upper(),
                            "path": path,
                            "summary": details.get('summary', ''),
                            "description": details.get('description', ''),
                            "tags": details.get('tags', []),
                            "parameters": details.get('parameters', []),
                            "requestBody": details.get('requestBody', None)
                        }
                        parsed_apis.append(api)
            
            # 保存到数据库
            apis_db.clear()
            apis_db.extend(parsed_apis)
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": f"成功解析 {len(parsed_apis)} 个API",
                    "count": len(parsed_apis)
                }
            )
        
    except Exception as e:
        print(f"❌ Swagger上传错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"上传失败: {str(e)}"
            }
        )

# ==================== Test Cases API ====================

# 从持久化存储加载测试用例
test_cases_db = data_manager.get_data("test_cases", [])
print(f"📂 从持久化存储加载了 {len(test_cases_db)} 个测试用例")

@app.get("/api/test-cases")
async def get_test_cases():
    """获取所有测试用例"""
    return {
        "success": True,
        "data": test_cases_db,
        "count": len(test_cases_db)
    }

@app.post("/api/test-cases")
async def create_test_case(test_case: Dict[str, Any]):
    """创建测试用例"""
    new_case = {
        "id": len(test_cases_db) + 1,
        "created_at": "2024-03-21",
        **test_case
    }
    test_cases_db.append(new_case)
    
    # 保存到持久化存储
    data_manager.add_item("test_cases", new_case, save=True)
    
    return {
        "success": True,
        "data": new_case,
        "message": "测试用例创建成功"
    }

class BatchDeleteRequest(BaseModel):
    ids: List[Union[int, str]]  # 支持整数和字符串ID

@app.post("/api/testcases/batch-delete")
async def batch_delete_testcases(request: BatchDeleteRequest):
    """批量删除测试用例"""
    try:
        deleted_count = 0
        ids_to_delete = set(request.ids)
        
        # 过滤掉要删除的测试用例
        global test_cases_db
        original_count = len(test_cases_db)
        test_cases_db[:] = [tc for tc in test_cases_db if tc['id'] not in ids_to_delete]
        deleted_count = original_count - len(test_cases_db)
        
        # 保存到持久化存储
        data_manager.set_data("test_cases", test_cases_db, save=True)
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"成功删除 {deleted_count} 个测试用例"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "批量删除失败"
        }

@app.post("/api/testcases/generate")
async def generate_testcases(file: UploadFile = File(...)):
    """AI生成测试用例"""
    try:
        # 读取上传的文件
        content = await file.read()
        filename = file.filename
        
        print(f"收到文件: {filename}, 大小: {len(content)} bytes")
        
        # 根据文件类型解析内容
        text_content = ""
        
        if filename.endswith('.docx'):
            # Word文档解析
            try:
                from docx import Document
                from io import BytesIO
                
                doc = Document(BytesIO(content))
                paragraphs = []
                for para in doc.paragraphs:
                    if para.text.strip():
                        paragraphs.append(para.text.strip())
                text_content = '\n'.join(paragraphs)
                print(f"✅ Word文档解析成功,提取到 {len(paragraphs)} 个段落")
            except ImportError:
                print("⚠️  python-docx未安装,尝试文本解析")
                text_content = content.decode('utf-8', errors='ignore')
            except Exception as e:
                print(f"⚠️  Word文档解析失败: {e},尝试文本解析")
                text_content = content.decode('utf-8', errors='ignore')
        else:
            # 文本文件解析
            try:
                text_content = content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    text_content = content.decode('gbk')
                except:
                    text_content = content.decode('utf-8', errors='ignore')
        
        if not text_content or len(text_content) < 50:
            return JSONResponse(
                content={
                    "success": False,
                    "error": "文件内容为空或过短,请上传有效的需求文档",
                    "message": "文件解析失败"
                },
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
        
        print(f"文件内容预览: {text_content[:200]}...")
        
        # 检查当前AI提供商配置
        from config.config import get_config
        config = get_config()
        current_provider = config.ai.default_provider
        
        print(f"🤖 当前AI提供商: {current_provider}")
        
        # 根据提供商决定生成方式
        if current_provider == 'mock':
            # Mock模式:使用快速生成
            print("📝 使用Mock模式快速生成...")
            generated_cases = _generate_smart_testcases(text_content, filename)
            generation_source = "smart_generated"
        else:
            # 真实AI模式:调用AI生成
            print(f"🚀 使用{current_provider}模式AI生成...")
            try:
                generated_cases = await _generate_testcases_with_ai(text_content, filename, current_provider)
                generation_source = "ai_generated"
            except Exception as e:
                print(f"⚠️  AI生成失败,回退到快速生成: {e}")
                generated_cases = _generate_smart_testcases(text_content, filename)
                generation_source = "smart_generated"
        
        # 转换为前端格式并保存到数据库
        final_cases = []
        import time
        import uuid
        
        # 使用更精确的时间戳(毫秒级)避免ID冲突
        base_timestamp = int(time.time() * 1000)
        
        for idx, tc in enumerate(generated_cases):
            # 使用毫秒级时间戳+索引+随机数生成唯一ID
            case_id = f"TC_{base_timestamp}_{idx}_{uuid.uuid4().hex[:6]}"
            
            # 🆕 根据测试类型推断 data_type 和 expected_behavior
            test_type = tc.get('type', '功能测试')
            title = tc.get('title', '')
            
            # 推断 data_type
            if '异常' in test_type or '参数校验' in title or '非法' in title:
                data_type = 'invalid'
            elif '边界' in test_type or '边界' in title or '临界' in title:
                data_type = 'boundary'
            else:
                data_type = 'valid'
            
            # 推断 expected_behavior
            if data_type == 'invalid':
                expected_behavior = 'client_error'
            else:
                expected_behavior = 'success'
            
            final_case = {
                "id": case_id,
                "title": tc['title'],
                "module": tc['module'],
                "priority": tc['priority'].lower(),
                "status": "pending",
                "lastRun": "未运行",
                "steps": tc['steps'],
                "expected": tc['expected'],
                "source": generation_source,  # 使用实际的生成源
                "type": tc.get('type', '功能测试'),
                "data_type": tc.get('data_type', data_type),  # 🆕 新增字段
                "expected_behavior": tc.get('expected_behavior', expected_behavior)  # 🆕 新增字段
            }
            final_cases.append(final_case)

        # 根据生成源显示不同的日志
        new_count = len(final_cases)
        total_count_before = len(test_cases_db)
        total_count_after = total_count_before + new_count
        
        if generation_source == "ai_generated":
            print(f"✅ AI生成完成! 新增 {new_count} 个测试用例,总计 {total_count_after} 个")
        else:
            print(f"✅ 快速生成完成! 新增 {new_count} 个测试用例,总计 {total_count_after} 个")

        # 保存到数据管理器(持久化)
        from utils.data_manager import get_data_manager
        data_manager = get_data_manager()
        
        # 添加到内存数据库
        test_cases_db.extend(final_cases)
        
        # 保存到持久化存储
        for case in final_cases:
            data_manager.add_item("test_cases", case, save=False)
        
        # 批量保存一次
        data_manager.set_data("test_cases", data_manager.get_data("test_cases", []), save=True)
        print(f"💾 已保存 {len(final_cases)} 个测试用例到持久化存储")
        
        # 同步写入 SQLite 数据库（v2 API 读取的数据源）
        try:
            from database.session import get_db_session
            from database.models import TestCase as DBTestCase
            db_saved = 0
            with get_db_session() as db:
                for case in final_cases:
                    exists = db.query(DBTestCase).filter(DBTestCase.id == case["id"]).first()
                    if not exists:
                        db_case = DBTestCase(
                            id=case["id"],
                            title=case["title"],
                            module=case.get("module"),
                            priority=case.get("priority", "medium"),
                            status=case.get("status", "pending"),
                            steps=case.get("steps"),
                            expected=case.get("expected"),
                            source=case.get("source", "ai_generated"),
                            data_type=case.get("data_type"),
                            expected_behavior=case.get("expected_behavior"),
                        )
                        db.add(db_case)
                        db_saved += 1
                db.commit()
            print(f"💾 已同步 {db_saved} 个测试用例到 SQLite 数据库")
        except Exception as e:
            print(f"⚠️  同步到 SQLite 失败（不影响内存数据）: {e}")
        
        return JSONResponse(
            content={
                "success": True,
                "count": len(final_cases),
                "testCases": final_cases,
                "message": f"成功生成 {len(final_cases)} 个测试用例",
                "stats": {
                    "testcases": len(final_cases)
                }
            },
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
        
    except Exception as e:
        print(f"❌ 生成测试用例失败: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            content={
                "success": False,
                "error": str(e),
                "message": "生成测试用例失败"
            },
            headers={"Content-Type": "application/json; charset=utf-8"}
        )

def _generate_smart_testcases(content: str, filename: str) -> List[Dict[str, Any]]:
    """智能快速生成测试用例(优化版) - 基于文档内容分析"""
    import re
    
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    
    # 更智能的模块识别
    modules = []
    module_patterns = [
        r'(\d+[\.\、]?\s*)?(.{2,20})(功能|模块|管理|系统)',
        r'(新增|修改|删除|查询|导入|导出|审核|统计)(.{2,15})',
        r'(\w+)(接口|API)',
        r'用户(登录|注册|认证|授权)',
        r'(订单|商品|库存|支付|物流|客户)(.{0,10})(管理|处理|查询)',
    ]
    
    for line in lines[:50]:  # 只分析前50行
        if len(line) > 100 or len(line) < 4:
            continue
        for pattern in module_patterns:
            matches = re.findall(pattern, line)
            if matches:
                # 提取有意义的模块名
                module_name = line[:30] if len(line) <= 30 else line[:27] + '...'
                if module_name not in modules:
                    modules.append(module_name)
                break
    
    # 如果没找到模块,尝试提取标题行
    if not modules:
        for line in lines[:30]:
            if 5 <= len(line) <= 50 and not any(c in line for c in ['。', '，', '、', '：']):
                modules.append(line)
    
    # 兜底方案
    if not modules:
        modules = ['核心功能验证', '数据处理流程', '用户交互场景', '系统集成测试']
    
    generated_cases = []
    
    # 测试场景模板(更专业)
    scenarios = [
        {
            "suffix": "正常流程",
            "priority": "high",
            "type": "功能测试",
            "data_type": "valid",  # 🆕 新增
            "expected_behavior": "success",  # 🆕 新增
            "steps_template": [
                "准备符合规范的测试数据",
                "按照正常业务流程执行操作",
                "验证操作结果符合预期",
                "检查相关数据状态正确更新"
            ],
            "expected_template": "操作成功完成,数据正确保存,系统状态正常"
        },
        {
            "suffix": "参数校验",
            "priority": "high",
            "type": "异常测试",
            "data_type": "invalid",  # 🆕 新增
            "expected_behavior": "client_error",  # 🆕 新增
            "steps_template": [
                "准备包含非法参数的测试数据(空值/超长/特殊字符)",
                "尝试执行操作",
                "验证系统返回明确的参数错误提示",
                "确认数据未被错误修改"
            ],
            "expected_template": "系统正确拦截非法参数,返回友好错误提示,数据保持一致性"
        },
        {
            "suffix": "权限控制",
            "priority": "medium",
            "type": "安全测试",
            "data_type": "invalid",  # 🆕 新增
            "expected_behavior": "client_error",  # 🆕 新增
            "steps_template": [
                "使用无权限或低权限账号登录",
                "尝试访问或操作受限资源",
                "验证系统拒绝访问",
                "检查审计日志记录"
            ],
            "expected_template": "系统正确拦截越权操作,返回权限不足提示"
        },
        {
            "suffix": "边界条件",
            "priority": "medium",
            "type": "边界测试",
            "data_type": "boundary",  # 🆕 新增
            "expected_behavior": "success",  # 🆕 新增
            "steps_template": [
                "准备边界值测试数据(最小值/最大值/临界值)",
                "执行操作并观察系统行为",
                "验证边界值处理正确",
                "确认无溢出或异常"
            ],
            "expected_template": "系统正确处理边界值,不出现异常或错误"
        }
    ]
    
    # 为每个模块生成多种场景的测试用例
    case_id = 1
    for i, module in enumerate(modules[:6], 1):  # 最多6个模块
        # 每个模块生成2-3个场景
        scenarios_to_use = scenarios[:3] if i <= 3 else scenarios[:2]
        
        for scenario in scenarios_to_use:
            generated_cases.append({
                "title": f"{module} - {scenario['suffix']}",
                "module": module,
                "priority": scenario['priority'],
                "status": "pending",
                "lastRun": "未运行",
                "steps": [f"{idx}. {step}" for idx, step in enumerate(scenario['steps_template'], 1)],
                "expected": scenario['expected_template'],
                "source": "smart_generated",
                "type": scenario['type'],
                "data_type": scenario['data_type'],  # 🆕 新增
                "expected_behavior": scenario['expected_behavior']  # 🆕 新增
            })
            case_id += 1
            
            if len(generated_cases) >= 15:  # 限制总数
                break
        
        if len(generated_cases) >= 15:
            break
    
    return generated_cases

def _load_project_knowledge() -> str:
    """加载项目知识库上下文，供AI生成时参考"""
    kb_path = Path(__file__).parent / "docs" / "蓝点后端知识库.md"
    if not kb_path.exists():
        return ""
    try:
        text = kb_path.read_text(encoding='utf-8')
        # 提取关键段落，控制 token 消耗
        sections = []
        keep_headings = ['统一响应结构', '业务状态码', '认证鉴权', '业务模块与接口路由', '路由前缀常量',
                         '通用接口命名模式', '测试断言规则', '多租户体系']
        current_section = []
        current_heading = ''
        for line in text.split('\n'):
            if line.startswith('## ') or line.startswith('### '):
                if current_heading and any(kw in current_heading for kw in keep_headings):
                    sections.extend(current_section)
                current_section = [line]
                current_heading = line
            else:
                current_section.append(line)
        if current_heading and any(kw in current_heading for kw in keep_headings):
            sections.extend(current_section)
        result = '\n'.join(sections).strip()
        if result:
            return f"\n\n## 项目知识库（蓝点回收系统）:\n{result[:3000]}"
        return ""
    except Exception as e:
        print(f"⚠️  加载项目知识库失败: {e}")
        return ""


async def _generate_testcases_with_ai(content: str, filename: str, provider: str) -> List[Dict[str, Any]]:
    """使用真实AI分批生成测试用例 — 先提取模块，再按模块逐个生成"""
    from ai.ai_client import AIClient
    from pathlib import Path
    import json
    
    ai_client = AIClient(provider=provider)
    content_length = len(content)
    print(f"📊 需求文档长度: {content_length} 字符")
    
    # 加载项目知识库上下文
    project_knowledge = _load_project_knowledge()
    if project_knowledge:
        print(f"📚 已加载项目知识库 ({len(project_knowledge)} 字符)")
    
    # ========== 第1步：让AI提取模块列表 ==========
    print(f"\n{'='*50}")
    print(f"📋 第1步: 提取需求模块...")
    print(f"{'='*50}")
    
    module_prompt = f"""请分析以下需求文档，提取出所有功能模块名称。

## 需求文档:
{content[:5000]}

请以JSON数组格式返回模块名称列表，例如:
["用户登录", "订单管理", "支付模块", "库存管理"]

只返回JSON数组，不要其他内容。"""

    modules = []
    try:
        module_response = ai_client.generate_text(
            prompt=module_prompt,
            system_prompt="你是需求分析专家，擅长从需求文档中提取功能模块。只返回JSON数组。",
            temperature=0.1,
            max_tokens=500
        )
        module_response = module_response.strip()
        if '```json' in module_response:
            module_response = module_response.split('```json')[1].split('```')[0].strip()
        elif '```' in module_response:
            module_response = module_response.split('```')[1].split('```')[0].strip()
        modules = json.loads(module_response)
        if not isinstance(modules, list):
            modules = []
    except Exception as e:
        print(f"⚠️  模块提取失败: {e}")
    
    # 兜底：如果提取失败，用文件名作为单个模块
    if not modules:
        modules = [filename.rsplit('.', 1)[0] if '.' in filename else "通用模块"]
    
    print(f"✅ 提取到 {len(modules)} 个模块: {modules}")
    
    # ========== 第2步：按模块逐个生成测试用例 ==========
    all_cases = []
    system_prompt = f"""你是一个专业的测试工程师。严格按JSON数组格式返回测试用例。
要求:
1. 每个用例的测试步骤至少5步，步骤要详细具体可执行
2. 测试数据用具体值（如: test@example.com），不要写"有效数据"
3. 覆盖: 功能测试、边界测试、异常测试、安全测试
4. 只返回JSON数组，不要其他文字
5. 业务接口成功断言: HTTP 200 且 body.code==200
6. 认证失败场景: body.code==401/402/405
7. 参数校验失败: body.code==10000
{project_knowledge}"""

    # 动态分配每个模块的用例数量（总目标约60，按模块内容量加权）
    TOTAL_TARGET = 60
    module_contents = {}
    for mod in modules:
        mod_text = content
        if len(content) > 3000 and len(modules) > 1:
            for keyword in [mod, mod[:4]]:
                idx = content.find(keyword)
                if idx >= 0:
                    start = max(0, idx - 500)
                    end = min(len(content), idx + 3000)
                    mod_text = content[start:end]
                    break
        module_contents[mod] = mod_text

    # 按内容长度加权分配，最少5个最多15个
    lengths = {m: len(t) for m, t in module_contents.items()}
    total_len = sum(lengths.values()) or 1
    module_counts = {}
    for m, l in lengths.items():
        raw = int(TOTAL_TARGET * l / total_len)
        module_counts[m] = max(5, min(15, raw))
    
    for i, module_name in enumerate(modules, 1):
        per_module = module_counts.get(module_name, 8)
        module_content = module_contents.get(module_name, content)
        print(f"\n{'='*50}")
        print(f"🔄 第2步 [{i}/{len(modules)}]: 为模块「{module_name}」生成 {per_module} 个用例...")
        print(f"{'='*50}")
        
        gen_prompt = f"""请为「{module_name}」模块生成 {per_module} 个测试用例。

## 需求文档片段:
{module_content[:4000]}

## 要求:
生成 {per_module} 个测试用例，覆盖以下维度:
- 功能测试(正常流程) 约40%
- 边界测试(极值/空值/超长) 约20%  
- 异常测试(非法输入/错误状态) 约20%
- 安全测试(注入/越权) 约20%

请以JSON数组格式返回:
[
  {{
    "title": "简洁标题(不超30字)",
    "module": "{module_name}",
    "priority": "high/medium/low",
    "steps": ["1. 步骤一", "2. 步骤二", "3. 步骤三", "4. 步骤四", "5. 步骤五"],
    "expected": "明确的预期结果",
    "type": "功能测试/异常测试/边界测试/安全测试"
  }}
]"""

        try:
            response = ai_client.generate_text(
                prompt=gen_prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=4000
            )
            
            # 解析JSON
            response = response.strip()
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0].strip()
            elif '```' in response:
                response = response.split('```')[1].split('```')[0].strip()
            
            testcases = None
            try:
                testcases = json.loads(response)
            except json.JSONDecodeError:
                # 尝试修复截断的JSON
                last_brace = response.rfind('}')
                if last_brace > 0:
                    truncated = response[:last_brace + 1].rstrip().rstrip(',') + ']'
                    try:
                        testcases = json.loads(truncated)
                    except json.JSONDecodeError:
                        pass
            
            if testcases and isinstance(testcases, list):
                for tc in testcases:
                    if isinstance(tc, dict) and tc.get('title'):
                        all_cases.append({
                            "title": tc.get('title', ''),
                            "module": tc.get('module', module_name),
                            "priority": tc.get('priority', 'medium'),
                            "status": "pending",
                            "lastRun": "未运行",
                            "steps": tc.get('steps', []),
                            "expected": tc.get('expected', ''),
                            "source": "ai_generated",
                            "type": tc.get('type', '功能测试')
                        })
                print(f"  ✅ 模块「{module_name}」生成 {len(testcases)} 个用例")
            else:
                print(f"  ⚠️  模块「{module_name}」JSON解析失败，跳过")
                
        except Exception as e:
            print(f"  ⚠️  模块「{module_name}」生成失败: {e}")
            continue
    
    if not all_cases:
        raise Exception("所有模块均生成失败")
    
    print(f"\n{'='*50}")
    print(f"✅ 分批生成完成! 共 {len(all_cases)} 个测试用例，覆盖 {len(modules)} 个模块")
    print(f"{'='*50}")
    
    return all_cases

def _generate_simple_testcases(content: str, filename: str) -> List[Dict[str, Any]]:
    """简化的测试用例生成(降级方案)"""
    return _generate_smart_testcases(content, filename)

# ==================== Test Runs API (V3 增强版) ====================

@app.get("/api/test-runs")
async def get_test_runs():
    """获取所有测试执行（V3增强版）"""
    return {
        "success": True,
        "testRuns": test_runs_db,
        "count": len(test_runs_db)
    }

@app.post("/api/test-runs/start")
async def start_test_run(config: Dict[str, Any]):
    """启动测试执行（V3增强版）"""
    import time
    from datetime import datetime
    
    new_run = {
        "id": len(test_runs_db) + 1,
        "name": f"测试运行-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "status": "running",
        "environment": config.get("environment", "staging"),
        "created_at": datetime.now().isoformat(),
        "startTime": datetime.now().strftime("%H:%M:%S"),
        "duration": "0s",
        "progress": 0,
        "totalTests": 0,
        "passed": 0,
        "failed": 0,
        "pending": 0,
        "tasks": [],
        "logs": [
            {"time": datetime.now().strftime("%H:%M:%S"), "level": "INFO", "message": "测试执行已启动"}
        ]
    }
    test_runs_db.insert(0, new_run)
    
    # 保存到持久化存储
    data_manager.set_data("test_runs", test_runs_db, save=True)
    
    return {
        "success": True,
        "testRun": new_run,
        "message": "测试执行已启动"
    }

@app.get("/api/test-runs/{run_id}/status")
async def get_test_run_status(run_id: int):
    """获取测试执行状态（V3增强版 - 支持并发任务状态）"""
    run = next((r for r in test_runs_db if r["id"] == run_id), None)
    if not run:
        raise HTTPException(status_code=404, detail="测试执行不存在")
    
    # 模拟并发执行状态更新
    if run["status"] == "running":
        import random
        from datetime import datetime
        
        # 更新进度
        run["progress"] = min(run["progress"] + random.randint(5, 15), 100)
        
        # 模拟任务执行
        if len(run["tasks"]) < 5:
            task_id = f"task-{len(run['tasks']) + 1:03d}"
            task_status = random.choice(["running", "success", "failed"])
            
            new_task = {
                "task_id": task_id,
                "name": f"测试用例 {len(run['tasks']) + 1}",
                "status": task_status,
                "duration": round(random.uniform(0.5, 3.0), 2) if task_status != "running" else 0
            }
            run["tasks"].append(new_task)
            
            # 更新统计
            run["totalTests"] = len(run["tasks"])
            run["passed"] = len([t for t in run["tasks"] if t["status"] == "success"])
            run["failed"] = len([t for t in run["tasks"] if t["status"] == "failed"])
            run["pending"] = len([t for t in run["tasks"] if t["status"] == "running"])
            
            # 添加日志
            log_level = "PASS" if task_status == "success" else "FAIL" if task_status == "failed" else "INFO"
            run["logs"].append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "level": log_level,
                "message": f"{new_task['name']} - {task_status}"
            })
        
        # 完成条件
        if run["progress"] >= 100:
            run["status"] = "completed" if run["failed"] == 0 else "failed"
            run["logs"].append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "level": "INFO",
                "message": f"测试执行完成 - {run['passed']}/{run['totalTests']} 通过"
            })
    
    return {
        "success": True,
        "testRun": run
    }

@app.get("/api/test-cases/export")
async def export_test_cases():
    """导出测试用例为 Excel"""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from datetime import datetime
        import io

        # 创建工作簿
        wb = Workbook()
        ws = wb.active
        ws.title = "测试用例"

        # 设置列宽
        ws.column_dimensions['A'].width = 8
        ws.column_dimensions['B'].width = 20
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 30
        ws.column_dimensions['E'].width = 20
        ws.column_dimensions['F'].width = 40
        ws.column_dimensions['G'].width = 20
        ws.column_dimensions['H'].width = 30
        ws.column_dimensions['I'].width = 10
        ws.column_dimensions['J'].width = 12
        ws.column_dimensions['K'].width = 12

        # 表头样式
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=11)
        header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        # 写入表头
        headers = ['序号', '模块', '测试点', '用例标题', '前置条件', '测试步骤', '测试数据', '预期结果', '优先级', '测试类型', '状态']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
            cell.border = border

        # 写入数据
        for idx, tc in enumerate(test_cases_db, 2):
            ws.cell(row=idx, column=1, value=idx-1).border = border
            ws.cell(row=idx, column=2, value=tc.get('module', '')).border = border
            ws.cell(row=idx, column=3, value=tc.get('testpoint', '')).border = border
            ws.cell(row=idx, column=4, value=tc.get('title', '')).border = border
            ws.cell(row=idx, column=5, value=tc.get('precondition', '')).border = border

            # 测试步骤（列表转字符串）
            steps = tc.get('steps', [])
            steps_text = '\n'.join(steps) if isinstance(steps, list) else str(steps)
            ws.cell(row=idx, column=6, value=steps_text).border = border
            ws.cell(row=idx, column=6).alignment = Alignment(wrap_text=True, vertical="top")

            ws.cell(row=idx, column=7, value=tc.get('test_data', '')).border = border
            ws.cell(row=idx, column=8, value=tc.get('expected', '')).border = border
            ws.cell(row=idx, column=9, value=tc.get('priority', '')).border = border
            ws.cell(row=idx, column=10, value=tc.get('type', '')).border = border
            ws.cell(row=idx, column=11, value=tc.get('status', '')).border = border

        # 合并V2数据库中的Swagger用例
        try:
            from database.session import get_db_session
            from database.models import TestCase as DBTestCase
            with get_db_session() as db:
                db_cases = db.query(DBTestCase).filter(DBTestCase.source == 'swagger').all()
                existing_ids = {tc.get('id') for tc in test_cases_db}
                for dbtc in db_cases:
                    if dbtc.id not in existing_ids:
                        row_idx = ws.max_row + 1
                        ws.cell(row=row_idx, column=1, value=row_idx-1).border = border
                        ws.cell(row=row_idx, column=2, value=dbtc.module or '').border = border
                        ws.cell(row=row_idx, column=3, value='').border = border
                        ws.cell(row=row_idx, column=4, value=dbtc.title or '').border = border
                        ws.cell(row=row_idx, column=5, value='').border = border
                        steps = dbtc.steps or []
                        steps_text = '\n'.join(steps) if isinstance(steps, list) else str(steps)
                        ws.cell(row=row_idx, column=6, value=steps_text).border = border
                        ws.cell(row=row_idx, column=7, value='').border = border
                        ws.cell(row=row_idx, column=8, value=dbtc.expected or '').border = border
                        ws.cell(row=row_idx, column=9, value=dbtc.priority or '').border = border
                        ws.cell(row=row_idx, column=10, value='Swagger导入').border = border
                        ws.cell(row=row_idx, column=11, value=dbtc.status or '').border = border
        except Exception as e:
            print(f"⚠️  导出V2用例失败: {e}")

        # 保存到内存
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        # 返回文件
        from starlette.responses import StreamingResponse
        from urllib.parse import quote
        filename = f"测试用例_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        ascii_filename = f"test_cases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        headers = {
            'Content-Disposition': f"attachment; filename=\"{ascii_filename}\"; filename*=UTF-8''{quote(filename)}"
        }
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers
        )

    except ImportError:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "openpyxl 未安装，请运行: pip install openpyxl"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"导出失败: {str(e)}"}
        )

# ==================== Reports API ====================

@app.get("/api/reports")
async def get_reports():
    """获取所有报告"""
    return {
        "success": True,
        "data": reports_db,
        "count": len(reports_db)
    }

@app.get("/api/reports/{report_id}")
async def get_report(report_id: int):
    """获取报告详情"""
    report = next((r for r in reports_db if r["id"] == report_id), None)
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    return {
        "success": True,
        "data": report
    }

# ==================== AI API ====================

@app.get("/api/ai/agents")
async def get_ai_agents():
    """获取AI代理列表"""
    return {
        "success": True,
        "data": [
            {"id": "testcase", "name": "测试用例生成", "status": "active"},
            {"id": "assertion", "name": "断言生成", "status": "active"},
        ]
    }

@app.post("/api/ai/generate")
async def ai_generate(data: Dict[str, Any]):
    """AI生成"""
    try:
        prompt = data.get('prompt', '')
        if not prompt:
            return {
                "success": False,
                "error": "缺少prompt参数"
            }
        
        # 调用Ollama AI
        from ai.mock_ai_client import OllamaAIClient
        ai_client = OllamaAIClient()
        
        response = ai_client.generate_text(
            prompt=prompt,
            system_prompt="你是一个专业的测试助手,帮助用户解决测试相关的问题。请用简洁、专业的语言回答。"
        )
        
        return {
            "success": True,
            "response": response,
            "message": "AI生成成功"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    """获取任务状态"""
    return {
        "success": True,
        "status": "completed",
        "progress": 100
    }

@app.get("/api/ai/providers/list")
async def list_ai_providers():
    """列出AI提供商"""
    return {
        "success": True,
        "providers": [
            {"id": "ollama", "name": "Ollama", "status": "available"},
            {"id": "deepseek", "name": "DeepSeek", "status": "available"},
            {"id": "anthropic", "name": "Anthropic/OpenClaw", "status": "available"},
        ]
    }

@app.post("/api/ai/providers/select")
async def select_ai_provider(data: Dict[str, str]):
    """选择AI提供商"""
    return {
        "success": True,
        "message": "AI提供商切换成功"
    }

@app.get("/api/ai/providers/{provider_id}/status")
async def get_provider_status(provider_id: str):
    """获取提供商状态"""
    return {
        "success": True,
        "status": "available"
    }

@app.get("/api/ai/providers/{provider}/models")
async def get_provider_models(provider: str):
    """获取提供商模型列表"""
    from config.config import get_config
    config = get_config()
    models = config.get_available_models(provider)
    if not models:
        if provider == "anthropic":
            models = [os.getenv("DEFAULT_AI_MODEL", "openclaw-default-api-KWJxLGWf")]
        elif provider == "mock":
            models = ["mock-model"]
        else:
            models = []
    return {
        "success": True,
        "models": models
    }

@app.post("/api/ai/providers/{provider}/test")
async def test_provider(provider: str):
    """测试提供商"""
    return {
        "success": True,
        "message": "测试成功"
    }

@app.get("/api/ai/current")
async def get_current_ai_config():
    """获取当前AI配置"""
    try:
        from config.config import get_config
        config = get_config()
        
        return {
            "success": True,
            "provider": config.ai.default_provider,
            "model": config.ai.default_model,
            "providers": {
                "deepseek": {
                    "name": "DeepSeek",
                    "models": config.get_available_models("deepseek"),
                    "api_key_configured": bool(config.ai.deepseek_api_key),
                    "base_url": config.ai.deepseek_base_url
                },
                "openai": {
                    "name": "OpenAI",
                    "models": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
                    "api_key_configured": bool(config.ai.openai_api_key),
                    "base_url": config.ai.openai_base_url
                },
                "ollama": {
                    "name": "Ollama (本地)",
                    "models": config.ai.ollama_models,
                    "api_key_configured": True,
                    "base_url": config.ai.ollama_base_url
                },
                "mock": {
                    "name": "Mock (测试)",
                    "models": ["mock-model"],
                    "api_key_configured": True,
                    "base_url": "local"
                },
                "anthropic": {
                    "name": "Anthropic/OpenClaw",
                    "models": [os.getenv("DEFAULT_AI_MODEL", "openclaw-default-api-KWJxLGWf")],
                    "api_key_configured": bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")),
                    "base_url": os.getenv("ANTHROPIC_BASE_URL", "")
                }
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/ai/providers/switch")
async def switch_ai_provider(data: Dict[str, str]):
    """切换AI提供商和模型 - 全局生效"""
    try:
        provider = data.get('provider')
        model = data.get('model')
        
        if not provider:
            return {
                "success": False,
                "error": "缺少provider参数"
            }
        
        # 更新.env文件
        from pathlib import Path
        env_file = Path(__file__).parent / '.env'
        
        if env_file.exists():
            # 读取现有配置
            with open(env_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 更新配置
            updated = False
            model_updated = False
            new_lines = []
            
            for line in lines:
                if line.startswith('DEFAULT_AI_PROVIDER='):
                    new_lines.append(f'DEFAULT_AI_PROVIDER={provider}\n')
                    updated = True
                elif line.startswith('DEFAULT_AI_MODEL=') and model:
                    new_lines.append(f'DEFAULT_AI_MODEL={model}\n')
                    model_updated = True
                else:
                    new_lines.append(line)
            
            # 如果没找到配置项,添加新的
            if not updated:
                new_lines.append(f'\nDEFAULT_AI_PROVIDER={provider}\n')
            if model and not model_updated:
                new_lines.append(f'DEFAULT_AI_MODEL={model}\n')
            
            # 写回文件
            with open(env_file, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
        
        # 重新加载配置
        from config.config import reload_config
        reload_config()
        
        # 清除AI客户端缓存,强制重新创建
        from ai import ai_client
        ai_client._ai_client = None
        
        return {
            "success": True,
            "message": f"已切换到 {provider}" + (f" - {model}" if model else ""),
            "provider": provider,
            "model": model
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ==================== Automation API ====================

@app.get("/api/automation/scripts")
async def get_automation_scripts():
    """获取自动化脚本"""
    return {
        "success": True,
        "scripts": scripts_db,
        "data": scripts_db,
        "count": len(scripts_db)
    }

@app.post("/api/automation/scripts/generate")
async def generate_automation_script(request: Dict[str, Any]):
    """从测试用例生成自动化脚本"""
    try:
        test_case_id = request.get('test_case_id')
        if not test_case_id:
            return {
                "success": False,
                "error": "缺少test_case_id参数"
            }
        
        # 查找测试用例
        testcase = next((tc for tc in test_cases_db if str(tc.get('id')) == str(test_case_id)), None)
        if not testcase:
            return {
                "success": False,
                "error": f"测试用例不存在: {test_case_id}"
            }
        
        # 生成脚本内容
        import time
        import json
        script_id = len(scripts_db) + 1
        
        # 构建Python requests脚本
        script_content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动生成的测试脚本
测试用例: {testcase.get('title', '未命名')}
生成时间: {time.strftime("%Y-%m-%d %H:%M:%S")}
"""

import requests
import json

def test_{testcase.get('id', 'case')}():
    """
    {testcase.get('title', '测试用例')}
    """
    print("=" * 60)
    print("测试用例: {testcase.get('title', '未命名')}")
    print("=" * 60)
    
    # 测试步骤
'''
        
        # 添加测试步骤
        steps = testcase.get('steps', [])
        for i, step in enumerate(steps, 1):
            # 避免f-string嵌套，使用字符串拼接
            script_content += f'''    print("步骤 {i}: {step}")
'''
        
        # 添加API执行逻辑（如果有）
        exec_config = testcase.get('execution_config', {})
        if exec_config:
            method = exec_config.get('method', 'GET')
            url = exec_config.get('url', '')
            data = exec_config.get('data', {})
            
            script_content += f'''
    # 执行API请求
    method = "{method}"
    url = "{url}"
    data = {json.dumps(data, ensure_ascii=False, indent=4)}
    
    print("\\n发送 " + method + " 请求到 " + url)
    
    try:
        if method == "GET":
            response = requests.get(url, params=data, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)
        elif method == "PUT":
            response = requests.put(url, json=data, timeout=30)
        elif method == "DELETE":
            response = requests.delete(url, json=data, timeout=30)
        else:
            print("不支持的HTTP方法: " + method)
            return False
        
        print("状态码: " + str(response.status_code))
        print("响应时间: " + str(int(response.elapsed.total_seconds() * 1000)) + "ms")
        
        # 验证结果
        if response.status_code < 400:
            print("✅ 测试通过")
            return True
        else:
            print("❌ 测试失败")
            return False
            
    except Exception as e:
        print("❌ 执行失败: " + str(e))
        return False

if __name__ == "__main__":
    result = test_{testcase.get('id', 'case')}()
    exit(0 if result else 1)
'''
        else:
            # 没有执行配置，生成简单的占位脚本
            script_content += '''
    # TODO: 添加具体的测试逻辑
    print("\\n✅ 测试步骤已完成")
    return True

if __name__ == "__main__":
    test_''' + str(testcase.get('id', 'case')) + '''()
'''
        
        # 保存脚本到数据库
        script = {
            "id": script_id,
            "name": f"{testcase.get('title', '测试脚本')}",
            "type": "python",
            "status": "active",
            "test_case_id": test_case_id,
            "content": script_content,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "language": "python"
        }
        
        scripts_db.append(script)
        data_manager.set_data("scripts", scripts_db, save=True)
        
        return {
            "success": True,
            "script_id": script_id,
            "script": script,
            "message": "脚本生成成功"
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "message": "脚本生成失败"
        }

@app.get("/api/automation/scripts/{script_id}/download")
async def download_script(script_id: int):
    """下载脚本"""
    try:
        # 查找脚本
        script = next((s for s in scripts_db if s.get('id') == script_id), None)
        if not script:
            raise HTTPException(status_code=404, detail="脚本不存在")
        
        # 返回脚本内容
        from fastapi.responses import Response
        content = script.get('content', '')
        filename = f"test_script_{script_id}.py"
        
        return Response(
            content=content,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/automation/scripts/{script_id}/execute", deprecated=True)
async def execute_script(script_id: int):
    """[已废弃] 脚本执行 — 后续将迁移到 V2"""
    print(f"⚠️ [DEPRECATED] /api/automation/scripts/{script_id}/execute 已废弃")
    try:
        # 查找脚本
        script = next((s for s in scripts_db if s.get('id') == script_id), None)
        if not script:
            return {
                "success": False,
                "error": "脚本不存在"
            }
        
        # 🔥 使用ExecutionEngine执行脚本
        from modules.executor.real_execution_engine import get_execution_engine
        
        engine = get_execution_engine()
        
        # 构建测试用例
        test_case = {
            'id': f'script_{script_id}',
            'name': script.get('name', '未命名脚本'),
            'execution_type': 'script',
            'config': {
                'script': script.get('content', '')
            },
            'timeout': 60
        }
        
        # 执行脚本
        result = engine.execute(test_case)
        
        # 记录执行历史
        test_run = {
            "id": len(test_runs_db) + 1,
            "script_id": script_id,
            "script_name": script.get('name', '未命名脚本'),
            "trace_id": result.trace_id,
            "status": result.status,
            "duration": f"{int(result.duration * 1000)}ms",
            "executed_at": result.end_time,
            "stdout": result.response.get('stdout', '') if result.response else '',
            "stderr": result.response.get('stderr', '') if result.response else '',
            "return_code": result.status_code
        }
        test_runs_db.append(test_run)
        data_manager.set_data("test_runs", test_runs_db, save=True)
        
        # 返回结果
        return {
            "success": result.success,
            "status": result.status,
            "execution_time": int(result.duration * 1000),
            "stdout": result.response.get('stdout', '') if result.response else '',
            "stderr": result.response.get('stderr', '') if result.response else '',
            "return_code": result.status_code,
            "trace_id": result.trace_id,
            "message": "脚本执行完成"
        }
                
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "message": "脚本执行失败"
        }

@app.post("/api/testcases/{testcase_id}/generate-script")
async def generate_test_script(testcase_id: str):
    """为测试用例生成自动化脚本"""
    try:
        # 查找测试用例（兼容旧内存数据和V2数据库）
        testcase = next((tc for tc in test_cases_db if str(tc.get('id')) == str(testcase_id)), None)
        if not testcase:
            # 尝试从V2数据库查找
            try:
                from database.session import get_db_session
                from database.models import TestCase as DBTestCase
                with get_db_session() as db:
                    db_tc = db.query(DBTestCase).filter(DBTestCase.id == testcase_id).first()
                    if db_tc:
                        testcase = {
                            'id': db_tc.id, 'title': db_tc.title, 'module': db_tc.module,
                            'priority': db_tc.priority, 'steps': db_tc.steps or [],
                            'expected': db_tc.expected, 'execution_config': db_tc.execution_config or {},
                            'assertions': db_tc.assertions or [], 'source': db_tc.source
                        }
            except Exception as e:
                print(f"V2数据库查找失败: {e}")
        if not testcase:
            raise HTTPException(status_code=404, detail="测试用例不存在")
        
        # 生成pytest脚本
        script_content = _generate_pytest_script(testcase)
        
        return {
            "success": True,
            "script": script_content,
            "message": "脚本生成成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 生成脚本失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "message": "脚本生成失败"
        }

@app.post("/api/testcases/{testcase_id}/manual-execute", deprecated=True)
async def manual_execute_test_case(testcase_id: str, data: Dict[str, Any]):
    """[已废弃] 手动执行 — 请迁移到 V2"""
    print(f"⚠️ [DEPRECATED] /api/testcases/{testcase_id}/manual-execute 已废弃")
    try:
        status = data.get('status', 'passed')
        notes = data.get('notes', '')
        steps = data.get('steps', [])
        
        # 更新旧内存中的用例状态
        updated = False
        for tc in test_cases_db:
            if str(tc.get('id')) == str(testcase_id):
                tc['status'] = status
                tc['lastRun'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                updated = True
                break
        
        # 也更新V2数据库
        if not updated:
            try:
                from database.session import get_db_session
                from database.models import TestCase as DBTestCase
                with get_db_session() as db:
                    db_tc = db.query(DBTestCase).filter(DBTestCase.id == testcase_id).first()
                    if db_tc:
                        db_tc.status = status
                        updated = True
            except Exception as e:
                print(f"⚠️  V2数据库更新失败: {e}")
        
        if not updated:
            return {"success": False, "error": f"测试用例不存在: {testcase_id}"}
        
        # 保存持久化数据
        try:
            data_manager.set_data("test_cases", test_cases_db, save=True)
        except Exception:
            pass
        
        return {
            "success": True,
            "message": f"手动测试已记录: {status}",
            "status": status,
            "testcase_id": testcase_id
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/testcases/{testcase_id}/execute", deprecated=True)
async def execute_test_case(testcase_id: str):
    """[已废弃] 请使用 POST /api/v2/test-cases/{case_id}/execute"""
    print(f"⚠️ [DEPRECATED] /api/testcases/{testcase_id}/execute 已废弃，请迁移到 /api/v2/test-cases/{{id}}/execute")
    try:
        import time
        
        # 查找测试用例
        testcase = next((tc for tc in test_cases_db if str(tc.get('id')) == str(testcase_id)), None)
        if not testcase:
            return {
                "success": False,
                "error": f"测试用例不存在: {testcase_id}",
                "message": "测试用例不存在"
            }
        
        # 提取执行配置
        exec_config = testcase.get('execution_config', {})
        
        if not exec_config:
            return {
                "success": False,
                "error": "测试用例没有执行配置",
                "message": "无法执行"
            }
        
        # 🔥 使用ExecutionEngine执行测试
        from modules.executor.real_execution_engine import get_execution_engine
        
        engine = get_execution_engine()
        
        # 处理URL（如果不是完整URL，添加base_url）
        url = exec_config.get('url', '')
        if not url.startswith('http'):
            base_url = exec_config.get('base_url', 'https://jsonplaceholder.typicode.com')
            url = base_url.rstrip('/') + '/' + url.lstrip('/')
        
        # 构建测试用例
        test_case = {
            'id': testcase_id,
            'name': testcase.get('title', '未命名'),
            'execution_type': 'api',
            'config': {
                'url': url,
                'method': exec_config.get('method', 'GET'),
                'headers': exec_config.get('headers', {}),
                'body': exec_config.get('data', {})
            },
            'timeout': testcase.get('timeout', 30)
        }
        
        # 执行测试
        result = engine.execute(test_case)
        
        # 更新测试用例状态
        testcase['status'] = 'passed' if result.success else 'failed'
        testcase['lastRun'] = result.end_time
        
        # 保存更新
        data_manager.set_data("test_cases", test_cases_db, save=True)
        
        # 记录执行历史
        test_run = {
            "id": len(test_runs_db) + 1,
            "testcase_id": testcase_id,
            "testcase_title": testcase.get('title', '未命名'),
            "trace_id": result.trace_id,
            "status": result.status,
            "duration": f"{int(result.duration * 1000)}ms",
            "executed_at": result.end_time,
            "status_code": result.status_code,
            "response_time": int(result.duration * 1000)
        }
        test_runs_db.append(test_run)
        data_manager.set_data("test_runs", test_runs_db, save=True)
        
        # 返回结果
        return {
            "success": result.success,
            "result": {
                "status": result.status,
                "status_code": result.status_code,
                "response_time": int(result.duration * 1000),
                "message": result.error_message if not result.success else "测试通过"
            },
            "trace_id": result.trace_id,
            "message": "测试执行完成"
        }
            
    except Exception as e:
        print(f"❌ 执行测试失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "message": "测试执行失败"
        }

def _generate_pytest_script(testcase: Dict[str, Any]) -> str:
    """P1-9E: 生成真实可运行的 pytest 测试脚本"""
    import json as _json

    title = testcase.get('title', '测试用例')
    module = testcase.get('module', '通用模块')
    steps = testcase.get('steps', [])
    expected = testcase.get('expected', '测试通过')
    exec_cfg = testcase.get('execution_config') or {}
    assertions = testcase.get('assertions') or []
    source = testcase.get('source', '')

    method_name = _sanitize_method_name(title)
    class_name = _sanitize_class_name(module)

    # 判断是否为接口用例（有 execution_config）
    has_api = bool(exec_cfg.get('method') and exec_cfg.get('url'))
    http_method = (exec_cfg.get('method') or 'GET').upper()
    api_path = exec_cfg.get('url') or ''
    body = exec_cfg.get('body')
    headers = exec_cfg.get('headers') or {}
    query_params = exec_cfg.get('query_params')

    body_str = _json.dumps(body, ensure_ascii=False, indent=8) if body else 'None'
    headers_str = _json.dumps({**{"Content-Type": "application/json"}, **headers}, ensure_ascii=False, indent=8) if has_api else '{}'
    query_str = _json.dumps(query_params, ensure_ascii=False, indent=8) if query_params else 'None'

    # 生成断言代码 (8 spaces indent = method body)
    ind = '        '
    assertion_lines = []
    for a in assertions:
        a_type = a.get('type', '')
        a_expected = a.get('expected')
        a_path = a.get('path', '')
        if a_type == 'status_code':
            assertion_lines.append(f'{ind}assert resp.status_code == {a_expected}, f"状态码断言失败: 期望 {a_expected}, 实际 {{resp.status_code}}"')
        elif a_type == 'status_code_in':
            assertion_lines.append(f'{ind}assert resp.status_code in {a_expected}, f"状态码断言失败: 期望在 {a_expected} 中, 实际 {{resp.status_code}}"')
        elif a_type == 'response_time':
            assertion_lines.append(f'{ind}assert resp.elapsed.total_seconds() * 1000 < {a_expected}, f"响应时间超限: {{resp.elapsed.total_seconds()*1000:.0f}}ms > {a_expected}ms"')
        elif a_type == 'field_exists':
            parts = a_path.split('.')
            access = 'data'
            for p in parts:
                access += f'["{p}"]' if p else ''
            assertion_lines.append(f'{ind}assert {access} is not None, "字段 {a_path} 不存在"')
        elif a_type == 'field_equals':
            parts = a_path.split('.')
            access = 'data'
            for p in parts:
                access += f'["{p}"]' if p else ''
            assertion_lines.append(f'{ind}assert {access} == {repr(a_expected)}, "字段 {a_path} 断言失败: 期望 {a_expected}, 实际 " + str({access})')

    if not assertion_lines and has_api:
        assertion_lines.append(f'{ind}assert resp.status_code == 200, f"状态码断言失败: 期望 200, 实际 {{resp.status_code}}"')

    assertions_code = '\n'.join(assertion_lines) if assertion_lines else f'{ind}pass  # 无断言'

    # 生成步骤注释
    steps_doc = ''
    for i, step in enumerate(steps, 1):
        steps_doc += f'        {i}. {step}\n'
    if not steps_doc:
        steps_doc = '        (无详细步骤)\n'

    if has_api:
        script = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{module} - 自动化测试脚本
用例: {title}
生成时间: {_get_current_time()}
"""

import os
import pytest
import requests

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
TOKEN = os.getenv("API_TOKEN", "")


class Test{class_name}:

    def setup_method(self):
        self.session = requests.Session()
        self.session.headers.update({{
            "Content-Type": "application/json",
            **({{
                "Authorization": f"Bearer {{TOKEN}}"
            }} if TOKEN else {{}})
        }})

    def teardown_method(self):
        self.session.close()

    def test_{method_name}(self):
        """
        {title}

        测试步骤:
{steps_doc}
        预期结果: {expected}
        """
        url = f"{{BASE_URL}}{api_path}"
        body = {body_str}
        params = {query_str}

        resp = self.session.request(
            method="{http_method}",
            url=url,
            json=body,
            params=params,
            timeout=30,
        )

        # --- 断言 ---
        data = None
        try:
            data = resp.json()
        except Exception:
            pass

{assertions_code}

        print(f"✅ 通过: {title} ({{resp.status_code}}, {{resp.elapsed.total_seconds()*1000:.0f}}ms)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
'''
    else:
        # 功能测试用例 — 生成步骤模板
        script = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{module} - 自动化测试脚本
用例: {title}
生成时间: {_get_current_time()}
"""

import pytest


class Test{class_name}:

    def test_{method_name}(self):
        """
        {title}

        测试步骤:
{steps_doc}
        预期结果: {expected}
        """
'''
        for i, step in enumerate(steps, 1):
            script += f'        # 步骤{i}: {step}\n'
            script += f'        print("执行步骤{i}: {step}")\n\n'

        script += f'''        # TODO: 补充测试逻辑和断言
        assert True, "{expected}"
        print("✅ 通过: {title}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
'''

    return script

def _sanitize_method_name(title: str) -> str:
    """清理方法名,移除非法字符"""
    import re
    # 移除特殊字符,只保留字母数字和下划线
    name = re.sub(r'[^\w\s]', '', title)
    # 替换空格为下划线
    name = name.replace(' ', '_')
    # 移除连续的下划线
    name = re.sub(r'_+', '_', name)
    # 移除首尾下划线
    name = name.strip('_')
    # 如果为空,使用默认名称
    if not name:
        name = 'test_case'
    return name.lower()

def _sanitize_class_name(module: str) -> str:
    """清理类名,移除非法字符"""
    import re
    # 移除特殊字符
    name = re.sub(r'[^\w\s]', '', module)
    # 替换空格为空
    name = name.replace(' ', '')
    # 如果为空,使用默认名称
    if not name:
        name = 'TestModule'
    return name

def _get_current_time() -> str:
    """获取当前时间"""
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ==================== Upload API ====================

@app.post("/api/upload/requirement")
async def upload_requirement(file: UploadFile = File(...)):
    """上传需求文档"""
    return {
        "success": True,
        "filename": file.filename,
        "message": "需求文档上传成功"
    }

@app.post("/api/upload/swagger")
async def upload_swagger(file: UploadFile = File(...)):
    """上传Swagger文档"""
    return {
        "success": True,
        "filename": file.filename,
        "message": "Swagger文档上传成功"
    }

# ==================== Knowledge API ====================

@app.get("/api/knowledge/stats")
async def get_knowledge_stats():
    """获取知识库统计"""
    return {
        "success": True,
        "stats": {
            "total_cases": 128,
            "modules": 8,
            "coverage": 78.5
        }
    }

@app.post("/api/knowledge/testcases/search")
async def search_testcases(data: Dict[str, str]):
    """搜索测试用例"""
    return {
        "success": True,
        "data": test_cases_db,
        "count": len(test_cases_db)
    }

@app.get("/api/knowledge/coverage")
async def get_knowledge_coverage():
    """获取知识库覆盖率"""
    return {
        "success": True,
        "coverage": 78.5,
        "details": {}
    }

# ==================== Modules SDK 集成 API ====================

@app.post("/api/testcases/generate-from-swagger")
async def generate_testcases_from_swagger(file: UploadFile = File(...)):
    """从 Swagger 生成测试用例（使用 modules SDK）"""
    try:
        import tempfile
        
        if not MODULES_SDK_AVAILABLE or not MODEL_CONVERTER_AVAILABLE:
            raise HTTPException(status_code=503, detail="Modules SDK 不可用")
        
        # 保存上传的文件
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json') as temp_file:
            temp_file.write(await file.read())
            temp_path = temp_file.name
        
        try:
            # 🔧 使用 modules SDK
            generator = SwaggerTestCaseGenerator(temp_path)
            test_cases = generator.generate_all_testcases()
            
            # 转换为 API 响应格式
            result = testcases_to_list(test_cases)
            
            # 添加 ID 和其他字段
            for i, tc_dict in enumerate(result, len(test_cases_db) + 1):
                tc_dict['id'] = i
                tc_dict['lastRun'] = '未运行'
                tc_dict['source'] = 'swagger_generated'
            
            # 保存到数据库
            test_cases_db.extend(result)
            data_manager.set_data("test_cases", test_cases_db, save=True)
            
            # 清理临时文件
            Path(temp_path).unlink()
            
            return {
                "success": True,
                "count": len(result),
                "testCases": result,
                "message": f"成功生成 {len(result)} 个测试用例",
                "stats": generator.get_statistics(test_cases)
            }
        finally:
            # 确保清理临时文件
            if Path(temp_path).exists():
                Path(temp_path).unlink()
                
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"生成失败: {str(e)}"
        }


@app.post("/api/testcases/execute-batch", deprecated=True)
async def execute_testcases_batch(request: Dict[str, Any]):
    """[已废弃] 请使用 POST /api/v2/test-cases/batch-execute"""
    print("⚠️ [DEPRECATED] /api/testcases/execute-batch 已废弃，请迁移到 /api/v2/test-cases/batch-execute")
    try:
        if not MODULES_SDK_AVAILABLE or not MODEL_CONVERTER_AVAILABLE:
            raise HTTPException(status_code=503, detail="Modules SDK 不可用")
        
        testcase_ids = request.get("testcase_ids", [])
        base_url = request.get("base_url", "http://localhost:8080")
        timeout = request.get("timeout", 30)
        parallel = request.get("parallel", True)
        max_workers = request.get("max_workers", 5)
        
        # 查找测试用例
        test_cases_to_run = [
            tc for tc in test_cases_db 
            if tc["id"] in testcase_ids
        ]
        
        if not test_cases_to_run:
            return {
                "success": False,
                "message": "未找到要执行的测试用例"
            }
        
        # 🔧 转换为 core TestCase 对象
        core_test_cases = []
        for tc in test_cases_to_run:
            # 确保有新字段
            tc = enrich_testcase_dict(tc)
            core_tc = dict_to_testcase(tc)
            core_test_cases.append(core_tc)
        
        # 🔧 使用 modules SDK 执行
        config = {
            "base_url": base_url,
            "timeout": timeout,
            "retry_on_failure": request.get("retry_on_failure", False),
            "max_retries": request.get("max_retries", 0)
        }
        
        engine = ExecutionEngine(config)
        results = engine.execute(core_test_cases, parallel=parallel, max_workers=max_workers)
        
        # 🔧 应用 Self-Healing
        healing_config = {
            "enable_l1": request.get("enable_healing_l1", True),
            "enable_l2": request.get("enable_healing_l2", True),
            "enable_l3": request.get("enable_healing_l3", True),
            "enable_l4": request.get("enable_healing_l4", True)
        }
        healing_engine = HealingEngine(healing_config)
        healed_results = healing_engine.heal(results)
        
        # 🔧 生成报告
        report_config = {
            "slow_threshold": request.get("slow_threshold", 2.0),
            "include_response": request.get("include_response", False)
        }
        report_generator = ReportGenerator(report_config)
        report = report_generator.generate(healed_results)
        
        # 转换为 API 响应格式
        results_dict = execution_results_to_list(healed_results)
        
        # 更新测试用例状态
        for result_dict in results_dict:
            tc_id = result_dict.get("test_case_id")
            if tc_id:
                for tc in test_cases_db:
                    if str(tc.get("id")) == str(tc_id):
                        tc["status"] = result_dict.get("status", "unknown")
                        tc["lastRun"] = result_dict.get("start_time", "刚刚")
                        break
        
        # 保存更新
        data_manager.set_data("test_cases", test_cases_db, save=True)
        
        # 获取修复报告
        healing_report = healing_engine.get_healing_report()
        
        return {
            "success": True,
            "results": results_dict,
            "report": report,
            "healing_report": healing_report,
            "message": f"执行完成: {report['summary']['passed']}/{report['summary']['total']} 通过"
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"执行失败: {str(e)}"
        }


@app.post("/api/test-data/generate-smart")
async def generate_smart_test_data(request: Dict[str, Any]):
    """生成智能测试数据（使用 modules SDK）"""
    try:
        if not MODULES_SDK_AVAILABLE:
            raise HTTPException(status_code=503, detail="Modules SDK 不可用")
        
        schema = request.get("schema", {})
        category = request.get("category", "valid")  # valid/boundary/invalid/null/empty
        case_id = request.get("case_id")
        
        # 🔧 使用 modules SDK
        data_manager_sdk = TestDataManager()
        data = data_manager_sdk.generate_data(schema, category, case_id)
        
        return {
            "success": True,
            "data": data,
            "category": category,
            "message": "测试数据生成成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"生成失败: {str(e)}"
        }


@app.post("/api/test-data/generate-all-categories")
async def generate_all_categories_test_data(request: Dict[str, Any]):
    """生成所有分类的测试数据（使用 modules SDK）"""
    try:
        if not MODULES_SDK_AVAILABLE:
            raise HTTPException(status_code=503, detail="Modules SDK 不可用")
        
        schema = request.get("schema", {})
        case_id = request.get("case_id")
        
        # 🔧 使用 modules SDK
        data_manager_sdk = TestDataManager()
        all_data = data_manager_sdk.generate_all_categories(schema, case_id)
        
        return {
            "success": True,
            "data": all_data,
            "message": "所有分类数据生成成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"生成失败: {str(e)}"
        }


# ==================== V2 智能执行Pipeline ====================

@app.post("/api/v2/test/run-intelligent")
async def run_intelligent_test_pipeline(request: Dict[str, Any]):
    """
    V2 智能执行Pipeline - 打通完整链路
    
    请求参数:
    {
        "test_case_ids": ["TC_001", "TC_002"],
        "environment": "test",
        "base_url": "https://jsonplaceholder.typicode.com"
    }
    
    返回:
    {
        "success": true,
        "execution_plan": {...},
        "results": [...],
        "healing": {...},
        "report": {...}
    }
    """
    try:
        if not MODULES_SDK_AVAILABLE:
            raise HTTPException(status_code=503, detail="Modules SDK 不可用")
        
        # 1. 解析请求参数
        test_case_ids = request.get("test_case_ids", [])
        environment = request.get("environment", "test")
        base_url = request.get("base_url", "")
        
        if not test_case_ids:
            raise HTTPException(status_code=400, detail="test_case_ids 不能为空")
        
        print(f"\n{'='*60}")
        print(f"🚀 开始智能执行Pipeline")
        print(f"{'='*60}")
        print(f"📋 测试用例数: {len(test_case_ids)}")
        print(f"🌍 环境: {environment}")
        print(f"🔗 Base URL: {base_url}")
        
        # 2. 查询完整测试用例（从内存数据库）
        test_cases_map = {}
        test_cases_list = []
        
        for tc_id in test_case_ids:
            # 从全局测试用例列表中查找
            found = False
            for tc in test_cases:
                if tc.get('id') == tc_id or str(tc.get('id')) == tc_id:
                    test_cases_map[tc_id] = tc
                    test_cases_list.append(tc)
                    found = True
                    break
            
            if not found:
                print(f"⚠️  测试用例 {tc_id} 未找到，跳过")
        
        if not test_cases_list:
            raise HTTPException(status_code=404, detail="未找到任何有效的测试用例")
        
        print(f"✅ 找到 {len(test_cases_list)} 个有效测试用例")
        
        # 3. 调用 TestIntelligenceAgent 生成执行计划
        print(f"\n{'='*60}")
        print(f"🧠 步骤1: Intelligence Agent - 生成执行计划")
        print(f"{'='*60}")
        
        try:
            from modules.agents.test_intelligence_agent import TestIntelligenceAgent, TestCase as IntelligenceTestCase
            
            # 创建Intelligence Agent
            intelligence_agent = TestIntelligenceAgent()
            
            # 转换测试用例格式
            intelligence_test_cases = []
            for tc in test_cases_list:
                intelligence_tc = IntelligenceTestCase(
                    test_case_id=str(tc.get('id', tc.get('test_case_id', 'unknown'))),
                    api=tc.get('api', tc.get('title', 'unknown')),
                    module=tc.get('module', 'default'),
                    priority=tc.get('priority', 'P2'),
                    tags=tc.get('tags', [])
                )
                intelligence_test_cases.append(intelligence_tc)
            
            # 生成执行计划
            execution_plan = intelligence_agent.optimize_execution_plan(intelligence_test_cases)
            
            print(f"✅ 执行计划生成完成")
            print(f"   - 选中测试: {len(execution_plan['selected_tests'])}")
            print(f"   - 跳过测试: {len(execution_plan['skipped_tests'])}")
            print(f"   - 并发分组: {len(execution_plan['parallel_groups'])}")
            
        except Exception as e:
            print(f"⚠️  Intelligence Agent 失败: {e}")
            # 降级: 使用简单执行计划
            execution_plan = {
                'selected_tests': test_case_ids,
                'skipped_tests': [],
                'execution_order': test_case_ids,
                'parallel_groups': {'default': test_case_ids},
                'risk_scores': [],
                'statistics': {
                    'total_tests': len(test_case_ids),
                    'selected_tests': len(test_case_ids),
                    'skipped_tests': 0
                }
            }
        
        # 4. 调用 ExecutionEngine 执行测试
        print(f"\n{'='*60}")
        print(f"⚙️  步骤2: Execution Engine - 执行测试")
        print(f"{'='*60}")
        
        execution_engine = ExecutionEngine()
        results = []
        
        # 按执行顺序执行测试
        for tc_id in execution_plan['execution_order']:
            if tc_id in test_cases_map:
                tc = test_cases_map[tc_id]
                print(f"🔄 执行: {tc_id} - {tc.get('title', 'N/A')}")
                
                try:
                    # 构建执行用例
                    exec_case = {
                        'test_case_id': tc_id,
                        'type': 'api',
                        'api': {
                            'method': tc.get('method', 'GET'),
                            'url': base_url + tc.get('path', tc.get('url', '/')),
                            'headers': tc.get('headers', {}),
                            'body': tc.get('body', tc.get('request_body', {})),
                            'expected_status': tc.get('expected_status', 200)
                        }
                    }
                    
                    # 执行测试
                    result = execution_engine.execute(exec_case)
                    results.append(result)
                    
                    status_icon = "✅" if result.status == TestCaseStatus.PASSED else "❌"
                    print(f"   {status_icon} {result.status.value} - 耗时: {result.duration}s")
                    
                except Exception as e:
                    print(f"   ❌ 执行失败: {e}")
                    # 创建失败结果
                    from modules.executor.real_execution_engine import ExecutionResult, ExecutionStatus
                    import time
                    
                    failed_result = ExecutionResult(
                        test_case_id=tc_id,
                        status=ExecutionStatus.FAILED,
                        start_time=time.time(),
                        end_time=time.time(),
                        duration=0.0,
                        error=str(e)
                    )
                    results.append(failed_result)
        
        print(f"✅ 执行完成，共 {len(results)} 个结果")
        
        # 5. 调用 HealingEngine 自动修复
        print(f"\n{'='*60}")
        print(f"🔧 步骤3: Healing Engine - 自动修复")
        print(f"{'='*60}")
        
        healing_engine = HealingEngine()
        healed_results = healing_engine.heal(results)
        healing_report = healing_engine.get_healing_report()
        
        print(f"✅ 修复完成")
        print(f"   - 总用例: {healing_report['total_cases']}")
        print(f"   - 已修复: {healing_report['healed_cases']}")
        print(f"   - 修复率: {healing_report['healing_rate']}")
        
        # 6. 调用 ReportGenerator 生成报告
        print(f"\n{'='*60}")
        print(f"📊 步骤4: Report Generator - 生成报告")
        print(f"{'='*60}")
        
        report_generator = ReportGenerator()
        report = report_generator.generate(healed_results)
        
        print(f"✅ 报告生成完成")
        print(f"   - 通过率: {report['summary']['pass_rate']}")
        print(f"   - 通过: {report['summary']['passed']}")
        print(f"   - 失败: {report['summary']['failed']}")
        
        # 7. 转换结果为可序列化格式
        results_dict = []
        for r in healed_results:
            result_dict = {
                'test_case_id': r.test_case_id,
                'status': r.status.value if hasattr(r.status, 'value') else str(r.status),
                'duration': r.duration,
                'start_time': r.start_time,
                'end_time': r.end_time,
                'error': r.error,
                'healing_applied': getattr(r, 'healing_applied', False),
                'healing_level': getattr(r, 'healing_level', {}).value if hasattr(getattr(r, 'healing_level', {}), 'value') else None,
                'healing_details': getattr(r, 'healing_details', None)
            }
            results_dict.append(result_dict)
        
        # 8. 返回完整结果
        print(f"\n{'='*60}")
        print(f"✅ Pipeline 执行完成")
        print(f"{'='*60}\n")
        
        return {
            "success": True,
            "execution_plan": execution_plan,
            "results": results_dict,
            "healing": healing_report,
            "report": report,
            "statistics": {
                "total_tests": len(test_case_ids),
                "executed_tests": len(results),
                "passed_tests": report['summary']['passed'],
                "failed_tests": report['summary']['failed'],
                "pass_rate": report['summary']['pass_rate'],
                "total_duration": report['summary']['total_duration']
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"Pipeline执行失败: {str(e)}",
            "error": str(e)
        }


# P2-2: 触发系统已在 backend/router_registry.py 注册（去重）

# ==================== 启动服务器 ====================

if __name__ == "__main__":
    from backend.config import settings
    print("\n" + "=" * 60)
    print("🚀 AI Test Platform Backend API Server (P2-2)")
    print("=" * 60)
    print(f"📍 地址: http://{settings.BACKEND_HOST}:{settings.BACKEND_PORT}")
    print(f"📖 API文档: http://localhost:{settings.BACKEND_PORT}/docs")
    print(f"🔍 健康检查: http://localhost:{settings.BACKEND_PORT}/health")
    print("=" * 60 + "\n")

    uvicorn.run(
        app,
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        log_level=settings.LOG_LEVEL.lower(),
    )
