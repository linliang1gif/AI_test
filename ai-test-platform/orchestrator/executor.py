"""
Executor - 任务执行分发器

最终目标：
- 执行解耦
- 不允许写业务逻辑
- 只做分发
- Runner 独立实现
"""
from typing import Dict, Any
from .task import Task, TaskStatus
from .base_runner import ApiRunner, UiRunner, IntegrationRunner


class TaskExecutor:
    """
    任务执行分发器
    
    核心设计：
    1. 不允许写业务逻辑
    2. 只做分发（根据 task_type 分发到对应 Runner）
    3. Runner 独立实现
    
    职责：
    - 根据任务类型分发到对应 Runner
    - 更新任务状态
    - 返回执行结果
    """
    
    def __init__(self):
        """初始化执行器"""
        # 初始化所有 Runner
        self.api_runner = ApiRunner()
        self.ui_runner = UiRunner()
        self.integration_runner = IntegrationRunner()
    
    def execute_task(self, task: Task) -> Dict[str, Any]:
        """
        执行任务（分发逻辑）
        
        核心逻辑：
        1. 根据 task.task_type 分发到对应 Runner
        2. 调用 Runner 的 run_cases() 方法
        3. 更新任务状态
        4. 返回结果
        
        Args:
            task: Task 实例
            
        Returns:
            执行结果
        """
        # 更新任务状态为 running
        task.start()
        
        try:
            # 分发到对应 Runner
            result = self._dispatch(task)
            
            # 更新任务状态为 success
            task.succeed(result)
            
            return result
            
        except Exception as e:
            # 更新任务状态为 failed
            error_msg = f"执行失败: {str(e)}"
            task.fail(error_msg)
            
            return {
                "status": "failed",
                "duration": 0.0,
                "details": error_msg
            }
    
    def _dispatch(self, task: Task) -> Dict[str, Any]:
        """
        分发逻辑（核心）
        
        根据 task.task_type 分发到对应 Runner
        
        Args:
            task: Task 实例
            
        Returns:
            执行结果
        """
        task_type = task.task_type
        case = task.case
        
        # 分发到对应 Runner
        if task_type == "api":
            return self._run_api(case)
        
        elif task_type == "ui":
            return self._run_ui(case)
        
        elif task_type == "integration":
            return self._run_integration(case)
        
        else:
            raise ValueError(f"不支持的任务类型: {task_type}")
    
    def _run_api(self, case: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行 API 测试
        
        Args:
            case: 测试用例
            
        Returns:
            执行结果
        """
        # 调用 ApiRunner
        return self.api_runner.run_cases([case])
    
    def _run_ui(self, case: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行 UI 测试
        
        Args:
            case: 测试用例
            
        Returns:
            执行结果
        """
        # 调用 UiRunner
        return self.ui_runner.run_cases([case])
    
    def _run_integration(self, case: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行集成测试
        
        Args:
            case: 测试用例
            
        Returns:
            执行结果
        """
        # 调用 IntegrationRunner
        return self.integration_runner.run_cases([case])


# 全局执行器实例
_executor = None


def get_executor() -> TaskExecutor:
    """获取执行器实例（单例）"""
    global _executor
    if _executor is None:
        _executor = TaskExecutor()
    return _executor


def execute_task(task: Task) -> Dict[str, Any]:
    """
    执行任务（便捷函数）
    
    这是对外暴露的主要接口
    
    Args:
        task: Task 实例
        
    Returns:
        执行结果
    """
    executor = get_executor()
    return executor.execute_task(task)
