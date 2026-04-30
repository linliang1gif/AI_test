#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Swagger/OpenAPI 导入路由
"""

import json

import requests
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from services.swagger_service import SwaggerService
from services.test_case_service import TestCaseService
from schemas.swagger_schemas import (
    SwaggerImportFromUrlRequest,
    SwaggerImportResponse,
    ApiSpecResponse,
    TestCaseResponse,
    TestCaseListResponse,
    GenerateTestCasesRequest,
    GenerateTestCasesResponse
)

router = APIRouter(prefix="/api/v2", tags=["Swagger导入"])


def _sample_from_json_schema(schema):
    if not isinstance(schema, dict):
        return None
    schema_type = schema.get("type")
    if schema_type == "object" or "properties" in schema:
        result = {}
        for name, prop in (schema.get("properties") or {}).items():
            result[name] = _sample_from_json_schema(prop)
        return result
    if schema_type == "array":
        return [_sample_from_json_schema(schema.get("items") or {})]
    if schema_type == "integer":
        return 1
    if schema_type == "number":
        return 1.0
    if schema_type == "boolean":
        return True
    return schema.get("example") or schema.get("default") or "string"


def _safe_json_loads(value):
    if not value:
        return None
    if isinstance(value, dict):
        return value
    try:
        return json.loads(value)
    except Exception:
        return None


def _detect_api_pattern(path, method):
    path_lower = (path or "").lower()
    method = (method or "").upper()
    if path_lower.endswith("/page"):
        return "page"
    if path_lower.endswith("/list"):
        return "list"
    if any(path_lower.endswith(x) for x in ["/detail", "/get", "/info", "/query"]):
        return "detail"
    if method == "POST" and any(path_lower.endswith(x) for x in ["/save", "/add", "/create", "/insert"]):
        return "save"
    if method in ["POST", "PUT"] and any(path_lower.endswith(x) for x in ["/update", "/edit", "/modify"]):
        return "update"
    if method in ["POST", "DELETE"] and any(path_lower.endswith(x) for x in ["/delete", "/remove"]):
        return "delete"
    if "/export" in path_lower or "/download" in path_lower:
        return "export"
    if "/import" in path_lower or "/upload" in path_lower:
        return "import"
    return "other"


def _is_write_api(path, method):
    pattern = _detect_api_pattern(path, method)
    return pattern in {"save", "update", "delete", "import"} or (method or "").upper() in {"PUT", "PATCH", "DELETE"}


def _generate_cases_from_yapi_data(data):
    if isinstance(data, dict) and isinstance(data.get("data"), list):
        data = data.get("data")
    if not isinstance(data, list):
        return None

    cases = []
    tags = []
    stats = {"total_apis": 0, "generated": 0, "by_method": {}, "by_tag": {}, "by_pattern": {}}

    for category in data:
        if not isinstance(category, dict):
            continue
        tag = category.get("name") or "未分类"
        if tag not in tags:
            tags.append(tag)
        for api in category.get("list") or []:
            if not isinstance(api, dict):
                continue
            method = (api.get("method") or "GET").upper()
            path = api.get("path") or (api.get("query_path") or {}).get("path") or "/"
            title = f"[{tag}] {api.get('title') or method + ' ' + path}"

            headers = {}
            for item in api.get("req_headers") or []:
                name = item.get("name")
                if name:
                    headers[name] = item.get("example") or item.get("value") or ""

            query_params = {}
            for item in api.get("req_query") or []:
                name = item.get("name")
                if name:
                    query_params[name] = item.get("example") or item.get("value") or "string"

            body = None
            if api.get("req_body_type") == "json":
                schema = _safe_json_loads(api.get("req_body_other"))
                body = _sample_from_json_schema(schema) if schema else None
            elif api.get("req_body_type") == "form":
                body = {}
                for item in api.get("req_body_form") or []:
                    name = item.get("name")
                    if name:
                        body[name] = item.get("example") or item.get("value") or "string"

            pattern = _detect_api_pattern(path, method)

            if pattern == "page":
                body = body or {}
                body.setdefault("pageNum", 1)
                body.setdefault("pageSize", 10)
            elif pattern == "list":
                body = body or {}
                body.setdefault("pageNum", 1)
                body.setdefault("pageSize", 10)
            elif pattern == "detail":
                if body and not any(k in body for k in ("uuid", "id", "ID")):
                    body = {"uuid": "00000000-0000-0000-0000-000000000000"}
            elif pattern == "delete":
                body = {"uuid": "00000000-0000-0000-0000-000000000000"}

            cases.append({
                "id": str(api.get("_id") or f"{method}_{path}"),
                "title": title,
                "method": method,
                "path": path,
                "headers": headers,
                "query_params": query_params,
                "body": body,
                "tags": [tag],
                "assertions": [
                    {"type": "status_code", "operator": "eq", "expected": 200},
                    {"type": "json_path", "path": "$.code", "operator": "eq", "expected": 200},
                ],
            })

            stats["total_apis"] += 1
            stats["generated"] += 1
            stats["by_method"][method] = stats["by_method"].get(method, 0) + 1
            stats["by_tag"][tag] = stats["by_tag"].get(tag, 0) + 1
            stats["by_pattern"][pattern] = stats["by_pattern"].get(pattern, 0) + 1

    return cases, {"base_url": "", "swagger_version": "yapi", "tags": tags, "stats": stats}


def _fetch_yapi_open_api(base_url, token, timeout=30):
    root_url = base_url.rstrip("/")
    project_resp = requests.get(
        f"{root_url}/api/project/get",
        params={"token": token},
        timeout=timeout,
        verify=False,
    )
    project_resp.raise_for_status()
    project_data = project_resp.json()
    if project_data.get("errcode") not in (0, None):
        raise ValueError(project_data.get("errmsg") or "YApi 项目信息获取失败")
    project = project_data.get("data") or {}
    project_id = project.get("_id") or project.get("id")
    if not project_id:
        raise ValueError("YApi 项目信息中缺少 project_id")

    candidate_paths = ["/api/interface/list_menu", "/api/interface/getCatMenu"]
    last_error = None
    for path in candidate_paths:
        try:
            menu_resp = requests.get(
                f"{root_url}{path}",
                params={"project_id": project_id, "token": token},
                timeout=timeout,
                verify=False,
            )
            menu_resp.raise_for_status()
            menu_data = menu_resp.json()
            if menu_data.get("errcode") not in (0, None):
                last_error = menu_data.get("errmsg") or f"{path} 返回错误"
                continue
            return menu_data
        except Exception as e:
            last_error = str(e)

    raise ValueError(last_error or "YApi 菜单接口获取失败")


@router.post("/swagger/import-file", response_model=SwaggerImportResponse)
async def import_swagger_from_file(
    project_id: int = Query(..., description="项目ID"),
    generate_cases: bool = Query(True, description="是否自动生成测试用例"),
    file: UploadFile = File(..., description="Swagger文件"),
    db: Session = Depends(get_db)
):
    """
    从文件导入 Swagger/OpenAPI
    
    支持的文件格式: JSON, YAML
    """
    try:
        # 读取文件内容
        content = await file.read()
        
        # 调用服务
        service = SwaggerService(db)
        result = service.import_from_file(
            project_id=project_id,
            file_content=content,
            filename=file.filename,
            generate_cases=generate_cases
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


@router.post("/swagger/import-url", response_model=SwaggerImportResponse)
async def import_swagger_from_url(
    request: SwaggerImportFromUrlRequest,
    db: Session = Depends(get_db)
):
    """
    从 URL 导入 Swagger/OpenAPI
    
    支持的 URL: 公开的 Swagger JSON/YAML 地址
    """
    try:
        service = SwaggerService(db)
        result = service.import_from_url(
            project_id=request.project_id,
            url=request.url,
            generate_cases=request.generate_cases
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


@router.post("/swagger/preview-url")
async def preview_swagger_from_url(request: SwaggerImportFromUrlRequest):
    """
    从 URL 预览 Swagger —— 解析返回 API 列表和自动生成的测试用例预览，不写入数据库。
    前端用此接口做选择性导入。
    """
    from app.executor_v2.swagger_to_cases import (
        fetch_swagger_from_url,
        generate_cases_from_swagger_data,
    )
    from pydantic import BaseModel
    from typing import Optional, List as TList

    try:
        data = fetch_swagger_from_url(request.url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Swagger URL 访问失败: {str(e)}")

    include_tags = getattr(request, "include_tags", None)
    exclude_tags = getattr(request, "exclude_tags", None)
    try:
        cases, meta = generate_cases_from_swagger_data(
            data,
            include_tags=include_tags,
            exclude_tags=exclude_tags,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解析失败: {str(e)}")

    return {
        "base_url": meta.get("base_url", ""),
        "swagger_version": meta.get("swagger_version", ""),
        "tags": meta.get("tags", []),
        "stats": meta.get("stats", {}),
        "cases": cases,
    }


@router.post("/swagger/preview-yapi")
async def preview_swagger_from_yapi(request: dict):
    """
    从 YApi 项目 token 预览 OpenAPI/Swagger。

    Body:
      yapi_base_url: YApi 服务地址，或包含 {token} 的完整 URL 模板
      token: YApi 项目唯一 token
      project_id: 兼容前端项目 ID，可选

    若 yapi_base_url 不包含 {token}，默认拼接：
      /api/open/plugin/export-full?type=json&status=all&token=<token>
    """
    from urllib.parse import quote
    from app.executor_v2.swagger_to_cases import (
        fetch_swagger_from_url,
        generate_cases_from_swagger_data,
    )

    yapi_base_url = (request.get("yapi_base_url") or "").strip().rstrip("/")
    token = (request.get("token") or "").strip()
    if not yapi_base_url:
        raise HTTPException(status_code=400, detail="缺少 yapi_base_url")
    if not token:
        raise HTTPException(status_code=400, detail="缺少 YApi token")

    # 智能清洗：用户可能粘贴了浏览器页面 URL，如
    #   https://yapi.xxx.com/project/489/interface/api
    # 需要自动提取根地址 https://yapi.xxx.com
    import re
    cleaned = yapi_base_url
    if "{token}" not in yapi_base_url:
        cleaned = re.sub(r'/project/\d+.*$', '', yapi_base_url)
        cleaned = re.sub(r'/group/\d+.*$', '', cleaned)
        cleaned = cleaned.rstrip("/")
        openapi_url = f"{cleaned}/api/open/plugin/export-full?type=json&status=all&token={quote(token)}"
    else:
        openapi_url = yapi_base_url.replace("{token}", quote(token))

    try:
        if "{token}" not in yapi_base_url:
            try:
                data = _fetch_yapi_open_api(cleaned, token)
                openapi_url = f"{cleaned}/api/interface/list_menu?token=***"
            except Exception:
                data = fetch_swagger_from_url(openapi_url)
        else:
            data = fetch_swagger_from_url(openapi_url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"YApi OpenAPI 访问失败: url={openapi_url}, error={str(e)}")

    try:
        yapi_result = _generate_cases_from_yapi_data(data)
        if yapi_result:
            cases, meta = yapi_result
        else:
            cases, meta = generate_cases_from_swagger_data(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"YApi OpenAPI 解析失败: {str(e)}")

    return {
        "source_url": openapi_url,
        "base_url": meta.get("base_url", ""),
        "swagger_version": meta.get("swagger_version", ""),
        "tags": meta.get("tags", []),
        "stats": meta.get("stats", {}),
        "cases": cases,
    }


@router.post("/swagger/batch-import")
async def batch_import_cases(
    request: dict,
    db: Session = Depends(get_db),
):
    """
    批量导入选中的 Swagger 用例到项目

    Body:
      project_id: int
      environment_id: int (optional)
      base_url: str
      cases: list[dict]   — 从 preview-url 返回的 cases 子集
    """
    import uuid
    from datetime import datetime
    from database.models import Project, TestCase

    project_id = request.get("project_id")
    base_url = request.get("base_url", "")
    cases_in = request.get("cases", [])
    env_id = request.get("environment_id")
    allow_write = bool(request.get("allow_write_operations", True))

    if not project_id:
        raise HTTPException(status_code=400, detail="缺少 project_id")
    if not cases_in:
        raise HTTPException(status_code=400, detail="没有选中用例")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    created = []
    skipped = 0
    skipped_write = 0
    for c in cases_in:
        path = c.get("path", "")
        method = c.get("method", "POST").upper()
        if _is_write_api(path, method) and not allow_write:
            skipped_write += 1
            continue
        full_url = base_url.rstrip("/") + path
        title = c.get("title", f"{method} {path}")
        case_id = f"SWG_{method}_{path.replace('/', '_').strip('_')}_{uuid.uuid4().hex[:6]}"

        # 检查是否已存在同路径同方法的用例
        existing = db.query(TestCase).filter(
            TestCase.source == "swagger",
            TestCase.title == title,
        ).first()
        if existing:
            skipped += 1
            continue

        tc = TestCase(
            id=case_id,
            title=title,
            module=c.get("tags", ["未分类"])[0] if c.get("tags") else "swagger",
            priority="medium",
            status="pending",
            steps=[],
            expected="HTTP 200 & code=200",
            data_type="valid",
            expected_behavior="success",
            execution_config={
                "method": method,
                "url": full_url,
                "headers": c.get("headers", {}),
                "body": c.get("body"),
                "query_params": c.get("query_params", {}),
                "timeout": 30,
            },
            assertions=c.get("assertions", []),
            tags=c.get("tags", []),
            source="swagger",
            created_by="swagger_import",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(tc)
        created.append(case_id)

    db.commit()

    return {
        "imported": len(created),
        "skipped": skipped,
        "skipped_write": skipped_write,
        "case_ids": created,
    }


@router.post("/swagger/fix-bodies")
async def fix_swagger_case_bodies(db: Session = Depends(get_db)):
    """
    修复已导入 Swagger 用例的请求体：
    - /list, /page 接口 → 确保有 pageNum + pageSize
    - /detail, /get 接口 → 确保有 uuid 或 id
    - 清理随机垃圾字符串
    """
    from copy import deepcopy
    from sqlalchemy.orm.attributes import flag_modified
    from database.models import TestCase
    cases = db.query(TestCase).filter(TestCase.source == "swagger").all()
    fixed = 0
    for tc in cases:
        cfg = deepcopy(tc.execution_config) if tc.execution_config else {}
        url = (cfg.get("url") or "").lower()
        method = (cfg.get("method") or "").upper()
        body = cfg.get("body") or {}
        changed = False
        pattern = _detect_api_pattern(url, method)

        if pattern in ("page", "list"):
            new_body = {"pageNum": 1, "pageSize": 10}
            if body != new_body:
                cfg["body"] = new_body
                changed = True
        elif pattern == "detail":
            new_body = {"uuid": "00000000-0000-0000-0000-000000000000"}
            if body != new_body:
                cfg["body"] = new_body
                changed = True
        elif pattern == "delete":
            new_body = {"uuid": "00000000-0000-0000-0000-000000000000"}
            if body != new_body:
                cfg["body"] = new_body
                changed = True

        if changed:
            tc.execution_config = cfg
            flag_modified(tc, "execution_config")
            fixed += 1

    db.commit()
    return {"fixed": fixed, "total_swagger_cases": len(cases)}


@router.get("/swagger/api-specs", response_model=List[ApiSpecResponse])
async def get_api_specs(
    project_id: int = Query(None, description="项目ID"),
    db: Session = Depends(get_db)
):
    """
    获取 API 规范列表
    
    可选按项目过滤
    """
    try:
        service = SwaggerService(db)
        
        if project_id:
            api_specs = service.get_api_specs_by_project(project_id)
        else:
            # 获取所有
            api_specs = db.query(service.api_spec_repo.model).all()
        
        return api_specs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/swagger/api-specs/{api_spec_id}", response_model=ApiSpecResponse)
async def get_api_spec(
    api_spec_id: int,
    db: Session = Depends(get_db)
):
    """获取 API 规范详情"""
    try:
        service = SwaggerService(db)
        api_spec = service.get_api_spec(api_spec_id)
        
        if not api_spec:
            raise HTTPException(status_code=404, detail="API规范不存在")
        
        return api_spec
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/swagger/api-specs/{api_spec_id}/content")
async def get_api_spec_content(
    api_spec_id: int,
    db: Session = Depends(get_db)
):
    """获取 API 规范的OpenAPI文件内容"""
    try:
        service = SwaggerService(db)
        api_spec = service.get_api_spec(api_spec_id)
        
        if not api_spec:
            raise HTTPException(status_code=404, detail="API规范不存在")
        
        # 尝试读取文件
        import json
        from pathlib import Path
        
        # 1. 尝试从raw_spec_path读取
        if api_spec.raw_spec_path:
            try:
                file_path = Path(api_spec.raw_spec_path)
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
            except Exception as e:
                print(f"无法从raw_spec_path读取: {e}")
        
        # 2. 尝试从uploads目录读取
        if api_spec.source_url:
            try:
                upload_dir = Path(__file__).parent.parent / "uploads" / "swagger"
                # 查找匹配的文件
                for file_path in upload_dir.glob(f"*{api_spec.source_url}"):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
            except Exception as e:
                print(f"无法从uploads读取: {e}")
        
        raise HTTPException(status_code=404, detail="OpenAPI文件不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取失败: {str(e)}")


@router.delete("/swagger/api-specs/{api_spec_id}")
async def delete_api_spec(
    api_spec_id: int,
    db: Session = Depends(get_db)
):
    """删除 API 规范"""
    try:
        service = SwaggerService(db)
        success = service.delete_api_spec(api_spec_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="API规范不存在")
        
        return {"success": True, "message": "删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.post("/swagger/generate-test-cases", response_model=GenerateTestCasesResponse)
async def generate_test_cases_from_swagger(
    request: GenerateTestCasesRequest,
    db: Session = Depends(get_db)
):
    """
    从已导入的 Swagger 生成测试用例
    
    用于重新生成或补充生成测试用例
    """
    try:
        service = SwaggerService(db)
        api_spec = service.get_api_spec(request.api_spec_id)
        
        if not api_spec:
            raise HTTPException(status_code=404, detail="API规范不存在")
        
        # 生成测试用例
        test_cases = service._generate_test_cases(
            api_spec_id=api_spec.id,
            swagger_file=api_spec.raw_spec_path,
            project_id=api_spec.project_id
        )
        
        return {
            "api_spec_id": api_spec.id,
            "test_cases_generated": len(test_cases),
            "test_case_ids": [tc.id for tc in test_cases]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.get("/test-cases", response_model=TestCaseListResponse)
async def get_test_cases(
    project_id: int = Query(None, description="项目ID"),
    source: str = Query(None, description="来源: swagger/manual/ai_generated"),
    status: str = Query(None, description="状态: pending/passed/failed/skipped"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    获取测试用例列表
    
    支持按项目、来源、状态过滤
    """
    try:
        service = TestCaseService(db)
        test_cases, total = service.get_test_cases(
            project_id=project_id,
            source=source,
            status=status,
            skip=skip,
            limit=limit
        )
        
        return {
            "total": total,
            "test_cases": test_cases
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/test-cases/{test_case_id}", response_model=TestCaseResponse)
async def get_test_case(
    test_case_id: str,
    db: Session = Depends(get_db)
):
    """获取测试用例详情"""
    try:
        service = TestCaseService(db)
        test_case = service.get_test_case(test_case_id)
        
        if not test_case:
            raise HTTPException(status_code=404, detail="测试用例不存在")
        
        return test_case
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")
