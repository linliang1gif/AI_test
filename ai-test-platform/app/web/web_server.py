#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Web可视化平台服务器

基于FastAPI的Web界面，提供：
- 需求上传
- 测试生成
- 执行测试
- 查看报告
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

class WebServer:
    """Web服务器"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.app = FastAPI(
            title="AI Test Platform",
            description="AI驱动的自动化测试平台",
            version="2.0.0"
        )
        
        # 设置CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 初始化组件
        self._initialize_components()
        
        # 设置路由
        self._setup_routes()
        
        # 设置静态文件
        self._setup_static_files()
        
        # 任务状态管理
        self.running_tasks = {}
    
    def _initialize_components(self):
        """初始化组件"""
        try:
            # 尝试导入流水线组件
            import sys
            from pathlib import Path
            
            # 添加项目根目录到路径
            project_root = Path(__file__).parent.parent.parent
            sys.path.append(str(project_root))
            
            from app.pipeline.pipeline_orchestrator import PipelineOrchestrator
            self.pipeline = PipelineOrchestrator()
            print("✅ 流水线组件初始化成功")
        except ImportError as e:
            print(f"⚠️  流水线组件导入失败: {e}")
            print("🔧 使用简化模式运行")
            self.pipeline = None
        except Exception as e:
            print(f"⚠️  组件初始化异常: {e}")
            self.pipeline = None
    
    def _setup_static_files(self):
        """设置静态文件服务"""
        # 创建静态文件目录
        static_dir = Path(__file__).parent / "static"
        static_dir.mkdir(exist_ok=True)
        
        templates_dir = Path(__file__).parent / "templates"
        templates_dir.mkdir(exist_ok=True)
        
        # 挂载静态文件
        self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    def _setup_routes(self):
        """设置路由"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def home():
            """主页"""
            return self._get_home_html()
        
        @self.app.post("/api/upload/requirement")
        async def upload_requirement(file: UploadFile = File(...)):
            """上传需求文档"""
            try:
                # 保存文件
                upload_dir = Path("uploads")
                upload_dir.mkdir(exist_ok=True)
                
                file_path = upload_dir / file.filename
                
                with open(file_path, "wb") as f:
                    content = await file.read()
                    f.write(content)
                
                return {
                    "success": True,
                    "message": "需求文档上传成功",
                    "file_path": str(file_path),
                    "file_size": len(content)
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")
        
        @self.app.post("/api/upload/swagger")
        async def upload_swagger(file: UploadFile = File(...)):
            """上传Swagger文档"""
            try:
                upload_dir = Path("uploads")
                upload_dir.mkdir(exist_ok=True)
                
                file_path = upload_dir / file.filename
                
                with open(file_path, "wb") as f:
                    content = await file.read()
                    f.write(content)
                
                return {
                    "success": True,
                    "message": "Swagger文档上传成功",
                    "file_path": str(file_path),
                    "file_size": len(content)
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")
        
        @self.app.post("/api/generate/tests")
        async def generate_tests(background_tasks: BackgroundTasks, config: Dict[str, Any]):
            """生成测试"""
            try:
                task_id = f"task_{int(asyncio.get_event_loop().time())}"
                
                # 在后台执行测试生成
                background_tasks.add_task(self._run_pipeline_task, task_id, config)
                
                self.running_tasks[task_id] = {
                    "status": "running",
                    "start_time": asyncio.get_event_loop().time(),
                    "progress": 0
                }
                
                return {
                    "success": True,
                    "task_id": task_id,
                    "message": "测试生成任务已启动"
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"启动测试生成失败: {str(e)}")
        
        @self.app.get("/api/task/{task_id}/status")
        async def get_task_status(task_id: str):
            """获取任务状态"""
            if task_id not in self.running_tasks:
                raise HTTPException(status_code=404, detail="任务不存在")
            
            return self.running_tasks[task_id]
        
        @self.app.get("/api/reports")
        async def list_reports():
            """获取报告列表"""
            try:
                reports_dir = Path("output/reports")
                if not reports_dir.exists():
                    return {"reports": []}
                
                reports = []
                for report_file in reports_dir.glob("*.html"):
                    stat = report_file.stat()
                    reports.append({
                        "name": report_file.name,
                        "path": str(report_file),
                        "size": stat.st_size,
                        "created_time": stat.st_ctime
                    })
                
                # 按创建时间排序
                reports.sort(key=lambda x: x["created_time"], reverse=True)
                
                return {"reports": reports}
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"获取报告列表失败: {str(e)}")
        
        @self.app.get("/api/reports/{report_name}")
        async def get_report(report_name: str):
            """获取报告内容"""
            try:
                report_path = Path("output/reports") / report_name
                
                if not report_path.exists():
                    raise HTTPException(status_code=404, detail="报告不存在")
                
                return FileResponse(
                    path=str(report_path),
                    media_type="text/html",
                    filename=report_name
                )
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"获取报告失败: {str(e)}")
    
    async def _run_pipeline_task(self, task_id: str, config: Dict[str, Any]):
        """运行流水线任务"""
        try:
            self.running_tasks[task_id]["status"] = "running"
            self.running_tasks[task_id]["progress"] = 10
            
            if not self.pipeline:
                raise Exception("流水线组件未初始化")
            
            # 执行流水线
            result = self.pipeline.execute_pipeline(config)
            
            self.running_tasks[task_id]["status"] = "completed" if result["success"] else "failed"
            self.running_tasks[task_id]["progress"] = 100
            self.running_tasks[task_id]["result"] = result
            
        except Exception as e:
            self.running_tasks[task_id]["status"] = "failed"
            self.running_tasks[task_id]["error"] = str(e)
    
    def _get_home_html(self) -> str:
        """获取主页HTML"""
        return '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Test Platform - AI自动化测试平台</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 0; text-align: center; margin-bottom: 30px; border-radius: 10px; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { font-size: 1.2em; opacity: 0.9; }
        .card { background: white; border-radius: 10px; padding: 30px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .upload-area { border: 2px dashed #ddd; border-radius: 10px; padding: 40px; text-align: center; margin-bottom: 20px; transition: all 0.3s; }
        .upload-area:hover { border-color: #667eea; background: #f8f9ff; }
        .btn { background: #667eea; color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-size: 16px; transition: all 0.3s; }
        .btn:hover { background: #5a6fd8; transform: translateY(-2px); }
        .btn-success { background: #28a745; }
        .btn-success:hover { background: #218838; }
        .progress { width: 100%; height: 20px; background: #f0f0f0; border-radius: 10px; overflow: hidden; margin: 20px 0; }
        .progress-bar { height: 100%; background: linear-gradient(90deg, #667eea, #764ba2); transition: width 0.3s; }
        .status { padding: 10px; border-radius: 6px; margin: 10px 0; }
        .status.success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .status.error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .status.info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI Test Platform</h1>
            <p>智能化自动化测试平台 - 从需求到测试报告的全流程自动化</p>
        </div>
        
        <div class="grid">
            <div class="card">
                <h2>📄 上传需求文档</h2>
                <div class="upload-area" onclick="document.getElementById('requirementFile').click()">
                    <p>点击或拖拽上传需求文档</p>
                    <p style="font-size: 14px; color: #666; margin-top: 10px;">支持 .txt, .md, .docx 格式</p>
                </div>
                <input type="file" id="requirementFile" style="display: none;" accept=".txt,.md,.docx">
                <div id="requirementStatus"></div>
            </div>
            
            <div class="card">
                <h2>🔗 上传Swagger文档</h2>
                <div class="upload-area" onclick="document.getElementById('swaggerFile').click()">
                    <p>点击或拖拽上传Swagger/OpenAPI文档</p>
                    <p style="font-size: 14px; color: #666; margin-top: 10px;">支持 .json, .yaml 格式</p>
                </div>
                <input type="file" id="swaggerFile" style="display: none;" accept=".json,.yaml,.yml">
                <div id="swaggerStatus"></div>
            </div>
        </div>
        
        <div class="card">
            <h2>🚀 生成测试</h2>
            <button class="btn btn-success" onclick="generateTests()" id="generateBtn">开始生成测试</button>
            <div id="taskProgress" style="display: none;">
                <div class="progress">
                    <div class="progress-bar" id="progressBar" style="width: 0%"></div>
                </div>
                <div id="taskStatus"></div>
            </div>
        </div>
        
        <div class="card">
            <h2>📊 测试报告</h2>
            <div id="reportsList">
                <p>暂无报告，请先生成测试</p>
            </div>
            <button class="btn" onclick="loadReports()">刷新报告列表</button>
        </div>
    </div>

    <script>
        let requirementPath = '';
        let swaggerPath = '';
        let currentTaskId = '';

        // 文件上传处理
        document.getElementById('requirementFile').addEventListener('change', function(e) {
            uploadFile(e.target.files[0], '/api/upload/requirement', 'requirementStatus', (path) => {
                requirementPath = path;
            });
        });

        document.getElementById('swaggerFile').addEventListener('change', function(e) {
            uploadFile(e.target.files[0], '/api/upload/swagger', 'swaggerStatus', (path) => {
                swaggerPath = path;
            });
        });

        async function uploadFile(file, endpoint, statusId, callback) {
            const formData = new FormData();
            formData.append('file', file);
            
            const statusDiv = document.getElementById(statusId);
            statusDiv.innerHTML = '<div class="status info">上传中...</div>';
            
            try {
                const response = await fetch(endpoint, {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    statusDiv.innerHTML = `<div class="status success">✅ ${result.message}</div>`;
                    callback(result.file_path);
                } else {
                    statusDiv.innerHTML = `<div class="status error">❌ 上传失败</div>`;
                }
            } catch (error) {
                statusDiv.innerHTML = `<div class="status error">❌ 上传失败: ${error.message}</div>`;
            }
        }

        async function generateTests() {
            if (!requirementPath) {
                alert('请先上传需求文档');
                return;
            }
            
            const config = {
                requirement_file: requirementPath,
                swagger_file: swaggerPath || null
            };
            
            document.getElementById('generateBtn').disabled = true;
            document.getElementById('taskProgress').style.display = 'block';
            
            try {
                const response = await fetch('/api/generate/tests', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(config)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    currentTaskId = result.task_id;
                    monitorTask(currentTaskId);
                } else {
                    document.getElementById('taskStatus').innerHTML = '<div class="status error">❌ 启动失败</div>';
                }
            } catch (error) {
                document.getElementById('taskStatus').innerHTML = `<div class="status error">❌ 启动失败: ${error.message}</div>`;
            }
        }

        async function monitorTask(taskId) {
            const interval = setInterval(async () => {
                try {
                    const response = await fetch(`/api/task/${taskId}/status`);
                    const status = await response.json();
                    
                    document.getElementById('progressBar').style.width = status.progress + '%';
                    
                    if (status.status === 'completed') {
                        clearInterval(interval);
                        document.getElementById('taskStatus').innerHTML = '<div class="status success">✅ 测试生成完成</div>';
                        document.getElementById('generateBtn').disabled = false;
                        loadReports();
                    } else if (status.status === 'failed') {
                        clearInterval(interval);
                        document.getElementById('taskStatus').innerHTML = '<div class="status error">❌ 测试生成失败</div>';
                        document.getElementById('generateBtn').disabled = false;
                    } else {
                        document.getElementById('taskStatus').innerHTML = '<div class="status info">🔄 正在生成测试...</div>';
                    }
                } catch (error) {
                    clearInterval(interval);
                    document.getElementById('taskStatus').innerHTML = '<div class="status error">❌ 状态查询失败</div>';
                    document.getElementById('generateBtn').disabled = false;
                }
            }, 2000);
        }

        async function loadReports() {
            try {
                const response = await fetch('/api/reports');
                const result = await response.json();
                
                const reportsDiv = document.getElementById('reportsList');
                
                if (result.reports.length === 0) {
                    reportsDiv.innerHTML = '<p>暂无报告</p>';
                } else {
                    const reportsHtml = result.reports.map(report => `
                        <div style="padding: 10px; border: 1px solid #ddd; margin: 10px 0; border-radius: 6px;">
                            <strong>${report.name}</strong>
                            <p style="font-size: 14px; color: #666;">大小: ${(report.size / 1024).toFixed(1)} KB</p>
                            <button class="btn" onclick="window.open('/api/reports/${report.name}', '_blank')">查看报告</button>
                        </div>
                    `).join('');
                    
                    reportsDiv.innerHTML = reportsHtml;
                }
            } catch (error) {
                document.getElementById('reportsList').innerHTML = '<div class="status error">❌ 加载报告失败</div>';
            }
        }

        // 页面加载时获取报告列表
        window.onload = function() {
            loadReports();
        };
    </script>
</body>
</html>
        '''
    
    def run(self):
        """启动Web服务器"""
        print(f"🌐 启动AI Test Platform Web服务器")
        print(f"📍 访问地址: http://{self.host}:{self.port}")
        print(f"📖 API文档: http://{self.host}:{self.port}/docs")
        
        try:
            uvicorn.run(
                self.app,
                host=self.host,
                port=self.port,
                log_level="info",
                access_log=True
            )
        except Exception as e:
            print(f"❌ Web服务器启动失败: {e}")
            print("🔧 可能的解决方案:")
            print("   1. 检查端口8080是否被占用")
            print("   2. 尝试使用管理员权限运行")
            print("   3. 检查防火墙设置")
            print("   4. 尝试使用简化版: python simple_web_server.py")

def main():
    """主函数"""
    import sys
    
    print("🚀 AI Test Platform Web服务器启动器")
    print("=" * 50)
    
    # 检查Python版本
    if sys.version_info < (3, 7):
        print("❌ Python版本过低，需要Python 3.7+")
        return
    
    print(f"✅ Python版本: {sys.version}")
    
    # 检查依赖
    try:
        import fastapi
        import uvicorn
        print("✅ 核心依赖检查通过")
    except ImportError as e:
        print(f"❌ 缺少核心依赖: {e}")
        print("请运行: pip install fastapi uvicorn")
        return
    
    # 创建必要目录
    try:
        Path("uploads").mkdir(exist_ok=True)
        Path("output").mkdir(exist_ok=True)
        Path("output/reports").mkdir(exist_ok=True)
        print("✅ 目录结构检查通过")
    except Exception as e:
        print(f"⚠️  目录创建警告: {e}")
    
    # 启动服务器
    try:
        server = WebServer(host="127.0.0.1", port=8080)  # 使用127.0.0.1而不是0.0.0.0
        server.run()
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("\n🔧 尝试简化版启动:")
        print("   python simple_web_server.py")

if __name__ == "__main__":
    main()