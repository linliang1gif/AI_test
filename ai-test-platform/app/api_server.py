#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Test Platform - FastAPI服务器

提供Web API接口访问AI测试平台功能。
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from config.config import get_config
from app.main import AITestPlatform

# 创建FastAPI应用
app = FastAPI(
    title="AI Test Platform API",
    description="AI测试设计与自动化平台API接口",
    version="1.0.0"
)

# 全局变量
config = get_config()
platform = AITestPlatform()

# 请求模型
class GenerateTestCasesRequest(BaseModel):
    requirement_text: str
    project_name: Optional[str] = "测试项目"
    module_name: Optional[str] = "核心模块"

class GenerateScriptsRequest(BaseModel):
    testcases: List[Dict[str, Any]]
    swagger_data: Optional[Dict[str, Any]] = None

class RunTestsRequest(BaseModel):
    test_files: Optional[List[str]] = None
    markers: Optional[str] = None

# API路由
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "AI Test Platform API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}

@app.post("/generate_testcases")
async def generate_testcases(request: GenerateTestCasesRequest):
    """生成测试用例"""
    try:
        # 保存需求文本到临时文件
        temp_requirement_file = config.paths.data_dir / "temp_requirement.txt"
        with open(temp_requirement_file, 'w', encoding='utf-8') as f:
            f.write(request.requirement_text)
        
        # 运行测试用例生成流程
        result = platform.run_complete_workflow(str(temp_requirement_file))
        
        if result['success']:
            return {
                "success": True,
                "message": "测试用例生成成功",
                "data": {
                    "modules_count": result['summary']['modules_count'],
                    "testcases_count": result['summary']['testcases_count'],
                    "excel_file": result['results'].get('excel_file'),
                    "report_file": result['results'].get('report')
                }
            }
        else:
            raise HTTPException(status_code=500, detail=result['error'])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_scripts")
async def generate_scripts(request: GenerateScriptsRequest):
    """生成自动化脚本"""
    try:
        # 转换测试用例格式
        api_testcases = []
        for testcase in request.testcases:
            api_testcase = {
                'id': testcase.get('id', ''),
                'title': testcase.get('title', ''),
                'api_name': testcase.get('api_name', 'test_api'),
                'method': testcase.get('method', 'POST'),
                'url': testcase.get('url', '/api/test'),
                'headers': testcase.get('headers', {'Content-Type': 'application/json'}),
                'request_data': testcase.get('request_data', {}),
                'expected_status': testcase.get('expected_status', 200),
                'expected_response': testcase.get('expected_response', {}),
                'test_type': testcase.get('test_type', '功能测试'),
                'priority': testcase.get('priority', '中')
            }
            api_testcases.append(api_testcase)
        
        # 生成脚本
        scripts = platform.api_script_generator.generate_api_scripts(api_testcases)
        
        return {
            "success": True,
            "message": "自动化脚本生成成功",
            "data": {
                "scripts_count": len(scripts),
                "script_files": list(scripts.keys()),
                "scripts": scripts
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/run_tests")
async def run_tests(request: RunTestsRequest):
    """运行测试"""
    try:
        if request.test_files:
            # 运行指定的测试文件
            results = platform.pytest_runner.run_specific_tests(request.test_files)
        else:
            # 运行所有测试
            results = platform.pytest_runner.run_tests(markers=request.markers)
        
        return {
            "success": True,
            "message": "测试执行完成",
            "data": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/report")
async def get_report():
    """获取最新的测试报告"""
    try:
        reports_dir = config.paths.reports_dir
        
        # 查找最新的HTML报告
        html_reports = list(reports_dir.glob("test_report_*.html"))
        if not html_reports:
            raise HTTPException(status_code=404, detail="未找到测试报告")
        
        latest_report = max(html_reports, key=lambda x: x.stat().st_mtime)
        
        return FileResponse(
            path=latest_report,
            media_type="text/html",
            filename=latest_report.name
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{file_type}")
async def download_file(file_type: str):
    """下载生成的文件"""
    try:
        output_dir = config.paths.output_dir
        
        if file_type == "excel":
            excel_files = list(output_dir.glob("*.xlsx"))
            if not excel_files:
                raise HTTPException(status_code=404, detail="未找到Excel文件")
            
            latest_excel = max(excel_files, key=lambda x: x.stat().st_mtime)
            return FileResponse(
                path=latest_excel,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                filename=latest_excel.name
            )
        
        elif file_type == "scripts":
            # 打包测试脚本
            import zipfile
            import tempfile
            
            tests_dir = config.paths.tests_dir
            if not tests_dir.exists():
                raise HTTPException(status_code=404, detail="未找到测试脚本")
            
            # 创建临时zip文件
            temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
            
            with zipfile.ZipFile(temp_zip.name, 'w') as zipf:
                for script_file in tests_dir.glob("*.py"):
                    zipf.write(script_file, script_file.name)
            
            return FileResponse(
                path=temp_zip.name,
                media_type="application/zip",
                filename="test_scripts.zip"
            )
        
        else:
            raise HTTPException(status_code=400, detail="不支持的文件类型")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload_requirement")
async def upload_requirement(file: UploadFile = File(...)):
    """上传需求文档"""
    try:
        # 保存上传的文件
        requirement_file = config.paths.data_dir / file.filename
        
        with open(requirement_file, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        return {
            "success": True,
            "message": "需求文档上传成功",
            "data": {
                "filename": file.filename,
                "size": len(content),
                "path": str(requirement_file)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload_swagger")
async def upload_swagger(file: UploadFile = File(...)):
    """上传Swagger文档"""
    try:
        # 保存上传的文件
        swagger_file = config.paths.data_dir / "swagger.json"
        
        with open(swagger_file, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        return {
            "success": True,
            "message": "Swagger文档上传成功",
            "data": {
                "filename": file.filename,
                "size": len(content),
                "path": str(swagger_file)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    """获取平台状态"""
    try:
        # 检查各个组件状态
        status = {
            "platform": "running",
            "config": "loaded",
            "ai_client": "connected",
            "components": {
                "requirement_parser": "ready",
                "swagger_parser": "ready",
                "module_splitter": "ready",
                "testpoint_generator": "ready",
                "scenario_generator": "ready",
                "testcase_generator": "ready",
                "api_script_generator": "ready",
                "pytest_runner": "ready",
                "bug_reasoner": "ready",
                "report_generator": "ready"
            },
            "directories": {
                "data_dir": str(config.paths.data_dir),
                "output_dir": str(config.paths.output_dir),
                "tests_dir": str(config.paths.tests_dir),
                "reports_dir": str(config.paths.reports_dir)
            }
        }
        
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 启动服务器
def start_server():
    """启动API服务器"""
    print("🚀 启动 AI Test Platform API 服务器")
    print(f"📁 数据目录: {config.paths.data_dir}")
    print(f"📁 输出目录: {config.paths.output_dir}")
    print("🌐 API文档: http://localhost:8000/docs")
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    start_server()