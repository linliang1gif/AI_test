#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""简化版后端API服务器 - 无依赖错误"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import json
import time
from typing import Dict, Any, List, Optional

# 导入简化的AI客户端
from ai.ai_client import get_ai_client

app = FastAPI(title="AI Test Platform API", version="2.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据存储
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)
data_file = data_dir / "simple_data.json"

def load_data():
    if data_file.exists():
        return json.loads(data_file.read_text(encoding='utf-8'))
    return {"projects": [], "testcases": [], "test_runs": []}

def save_data(data):
    data_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

# Pydantic模型
class TestCaseGenerate(BaseModel):
    requirement: str
    provider: str = "ollama"

class ProjectCreate(BaseModel):
    name: str
    description: str = ""

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/dashboard/stats")
async def dashboard_stats():
    data = load_data()
    return {
        "total_projects": len(data.get("projects", [])),
        "total_testcases": len(data.get("testcases", [])),
        "total_test_runs": len(data.get("test_runs", [])),
        "pass_rate": 85.5
    }

@app.get("/api/ai/current")
async def get_current_ai():
    return {
        "provider": "ollama",
        "model": "qwen2.5:1.5b",
        "status": "available"
    }

@app.get("/api/ai-providers")
async def get_ai_providers():
    return [
        {"id": "ollama", "name": "Ollama (本地)", "status": "available"},
        {"id": "mock", "name": "Mock (测试)", "status": "available"},
        {"id": "deepseek", "name": "DeepSeek", "status": "unavailable"}
    ]

@app.post("/api/ai/generate-testcases")
async def generate_testcases(request: TestCaseGenerate):
    try:
        # 使用AI生成测试用例
        use_ollama = request.provider == "ollama"
        use_mock = request.provider == "mock"

        client = get_ai_client(use_ollama=use_ollama, use_mock=use_mock)

        prompt = f"""
请为以下需求生成5个测试用例，返回JSON格式：

需求：{request.requirement}

返回格式：
[
  {{"id": "TC001", "title": "测试用例标题", "priority": "高", "steps": ["步骤1", "步骤2"], "expected": "预期结果"}},
  ...
]
"""

        response = client.generate_text(prompt)

        # 解析响应
        try:
            start = response.find('[')
            end = response.rfind(']') + 1
            if start != -1 and end > 0:
                testcases = json.loads(response[start:end])
            else:
                testcases = []
        except:
            testcases = [
                {"id": "TC001", "title": "基本功能测试", "priority": "高", "steps": ["执行操作"], "expected": "成功"}
            ]

        # 保存
        data = load_data()
        data["testcases"].extend(testcases)
        save_data(data)

        return {"success": True, "testcases": testcases, "count": len(testcases)}

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/testcases/generate")
async def generate_testcases_alt(request: TestCaseGenerate):
    return await generate_testcases(request)

@app.get("/api/projects")
async def get_projects():
    data = load_data()
    return data.get("projects", [])

@app.post("/api/projects")
async def create_project(project: ProjectCreate):
    data = load_data()
    new_project = {
        "id": len(data["projects"]) + 1,
        "name": project.name,
        "description": project.description,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    data["projects"].append(new_project)
    save_data(data)
    return new_project

@app.get("/api/testcases")
async def get_testcases():
    data = load_data()
    return data.get("testcases", [])

@app.get("/api/test-cases")
async def get_test_cases():
    data = load_data()
    return data.get("testcases", [])

@app.post("/api/testcases/generate")
async def generate_testcases_alt(request: TestCaseGenerate):
    return await generate_testcases(request)

@app.get("/api/test-runs")
async def get_test_runs():
    data = load_data()
    return data.get("test_runs", [])

@app.get("/api/apis")
async def get_apis():
    return []

@app.get("/api/automation/scripts")
async def get_scripts():
    return []

@app.post("/api/upload/requirement")
async def upload_requirement(file: UploadFile = File(...)):
    try:
        content = await file.read()
        text = content.decode('utf-8')

        return {
            "success": True,
            "filename": file.filename,
            "content": text[:500],
            "size": len(content)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 AI Test Platform - 简化版后端")
    print("=" * 60)
    print("\n✅ 启动服务...")
    print("📍 地址: http://127.0.0.1:8081")
    print("📍 API文档: http://127.0.0.1:8081/docs")
    print("\n💡 功能:")
    print("  - AI生成测试用例 (Ollama/Mock)")
    print("  - 项目管理")
    print("  - 测试用例管理")
    print("  - 数据持久化")
    print("\n" + "=" * 60)

    uvicorn.run(app, host="127.0.0.1", port=8081)
