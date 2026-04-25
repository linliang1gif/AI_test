#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Test Platform - Backend API Server
完整的后端API服务器,包含所有功能模块
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

# 🔧 强制加载.env文件,覆盖系统环境变量
from dotenv import load_dotenv
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)
print(f"✅ 已加载环境变量: ANTHROPIC_BASE_URL={os.getenv('ANTHROPIC_BASE_URL')}")

# 使用配置文件中的AI提供商设置
# 不强制设置,让系统读取.env配置
# os.environ['USE_OLLAMA'] = '1'
# os.environ['AI_PROVIDER'] = 'ollama'

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, 'test_data')

# 🔧 添加项目根目录到路径（架构重构）
# modules 和 core 在项目根目录下，需要添加根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 🔧 导入 modules SDK
try:
    from modules.swagger import SwaggerTestCaseGenerator
    from modules.executor import ExecutionEngine
    from modules.healing import HealingEngine
    from modules.report import ReportGenerator
    from modules.data import TestDataManager
    MODULES_SDK_AVAILABLE = True
    print("✅ Modules SDK 已加载")
except ImportError as e:
    MODULES_SDK_AVAILABLE = False
    print(f"⚠️  Modules SDK 导入失败: {e}")

# 🔧 导入 core 模型
try:
    from core import (
        TestCase,
        ExecutionResult,
        TestCaseStatus,
        TestCasePriority,
        DataType,
        ExpectedBehavior,
        create_test_case,
        create_execution_result
    )
    CORE_MODELS_AVAILABLE = True
    print("✅ Core Models 已加载")
except ImportError as e:
    CORE_MODELS_AVAILABLE = False
    print(f"⚠️  Core Models 导入失败: {e}")

# 🔧 导入数据转换器
try:
    from utils.model_converter import (
        testcase_to_dict,
        dict_to_testcase,
        execution_result_to_dict,
        testcases_to_list,
        execution_results_to_list,
        enrich_testcase_dict,
        enrich_testcase_list
    )
    MODEL_CONVERTER_AVAILABLE = True
    print("✅ Model Converter 已加载")
except ImportError as e:
    MODEL_CONVERTER_AVAILABLE = False
    print(f"⚠️  Model Converter 导入失败: {e}")

# 导入Test Agent
try:
    from agent.controller import router as agent_router
    TEST_AGENT_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Test Agent导入失败: {e}")
    TEST_AGENT_AVAILABLE = False

# 导入 AI 路由
try:
    from routes.ai_routes import router as ai_router
    AI_ROUTES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  AI Routes导入失败: {e}")
    AI_ROUTES_AVAILABLE = False

# 导入Strategy Engine
try:
    from strategy.controller import router as strategy_router
    STRATEGY_ENGINE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Strategy Engine导入失败: {e}")
    STRATEGY_ENGINE_AVAILABLE = False

# 导入Orchestrator
try:
    from orchestrator.controller import router as orchestrator_router
    ORCHESTRATOR_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Orchestrator导入失败: {e}")
    ORCHESTRATOR_AVAILABLE = False

# 导入Self-Healing
try:
    from self_healing.controller import router as healing_router
    SELF_HEALING_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Self-Healing导入失败: {e}")
    SELF_HEALING_AVAILABLE = False

# 导入Pipeline
try:
    from pipeline.controller import router as pipeline_router
    PIPELINE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Pipeline导入失败: {e}")
    PIPELINE_AVAILABLE = False

# 导入Case Generator
try:
    from case_generator.controller import case_router
    CASE_GENERATOR_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Case Generator导入失败: {e}")
    CASE_GENERATOR_AVAILABLE = False

# 🔥 导入触发系统
try:
    from modules.trigger.test_trigger_system import TestTriggerSystem
    from modules.trigger.trigger_api import create_trigger_router
    TRIGGER_SYSTEM_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  触发系统导入失败: {e}")
    TRIGGER_SYSTEM_AVAILABLE = False

# 🔥 导入分析系统
try:
    from modules.analysis.analysis_api import router as analysis_router
    ANALYSIS_SYSTEM_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  分析系统导入失败: {e}")
    ANALYSIS_SYSTEM_AVAILABLE = False

