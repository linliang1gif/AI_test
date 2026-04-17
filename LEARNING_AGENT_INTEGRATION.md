# LearningAgent 集成指南

## 概述

LearningAgent 是一个学习型代理，用于构建"测试反馈闭环"，让系统具备学习能力，基于历史执行结果优化未来测试。

---

## 核心功能

### 1. 失败模式学习

识别常见失败模式，统计频率和严重程度。

**数据结构**:
```json
{
  "/payment/create::timeout": {
    "api": "/payment/create",
    "error_type": "timeout",
    "frequency": 10,
    "first_seen": "2026-04-17T10:00:00",
    "last_seen": "2026-04-17T12:00:00",
    "severity": 0.8,
    "error_messages": [...]
  }
}
```

### 2. 修复策略学习

统计每种错误类型的最优修复策略。

**数据结构**:
```json
{
  "timeout": {
    "L1_RETRY": {"success": 8, "total": 10, "rate": 0.8},
    "L2_DATA": {"success": 2, "total": 3, "rate": 0.67}
  }
}
```

### 3. 覆盖缺口分析

识别高风险但测试少的 API。

**数据结构**:
```json
[
  {
    "api": "/payment/refund",
    "test_count": 2,
    "failure_rate": 1.0,
    "priority": "high",
    "identified_at": "2026-04-17T10:00:00"
  }
]
```

### 4. 数据持久化

存储学习结果到知识库。

**文件结构**:
```
knowledge/
├── failures.json          # 失败模式
├── healing_stats.json     # 修复统计
├── coverage_gaps.json     # 覆盖缺口
└── api_stats.json         # API 统计
```

---

## API 接口

### 初始化

```python
from modules.agents import LearningAgent

learning_agent = LearningAgent(knowledge_dir="knowledge")
```

### 学习

```python
# 学习执行结果和修复记录
learning_agent.learn(execution_results, healing_records)
```

### 查询失败模式

```python
# 获取所有失败模式
patterns = learning_agent.get_failure_patterns()

# 获取特定 API 的失败模式
patterns = learning_agent.get_failure_patterns(api="/payment/create")

# 获取高频失败模式
patterns = learning_agent.get_failure_patterns(min_frequency=5)
```

### 查询最优修复策略

```python
# 获取 timeout 错误的最优修复策略
best_strategy = learning_agent.get_best_healing_strategy("timeout")
# 返回: "L1_RETRY"
```

### 查询高风险 API

```python
# 获取前 10 个高风险 API
high_risk = learning_agent.get_high_risk_apis(top_n=10)
```

### 查询覆盖缺口

```python
# 获取所有覆盖缺口
gaps = learning_agent.get_coverage_gaps()

# 获取高优先级缺口
gaps = learning_agent.get_coverage_gaps(priority="high")
```

### 获取学习摘要

```python
summary = learning_agent.get_learning_summary()
```

---

## 集成方式

### 1. 在 Pipeline 中集成

在 `pipeline_v2.py` 的最后添加学习阶段：

```python
# ========== 阶段 6: Learning Agent（学习反馈）==========
print(f"\n[6/6] 🧠 Learning Agent - 学习反馈...")

try:
    learning_agent = LearningAgent(knowledge_dir="knowledge")
    
    # 学习执行结果和修复记录
    learning_agent.learn(results, healing_records)
    
    # 获取学习摘要
    summary = learning_agent.get_learning_summary()
    
    print(f"  ✅ 学习完成")
    print(f"     失败模式: {summary['failure_patterns']['total_patterns']}")
    print(f"     修复策略: {summary['healing_strategies']['error_types_learned']}")
    print(f"     覆盖缺口: {summary['coverage_gaps']['total_gaps']}")
    print(f"     高风险API: {summary['api_stats']['high_risk_apis']}")

except Exception as e:
    print(f"  ⚠️  学习失败: {e}")
```

---

### 2. 与 DesignAgent 集成

