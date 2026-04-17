"""
Healing Worker - 独立的失败任务修复器

最终目标：
- Execution 与 Healing 解耦
- 不在 Orchestrator 内调用
- 必须独立处理失败任务
- 支持重试次数限制
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from typing import List, Dict, Any
from orchestrator.task import Task
from orchestrator.task_queue import TaskQueue


class HealingWorker:
    """
    独立的失败任务修复器
    
    核心设计：
    1. 不在 Orchestrator 内调用
    2. 必须独立处理失败任务
    3. 支持重试次数限制
    
    职责：
    - 分析失败任务
    - 尝试修复
    - 重试任务
    """
    
    def __init__(self, max_retries: int = 3):
        """
        初始化 Healing Worker
        
        Args:
            max_retries: 最大重试次数（默认3次）
        """
        self.max_retries = max_retries
        self.healed_tasks = []
        self.failed_tasks = []
    
    def run(self, failure_queue: TaskQueue) -> Dict[str, Any]:
        """
        处理失败任务
        
        流程：
        1. 从失败队列获取任务
        2. 分析失败原因
        3. 尝试修复
        4. 重试任务
        
        Args:
            failure_queue: 失败任务队列
            
        Returns:
            {
                "healed": [修复成功的任务],
                "failed": [修复失败的任务],
                "summary": {...}
            }
        """
        print(f"\n🔧 Healing Worker 启动")
        
        # 获取所有失败任务
        failed_tasks = failure_queue.get_all_tasks()
        
        if not failed_tasks:
            print("   ✅ 没有失败任务需要修复")
            return self._empty_result()
        
        print(f"   📦 发现 {len(failed_tasks)} 个失败任务")
        
        # 处理每个失败任务
        for task in failed_tasks:
            self._process_failed_task(task)
        
        # 构建结果
        result = {
            "healed": [t.to_dict() for t in self.healed_tasks],
            "failed": [t.to_dict() for t in self.failed_tasks],
            "summary": {
                "total": len(failed_tasks),
                "healed": len(self.healed_tasks),
                "failed": len(self.failed_tasks),
                "heal_rate": round(len(self.healed_tasks) / len(failed_tasks) * 100, 2) if failed_tasks else 0.0
            }
        }
        
        print(f"\n✅ Healing Worker 完成: {len(self.healed_tasks)}/{len(failed_tasks)} 修复成功")
        
        return result
    
    def _process_failed_task(self, task: Task):
        """
        处理单个失败任务
        
        流程：
        1. 检查重试次数
        2. 分析失败原因
        3. 尝试修复
        4. 重试任务
        
        Args:
            task: 失败的任务
        """
        print(f"\n   🔍 分析任务: {task.id}")
        print(f"      失败原因: {task.error}")
        print(f"      重试次数: {task.retry_count}/{self.max_retries}")
        
        # 检查是否可以重试
        if task.retry_count >= self.max_retries:
            print(f"      ❌ 达到最大重试次数，放弃修复")
            self.failed_tasks.append(task)
            return
        
        # 分析失败原因
        fix_strategy = self._analyze_and_fix(task)
        
        if fix_strategy:
            print(f"      ✅ 找到修复策略: {fix_strategy}")
            
            # 尝试重试
            success = self._retry_task(task)
            
            if success:
                print(f"      ✅ 修复成功")
                self.healed_tasks.append(task)
            else:
                print(f"      ⚠️  修复失败，需要进一步处理")
                self.failed_tasks.append(task)
        else:
            print(f"      ❌ 无法找到修复策略")
            self.failed_tasks.append(task)
    
    def _analyze_and_fix(self, task: Task) -> str:
        """
        分析失败原因并尝试修复
        
        Args:
            task: 失败的任务
            
        Returns:
            修复策略描述，如果无法修复返回 None
        """
        error = task.error or ""
        
        # 常见失败原因分析
        if "timeout" in error.lower():
            return "增加超时时间"
        
        elif "connection" in error.lower():
            return "重新建立连接"
        
        elif "not found" in error.lower():
            return "检查资源是否存在"
        
        elif "permission" in error.lower():
            return "检查权限配置"
        
        elif "断言失败" in error or "assertion" in error.lower():
            return "更新断言条件"
        
        else:
            # 未知错误，尝试通用修复
            return "通用重试策略"
    
    def _retry_task(self, task: Task) -> bool:
        """
        重试任务
        
        Args:
            task: 要重试的任务
            
        Returns:
            是否重试成功
        """
        # Mock: 模拟重试
        # 实际应该: 重新执行任务
        
        # 增加重试次数
        task.retry_count += 1
        
        # Mock: 50% 成功率
        import random
        success = random.random() > 0.5
        
        if success:
            # 重试成功
            task.status = "success"
            task.error = None
            task.result = {"status": "passed", "healed": True}
        else:
            # 重试失败
            task.status = "failed"
        
        return success
    
    def _empty_result(self) -> Dict[str, Any]:
        """返回空结果"""
        return {
            "healed": [],
            "failed": [],
            "summary": {
                "total": 0,
                "healed": 0,
                "failed": 0,
                "heal_rate": 0.0
            }
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        total = len(self.healed_tasks) + len(self.failed_tasks)
        
        return {
            "total_processed": total,
            "healed": len(self.healed_tasks),
            "failed": len(self.failed_tasks),
            "heal_rate": round(len(self.healed_tasks) / total * 100, 2) if total > 0 else 0.0
        }


# 便捷函数
def create_healing_worker(max_retries: int = 3) -> HealingWorker:
    """
    创建 Healing Worker
    
    Args:
        max_retries: 最大重试次数
        
    Returns:
        HealingWorker 实例
    """
    return HealingWorker(max_retries=max_retries)
