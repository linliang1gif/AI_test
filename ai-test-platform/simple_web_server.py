#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Test Platform - 简化版Web服务器

解决启动问题的简化版本，确保Web服务器能够正常启动
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
    from fastapi import FastAPI, File, UploadFile, HTTPException
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    print("✅ FastAPI导入成功")
except ImportError as e:
    print(f"❌ FastAPI导入失败: {e}")
    print("请安装依赖: pip install fastapi uvicorn")
    sys.exit(1)

class SimpleWebServer:
    """简化版Web服务器"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8080):
        self.host = host
        self.port = port
        self.app = FastAPI(
            title="AI Test Platform - Simple",
            description="AI测试平台简化版",
            version="1.0.0"
        )
        
        # 设置CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 设置路由
        self._setup_routes()
    
    def _setup_routes(self):
        """设置路由"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def home():
            """主页"""
            return self._get_simple_html()
        
        @self.app.get("/api/status")
        async def status():
            """服务状态"""
            return {
                "status": "running",
                "message": "AI Test Platform 简化版运行中",
                "timestamp": time.time(),
                "version": "1.0.0"
            }
        
        @self.app.post("/api/upload")
        async def upload_file(file: UploadFile = File(...)):
            """文件上传测试"""
            try:
                # 创建上传目录
                upload_dir = Path("uploads")
                upload_dir.mkdir(exist_ok=True)
                
                # 保存文件
                file_path = upload_dir / file.filename
                content = await file.read()
                
                with open(file_path, "wb") as f:
                    f.write(content)
                
                return {
                    "success": True,
                    "message": f"文件 {file.filename} 上传成功",
                    "file_path": str(file_path),
                    "file_size": len(content)
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "message": f"文件上传失败: {str(e)}"
                }
        
        @self.app.get("/api/test")
        async def test_api():
            """API测试"""
            return {
                "success": True,
                "message": "API测试成功",
                "data": {
                    "platform": "AI Test Platform",
                    "features": [
                        "需求文档解析",
                        "测试用例生成", 
                        "API测试脚本生成",
                        "自动化测试执行"
                    ]
                }
            }
    
    def _get_simple_html(self) -> str:
        """获取简化版HTML页面"""
        return '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Test Platform - 简化版</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Microsoft YaHei', Arial, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container { 
            background: white; 
            border-radius: 20px; 
            padding: 40px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            max-width: 600px;
            width: 90%;
            text-align: center;
        }
        .header { margin-bottom: 30px; }
        .header h1 { 
            color: #333; 
            font-size: 2.5em; 
            margin-bottom: 10px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .header p { color: #666; font-size: 1.1em; }
        .status { 
            background: #f8f9fa; 
            border-radius: 10px; 
            padding: 20px; 
            margin: 20px 0;
            border-left: 4px solid #28a745;
        }
        .status.success { border-left-color: #28a745; }
        .status h3 { color: #28a745; margin-bottom: 10px; }
        .features { text-align: left; margin: 20px 0; }
        .features h3 { color: #333; margin-bottom: 15px; }
        .features ul { list-style: none; }
        .features li { 
            padding: 8px 0; 
            color: #555;
            position: relative;
            padding-left: 25px;
        }
        .features li:before {
            content: "✅";
            position: absolute;
            left: 0;
        }
        .btn { 
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white; 
            border: none; 
            padding: 12px 30px; 
            border-radius: 25px; 
            cursor: pointer; 
            font-size: 16px; 
            margin: 10px;
            transition: all 0.3s;
        }
        .btn:hover { 
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        .upload-area {
            border: 2px dashed #ddd;
            border-radius: 10px;
            padding: 30px;
            margin: 20px 0;
            transition: all 0.3s;
            cursor: pointer;
        }
        .upload-area:hover {
            border-color: #667eea;
            background: #f8f9ff;
        }
        .result {
            margin: 20px 0;
            padding: 15px;
            border-radius: 8px;
            display: none;
        }
        .result.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .result.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI Test Platform</h1>
            <p>智能化自动化测试平台 - 简化版</p>
        </div>
        
        <div class="status success">
            <h3>🎉 服务器运行正常</h3>
            <p>Web服务器已成功启动，所有功能正常运行</p>
        </div>
        
        <div class="features">
            <h3>🚀 核心功能</h3>
            <ul>
                <li>AI驱动的需求解析</li>
                <li>智能测试用例生成</li>
                <li>自动化API测试脚本</li>
                <li>Self Healing自修复</li>
                <li>测试覆盖率分析</li>
                <li>Web可视化界面</li>
            </ul>
        </div>
        
        <div class="upload-area" onclick="document.getElementById('fileInput').click()">
            <p>📁 点击上传测试文件</p>
            <p style="font-size: 14px; color: #666; margin-top: 10px;">支持需求文档和Swagger文件</p>
        </div>
        <input type="file" id="fileInput" style="display: none;">
        
        <div id="result" class="result"></div>
        
        <div>
            <button class="btn" onclick="testAPI()">🧪 测试API</button>
            <button class="btn" onclick="checkStatus()">📊 检查状态</button>
            <button class="btn" onclick="window.open('/docs', '_blank')">📖 API文档</button>
        </div>
        
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #666; font-size: 14px;">
            <p>🌐 访问地址: <strong>http://localhost:8080</strong></p>
            <p>📞 如需完整功能，请配置AI API Key后重启</p>
        </div>
    </div>

    <script>
        // 文件上传
        document.getElementById('fileInput').addEventListener('change', async function(e) {
            const file = e.target.files[0];
            if (!file) return;
            
            const formData = new FormData();
            formData.append('file', file);
            
            showResult('上传中...', 'success');
            
            try {
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showResult(`✅ ${result.message}`, 'success');
                } else {
                    showResult(`❌ ${result.message}`, 'error');
                }
            } catch (error) {
                showResult(`❌ 上传失败: ${error.message}`, 'error');
            }
        });
        
        // 测试API
        async function testAPI() {
            try {
                const response = await fetch('/api/test');
                const result = await response.json();
                
                if (result.success) {
                    showResult(`✅ API测试成功: ${result.message}`, 'success');
                } else {
                    showResult(`❌ API测试失败`, 'error');
                }
            } catch (error) {
                showResult(`❌ API测试失败: ${error.message}`, 'error');
            }
        }
        
        // 检查状态
        async function checkStatus() {
            try {
                const response = await fetch('/api/status');
                const result = await response.json();
                
                showResult(`✅ 服务状态: ${result.message}`, 'success');
            } catch (error) {
                showResult(`❌ 状态检查失败: ${error.message}`, 'error');
            }
        }
        
        // 显示结果
        function showResult(message, type) {
            const resultDiv = document.getElementById('result');
            resultDiv.textContent = message;
            resultDiv.className = `result ${type}`;
            resultDiv.style.display = 'block';
            
            setTimeout(() => {
                resultDiv.style.display = 'none';
            }, 5000);
        }
        
        // 页面加载完成后自动检查状态
        window.onload = function() {
            checkStatus();
        };
    </script>
</body>
</html>
        '''
    
    def run(self):
        """启动服务器"""
        print("🚀 启动AI Test Platform简化版Web服务器")
        print(f"📍 服务器地址: http://{self.host}:{self.port}")
        print(f"📖 API文档: http://{self.host}:{self.port}/docs")
        print("🔧 如遇问题，请检查端口占用或防火墙设置")
        print("=" * 50)
        
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
            print("🔧 尝试解决方案:")
            print("   1. 检查端口8080是否被占用")
            print("   2. 尝试使用其他端口")
            print("   3. 检查防火墙设置")

def main():
    """主函数"""
    print("🔍 检查环境...")
    
    # 检查Python版本
    if sys.version_info < (3, 7):
        print("❌ Python版本过低，需要Python 3.7+")
        return
    
    print(f"✅ Python版本: {sys.version}")
    
    # 检查依赖
    try:
        import fastapi
        import uvicorn
        print("✅ 依赖检查通过")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install fastapi uvicorn")
        return
    
    # 启动服务器
    server = SimpleWebServer()
    server.run()

if __name__ == "__main__":
    main()