DesignAgent 在生成测试时调用 LearningAgent 获取高风险 API：

```python
class DesignAgent:
    def __init__(self, config=None, learning_agent=None):
        self.config = config or {}
        self.learning_agent = learning_agent
    
    def design_from_discovery(self, test_points):
        """设计测试用例"""
        
        # 如果有 LearningAgent，优先为高风险 API 生成更多测试
        if self.learning_agent:
            high_risk_apis = self.learning_agent.get_high_risk_apis()
            
            # 为高风险 API 增加测试用例数量
            for api_info in high_risk_apis:
                api = api_info['api']
                # 增加该 API 的测试用例配额
                self.logger.info(f"高风险 API {api}，增加测试用例")
        
        # 继续正常的设计流程
        testcases = self._generate_testcases(test_points)
        
        return testcases
```

**使用示例**:
```python
learning_agent = LearningAgent()
design_agent = DesignAgent(learning_agent=learning_agent)

testcases = design_agent.design_from_discovery(test_points)
```

---

### 3. 与 HealingAgent 集成

HealingAgent 在修复时调用 LearningAgent 获取最优策略：

```python
class HealingAgent:
    def __init__(self, config=None, learning_agent=None):
        self.config = config or {}
        self.learning_agent = learning_agent
    
    def _decide_healing_level(self, failure_info):
        """决策修复层级"""
        
        category = failure_info['category']
        error_type = category.value if hasattr(category, 'value') else str(category)
        
        # 如果有 LearningAgent，使用学习到的最优策略
        if self.learning_agent:
            best_strategy = self.learning_agent.get_best_healing_strategy(error_type)
            
            if best_strategy:
                self.logger.info(f"使用学习到的最优策略: {best_strategy}")
                return self._get_healing_level(best_strategy)
        
        # 否则使用默认决策逻辑
        return self._default_decision(failure_info)
```

**使用示例**:
```python
learning_agent = LearningAgent()
healing_agent = HealingAgent(learning_agent=learning_agent)

healing_records = healing_agent.heal(results)
```

---

## 完整集成示例