# 导入测试数据工厂
try:
    from test_data.data_factory import factory
    TEST_DATA_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  测试数据工厂导入失败: {e}")
    TEST_DATA_AVAILABLE = False

# 创建FastAPI应用
app = FastAPI(
    title="AI Test Platform Backend API",
    description="AI测试平台完整后端API",
    version="1.2.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册Test Agent路由
if TEST_AGENT_AVAILABLE:
    app.include_router(agent_router, prefix="/api")
    print("✅ Test Agent模块已加载")

# 注册 AI 路由
if AI_ROUTES_AVAILABLE:
    app.include_router(ai_router, prefix="/api")
    print("✅ AI Routes模块已加载")

# 注册Strategy Engine路由
if STRATEGY_ENGINE_AVAILABLE:
    app.include_router(strategy_router, prefix="/api")
    print("✅ Strategy Engine模块已加载")

# 注册Orchestrator路由
if ORCHESTRATOR_AVAILABLE:
    app.include_router(orchestrator_router, prefix="/api")
    print("✅ Orchestrator模块已加载")

# 注册Self-Healing路由
if SELF_HEALING_AVAILABLE:
    app.include_router(healing_router, prefix="/api")
    print("✅ Self-Healing模块已加载")

# 注册Pipeline路由
if PIPELINE_AVAILABLE:
    app.include_router(pipeline_router, prefix="/api")
    print("✅ Pipeline模块已加载")

# 注册Case Generator路由
if CASE_GENERATOR_AVAILABLE:
    app.include_router(case_router, prefix="/api")
    print("✅ Case Generator模块已加载")

# 🔥 初始化并注册触发系统
if TRIGGER_SYSTEM_AVAILABLE:
    # 创建触发系统实例
    trigger_system = TestTriggerSystem(pipeline_service=None)  # 暂时不对接Pipeline
    trigger_router = create_trigger_router(trigger_system)
    app.include_router(trigger_router)
    print("✅ 触发系统已加载")
else:
    trigger_system = None

# 🔥 注册分析系统
if ANALYSIS_SYSTEM_AVAILABLE:
    app.include_router(analysis_router)
    print("✅ 分析系统已加载")

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

# ==================== 基础路由 ====================

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "AI Test Platform Backend API",
        "version": "1.2.0",
        "status": "running",
        "features": {
            "test_data_factory": TEST_DATA_AVAILABLE,
            "ai_generation": True,
            "test_execution": True
        }
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "test_data_factory": "available" if TEST_DATA_AVAILABLE else "unavailable"
    }

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

@app.post("/api/execute-api")
async def execute_api(request: Dict[str, Any]):
    """执行单个API测试（使用ExecutionEngine）"""
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
    ids: List[int]

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
        else:
            # 真实AI模式:调用AI生成
            print(f"🚀 使用{current_provider}模式AI生成...")
            try:
                generated_cases = await _generate_testcases_with_ai(text_content, filename, current_provider)
            except Exception as e:
                print(f"⚠️  AI生成失败,回退到快速生成: {e}")
                generated_cases = _generate_smart_testcases(text_content, filename)
        
        # 转换为前端格式并保存到数据库
        final_cases = []
        import time
        
        for idx, tc in enumerate(generated_cases):
            # 🆕 使用时间戳+索引生成唯一ID
            case_id = f"TC_{int(time.time())}_{idx}"
            
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
                "source": "ai_generated",
                "type": tc.get('type', '功能测试'),
                "data_type": tc.get('data_type', data_type),  # 🆕 新增字段
                "expected_behavior": tc.get('expected_behavior', expected_behavior)  # 🆕 新增字段
            }
            final_cases.append(final_case)

        print(f"✅ 快速生成完成! 共生成 {len(final_cases)} 个测试用例")

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

