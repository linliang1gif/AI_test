#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 路由模块 - 提供 AI 生成测试用例和脚本的接口
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
import json
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai.ai_client import get_ai_client

# 导入 SVN 工具
try:
    from utils.svn_utils import svn_downloader
    from utils.document_parser import parse_document
    SVN_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  SVN 工具导入失败: {e}")
    SVN_AVAILABLE = False

router = APIRouter()


class TestCaseGenerate(BaseModel):
    """测试用例生成请求"""
    requirement: str
    module: Optional[str] = "默认模块"
    count: Optional[int] = 5
    provider: Optional[str] = None


class TestCase(BaseModel):
    """测试用例"""
    title: str
    module: Optional[str] = None
    priority: Optional[str] = None
    steps: List[str]
    expected: str


class ScriptGenerate(BaseModel):
    """测试脚本生成请求"""
    testcase: TestCase
    framework: Optional[str] = "pytest"
    provider: Optional[str] = None


class SVNTestCaseGenerate(BaseModel):
    """从 SVN 生成测试用例请求"""
    svn_url: str
    svn_username: Optional[str] = None
    svn_password: Optional[str] = None
    module: Optional[str] = "默认模块"
    count: Optional[int] = 100
    provider: Optional[str] = None


@router.post("/ai/generate-testcases")
async def generate_testcases(request: TestCaseGenerate):
    """
    AI 生成测试用例
    
    根据需求文档使用 AI 生成测试用例
    """
    try:
        # 获取 AI 客户端
        use_ollama = request.provider == "ollama" if request.provider else None
        use_mock = request.provider == "mock" if request.provider else None
        
        client = get_ai_client(use_ollama=use_ollama, use_mock=use_mock)
        
        # 构建提示词
        prompt = f"""请为以下需求生成{request.count}个测试用例，返回JSON数组格式：

需求：
{request.requirement}

模块：{request.module}

返回格式（必须是有效的JSON数组）：
[
  {{
    "title": "测试用例标题",
    "module": "{request.module}",
    "priority": "high/medium/low",
    "steps": ["步骤1", "步骤2", "步骤3"],
    "expected": "预期结果描述"
  }}
]

注意：
1. 只返回JSON数组，不要有其他文字
2. 确保JSON格式正确
3. 每个测试用例都要有完整的字段
"""
        
        system_prompt = "你是一个专业的测试工程师，擅长根据需求生成高质量的测试用例。"
        
        # 调用 AI
        response = client.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=2000
        )
        
        # 解析响应
        try:
            # 提取 JSON 部分
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0].strip()
            elif '```' in response:
                response = response.split('```')[1].split('```')[0].strip()
            
            # 查找 JSON 数组
            start = response.find('[')
            end = response.rfind(']') + 1
            
            if start != -1 and end > 0:
                json_str = response[start:end]
                testcases = json.loads(json_str)
            else:
                # 如果没有找到数组，尝试直接解析
                testcases = json.loads(response)
            
            # 确保是列表
            if not isinstance(testcases, list):
                testcases = [testcases]
            
            return {
                "success": True,
                "testcases": testcases,
                "count": len(testcases)
            }
            
        except json.JSONDecodeError as e:
            # JSON 解析失败，返回默认测试用例
            print(f"JSON 解析失败: {e}")
            print(f"原始响应: {response[:500]}")
            
            return {
                "success": True,
                "testcases": [
                    {
                        "title": "基本功能测试",
                        "module": request.module,
                        "priority": "high",
                        "steps": ["执行基本操作", "验证结果"],
                        "expected": "功能正常"
                    }
                ],
                "count": 1,
                "warning": "AI 响应格式不正确，返回默认测试用例"
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成测试用例失败: {str(e)}")


@router.post("/ai/generate-testcases-from-svn")
async def generate_testcases_from_svn(request: SVNTestCaseGenerate):
    """
    从 SVN 下载需求文档并生成测试用例
    
    支持从 SVN 仓库直接读取需求文档（.docx, .txt, .md, .pdf）并生成测试用例
    """
    if not SVN_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="SVN 功能不可用，请检查 svn_utils 和 document_parser 模块"
        )
    
    try:
        # 1. 从 SVN 下载文件
        print(f"📥 开始从 SVN 下载文件: {request.svn_url}")
        success, file_path, error = svn_downloader.download(
            svn_url=request.svn_url,
            username=request.svn_username,
            password=request.svn_password
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=f"SVN 下载失败: {error}")
        
        print(f"✅ 文件下载成功: {file_path}")
        
        # 2. 解析文档内容
        try:
            content = parse_document(file_path)
            print(f"✅ 文档解析成功，内容长度: {len(content)} 字符")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"文档解析失败: {str(e)}")
        
        # 3. 使用 AI 生成测试用例
        use_ollama = request.provider == "ollama" if request.provider else None
        use_mock = request.provider == "mock" if request.provider else None
        
        client = get_ai_client(use_ollama=use_ollama, use_mock=use_mock)
        
        # 根据内容长度调整生成数量
        content_length = len(content)
        if content_length > 5000:
            target_count = request.count or 150
            content_preview = content[:8000]
            max_tokens = 12000
        elif content_length > 3000:
            target_count = request.count or 100
            content_preview = content[:5000]
            max_tokens = 8000
        else:
            target_count = request.count or 50
            content_preview = content[:3000]
            max_tokens = 6000
        
        # 构建提示词
        prompt = f"""请为以下需求文档生成{target_count}个测试用例，返回JSON数组格式：

需求文档：
{content_preview}

模块：{request.module}

测试用例必须覆盖以下维度:
1. 功能测试 - 正常流程、核心功能、业务规则
2. 边界测试 - 最小值/最大值、临界值、空值、超长数据
3. 异常测试 - 非法输入、错误参数、异常状态
4. 安全测试 - SQL注入、XSS攻击、权限控制
5. 性能测试 - 响应时间、并发处理
6. 兼容性测试 - 不同浏览器、设备、分辨率

返回格式（必须是有效的JSON数组）：
[
  {{
    "title": "测试用例标题",
    "module": "{request.module}",
    "priority": "high/medium/low",
    "steps": ["步骤1", "步骤2", "步骤3", "步骤4", "步骤5"],
    "expected": "预期结果描述",
    "type": "功能测试/边界测试/异常测试/安全测试/性能测试/兼容性测试"
  }}
]

注意：
1. 只返回JSON数组，不要有其他文字
2. 确保JSON格式正确
3. 每个测试用例都要有完整的字段
4. 测试步骤至少5步，要具体可执行
5. 测试数据要具体（如: test@example.com），不要用"有效数据"这种泛指
"""
        
        system_prompt = """你是一个专业的测试工程师，擅长根据需求生成高质量的测试用例。
你必须严格遵循 Skill 规范：
- 每个模块至少生成 100 个测试用例
- 覆盖 6 个测试维度（功能、边界、异常、安全、性能、兼容性）
- 每个测试点至少 20 个场景
- 每个场景至少 5 个测试用例
- 测试步骤至少 5 步且具体可执行
- 测试数据必须是具体示例，不能是泛指"""
        
        # 调用 AI
        print(f"🤖 开始 AI 生成，目标: {target_count} 个测试用例")
        response = client.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=max_tokens
        )
        
        # 解析响应
        try:
            # 提取 JSON 部分
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0].strip()
            elif '```' in response:
                response = response.split('```')[1].split('```')[0].strip()
            
            # 查找 JSON 数组
            start = response.find('[')
            end = response.rfind(']') + 1
            
            if start != -1 and end > 0:
                json_str = response[start:end]
                testcases = json.loads(json_str)
            else:
                testcases = json.loads(response)
            
            # 确保是列表
            if not isinstance(testcases, list):
                testcases = [testcases]
            
            print(f"✅ AI 生成成功: {len(testcases)} 个测试用例")
            
            # 4. 清理临时文件
            try:
                import os
                os.unlink(file_path)
                print(f"🗑️  已删除临时文件: {file_path}")
            except:
                pass
            
            return {
                "success": True,
                "testcases": testcases,
                "count": len(testcases),
                "source": "svn",
                "svn_url": request.svn_url,
                "document_length": content_length
            }
            
        except json.JSONDecodeError as e:
            print(f"JSON 解析失败: {e}")
            print(f"原始响应: {response[:500]}")
            
            return {
                "success": False,
                "error": "AI 响应格式不正确",
                "detail": str(e)
            }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成测试用例失败: {str(e)}")


