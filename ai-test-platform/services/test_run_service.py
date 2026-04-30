#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试执行服务 - 管理测试执行和状态流转
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import uuid

from database import (
    TestRun, RunCase, RunStep, RunStatusHistory,
    get_test_run_repo, get_run_case_repo
)
from database.repository import BaseRepository
from schemas.test_run_schemas import (
    TestRunCreate, TestRunUpdate, StatusUpdateRequest
)
from services.state_machine import RunStateMachine


class TestRunService:
    """测试执行服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.run_repo = get_test_run_repo(db)
        self.case_repo = get_run_case_repo(db)
        self.history_repo = BaseRepository(RunStatusHistory, db)
        self.state_machine = RunStateMachine
    
    def create_test_run(self, run_data: TestRunCreate) -> TestRun:
        """
        创建测试执行
        
        Args:
            run_data: 测试执行创建数据
            
        Returns:
            TestRun: 创建的测试执行对象
        """
        # 生成run_id和trace_id
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        run_id = f"RUN_{timestamp}_{uuid.uuid4().hex[:8]}"
        trace_id = f"TRACE_{uuid.uuid4().hex}"
        
        # 创建TestRun对象
        test_run = TestRun(
            id=run_id,
            project_id=run_data.project_id,
            environment_id=run_data.environment_id,
            trigger_type=run_data.trigger_type or 'manual',
            status='created',
            trace_id=trace_id,
            created_by=run_data.created_by or 'system'
        )
        
        try:
            # 保存到数据库
            created_run = self.run_repo.create(test_run)
            
            # 记录状态历史(首次创建)
            self._record_status_change(
                entity_type='run',
                entity_id=run_id,
                from_status=None,
                to_status='created',
                changed_by=run_data.created_by or 'system',
                reason='测试执行创建'
            )
            
            return created_run
        except IntegrityError as e:
            raise ValueError(f"创建测试执行失败: {str(e)}")
    
    def get_test_run(self, run_id: str) -> Optional[TestRun]:
        """获取测试执行详情"""
        return self.run_repo.get_by_id(run_id)
    
    def get_test_runs(
        self,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[TestRun]:
        """
        获取测试执行列表
        
        Args:
            project_id: 项目ID(可选)
            status: 状态过滤(可选)
            skip: 跳过数量
            limit: 限制数量
            
        Returns:
            List[TestRun]: 测试执行列表
        """
        query = self.db.query(TestRun)
        if project_id:
            query = query.filter(TestRun.project_id == project_id)
        if status:
            query = query.filter(TestRun.status == status)
        return (
            query
            .order_by(TestRun.created_at.desc(), TestRun.start_time.desc(), TestRun.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def update_run_status(
        self,
        run_id: str,
        status_data: StatusUpdateRequest
    ) -> TestRun:
        """
        更新测试执行状态
        
        Args:
            run_id: 测试执行ID
            status_data: 状态更新数据
            
        Returns:
            TestRun: 更新后的测试执行对象
            
        Raises:
            ValueError: 状态流转不合法
        """
        # 获取当前run
        test_run = self.run_repo.get_by_id(run_id)
        if not test_run:
            raise ValueError(f"测试执行 {run_id} 不存在")
        
        current_status = test_run.status
        new_status = status_data.status
        
        # 验证状态流转
        is_valid, error_msg = self.state_machine.validate_transition(
            current_status, new_status
        )
        if not is_valid:
            raise ValueError(error_msg)
        
        # 更新状态
        updates = {'status': new_status}
        
        # 根据状态更新时间戳
        if new_status == 'running' and not test_run.start_time:
            updates['start_time'] = datetime.now()
        elif new_status in ['passed', 'failed', 'aborted']:
            if not test_run.end_time:
                updates['end_time'] = datetime.now()
                if test_run.start_time:
                    duration = (updates['end_time'] - test_run.start_time).total_seconds()
                    updates['duration'] = duration
        
        # 执行更新
        updated_run = self.run_repo.update(run_id, updates)
        
        # 记录状态历史
        self._record_status_change(
            entity_type='run',
            entity_id=run_id,
            from_status=current_status,
            to_status=new_status,
            changed_by=status_data.changed_by or 'system',
            reason=status_data.reason
        )
        
        return updated_run
    
    def get_run_cases(self, run_id: str) -> List[RunCase]:
        """
        获取测试执行的所有用例记录
        
        Args:
            run_id: 测试执行ID
            
        Returns:
            List[RunCase]: 用例执行记录列表
        """
        return self.case_repo.get_by_run(run_id)
    
    def get_status_history(
        self,
        entity_type: str,
        entity_id: str
    ) -> List[RunStatusHistory]:
        """
        获取状态历史
        
        Args:
            entity_type: 实体类型(run/run_case/run_step)
            entity_id: 实体ID
            
        Returns:
            List[RunStatusHistory]: 状态历史记录列表
        """
        return self.db.query(RunStatusHistory).filter(
            RunStatusHistory.entity_type == entity_type,
            RunStatusHistory.entity_id == entity_id
        ).order_by(RunStatusHistory.changed_at.asc()).all()
    
    def update_run_case_status(
        self,
        run_case_id: int,
        new_status: str,
        changed_by: str = 'system',
        reason: Optional[str] = None
    ) -> RunCase:
        """
        更新用例执行状态
        
        Args:
            run_case_id: 用例执行记录ID
            new_status: 新状态
            changed_by: 操作人
            reason: 变更原因
            
        Returns:
            RunCase: 更新后的用例执行记录
        """
        run_case = self.case_repo.get_by_id(run_case_id)
        if not run_case:
            raise ValueError(f"用例执行记录 {run_case_id} 不存在")
        
        current_status = run_case.status
        
        # 验证状态流转(复用run的状态机规则)
        is_valid, error_msg = self.state_machine.validate_transition(
            current_status, new_status
        )
        if not is_valid:
            raise ValueError(error_msg)
        
        # 更新状态
        updates = {'status': new_status}
        
        # 更新时间戳
        if new_status == 'running' and not run_case.start_time:
            updates['start_time'] = datetime.now()
        elif new_status in ['passed', 'failed', 'skipped']:
            if not run_case.end_time:
                updates['end_time'] = datetime.now()
                if run_case.start_time:
                    duration = (updates['end_time'] - run_case.start_time).total_seconds()
                    updates['duration'] = duration
        
        updated_case = self.case_repo.update(run_case_id, updates)
        
        # 记录状态历史
        self._record_status_change(
            entity_type='run_case',
            entity_id=str(run_case_id),
            from_status=current_status,
            to_status=new_status,
            changed_by=changed_by,
            reason=reason
        )
        
        return updated_case
    
    def update_run_step_status(
        self,
        run_step_id: int,
        new_status: str,
        changed_by: str = 'system',
        reason: Optional[str] = None
    ):
        """
        更新步骤执行状态
        
        Args:
            run_step_id: 步骤执行ID
            new_status: 新状态
            changed_by: 操作人
            reason: 变更原因
        """
        run_step = self.db.query(RunStep).filter(RunStep.id == run_step_id).first()
        if not run_step:
            raise ValueError(f"步骤执行记录 {run_step_id} 不存在")
        
        current_status = run_step.status
        
        # 简化的状态流转(步骤级别)
        # pending -> running -> passed/failed/skipped
        valid_transitions = {
            'pending': {'running'},
            'running': {'passed', 'failed', 'skipped'}
        }
        
        if current_status not in valid_transitions:
            raise ValueError(f"无效的源状态: {current_status}")
        
        if new_status not in valid_transitions.get(current_status, set()):
            raise ValueError(f"不允许从 '{current_status}' 流转到 '{new_status}'")
        
        # 更新状态
        run_step.status = new_status
        
        # 更新时间戳
        if new_status == 'running' and not run_step.start_time:
            run_step.start_time = datetime.now()
        elif new_status in ['passed', 'failed', 'skipped']:
            if not run_step.end_time:
                run_step.end_time = datetime.now()
                if run_step.start_time:
                    run_step.duration = (run_step.end_time - run_step.start_time).total_seconds()
        
        self.db.commit()
        self.db.refresh(run_step)
        
        # 记录状态历史
        self._record_status_change(
            entity_type='run_step',
            entity_id=str(run_step_id),
            from_status=current_status,
            to_status=new_status,
            changed_by=changed_by,
            reason=reason
        )
        
        return run_step
    
    def _record_status_change(
        self,
        entity_type: str,
        entity_id: str,
        from_status: Optional[str],
        to_status: str,
        changed_by: str = 'system',
        reason: Optional[str] = None
    ):
        """
        记录状态变更历史
        
        Args:
            entity_type: 实体类型(run/run_case/run_step)
            entity_id: 实体ID
            from_status: 原状态
            to_status: 新状态
            changed_by: 操作人
            reason: 变更原因
        """
        history = RunStatusHistory(
            entity_type=entity_type,
            entity_id=entity_id,
            from_status=from_status,
            to_status=to_status,
            changed_at=datetime.now(),
            changed_by=changed_by,
            reason=reason
        )
        
        self.history_repo.create(history)
