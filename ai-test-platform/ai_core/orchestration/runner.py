"""
OrchestrationRunner - 编排调度器
协调Agent、Workflow、Skill的执行
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# 导入ai_core内部模块
from ..agents.test_agent import TestAgent
from ..workflow.test_workflow import TestWorkflow, WorkflowStage
from ..skills.pytest_skill import PytestSkill


class OrchestrationRunner:
    """
    编排调度器
    
    职责：
    1. 协调多个Agent协作
    2. 管理Workflow执行
    3. 调度Skill执行
    4. 并行任务管理
    5. 资源分配和监控
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化编排调度器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 初始化组件
        self.agents = {}
        self.workflows = {}
        self.skills = {}
        
        # 线程池
        self.executor = ThreadPoolExecutor(
            max_workers=self.config.get("max_workers", 4)
        )
        
        # 任务队列和状态
        self.task_queue = []
        self.running_tasks = {}
        self.completed_tasks = []
        
        self.logger.info("OrchestrationRunner initialized")
    
    def register_agent(self, name: str, agent: TestAgent):
        """注册Agent"""
        self.agents[name] = agent
        self.logger.info(f"Registered agent: {name}")
    
    def register_workflow(self, name: str, workflow: TestWorkflow):
        """注册Workflow"""
        self.workflows[name] = workflow
        self.logger.info(f"Registered workflow: {name}")
    
    def register_skill(self, name: str, skill: PytestSkill):
        """注册Skill"""
        self.skills[name] = skill
        self.logger.info(f"Registered skill: {name}")
    
    def run_agent_task(self, agent_name: str, task: Dict) -> Dict:
        """
        运行Agent任务
        
        Args:
            agent_name: Agent名称
            task: 任务定义
            
        Returns:
            执行结果
        """
        if agent_name not in self.agents:
            raise ValueError(f"Agent not found: {agent_name}")
        
        agent = self.agents[agent_name]
        return agent.execute_task(task)
    
    def run_workflow(self, workflow_name: str, input_data: Dict) -> Dict:
        """
        运行Workflow
        
        Args:
            workflow_name: Workflow名称
            input_data: 输入数据
            
        Returns:
            执行结果
        """
        if workflow_name not in self.workflows:
            raise ValueError(f"Workflow not found: {workflow_name}")
        
        workflow = self.workflows[workflow_name]
        return workflow.run(input_data)
    
    def run_skill(self, skill_name: str, **kwargs) -> Dict:
        """
        运行Skill
        
        Args:
            skill_name: Skill名称
            **kwargs: Skill参数
            
        Returns:
            执行结果
        """
        if skill_name not in self.skills:
            raise ValueError(f"Skill not found: {skill_name}")
        
        skill = self.skills[skill_name]
        return skill.execute(**kwargs)
    
    def run_parallel_tasks(self, tasks: List[Dict]) -> List[Dict]:
        """
        并行运行多个任务
        
        Args:
            tasks: 任务列表，每个任务包含type和params
            
        Returns:
            所有任务的执行结果
        """
        self.logger.info(f"Running {len(tasks)} tasks in parallel")
        
        futures = []
        for task in tasks:
            future = self.executor.submit(self._execute_task, task)
            futures.append(future)
        
        results = []
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                self.logger.error(f"Task failed: {e}")
                results.append({"status": "failed", "error": str(e)})
        
        return results
    
    def create_pipeline(self, pipeline_config: Dict) -> Dict:
        """
        创建测试流水线
        
        Args:
            pipeline_config: 流水线配置
            
        Returns:
            流水线执行结果
        """
        self.logger.info("Creating test pipeline")
        
        pipeline_result = {
            "pipeline_id": self._generate_pipeline_id(),
            "start_time": datetime.now().isoformat(),
            "stages": []
        }
        
        try:
            stages = pipeline_config.get("stages", [])
            
            for stage in stages:
                stage_result = self._execute_pipeline_stage(stage)
                pipeline_result["stages"].append(stage_result)
            
            pipeline_result["status"] = "completed"
            pipeline_result["end_time"] = datetime.now().isoformat()
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            pipeline_result["status"] = "failed"
            pipeline_result["error"] = str(e)
            pipeline_result["end_time"] = datetime.now().isoformat()
        
        return pipeline_result
    
    def get_status(self) -> Dict:
        """获取调度器状态"""
        return {
            "agents": list(self.agents.keys()),
            "workflows": list(self.workflows.keys()),
            "skills": list(self.skills.keys()),
            "running_tasks": len(self.running_tasks),
            "completed_tasks": len(self.completed_tasks),
            "queued_tasks": len(self.task_queue)
        }
    
    def _execute_task(self, task: Dict) -> Dict:
        """执行单个任务"""
        task_type = task.get("type")
        params = task.get("params", {})
        
        if task_type == "agent":
            return self.run_agent_task(params["agent_name"], params["task"])
        elif task_type == "workflow":
            return self.run_workflow(params["workflow_name"], params["input_data"])
        elif task_type == "skill":
            return self.run_skill(params["skill_name"], **params.get("kwargs", {}))
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    def _execute_pipeline_stage(self, stage: Dict) -> Dict:
        """执行流水线阶段"""
        stage_name = stage.get("name")
        stage_type = stage.get("type")
        
        self.logger.info(f"Executing pipeline stage: {stage_name}")
        
        if stage_type == "parallel":
            tasks = stage.get("tasks", [])
            results = self.run_parallel_tasks(tasks)
            return {"stage": stage_name, "results": results}
        else:
            task = stage.get("task", {})
            result = self._execute_task(task)
            return {"stage": stage_name, "result": result}
    
    def _generate_pipeline_id(self) -> str:
        """生成流水线ID"""
        return f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def shutdown(self):
        """关闭调度器"""
        self.logger.info("Shutting down orchestration runner")
        self.executor.shutdown(wait=True)