@router.post("/ai/generate-script")
async def generate_script(request: ScriptGenerate):
    """
    AI 生成测试脚本
    
    根据测试用例使用 AI 生成自动化测试脚本
    """
    try:
        # 获取 AI 客户端
        use_ollama = request.provider == "ollama" if request.provider else None
        use_mock = request.provider == "mock" if request.provider else None
        
        client = get_ai_client(use_ollama=use_ollama, use_mock=use_mock)
        
        # 构建提示词
        steps_text = "\n".join([f"{i+1}. {step}" for i, step in enumerate(request.testcase.steps)])
        
        prompt = f"""请为以下测试用例生成{request.framework}自动化测试脚本：

测试用例：
标题：{request.testcase.title}
模块：{request.testcase.module}
优先级：{request.testcase.priority}

测试步骤：
{steps_text}

预期结果：
{request.testcase.expected}

要求：
1. 使用{request.framework}框架
2. 包含必要的导入语句
3. 包含测试类和测试方法
4. 添加适当的断言
5. 添加注释说明
6. 代码要完整可运行

请直接返回Python代码，不要有其他说明文字。
"""
        
        system_prompt = f"你是一个专业的测试开发工程师，擅长编写{request.framework}自动化测试脚本。"
        
        # 调用 AI
        response = client.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.2,
            max_tokens=1500
        )
        
        # 提取代码部分
        if '```python' in response:
            script = response.split('```python')[1].split('```')[0].strip()
        elif '```' in response:
            script = response.split('```')[1].split('```')[0].strip()
        else:
            script = response.strip()
        
        return {
            "success": True,
            "script": script,
            "framework": request.framework
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成测试脚本失败: {str(e)}")


@router.get("/ai/providers")
async def get_ai_providers():
    """
    获取可用的 AI 提供商列表
    """
    from config.config import get_config
    
    config = get_config()
    
    providers = [
        {
            "id": "deepseek",
            "name": "DeepSeek",
            "status": "available" if config.ai.deepseek_api_key else "unavailable",
            "models": config.get_available_models("deepseek")
        },
        {
            "id": "openai",
            "name": "智谱 BigModel",
            "status": "available" if config.ai.openai_api_key else "unavailable",
            "models": config.get_available_models("openai") or ["glm-4-flash", "glm-4", "glm-3-turbo"]
        },
        {
            "id": "ollama",
            "name": "Ollama (本地)",
            "status": "available",
            "models": config.get_available_models("ollama") or config.ai.ollama_models
        },
        {
            "id": "mock",
            "name": "Mock (测试)",
            "status": "available",
            "models": ["mock"]
        }
    ]
    
    return {
        "providers": providers,
        "default": config.ai.default_provider
    }


@router.get("/ai/config")
async def get_ai_config():
    """
    获取 AI 配置信息
    """
    from config.config import get_config
    
    config = get_config()
    
    return {
        "default_provider": config.ai.default_provider,
        "default_model": config.ai.default_model,
        "module_configs": config.get_all_module_configs(),
        "available_modules": [
            {
                "id": "testcase_generation",
                "name": "测试用例生成",
                "description": "从需求文档生成测试用例"
            },
            {
                "id": "script_generation",
                "name": "测试脚本生成",
                "description": "从测试用例生成自动化脚本"
            },
            {
                "id": "swagger_analysis",
                "name": "Swagger 分析",
                "description": "分析 Swagger 文档生成测试用例"
            },
            {
                "id": "test_optimization",
                "name": "测试优化",
                "description": "优化测试用例和测试策略"
            }
        ]
    }


@router.post("/ai/config/update")
async def update_ai_config(request: dict):
    """
    更新 AI 配置（立即生效，无需重启）
    """
    import os
    from pathlib import Path
    
    try:
        env_path = Path(__file__).parent.parent / ".env"
        
        # 读取现有配置
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 更新配置
        updates = request.get("updates", {})
        new_lines = []
        updated_keys = set()
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith('#'):
                new_lines.append(line)
                continue
            
            if '=' in line:
                key = line.split('=')[0].strip()
                if key in updates:
                    new_lines.append(f"{key}={updates[key]}\n")
                    updated_keys.add(key)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        # 添加新的配置项
        for key, value in updates.items():
            if key not in updated_keys:
                new_lines.append(f"{key}={value}\n")
        
        # 写回文件
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        # 重新加载配置，使其立即生效
        from config.config import reload_config
        reload_config()
        
        return {
            "success": True,
            "message": "配置已更新并立即生效"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")
