#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目配置路由 - 使用数据库
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional

from database import get_db
from database.models import Environment
from services import ProjectService, EnvironmentService, AuthService
from schemas.project_schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    EnvironmentCreate,
    EnvironmentUpdate,
    EnvironmentResponse,
    AuthProfileCreate,
    AuthProfileUpdate,
    AuthProfileResponse
)
from backend.danger_guard import check_confirm, ConfirmRequest

router = APIRouter(prefix="/api/v2", tags=["项目配置"])


def _auth_type_value(auth_type: Any) -> str:
    return getattr(auth_type, "value", auth_type) or ""


def _normalize_token_value(token: str) -> str:
    token = (token or "").strip()
    if token.lower().startswith("bearer "):
        return token.split(None, 1)[1].strip()
    return token


def _extract_auth_token(auth_type: Any, auth_config: Optional[Dict[str, Any]]) -> str:
    auth_type = _auth_type_value(auth_type)
    auth_config = auth_config or {}
    if auth_type == "bearer":
        return _normalize_token_value(auth_config.get("token", ""))
    if auth_type == "custom":
        header_name = str(auth_config.get("header_name") or "Authorization").lower()
        if header_name == "authorization":
            return _normalize_token_value(auth_config.get("token") or auth_config.get("value") or "")
    if auth_type == "oauth2":
        return _normalize_token_value(auth_config.get("access_token") or auth_config.get("token") or "")
    return ""


def _write_normalized_token(auth_type: Any, auth_config: Optional[Dict[str, Any]], token: str) -> None:
    if not auth_config:
        return
    auth_type = _auth_type_value(auth_type)
    if auth_type in ("bearer", "oauth2") and "token" in auth_config:
        auth_config["token"] = token
    elif auth_type == "custom":
        if "token" in auth_config:
            auth_config["token"] = token
        elif "value" in auth_config:
            auth_config["value"] = token


def _validate_auth_token_or_raise(db: Session, environment_id: int, auth_type: Any, auth_config: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    token = _extract_auth_token(auth_type, auth_config)
    if not token:
        return None

    env = db.query(Environment).filter(Environment.id == environment_id).first()
    if not env:
        return None

    from routes.page_scanner_routes import _validate_business_token

    result = _validate_business_token(env.base_url, token)
    if not result.get("valid"):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "TOKEN_VALIDATION_FAILED",
                "message": result.get("message") or "Token 校验失败",
                "status": result.get("status"),
                "business_code": result.get("business_code"),
            },
        )

    _write_normalized_token(auth_type, auth_config, token)
    return result


def _sync_auth_token_to_web_session(db: Session, environment_id: int, auth_type: Any, auth_config: Optional[Dict[str, Any]]) -> None:
    token = _extract_auth_token(auth_type, auth_config)
    if not token:
        return
    env = db.query(Environment).filter(Environment.id == environment_id).first()
    if not env:
        return
    try:
        from routes.case_execute_routes import _sync_web_ui_session_token

        _sync_web_ui_session_token(env.project_id, token)
    except Exception:
        pass


# ==================== Project APIs ====================

@router.post("/projects", response_model=ProjectResponse, status_code=201)
async def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db)
):
    """创建项目"""
    try:
        service = ProjectService(db)
        new_project = service.create_project(project)
        return new_project
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建项目失败: {str(e)}")


@router.get("/projects")
async def get_projects(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """获取项目列表 - 统一返回格式"""
    try:
        service = ProjectService(db)
        if active_only:
            projects = service.get_active_projects()
        else:
            projects = service.get_all_projects(skip=skip, limit=limit)
        
        # 统一返回格式
        return {
            "projects": projects,
            "total": len(projects),
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取项目列表失败: {str(e)}")


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    """获取项目详情"""
    try:
        service = ProjectService(db)
        project = service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"项目ID {project_id} 不存在")
        return project
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取项目失败: {str(e)}")


@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """更新项目"""
    try:
        service = ProjectService(db)
        updated_project = service.update_project(project_id, project)
        if not updated_project:
            raise HTTPException(status_code=404, detail=f"项目ID {project_id} 不存在")
        return updated_project
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新项目失败: {str(e)}")


@router.delete("/projects/{project_id}", status_code=204)
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    body: Optional[ConfirmRequest] = Body(None),
):
    """删除项目"""
    # Phase 10B: 危险操作守卫
    check_confirm("DELETE_PROJECT", (body or ConfirmRequest()).confirm, (body or ConfirmRequest()).confirm_text)
    try:
        service = ProjectService(db)
        success = service.delete_project(project_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"项目ID {project_id} 不存在")
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除项目失败: {str(e)}")


# ==================== Environment APIs ====================

@router.post("/environments", response_model=EnvironmentResponse, status_code=201)
async def create_environment(
    environment: EnvironmentCreate,
    db: Session = Depends(get_db)
):
    """创建环境"""
    try:
        service = EnvironmentService(db)
        new_env = service.create_environment(environment)
        return new_env
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建环境失败: {str(e)}")


@router.get("/environments", response_model=List[EnvironmentResponse])
async def get_environments(
    project_id: Optional[int] = Query(None, description="项目ID（可选）"),
    db: Session = Depends(get_db)
):
    """获取环境列表，支持按项目ID过滤"""
    try:
        service = EnvironmentService(db)
        if project_id:
            environments = service.get_project_environments(project_id)
        else:
            # 获取所有环境
            environments = db.query(Environment).all()
        return environments
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取环境列表失败: {str(e)}")


