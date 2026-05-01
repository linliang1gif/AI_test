#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目配置路由 - 使用数据库
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

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

router = APIRouter(prefix="/api/v2", tags=["项目配置"])


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
    db: Session = Depends(get_db)
):
    """删除项目"""
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
    db: Session = Depends(get_db)
):
    """删除环境"""
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
        service = AuthService(db)
        new_auth = service.create_auth_profile(auth_profile)
        
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
        updated_auth = service.update_auth_profile(auth_id, auth_profile)
        if not updated_auth:
            raise HTTPException(status_code=404, detail=f"鉴权配置ID {auth_id} 不存在")
        
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
