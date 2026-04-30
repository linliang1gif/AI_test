#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境业务逻辑
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from database import Environment, get_environment_repo, get_project_repo
from schemas.project_schemas import EnvironmentCreate, EnvironmentUpdate


class EnvironmentService:
    """环境服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = get_environment_repo(db)
        self.project_repo = get_project_repo(db)
    
    def create_environment(self, env_data: EnvironmentCreate) -> Environment:
        """创建环境"""
        # 检查项目是否存在
        project = self.project_repo.get_by_id(env_data.project_id)
        if not project:
            raise ValueError(f"项目ID {env_data.project_id} 不存在")
        
        # 检查同一项目下环境名是否重复
        existing_envs = self.repo.get_by_project(env_data.project_id)
        if any(env.name == env_data.name.value for env in existing_envs):
            raise ValueError(f"项目下已存在 '{env_data.name.value}' 环境")
        
        environment = Environment(
            project_id=env_data.project_id,
            name=env_data.name.value,
            base_url=env_data.base_url,
            is_protected=env_data.is_protected,
            allow_write=env_data.allow_write,
            timeout_seconds=env_data.timeout_seconds,
            retry_count=env_data.retry_count
        )
        
        return self.repo.create(environment)
    
    def get_environment(self, env_id: int) -> Optional[Environment]:
        """获取环境"""
        return self.repo.get_by_id(env_id)
    
    def get_project_environments(self, project_id: int) -> List[Environment]:
        """获取项目的所有环境"""
        return self.repo.get_by_project(project_id)
    
    def update_environment(self, env_id: int, env_data: EnvironmentUpdate) -> Optional[Environment]:
        """更新环境"""
        environment = self.repo.get_by_id(env_id)
        if not environment:
            return None
        
        # 构建更新字典
        updates = {}
        if env_data.name is not None:
            updates['name'] = env_data.name.value
        if env_data.base_url is not None:
            updates['base_url'] = env_data.base_url
        if env_data.is_protected is not None:
            updates['is_protected'] = env_data.is_protected
        if env_data.allow_write is not None:
            updates['allow_write'] = env_data.allow_write
        if env_data.timeout_seconds is not None:
            updates['timeout_seconds'] = env_data.timeout_seconds
        if env_data.retry_count is not None:
            updates['retry_count'] = env_data.retry_count
        
        return self.repo.update(env_id, updates)
    
    def delete_environment(self, env_id: int) -> bool:
        """删除环境"""
        return self.repo.delete(env_id)
    
    def get_protected_environments(self) -> List[Environment]:
        """获取受保护的环境"""
        return self.repo.get_protected_environments()