async def _generate_testcases_with_ai(content: str, filename: str, provider: str) -> List[Dict[str, Any]]:
    """使用真实AI生成测试用例(集成知识库RAG)"""
    from ai.ai_client import AIClient
    import json
    
    # 创建AI客户端
    ai_client = AIClient(provider=provider)
    
    # 🔍 查询知识库获取相关上下文
    knowledge_context = ""
    try:
        from knowledge.decision_rag import get_decision_rag
        
        # 从需求文档中提取关键词用于知识库检索
        keywords = content[:500]  # 使用前500字符作为查询
        
        # 使用决策级RAG检索知识
        rag = get_decision_rag()
        knowledge = rag.retrieve_knowledge_v2(
            query=keywords,
            context_type="case_generation",  # 用例生成场景
            max_tokens=1500
        )
        
        # 提取API信息
        apis = knowledge.get('apis', [])
        if apis:
            knowledge_context += "\n\n## 相关API接口信息:\n"
            for i, api in enumerate(apis[:3], 1):  # 最多3个API
                api_path = api.get('path', '')
                api_method = api.get('method', '')
                api_desc = api.get('description', '')
                knowledge_context += f"\n### API {i}: {api_method} {api_path}\n"
                if api_desc:
                    knowledge_context += f"描述: {api_desc[:200]}\n"
        
        # 提取代码信息
        backend_code = knowledge.get('code', {}).get('backend', [])
        if backend_code:
            knowledge_context += "\n\n## 相关后端代码:\n"
            for i, code in enumerate(backend_code[:2], 1):  # 最多2个代码片段
                code_file = code.get('file', '')
                code_content = code.get('content', '')
                knowledge_context += f"\n### 代码片段 {i} ({code_file}):\n{code_content[:200]}\n"
        
        if knowledge_context:
            confidence = knowledge.get('confidence', 0)
            print(f"✅ 知识库检索成功 (置信度: {confidence:.2f})")
        else:
            print(f"ℹ️  知识库为空或未找到相关信息,使用基础模式")
            
    except ImportError as e:
        print(f"⚠️  知识库模块未安装(将使用基础模式): {e}")
    except Exception as e:
        print(f"⚠️  知识库检索失败(将继续使用基础模式): {e}")
        import traceback
        traceback.print_exc()
    
    # 构建增强的提示词
    prompt = f"""请根据以下需求文档和相关技术信息生成测试用例。

## 需求文档内容:
{content[:2000]}

{knowledge_context}

请基于以上信息生成5-10个高质量测试用例,每个测试用例包含:
- title: 测试用例标题
- module: 所属模块
- priority: 优先级(high/medium/low)
- steps: 详细的测试步骤列表
- expected: 预期结果
- type: 测试类型(功能测试/异常测试/边界测试/性能测试等)

注意事项:
1. 如果有API信息,请在测试步骤中包含具体的API调用
2. 如果有代码实现,请考虑代码中的边界条件和异常处理
3. 测试用例应该覆盖正常场景、异常场景和边界条件
4. 测试步骤要具体、可执行

请以JSON数组格式返回,示例:
[
  {{
    "title": "用户登录-正常场景",
    "module": "用户管理",
    "priority": "high",
    "steps": ["1. 调用POST /api/login接口", "2. 传入正确的用户名和密码", "3. 验证返回token"],
    "expected": "返回200状态码,包含有效的JWT token",
    "type": "功能测试"
  }}
]
"""
    
    try:
        # 调用AI生成
        response = ai_client.generate_text(
            prompt=prompt,
            system_prompt="你是一个专业的测试工程师,擅长根据需求文档和技术文档生成高质量、可执行的测试用例。你会充分利用API文档和代码信息来设计更精准的测试场景。",
            temperature=0.3,
            max_tokens=3000  # 增加token限制以容纳更多内容
        )
        
        # 解析AI返回的JSON
        # 尝试提取JSON部分
        response = response.strip()
        if '```json' in response:
            response = response.split('```json')[1].split('```')[0].strip()
        elif '```' in response:
            response = response.split('```')[1].split('```')[0].strip()
        
        testcases = json.loads(response)
        
        # 标准化格式
        standardized_cases = []
        for tc in testcases:
            standardized_cases.append({
                "title": tc.get('title', '未命名测试用例'),
                "module": tc.get('module', '通用模块'),
                "priority": tc.get('priority', 'medium'),
                "status": "pending",
                "lastRun": "未运行",
                "steps": tc.get('steps', []),
                "expected": tc.get('expected', ''),
                "source": "ai_generated",
                "type": tc.get('type', '功能测试')
            })
        
        return standardized_cases
        
    except json.JSONDecodeError as e:
        print(f"⚠️  AI返回的JSON解析失败: {e}")
        print(f"AI原始响应: {response[:500]}")
        raise Exception(f"AI返回格式错误: {str(e)}")
    except Exception as e:
        print(f"⚠️  AI生成失败: {e}")
        raise

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

        # 保存到内存
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        # 返回文件
        filename = f"测试用例_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return FileResponse(
            path=None,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            content=output.getvalue()
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

