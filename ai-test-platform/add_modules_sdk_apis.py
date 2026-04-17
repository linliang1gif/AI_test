#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加 Modules SDK 集成的 API 端点到 backend_api_server.py
这个脚本会在文件末尾添加新的 API 端点
"""

# 要添加到 backend_api_server.py 末尾的代码
NEW_APIS = '''
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


@app.post("/api/reports/generate-from-results")
async def generate_report_from_results(request: Dict[str, Any]):
    """从执行结果生成报告（使用 modules SDK）"""
    try:
        if not MODULES_SDK_AVAILABLE:
            raise HTTPException(status_code=503, detail="Modules SDK 不可用")
        
        results_data = request.get("results", [])
        format_type = request.get("format", "json")  # json/html/text
        
        # 这里简化处理，实际应该从数据库加载完整的执行结果
        # 或者接收完整的 ExecutionResult 数据
        
        # 🔧 使用 modules SDK
        report_config = {
            "slow_threshold": request.get("slow_threshold", 2.0),
            "include_response": request.get("include_response", False)
        }
        report_generator = ReportGenerator(report_config)
        
        # 注意：这里需要 ExecutionResult 对象列表
        # 简化处理，返回提示信息
        return {
            "success": True,
            "message": "请使用 /api/testcases/execute-batch 执行测试后自动生成报告",
            "format": format_type
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"报告生成失败: {str(e)}"
        }


# ==================== 启动服务器 ====================
'''

if __name__ == "__main__":
    # 读取现有文件
    with open("backend_api_server.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # 检查是否已经添加过
    if "# ==================== Modules SDK 集成 API ====================" in content:
        print("✅ Modules SDK API 已经存在，无需重复添加")
    else:
        # 在文件末尾添加新的 API
        # 找到最后一个 if __name__ == "__main__": 之前的位置
        if 'if __name__ == "__main__":' in content:
            parts = content.rsplit('if __name__ == "__main__":', 1)
            new_content = parts[0] + NEW_APIS + '\nif __name__ == "__main__":' + parts[1]
        else:
            new_content = content + "\n" + NEW_APIS
        
        # 写回文件
        with open("backend_api_server.py", "w", encoding="utf-8") as f:
            f.write(new_content)
        
        print("✅ 成功添加 Modules SDK 集成 API")
