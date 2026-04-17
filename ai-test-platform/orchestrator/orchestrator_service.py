"""
Orchestrator Service - 测试执行调度服务（V3 重构版）

最终目标：
- Orchestrator = 调度中心
- 支持并发（线程数可配置）
- 不直接执行 case
- 不包含修复逻辑

架构：
- Task: 统一执行单元
- TaskQueue: 任务队列
- Worker: 并发执行线程
- Executor: 执行分发器
"""
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from .task import Task, TaskFactory
from .task_queue import TaskQueue
from .worker import WorkerPool
from .base_runner import get_runner


class OrchestratorService:
    """
    测试执行调度服务（V3 重构版）
    
    核心设计：
    1. 支持并发（线程数可配置）
    2. 不直接执行 case（通过 Worker + Executor）
    3. 不包含修复逻辑（Healing 独立）
    
    职责：
    - 构建任务（Task）
    - 管理任务队列（TaskQueue）
    - 启动 Worker 线程池
    - 收集执行结果
    """
    
    def __init__(self, num_workers: int = 5):
        """
        初始化调度服务
        
        Args:
            num_workers: Worker 线程数（默认5）
        """
        self.num_workers = num_workers
        self.execution_history = []
        self.log_dir = Path("output/orchestrator_logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def run(self, context: dict) -> dict:
        """
        执行测试（V3 重构版）
        
        流程：
        1. 构建任务（Task）
        2. 添加到任务队列（TaskQueue）
        3. 启动 Worker 线程池
        4. 等待执行完成
        5. 收集结果
        
        Args:
            context: 执行上下文
            {
                "cases": [
                    {
                        "module": "支付模块",
                        "cases": [...]
                    }
                ],
                "num_workers": 5  # 可选，覆盖默认值
            }
            
        Returns:
            {
                "results": [Task列表],
                "failures": [失败的Task列表],
                "summary": {...},
                "executed_at": "..."
            }
        """
        try:
            start_time = time.time()
            
            # 1. 提取用例
            module_cases_list = context.get('cases', [])
            
            if not module_cases_list:
                print("⏭️  用例为空，无需执行")
                return self._empty_result()
            
            # 获取 Worker 数量
            num_workers = context.get('num_workers', self.num_workers)
            
            print(f"🚀 开始执行（V3调度模式）: {len(module_cases_list)}个模块, {num_workers}个Worker")
            
            # 2. 构建任务
            task_queue = TaskQueue()
            result_list = []
            failure_queue = TaskQueue()
            
            total_tasks = self._build_tasks(module_cases_list, task_queue)
            
            print(f"✅ 构建任务: {total_tasks} 个")
            
            # 3. 启动 Worker 线程池
            pool = WorkerPool(
                num_workers=num_workers,
                task_queue=task_queue,
                result_list=result_list,
                failure_queue=failure_queue
            )
            
            pool.start()
            
            # 4. 等待执行完成
            pool.wait_completion(timeout=300)  # 5分钟超时
            
            # 5. 停止线程池
            pool.stop()
            
            # 6. 收集结果
            total_duration = time.time() - start_time
            
            # 获取失败任务
            failed_tasks = failure_queue.get_all_tasks()
            
            # 构建摘要
            summary = self._build_summary_v3(result_list, failed_tasks, total_duration)
            
            # 7. 构建最终结果
            final_result = {
                "results": [task.to_dict() for task in result_list],
                "failures": [task.to_dict() for task in failed_tasks],
                "summary": summary,
                "executed_at": datetime.now().isoformat(),
                "mode": "v3_scheduler"
            }
            
            # 8. 记录历史
            self._log_execution(context, final_result)
            
            print(f"\n✅ 执行完成: {summary['passed']}/{summary['total']} 通过")
            
            return final_result
            
        except Exception as e:
            print(f"❌ 执行失败: {e}")
            import traceback
            traceback.print_exc()
            return self._empty_result()
    
    def _build_tasks(self, module_cases_list: List[Dict[str, Any]], task_queue: TaskQueue) -> int:
        """
        构建任务
        
        流程：
        1. 遍历模块
        2. 遍历 cases
        3. 为每个 case 创建 Task
        4. 添加到任务队列
        
        Args:
            module_cases_list: 模块用例列表
            task_queue: 任务队列
            
        Returns:
            任务总数
        """
        total_tasks = 0
        
        for module_cases in module_cases_list:
            module_name = module_cases.get('module', '未知模块')
            test_cases = module_cases.get('cases', [])
            
            print(f"  📦 构建任务: {module_name} ({len(test_cases)}个用例)")
            
            for case in test_cases:
                # 确定任务类型
                task_type = self._get_task_type(case)
                
                # 确定优先级
                priority = self._get_priority(case)
                
                # 创建 Task
                task = Task(
                    task_id=str(uuid4()),
                    case=case,
                    task_type=task_type,
                    priority=priority
                )
                
                # 添加到队列
                task_queue.add_task(task)
                total_tasks += 1
        
        return total_tasks
    
    def _get_task_type(self, case: Dict[str, Any]) -> str:
        """
        获取任务类型
        
        根据 case.type 映射到 task_type
        """
        case_type = case.get('type', '功能测试').lower()
        
        if 'api' in case_type or '接口' in case_type or '功能' in case_type:
            return "api"
        elif 'ui' in case_type or '界面' in case_type:
            return "ui"
        elif 'integration' in case_type or '集成' in case_type:
            return "integration"
        else:
            return "api"  # 默认
    
    def _get_priority(self, case: Dict[str, Any]) -> int:
        """
        获取优先级
        
        优先级规则：
        - P0: 10
        - P1: 8
        - P2: 5
        - P3: 3
        - 默认: 5
        """
        priority_str = case.get('priority', 'P2')
        
        priority_map = {
            'P0': 10,
            'P1': 8,
            'P2': 5,
            'P3': 3
        }
        
        return priority_map.get(priority_str, 5)
    
    def _build_summary_v3(self, result_list: List[Task], failed_tasks: List[Task], duration: float) -> Dict[str, Any]:
        """
        构建执行摘要（V3版本）
        
        Args:
            result_list: 成功的任务列表
            failed_tasks: 失败的任务列表
            duration: 执行时长
            
        Returns:
            摘要信息
        """
        total = len(result_list) + len(failed_tasks)
        passed = len(result_list)
        failed = len(failed_tasks)
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "duration": round(duration, 2),
            "pass_rate": round(passed / total * 100, 2) if total > 0 else 0.0
        }
    
    def _empty_result(self) -> dict:
        """返回空结果"""
        return {
            "results": [],
            "failures": [],
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "duration": 0.0,
                "pass_rate": 0.0
            },
            "executed_at": datetime.now().isoformat(),
            "mode": "v3_scheduler"
        }
    
    def _log_execution(self, input_data: dict, result: dict):
        """记录执行历史"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "input_summary": input_data.get('summary', {}),
                "execution_result": result
            }
            
            self.execution_history.append(log_entry)
            
            # 保存到文件
            log_file = self.log_dir / f"execution_{datetime.now().strftime('%Y%m%d')}.jsonl"
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
                
        except Exception as e:
            print(f"⚠️  记录执行历史失败: {e}")
    
    def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取执行历史"""
        return self.execution_history[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.execution_history:
            return {
                "total_executions": 0,
                "total_tests": 0,
                "total_passed": 0,
                "total_failed": 0,
                "avg_pass_rate": 0.0
            }
        
        total_executions = len(self.execution_history)
        total_tests = sum(e['execution_result']['summary']['total'] for e in self.execution_history)
        total_passed = sum(e['execution_result']['summary']['passed'] for e in self.execution_history)
        total_failed = sum(e['execution_result']['summary']['failed'] for e in self.execution_history)
        
        avg_pass_rate = round(total_passed / total_tests * 100, 2) if total_tests > 0 else 0.0
        
        return {
            "total_executions": total_executions,
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "avg_pass_rate": avg_pass_rate
        }


# 全局服务实例
_orchestrator_service = None

def get_orchestrator_service(num_workers: int = 5) -> OrchestratorService:
    """
    获取调度服务实例
    
    Args:
        num_workers: Worker 线程数（默认5）
        
    Returns:
        OrchestratorService 实例
    """
    global _orchestrator_service
    if _orchestrator_service is None:
        _orchestrator_service = OrchestratorService(num_workers=num_workers)
    return _orchestrator_service
