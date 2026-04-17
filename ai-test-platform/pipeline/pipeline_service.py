"""
Pipeline Service - 测试流程总调度服务 V3
统一流程编排：Agent → Strategy → Case Generator → Orchestrator → Self-Healing → Report

核心设计 V3：
1. 使用 TestContext 统一数据模型
2. 所有模块只接收 context
3. 不再传多个 JSON
4. Pipeline 只传 context
"""
import json
import time
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

from common.context import TestContext
from agent.test_agent_service import get_test_agent_service
from strategy.strategy_service import get_strategy_service
from case_generator.case_service import get_case_service
from orchestrator.orchestrator_service import get_orchestrator_service
from self_healing.healing_service import get_healing_service
from .report_generator import generate_report


class PipelineService:
    """测试流程总调度服务 V3 - 使用 TestContext"""
    
    def __init__(self):
        self.pipeline_history = []
        self.log_dir = Path("output/pipeline_logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置：是否启用 Case Generator
        self.use_case_generator = True  # 可通过环境变量或配置文件控制
    
    def run_pipeline(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行完整测试流程 V3
        
        流程：Agent → Strategy → Case Generator（可选）→ Orchestrator → Self-Healing → Report
        
        核心设计 V3：
        1. 使用 TestContext 统一数据模型
        2. 所有模块只接收 context
        3. 不再传多个 JSON
        
        Args:
            input_data: {
                "requirement": str,
                "git_diff": str,
                "priority": str (optional),
                "use_case_generator": bool (optional)
            }
            
        Returns:
            完整流程结果（context.to_dict()）
        """
        start_time = time.time()
        
        # ==================== 初始化 TestContext ====================
        context = TestContext(
            requirement=input_data.get('requirement', ''),
            git_diff=input_data.get('git_diff', ''),
            priority=input_data.get('priority', 'P1'),
            use_case_generator=input_data.get('use_case_generator', self.use_case_generator)
        )
        
        print(f"\n{'='*70}")
        print(f"🚀 AI Test Pipeline V3 启动 [Trace: {context.trace_id}]")
        print(f"{'='*70}")
        
        try:
            # ==================== 阶段1: Test Agent ====================
            context = self._stage_agent(context)
            
            # 提前退出检查
            if context.is_skip():
                print(f"\n⏭️  跳过执行: {context.decision.get('reason', '无需测试')}")
                context = self._stage_report(context)
                total_duration = round(time.time() - start_time, 2)
                print(f"\n✅ Pipeline 完成 [耗时: {total_duration}s]")
                self._log_pipeline(context)
                return context.to_dict()
            
            # ==================== 阶段2: Strategy Engine ====================
            context = self._stage_strategy(context)
            
            # ==================== 阶段3: Case Generator（可选）====================
            if context.use_case_generator:
                context = self._stage_case_generator(context)
            else:
                print(f"\n⏭️  跳过 Case Generator（配置禁用）")
                context.cases = None
            
            # ==================== 阶段4: Orchestrator ====================
            context = self._stage_orchestrator(context)
            
            # ==================== 阶段5: Self-Healing ====================
            if context.should_heal():
                context = self._stage_healing(context)
            else:
                print(f"\n⏭️  跳过修复: 所有测试通过")
                context.healing = None
            
            # ==================== 阶段6: Report ====================
            context = self._stage_report(context)
            
            # ==================== 完成 ====================
            total_duration = round(time.time() - start_time, 2)
            
            # 记录日志
            self._log_pipeline(context)
            
            print(f"\n{'='*70}")
            print(f"✅ Pipeline V3 完成 [Trace: {context.trace_id}] [耗时: {total_duration}s]")
            print(f"{'='*70}")
            
            return context.to_dict()
            
        except Exception as e:
            print(f"\n❌ Pipeline 异常: {e}")
            import traceback
            traceback.print_exc()
            
            # 生成错误报告
            context.report = {
                "summary": {
                    "status": "error",
                    "total": 0,
                    "passed": 0,
                    "failed": 0
                },
                "details": [],
                "ai_analysis": f"Pipeline 执行异常: {str(e)}"
            }
            
            total_duration = round(time.time() - start_time, 2)
            context.add_timeline_event("error", "failed", total_duration, str(e))
            
            return context.to_dict()
    
    
    def _stage_agent(self, context: TestContext) -> TestContext:
        """
        阶段1: Test Agent - AI 决策分析
        
        只操作 context，不直接调用其他模块
        """
        step_start = time.time()
        print(f"\n【阶段1】Test Agent - AI 决策分析")
        print("-" * 70)
        
        try:
            agent_service = get_test_agent_service()
            
            # 从 context 获取输入
            requirement = context.requirement
            git_diff = context.git_diff
            
            # 执行分析
            decision = agent_service.analyze(requirement, git_diff)
            
            # 写入 context
            context.decision = decision
            context.add_timeline_event(
                "agent",
                "completed",
                round(time.time() - step_start, 2)
            )
            
            print(f"✅ 决策完成: {decision['action']}")
            print(f"   需要测试: {decision['need_test']}")
            print(f"   风险等级: {decision['risk_level']}")
            print(f"   解析模块: {len(decision.get('parsed_modules', []))} 个")
            
        except Exception as e:
            print(f"❌ Agent 阶段失败: {e}")
            context.decision = self._get_default_decision()
            context.add_timeline_event(
                "agent",
                "failed",
                round(time.time() - step_start, 2),
                str(e)
            )
        
        return context
    
    def _stage_strategy(self, context: TestContext) -> TestContext:
        """
        阶段2: Strategy Engine - 生成测试策略
        
        只操作 context，不直接调用其他模块
        """
        step_start = time.time()
        print(f"\n【阶段2】Strategy Engine - 生成测试策略")
        print("-" * 70)
        
        try:
            strategy_service = get_strategy_service()
            
            # 从 context 获取输入
            decision = context.decision
            
            # 生成策略
            strategy = strategy_service.generate_strategy(decision)
            
            # 写入 context
            context.strategy = strategy
            context.add_timeline_event(
                "strategy",
                "completed",
                round(time.time() - step_start, 2)
            )
            
            print(f"✅ 策略生成: {len(strategy.get('strategy', []))} 个模块")
            print(f"   总用例数: {strategy.get('total_cases', 0)}")
            
        except Exception as e:
            print(f"❌ Strategy 阶段失败: {e}")
            context.strategy = {"strategy": [], "total_modules": 0, "total_cases": 0}
            context.add_timeline_event(
                "strategy",
                "failed",
                round(time.time() - step_start, 2),
                str(e)
            )
        
        return context
    
    def _stage_case_generator(self, context: TestContext) -> TestContext:
        """
        阶段3: Case Generator - 生成测试用例（可选）
        
        只操作 context，不直接调用其他模块
        """
        step_start = time.time()
        print(f"\n【阶段3】Case Generator - 生成测试用例")
        print("-" * 70)
        
        try:
            case_service = get_case_service()
            
            # 从 context 获取输入
            strategy = context.strategy
            
            # 生成用例
            cases = case_service.generate_cases(strategy)
            
            # 写入 context
            context.cases = cases
            context.add_timeline_event(
                "case_generator",
                "completed",
                round(time.time() - step_start, 2)
            )
            
            print(f"✅ 用例生成: {len(cases.get('cases', []))} 个模块")
            print(f"   总用例数: {cases.get('total_cases', 0)}")
            
        except Exception as e:
            print(f"❌ Case Generator 阶段失败: {e}")
            context.cases = None
            context.add_timeline_event(
                "case_generator",
                "failed",
                round(time.time() - step_start, 2),
                str(e)
            )
        
        return context
    
    def _stage_orchestrator(self, context: TestContext) -> TestContext:
        """
        阶段4: Orchestrator - 执行测试（V3 适配）
        
        只操作 context，不直接调用其他模块
        
        V3 改动：
        - 传递完整的 context 字典给 Orchestrator
        - Orchestrator 从 context 中提取 cases
        """
        step_start = time.time()
        print(f"\n【阶段4】Orchestrator - 执行测试（V3调度模式）")
        print("-" * 70)
        
        try:
            orchestrator_service = get_orchestrator_service()
            
            # 构建 Orchestrator 输入（V3 格式）
            orchestrator_input = {
                "cases": self._extract_cases_for_orchestrator(context),
                "num_workers": 5  # 可配置
            }
            
            # 执行测试（V3 接口）
            execution = orchestrator_service.run(orchestrator_input)
            
            # 写入 context
            context.execution = execution
            context.add_timeline_event(
                "orchestrator",
                "completed",
                round(time.time() - step_start, 2)
            )
            
            exec_summary = execution.get('summary', {})
            exec_mode = execution.get('mode', 'unknown')
            print(f"✅ 执行完成: {exec_summary.get('passed', 0)}/{exec_summary.get('total', 0)} 通过")
            print(f"   执行模式: {exec_mode}")
            
        except Exception as e:
            print(f"❌ Orchestrator 阶段失败: {e}")
            import traceback
            traceback.print_exc()
            context.execution = {
                "results": [],
                "failures": [],
                "summary": {"total": 0, "passed": 0, "failed": 0, "duration": 0.0, "pass_rate": 0.0},
                "mode": "v3_scheduler"
            }
            context.add_timeline_event(
                "orchestrator",
                "failed",
                round(time.time() - step_start, 2),
                str(e)
            )
        
        return context
    
    def _stage_healing(self, context: TestContext) -> TestContext:
        """
        阶段5: Self-Healing - 自动修复（V3 适配）
        
        只操作 context，不直接调用其他模块
        
        V3 改动：
        - 使用 Healing Worker 独立处理
        - 传递 failure_queue 而不是失败列表
        """
        step_start = time.time()
        
        execution = context.execution
        failed_count = execution.get('summary', {}).get('failed', 0)
        
        print(f"\n【阶段5】Self-Healing - 自动修复（独立Worker模式）({failed_count} 个失败)")
        print("-" * 70)
        
        try:
            from self_healing.healing_worker import create_healing_worker
            from orchestrator.task_queue import TaskQueue
            from orchestrator.task import Task
            
            # 构建失败任务队列
            failure_queue = TaskQueue()
            
            # 从 execution 提取失败任务
            failed_task_dicts = execution.get('failures', [])
            
            for task_dict in failed_task_dicts:
                # 重建 Task 对象
                task = Task(
                    task_id=task_dict.get('id'),
                    case=task_dict.get('case', {}),
                    task_type=task_dict.get('task_type', 'api'),
                    priority=task_dict.get('priority', 5),
                    status=task_dict.get('status', 'failed'),
                    result=task_dict.get('result'),
                    error=task_dict.get('error'),
                    retry_count=task_dict.get('retry_count', 0)
                )
                failure_queue.add_task(task)
            
            # 创建 Healing Worker
            healing_worker = create_healing_worker(max_retries=3)
            
            # 执行修复
            healing_result = healing_worker.run(failure_queue)
            
            # 写入 context
            context.healing = healing_result
            context.add_timeline_event(
                "healing",
                "completed",
                round(time.time() - step_start, 2)
            )
            
            summary = healing_result.get('summary', {})
            print(f"✅ 修复完成: {summary.get('healed', 0)}/{summary.get('total', 0)} 成功")
            
        except Exception as e:
            print(f"❌ Healing 阶段失败: {e}")
            import traceback
            traceback.print_exc()
            context.healing = {
                "healed": [],
                "failed": [],
                "summary": {
                    "total": 0,
                    "healed": 0,
                    "failed": 0,
                    "heal_rate": 0.0
                }
            }
            context.add_timeline_event(
                "healing",
                "failed",
                round(time.time() - step_start, 2),
                str(e)
            )
        
        return context
    
    def _stage_report(self, context: TestContext) -> TestContext:
        """
        阶段6: Report - 生成测试报告
        
        只操作 context，不直接调用其他模块
        """
        step_start = time.time()
        print(f"\n【阶段6】Report - 生成测试报告")
        print("-" * 70)
        
        try:
            # 从 context 生成报告（传递字典格式）
            context_dict = context.to_dict()
            report = generate_report(context_dict)
            
            # 写入 context
            context.report = report
            context.add_timeline_event(
                "report",
                "completed",
                round(time.time() - step_start, 2)
            )
            
            print(f"✅ 报告生成: {report['summary']['status']}")
            
        except Exception as e:
            print(f"❌ Report 阶段失败: {e}")
            context.report = {
                "summary": {"status": "error", "total": 0, "passed": 0, "failed": 0},
                "details": [],
                "ai_analysis": f"报告生成失败: {str(e)}"
            }
            context.add_timeline_event(
                "report",
                "failed",
                round(time.time() - step_start, 2),
                str(e)
            )
        
        return context
    
    
    def _get_default_decision(self) -> Dict[str, Any]:
        """获取默认决策（用于异常情况）"""
        return {
            "need_test": False,
            "action": "skip",
            "confidence": 0.0,
            "risk_level": "低",
            "test_types": [],
            "reason": "Agent 分析失败，默认跳过"
        }
    
    def _extract_cases_for_orchestrator(self, context: TestContext) -> List[Dict[str, Any]]:
        """
        从 context 提取用例供 Orchestrator 使用
        
        优先级：
        1. 如果有 cases（Case Generator 生成），使用 cases
        2. 否则使用 strategy（直接执行策略）
        
        Args:
            context: 测试上下文
            
        Returns:
            用例列表（模块格式）
        """
        # 优先使用 Case Generator 生成的用例
        if context.cases:
            cases_data = context.cases
            return cases_data.get('cases', [])
        
        # 否则使用 Strategy（转换为用例格式）
        if context.strategy:
            strategy_data = context.strategy
            strategy_modules = strategy_data.get('strategy', [])
            
            # 转换 strategy 为 cases 格式
            cases = []
            for module in strategy_modules:
                module_cases = {
                    "module": module.get('module', '未知模块'),
                    "cases": []
                }
                
                # 将 test_points 转换为 cases
                for point in module.get('test_points', []):
                    case = {
                        "name": point.get('name', ''),
                        "type": point.get('type', '功能测试'),
                        "priority": point.get('priority', 'P2'),
                        "description": point.get('description', ''),
                        "steps": point.get('steps', [])
                    }
                    module_cases['cases'].append(case)
                
                cases.append(module_cases)
            
            return cases
        
        # 都没有，返回空
        return []
    
    
    def _log_pipeline(self, context: TestContext):
        """记录 Pipeline 日志"""
        try:
            context_dict = context.to_dict()
            
            log_entry = {
                "trace_id": context.trace_id,
                "timestamp": context.created_at,
                "input": {
                    "requirement": context.requirement,
                    "git_diff": context.git_diff,
                    "priority": context.priority
                },
                "result": {
                    "decision": context.decision,
                    "strategy": context.strategy,
                    "cases": context.cases,
                    "execution": context.execution,
                    "healing": context.healing,
                    "report": context.report,
                    "timeline": context.timeline,
                    "total_duration": context.get_total_duration()
                }
            }
            
            self.pipeline_history.append(log_entry)
            
            # 保存到文件
            log_file = self.log_dir / f"pipeline_{datetime.now().strftime('%Y%m%d')}.jsonl"
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
                
        except Exception as e:
            print(f"⚠️  记录 Pipeline 日志失败: {e}")
    
    def get_pipeline_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取 Pipeline 历史"""
        return self.pipeline_history[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.pipeline_history:
            return {
                "total_pipelines": 0,
                "skipped": 0,
                "executed": 0,
                "avg_duration": 0.0,
                "success_rate": 0.0
            }
        
        total = len(self.pipeline_history)
        skipped = sum(
            1 for p in self.pipeline_history 
            if p['result'].get('decision', {}).get('action') in ['skip', 'skip_test']
        )
        executed = total - skipped
        
        durations = [p['result'].get('total_duration', 0) for p in self.pipeline_history]
        avg_duration = sum(durations) / len(durations) if durations else 0.0
        
        # 计算成功率（passed 或 partial 算成功）
        successful = sum(
            1 for p in self.pipeline_history
            if p['result'].get('report', {}).get('summary', {}).get('status') in ['passed', 'partial', 'skipped']
        )
        success_rate = round(successful / total * 100, 2) if total > 0 else 0.0
        
        return {
            "total_pipelines": total,
            "skipped": skipped,
            "executed": executed,
            "avg_duration": round(avg_duration, 2),
            "success_rate": success_rate
        }


# 全局服务实例
_pipeline_service = None

def get_pipeline_service() -> PipelineService:
    """获取 Pipeline 服务实例"""
    global _pipeline_service
    if _pipeline_service is None:
        _pipeline_service = PipelineService()
    return _pipeline_service
