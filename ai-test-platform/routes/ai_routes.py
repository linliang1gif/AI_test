#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 路由模块 - 提供 AI 生成测试用例和脚本的接口
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query, Depends
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import json
import logging
import sys
import tempfile
import os
import uuid
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from database import get_db
from database.models import TestCase as TestCaseDB

from ai.ai_client import get_ai_client

# 导入文档解析工具
try:
    from utils.document_parser import parse_document, parse_document_structured, parse_axure_folder, parse_axure_folder_structured
    DOC_PARSER_AVAILABLE = True
except ImportError as e:
    logger.info(f"  文档解析工具导入失败: {e}")
    DOC_PARSER_AVAILABLE = False

# 导入知识库检索
try:
    from knowledge.manual_retriever import retrieve_manual_context, retrieve_for_modules
    KB_AVAILABLE = True
except ImportError as e:
    logger.info(f"  知识库检索导入失败: {e}")
    KB_AVAILABLE = False

# 导入 SVN 工具
try:
    from utils.svn_utils import svn_downloader
    SVN_AVAILABLE = True
except ImportError as e:
    logger.info(f"  SVN 工具导入失败: {e}")
    SVN_AVAILABLE = False

router = APIRouter()


def _scan_complete_objects(text: str) -> list:
    """在被截断的 JSON 数组文本里逐个扫描完整的 {...} 对象，返回已成功解析的对象列表。

    用于 AI 输出被 max_tokens 截断的场景。
    """
    items = []
    depth = 0
    in_str = False
    escape = False
    obj_start = -1
    for i, ch in enumerate(text):
        if escape:
            escape = False
            continue
        if ch == '\\' and in_str:
            escape = True
            continue
        if ch == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if ch == '{':
            if depth == 0:
                obj_start = i
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0 and obj_start >= 0:
                chunk = text[obj_start:i + 1]
                try:
                    items.append(json.loads(chunk))
                except json.JSONDecodeError:
                    pass
                obj_start = -1
    return items


def _parse_ai_testcase_response(response: str) -> list:
    """健壮地解析 AI 返回的测试用例 JSON，支持多种格式"""
    # 1. 去掉 markdown 代码块
    if '```json' in response:
        response = response.split('```json')[1].split('```')[0].strip()
    elif '```' in response:
        parts = response.split('```')
        if len(parts) >= 3:
            response = parts[1].strip()

    # 2. 尝试找数组
    start = response.find('[')
    end = response.rfind(']') + 1
    if start != -1 and end > start:
        try:
            arr = json.loads(response[start:end])
            if isinstance(arr, list) and len(arr) > 0:
                return arr
        except json.JSONDecodeError:
            pass

    # 3. 尝试解析整体
    try:
        obj = json.loads(response)
    except json.JSONDecodeError:
        # 4. 尝试修复截断的 JSON（末尾缺 ] 或 }）
        for suffix in [']', ']}', ']\n}', '"}]', '"}]}']:
            try:
                obj = json.loads(response + suffix)
                break
            except json.JSONDecodeError:
                continue
        else:
            # 5. 兜底：截断 fallback - 逐个扫回已生成的完整 {...} 对象
            arr_start = response.find('[')
            scan_text = response[arr_start + 1:] if arr_start >= 0 else response
            partial = _scan_complete_objects(scan_text)
            if partial:
                logger.info(f"⚠️ AI 响应被截断，已 fallback 解析出 {len(partial)} 条完整用例")
                return partial
            raise json.JSONDecodeError("无法解析 AI 响应", response[:200], 0)

    # 6. 如果是 dict，尝试提取其中的数组字段
    if isinstance(obj, dict):
        for key in ('testcases', 'test_cases', 'data', 'cases', 'results'):
            if key in obj and isinstance(obj[key], list):
                return obj[key]
        # 如果 dict 本身看起来像单条用例
        if 'title' in obj:
            return [obj]
        raise json.JSONDecodeError("AI 返回了对象但未找到用例数组", str(list(obj.keys())), 0)

    if isinstance(obj, list):
        return obj

    return [obj]


