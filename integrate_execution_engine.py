#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成ExecutionEngine到backend_api_server.py的示例代码
"""

# ==================== 示例1: 替换execute_test_case ====================

# 旧代码 ❌
"""
@app.post("/api/testcases/{testcase_id}/execute")
async def execute_test_case(testcase_id: str):
    try:
        import time
        
        testcase = next((tc for tc in test_cases_db 
                        if str(tc.get('id')) == str(testcase_id)), None)
        if not testcase:
            return {"success": False, "error": "测试用例不存在"}
        
        exec_config = testcase.get('execution_config', {})
        method = exec_config.get('method', 'GET')
        url = exec_config.get('url', '')
        data = exec_config.get('data', {})
        
        # 手动使用requests
        response = requests.request(method, url, json=data, timeout=30)
        
        success = response.status_code < 400
        status = 'passed' if success else 'failed'
        
        return {
            "success": True,
            "result": {
                "status": status,
                "status_code": response.status_code
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
"""

# 新代码 ✅
from modules.executor.real_execution_engine import get_execution_engine

async def execute_test_case_new(testcase_id: str):
    """使用ExecutionEngine执行测试用例"""
    try:
        # 查找测试用例
        testcase = next((tc for tc in test_cases_db 
                        if str(tc.get('id')) == str(testcase_id)), None)
        if not testcase:
            return {"success": False, "error": "测试用例不存在"}
        
        # 获取执行引擎
        engine = get_execution_engine()
        
        # 构建测试用例
        test_case = {
            'id': testcase_id,
            'name': testcase.get('title', '未命名'),
            'execution_type': 'api',
            'config': testcase.get('execution_config', {}),
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
            "trace_id": result.trace_id,
            "status": result.status,
            "duration": f"{int(result.duration * 1000)}ms",
            "executed_at": result.end_time
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
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "message": "测试执行失败"
        }


# ==================== 示例2: 替换execute_api ====================

# 旧代码 ❌
"""
@app.post("/api/execute-api")
async def execute_api(request: Dict[str, Any]):
    try:
        method = request.get('method', 'GET')
        url = request.get('base_url') + request.get('path')
        data = request.get('data', {})
        
        response = requests.request(method, url, json=data, timeout=30)
        
        return {
            "success": response.status_code < 400,
            "status_code": response.status_code,
            "response_data": response.json()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
"""

# 新代码 ✅
async def execute_api_new(request: Dict[str, Any]):
    """使用ExecutionEngine执行API"""
    try:
        # 获取执行引擎
        engine = get_execution_engine()
        
        # 构建完整URL
        base_url = request.get('base_url', '')
        path = request.get('path', '')
        url = base_url.rstrip('/') + '/' + path.lstrip('/')
        
        # 构建测试用例
        test_case = {
            'id': 'api_test',
            'name': f"{request.get('method')} {url}",
            'execution_type': 'api',
            'config': {
                'url': url,
                'method': request.get('method', 'GET'),
                'headers': request.get('headers', {}),
                'body': request.get('data', {})
            },
            'timeout': request.get('timeout', 30)
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
            "error": str(e)
        }


# ==================== 示例3: 替换脚本执行 ====================

# 旧代码 ❌
"""
@app.post("/api/automation/scripts/{script_id}/execute")
async def execute_script(script_id: int):
    try:
        script = next((s for s in scripts_db if s.get('id') == script_id), None)
        if not script:
            return {"success": False, "error": "脚本不存在"}
        
        # 手动使用subprocess
        result = subprocess.run(['python', temp_file], capture_output=True)
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
"""

# 新代码 ✅
async def execute_script_new(script_id: int):
    """使用ExecutionEngine执行脚本"""
    try:
        # 查找脚本
        script = next((s for s in scripts_db if s.get('id') == script_id), None)
        if not script:
            return {"success": False, "error": "脚本不存在"}
        
        # 获取执行引擎
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
            "trace_id": result.trace_id,
            "status": result.status,
            "duration": f"{int(result.duration * 1000)}ms",
            "executed_at": result.end_time,
            "stdout": result.response.get('stdout', '') if result.response else '',
            "stderr": result.response.get('stderr', '') if result.response else ''
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


# ==================== 使用说明 ====================

print("""
集成ExecutionEngine的步骤：

1. 导入执行引擎
   from modules.executor.real_execution_engine import get_execution_engine

2. 获取引擎实例
   engine = get_execution_engine()

3. 构建测试用例
   test_case = {
       'id': 'test_id',
       'name': 'test_name',
       'execution_type': 'api',  # 或 'script', 'command'
       'config': {...},
       'timeout': 30
   }

4. 执行测试
   result = engine.execute(test_case)

5. 处理结果
   if result.success:
       # 成功处理
   else:
       # 失败处理

6. 记录trace_id
   保存result.trace_id用于追踪和调试

优势：
✅ 统一的执行接口
✅ 完整的错误处理
✅ 丰富的观测数据
✅ 自动资源管理
✅ 会话复用提升性能
""")
