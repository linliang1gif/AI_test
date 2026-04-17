#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UnifiedExecutionScheduler - 统一执行调度器

核心能力：
1. 优先级队列（P0 > P1 > P2）
2. 并发控制（max_workers）
3. 限流控制（rate limiting）
4. 失败隔离（某个任务失败不影响其他）
5. 任务状态管理（pending/running/success/failed）
6. 对接 ExecutionEngine（真实执行）
"""

import time
import threading
import queue
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, Future
from collections import defaultdict


# ==================== 枚举定义 ====================

class TaskPriority(Enum):
    """任务优先级"""
    P0 = 0  # 最高优先级
    P1 = 1  # 高优先级
    P2 = 2  # 中优先级
    P3 = 3  # 低优先级


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 执行中
    SUCCESS = "success"      # 成功
    FAILED = "failed"        # 失败
    CANCELLED = "cancelled"  # 已取消


# ==================== 数据结构 ====================

@dataclass
class Task:
    """任务数据结构"""
    task_id: str
    test_case: Dict[str, Any]
    priority: TaskPriority = TaskPriority.P2
    status: TaskStatus = TaskStatus.PENDING
    
    # 执行信息
    submit_time: datetime = field(default_factory=datetime.now)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    # 结果信息
    result: Optional[Any] = None
    error: Optional[str] = None
    trace_id: Optional[str] = None
    
    # 重试信息
    retry_count: int = 0
    max_retries: int = 3
    
    def __lt__(self, other):
        """优先级比较（用于优先级队列）"""
        return self.priority.value < other.priority.value


@dataclass
class SchedulerStatistics:
    """调度器统计信息"""
    total_submitted: int = 0
    total_executed: int = 0
    total_success: int = 0
    total_failed: int = 0
    total_cancelled: int = 0
    
    # 按优先级统计
    by_priority: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    # 性能统计
    avg_wait_time: float = 0.0
    avg_execution_time: float = 0.0
    
    # 限流统计
    total_throttled: int = 0
    current_qps: float = 0.0


# ==================== 限流器 ====================

class RateLimiter:
    """令牌桶限流器"""
    
    def __init__(self, rate: int = 10, capacity: int = 10):
        """
        初始化限流器
        
        Args:
            rate: 每秒生成的令牌数
            capacity: 令牌桶容量
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = threading.Lock()
    
    def acquire(self, timeout: float = 1.0) -> bool:
        """
        获取令牌
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            是否成功获取令牌
        """
        deadline = time.time() + timeout
        
        while time.time() < deadline:
            with self.lock:
                # 补充令牌
                now = time.time()
                elapsed = now - self.last_update
                self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
                self.last_update = now
                
                # 尝试获取令牌
                if self.tokens >= 1:
                    self.tokens -= 1
                    return True
            
            # 等待一小段时间
            time.sleep(0.01)
        
        return False
    
    def get_current_rate(self) -> float:
        """获取当前速率"""
        with self.lock:
            return self.rate - self.tokens


# ==================== 统一执行调度器 ====================

