"""
TaskQueue - 任务队列

最终目标：
- 解耦任务生产与执行
- 支持优先级调度
- 支持并发安全
- 不允许直接执行任务
"""
from queue import PriorityQueue, Empty
from threading import Lock
from typing import Optional, List
from datetime import datetime

from .task import Task, TaskStatus


class TaskQueue:
    """
    任务队列
    
    核心设计：
    1. 支持优先级调度（优先级高的先执行）
    2. 支持并发安全（线程安全）
    3. 不允许直接执行任务（只负责队列管理）
    
    职责：
    - 任务入队（add_task）
    - 任务出队（get_task）
    - 队列状态查询（size, is_empty, peek）
    - 任务查询（get_all_tasks, get_tasks_by_status）
    """
    
    def __init__(self, max_size: int = 0):
        """
        初始化任务队列
        
        Args:
            max_size: 队列最大容量（0表示无限制）
        """
        # 优先级队列（线程安全）
        self.queue = PriorityQueue(maxsize=max_size)
        
        # 任务索引（用于快速查询）
        self.task_index = {}  # task_id -> task
        self.index_lock = Lock()  # 索引锁
        
        # 统计信息
        self.total_added = 0
        self.total_completed = 0
        
        # 创建时间
        self.created_at = datetime.now().isoformat()
    
    def add_task(self, task: Task) -> bool:
        """
        添加任务到队列
        
        Args:
            task: Task 实例
            
        Returns:
            是否添加成功
        """
        try:
            # 优先级取负数（PriorityQueue 是最小堆，负数优先级高）
            # 例如：priority=5 -> -5，priority=3 -> -3
            # -5 < -3，所以 priority=5 的任务先出队
            priority = -task.priority
            
            # 入队（元组：(优先级, 任务ID, 任务对象)）
            # 添加任务ID是为了在优先级相同时按照添加顺序排序
            self.queue.put((priority, task.id, task), block=False)
            
            # 更新索引
            with self.index_lock:
                self.task_index[task.id] = task
                self.total_added += 1
            
            return True
            
        except Exception as e:
            print(f"⚠️  添加任务失败: {e}")
            return False
    
    def get_task(self, block: bool = True, timeout: Optional[float] = None) -> Optional[Task]:
        """
        从队列获取任务（按优先级）
        
        Args:
            block: 是否阻塞等待
            timeout: 超时时间（秒）
            
        Returns:
            Task 实例，如果队列为空返回 None
        """
        try:
            # 出队
            priority, task_id, task = self.queue.get(block=block, timeout=timeout)
            
            # 不从索引中删除（保留用于查询）
            # 只在任务完成时更新统计
            
            return task
            
        except Empty:
            return None
        except Exception as e:
            print(f"⚠️  获取任务失败: {e}")
            return None
    
    def add_tasks(self, tasks: List[Task]) -> int:
        """
        批量添加任务
        
        Args:
            tasks: Task 列表
            
        Returns:
            成功添加的任务数量
        """
        success_count = 0
        
        for task in tasks:
            if self.add_task(task):
                success_count += 1
        
        return success_count
    
    def size(self) -> int:
        """获取队列大小"""
        return self.queue.qsize()
    
    def is_empty(self) -> bool:
        """判断队列是否为空"""
        return self.queue.empty()
    
    def is_full(self) -> bool:
        """判断队列是否已满"""
        return self.queue.full()
    
    def peek(self) -> Optional[Task]:
        """
        查看队列头部任务（不出队）
        
        注意：PriorityQueue 不支持 peek，这里通过索引实现
        """
        with self.index_lock:
            if not self.task_index:
                return None
            
            # 找到优先级最高的待执行任务
            pending_tasks = [
                t for t in self.task_index.values()
                if t.status == TaskStatus.PENDING.value
            ]
            
            if not pending_tasks:
                return None
            
            # 按优先级排序
            return max(pending_tasks, key=lambda t: t.priority)
    
    def get_all_tasks(self) -> List[Task]:
        """获取所有任务（包括已完成的）"""
        with self.index_lock:
            return list(self.task_index.values())
    
    def get_tasks_by_status(self, status: str) -> List[Task]:
        """
        按状态获取任务
        
        Args:
            status: 任务状态 (pending/running/success/failed)
            
        Returns:
            任务列表
        """
        with self.index_lock:
            return [
                task for task in self.task_index.values()
                if task.status == status
            ]
    
    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """
        根据ID获取任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            Task 实例，如果不存在返回 None
        """
        with self.index_lock:
            return self.task_index.get(task_id)
    
    def mark_task_completed(self, task_id: str):
        """
        标记任务完成（用于统计）
        
        Args:
            task_id: 任务ID
        """
        with self.index_lock:
            if task_id in self.task_index:
                task = self.task_index[task_id]
                if task.status in [TaskStatus.SUCCESS.value, TaskStatus.FAILED.value]:
                    self.total_completed += 1
    
    def clear(self):
        """清空队列"""
        # 清空优先级队列
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except Empty:
                break
        
        # 清空索引
        with self.index_lock:
            self.task_index.clear()
            self.total_added = 0
            self.total_completed = 0
    
    def get_statistics(self) -> dict:
        """
        获取队列统计信息
        
        Returns:
            统计信息字典
        """
        with self.index_lock:
            pending = len([t for t in self.task_index.values() if t.status == TaskStatus.PENDING.value])
            running = len([t for t in self.task_index.values() if t.status == TaskStatus.RUNNING.value])
            success = len([t for t in self.task_index.values() if t.status == TaskStatus.SUCCESS.value])
            failed = len([t for t in self.task_index.values() if t.status == TaskStatus.FAILED.value])
            
            return {
                "queue_size": self.size(),
                "total_tasks": len(self.task_index),
                "pending": pending,
                "running": running,
                "success": success,
                "failed": failed,
                "total_added": self.total_added,
                "total_completed": self.total_completed,
                "created_at": self.created_at
            }
    
    def __repr__(self) -> str:
        """字符串表示"""
        return f"TaskQueue(size={self.size()}, total={len(self.task_index)})"
    
    def __len__(self) -> int:
        """队列长度"""
        return self.size()


# 便捷函数
def create_task_queue(max_size: int = 0) -> TaskQueue:
    """创建任务队列"""
    return TaskQueue(max_size=max_size)
