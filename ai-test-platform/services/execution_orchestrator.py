#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行编排器 - 集成ExecutionEngine和TestRunService
负责协调执行流程和状态管理
"""

import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core import TestCase, ExecutionResult, TestCaseStatus
from modules.executor import ExecutionEngine
from database import RunCase, RunStep
from services.test_run_service import TestRunService
from schemas.test_run_schemas import TestRunCreate, StatusUpdateRequest


class ExecutionOrchestrator:
    """
    执行编排器
    
    职责:
    1. 创建TestRun并管理状态流转
    2. 为每个TestCase创建RunCase
    3. 为关键步骤创建RunStep
    4. 调用ExecutionEngine执行测试
    5. 收集结果并更新状态
    """
    
    def __init__(self, db: Session, execution_engine: Optional[ExecutionEngine] = None):
        """
        初始化执行编排器
        
        Args:
            db: 数据库会话
            execution_engine: 执行引擎(可选,如不提供则创建默认实例)
        """
        self.db = db
        self.test_run_service = TestRunService(db)
        self.execution_engine = execution_engine or ExecutionEngine()
    
    def execute_test_cases(
        self,
        test_cases: List[TestCase],
        project_id: int,
        environment_id: int,
        trigger_type: str = 'manual',
        created_by: str = 'system',
        max_workers: int = 5,
        parallel: bool = True
    ) -> Dict[str, Any]:
        """
        执行测试用例(完整链路)
        
        Args:
            test_cases: 测试用例列表
            project_id: 项目ID
            environment_id: 环境ID
            trigger_type: 触发类型
            created_by: 创建人
            max_workers: 最大并发数
            parallel: 是否并行执行
            
        Returns:
            Dict: 执行结果摘要
        """
        # 1. 创建TestRun (状态: created)
        test_run = self._create_test_run(
            project_id=project_id,
            environment_id=environment_id,
            trigger_type=trigger_type,
            created_by=created_by,
            total_cases=len(test_cases)
        )
        
        run_id = test_run.id
        print(f"✅ 创建TestRun: {run_id}")
        
        try:
            # 2. 创建RunCase记录
            run_cases = self._create_run_cases(run_id, test_cases)
            print(f"✅ 创建RunCase: {len(run_cases)}个")
            
            # 3. 状态流转: created → queued
            self._update_run_status(run_id, 'queued', created_by, '进入执行队列')
            
            # 4. 状态流转: queued → preparing
            self._update_run_status(run_id, 'preparing', created_by, '准备执行环境')
            
            # 5. 状态流转: preparing → running
            self._update_run_status(run_id, 'running', created_by, '开始执行测试')
            
            # 6. 执行测试用例
            print(f"🚀 开始执行测试...")
            
            # 逐个执行测试用例并记录RunStep
            execution_results = []
            for idx, test_case in enumerate(test_cases):
                run_case = run_cases[idx]
                
                # 创建RunStep: 准备执行
                step1 = self.create_run_step(
                    run_case_id=run_case.id,
                    step_name="准备执行",
                    step_order=1,
                    changed_by=created_by
                )
                self.update_run_step_status(step1.id, 'running', created_by, '开始准备')
                
                # 更新RunCase状态为running
                self.test_run_service.update_run_case_status(
                    run_case_id=run_case.id,
                    new_status='running',
                    changed_by=created_by,
                    reason='开始执行测试用例'
                )
                
                # 执行测试
                try:
                    result = self.execution_engine._run_single(test_case)
                    execution_results.append(result)
                    
                    # 完成准备步骤
                    self.update_run_step_status(step1.id, 'passed', created_by, '准备完成')
                    
                    # 创建RunStep: 执行测试
                    step2 = self.create_run_step(
                        run_case_id=run_case.id,
                        step_name="执行测试",
                        step_order=2,
                        changed_by=created_by
                    )
                    self.update_run_step_status(step2.id, 'running', created_by, '执行中')
                    
                    # 处理枚举类型
                    from core import TestCaseStatus
                    status = result.status
                    if isinstance(status, TestCaseStatus):
                        status_str = status.value if hasattr(status, 'value') else str(status).split('.')[-1].lower()
                    else:
                        status_str = str(status).lower()
                    
                    # 根据结果更新step2状态
                    if status_str == 'passed':
                        self.update_run_step_status(step2.id, 'passed', created_by, '执行成功')
                        print(f"  ✅ {test_case.id}: passed")
                    else:
                        self.update_run_step_status(step2.id, 'failed', created_by, f'执行失败: {result.error}')
                        print(f"  ❌ {test_case.id}: {status_str}")
                    
                    # 记录请求/响应快照到RunStep
                    self._record_execution_snapshot(step2.id, test_case, result)
                    
                except Exception as e:
                    # 执行异常
                    print(f"  ❌ {test_case.id}: error - {e}")
                    self.update_run_step_status(step1.id, 'failed', created_by, f'执行异常: {str(e)}')
                    
                    # 创建失败的ExecutionResult
                    from core import create_execution_result
                    result = create_execution_result(
                        test_case_id=test_case.id,
                        status='error',
                        start_time=datetime.now(),
                        end_time=datetime.now(),
                        error=str(e),
                        error_type=type(e).__name__
                    )
                    execution_results.append(result)
            
            # 7. 更新RunCase状态和结果
            self._update_run_cases(run_cases, execution_results, created_by)
            
            # 8. 统计结果
            stats = self._calculate_statistics(execution_results)
            
            # 9. 更新TestRun统计信息
            self._update_run_statistics(run_id, stats)
            
            # 10. 确定最终状态
            final_status = self._determine_final_status(stats)
            
            # 11. 状态流转到终态
            self._update_run_status(
                run_id, 
                final_status, 
                created_by, 
                f"执行完成: {stats['passed']}/{stats['total']} 通过"
            )
            
            print(f"✅ 执行完成: {final_status}")
            
            return {
                'success': True,
                'run_id': run_id,
                'trace_id': test_run.trace_id,
                'status': final_status,
                'statistics': stats,
                'results': execution_results
            }
            
        except Exception as e:
            # 执行失败,标记为failed
            print(f"❌ 执行失败: {e}")
            self._update_run_status(
                run_id, 
                'failed', 
                created_by, 
                f"执行异常: {str(e)}"
            )
            
            return {
                'success': False,
                'run_id': run_id,
                'error': str(e)
            }
    
    def _create_test_run(
        self,
        project_id: int,
        environment_id: int,
        trigger_type: str,
        created_by: str,
        total_cases: int
    ):
        """创建TestRun"""
        run_data = TestRunCreate(
            project_id=project_id,
            environment_id=environment_id,
            trigger_type=trigger_type,
            created_by=created_by
        )
        
        test_run = self.test_run_service.create_test_run(run_data)
        
        # 更新total_cases
        from database.repository import BaseRepository
        from database.models import TestRun
        repo = BaseRepository(TestRun, self.db)
        repo.update(test_run.id, {'total_cases': total_cases})
        
        return test_run
    
    def _create_run_cases(self, run_id: str, test_cases: List[TestCase]) -> List[RunCase]:
        """为每个测试用例创建RunCase记录"""
        run_cases = []
        
        for test_case in test_cases:
            run_case = RunCase(
                run_id=run_id,
                test_case_id=test_case.id,
                status='created'  # 修改为created,与状态机一致
            )
            self.db.add(run_case)
            run_cases.append(run_case)
        
        self.db.commit()
        
        # 刷新以获取ID
        for run_case in run_cases:
            self.db.refresh(run_case)
        
        return run_cases
    
    def _update_run_status(
        self,
        run_id: str,
        status: str,
        changed_by: str,
        reason: str
    ):
        """更新TestRun状态"""
        status_data = StatusUpdateRequest(
            status=status,
            changed_by=changed_by,
            reason=reason
        )
        
        self.test_run_service.update_run_status(run_id, status_data)
        print(f"  状态流转: → {status}")
    
    def _update_run_cases(
        self,
        run_cases: List[RunCase],
        execution_results: List[ExecutionResult],
        changed_by: str
    ):
        """更新RunCase状态和结果"""
        from core import TestCaseStatus
        
        # 创建结果映射
        results_map = {result.test_case_id: result for result in execution_results}
        
        for run_case in run_cases:
            result = results_map.get(run_case.test_case_id)
            if not result:
                continue
            
            # 处理枚举类型
            status = result.status
            if isinstance(status, TestCaseStatus):
                status_str = status.value if hasattr(status, 'value') else str(status).split('.')[-1].lower()
            else:
                status_str = str(status).lower()
            
            # 映射状态
            status_mapping = {
                'passed': 'passed',
                'failed': 'failed',
                'skipped': 'skipped',
                'error': 'failed'
            }
            new_status = status_mapping.get(status_str, 'failed')
            
            # 更新RunCase
            try:
                self.test_run_service.update_run_case_status(
                    run_case_id=run_case.id,
                    new_status=new_status,
                    changed_by=changed_by,
                    reason=f"执行结果: {status_str}"
                )
                
                # 更新详细信息
                updates = {
                    'start_time': result.start_time,
                    'end_time': result.end_time,
                    'duration': result.duration,
                    'error_message': result.error,
                    'error_type': result.error_type,
                    'stack_trace': result.stack_trace
                }
                
                from database.repository import BaseRepository
                repo = BaseRepository(RunCase, self.db)
                repo.update(run_case.id, updates)
                
            except Exception as e:
                print(f"  ⚠️  更新RunCase失败: {e}")
    
    def _calculate_statistics(self, results: List[ExecutionResult]) -> Dict[str, int]:
        """计算统计信息"""
        from core import TestCaseStatus
        
        stats = {
            'total': len(results),
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'error': 0
        }
        
        for result in results:
            # 处理枚举类型和字符串类型
            status = result.status
            if isinstance(status, TestCaseStatus):
                status_str = status.value if hasattr(status, 'value') else str(status).split('.')[-1].lower()
            else:
                status_str = str(status).lower()
            
            if status_str == 'passed':
                stats['passed'] += 1
            elif status_str == 'failed':
                stats['failed'] += 1
            elif status_str == 'skipped':
                stats['skipped'] += 1
            else:
                stats['error'] += 1
        
        return stats
    
    def _update_run_statistics(self, run_id: str, stats: Dict[str, int]):
        """更新TestRun统计信息"""
        from database.repository import BaseRepository
        from database.models import TestRun
        
        repo = BaseRepository(TestRun, self.db)
        repo.update(run_id, {
            'passed_cases': stats['passed'],
            'failed_cases': stats['failed'] + stats['error'],
            'skipped_cases': stats['skipped']
        })
    
    def _determine_final_status(self, stats: Dict[str, int]) -> str:
        """确定最终状态"""
        if stats['failed'] > 0 or stats['error'] > 0:
            return 'failed'
        elif stats['passed'] == stats['total']:
            return 'passed'
        elif stats['skipped'] == stats['total']:
            return 'aborted'
        else:
            return 'passed'  # 部分通过也算passed
    
    def create_run_step(
        self,
        run_case_id: int,
        step_name: str,
        step_order: int,
        changed_by: str = 'system'
    ) -> RunStep:
        """
        创建RunStep记录
        
        Args:
            run_case_id: RunCase ID
            step_name: 步骤名称
            step_order: 步骤顺序
            changed_by: 操作人
            
        Returns:
            RunStep: 创建的步骤记录
        """
        run_step = RunStep(
            run_case_id=run_case_id,
            step_name=step_name,
            step_order=step_order,
            status='pending'
        )
        
        self.db.add(run_step)
        self.db.commit()
        self.db.refresh(run_step)
        
        # 记录状态历史
        self.test_run_service._record_status_change(
            entity_type='run_step',
            entity_id=str(run_step.id),
            from_status=None,
            to_status='pending',
            changed_by=changed_by,
            reason='步骤创建'
        )
        
        return run_step
    
    def update_run_step_status(
        self,
        run_step_id: int,
        new_status: str,
        changed_by: str = 'system',
        reason: Optional[str] = None
    ):
        """更新RunStep状态"""
        self.test_run_service.update_run_step_status(
            run_step_id=run_step_id,
            new_status=new_status,
            changed_by=changed_by,
            reason=reason
        )

    
    def _record_execution_snapshot(
        self,
        run_step_id: int,
        test_case,
        result: ExecutionResult
    ):
        """
        记录执行快照(请求/响应)
        
        Args:
            run_step_id: RunStep ID
            test_case: 测试用例
            result: 执行结果
        """
        # 准备请求快照
        exec_config = test_case.execution_config or {}
        request_snapshot = {
            'method': exec_config.get('method', 'GET'),
            'url': exec_config.get('url', ''),
            'headers': self._mask_sensitive_headers(exec_config.get('headers', {})),
            'params': exec_config.get('params'),
            'json': exec_config.get('json'),
            'data': exec_config.get('data')
        }
        
        # 准备响应快照
        response_snapshot = None
        if result.response:
            response_snapshot = {
                'status_code': result.response.get('status_code'),
                'headers': dict(result.response.get('headers', {})),
                'body': self._truncate_body(result.response.get('body')),
                'response_time': result.response.get('response_time'),
                'encoding': result.response.get('encoding')
            }
        
        # 更新RunStep
        run_step = self.db.query(RunStep).filter(RunStep.id == run_step_id).first()
        if run_step:
            run_step.input_snapshot = request_snapshot
            run_step.output_snapshot = response_snapshot
            self.db.commit()
    
    def _mask_sensitive_headers(self, headers: Dict) -> Dict:
        """
        脱敏敏感请求头
        
        Args:
            headers: 原始请求头
            
        Returns:
            脱敏后的请求头
        """
        if not headers:
            return {}
        
        masked = headers.copy()
        sensitive_keys = ['authorization', 'cookie', 'x-api-key', 'api-key', 'token']
        
        for key in masked:
            if key.lower() in sensitive_keys:
                value = masked[key]
                if isinstance(value, str) and len(value) > 8:
                    # 保留前4位和后4位
                    masked[key] = f"{value[:4]}****{value[-4:]}"
                else:
                    masked[key] = "****"
        
        return masked
    
    def _truncate_body(self, body, max_length: int = 5000):
        """
        截断响应体
        
        Args:
            body: 响应体
            max_length: 最大长度
            
        Returns:
            截断后的响应体
        """
        if body is None:
            return None
        
        if isinstance(body, dict):
            import json
            body_str = json.dumps(body, ensure_ascii=False)
            if len(body_str) > max_length:
                return body_str[:max_length] + "...[truncated]"
            return body
        elif isinstance(body, str):
            if len(body) > max_length:
                return body[:max_length] + "...[truncated]"
            return body
        else:
            return str(body)[:max_length]