def _save_testcases_to_db(db: Session, testcases: list, source: str = "ai_generated") -> list:
    """将 AI 生成的测试用例列表写入数据库，返回保存的 id 列表"""
    saved_ids = []
    for tc in testcases:
        tc_id = f"TC_AI_{uuid.uuid4().hex[:8]}"
        row = TestCaseDB(
            id=tc_id,
            title=tc.get("title", "AI生成用例"),
            module=tc.get("module", ""),
            priority=tc.get("priority", "medium"),
            status="pending",
            steps=tc.get("steps", []),
            expected=tc.get("expected", ""),
            data_type=tc.get("type", "functional"),
            expected_behavior="success",
            execution_config={},
            assertions=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by="ai",
            source=source,
            case_type="functional",
            tags=[f"test_point:{tc.get('test_point', '')}"] if tc.get("test_point") else [],
        )
        db.add(row)
        saved_ids.append(tc_id)
    db.commit()
    return saved_ids


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
        
        # 检索知识库上下文
        kb_ref = ""
        if KB_AVAILABLE:
            try:
                ctx = retrieve_manual_context(request.requirement[:500], n_results=3)
                if ctx:
                    kb_ref = f"\n\n【操作手册参考】:\n{ctx[:3000]}\n"
            except Exception as _e:
                logger.warning("[P1] knowledge base retrieve fallback: %s", _e)

        # 构建提示词
        prompt = f"""请为以下需求生成{request.count}个测试用例，返回JSON数组格式：

需求：
{request.requirement}
{kb_ref}
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
        response = await asyncio.to_thread(
            client.generate_text,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=2000,
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
            logger.info(f"JSON 解析失败: {e}")
            logger.info(f"原始响应: {response[:500]}")
            
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
        logger.info(f"📥 开始从 SVN 下载文件: {request.svn_url}")
        success, file_path, error = svn_downloader.download(
            svn_url=request.svn_url,
            username=request.svn_username,
            password=request.svn_password
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=f"SVN 下载失败: {error}")
        
        logger.info(f"✅ 文件下载成功: {file_path}")
        
        # 2. 解析文档内容
        try:
            content = parse_document(file_path)
            logger.info(f"✅ 文档解析成功，内容长度: {len(content)} 字符")
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
        
        # 检索知识库上下文
        kb_ref = ""
        if KB_AVAILABLE:
            try:
                ctx = retrieve_manual_context(content[:500], n_results=3)
                if ctx:
                    kb_ref = f"\n\n【操作手册参考】:\n{ctx[:3000]}\n"
            except Exception as _e:
                logger.warning("[P1] knowledge base retrieve fallback: %s", _e)

        # 构建提示词
        prompt = f"""请为以下需求文档生成{target_count}个测试用例，返回JSON数组格式：

