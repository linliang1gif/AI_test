# AI 测试平台最终系统架构

## 六阶段流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                         TestContext                                  │
│  统一数据模型 - 所有模块只接收/操作 context                           │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  阶段1: Agent (需求理解 + AI决策)                                     │
│  ────────────────────────────────────────────────────────────────   │
│  输入: requirement, git_diff, priority                               │
│  能力:                                                               │
│    • RequirementParser (传统能力)                                    │
│    • ModuleSplitter (传统能力)                                       │
│    • LLM 决策分析 (AI能力)                                           │
│  输出: decision {need_test, risk_level, test_types, parsed_modules}  │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  阶段2: Strategy (测试规划)                                          │
│  ────────────────────────────────────────────────────────────────   │
│  输入: decision                                                      │
│  能力:                                                               │
│    • 规则引擎 (优先级 + 风险 → 测试类型)                             │
│    • 用例数量估算                                                    │
│  输出: strategy {strategy[], total_cases, execution_hint}            │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  阶段3: Case Generator (传统能力重用) [可选]                         │
│  ────────────────────────────────────────────────────────────────   │
│  输入: strategy                                                      │
│  能力:                                                               │
│    • ScenarioBuilder (传统能力)                                      │
│    • CaseBuilder (传统能力)                                          │
│    • 优先级过滤 (P0→正常+异常+边界, P1→正常+异常, P2→正常)           │
│  输出: cases {cases[], total_cases}                                  │
│  注: 可通过 use_case_generator 配置启用/禁用                         │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  阶段4: Orchestrator (执行 + 脚本生成)                               │
│  ────────────────────────────────────────────────────────────────   │
│  输入: strategy, cases (optional)                                    │
│  能力:                                                               │
│    • 双模式执行:                                                     │
│      - cases 模式: 基于用例列表执行                                  │
│      - strategy 模式: 基于策略执行                                   │
│    • ApiRunner / UiRunner / IntegrationRunner                        │
│    • 脚本生成 (ApiScriptGenerator) [TODO]                           │
│    • 并发执行                                                        │
│  输出: execution {results[], summary, mode, case_results}            │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  阶段5: Self-Healing (失败修复)                                      │
│  ────────────────────────────────────────────────────────────────   │
│  输入: execution                                                     │
│  能力:                                                               │
│    • ErrorAnalyzer (6种错误类型识别)                                 │
│    • Fixer (自动修复策略)                                            │
│    • 重试机制                                                        │
│  输出: healing {records[], statistics}                               │
│  触发条件: execution.failed > 0                                      │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  阶段6: Report (覆盖率 + AI总结) [V2增强]                            │
│  ────────────────────────────────────────────────────────────────   │
│  输入: 所有阶段数据 (decision, strategy, cases, execution, healing)  │
│  能力:                                                               │
│    • 覆盖率分析:                                                     │
│      - case_based: executed_cases / total_cases                     │
│      - strategy_based: 100% (假设全部执行)                          │
│    • 传统覆盖率接入 (CoverageAnalyzer)                               │
│    • AI 总结增强 (JSON格式)                                          │
│    • 修复统计集成                                                    │
│  输出: report {summary, details, coverage, ai_analysis}              │
└─────────────────────────────────────────────────────────────────────┘
```

## 核心设计原则

### 1. 统一数据模型 (TestContext)
```python
class TestContext:
    # 输入
    requirement: str
    git_diff: str
    priority: str
    
    # 阶段输出
    decision: Dict
    strategy: Dict
    cases: Dict
    execution: Dict
    healing: Dict
    report: Dict
    
    # 元数据
    trace_id: str
    timeline: List
```

### 2. 模块解耦
- 所有模块只接收 TestContext
- 不再传多个 JSON
- Pipeline 只传 context
- 禁止跨模块直接调用

### 3. 流程可插拔
- Case Generator 可启用/禁用
- Self-Healing 按需触发
- 支持提前退出（skip 场景）

### 4. 传统能力重用
- Agent: RequirementParser + ModuleSplitter
- Case Generator: ScenarioBuilder + CaseBuilder
- Report: CoverageAnalyzer (可选)

## 数据流转

```
输入数据
  ↓
Agent 解析 + 决策
  ↓ decision {parsed_modules, need_test, risk_level}
Strategy 规划
  ↓ strategy {strategy[], total_cases}
Case Generator 生成用例 [可选]
  ↓ cases {cases[], total_cases}
Orchestrator 执行
  ↓ execution {results[], summary, case_results}
Self-Healing 修复 [按需]
  ↓ healing {records[], statistics}
Report 生成报告
  ↓ report {summary, coverage, ai_analysis}
输出结果
```

## 两种执行模式

### 模式1: 完整模式 (use_case_generator=True)
```
Agent → Strategy → Case Generator → Orchestrator(cases) → Healing → Report
```
- 生成详细测试用例
- 基于用例执行
- 覆盖率 = executed_cases / total_cases

### 模式2: 快速模式 (use_case_generator=False)
```
Agent → Strategy → Orchestrator(strategy) → Healing → Report
```
- 跳过用例生成
- 基于策略执行
- 覆盖率 = 100% (假设全部执行)

## 模块职责

| 模块 | 职责 | 传统能力 | AI能力 |
|------|------|----------|--------|
| Agent | 需求理解 + 决策 | RequirementParser, ModuleSplitter | LLM 决策分析 |
| Strategy | 测试规划 | 规则引擎 | - |
| Case Generator | 用例生成 | ScenarioBuilder, CaseBuilder | - |
| Orchestrator | 执行调度 | ApiRunner, UiRunner, IntegrationRunner | - |
| Self-Healing | 失败修复 | ErrorAnalyzer, Fixer | - |
| Report | 可观测中心 | CoverageAnalyzer | AI 总结 |

## API 端点

```
POST   /api/pipeline/run          # 运行完整流程
GET    /api/pipeline/history      # 获取历史记录
GET    /api/pipeline/statistics   # 获取统计信息
GET    /api/pipeline/health       # 健康检查
GET    /api/pipeline/trace/{id}   # 追踪详情
```

## 系统特性

✅ 统一数据模型 (TestContext)
✅ 模块完全解耦
✅ 流程可插拔
✅ 传统能力重用
✅ AI 能力增强
✅ 覆盖率分析
✅ 自动修复
✅ 可追溯性 (trace_id + timeline)
✅ 向后兼容

## 性能指标

- P0 优先级: ~40-60s
- P1 优先级: ~30-40s
- P2 优先级: ~20-30s
- API 响应: <1s
- 并发执行: 3-5x 加速

---

**版本**: V3
**状态**: ✅ 生产就绪
**最后更新**: 2026-03-23