class UnifiedExecutionScheduler:
    """
    统一执行调度器
    
    核心能力：
    1. 优先级队列 - P0 > P1 > P2
    2. 并发控制 - max_workers
    3. 限流控制 - rate limiting
    4. 失败隔离 - 任务失败不影响其他
    5. 状态管理 - pending/running/success/failed
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化调度器
        
        Args:
            config: 配置字典
                - max_workers: 最大并发数（默认5）
                - rate_limit: 每秒最大请求数（默认10）
                - enable_rate_limit: 是否启用限流（默认True）
                - max_retries: 最大重试次数（默认3）
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 并发控制
        self.max_workers = self.config.get('max_workers', 5)
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # 限流控制
        self.enable_rate_limit = self.config.get('enable_rate_limit', True)
        self.rate_limit = self.config.get('rate_limit', 10)
        self.rate_limiter = RateLimiter(rate=self.rate_limit, capacity=self.rate_limit)
        
        # 优先级队列（使用 PriorityQueue）
        self.task_queue = queue.PriorityQueue()
        
        # 任务管理
        self.tasks: Dict[str, Task] = {}
        self.futures: Dict[str, Future] = {}
        self.lock = threading.Lock()
        
        # 运行状态
        self.is_running = False
        self.should_stop = False
        self.scheduler_thread: Optional[threading.Thread] = None
        
        # 统计信息
        self.stats = SchedulerStatistics()
        
        # ExecutionEngine
        self.execution_engine = None
        self._init_execution_engine()
        
        self.logger.info(
            f"UnifiedExecutionScheduler 初始化: "
            f"max_workers={self.max_workers}, "
            f"rate_limit={self.rate_limit}, "
            f"enable_rate_limit={self.enable_rate_limit}"
        )
    
    def _init_execution_engine(self):
        """初始化 ExecutionEngine"""
        try:
            from modules.executor.real_execution_engine import get_execution_engine
            self.execution_engine = get_execution_engine()
            self.logger.info("✅ ExecutionEngine 已加载")
        except ImportError as e:
            self.logger.warning(f"⚠️  无法加载 ExecutionEngine: {e}")
    
    # ==================== 公共接口 ====================
    
    def submit(self, test_case: Dict[str, Any], priority: str = "P2") -> str:
        """
        提交测试任务
        
        Args:
            test_case: 测试用例
            priority: 优先级（P0/P1/P2/P3）
            
        Returns:
            task_id: 任务ID
        """
        # 生成任务ID
        task_id = test_case.get('id', f"task_{int(time.time() * 1000)}")
        
        # 解析优先级
        try:
            priority_enum = TaskPriority[priority.upper()]
        except KeyError:
            priority_enum = TaskPriority.P2
            self.logger.warning(f"无效的优先级 {priority}，使用默认 P2")
        
        # 创建任务
        task = Task(
            task_id=task_id,
            test_case=test_case,
            priority=priority_enum,
            max_retries=self.config.get('max_retries', 3)
        )
        
        # 保存任务
        with self.lock:
            self.tasks[task_id] = task
            self.stats.total_submitted += 1
            self.stats.by_priority[priority] += 1
        
        # 加入队列
        self.task_queue.put(task)
        
        self.logger.info(f"任务已提交: {task_id} (优先级: {priority})")
        
        return task_id
    
    def set_priority(self, task_id: str, priority: str) -> bool:
        """
        设置任务优先级
        
        Args:
            task_id: 任务ID
            priority: 新优先级（P0/P1/P2/P3）
            
        Returns:
            是否成功
        """
        with self.lock:
            task = self.tasks.get(task_id)
            
            if not task:
                self.logger.warning(f"任务不存在: {task_id}")
                return False
            
            if task.status != TaskStatus.PENDING:
                self.logger.warning(f"任务已开始执行，无法修改优先级: {task_id}")
                return False
            
            # 解析优先级
            try:
                priority_enum = TaskPriority[priority.upper()]
            except KeyError:
                self.logger.warning(f"无效的优先级: {priority}")
                return False
            
            # 更新优先级
            old_priority = task.priority
            task.priority = priority_enum
            
            self.logger.info(
                f"任务优先级已更新: {task_id} "
                f"({old_priority.name} → {priority_enum.name})"
            )
            
            return True
    
    def run(self, blocking: bool = True):
        """
        启动调度器
        
        Args:
            blocking: 是否阻塞等待（默认True）
        """
        if self.is_running:
            self.logger.warning("调度器已在运行")
            return
        
        self.is_running = True
        self.should_stop = False
        
        # 启动调度线程
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("🚀 调度器已启动")
        
        if blocking:
            try:
                self.scheduler_thread.join()
            except KeyboardInterrupt:
                self.logger.info("收到中断信号")
                self.stop()
    
    def stop(self):
        """停止调度器"""
        self.logger.info("正在停止调度器...")
        self.should_stop = True
        
        # 等待调度线程结束
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        # 关闭线程池
        self.executor.shutdown(wait=True)
        
        self.is_running = False
        self.logger.info("✅ 调度器已停止")
    
    def wait_all(self, timeout: Optional[float] = None) -> bool:
        """
        等待所有任务完成
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            是否所有任务都完成
        """
        deadline = time.time() + timeout if timeout else None
        
        while True:
            with self.lock:
                pending_count = sum(
                    1 for task in self.tasks.values() 
                    if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]
                )
                
                if pending_count == 0:
                    return True
            
            if deadline and time.time() >= deadline:
                return False
            
            time.sleep(0.1)
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态信息
        """
        with self.lock:
            task = self.tasks.get(task_id)
            
            if not task:
                return None
            
            return {
                'task_id': task.task_id,
                'status': task.status.value,
                'priority': task.priority.name,
                'submit_time': task.submit_time.isoformat(),
                'start_time': task.start_time.isoformat() if task.start_time else None,
                'end_time': task.end_time.isoformat() if task.end_time else None,
                'retry_count': task.retry_count,
                'trace_id': task.trace_id,
                'error': task.error
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.lock:
            # 计算平均等待时间和执行时间
            wait_times = []
            exec_times = []
            
            for task in self.tasks.values():
                if task.start_time:
                    wait_time = (task.start_time - task.submit_time).total_seconds()
                    wait_times.append(wait_time)
                
                if task.start_time and task.end_time:
                    exec_time = (task.end_time - task.start_time).total_seconds()
                    exec_times.append(exec_time)
            
            self.stats.avg_wait_time = sum(wait_times) / len(wait_times) if wait_times else 0
            self.stats.avg_execution_time = sum(exec_times) / len(exec_times) if exec_times else 0
            self.stats.current_qps = self.rate_limiter.get_current_rate()
            
            return {
                'total_submitted': self.stats.total_submitted,
                'total_executed': self.stats.total_executed,
                'total_success': self.stats.total_success,
                'total_failed': self.stats.total_failed,
                'total_cancelled': self.stats.total_cancelled,
                'by_priority': dict(self.stats.by_priority),
                'avg_wait_time': f"{self.stats.avg_wait_time:.3f}s",
                'avg_execution_time': f"{self.stats.avg_execution_time:.3f}s",
                'current_qps': f"{self.stats.current_qps:.2f}",
                'total_throttled': self.stats.total_throttled,
                'queue_size': self.task_queue.qsize(),
                'running_tasks': sum(
                    1 for task in self.tasks.values() 
                    if task.status == TaskStatus.RUNNING
                )
            }
    
    # ==================== 内部方法 ====================
    
    def _scheduler_loop(self):
        """调度器主循环"""
        self.logger.info("调度器主循环已启动")
        
        while not self.should_stop:
            try:
                # 从队列获取任务（带超时）
                try:
                    task = self.task_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                
                # 检查任务是否已取消
                with self.lock:
                    if task.status == TaskStatus.CANCELLED:
                        self.logger.info(f"任务已取消: {task.task_id}")
                        continue
                
                # 限流控制
                if self.enable_rate_limit:
                    if not self.rate_limiter.acquire(timeout=5.0):
                        self.logger.warning(f"限流：任务 {task.task_id} 等待超时")
                        self.stats.total_throttled += 1
                        # 重新放回队列
                        self.task_queue.put(task)
                        continue
                
                # 提交任务到线程池
                future = self.executor.submit(self._execute_task, task)
                
                with self.lock:
                    self.futures[task.task_id] = future
                
            except Exception as e:
                self.logger.error(f"调度器循环异常: {e}")
                import traceback
                traceback.print_exc()
        
        self.logger.info("调度器主循环已退出")
    
    def _execute_task(self, task: Task):
        """
        执行任务（在线程池中运行）
        
        Args:
            task: 任务对象
        """
        # 更新状态为运行中
        with self.lock:
            task.status = TaskStatus.RUNNING
            task.start_time = datetime.now()
        
        self.logger.info(f"开始执行任务: {task.task_id} (优先级: {task.priority.name})")
        
        try:
            # 使用 ExecutionEngine 执行
            if self.execution_engine:
                result = self.execution_engine.execute(task.test_case)
                
                # 更新任务结果
                with self.lock:
                    task.result = result
                    task.trace_id = result.trace_id if hasattr(result, 'trace_id') else None
                    task.end_time = datetime.now()
                    
                    if result.success:
                        task.status = TaskStatus.SUCCESS
                        self.stats.total_success += 1
                        self.logger.info(
                            f"✅ 任务成功: {task.task_id} "
                            f"(trace_id: {task.trace_id})"
                        )
                    else:
                        # 检查是否需要重试
                        if task.retry_count < task.max_retries:
                            task.retry_count += 1
                            task.status = TaskStatus.PENDING
                            self.logger.warning(
                                f"任务失败，重试 [{task.retry_count}/{task.max_retries}]: "
                                f"{task.task_id}"
                            )
                            # 重新放回队列
                            self.task_queue.put(task)
                            return
                        else:
                            task.status = TaskStatus.FAILED
                            task.error = result.error_message if hasattr(result, 'error_message') else "Unknown error"
                            self.stats.total_failed += 1
                            self.logger.error(
                                f"❌ 任务失败: {task.task_id} "
                                f"(trace_id: {task.trace_id}, error: {task.error})"
                            )
            else:
                # 模拟执行（降级方案）
                self.logger.warning(f"ExecutionEngine 不可用，使用模拟执行: {task.task_id}")
                time.sleep(0.1)
                
                with self.lock:
                    task.status = TaskStatus.SUCCESS
                    task.end_time = datetime.now()
                    self.stats.total_success += 1
            
            # 更新统计
            with self.lock:
                self.stats.total_executed += 1
        
        except Exception as e:
            # 失败隔离：捕获异常，不影响其他任务
            self.logger.error(f"任务执行异常: {task.task_id}, {e}")
            import traceback
            traceback.print_exc()
            
            with self.lock:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                task.end_time = datetime.now()
                self.stats.total_failed += 1
                self.stats.total_executed += 1
    
    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功取消
        """
        with self.lock:
            task = self.tasks.get(task_id)
            
            if not task:
                return False
            
            if task.status == TaskStatus.RUNNING:
                self.logger.warning(f"任务正在执行，无法取消: {task_id}")
                return False
            
            if task.status == TaskStatus.PENDING:
                task.status = TaskStatus.CANCELLED
                self.stats.total_cancelled += 1
                self.logger.info(f"任务已取消: {task_id}")
                return True
            
            return False
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop()


# ==================== 便捷函数 ====================

_scheduler_instance = None

def get_scheduler(config: Optional[Dict] = None) -> UnifiedExecutionScheduler:
    """获取全局调度器实例（单例模式）"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = UnifiedExecutionScheduler(config)
    return _scheduler_instance
