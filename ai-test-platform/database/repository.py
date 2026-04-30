#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用Repository - 提供基础CRUD能力
"""

from typing import TypeVar, Generic, Type, List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from .models import Base

T = TypeVar('T', bound=Base)


class BaseRepository(Generic[T]):
    """
    通用Repository基类
    提供标准CRUD操作
    """
    
    def __init__(self, model: Type[T], db: Session):
        self.model = model
        self.db = db
    
    def create(self, obj: T) -> T:
        """创建对象"""
        try:
            self.db.add(obj)
            self.db.commit()
            self.db.refresh(obj)
            return obj
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"创建失败: {str(e)}")
    
    def get_by_id(self, id: Any) -> Optional[T]:
        """根据ID获取对象"""
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """获取所有对象(分页)"""
        return self.db.query(self.model).offset(skip).limit(limit).all()
    
    def update(self, id: Any, updates: Dict[str, Any]) -> Optional[T]:
        """更新对象"""
        try:
            obj = self.get_by_id(id)
            if not obj:
                return None
            
            for key, value in updates.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
            
            self.db.commit()
            self.db.refresh(obj)
            return obj
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"更新失败: {str(e)}")
    
    def delete(self, id: Any) -> bool:
        """删除对象"""
        try:
            obj = self.get_by_id(id)
            if not obj:
                return False
            
            self.db.delete(obj)
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"删除失败: {str(e)}")
    
    def count(self) -> int:
        """统计数量"""
        return self.db.query(self.model).count()
    
    def exists(self, id: Any) -> bool:
        """检查是否存在"""
        return self.db.query(self.model).filter(self.model.id == id).count() > 0
    
    def filter_by(self, **kwargs) -> List[T]:
        """根据条件过滤"""
        return self.db.query(self.model).filter_by(**kwargs).all()
    
    def first_by(self, **kwargs) -> Optional[T]:
        """根据条件获取第一个"""
        return self.db.query(self.model).filter_by(**kwargs).first()


class ProjectRepository(BaseRepository):
    """项目Repository"""
    
    def get_active_projects(self) -> List:
        """获取活跃项目"""
        return self.filter_by(status='active')
    
    def get_by_name(self, name: str) -> Optional:
        """根据名称获取项目"""
        return self.first_by(name=name)


class EnvironmentRepository(BaseRepository):
    """环境Repository"""
    
    def get_by_project(self, project_id: int) -> List:
        """获取项目的所有环境"""
        return self.filter_by(project_id=project_id)
    
    def get_protected_environments(self) -> List:
        """获取受保护的环境"""
        return self.filter_by(is_protected=True)


class ApiSpecRepository(BaseRepository):
    """API规范Repository"""
    
    def get_by_project(self, project_id: int) -> List:
        """获取项目的所有API规范"""
        return self.filter_by(project_id=project_id)
    
    def get_by_source_type(self, source_type: str) -> List:
        """根据来源类型获取API规范"""
        return self.filter_by(source_type=source_type)


class TestCaseRepository(BaseRepository):
    """测试用例Repository"""
    
    def get_by_module(self, module: str) -> List:
        """根据模块获取测试用例"""
        return self.filter_by(module=module)
    
    def get_by_priority(self, priority: str) -> List:
        """根据优先级获取测试用例"""
        return self.filter_by(priority=priority)
    
    def get_by_status(self, status: str) -> List:
        """根据状态获取测试用例"""
        return self.filter_by(status=status)
    
    def search(self, keyword: str, skip: int = 0, limit: int = 100) -> List:
        """搜索测试用例"""
        from sqlalchemy import or_
        return self.db.query(self.model).filter(
            or_(
                self.model.title.like(f'%{keyword}%'),
                self.model.module.like(f'%{keyword}%')
            )
        ).offset(skip).limit(limit).all()


class TestRunRepository(BaseRepository):
    """测试执行Repository"""
    
    def get_by_project(self, project_id: int, skip: int = 0, limit: int = 50) -> List:
        """获取项目的测试执行记录"""
        return self.db.query(self.model).filter(
            self.model.project_id == project_id
        ).order_by(self.model.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_by_status(self, status: str) -> List:
        """根据状态获取测试执行"""
        return self.filter_by(status=status)
    
    def get_by_trace_id(self, trace_id: str) -> Optional:
        """根据trace_id获取测试执行"""
        return self.first_by(trace_id=trace_id)
    
    def get_recent(self, limit: int = 10) -> List:
        """获取最近的测试执行"""
        return self.db.query(self.model).order_by(
            self.model.created_at.desc()
        ).limit(limit).all()


class RunCaseRepository(BaseRepository):
    """测试用例执行记录Repository"""
    
    def get_by_run(self, run_id: str) -> List:
        """获取测试执行的所有用例记录"""
        return self.filter_by(run_id=run_id)
    
    def get_failed_cases(self, run_id: str) -> List:
        """获取失败的用例"""
        return self.db.query(self.model).filter(
            self.model.run_id == run_id,
            self.model.status == 'failed'
        ).all()


class ReportRepository(BaseRepository):
    """报告Repository"""
    
    def get_by_run(self, run_id: str) -> Optional:
        """根据run_id获取报告"""
        return self.first_by(run_id=run_id)
    
    def get_recent(self, limit: int = 20) -> List:
        """获取最近的报告"""
        return self.db.query(self.model).order_by(
            self.model.created_at.desc()
        ).limit(limit).all()


class HealingRecordRepository(BaseRepository):
    """修复记录Repository"""
    
    def get_by_test_case(self, test_case_id: str) -> List:
        """获取测试用例的修复记录"""
        return self.filter_by(test_case_id=test_case_id)
    
    def get_successful_healings(self) -> List:
        """获取成功的修复记录"""
        return self.filter_by(success=True)
    
    def get_recent(self, limit: int = 50) -> List:
        """获取最近的修复记录"""
        return self.db.query(self.model).order_by(
            self.model.timestamp.desc()
        ).limit(limit).all()


# 便捷函数：创建Repository实例
def get_project_repo(db: Session) -> ProjectRepository:
    from .models import Project
    return ProjectRepository(Project, db)


def get_environment_repo(db: Session) -> EnvironmentRepository:
    from .models import Environment
    return EnvironmentRepository(Environment, db)


def get_api_spec_repo(db: Session):
    from .models import ApiSpec
    return ApiSpecRepository(ApiSpec, db)


def get_test_case_repo(db: Session) -> TestCaseRepository:
    from .models import TestCase
    return TestCaseRepository(TestCase, db)


def get_test_run_repo(db: Session) -> TestRunRepository:
    from .models import TestRun
    return TestRunRepository(TestRun, db)


def get_run_case_repo(db: Session) -> RunCaseRepository:
    from .models import RunCase
    return RunCaseRepository(RunCase, db)


def get_report_repo(db: Session) -> ReportRepository:
    from .models import Report
    return ReportRepository(Report, db)


def get_healing_record_repo(db: Session) -> HealingRecordRepository:
    from .models import HealingRecord
    return HealingRecordRepository(HealingRecord, db)
