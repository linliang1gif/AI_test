# AI Core 完整目录结构

```
ai_core/
│
├── __init__.py                          # 模块入口，导出核心类
│   ├── TestAgent                        # 智能测试代理
│   ├── TestWorkflow                     # 测试工作流
│   ├── PytestSkill                      # Pytest技能
│   └── OrchestrationRunner              # 编排调度器
│
├── agents/                              # 智能代理模块
│   ├── __init__.py                      # 导出TestAgent
│   └── test_agent.py                    # 测试代理实现
│       ├── TestAgent类
│       │   ├── understand_requirement() # 理解测试需求
│       │   ├── plan_test_strategy()     # 规划测试策略
│       │   ├── generate_test_artifacts()# 生成测试制品
│       │   ├── execute_task()           # 执行测试任务
│       │   └── get_status()             # 获取代理状态
│       └── 调用已有模块:
│           ├── ai.ai_client.AIClient
│           ├── ai.enhanced_ai_client.EnhancedAIClient
│           ├── parser.requirement_parser.RequirementParser
│           ├── test_design.testpoint_generator.TestPointGenerator
│           └── test_design.testcase_generator.TestCaseGenerator
│
├── workflow/                            # 工作流模块
│   ├── __init__.py                      # 导出TestWorkflow
│   └── test_workflow.py                 # 测试工作流实现
│       ├── WorkflowStage枚举
│       │   ├── PARSE                    # 解析阶段
│       │   ├── DESIGN                   # 设计阶段
│       │   ├── GENERATE                 # 生成阶段
│       │   ├── EXECUTE                  # 执行阶段
│       │   └── REPORT                   # 报告阶段
│       ├── TestWorkflow类
│       │   ├── run()                    # 运行完整工作流
│       │   ├── run_partial()            # 运行部分阶段
│       │   ├── register_hook()          # 注册钩子函数
│       │   └── get_status()             # 获取工作流状态
│       └── 调用已有模块:
│           ├── parser.requirement_parser.RequirementParser
│           ├── test_design.testpoint_generator.TestPointGenerator
│           ├── test_design.testcase_generator.TestCaseGenerator
│           ├── automation.api_script_generator.APIScriptGenerator
│           ├── executor.pytest_runner.PytestRunner
│           └── report.report_generator.ReportGenerator
│
├── skills/                              # 技能库模块
│   ├── __init__.py                      # 导出PytestSkill
│   └── pytest_skill.py                  # Pytest技能实现
│       ├── PytestSkill类
│       │   ├── execute()                # 执行pytest测试
│       │   ├── execute_with_retry()     # 带重试的执行
│       │   └── generate_coverage_report()# 生成覆盖率报告
│       └── 调用已有模块:
│           └── executor.pytest_runner.PytestRunner
│
├── orchestration/                       # 编排调度模块
│   ├── __init__.py                      # 导出OrchestrationRunner
│   └── runner.py                        # 调度器实现
│       ├── OrchestrationRunner类
│       │   ├── register_agent()         # 注册Agent
│       │   ├── register_workflow()      # 注册Workflow
│       │   ├── register_skill()         # 注册Skill
│       │   ├── run_agent_task()         # 运行Agent任务
│       │   ├── run_workflow()           # 运行Workflow
│       │   ├── run_skill()              # 运行Skill
│       │   ├── run_parallel_tasks()     # 并行运行任务
│       │   ├── create_pipeline()        # 创建测试流水线
│       │   ├── get_status()             # 获取调度器状态
│       │   └── shutdown()               # 关闭调度器
│       └── 使用ThreadPoolExecutor实现并行调度
│
├── examples/                            # 示例代码
│   └── demo_ai_core.py                  # 完整使用示例
│       ├── demo_test_agent()            # Agent演示
│       ├── demo_test_workflow()         # Workflow演示
│       ├── demo_pytest_skill()          # Skill演示
│       ├── demo_orchestration_runner()  # 调度器演示
│       ├── demo_parallel_execution()    # 并行执行演示
│       └── demo_pipeline()              # 流水线演示
│
├── README.md                            # 使用文档
└── STRUCTURE.md                         # 本文档（目录结构说明）
```

## 模块依赖关系

```
OrchestrationRunner (编排调度器)
    ├── TestAgent (智能代理)
    │   ├── AIClient (已有)
    │   ├── EnhancedAIClient (已有)
    │   ├── RequirementParser (已有)
    │   ├── TestPointGenerator (已有)
    │   └── TestCaseGenerator (已有)
    │
    ├── TestWorkflow (工作流)
    │   ├── RequirementParser (已有)
    │   ├── TestPointGenerator (已有)
    │   ├── TestCaseGenerator (已有)
    │   ├── APIScriptGenerator (已有)
    │   ├── PytestRunner (已有)
    │   └── ReportGenerator (已有)
    │
    └── PytestSkill (技能)
        └── PytestRunner (已有)
```

## 核心特性

### 1. 非侵入式设计
- 不修改任何已有代码
- 只通过import调用现有模块
- 完全独立的新模块

### 2. 模块化架构
- Agent: 智能决策和任务规划
- Workflow: 流程编排和阶段管理
- Skill: 具体能力封装
- Orchestration: 统一调度和协调

### 3. 灵活组合
- 可单独使用任一组件
- 可通过调度器组合使用
- 支持自定义扩展

### 4. 并行执行
- ThreadPoolExecutor实现
- 支持任务并行调度
- 提高执行效率

### 5. 完整监控
- 状态跟踪
- 日志记录
- 错误处理

## 使用场景

### 场景1: 单独使用Agent
```python
from ai_core import TestAgent

agent = TestAgent()
result = agent.execute_task(task)
```

### 场景2: 单独使用Workflow
```python
from ai_core import TestWorkflow

workflow = TestWorkflow()
result = workflow.run(input_data)
```

### 场景3: 使用调度器编排
```python
from ai_core import OrchestrationRunner, TestAgent, TestWorkflow

runner = OrchestrationRunner()
runner.register_agent("agent1", TestAgent())
runner.register_workflow("workflow1", TestWorkflow())

# 运行Agent
result1 = runner.run_agent_task("agent1", task)

# 运行Workflow
result2 = runner.run_workflow("workflow1", input_data)
```

### 场景4: 创建测试流水线
```python
pipeline_config = {
    "stages": [
        {"name": "分析", "type": "sequential", "task": {...}},
        {"name": "执行", "type": "parallel", "tasks": [...]},
        {"name": "报告", "type": "sequential", "task": {...}}
    ]
}

result = runner.create_pipeline(pipeline_config)
```

## 扩展点

1. **新增Agent**: 继承TestAgent或创建新类
2. **新增Skill**: 实现execute()方法
3. **自定义Workflow**: 继承TestWorkflow添加新阶段
4. **钩子函数**: 在Workflow各阶段注册钩子

## 版本信息

- 版本: 1.0.0
- 创建日期: 2024-03-20
- Python版本: 3.7+
