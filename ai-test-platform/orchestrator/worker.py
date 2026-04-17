"""
Worker - 任务执行线程

最终目标：
- 支持并发执行
- 必须独立线程
- 不允许直接依赖 Pipeline
- 执行逻辑必须可扩展
"""
import threading
from typing import List, Optional
from queue import Empty
import time

from .task import Task, TaskStatus
from .task_queue import TaskQueue
from .executor import get_executor


class Worker(threading.Thread):
    """
    任务执行线程
    
    核心设计：
    1. 必须独立线程（继承 threading.Thread）
    2. 不允许直接依赖 Pipeline
    3. 执行逻辑必须可扩展（通过 Executor 分发）
    
    职责：
    - 从队列获取任务
    - 调用 Executor 执行任务
    - 处理执行结果
    - 处理失败任务（重试或放入失败队列）
    """
    
    def __init__(
        self,
        worker_id: str,
        task_queue: TaskQueue,
        result_list: List[Task],
        failure_queue: TaskQueue,
        stop_event: Optional[threading.Event] = None
    ):
        """
        初始化 Worker
        
        Args:
            worker_id: Worker 唯一标识
            task_queue: 任务队列
            result_list: 结果列表（成功的任务）
            failure_queue: 失败队列（失败的任务）
            stop_event: 停止事件（用于优雅停止）
        """
        super().__init__(name=f"Worker-{worker_id}")
        
        self.worker_id = worker_id
        self.queue = task_queue
        self.result_list = result_list
        self.failure_queue = failure_queue
        self.stop_event = stop_event or threading.Event()
        
        # 执行器（可扩展）
        self.executor = get_executor()
        
        # 统计信息
        self.tasks_processed = 0
        self.tasks_succeeded = 0
        self.tasks_failed = 0
        
        # 设置为守护线程
        self.daemon = True
    
    def run(self):
        """
        线程主循环
        
        流程：
        1. 从队列获取任务
        2. 更新任务状态为 running
        3. 调用 Executor 执行任务
        4. 处理执行结果
        5. 处理失败任务（重试或放入失败队列）
        """
        print(f"    🚀 {self.name} 启动")
        
        while not self.stop_event.is_set():
            try:
                # 从队列获取任务（超时1秒，避免阻塞）
                task = self.queue.get_task(block=True, timeout=1.0)
                
                if task is None:
                    # 队列为空，继续等待
                    continue
                
                # 执行任务
                self._execute_task(task)
                
            except Empty:
                # 队列为空，继续等待
                continue
            except Exception as e:
                print(f"    ⚠️  {self.name} 异常: {e}")
        
        print(f"    🛑 {self.name} 停止")
    
    def _execute_task(self, task: Task):
        """
        执行任务
        
        Args:
            task: Task 实例
        """
        try:
            print(f"    🔧 {self.name} 执行任务: {task.id}")
            
            # 更新任务状态为 running
            task.status = TaskStatus.RUNNING.value
            
            # 调用 Executor 执行任务（可扩展）
            result = self.executor.execute_task(task)
            
            # 处理执行结果
            if task.status == TaskStatus.SUCCESS.value:
                # 成功：添加到结果列表
                task.result = result
                self.result_list.append(task)
                self.tasks_succeeded += 1
                print(f"    ✅ {self.name} 任务成功: {task.id}")
            else:
                # 失败：处理失败任务
                self._handle_failure(task)
            
            self.tasks_processed += 1
            
        except Exception as e:
            # 异常：标记任务失败
            task.status = TaskStatus.FAILED.value
            task.error = str(e)
            self._handle_failure(task)
            self.tasks_processed += 1
    
    def _handle_failure(self, task: Task):
        """
        处理失败任务
        
        流程：
        1. 检查是否可以重试
        2. 可以重试：重新放入队列
        3. 不能重试：放入失败队列
        
        Args:
            task: 失败的任务
        """
        if task.can_retry():
            # 可以重试：重新放入队列
            task.retry()
            self.queue.add_task(task)
            print(f"    🔄 {self.name} 任务重试: {task.id} (第{task.retry_count}次)")
        else:
            # 不能重试：放入失败队列
            self.failure_queue.add_task(task)
            self.tasks_failed += 1
            print(f"    ❌ {self.name} 任务失败: {task.id} - {task.error}")
    
    def stop(self):
        """停止 Worker"""
        self.stop_event.set()
    
    def get_statistics(self) -> dict:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        return {
            "worker_id": self.worker_id,
            "name": self.name,
            "is_alive": self.is_alive(),
            "tasks_processed": self.tasks_processed,
            "tasks_succeeded": self.tasks_succeeded,
            "tasks_failed": self.tasks_failed
        }
    
    def __repr__(self) -> str:
        """字符串表示"""
        return f"Worker(id={self.worker_id}, processed={self.tasks_processed})"


