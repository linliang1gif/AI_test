#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试用例服务
"""

from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_

from database.models import TestCase
from database.repository import TestCaseRepository


class TestCaseService:
    """测试用例服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = TestCaseRepository(TestCase, db)
    
    def get_test_cases(
        self,
        project_id: Optional[int] = None,
        source: Optional[str] = None,
        status: Optional[str] = None,
        case_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[TestCase], int]:
        """
        获取测试用例列表
        
        Args:
            project_id: 项目ID
            source: 来源过滤
            status: 状态过滤
            case_type: 用例类型过滤 (api/functional/web_ui)
            skip: 跳过数量
            limit: 限制数量
            
        Returns:
            (测试用例列表, 总数)
        """
        query = self.db.query(TestCase).filter(TestCase.status != 'deleted')
        
        # 应用过滤条件
        filters = []
        if project_id:
            # 通过 tags 字段 LIKE 匹配 project:N（tags 存储为 JSON 数组文本）
            filters.append(TestCase.tags.like(f'%"project:{project_id}"%'))
        if source:
            filters.append(TestCase.source == source)
        if status:
            filters.append(TestCase.status == status)
        if case_type:
            filters.append(TestCase.case_type == case_type)
        
        if filters:
            query = query.filter(and_(*filters))
        
        # 获取总数
        total = query.count()
        
        # 分页
        test_cases = query.offset(skip).limit(limit).all()
        
        return test_cases, total
    
    def get_test_case(self, test_case_id: str) -> Optional[TestCase]:
        """获取测试用例详情（排除已软删除）"""
        tc = self.repo.get_by_id(test_case_id)
        if tc and tc.status == 'deleted':
            return None
        return tc
    
    def create_test_case(self, test_case_data: dict) -> TestCase:
        """创建测试用例"""
        test_case = TestCase(**test_case_data)
        self.db.add(test_case)
        self.db.commit()
        self.db.refresh(test_case)
        return test_case
    
    def update_test_case(self, test_case_id: str, update_data: dict) -> Optional[TestCase]:
        """更新测试用例"""
        test_case = self.repo.get_by_id(test_case_id)
        if not test_case:
            return None
        
        for key, value in update_data.items():
            if hasattr(test_case, key):
                setattr(test_case, key, value)
        
        self.db.commit()
        self.db.refresh(test_case)
        return test_case
    
    def delete_test_case(self, test_case_id: str) -> bool:
        """删除测试用例"""
        return self.repo.delete(test_case_id)
