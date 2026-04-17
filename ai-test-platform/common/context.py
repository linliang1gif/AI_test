"""
TestContext - 统一测试上下文数据模型

最终目标：
- 统一数据流
- 降低耦合
- 所有模块只接收 context
- 不再传多个 JSON
- Pipeline 只传 context
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field, asdict
import uuid


@dataclass
class TestContext:
    """
    统一测试上下文
    
    所有模块只操作这个 context 对象：
    - Agent: 读取 requirement, git_diff, priority → 写入 decision
    - Strategy: 读取 decision → 写入 strategy
    - Case Generator: 读取 strategy → 写入 cases
    - Orchestrator: 读取 strategy/cases → 写入 execution
    - Self-Healing: 读取 execution → 写入 healing
    - Report: 读取所有 → 写入 report
    """
    
    # ============================================================
    # 输入数据（由 Pipeline 初始化）
    # ============================================================
    requirement: str = ""
    git_diff: str = ""
    priority: str = "P1"
    
    # ============================================================
    # 配置参数
    # ============================================================
    use_case_generator: bool = True
    
    # ============================================================
    # 阶段输出数据（由各模块写入）
    # ============================================================
    decision: Optional[Dict[str, Any]] = None
    strategy: Optional[Dict[str, Any]] = None
    cases: Optional[Dict[str, Any]] = None
    execution: Optional[Dict[str, Any]] = None
    healing: Optional[Dict[str, Any]] = None
    report: Optional[Dict[str, Any]] = None
    
    # ============================================================
    # 元数据
    # ============================================================
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    timeline: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestContext':
        """从字典创建"""
        return cls(**data)
    
    def add_timeline_event(self, stage: str, status: str, duration: float = 0.0, details: str = ""):
        """添加时间线事件"""
        self.timeline.append({
            "stage": stage,
            "status": status,
            "duration": duration,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_stage_data(self, stage: str) -> Optional[Dict[str, Any]]:
        """获取指定阶段的数据"""
        stage_map = {
            "agent": self.decision,
            "decision": self.decision,
            "strategy": self.strategy,
            "case_generator": self.cases,
            "cases": self.cases,
            "orchestrator": self.execution,
            "execution": self.execution,
            "healing": self.healing,
            "self_healing": self.healing,
            "report": self.report
        }
        return stage_map.get(stage)
    
    def set_stage_data(self, stage: str, data: Dict[str, Any]):
        """设置指定阶段的数据"""
        if stage in ["agent", "decision"]:
            self.decision = data
        elif stage == "strategy":
            self.strategy = data
        elif stage in ["case_generator", "cases"]:
            self.cases = data
        elif stage in ["orchestrator", "execution"]:
            self.execution = data
        elif stage in ["healing", "self_healing"]:
            self.healing = data
        elif stage == "report":
            self.report = data
    
    def is_skip(self) -> bool:
        """判断是否跳过测试"""
        if not self.decision:
            return False
        
        action = self.decision.get('action', '')
        return action in ['skip', 'skip_test']
    
    def should_heal(self) -> bool:
        """判断是否需要修复"""
        if not self.execution:
            return False
        
        summary = self.execution.get('summary', {})
        failed = summary.get('failed', 0)
        
        return failed > 0
    
    def get_total_duration(self) -> float:
        """获取总耗时"""
        return sum(event.get('duration', 0.0) for event in self.timeline)
    
    def __repr__(self) -> str:
        """字符串表示"""
        return f"TestContext(trace_id={self.trace_id}, stages={len([s for s in [self.decision, self.strategy, self.cases, self.execution, self.healing, self.report] if s])})"
