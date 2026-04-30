#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backend API Server - Modules SDK 集成示例
展示如何在 backend_api_server.py 中集成 modules SDK

使用方法：
1. 将这些代码片段复制到 backend_api_server.py 的相应位置
2. 或者直接导入这个模块使用这些函数
"""

import sys
from pathlib import Path
from typing import Dict, Any, List
from fastapi import UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

# ==================== 步骤1：添加导入（放在文件顶部） ====================

# 添加 modules 和 core 到路径
modules_path = Path(__file__).parent.parent / 'modules'
core_path = Path(__file__).parent.parent / 'core'
sys.path.insert(0, str(modules_path))
sys.path.insert(0, str(core_path))

# 导入 modules SDK
from modules.swagger import SwaggerTestCaseGenerator
from modules.executor import ExecutionEngine
from modules.healing import HealingEngine
from modules.report import ReportGenerator
from modules.data import TestDataManager

# 导入 core 模型
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

# 导入数据转换器
from utils.model_converter import (
    testcase_to_dict,
    dict_to_testcase,
    execution_result_to_dict,
    testcases_to_list,
    execution_results_to_list,
    enrich_testcase_dict,
    enrich_testcase_list
)

# ==================== 步骤2：Swagger 解析 API（替换现有实现） ====================

async def parse_swagger_with_modules(data: Dict[str, str]):
    """
    解析 Swagger URL（使用 modules SDK）
    
    替换 backend_api_server.py 中的 @app.post("/api/swagger/parse")
    """
    try:
        url = data.get('url')
        if not url:
            return {"success": False, "message": "缺少URL参数"}
        
        # 🔧 使用 modules SDK
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
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"解析失败: {str(e)}"
        }


async def upload_swagger_with_modules(file: UploadFile = File(...)):
    """
    上传 Swagger 文件（使用 modules SDK）
    
    替换 backend_api_server.py 中的 @app.post("/api/swagger/upload")
    """
    try:
        import json
        import yaml
        import tempfile
        
        # 检查文件
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
        
        # 保存到临时文件
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json') as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name
        
        # 🔧 使用 modules SDK
        generator = SwaggerTestCaseGenerator(temp_path)
        test_cases = generator.generate_all_testcases()
        
        # 转换为 API 响应格式
        apis = generator.export_to_json(test_cases)
        
        # 清理临时文件
        Path(temp_path).unlink()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"成功解析 {len(apis)} 个API",
                "count": len(apis),
                "apis": apis
            }
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"上传失败: {str(e)}"
            }
        )


# ==================== 步骤3：测试用例生成 API ====================

async def generate_testcases_from_swagger(file: UploadFile = File(...), test_cases_db: List = None, data_manager = None):
    """
    从 Swagger 生成测试用例（使用 modules SDK）
    
    新增 API 端点: @app.post("/api/testcases/generate-from-swagger")
    """
    try:
        import tempfile
        
        # 保存上传的文件
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json') as temp_file:
            temp_file.write(await file.read())
            temp_path = temp_file.name
        
        # 🔧 使用 modules SDK
        generator = SwaggerTestCaseGenerator(temp_path)
        test_cases = generator.generate_all_testcases()
        
        # 转换为 API 响应格式
        result = testcases_to_list(test_cases)
        
        # 添加 ID（如果需要）
        for i, tc_dict in enumerate(result, len(test_cases_db) + 1):
            tc_dict['id'] = i
            tc_dict['lastRun'] = '未运行'
            tc_dict['source'] = 'swagger_generated'
        
        # 保存到数据库
        test_cases_db.extend(result)
        if data_manager:
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
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"生成失败: {str(e)}"
        }


# ==================== 步骤4：测试执行 API ====================

async def execute_testcases_with_modules(request: Dict[str, Any], test_cases_db: List):
    """
    执行测试用例（使用 modules SDK）
    
    替换或新增 API 端点: @app.post("/api/testcases/execute")
    """
    try:
        testcase_ids = request.get("testcase_ids", [])
        
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
            "base_url": request.get("base_url", "http://localhost:8080"),
            "timeout": request.get("timeout", 30),
            "retry_on_failure": request.get("retry_on_failure", False),
            "max_retries": request.get("max_retries", 0)
        }
        
        engine = ExecutionEngine(config)
        results = engine.execute(core_test_cases, parallel=True, max_workers=5)
        
        # 🔧 应用 Self-Healing
        healing_config = {
            "enable_l1": True,
            "enable_l2": True,
            "enable_l3": True,
            "enable_l4": True
        }
        healing_engine = HealingEngine(healing_config)
        healed_results = healing_engine.heal(results)
        
        # 🔧 生成报告
        report_config = {
            "slow_threshold": 2.0,
            "include_response": False
        }
        report_generator = ReportGenerator(report_config)
        report = report_generator.generate(healed_results)
        
        # 转换为 API 响应格式
        results_dict = execution_results_to_list(healed_results)
        
        # 获取修复报告
        healing_report = healing_engine.get_healing_report()
        
        return {
            "success": True,
            "results": results_dict,
            "report": report,
            "healing_report": healing_report,
            "message": f"执行完成: {report['summary']['passed']}/{report['summary']['total']} 通过"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"执行失败: {str(e)}"
        }


# ==================== 步骤5：测试数据生成 API ====================

async def generate_test_data_with_modules(request: Dict[str, Any]):
    """
    生成测试数据（使用 modules SDK）
    
    新增或替换 API 端点: @app.post("/api/test-data/generate-smart")
    """
    try:
        schema = request.get("schema", {})
        category = request.get("category", "valid")  # valid/boundary/invalid
        case_id = request.get("case_id")
        
        # 🔧 使用 modules SDK
        data_manager = TestDataManager()
        data = data_manager.generate_data(schema, category, case_id)
        
        return {
            "success": True,
            "data": data,
            "category": category,
            "message": "测试数据生成成功"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"生成失败: {str(e)}"
        }


async def generate_all_categories_data(request: Dict[str, Any]):
    """
    生成所有分类的测试数据
    
    新增 API 端点: @app.post("/api/test-data/generate-all-categories")
    """
    try:
        schema = request.get("schema", {})
        case_id = request.get("case_id")
        
        # 🔧 使用 modules SDK
        data_manager = TestDataManager()
        all_data = data_manager.generate_all_categories(schema, case_id)
        
        return {
            "success": True,
            "data": all_data,
            "message": "所有分类数据生成成功"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"生成失败: {str(e)}"
        }


# ==================== 步骤6：报告生成 API ====================

async def generate_report_with_modules(request: Dict[str, Any]):
    """
    生成测试报告（使用 modules SDK）
    
    新增 API 端点: @app.post("/api/reports/generate")
    """
    try:
        results_data = request.get("results", [])
        format_type = request.get("format", "json")  # json/html/text
        
        # 转换为 ExecutionResult 对象（这里简化处理）
        # 实际应该从数据库加载完整的执行结果
        
        # 🔧 使用 modules SDK
        report_config = {
            "slow_threshold": request.get("slow_threshold", 2.0),
            "include_response": request.get("include_response", False)
        }
        report_generator = ReportGenerator(report_config)
        
        if format_type == "html":
            # 假设 results 是 ExecutionResult 对象列表
            report_html = report_generator.generate_html_report([])
            return {
                "success": True,
                "report": report_html,
                "format": "html",
                "message": "HTML报告生成成功"
            }
        elif format_type == "text":
            report_text = report_generator.generate_text_report([])
            return {
                "success": True,
                "report": report_text,
                "format": "text",
                "message": "文本报告生成成功"
            }
        else:
            report_json = report_generator.generate([])
            return {
                "success": True,
                "report": report_json,
                "format": "json",
                "message": "JSON报告生成成功"
            }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"报告生成失败: {str(e)}"
        }


# ==================== 使用示例 ====================

"""
在 backend_api_server.py 中使用这些函数：

# 导入
from backend_api_modules_integration import (
    parse_swagger_with_modules,
    upload_swagger_with_modules,
    generate_testcases_from_swagger,
    execute_testcases_with_modules,
    generate_test_data_with_modules,
    generate_report_with_modules
)

# 替换现有端点
@app.post("/api/swagger/parse")
async def parse_swagger(data: Dict[str, str]):
    return await parse_swagger_with_modules(data)

@app.post("/api/swagger/upload")
async def upload_swagger(file: UploadFile = File(...)):
    return await upload_swagger_with_modules(file)

# 新增端点
@app.post("/api/testcases/generate-from-swagger")
async def generate_from_swagger(file: UploadFile = File(...)):
    return await generate_testcases_from_swagger(file, test_cases_db, data_manager)

@app.post("/api/testcases/execute")
async def execute_testcases(request: Dict[str, Any]):
    return await execute_testcases_with_modules(request, test_cases_db)

@app.post("/api/test-data/generate-smart")
async def generate_smart_data(request: Dict[str, Any]):
    return await generate_test_data_with_modules(request)

@app.post("/api/reports/generate")
async def generate_report(request: Dict[str, Any]):
    return await generate_report_with_modules(request)
"""
