"""
Task - 统一执行最小单元

最终目标：
- 统一执行最小单元
- 所有执行单元必须转成 Task
- 支持优先级调度
"""
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"      # 待执行
    RUNNING = "running"      # 执行中
    SUCCESS = "success"      # 成功
    FAILED = "failed"        # 失败


class TaskType(Enum):
    """任务类型枚举"""
    API = "api"
    UI = "ui"
    INTEGRATION = "integration"


class Task:
    """
    统一执行最小单元
    
    核心设计：
    1. 所有执行单元必须转成 Task
    2. status 包含：pending / running / success / failed
    3. 必须支持 priority
    
    使用场景：
    - Orchestrator 将 case 转换为 Task
    - TaskQueue 管理 Task 队列
    - Runner 执行 Task
    """
    
    def __init__(
        self,
        task_id: str,
        case: Dict[str, Any],
        task_type: str,
        priority: int = 1
    ):
        """
        初始化 Task
        
        Args:
            task_id: 任务唯一标识
            case: 测试用例数据
            task_type: 任务类型 (api/ui/integration)
            priority: 优先级 (1-10, 数字越大优先级越高)
        """
        self.id = task_id
        self.case = case
        self.task_type = task_type
        self.priority = priority
        
        # 状态管理
        self.status = TaskStatus.PENDING.value
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        
        # 时间戳
        self.created_at = datetime.now().isoformat()
        self.started_at: Optional[str] = None
        self.finished_at: Optional[str] = None
        
        # 执行信息
        self.duration: float = 0.0
        self.retry_count: int = 0
        self.max_retries: int = 3
    
    def start(self):
        """开始执行"""
        self.status = TaskStatus.RUNNING.value
        self.started_at = datetime.now().isoformat()
    
    def succeed(self, result: Dict[str, Any]):
        """执行成功"""
        self.status = TaskStatus.SUCCESS.value
        self.result = result
        self.finished_at = datetime.now().isoformat()
        self._calculate_duration()
    
    def fail(self, error: str):
        """执行失败"""
        self.status = TaskStatus.FAILED.value
        self.error = error
        self.finished_at = datetime.now().isoformat()
        self._calculate_duration()
    
    def retry(self):
        """重试"""
        self.retry_count += 1
        self.status = TaskStatus.PENDING.value
        self.error = None
    
    def can_retry(self) -> bool:
        """是否可以重试"""
        return self.retry_count < self.max_retries
    
    def _calculate_duration(self):
        """计算执行时长"""
        if self.started_at and self.finished_at:
            start = datetime.fromisoformat(self.started_at)
            finish = datetime.fromisoformat(self.finished_at)
            self.duration = (finish - start).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "case": self.case,
            "task_type": self.task_type,
            "priority": self.priority,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration": self.duration,
            "retry_count": self.retry_count
        }
    
    @classmethod
    def from_case(
        cls,
        case: Dict[str, Any],
        task_type: str,
        priority: int = 1
    ) -> 'Task':
        """
        从测试用例创建 Task
        
        Args:
            case: 测试用例数据
            task_type: 任务类型
            priority: 优先级
            
        Returns:
            Task 实例
        """
        task_id = case.get('id', f"task_{datetime.now().timestamp()}")
        return cls(task_id, case, task_type, priority)
    
    def __repr__(self) -> str:
        """字符串表示"""
        return f"Task(id={self.id}, type={self.task_type}, status={self.status}, priority={self.priority})"
    
    def __lt__(self, other: 'Task') -> bool:
        """比较优先级（用于优先级队列）"""
        # 优先级高的排在前面
        return self.priority > other.priority
    
    def __eq__(self, other: 'Task') -> bool:
        """相等比较"""
        return self.id == other.id
    
    def __hash__(self) -> int:
        """哈希值"""
        return hash(self.id)


class TaskFactory:
    """Task 工厂类"""
    
    @staticmethod
    def create_from_case(
        case: Dict[str, Any],
        task_type: str,
        priority: int = 1
    ) -> Task:
        """
        从测试用例创建 Task
        
        Args:
            case: 测试用例数据
            task_type: 任务类型
            priority: 优先级
            
        Returns:
            Task 实例
        """
        return Task.from_case(case, task_type, priority)
    
    @staticmethod
    def create_batch_from_cases(
        cases: list,
        task_type: str,
        priority: int = 1
    ) -> list:
        """
        批量创建 Task
        
        Args:
            cases: 测试用例列表
            task_type: 任务类型
            priority: 优先级
            
        Returns:
            Task 列表
        """
        return [
            Task.from_case(case, task_type, priority)
            for case in cases
        ]
    
    @staticmethod
    def create_from_strategy(
        strategy: Dict[str, Any],
        priority_map: Optional[Dict[str, int]] = None
    ) -> list:
        """
        从策略创建 Task 列表
        
        Args:
            strategy: 策略数据
            priority_map: 优先级映射 (test_type -> priority)
            
        Returns:
            Task 列表
        """
        if priority_map is None:
            priority_map = {
                "api": 3,
                "ui": 2,
                "integration": 1
            }
        
        tasks = []
        
        for module_strategy in strategy.get('strategy', []):
            module_name = module_strategy.get('module', {}).get('name', '未知')
            test_types = module_strategy.get('test_types', [])
            
            for test_type in test_types:
                # 创建虚拟用例
                case = {
                    "id": f"{module_name}_{test_type}",
                    "title": f"{module_name} - {test_type} 测试",
                    "module": module_name,
                    "type": test_type
                }
                
                priority = priority_map.get(test_type, 1)
                task = Task.from_case(case, test_type, priority)
                tasks.append(task)
        
        return tasks


# 便捷函数
def create_task(
    task_id: str,
    case: Dict[str, Any],
    task_type: str,
    priority: int = 1
) -> Task:
    """创建 Task"""
    return Task(task_id, case, task_type, priority)


def create_tasks_from_cases(
    cases: list,
    task_type: str,
    priority: int = 1
) -> list:
    """从用例列表创建 Task 列表"""
    return TaskFactory.create_batch_from_cases(cases, task_type, priority)