需求文档：
{content_preview}
{kb_ref}
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
        logger.info(f"🤖 开始 AI 生成，目标: {target_count} 个测试用例")
        response = await asyncio.to_thread(
            client.generate_text,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=max_tokens,
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
            
            logger.info(f"✅ AI 生成成功: {len(testcases)} 个测试用例")
            
            # 4. 清理临时文件
            try:
                import os
                os.unlink(file_path)
                logger.info("🗑️  已删除临时文件: %s", file_path)
            except Exception as _e:
                logger.debug("删除临时文件失败 %s: %s", file_path, _e)
            
            return {
                "success": True,
                "testcases": testcases,
                "count": len(testcases),
                "source": "svn",
                "svn_url": request.svn_url,
                "document_length": content_length
            }
            
        except json.JSONDecodeError as e:
            logger.info(f"JSON 解析失败: {e}")
            logger.info(f"原始响应: {response[:500]}")
            
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
        response = await asyncio.to_thread(
            client.generate_text,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.2,
            max_tokens=1500,
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
            },
            {
                "id": "case_review",
                "name": "AI 用例评审",
                "description": "对测试用例进行质量评审、漏测分析和优化建议"
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


# ==================== 文件上传生成测试用例 ====================

ALLOWED_EXTENSIONS = {'.html', '.htm', '.txt', '.md', '.docx', '.doc', '.pdf'}


def _save_upload_file(upload: UploadFile) -> str:
    """保存上传文件到临时目录，返回路径"""
    suffix = Path(upload.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {suffix}，支持: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    fd, tmp_path = tempfile.mkstemp(suffix=suffix)
    try:
        content = upload.file.read()
        with os.fdopen(fd, 'wb') as f:
            f.write(content)
    except Exception:
        os.close(fd)
        raise
    return tmp_path


@router.post("/ai/upload-preview")
async def upload_and_preview(file: UploadFile = File(...)):
    """
    上传需求文档并返回结构化预览（模块/功能点/规则/字段）

    支持格式: .html, .htm, .txt, .md, .docx, .pdf
    前端用此结果展示预览，用户确认后再调 /ai/generate-testcases-from-file 生成用例
    """
    if not DOC_PARSER_AVAILABLE:
        raise HTTPException(status_code=503, detail="文档解析模块不可用")

    tmp_path = _save_upload_file(file)
    try:
        structured = parse_document_structured(tmp_path)
        return {
            "success": True,
            "filename": file.filename,
            "structured": {
                "modules": structured["modules"],
                "features": structured["features"],
                "rules": structured["rules"],
                "fields": structured["fields"],
                "axure_notes": structured["axure_notes"],
                "stats": structured["stats"],
            },
            "raw_text_length": len(structured["raw_text"]),
            "raw_text_preview": structured["raw_text"][:3000],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文档解析失败: {str(e)}")
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


class FolderPreviewRequest(BaseModel):
    folder_path: str


@router.post("/ai/folder-preview")
async def folder_preview(request: FolderPreviewRequest):
    """
    解析本地 Axure 文件夹并返回结构化预览（模块/功能点/规则/字段/注释）
    """
    if not DOC_PARSER_AVAILABLE:
        raise HTTPException(status_code=503, detail="文档解析模块不可用")

    folder = Path(request.folder_path)
    if not folder.is_dir():
        raise HTTPException(status_code=400, detail=f"文件夹不存在: {request.folder_path}")

    try:
        structured = parse_axure_folder_structured(str(folder))
        return {
            "success": True,
            "filename": folder.name,
            "structured": {
                "modules": structured["modules"],
                "features": structured["features"],
                "rules": structured["rules"],
                "fields": structured["fields"],
                "axure_notes": structured["axure_notes"],
                "stats": structured["stats"],
            },
            "raw_text_length": len(structured["raw_text"]),
            "raw_text_preview": structured["raw_text"][:3000],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文件夹解析失败: {str(e)}")


@router.post("/ai/generate-testcases-from-file")
async def generate_testcases_from_file(
    file: UploadFile = File(...),
    module: str = Form("默认模块"),
    count: int = Form(100),
    provider: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
    extra_requirements: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    上传需求文档（HTML/TXT/MD/DOCX/PDF），AI 提取测试点并生成功能测试用例

    流程: 上传文件 → 解析文本 → AI 提取测试点 → AI 生成测试用例
    """
    if not DOC_PARSER_AVAILABLE:
        raise HTTPException(status_code=503, detail="文档解析模块不可用")

    tmp_path = _save_upload_file(file)
    try:
        # 1. 解析文档
        structured = parse_document_structured(tmp_path)
        raw_text = structured["raw_text"]
        stats = structured["stats"]
        logger.info(f"📄 文档解析完成: {file.filename}, {stats}")

        if not raw_text or len(raw_text.strip()) < 10:
            raise HTTPException(status_code=400, detail="文档内容为空或过短，无法生成测试用例")

        # 2. 根据内容长度调整参数
        content_length = len(raw_text)
        if content_length > 8000:
            content_preview = raw_text[:10000]
            base_max_tokens = 16000
        elif content_length > 3000:
            content_preview = raw_text[:6000]
            base_max_tokens = 12000
        else:
            content_preview = raw_text
            base_max_tokens = 8000
        # 根据 count 动态放大 max_tokens（避免 100 条时 JSON 被截断）
        # 每条用例 ~220 tokens + 1500 prompt 开销，cap 32000
        max_tokens = min(32000, max(base_max_tokens, count * 220 + 1500))

        # 3. 构建增强 prompt（含结构化信息）
        structure_hint = ""
        if structured["modules"]:
            module_names = [m["name"] for m in structured["modules"]]
            structure_hint += f"\n已识别模块: {', '.join(module_names)}"
        if structured["rules"]:
            rules_text = '\n'.join(f"  - {r}" for r in structured["rules"][:20])
            structure_hint += f"\n\n业务规则:\n{rules_text}"
        if structured["fields"]:
            fields_text = ', '.join(f["name"] for f in structured["fields"][:30])
            structure_hint += f"\n\n表单字段: {fields_text}"
        if structured["axure_notes"]:
            notes_text = '\n'.join(f"  - {n}" for n in structured["axure_notes"][:20])
            structure_hint += f"\n\nAxure 需求注释:\n{notes_text}"

        extra_hint = ""
        if extra_requirements:
            extra_hint = f"\n\n额外测试要求:\n{extra_requirements}"

        # 3.5 从知识库检索操作手册上下文
        kb_hint = ""
        if KB_AVAILABLE:
            try:
                # 用模块名 + 原始文本前500字作为检索 query
                query_parts = []
                if structured["modules"]:
                    query_parts.extend([m["name"] for m in structured["modules"][:5]])
                query_parts.append(raw_text[:500])
                kb_query = " ".join(query_parts)

                kb_context = retrieve_manual_context(kb_query, n_results=5)
                if kb_context:
                    kb_hint = f"\n\n【操作手册参考（来自知识库）】:\n{kb_context[:4000]}"
                    logger.info(f"📚 知识库命中: {len(kb_context)} 字符")
            except Exception as e:
                logger.info(f"⚠️ 知识库检索异常: {e}")

        prompt = f"""请为以下需求文档生成{count}个功能测试用例，返回JSON数组格式。

需求文档内容:
{content_preview}
{structure_hint}{extra_hint}{kb_hint}

模块: {module}

测试用例必须覆盖以下维度:
1. 功能测试 - 正常流程、核心功能、业务规则
2. 边界测试 - 最小值/最大值、临界值、空值、超长数据
3. 异常测试 - 非法输入、错误参数、异常状态
4. 安全测试 - SQL注入、XSS攻击、权限控制
5. 兼容性测试 - 不同浏览器、设备

返回格式（必须是有效的JSON数组）:
[
  {{
    "title": "测试用例标题",
    "module": "所属模块",
    "priority": "high/medium/low",
    "test_point": "对应测试点",
    "precondition": "前置条件",
    "steps": ["步骤1", "步骤2", "步骤3", "步骤4", "步骤5"],
    "expected": "预期结果",
    "type": "功能测试/边界测试/异常测试/安全测试/兼容性测试"
  }}
]

注意:
1. 只返回JSON数组，不要有其他文字
2. 每个测试用例必须有完整字段
3. 测试步骤至少5步，要具体可执行
4. 测试数据要具体（如: test@example.com），不要用"有效数据"这种泛指
5. 确保覆盖文档中所有功能点和业务规则，不要遗漏
"""

        system_prompt = """你是一个专业的测试工程师，擅长从需求文档中提取测试点并生成高质量的功能测试用例。
你必须:
- 覆盖文档中提到的所有功能点
- 为每个功能点生成正常、异常、边界测试用例
- 特别关注业务规则和校验逻辑
- 测试步骤具体可执行，测试数据使用真实示例"""

        # 4. 调用 AI
        use_ollama = provider == "ollama" if provider else None
        use_mock = provider == "mock" if provider else None
        client = get_ai_client(use_ollama=use_ollama, use_mock=use_mock, provider=provider)

        use_model = model or getattr(client, 'ai_config', {}).get("model", None) or "deepseek-chat"
        logger.info(f"🤖 AI 生成中，提供商={provider or 'auto'}, 模型={use_model}, 目标: {count} 个测试用例...")
        response = await asyncio.to_thread(
            client.generate_text,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=max_tokens,
            model=use_model,
        )

        # 5. 解析 AI 响应
        try:
            testcases = _parse_ai_testcase_response(response)
            logger.info(f"✅ AI 生成成功: {len(testcases)} 个测试用例")

            # 6. 保存到数据库
            saved_ids = _save_testcases_to_db(db, testcases, source="ai_generated")
            logger.info(f"💾 已保存 {len(saved_ids)} 条用例到数据库")

            return {
                "success": True,
                "testcases": testcases,
                "count": len(testcases),
                "saved_ids": saved_ids,
                "source": "file_upload",
                "filename": file.filename,
                "document_stats": stats,
                "coverage": {
                    "total_modules_in_doc": len(structured["modules"]),
                    "total_features_in_doc": len(structured["features"]),
                    "total_rules_in_doc": len(structured["rules"]),
                    "testcases_generated": len(testcases),
                }
            }

        except json.JSONDecodeError as e:
            logger.info(f"JSON 解析失败: {e}")
            logger.info(f"原始响应: {response[:500]}")
            return {
                "success": False,
                "error": "AI 响应格式不正确",
                "detail": str(e),
                "raw_response_preview": response[:500]
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成测试用例失败: {str(e)}")
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


class FolderRequest(BaseModel):
    folder_path: str
    module: str = "默认模块"
    count: int = 100
    provider: Optional[str] = None
    model: Optional[str] = None
    extra_requirements: Optional[str] = None


@router.post("/ai/generate-testcases-from-folder")
async def generate_testcases_from_folder(request: FolderRequest, db: Session = Depends(get_db)):
    """
    从本地 Axure 文件夹（_files 目录）解析需求并生成功能测试用例

    流程: 读取文件夹 → 解析 data.js + HTML → AI 生成测试用例
    """
    if not DOC_PARSER_AVAILABLE:
        raise HTTPException(status_code=503, detail="文档解析模块不可用")

    folder = Path(request.folder_path)
    if not folder.is_dir():
        raise HTTPException(status_code=400, detail=f"文件夹不存在: {request.folder_path}")

    try:
        # 1. 解析 Axure 文件夹
        structured = parse_axure_folder_structured(str(folder))
        raw_text = structured["raw_text"]
        stats = structured["stats"]
        logger.info(f"📂 Axure 文件夹解析完成: {folder.name}, {stats}")

        if not raw_text or len(raw_text.strip()) < 10:
            raise HTTPException(status_code=400, detail="文件夹内容为空或过短，无法生成测试用例")

        # 2. 内容长度调整
        content_length = len(raw_text)
        if content_length > 8000:
            content_preview = raw_text[:10000]
            base_max_tokens = 16000
        elif content_length > 3000:
            content_preview = raw_text[:6000]
            base_max_tokens = 12000
        else:
            content_preview = raw_text
            base_max_tokens = 8000
        # 根据 count 动态放大 max_tokens（避免 100 条时 JSON 被截断）
        max_tokens = min(32000, max(base_max_tokens, request.count * 220 + 1500))

        # 3. 构建增强 prompt
        structure_hint = ""
        if structured["modules"]:
            module_names = [m["name"] for m in structured["modules"]]
            structure_hint += f"\n已识别模块: {', '.join(module_names)}"
        if structured["rules"]:
            rules_text = '\n'.join(f"  - {r}" for r in structured["rules"][:20])
            structure_hint += f"\n\n业务规则:\n{rules_text}"
        if structured["fields"]:
            fields_text = ', '.join(f["name"] for f in structured["fields"][:30])
            structure_hint += f"\n\n表单字段: {fields_text}"
        if structured["axure_notes"]:
            notes_text = '\n'.join(f"  - {n}" for n in structured["axure_notes"][:30])
            structure_hint += f"\n\nAxure 需求注释:\n{notes_text}"

        extra_hint = ""
        if request.extra_requirements:
            extra_hint = f"\n\n额外测试要求:\n{request.extra_requirements}"

        # 3.5 知识库检索
        kb_hint = ""
        if KB_AVAILABLE:
            try:
                query_parts = [m["name"] for m in structured["modules"][:5]]
                query_parts.append(raw_text[:500])
                kb_context = retrieve_manual_context(" ".join(query_parts), n_results=5)
                if kb_context:
                    kb_hint = f"\n\n【操作手册参考（来自知识库）】:\n{kb_context[:4000]}"
                    logger.info(f"📚 知识库命中: {len(kb_context)} 字符")
            except Exception as e:
                logger.info(f"⚠️ 知识库检索异常: {e}")

        prompt = f"""请为以下需求文档生成{request.count}个功能测试用例，返回JSON数组格式。

需求文档内容:
{content_preview}
{structure_hint}{extra_hint}{kb_hint}

模块: {request.module}

测试用例必须覆盖以下维度:
1. 功能测试 - 正常流程、核心功能、业务规则
2. 边界测试 - 最小值/最大值、临界值、空值、超长数据
3. 异常测试 - 非法输入、错误参数、异常状态
4. 安全测试 - SQL注入、XSS攻击、权限控制
5. 兼容性测试 - 不同浏览器、设备

返回格式（必须是有效的JSON数组）:
[
  {{
    "title": "测试用例标题",
    "module": "所属模块",
    "priority": "high/medium/low",
    "test_point": "对应测试点",
    "precondition": "前置条件",
    "steps": ["步骤1", "步骤2", "步骤3", "步骤4", "步骤5"],
    "expected": "预期结果",
    "type": "功能测试/边界测试/异常测试/安全测试/兼容性测试"
  }}
]

注意:
1. 只返回JSON数组，不要有其他文字
2. 每个测试用例必须有完整字段
3. 测试步骤至少5步，要具体可执行
4. 测试数据要具体（如: test@example.com），不要用"有效数据"这种泛指
5. 确保覆盖文档中所有功能点和业务规则，不要遗漏
"""

        system_prompt = """你是一个专业的测试工程师，擅长从需求文档中提取测试点并生成高质量的功能测试用例。
你必须:
- 覆盖文档中提到的所有功能点
- 为每个功能点生成正常、异常、边界测试用例
- 特别关注业务规则和校验逻辑
- 测试步骤具体可执行，测试数据使用真实示例"""

        # 4. 调用 AI
        use_ollama = request.provider == "ollama" if request.provider else None
        use_mock = request.provider == "mock" if request.provider else None
        client = get_ai_client(use_ollama=use_ollama, use_mock=use_mock, provider=request.provider)

        use_model = request.model or getattr(client, 'ai_config', {}).get("model", None) or "deepseek-chat"
        logger.info(f"🤖 AI 生成中，提供商={request.provider or 'auto'}, 模型={use_model}, 目标: {request.count} 个测试用例...")
        response = await asyncio.to_thread(
            client.generate_text,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=max_tokens,
            model=use_model,
        )

        # 5. 解析 AI 响应
        try:
            testcases = _parse_ai_testcase_response(response)
            logger.info(f"✅ AI 生成成功: {len(testcases)} 个测试用例")

            # 6. 保存到数据库
            saved_ids = _save_testcases_to_db(db, testcases, source="ai_generated")
            logger.info(f"💾 已保存 {len(saved_ids)} 条用例到数据库")

            return {
                "success": True,
                "testcases": testcases,
                "count": len(testcases),
                "saved_ids": saved_ids,
                "source": "axure_folder",
                "folder_name": folder.name,
                "document_stats": stats,
                "coverage": {
                    "total_modules_in_doc": len(structured["modules"]),
                    "total_features_in_doc": len(structured["features"]),
                    "total_rules_in_doc": len(structured["rules"]),
                    "testcases_generated": len(testcases),
                }
            }

        except json.JSONDecodeError as e:
            logger.info(f"JSON 解析失败: {e}")
            logger.info(f"原始响应: {response[:500]}")
            return {
                "success": False,
                "error": "AI 响应格式不正确",
                "detail": str(e),
                "raw_response_preview": response[:500]
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成测试用例失败: {str(e)}")