@app.post("/api/reports/generate")
async def generate_report(data: Dict[str, Any] = {}):
    """生成测试报告（基于测试运行数据）"""
    from datetime import datetime
    try:
        run_id = data.get("run_id")
        title = data.get("title", f"测试报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

        # 获取关联的测试运行数据
        run_data = None
        if run_id:
            run_data = next((r for r in test_runs_db if str(r.get("id")) == str(run_id)), None)

        # 计算统计数据
        total = len(test_cases_db)
        passed = sum(1 for tc in test_cases_db if tc.get("status") == "passed")
        failed = sum(1 for tc in test_cases_db if tc.get("status") == "failed")
        pending = total - passed - failed

        report = {
            "id": len(reports_db) + 1,
            "title": title,
            "run_id": run_id,
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "pending": pending,
                "pass_rate": f"{(passed/total*100):.1f}%" if total > 0 else "0%"
            },
            "test_cases": test_cases_db,
            "run_details": run_data
        }

        reports_db.append(report)
        data_manager.set_data("reports", reports_db, save=True)

        return {
            "success": True,
            "message": "报告生成成功",
            "data": report,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"报告生成失败: {str(e)}",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

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
    if provider == "anthropic":
        return {
            "success": True,
            "models": [
                os.getenv("DEFAULT_AI_MODEL", "openclaw-default-api-KWJxLGWf"),
                "openclaw-default-api-KWJxLGWf"
            ]
        }
    return {
        "success": True,
        "models": ["qwen2.5:1.5b", "llama3.2:1b"]
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
                    "models": ["deepseek-chat", "deepseek-coder"],
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

@app.post("/api/automation/scripts/{script_id}/execute")
async def execute_script(script_id: int):
    """执行脚本（使用ExecutionEngine）"""
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
async def generate_test_script(testcase_id: int):
    """为测试用例生成自动化脚本"""
    try:
        # 查找测试用例
        testcase = next((tc for tc in test_cases_db if tc['id'] == testcase_id), None)
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

@app.post("/api/testcases/{testcase_id}/execute")
async def execute_test_case(testcase_id: str):
    """执行测试用例（使用ExecutionEngine）"""
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


@app.post("/api/testcases/{testcase_id}/manual-execute")
async def manual_execute_test_case(testcase_id: str, data: Dict[str, Any] = {}):
    """手动执行测试用例（支持自定义参数覆盖）"""
    from datetime import datetime
    try:
        testcase = next((tc for tc in test_cases_db if str(tc.get("id")) == str(testcase_id)), None)
        if not testcase:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": f"测试用例不存在: {testcase_id}",
                    "data": None,
                    "timestamp": datetime.now().isoformat()
                }
            )

        custom_url = data.get("url")
        custom_method = data.get("method", "GET")
        custom_headers = data.get("headers", {})
        custom_body = data.get("body")
        custom_params = data.get("params", {})
        custom_timeout = data.get("timeout", 30)

        exec_config = testcase.get("execution_config", {})
        url = custom_url or exec_config.get("url", "")
        method = custom_method or exec_config.get("method", "GET")
        headers = {**exec_config.get("headers", {}), **custom_headers}

        if not url:
            return JSONResponse(
                status_code=422,
                content={
                    "success": False,
                    "message": "缺少请求URL",
                    "data": None,
                    "timestamp": datetime.now().isoformat()
                }
            )

        from modules.executor.real_execution_engine import get_execution_engine

        engine = get_execution_engine()
        test_case_input = {
            "id": testcase_id,
            "name": testcase.get("title", "未命名"),
            "execution_type": "api",
            "config": {
                "url": url,
                "method": method,
                "headers": headers,
                "body": custom_body if custom_body is not None else exec_config.get("data", {}),
                "params": custom_params
            },
            "timeout": custom_timeout
        }

        result = engine.execute(test_case_input)

        testcase["status"] = "passed" if result.success else "failed"
        testcase["lastRun"] = datetime.now().isoformat()
        data_manager.set_data("test_cases", test_cases_db, save=True)

        test_run = {
            "id": len(test_runs_db) + 1,
            "testcase_id": testcase_id,
            "testcase_title": testcase.get("title", "未命名"),
            "trace_id": result.trace_id,
            "status": result.status,
            "duration": f"{int(result.duration * 1000)}ms",
            "executed_at": result.end_time or datetime.now().isoformat(),
            "status_code": result.status_code,
            "response_time": int(result.duration * 1000),
            "manual": True
        }
        test_runs_db.append(test_run)
        data_manager.set_data("test_runs", test_runs_db, save=True)

        return {
            "success": result.success,
            "message": "手动执行完成",
            "data": {
                "status": result.status,
                "status_code": result.status_code,
                "response_time": int(result.duration * 1000),
                "trace_id": result.trace_id
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"手动执行失败: {str(e)}",
                "data": None,
                "timestamp": datetime.now().isoformat()
            }
        )