@router.get("/projects/{project_id}/environments", response_model=List[EnvironmentResponse])
async def get_project_environments(
    project_id: int,
    db: Session = Depends(get_db)
):
    """获取项目的所有环境"""
    try:
        service = EnvironmentService(db)
        environments = service.get_project_environments(project_id)
        return environments
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取环境列表失败: {str(e)}")


@router.get("/environments/{env_id}", response_model=EnvironmentResponse)
async def get_environment(
    env_id: int,
    db: Session = Depends(get_db)
):
    """获取环境详情"""
    try:
        service = EnvironmentService(db)
        environment = service.get_environment(env_id)
        if not environment:
            raise HTTPException(status_code=404, detail=f"环境ID {env_id} 不存在")
        return environment
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取环境失败: {str(e)}")


@router.put("/environments/{env_id}", response_model=EnvironmentResponse)
async def update_environment(
    env_id: int,
    environment: EnvironmentUpdate,
    db: Session = Depends(get_db)
):
    """更新环境"""
    try:
        service = EnvironmentService(db)
        updated_env = service.update_environment(env_id, environment)
        if not updated_env:
            raise HTTPException(status_code=404, detail=f"环境ID {env_id} 不存在")
        return updated_env
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新环境失败: {str(e)}")


@router.delete("/environments/{env_id}", status_code=204)
async def delete_environment(
    env_id: int,
    db: Session = Depends(get_db),
    body: Optional[ConfirmRequest] = Body(None),
):
    """删除环境"""
    # Phase 10B: 危险操作守卫
    check_confirm("DELETE_ENVIRONMENT", (body or ConfirmRequest()).confirm, (body or ConfirmRequest()).confirm_text)
    try:
        service = EnvironmentService(db)
        success = service.delete_environment(env_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"环境ID {env_id} 不存在")
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除环境失败: {str(e)}")


# ==================== AuthProfile APIs ====================

@router.post("/auth-profiles", response_model=AuthProfileResponse, status_code=201)
async def create_auth_profile(
    auth_profile: AuthProfileCreate,
    db: Session = Depends(get_db)
):
    """创建鉴权配置"""
    try:
        token_validation = _validate_auth_token_or_raise(
            db,
            auth_profile.environment_id,
            auth_profile.auth_type,
            auth_profile.auth_config,
        )
        service = AuthService(db)
        new_auth = service.create_auth_profile(auth_profile)
        if token_validation:
            _sync_auth_token_to_web_session(db, new_auth.environment_id, new_auth.auth_type, auth_profile.auth_config)
        
        # 返回脱敏数据
        return AuthProfileResponse(
            id=new_auth.id,
            environment_id=new_auth.environment_id,
            auth_type=new_auth.auth_type,
            auth_config_masked=service.mask_sensitive_data(new_auth),
            default_headers=new_auth.default_headers,
            created_at=new_auth.created_at,
            updated_at=new_auth.updated_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建鉴权配置失败: {str(e)}")


@router.get("/environments/{env_id}/auth-profile", response_model=AuthProfileResponse)
async def get_environment_auth_profile(
    env_id: int,
    db: Session = Depends(get_db)
):
    """获取环境的鉴权配置"""
    try:
        service = AuthService(db)
        auth_profile = service.get_by_environment(env_id)
        if not auth_profile:
            raise HTTPException(status_code=404, detail=f"环境ID {env_id} 没有鉴权配置")
        
        # 返回脱敏数据
        return AuthProfileResponse(
            id=auth_profile.id,
            environment_id=auth_profile.environment_id,
            auth_type=auth_profile.auth_type,
            auth_config_masked=service.mask_sensitive_data(auth_profile),
            default_headers=auth_profile.default_headers,
            created_at=auth_profile.created_at,
            updated_at=auth_profile.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取鉴权配置失败: {str(e)}")


@router.put("/auth-profiles/{auth_id}", response_model=AuthProfileResponse)
async def update_auth_profile(
    auth_id: int,
    auth_profile: AuthProfileUpdate,
    db: Session = Depends(get_db)
):
    """更新鉴权配置"""
    try:
        service = AuthService(db)
        existing = service.get_auth_profile(auth_id)
        if not existing:
            raise HTTPException(status_code=404, detail=f"鉴权配置ID {auth_id} 不存在")
        effective_auth_type = auth_profile.auth_type if auth_profile.auth_type is not None else existing.auth_type
        token_validation = None
        if auth_profile.auth_config is not None:
            token_validation = _validate_auth_token_or_raise(
                db,
                existing.environment_id,
                effective_auth_type,
                auth_profile.auth_config,
            )
        updated_auth = service.update_auth_profile(auth_id, auth_profile)
        if not updated_auth:
            raise HTTPException(status_code=404, detail=f"鉴权配置ID {auth_id} 不存在")
        if token_validation:
            _sync_auth_token_to_web_session(db, updated_auth.environment_id, effective_auth_type, auth_profile.auth_config)
        
        # 返回脱敏数据
        return AuthProfileResponse(
            id=updated_auth.id,
            environment_id=updated_auth.environment_id,
            auth_type=updated_auth.auth_type,
            auth_config_masked=service.mask_sensitive_data(updated_auth),
            default_headers=updated_auth.default_headers,
            created_at=updated_auth.created_at,
            updated_at=updated_auth.updated_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新鉴权配置失败: {str(e)}")


@router.delete("/auth-profiles/{auth_id}", status_code=204)
async def delete_auth_profile(
    auth_id: int,
    db: Session = Depends(get_db)
):
    """删除鉴权配置"""
    try:
        service = AuthService(db)
        success = service.delete_auth_profile(auth_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"鉴权配置ID {auth_id} 不存在")
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除鉴权配置失败: {str(e)}")
