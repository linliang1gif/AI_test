#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Test Platform - 增强版Web服务器

提供更丰富的界面和完整功能
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

try:
    from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    print("✅ FastAPI导入成功")
except ImportError as e:
    print(f"❌ FastAPI导入失败: {e}")
    sys.exit(1)

class EnhancedWebServer:
    """增强版Web服务器"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8080):
        self.host = host
        self.port = port
        self.app = FastAPI(
            title="AI Test Platform - Enhanced",
            description="AI测试平台增强版 - 完整功能界面",
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
        
        # 任务管理
        self.running_tasks = {}
        
        # 设置路由
        self._setup_routes()
    
    def _setup_routes(self):
        """设置路由"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def home():
            """主页 - 增强版界面"""
            return self._get_enhanced_html()
        
        @self.app.get("/api/status")
        async def status():
            """服务状态"""
            return {
                "status": "running",
                "message": "AI Test Platform 增强版运行中",
                "timestamp": time.time(),
                "version": "2.0.0",
                "features": [
                    "AI需求解析",
                    "智能测试设计", 
                    "自动化脚本生成",
                    "Self Healing修复",
                    "覆盖率分析",
                    "多Agent协同"
                ]
            }
        
        @self.app.post("/api/upload/requirement")
        async def upload_requirement(file: UploadFile = File(...)):
            """上传需求文档"""
            try:
                upload_dir = Path("uploads")
                upload_dir.mkdir(exist_ok=True)
                
                file_path = upload_dir / file.filename
                content = await file.read()
                
                with open(file_path, "wb") as f:
                    f.write(content)
                
                return {
                    "success": True,
                    "message": f"需求文档 {file.filename} 上传成功",
                    "file_path": str(file_path),
                    "file_size": len(content),
                    "file_type": "requirement"
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "message": f"需求文档上传失败: {str(e)}"
                }
        
        @self.app.post("/api/upload/swagger")
        async def upload_swagger(file: UploadFile = File(...)):
            """上传Swagger文档"""
            try:
                upload_dir = Path("uploads")
                upload_dir.mkdir(exist_ok=True)
                
                file_path = upload_dir / file.filename
                content = await file.read()
                
                with open(file_path, "wb") as f:
                    f.write(content)
                
                return {
                    "success": True,
                    "message": f"Swagger文档 {file.filename} 上传成功",
                    "file_path": str(file_path),
                    "file_size": len(content),
                    "file_type": "swagger"
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "message": f"Swagger文档上传失败: {str(e)}"
                }
        
        @self.app.post("/api/generate/tests")
        async def generate_tests(background_tasks: BackgroundTasks, config: Dict[str, Any]):
            """生成测试 - 模拟完整流程"""
            try:
                task_id = f"task_{int(time.time())}"
                
                # 在后台执行模拟任务
                background_tasks.add_task(self._simulate_test_generation, task_id, config)
                
                self.running_tasks[task_id] = {
                    "status": "running",
                    "start_time": time.time(),
                    "progress": 0,
                    "current_step": "初始化",
                    "steps": [
                        "需求解析",
                        "模块拆分", 
                        "测试点生成",
                        "测试用例生成",
                        "API解析",
                        "脚本生成",
                        "测试执行",
                        "Bug分析",
                        "报告生成"
                    ]
                }
                
                return {
                    "success": True,
                    "task_id": task_id,
                    "message": "AI测试生成任务已启动",
                    "estimated_time": "3-5分钟"
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
                reports_dir.mkdir(parents=True, exist_ok=True)
                
                reports = []
                
                # 创建一些示例报告
                sample_reports = [
                    {
                        "name": "AI测试报告_20260314.html",
                        "size": 1024 * 50,  # 50KB
                        "created_time": time.time() - 3600,
                        "type": "综合报告"
                    },
                    {
                        "name": "覆盖率分析报告.html", 
                        "size": 1024 * 30,  # 30KB
                        "created_time": time.time() - 7200,
                        "type": "覆盖率报告"
                    },
                    {
                        "name": "Self_Healing日志.html",
                        "size": 1024 * 20,  # 20KB
                        "created_time": time.time() - 10800,
                        "type": "修复日志"
                    }
                ]
                
                return {"reports": sample_reports}
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"获取报告列表失败: {str(e)}")
        
        @self.app.get("/api/features")
        async def get_features():
            """获取平台功能特性"""
            return {
                "enterprise_features": [
                    {
                        "name": "Swagger/OpenAPI解析",
                        "description": "自动解析接口文档，提取API信息",
                        "status": "available"
                    },
                    {
                        "name": "接口测试生成",
                        "description": "自动生成pytest接口测试脚本",
                        "status": "available"
                    },
                    {
                        "name": "Self Healing修复",
                        "description": "测试失败时AI自动分析并修复",
                        "status": "available"
                    },
                    {
                        "name": "覆盖率分析",
                        "description": "全面的测试覆盖率分析和建议",
                        "status": "available"
                    },
                    {
                        "name": "AI Agent系统",
                        "description": "多个专业化Agent协同工作",
                        "status": "available"
                    },
                    {
                        "name": "自动化流水线",
                        "description": "端到端自动化测试流程",
                        "status": "available"
                    }
                ]
            }
    
    async def _simulate_test_generation(self, task_id: str, config: Dict[str, Any]):
        """模拟测试生成过程"""
        try:
            steps = self.running_tasks[task_id]["steps"]
            
            for i, step in enumerate(steps):
                # 模拟每个步骤的执行时间
                await self._async_sleep(2)  # 每步2秒
                
                progress = int((i + 1) / len(steps) * 100)
                
                self.running_tasks[task_id].update({
                    "progress": progress,
                    "current_step": step,
                    "status": "running" if progress < 100 else "completed"
                })
            
            # 任务完成
            self.running_tasks[task_id].update({
                "status": "completed",
                "progress": 100,
                "current_step": "完成",
                "result": {
                    "modules_generated": 5,
                    "testpoints_generated": 25,
                    "testcases_generated": 150,
                    "api_scripts_generated": 12,
                    "coverage_rate": "85%"
                }
            })
            
        except Exception as e:
            self.running_tasks[task_id].update({
                "status": "failed",
                "error": str(e)
            })
    
    async def _async_sleep(self, seconds: int):
        """异步睡眠"""
        import asyncio
        await asyncio.sleep(seconds)
    
    def _get_enhanced_html(self) -> str:
        """获取增强版HTML界面"""
        return '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Test Platform - 企业级版本</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body { 
            font-family: 'Segoe UI', 'Microsoft YaHei', Arial, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .navbar {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 1rem 2rem;
            box-shadow: 0 2px 20px rgba(0,0,0,0.1);
            position: sticky;
            top: 0;
            z-index: 1000;
        }
        
        .navbar-content {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            display: flex;
            align-items: center;
            font-size: 1.5rem;
            font-weight: bold;
            color: #333;
        }
        
        .logo i {
            margin-right: 0.5rem;
            color: #667eea;
        }
        
        .nav-links {
            display: flex;
            gap: 2rem;
        }
        
        .nav-link {
            color: #666;
            text-decoration: none;
            font-weight: 500;
            transition: color 0.3s;
        }
        
        .nav-link:hover {
            color: #667eea;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .hero {
            text-align: center;
            color: white;
            margin-bottom: 3rem;
        }
        
        .hero h1 {
            font-size: 3rem;
            margin-bottom: 1rem;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
        
        .hero p {
            font-size: 1.2rem;
            opacity: 0.9;
            margin-bottom: 2rem;
        }
        
        .version-badge {
            display: inline-block;
            background: rgba(255,255,255,0.2);
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
            margin-bottom: 2rem;
        }
        
        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 2rem;
            margin-bottom: 3rem;
        }
        
        .card {
            background: white;
            border-radius: 15px;
            padding: 2rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s, box-shadow 0.3s;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.15);
        }
        
        .card-header {
            display: flex;
            align-items: center;
            margin-bottom: 1.5rem;
        }
        
        .card-icon {
            width: 50px;
            height: 50px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 1rem;
            font-size: 1.5rem;
            color: white;
        }
        
        .card-title {
            font-size: 1.3rem;
            font-weight: 600;
            color: #333;
        }
        
        .upload-area {
            border: 2px dashed #ddd;
            border-radius: 10px;
            padding: 2rem;
            text-align: center;
            transition: all 0.3s;
            cursor: pointer;
            margin: 1rem 0;
        }
        
        .upload-area:hover {
            border-color: #667eea;
            background: #f8f9ff;
        }
        
        .upload-area.dragover {
            border-color: #667eea;
            background: #f0f4ff;
            transform: scale(1.02);
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 0.8rem 2rem;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 500;
            transition: all 0.3s;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .btn-secondary {
            background: linear-gradient(135deg, #6c757d, #495057);
        }
        
        .btn-success {
            background: linear-gradient(135deg, #28a745, #20c997);
        }
        
        .progress-container {
            margin: 2rem 0;
            display: none;
        }
        
        .progress {
            width: 100%;
            height: 8px;
            background: #f0f0f0;
            border-radius: 4px;
            overflow: hidden;
            margin: 1rem 0;
        }
        
        .progress-bar {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.3s ease;
            border-radius: 4px;
        }
        
        .status-message {
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            display: none;
        }
        
        .status-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .status-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .status-info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
            margin: 2rem 0;
        }
        
        .feature-item {
            display: flex;
            align-items: center;
            padding: 1rem;
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            color: white;
        }
        
        .feature-icon {
            margin-right: 1rem;
            font-size: 1.2rem;
        }
        
        .reports-list {
            max-height: 300px;
            overflow-y: auto;
        }
        
        .report-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem;
            border: 1px solid #eee;
            border-radius: 8px;
            margin-bottom: 0.5rem;
            transition: background 0.3s;
        }
        
        .report-item:hover {
            background: #f8f9fa;
        }
        
        .report-info h4 {
            margin: 0;
            color: #333;
        }
        
        .report-meta {
            font-size: 0.9rem;
            color: #666;
        }
        
        .footer {
            text-align: center;
            padding: 2rem;
            color: rgba(255,255,255,0.8);
            border-top: 1px solid rgba(255,255,255,0.1);
        }
        
        @media (max-width: 768px) {
            .dashboard {
                grid-template-columns: 1fr;
            }
            
            .hero h1 {
                font-size: 2rem;
            }
            
            .navbar-content {
                flex-direction: column;
                gap: 1rem;
            }
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .step-indicator {
            display: flex;
            justify-content: space-between;
            margin: 1rem 0;
            font-size: 0.9rem;
        }
        
        .step {
            padding: 0.5rem;
            border-radius: 5px;
            background: #f8f9fa;
            color: #666;
            transition: all 0.3s;
        }
        
        .step.active {
            background: #667eea;
            color: white;
        }
        
        .step.completed {
            background: #28a745;
            color: white;
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="navbar-content">
            <div class="logo">
                <i class="fas fa-robot"></i>
                AI Test Platform
            </div>
            <div class="nav-links">
                <a href="#" class="nav-link">首页</a>
                <a href="#features" class="nav-link">功能</a>
                <a href="#reports" class="nav-link">报告</a>
                <a href="/docs" class="nav-link" target="_blank">API文档</a>
            </div>
        </div>
    </nav>

    <div class="container">
        <div class="hero">
            <div class="version-badge">
                <i class="fas fa-crown"></i> 企业级版本 v2.0.0
            </div>
            <h1><i class="fas fa-brain"></i> AI Test Platform</h1>
            <p>智能化自动化测试平台 - 从需求到报告的全流程AI驱动</p>
            
            <div class="features-grid">
                <div class="feature-item">
                    <i class="fas fa-magic feature-icon"></i>
                    <span>AI驱动测试设计</span>
                </div>
                <div class="feature-item">
                    <i class="fas fa-cogs feature-icon"></i>
                    <span>Self Healing自修复</span>
                </div>
                <div class="feature-item">
                    <i class="fas fa-chart-line feature-icon"></i>
                    <span>智能覆盖率分析</span>
                </div>
                <div class="feature-item">
                    <i class="fas fa-users feature-icon"></i>
                    <span>多Agent协同</span>
                </div>
            </div>
        </div>

        <div class="dashboard">
            <!-- 文档上传卡片 -->
            <div class="card">
                <div class="card-header">
                    <div class="card-icon" style="background: linear-gradient(135deg, #ff6b6b, #ee5a24);">
                        <i class="fas fa-file-upload"></i>
                    </div>
                    <div class="card-title">智能文档解析</div>
                </div>
                
                <div class="upload-area" id="requirementUpload">
                    <i class="fas fa-cloud-upload-alt" style="font-size: 2rem; color: #667eea; margin-bottom: 1rem;"></i>
                    <p><strong>上传需求文档</strong></p>
                    <p style="font-size: 0.9rem; color: #666; margin-top: 0.5rem;">
                        支持 .txt, .md, .docx 格式
                    </p>
                </div>
                <input type="file" id="requirementFile" style="display: none;" accept=".txt,.md,.docx">
                
                <div class="upload-area" id="swaggerUpload" style="margin-top: 1rem;">
                    <i class="fas fa-code" style="font-size: 2rem; color: #28a745; margin-bottom: 1rem;"></i>
                    <p><strong>上传Swagger文档</strong></p>
                    <p style="font-size: 0.9rem; color: #666; margin-top: 0.5rem;">
                        支持 .json, .yaml 格式
                    </p>
                </div>
                <input type="file" id="swaggerFile" style="display: none;" accept=".json,.yaml,.yml">
                
                <div id="uploadStatus" class="status-message"></div>
            </div>

            <!-- 测试生成卡片 -->
            <div class="card">
                <div class="card-header">
                    <div class="card-icon" style="background: linear-gradient(135deg, #667eea, #764ba2);">
                        <i class="fas fa-rocket"></i>
                    </div>
                    <div class="card-title">AI测试生成</div>
                </div>
                
                <p style="color: #666; margin-bottom: 1.5rem;">
                    基于AI的端到端测试生成，包含完整的测试生命周期
                </p>
                
                <button class="btn" id="generateBtn" onclick="startTestGeneration()">
                    <i class="fas fa-magic"></i>
                    开始AI测试生成
                </button>
                
                <div class="progress-container" id="progressContainer">
                    <div class="step-indicator" id="stepIndicator"></div>
                    <div class="progress">
                        <div class="progress-bar" id="progressBar"></div>
                    </div>
                    <div id="currentStep" style="text-align: center; margin-top: 0.5rem; font-weight: 500;"></div>
                </div>
                
                <div id="generationStatus" class="status-message"></div>
            </div>

            <!-- 功能特性卡片 -->
            <div class="card" id="features">
                <div class="card-header">
                    <div class="card-icon" style="background: linear-gradient(135deg, #28a745, #20c997);">
                        <i class="fas fa-star"></i>
                    </div>
                    <div class="card-title">企业级特性</div>
                </div>
                
                <div id="featuresList">
                    <div style="text-align: center; color: #666;">
                        <div class="loading"></div>
                        <p style="margin-top: 1rem;">加载功能特性...</p>
                    </div>
                </div>
                
                <button class="btn btn-secondary" onclick="loadFeatures()" style="margin-top: 1rem;">
                    <i class="fas fa-sync-alt"></i>
                    刷新特性
                </button>
            </div>

            <!-- 测试报告卡片 -->
            <div class="card" id="reports">
                <div class="card-header">
                    <div class="card-icon" style="background: linear-gradient(135deg, #ffc107, #fd7e14);">
                        <i class="fas fa-chart-bar"></i>
                    </div>
                    <div class="card-title">测试报告中心</div>
                </div>
                
                <div class="reports-list" id="reportsList">
                    <div style="text-align: center; color: #666; padding: 2rem;">
                        <i class="fas fa-file-alt" style="font-size: 2rem; margin-bottom: 1rem;"></i>
                        <p>暂无报告，请先生成测试</p>
                    </div>
                </div>
                
                <button class="btn btn-success" onclick="loadReports()">
                    <i class="fas fa-sync-alt"></i>
                    刷新报告
                </button>
            </div>
        </div>
    </div>

    <div class="footer">
        <p><i class="fas fa-globe"></i> 访问地址: <strong>http://127.0.0.1:8080</strong></p>
        <p><i class="fas fa-info-circle"></i> AI Test Platform 企业级版本 - 智能化测试解决方案</p>
    </div>

    <script>
        let requirementUploaded = false;
        let swaggerUploaded = false;
        let currentTaskId = null;

        // 页面加载完成后初始化
        window.onload = function() {
            loadFeatures();
            loadReports();
            setupDragAndDrop();
        };

        // 设置拖拽上传
        function setupDragAndDrop() {
            const requirementArea = document.getElementById('requirementUpload');
            const swaggerArea = document.getElementById('swaggerUpload');

            [requirementArea, swaggerArea].forEach(area => {
                area.addEventListener('dragover', (e) => {
                    e.preventDefault();
                    area.classList.add('dragover');
                });

                area.addEventListener('dragleave', () => {
                    area.classList.remove('dragover');
                });

                area.addEventListener('drop', (e) => {
                    e.preventDefault();
                    area.classList.remove('dragover');
                    
                    const files = e.dataTransfer.files;
                    if (files.length > 0) {
                        const fileInput = area.id === 'requirementUpload' ? 
                            document.getElementById('requirementFile') : 
                            document.getElementById('swaggerFile');
                        
                        fileInput.files = files;
                        fileInput.dispatchEvent(new Event('change'));
                    }
                });
            });

            // 点击上传
            requirementArea.onclick = () => document.getElementById('requirementFile').click();
            swaggerArea.onclick = () => document.getElementById('swaggerFile').click();
        }

        // 文件上传处理
        document.getElementById('requirementFile').addEventListener('change', function(e) {
            uploadFile(e.target.files[0], '/api/upload/requirement', 'requirement');
        });

        document.getElementById('swaggerFile').addEventListener('change', function(e) {
            uploadFile(e.target.files[0], '/api/upload/swagger', 'swagger');
        });

        async function uploadFile(file, endpoint, type) {
            if (!file) return;

            const formData = new FormData();
            formData.append('file', file);

            showStatus('上传中...', 'info');

            try {
                const response = await fetch(endpoint, {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (result.success) {
                    showStatus(`✅ ${result.message}`, 'success');
                    
                    if (type === 'requirement') {
                        requirementUploaded = true;
                    } else if (type === 'swagger') {
                        swaggerUploaded = true;
                    }
                    
                    updateGenerateButton();
                } else {
                    showStatus(`❌ ${result.message}`, 'error');
                }
            } catch (error) {
                showStatus(`❌ 上传失败: ${error.message}`, 'error');
            }
        }

        function updateGenerateButton() {
            const btn = document.getElementById('generateBtn');
            if (requirementUploaded) {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-magic"></i> 开始AI测试生成';
            }
        }

        async function startTestGeneration() {
            if (!requirementUploaded) {
                showStatus('请先上传需求文档', 'error');
                return;
            }

            const config = {
                requirement_uploaded: requirementUploaded,
                swagger_uploaded: swaggerUploaded
            };

            document.getElementById('generateBtn').disabled = true;
            document.getElementById('progressContainer').style.display = 'block';

            try {
                const response = await fetch('/api/generate/tests', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(config)
                });

                const result = await response.json();

                if (result.success) {
                    currentTaskId = result.task_id;
                    showGenerationStatus(`🚀 ${result.message}`, 'info');
                    monitorTask(currentTaskId);
                } else {
                    showGenerationStatus('❌ 启动失败', 'error');
                    document.getElementById('generateBtn').disabled = false;
                }
            } catch (error) {
                showGenerationStatus(`❌ 启动失败: ${error.message}`, 'error');
                document.getElementById('generateBtn').disabled = false;
            }
        }

        async function monitorTask(taskId) {
            const interval = setInterval(async () => {
                try {
                    const response = await fetch(`/api/task/${taskId}/status`);
                    const status = await response.json();

                    updateProgress(status);

                    if (status.status === 'completed') {
                        clearInterval(interval);
                        showGenerationStatus('✅ AI测试生成完成！', 'success');
                        document.getElementById('generateBtn').disabled = false;
                        loadReports();
                    } else if (status.status === 'failed') {
                        clearInterval(interval);
                        showGenerationStatus('❌ 测试生成失败', 'error');
                        document.getElementById('generateBtn').disabled = false;
                    }
                } catch (error) {
                    clearInterval(interval);
                    showGenerationStatus('❌ 状态查询失败', 'error');
                    document.getElementById('generateBtn').disabled = false;
                }
            }, 2000);
        }

        function updateProgress(status) {
            const progressBar = document.getElementById('progressBar');
            const currentStep = document.getElementById('currentStep');
            const stepIndicator = document.getElementById('stepIndicator');

            progressBar.style.width = status.progress + '%';
            currentStep.textContent = `当前步骤: ${status.current_step} (${status.progress}%)`;

            // 更新步骤指示器
            if (status.steps) {
                stepIndicator.innerHTML = status.steps.map((step, index) => {
                    let className = 'step';
                    if (step === status.current_step) {
                        className += ' active';
                    } else if (status.progress > (index / status.steps.length) * 100) {
                        className += ' completed';
                    }
                    return `<div class="${className}">${step}</div>`;
                }).join('');
            }
        }

        async function loadFeatures() {
            try {
                const response = await fetch('/api/features');
                const result = await response.json();

                const featuresList = document.getElementById('featuresList');
                
                if (result.enterprise_features) {
                    const featuresHtml = result.enterprise_features.map(feature => `
                        <div style="display: flex; align-items: center; padding: 0.8rem; border-left: 3px solid #28a745; background: #f8f9fa; margin-bottom: 0.5rem; border-radius: 5px;">
                            <i class="fas fa-check-circle" style="color: #28a745; margin-right: 1rem;"></i>
                            <div>
                                <strong>${feature.name}</strong>
                                <p style="margin: 0; font-size: 0.9rem; color: #666;">${feature.description}</p>
                            </div>
                        </div>
                    `).join('');
                    
                    featuresList.innerHTML = featuresHtml;
                }
            } catch (error) {
                document.getElementById('featuresList').innerHTML = 
                    '<div style="color: #dc3545; text-align: center;">❌ 加载功能特性失败</div>';
            }
        }

        async function loadReports() {
            try {
                const response = await fetch('/api/reports');
                const result = await response.json();

                const reportsList = document.getElementById('reportsList');

                if (result.reports && result.reports.length > 0) {
                    const reportsHtml = result.reports.map(report => `
                        <div class="report-item">
                            <div class="report-info">
                                <h4><i class="fas fa-file-alt"></i> ${report.name}</h4>
                                <div class="report-meta">
                                    类型: ${report.type} | 大小: ${(report.size / 1024).toFixed(1)} KB | 
                                    创建时间: ${new Date(report.created_time * 1000).toLocaleString()}
                                </div>
                            </div>
                            <button class="btn" onclick="viewReport('${report.name}')">
                                <i class="fas fa-eye"></i> 查看
                            </button>
                        </div>
                    `).join('');

                    reportsList.innerHTML = reportsHtml;
                } else {
                    reportsList.innerHTML = `
                        <div style="text-align: center; color: #666; padding: 2rem;">
                            <i class="fas fa-file-alt" style="font-size: 2rem; margin-bottom: 1rem;"></i>
                            <p>暂无报告，请先生成测试</p>
                        </div>
                    `;
                }
            } catch (error) {
                document.getElementById('reportsList').innerHTML = 
                    '<div style="color: #dc3545; text-align: center;">❌ 加载报告失败</div>';
            }
        }

        function viewReport(reportName) {
            // 模拟打开报告
            showStatus(`📊 正在打开报告: ${reportName}`, 'info');
            setTimeout(() => {
                showStatus(`✅ 报告已在新窗口打开`, 'success');
            }, 1000);
        }

        function showStatus(message, type) {
            const statusDiv = document.getElementById('uploadStatus');
            statusDiv.textContent = message;
            statusDiv.className = `status-message status-${type}`;
            statusDiv.style.display = 'block';

            setTimeout(() => {
                statusDiv.style.display = 'none';
            }, 5000);
        }

        function showGenerationStatus(message, type) {
            const statusDiv = document.getElementById('generationStatus');
            statusDiv.textContent = message;
            statusDiv.className = `status-message status-${type}`;
            statusDiv.style.display = 'block';

            if (type !== 'info') {
                setTimeout(() => {
                    statusDiv.style.display = 'none';
                }, 5000);
            }
        }
    </script>
</body>
</html>
        '''
    
    def run(self):
        """启动增强版Web服务器"""
        print(f"🚀 启动AI Test Platform增强版Web服务器")
        print(f"📍 服务器地址: http://{self.host}:{self.port}")
        print(f"📖 API文档: http://{self.host}:{self.port}/docs")
        print(f"✨ 企业级功能: 完整界面 + 高级特性")
        print("=" * 60)
        
        try:
            uvicorn.run(
                self.app,
                host=self.host,
                port=self.port,
                log_level="info",
                access_log=True
            )
        except Exception as e:
            print(f"❌ 服务器启动失败: {e}")

def main():
    """主函数"""
    print("🚀 AI Test Platform 增强版Web服务器")
    print("=" * 50)
    
    server = EnhancedWebServer(host="127.0.0.1", port=8080)
    server.run()

if __name__ == "__main__":
    main()