### Pipeline V3（带学习反馈）

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pipeline V3 - 带学习反馈闭环
"""

from modules.discovery import TestDiscoveryAgent
from modules.agents import DesignAgent, ExecutionAgent, HealingAgent, LearningAgent
from modules.report import ReportGenerator


def run_pipeline_v3(old_swagger, new_swagger, base_url, output_dir):
    """运行带学习反馈的 Pipeline"""
    
    # 初始化 LearningAgent
    learning_agent = LearningAgent(knowledge_dir="knowledge")
    
    # 1. Discovery
    discovery_agent = TestDiscoveryAgent()
    test_points = discovery_agent.discover_from_swagger_changes(
        old_swagger=old_swagger,
        new_swagger=new_swagger
    )
    
    # 2. Design（使用学习到的高风险 API）
    design_agent = DesignAgent(learning_agent=learning_agent)
    testcases = design_agent.design_from_discovery(test_points)
    
    # 3. Execution
    execution_agent = ExecutionAgent(config={'strategy': 'adaptive'})
    results = execution_agent.run(testcases)
    
    # 4. Healing（使用学习到的最优策略）
    healing_agent = HealingAgent(learning_agent=learning_agent)
    healing_records = healing_agent.heal(results)
    
    # 5. Report
    report_generator = ReportGenerator()
    report = report_generator.generate(results)
    
    # 6. Learning（学习本次执行结果）
    learning_agent.learn(results, healing_records)
    
    # 7. 输出学习摘要
    summary = learning_agent.get_learning_summary()
    print(f"\n学习摘要:")
    print(f"  失败模式: {summary['failure_patterns']['total_patterns']}")
    print(f"  修复策略: {summary['healing_strategies']['error_types_learned']}")
    print(f"  覆盖缺口: {summary['coverage_gaps']['total_gaps']}")
    print(f"  高风险API: {summary['api_stats']['high_risk_apis']}")
    
    return results
```

---

## 数据存储结构

### failures.json

```json
{
  "/payment/create::timeout": {
    "api": "/payment/create",
    "error_type": "timeout",
    "frequency": 10,
    "first_seen": "2026-04-17T10:00:00",
    "last_seen": "2026-04-17T12:00:00",
    "severity": 0.8,
    "error_messages": [
      {
        "message": "Connection timeout after 30s",
        "timestamp": "2026-04-17T10:00:00"
      }
    ]
  }
}
```

### healing_stats.json

```json
{
  "timeout": {
    "L1_RETRY": {
      "success": 8,
      "total": 10,
      "rate": 0.8
    },
    "L2_DATA": {
      "success": 2,
      "total": 3,
      "rate": 0.67
    }
  },
  "connection": {
    "L1_RETRY": {
      "success": 5,
      "total": 7,
      "rate": 0.71
    }
  }
}
```

### coverage_gaps.json

```json
[
  {
    "api": "/payment/refund",
    "test_count": 2,
    "failure_rate": 1.0,
    "priority": "high",
    "identified_at": "2026-04-17T10:00:00"
  },
  {
    "api": "/order/cancel",
    "test_count": 3,
    "failure_rate": 0.67,
    "priority": "high",
    "identified_at": "2026-04-17T10:05:00"
  }
]
```

### api_stats.json

```json
{
  "/payment/create": {
    "total_executions": 100,
    "total_failures": 15,
    "failure_rate": 0.15,
    "last_executed": "2026-04-17T12:00:00",
    "risk_score": 0.55
  },
  "/order/create": {
    "total_executions": 80,
    "total_failures": 5,
    "failure_rate": 0.0625,
    "last_executed": "2026-04-17T12:00:00",
    "risk_score": 0.19
  }
}
```

---

## 学习反馈闭环

```
┌─────────────────────────────────────────────────────────┐
│                  测试反馈闭环                             │
└─────────────────────────────────────────────────────────┘

执行测试
    ↓
收集结果（ExecutionResult + HealingRecord）
    ↓
LearningAgent.learn()
    ├─ 学习失败模式
    ├─ 学习修复策略
    ├─ 分析覆盖缺口
    └─ 更新 API 统计
    ↓
持久化知识（knowledge/*.json）
    ↓
下次测试时使用
    ├─ DesignAgent 优先测试高风险 API
    ├─ HealingAgent 使用最优修复策略
    └─ 补充覆盖缺口
```

---

## 使用场景

### 场景 1: 识别高风险 API

```python
learning_agent = LearningAgent()

# 获取高风险 API
high_risk = learning_agent.get_high_risk_apis(top_n=5)

for api in high_risk:
    print(f"{api['api']}: 风险分数={api['risk_score']:.2f}")
```

### 场景 2: 优化修复策略

```python
# 查询 timeout 错误的最优修复策略
best_strategy = learning_agent.get_best_healing_strategy("timeout")

# 在 HealingAgent 中使用
if best_strategy == "L1_RETRY":
    # 使用重试策略
    pass
elif best_strategy == "L2_DATA":
    # 使用数据修复策略
    pass
```

### 场景 3: 补充测试覆盖

```python
# 获取覆盖缺口
gaps = learning_agent.get_coverage_gaps(priority="high")

# 为这些 API 生成更多测试
for gap in gaps:
    print(f"需要补充测试: {gap['api']} (失败率={gap['failure_rate']:.1%})")
```

---

## 总结

LearningAgent 实现了完整的测试反馈闭环：

1. ✅ **失败模式学习** - 识别常见失败模式
2. ✅ **修复策略学习** - 统计最优修复策略
3. ✅ **覆盖缺口分析** - 识别高风险但测试少的API
4. ✅ **数据持久化** - 存储和加载学习结果

通过与 DesignAgent 和 HealingAgent 集成，系统具备了真正的"学习能力"，能够基于历史数据不断优化测试策略！