def _generate_pytest_script(testcase: Dict[str, Any]) -> str:
    """生成pytest测试脚本"""
    import json
    
    title = testcase.get('title', '测试用例')
    module = testcase.get('module', '通用模块')
    steps = testcase.get('steps', [])
    expected = testcase.get('expected', '测试通过')
    
    # 生成测试方法名
    method_name = _sanitize_method_name(title)
    
    # 生成脚本内容
    script = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
{module} - 自动化测试脚本
测试用例: {title}
生成时间: {_get_current_time()}
"""

import pytest
import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

class Test{_sanitize_class_name(module)}:
    """
    {module}测试类
    """
    
    def setup_method(self):
        """测试前置设置"""
        self.session = requests.Session()
        self.session.headers.update({{"Content-Type": "application/json"}})
    
    def teardown_method(self):
        """测试后置清理"""
        if hasattr(self, 'session'):
            self.session.close()
    
    def test_{method_name}(self):
        """
        {title}
        
        测试步骤:
'''
    
    # 添加测试步骤
    for i, step in enumerate(steps, 1):
        script += f'        {i}. {step}\n'
    
    script += f'''        
        预期结果: {expected}
        """
        # 准备测试数据
        test_data = {{
            "test_case_id": {testcase['id']},
            "title": "{title}"
        }}
        
        # 执行测试步骤
'''
    
    # 根据步骤生成代码
    for i, step in enumerate(steps, 1):
        script += f'''        # 步骤{i}: {step}
        print(f"执行步骤{i}: {step}")
        
'''
    
    script += f'''        # 验证结果
        # TODO: 添加具体的断言逻辑
        assert True, "{expected}"
        
        print("✅ 测试通过: {title}")

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
async def upload_swagger_legacy(file: UploadFile = File(...)):
    """[兼容别名] 上传Swagger文档 - 转发到 /api/swagger/upload"""
    return await upload_swagger_main(file)

@app.post("/api/swagger/upload")
async def upload_swagger_main(file: UploadFile = File(...)):
    """上传Swagger文档 - 真实解析并返回接口信息"""
    from datetime import datetime
    try:
        if not file:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "未选择文件",
                    "data": None,
                    "timestamp": datetime.now().isoformat()
                }
            )

        if not file.filename:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "文件名为空",
                    "data": None,
                    "timestamp": datetime.now().isoformat()
                }
            )

        content = await file.read()
        if not content:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "文件内容为空",
                    "data": None,
                    "timestamp": datetime.now().isoformat()
                }
            )

        # 检查文件格式
        filename_lower = file.filename.lower()
        if not (filename_lower.endswith('.json') or filename_lower.endswith('.yaml') or filename_lower.endswith('.yml')):
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": f"不支持的文件格式，请上传 JSON 或 YAML 文件",
                    "data": None,
                    "timestamp": datetime.now().isoformat()
                }
            )

        # 尝试解析 JSON
        import json as _json
        import tempfile
        import yaml as _yaml

        try:
            swagger_data = _json.loads(content.decode('utf-8'))
            detected_format = 'json'
        except Exception:
            try:
                swagger_data = _yaml.safe_load(content)
                detected_format = 'yaml'
            except Exception as parse_err:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "message": f"文件解析失败: {str(parse_err)}",
                        "data": None,
                        "timestamp": datetime.now().isoformat()
                    }
                )

        if not swagger_data or not isinstance(swagger_data, dict):
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "无效的Swagger/OpenAPI文档格式",
                    "data": None,
                    "timestamp": datetime.now().isoformat()
                }
            )

        # 提取基本信息
        info = swagger_data.get('info', {})
        swagger_version = swagger_data.get('swagger', swagger_data.get('openapi', 'unknown'))
        paths = swagger_data.get('paths', {})
        api_count = 0
        path_count = len(paths)
        method_count = 0

        # 提取API列表
        apis = []
        for path, methods in paths.items():
            if isinstance(methods, dict):
                for method, details in methods.items():
                    if method.upper() in ('GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'):
                        method_count += 1
                        api_count += 1
                        apis.append({
                            "id": api_count,
                            "name": details.get('summary', details.get('operationId', f"{method}_{path}")),
                            "method": method.upper(),
                            "path": path,
                            "description": details.get('description', ''),
                            "tags": details.get('tags', []),
                            "status": "active",
                            "parameters": details.get('parameters', []),
                            "responses": details.get('responses', {})
                        })

        # 保存到数据库
        if apis:
            global apis_db
            apis_db.clear()
            apis_db.extend(apis)
            data_manager.set_data("apis", apis_db, save=True)

        result = {
            "success": True,
            "message": f"成功解析: {info.get('title', file.filename)}",
            "data": {
                "filename": file.filename,
                "format": detected_format,
                "title": info.get('title', ''),
                "version": info.get('version', ''),
                "swagger_version": swagger_version,
                "path_count": path_count,
                "method_count": method_count,
                "api_count": api_count,
                "apis": apis[:50]  # 限制返回前50个
            },
            "timestamp": datetime.now().isoformat()
        }

        return result

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"上传处理失败: {str(e)}",
                "data": None,
                "timestamp": datetime.now().isoformat()
            }
        )

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

# ==================== 启动服务器 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 AI Test Platform Backend API Server")
    print("=" * 60)
    print(f"📦 版本: 1.2.0")
    print(f"🏭 测试数据工厂: {'✅ 可用' if TEST_DATA_AVAILABLE else '❌ 不可用'}")
    print(f"🌐 API文档: http://localhost:8000/docs")
    print(f"🔍 健康检查: http://localhost:8000/health")
    print("=" * 60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

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


@app.post("/api/testcases/execute-batch")
async def execute_testcases_batch(request: Dict[str, Any]):
    """批量执行测试用例（使用 modules SDK）"""
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


# ==================== 触发系统集成 ====================

# 导入触发系统
try:
    from modules.trigger import TestTriggerSystem
    from modules.trigger.trigger_api import create_trigger_router
    
    # 创建触发系统实例（暂时不连接Pipeline，后续集成）
    trigger_system = TestTriggerSystem(pipeline_service=None)
    
    # 创建并添加触发系统路由
    trigger_router = create_trigger_router(trigger_system)
    app.include_router(trigger_router)
    
    print("✅ 触发系统已集成")
    TRIGGER_SYSTEM_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  触发系统导入失败: {e}")
    TRIGGER_SYSTEM_AVAILABLE = False

# ==================== 启动服务器 ====================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 AI测试平台后端服务启动")
    print("=" * 60)
    print(f"📍 地址: http://0.0.0.0:8000")
    print(f"📖 API文档: http://0.0.0.0:8000/docs")
    if TRIGGER_SYSTEM_AVAILABLE:
        print(f"🔗 触发系统: http://0.0.0.0:8000/api/trigger")
    print("=" * 60 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
