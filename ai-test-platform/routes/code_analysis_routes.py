#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
代码分析路由 - 需求-代码对比、白盒测试分析
"""

import json
import sys
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.code_analyzer import scan_code_directory, summarize_code_analysis
from utils.req_code_diff import run_req_code_diff

try:
    from utils.document_parser import parse_document_structured, parse_axure_folder_structured
    DOC_PARSER_AVAILABLE = True
except ImportError:
    DOC_PARSER_AVAILABLE = False

try:
    from ai.ai_client import get_ai_client
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

router = APIRouter()


# ── 请求模型 ──

class CodeScanRequest(BaseModel):
    code_path: str
    languages: Optional[list] = None


class ReqCodeDiffRequest(BaseModel):
    requirement_path: str          # 需求文档路径或 Axure 文件夹路径
    code_path: str                 # 代码目录路径
    languages: Optional[list] = None
    use_ai: bool = True            # 是否用 AI 对比（否则纯规则匹配）
    provider: Optional[str] = None
    model: Optional[str] = None


# ── 代码扫描 ──

@router.post("/code-analysis/scan")
async def scan_code(request: CodeScanRequest):
    """扫描代码目录，返回结构化分析结果"""
    code_path = Path(request.code_path)
    if not code_path.is_dir():
        raise HTTPException(status_code=400, detail=f"代码目录不存在: {request.code_path}")

    try:
        analysis = scan_code_directory(str(code_path), request.languages)
        summary = summarize_code_analysis(analysis)
        return {
            "success": True,
            "analysis": analysis,
            "summary_text": summary,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"代码扫描失败: {str(e)}")


# ── 需求-代码对比 ──

@router.post("/code-analysis/diff")
async def req_code_diff(request: ReqCodeDiffRequest):
    """
    需求-代码对比分析

    流程: 解析需求文档 + 扫描代码 → AI/规则对比 → 差异报告 + Bug 清单
    """
    # 1. 解析需求
    req_path = Path(request.requirement_path)
    if not req_path.exists():
        raise HTTPException(status_code=400, detail=f"需求路径不存在: {request.requirement_path}")

    if not DOC_PARSER_AVAILABLE:
        raise HTTPException(status_code=503, detail="文档解析模块不可用")

    try:
        if req_path.is_dir():
            # Axure 文件夹
            req_data = parse_axure_folder_structured(str(req_path))
        else:
            # 单个文档
            req_data = parse_document_structured(str(req_path))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"需求文档解析失败: {str(e)}")

    # 2. 扫描代码
    code_path = Path(request.code_path)
    if not code_path.is_dir():
        raise HTTPException(status_code=400, detail=f"代码目录不存在: {request.code_path}")

    try:
        code_analysis = scan_code_directory(str(code_path), request.languages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"代码扫描失败: {str(e)}")

    # 3. 对比
    ai_client = None
    if request.use_ai and AI_AVAILABLE:
        try:
            ai_client = get_ai_client(provider=request.provider)
        except Exception as e:
            print(f"⚠️ AI 客户端初始化失败，使用规则匹配: {e}")

    try:
        diff_result = run_req_code_diff(req_data, code_analysis, ai_client=ai_client)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对比分析失败: {str(e)}")

    return {
        "success": True,
        "requirement_stats": req_data.get("stats", {}),
        "code_stats": code_analysis["stats"],
        "diff": diff_result,
        "code_summary": summarize_code_analysis(code_analysis),
    }


# ── 白盒测试用例生成 ──

class WhiteboxRequest(BaseModel):
    code_path: str
    languages: Optional[list] = None
    focus_files: Optional[list] = None   # 聚焦特定文件
    provider: Optional[str] = None
    model: Optional[str] = None
    count: int = 50


@router.post("/code-analysis/whitebox-testcases")
async def generate_whitebox_testcases(request: WhiteboxRequest):
    """
    白盒测试：基于代码结构（分支/条件/路由）生成测试用例
    """
    code_path = Path(request.code_path)
    if not code_path.is_dir():
        raise HTTPException(status_code=400, detail=f"代码目录不存在: {request.code_path}")

    if not AI_AVAILABLE:
        raise HTTPException(status_code=503, detail="AI 模块不可用")

    try:
        analysis = scan_code_directory(str(code_path), request.languages)
        code_summary = summarize_code_analysis(analysis)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"代码扫描失败: {str(e)}")

    # 聚焦特定文件
    if request.focus_files:
        focus_set = set(request.focus_files)
        analysis["conditions"] = [c for c in analysis["conditions"] if c["file"] in focus_set]
        analysis["functions"] = [f for f in analysis["functions"] if f["file"] in focus_set]

    # 构建 prompt
    conditions_text = "\n".join(
        f"  - if ({c['expression'][:80]}) [{c['file']}:{c['line']}]"
        for c in analysis["conditions"][:50]
    )

    routes_text = "\n".join(
        f"  - {r['method']} {r['path']} → {r['handler']} [{r['file']}]"
        for r in analysis["routes"][:30]
    )

    prompt = f"""基于以下代码结构生成 {request.count} 个白盒测试用例。

## 代码概览
{code_summary[:6000]}

## 条件分支 ({len(analysis['conditions'])} 个)
{conditions_text}

## API 路由 ({len(analysis['routes'])} 个)
{routes_text}

请生成覆盖以上条件分支和 API 路由的测试用例，返回 JSON 数组:
[
  {{
    "title": "测试用例标题",
    "module": "所属模块",
    "type": "白盒测试/分支覆盖/路径覆盖",
    "priority": "high/medium/low",
    "target": "测试目标（哪个条件/函数/路由）",
    "precondition": "前置条件",
    "steps": ["步骤1", "步骤2", ...],
    "expected": "预期结果",
    "coverage_type": "条件覆盖/分支覆盖/路径覆盖/边界覆盖"
  }}
]

要求:
1. 覆盖每个条件分支的 true/false 两种情况
2. 覆盖每个 API 路由的正常和异常情况
3. 测试数据具体，步骤可执行
"""

    system_prompt = """你是白盒测试专家，擅长根据代码结构设计测试用例。
重点覆盖：条件分支(if/else)、循环边界、API 路由、异常处理。"""

    try:
        client = get_ai_client(provider=request.provider)
        response = client.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=8000,
        )

        from routes.ai_routes import _parse_ai_testcase_response
        testcases = _parse_ai_testcase_response(response)

        return {
            "success": True,
            "testcases": testcases,
            "count": len(testcases),
            "code_stats": analysis["stats"],
            "conditions_analyzed": len(analysis["conditions"]),
            "routes_analyzed": len(analysis["routes"]),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"白盒测试用例生成失败: {str(e)}")
