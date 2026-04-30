#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目业务逻辑
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import Project, get_project_repo
from schemas.project_schemas import ProjectCreate, ProjectUpdate


class ProjectService:
    """项目服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = get_project_repo(db)
    
    def create_project(self, project_data: ProjectCreate) -> Project:
        """创建项目"""
        # 检查项目名是否已存在
        existing = self.repo.get_by_name(project_data.name)
        if existing:
            raise ValueError(f"项目名称 '{project_data.name}' 已存在")
        
        project = Project(
            name=project_data.name,
            description=project_data.description,
            owner=project_data.owner,
            team=project_data.team,
            status='active'
        )
        
        try:
            return self.repo.create(project)
        except IntegrityError as e:
            raise ValueError(f"创建项目失败: {str(e)}")
    
    def get_project(self, project_id: int) -> Optional[Project]:
        """获取项目"""
        return self.repo.get_by_id(project_id)
    
    def get_all_projects(self, skip: int = 0, limit: int = 100) -> List[Project]:
        """获取所有项目"""
        return self.repo.get_all(skip=skip, limit=limit)
    
    def get_active_projects(self) -> List[Project]:
        """获取活跃项目"""
        return self.repo.get_active_projects()
    
    def update_project(self, project_id: int, project_data: ProjectUpdate) -> Optional[Project]:
        """更新项目"""
        # 检查项目是否存在
        project = self.repo.get_by_id(project_id)
        if not project:
            return None
        
        # 如果更新名称,检查是否重复
        if project_data.name and project_data.name != project.name:
            existing = self.repo.get_by_name(project_data.name)
            if existing:
                raise ValueError(f"项目名称 '{project_data.name}' 已存在")
        
        # 构建更新字典(只更新非None字段)
        updates = {k: v for k, v in project_data.dict().items() if v is not None}
        
        return self.repo.update(project_id, updates)
    
    def delete_project(self, project_id: int) -> bool:
        """删除项目"""
        return self.repo.delete(project_id)
    
    def archive_project(self, project_id: int) -> Optional[Project]:
        """归档项目"""
        return self.repo.update(project_id, {'status': 'archived'})