class WorkerPool:
    """
    Worker 线程池
    
    管理多个 Worker 线程，支持并发执行
    """
    
    def __init__(
        self,
        num_workers: int,
        task_queue: TaskQueue,
        result_list: List[Task],
        failure_queue: TaskQueue
    ):
        """
        初始化 Worker 线程池
        
        Args:
            num_workers: Worker 数量
            task_queue: 任务队列
            result_list: 结果列表
            failure_queue: 失败队列
        """
        self.num_workers = num_workers
        self.task_queue = task_queue
        self.result_list = result_list
        self.failure_queue = failure_queue
        
        # Worker 列表
        self.workers: List[Worker] = []
        
        # 停止事件
        self.stop_event = threading.Event()
    
    def start(self):
        """启动所有 Worker"""
        print(f"\n🚀 启动 Worker 线程池: {self.num_workers} 个 Worker")
        
        for i in range(self.num_workers):
            worker = Worker(
                worker_id=f"worker_{i+1}",
                task_queue=self.task_queue,
                result_list=self.result_list,
                failure_queue=self.failure_queue,
                stop_event=self.stop_event
            )
            worker.start()
            self.workers.append(worker)
        
        print(f"✅ Worker 线程池启动完成\n")
    
    def stop(self):
        """停止所有 Worker"""
        print(f"\n🛑 停止 Worker 线程池")
        
        # 设置停止事件
        self.stop_event.set()
        
        # 等待所有 Worker 停止
        for worker in self.workers:
            worker.join(timeout=2.0)
        
        print(f"✅ Worker 线程池停止完成\n")
    
    def wait_completion(self, timeout: Optional[float] = None):
        """
        等待所有任务完成
        
        Args:
            timeout: 超时时间（秒）
        """
        start_time = time.time()
        
        while not self.task_queue.is_empty():
            # 检查超时
            if timeout and (time.time() - start_time) > timeout:
                print(f"⚠️  等待超时: {timeout}s")
                break
            
            # 等待一段时间
            time.sleep(0.1)
        
        # 等待所有 Worker 处理完当前任务
        time.sleep(0.5)
    
    def get_statistics(self) -> dict:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        worker_stats = [w.get_statistics() for w in self.workers]
        
        total_processed = sum(w.tasks_processed for w in self.workers)
        total_succeeded = sum(w.tasks_succeeded for w in self.workers)
        total_failed = sum(w.tasks_failed for w in self.workers)
        
        return {
            "num_workers": self.num_workers,
            "total_processed": total_processed,
            "total_succeeded": total_succeeded,
            "total_failed": total_failed,
            "workers": worker_stats
        }
    
    def __repr__(self) -> str:
        """字符串表示"""
        return f"WorkerPool(workers={self.num_workers})"


# 便捷函数
def create_worker_pool(
    num_workers: int,
    task_queue: TaskQueue,
    result_list: List[Task],
    failure_queue: TaskQueue
) -> WorkerPool:
    """
    创建 Worker 线程池
    
    Args:
        num_workers: Worker 数量
        task_queue: 任务队列
        result_list: 结果列表
        failure_queue: 失败队列
        
    Returns:
        WorkerPool 实例
    """
    return WorkerPool(num_workers, task_queue, result_list, failure_queue)
