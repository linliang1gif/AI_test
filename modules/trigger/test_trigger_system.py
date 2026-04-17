"""
CI/CD自动测试触发系统
支持Git push、API手动触发、定时任务触发
"""
import uuid
import logging
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from croniter import croniter
import json


class TriggerType(Enum):
    """触发类型"""
    GIT_PUSH = "git_push"
    MANUAL = "manual"
    SCHEDULED = "scheduled"


class TriggerStatus(Enum):
    """触发状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TriggerRecord:
    """触发记录"""
    trigger_id: str
    trigger_type: str
    status: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    # 触发源信息
    source: Optional[Dict[str, Any]] = None
    
    # Pipeline信息
    trace_id: Optional[str] = None
    pipeline_result: Optional[Dict[str, Any]] = None
    
    # 错误信息
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


class TestTriggerSystem:
    """
    测试触发系统
    支持Git push、API手动触发、定时任务触发
    """
    
    def __init__(self, pipeline_service=None):
        """
        初始化触发系统
        
        Args:
            pipeline_service: Pipeline服务实例
        """
        self.pipeline_service = pipeline_service
        self.logger = logging.getLogger(__name__)
        
        # 触发记录
        self.triggers: Dict[str, TriggerRecord] = {}
        self.lock = threading.Lock()
        
        # 定时任务
        self.scheduled_jobs: Dict[str, Dict[str, Any]] = {}
        self.scheduler_thread: Optional[threading.Thread] = None
        self.scheduler_running = False
        
        self.logger.info("TestTriggerSystem 初始化完成")
    
    # ==================== Git Push 触发 ====================
    
    def on_git_push(
        self,
        repo: str,
        branch: str,
        commit_id: str,
        commit_message: Optional[str] = None,
        changed_files: Optional[List[str]] = None,
        author: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Git变更触发测试
        
        Args:
            repo: 仓库名称
            branch: 分支名称
            commit_id: 提交ID
            commit_message: 提交信息
            changed_files: 变更文件列表
            author: 提交作者
            
        Returns:
            触发结果
        """
        trigger_id = f"git_{int(time.time() * 1000)}"
        
        self.logger.info(
            f"Git Push 触发: repo={repo}, branch={branch}, "
            f"commit={commit_id[:8]}"
        )
        
        # 创建触发记录
        record = TriggerRecord(
            trigger_id=trigger_id,
            trigger_type=TriggerType.GIT_PUSH.value,
            status=TriggerStatus.PENDING.value,
            created_at=datetime.now().isoformat(),
            source={
                "repo": repo,
                "branch": branch,
                "commit_id": commit_id,
                "commit_message": commit_message,
                "changed_files": changed_files or [],
                "author": author
            }
        )
        
        with self.lock:
            self.triggers[trigger_id] = record
        
        # 异步执行Pipeline
        thread = threading.Thread(
            target=self._execute_git_trigger,
            args=(trigger_id, record),
            daemon=True
        )
        thread.start()
        
        return {
            "trigger_id": trigger_id,
            "status": TriggerStatus.PENDING.value,
            "message": "Git触发已提交，正在分析变更..."
        }
    
    def _execute_git_trigger(self, trigger_id: str, record: TriggerRecord):
        """执行Git触发的测试"""
        try:
            # 更新状态为运行中
            with self.lock:
                record.status = TriggerStatus.RUNNING.value
                record.started_at = datetime.now().isoformat()
            
            source = record.source
            
            # 1. 分析变更文件，生成测试策略
            test_strategy = self._analyze_git_changes(
                changed_files=source.get("changed_files", []),
                commit_message=source.get("commit_message", "")
            )
            
            self.logger.info(f"Git触发 {trigger_id}: 测试策略 = {test_strategy}")
            
            # 2. 构建测试需求
            requirement = self._build_requirement_from_git(source, test_strategy)
            
            # 3. 调用Pipeline
            if self.pipeline_service:
                pipeline_result = self.pipeline_service.run_pipeline(
                    requirement=requirement,
                    swagger_file=None,  # Git触发通常不需要swagger
                    config={
                        "trigger_type": "git_push",
                        "trigger_id": trigger_id,
                        "test_strategy": test_strategy
                    }
                )
                
                # 更新记录
                with self.lock:
                    record.status = TriggerStatus.SUCCESS.value
                    record.trace_id = pipeline_result.get("trace_id")
                    record.pipeline_result = pipeline_result
                    record.completed_at = datetime.now().isoformat()
                
                self.logger.info(
                    f"✅ Git触发 {trigger_id} 完成: "
                    f"trace_id={record.trace_id}"
                )
            else:
                # 模拟执行
                self.logger.warning(f"Pipeline服务未配置，使用模拟执行: {trigger_id}")
                with self.lock:
                    record.status = TriggerStatus.SUCCESS.value
                    record.trace_id = str(uuid.uuid4())
                    record.pipeline_result = {"simulated": True}
                    record.completed_at = datetime.now().isoformat()
        
        except Exception as e:
            self.logger.error(f"Git触发 {trigger_id} 失败: {e}")
            with self.lock:
                record.status = TriggerStatus.FAILED.value
                record.error = str(e)
                record.completed_at = datetime.now().isoformat()
    
    def _analyze_git_changes(
        self,
        changed_files: List[str],
        commit_message: str
    ) -> Dict[str, Any]:
        """
        分析Git变更，生成测试策略
        
        Args:
            changed_files: 变更文件列表
            commit_message: 提交信息
            
        Returns:
            测试策略
        """
        strategy = {
            "test_scope": "incremental",  # incremental | full
            "priority": "P1",
            "focus_areas": []
        }
        
        # 分析变更文件类型
        api_files = [f for f in changed_files if "api" in f.lower() or "controller" in f.lower()]
        model_files = [f for f in changed_files if "model" in f.lower() or "entity" in f.lower()]
        service_files = [f for f in changed_files if "service" in f.lower()]
        
        # 根据变更确定测试范围
        if api_files:
            strategy["focus_areas"].append("api_testing")
        if model_files:
            strategy["focus_areas"].append("data_validation")
        if service_files:
            strategy["focus_areas"].append("business_logic")
        
        # 根据提交信息调整优先级
        if any(keyword in commit_message.lower() for keyword in ["hotfix", "critical", "urgent"]):
            strategy["priority"] = "P0"
        elif any(keyword in commit_message.lower() for keyword in ["feature", "新功能"]):
            strategy["priority"] = "P1"
        else:
            strategy["priority"] = "P2"
        
        # 判断是否需要全量测试
        if any(keyword in commit_message.lower() for keyword in ["refactor", "重构", "架构"]):
            strategy["test_scope"] = "full"
        
        return strategy
    
    def _build_requirement_from_git(
        self,
        source: Dict[str, Any],
        strategy: Dict[str, Any]
    ) -> str:
        """从Git信息构建测试需求"""
        repo = source.get("repo", "unknown")
        branch = source.get("branch", "unknown")
        commit_msg = source.get("commit_message", "")
        changed_files = source.get("changed_files", [])
        
        requirement = f"""
基于Git提交自动生成的测试需求：

仓库: {repo}
分支: {branch}
提交信息: {commit_msg}

变更文件:
{chr(10).join(f"- {f}" for f in changed_files[:10])}

测试策略:
- 测试范围: {strategy['test_scope']}
- 优先级: {strategy['priority']}
- 关注领域: {', '.join(strategy['focus_areas'])}

请根据以上变更生成相应的测试用例。
"""
        return requirement.strip()
    
    # ==================== 手动触发 ====================
    
    def manual_trigger(
        self,
        requirement: str,
        priority: str = "P1",
        swagger_file: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        user: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        手动触发测试
        
        Args:
            requirement: 测试需求描述
            priority: 优先级 (P0/P1/P2/P3)
            swagger_file: Swagger文件路径（可选）
            config: 额外配置
            user: 触发用户
            
        Returns:
            触发结果
        """
        trigger_id = f"manual_{int(time.time() * 1000)}"
        
        self.logger.info(f"手动触发: priority={priority}, user={user}")
        
        # 创建触发记录
        record = TriggerRecord(
            trigger_id=trigger_id,
            trigger_type=TriggerType.MANUAL.value,
            status=TriggerStatus.PENDING.value,
            created_at=datetime.now().isoformat(),
            source={
                "requirement": requirement,
                "priority": priority,
                "swagger_file": swagger_file,
                "user": user,
                "config": config or {}
            }
        )
        
        with self.lock:
            self.triggers[trigger_id] = record
        
        # 异步执行Pipeline
        thread = threading.Thread(
            target=self._execute_manual_trigger,
            args=(trigger_id, record),
            daemon=True
        )
        thread.start()
        
        return {
            "trigger_id": trigger_id,
            "status": TriggerStatus.PENDING.value,
            "message": "手动触发已提交，正在执行..."
        }
    
    def _execute_manual_trigger(self, trigger_id: str, record: TriggerRecord):
        """执行手动触发的测试"""
        try:
            # 更新状态为运行中
            with self.lock:
                record.status = TriggerStatus.RUNNING.value
                record.started_at = datetime.now().isoformat()
            
            source = record.source
            
            # 调用Pipeline
            if self.pipeline_service:
                pipeline_config = source.get("config", {})
                pipeline_config.update({
                    "trigger_type": "manual",
                    "trigger_id": trigger_id,
                    "priority": source.get("priority", "P1")
                })
                
                pipeline_result = self.pipeline_service.run_pipeline(
                    requirement=source.get("requirement"),
                    swagger_file=source.get("swagger_file"),
                    config=pipeline_config
                )
                
                # 更新记录
                with self.lock:
                    record.status = TriggerStatus.SUCCESS.value
                    record.trace_id = pipeline_result.get("trace_id")
                    record.pipeline_result = pipeline_result
                    record.completed_at = datetime.now().isoformat()
                
                self.logger.info(
                    f"✅ 手动触发 {trigger_id} 完成: "
                    f"trace_id={record.trace_id}"
                )
            else:
                # 模拟执行
                self.logger.warning(f"Pipeline服务未配置，使用模拟执行: {trigger_id}")
                with self.lock:
                    record.status = TriggerStatus.SUCCESS.value
                    record.trace_id = str(uuid.uuid4())
                    record.pipeline_result = {"simulated": True}
                    record.completed_at = datetime.now().isoformat()
        
        except Exception as e:
            self.logger.error(f"手动触发 {trigger_id} 失败: {e}")
            with self.lock:
                record.status = TriggerStatus.FAILED.value
                record.error = str(e)
                record.completed_at = datetime.now().isoformat()
    
    # ==================== 定时触发 ====================
    
    def schedule_trigger(
        self,
        cron_expression: str,
        requirement: str,
        job_name: str,
        priority: str = "P2",
        swagger_file: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        enabled: bool = True
    ) -> Dict[str, Any]:
        """
        添加定时触发任务
        
        Args:
            cron_expression: Cron表达式 (如: "0 2 * * *" 每天凌晨2点)
            requirement: 测试需求描述
            job_name: 任务名称
            priority: 优先级
            swagger_file: Swagger文件路径
            config: 额外配置
            enabled: 是否启用
            
        Returns:
            任务信息
        """
        # 验证cron表达式
        try:
            croniter(cron_expression)
        except Exception as e:
            return {
                "success": False,
                "error": f"无效的cron表达式: {e}"
            }
        
        job_id = f"job_{job_name}_{int(time.time())}"
        
        job = {
            "job_id": job_id,
            "job_name": job_name,
            "cron_expression": cron_expression,
            "requirement": requirement,
            "priority": priority,
            "swagger_file": swagger_file,
            "config": config or {},
            "enabled": enabled,
            "created_at": datetime.now().isoformat(),
            "last_run": None,
            "next_run": None,
            "run_count": 0
        }
        
        with self.lock:
            self.scheduled_jobs[job_id] = job
        
        # 启动调度器（如果还未启动）
        if not self.scheduler_running:
            self.start_scheduler()
        
        self.logger.info(
            f"定时任务已添加: {job_name} (cron: {cron_expression})"
        )
        
        return {
            "success": True,
            "job_id": job_id,
            "job": job
        }
    
    def start_scheduler(self):
        """启动定时调度器"""
        if self.scheduler_running:
            self.logger.warning("调度器已在运行")
            return
        
        self.scheduler_running = True
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            daemon=True
        )
        self.scheduler_thread.start()
        
        self.logger.info("🕐 定时调度器已启动")
    
    def stop_scheduler(self):
        """停止定时调度器"""
        self.scheduler_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        self.logger.info("定时调度器已停止")
    
    def _scheduler_loop(self):
        """调度器主循环"""
        while self.scheduler_running:
            try:
                current_time = datetime.now()
                
                with self.lock:
                    jobs = list(self.scheduled_jobs.values())
                
                for job in jobs:
                    if not job.get("enabled", True):
                        continue
                    
                    # 计算下次运行时间
                    cron = croniter(job["cron_expression"], current_time)
                    next_run = cron.get_next(datetime)
                    
                    # 检查是否需要执行
                    last_run = job.get("last_run")
                    if last_run:
                        last_run_dt = datetime.fromisoformat(last_run)
                        if current_time >= next_run and current_time > last_run_dt:
                            self._execute_scheduled_job(job)
                    else:
                        # 首次运行
                        if current_time >= next_run:
                            self._execute_scheduled_job(job)
                
                # 每分钟检查一次
                time.sleep(60)
            
            except Exception as e:
                self.logger.error(f"调度器循环错误: {e}")
                time.sleep(60)
    
    def _execute_scheduled_job(self, job: Dict[str, Any]):
        """执行定时任务"""
        job_id = job["job_id"]
        job_name = job["job_name"]
        
        trigger_id = f"scheduled_{job_name}_{int(time.time() * 1000)}"
        
        self.logger.info(f"执行定时任务: {job_name}")
        
        # 创建触发记录
        record = TriggerRecord(
            trigger_id=trigger_id,
            trigger_type=TriggerType.SCHEDULED.value,
            status=TriggerStatus.PENDING.value,
            created_at=datetime.now().isoformat(),
            source={
                "job_id": job_id,
                "job_name": job_name,
                "cron_expression": job["cron_expression"],
                "requirement": job["requirement"],
                "priority": job["priority"],
                "swagger_file": job.get("swagger_file"),
                "config": job.get("config", {})
            }
        )
        
        with self.lock:
            self.triggers[trigger_id] = record
            job["last_run"] = datetime.now().isoformat()
            job["run_count"] = job.get("run_count", 0) + 1
        
        # 异步执行
        thread = threading.Thread(
            target=self._execute_scheduled_trigger,
            args=(trigger_id, record),
            daemon=True
        )
        thread.start()
    
    def _execute_scheduled_trigger(self, trigger_id: str, record: TriggerRecord):
        """执行定时触发的测试"""
        try:
            # 更新状态为运行中
            with self.lock:
                record.status = TriggerStatus.RUNNING.value
                record.started_at = datetime.now().isoformat()
            
            source = record.source
            
            # 调用Pipeline
            if self.pipeline_service:
                pipeline_config = source.get("config", {})
                pipeline_config.update({
                    "trigger_type": "scheduled",
                    "trigger_id": trigger_id,
                    "job_name": source.get("job_name"),
                    "priority": source.get("priority", "P2")
                })
                
                pipeline_result = self.pipeline_service.run_pipeline(
                    requirement=source.get("requirement"),
                    swagger_file=source.get("swagger_file"),
                    config=pipeline_config
                )
                
                # 更新记录
                with self.lock:
                    record.status = TriggerStatus.SUCCESS.value
                    record.trace_id = pipeline_result.get("trace_id")
                    record.pipeline_result = pipeline_result
                    record.completed_at = datetime.now().isoformat()
                
                self.logger.info(
                    f"✅ 定时触发 {trigger_id} 完成: "
                    f"trace_id={record.trace_id}"
                )
            else:
                # 模拟执行
                self.logger.warning(f"Pipeline服务未配置，使用模拟执行: {trigger_id}")
                with self.lock:
                    record.status = TriggerStatus.SUCCESS.value
                    record.trace_id = str(uuid.uuid4())
                    record.pipeline_result = {"simulated": True}
                    record.completed_at = datetime.now().isoformat()
        
        except Exception as e:
            self.logger.error(f"定时触发 {trigger_id} 失败: {e}")
            with self.lock:
                record.status = TriggerStatus.FAILED.value
                record.error = str(e)
                record.completed_at = datetime.now().isoformat()
    
    # ==================== 查询接口 ====================
    
    def get_trigger_status(self, trigger_id: str) -> Optional[Dict[str, Any]]:
        """
        获取触发状态
        
        Args:
            trigger_id: 触发ID
            
        Returns:
            触发记录
        """
        with self.lock:
            record = self.triggers.get(trigger_id)
            if record:
                return record.to_dict()
        return None
    
    def list_triggers(
        self,
        trigger_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        列出触发记录
        
        Args:
            trigger_type: 触发类型过滤
            status: 状态过滤
            limit: 返回数量限制
            
        Returns:
            触发记录列表
        """
        with self.lock:
            records = list(self.triggers.values())
        
        # 过滤
        if trigger_type:
            records = [r for r in records if r.trigger_type == trigger_type]
        if status:
            records = [r for r in records if r.status == status]
        
        # 排序（最新的在前）
        records.sort(key=lambda r: r.created_at, reverse=True)
        
        # 限制数量
        records = records[:limit]
        
        return [r.to_dict() for r in records]
    
    def list_scheduled_jobs(self) -> List[Dict[str, Any]]:
        """列出所有定时任务"""
        with self.lock:
            return list(self.scheduled_jobs.values())
    
    def update_scheduled_job(
        self,
        job_id: str,
        enabled: Optional[bool] = None,
        cron_expression: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        更新定时任务
        
        Args:
            job_id: 任务ID
            enabled: 是否启用
            cron_expression: 新的cron表达式
            
        Returns:
            更新结果
        """
        with self.lock:
            job = self.scheduled_jobs.get(job_id)
            if not job:
                return {"success": False, "error": "任务不存在"}
            
            if enabled is not None:
                job["enabled"] = enabled
            
            if cron_expression:
                try:
                    croniter(cron_expression)
                    job["cron_expression"] = cron_expression
                except Exception as e:
                    return {"success": False, "error": f"无效的cron表达式: {e}"}
            
            return {"success": True, "job": job}
    
    def delete_scheduled_job(self, job_id: str) -> Dict[str, Any]:
        """删除定时任务"""
        with self.lock:
            if job_id in self.scheduled_jobs:
                del self.scheduled_jobs[job_id]
                return {"success": True}
            return {"success": False, "error": "任务不存在"}
