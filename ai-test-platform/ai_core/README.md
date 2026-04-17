# AI Core - AI调度层

## 概述

AI Core是AI Test Platform的智能调度层，提供Agent、Workflow、Skill的编排和调度能力。

## 目录结构

```
ai_core/
├── __init__.py              # 模块入口
├── agents/                  # 智能代理
│   ├── __init__.py
│   └── test_agent.py       # 测试代理
├── workflow/                # 工作流
│   ├── __init__.py
│   └── test_workflow.py    # 测试工作流
├── skills/                  # 技能库
│   ├── __init__.py
│   └── pytest_skill.py     # Pytest技能
├── orchestration/           # 编排调度
│   ├── __init__.py
│   └── runner.py           # 调度器
└── README.md               # 本文档
```

## 核心组件

### 1. TestAgent (智能测试代理)

负责理解测试需求、规划测试策略、调度测试执行。

```python
from ai_core import TestAgent

# 创建代理
agent = TestAgent()

# 执行任务
task = {
    "id": "task_001",
    "name": "登录功能测试",
    "requirement": "测试用户登录功能",
    "doc_path": "requirements/login.docx"
}

result = agent.execute_task(task)
```

### 2. TestWorkflow (测试工作流)

定义和执行端到端测试流程。

```python
from ai_core import TestWorkflow

# 创建工作流
workflow = TestWorkflow()

# 运行完整工作流
input_data = {
    "doc_path": "requirements/feature.docx"
}

result = workflow.run(input_data)
```

### 3. PytestSkill (Pytest技能)

封装pytest测试执行能力。

```python
from ai_core import PytestSkill

# 创建技能
skill = PytestSkill()

# 执行测试
result = skill.execute(
    test_files=["tests/test_login.py"],
    options={"verbose": True}
)
```

### 4. OrchestrationRunner (编排调度器)

协调Agent、Workflow、Skill的执行。

```python
from ai_core import OrchestrationRunner, TestAgent, TestWorkflow, PytestSkill

# 创建调度器
runner = OrchestrationRunner()

# 注册组件
runner.register_agent("test_agent", TestAgent())
runner.register_workflow("test_workflow", TestWorkflow())
runner.register_skill("pytest", PytestSkill())

# 运行Agent任务
result = runner.run_agent_task("test_agent", task)

# 运行Workflow
result = runner.run_workflow("test_workflow", input_data)

# 并行运行多个任务
tasks = [
    {"type": "agent", "params": {"agent_name": "test_agent", "task": task1}},
    {"type": "skill", "params": {"skill_name": "pytest", "kwargs": {"test_files": ["test1.py"]}}}
]
results = runner.run_parallel_tasks(tasks)
```

## 设计原则

1. **非侵入性**: 不修改任何已有代码，只通过import调用
2. **模块化**: 清晰的职责划分，易于扩展
3. **可组合**: Agent、Workflow、Skill可灵活组合
4. **可观测**: 完整的日志和状态跟踪

## 与现有模块的集成

AI Core通过import方式调用现有模块：

- `ai.ai_client` - AI客户端
- `parser.requirement_parser` - 需求解析
- `test_design.testpoint_generator` - 测试点生成
- `test_design.testcase_generator` - 测试用例生成
- `automation.api_script_generator` - API脚本生成
- `executor.pytest_runner` - Pytest执行器
- `report.report_generator` - 报告生成

## 使用示例

### 完整示例：端到端测试流程

```python
from ai_core import OrchestrationRunner, TestAgent, TestWorkflow, PytestSkill

# 1. 初始化调度器
runner = OrchestrationRunner(config={"max_workers": 4})

# 2. 注册组件
runner.register_agent("main_agent", TestAgent())
runner.register_workflow("e2e_workflow", TestWorkflow())
runner.register_skill("pytest", PytestSkill())

# 3. 创建测试流水线
pipeline_config = {
    "stages": [
        {
            "name": "需求分析",
            "type": "sequential",
            "task": {
                "type": "agent",
                "params": {
                    "agent_name": "main_agent",
                    "task": {
                        "requirement": "用户登录功能",
                        "doc_path": "docs/login.docx"
                    }
                }
            }
        },
        {
            "name": "测试执行",
            "type": "parallel",
            "tasks": [
                {
                    "type": "skill",
                    "params": {
                        "skill_name": "pytest",
                        "kwargs": {"test_files": ["tests/test_login.py"]}
                    }
                },
                {
                    "type": "skill",
                    "params": {
                        "skill_name": "pytest",
                        "kwargs": {"test_files": ["tests/test_api.py"]}
                    }
                }
            ]
        }
    ]
}

# 4. 执行流水线
result = runner.create_pipeline(pipeline_config)

# 5. 查看状态
status = runner.get_status()
print(f"调度器状态: {status}")

# 6. 关闭调度器
runner.shutdown()
```

## 扩展指南

### 添加新的Agent

```python
from ai_core.agents.test_agent import TestAgent

class CustomAgent(TestAgent):
    def custom_method(self):
        # 自定义逻辑
        pass
```

### 添加新的Skill

```python
from ai_core.skills.pytest_skill import PytestSkill

class SeleniumSkill:
    def execute(self, **kwargs):
        # Selenium测试逻辑
        pass
```

## 注意事项

1. 所有组件都是独立的，不依赖修改现有代码
2. 通过OrchestrationRunner统一管理和调度
3. 支持并行执行提高效率
4. 完整的错误处理和日志记录

## 版本

- 当前版本: 1.0.0
- 发布日期: 2024-03-20
