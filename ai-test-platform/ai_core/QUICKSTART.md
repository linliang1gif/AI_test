# AI Core 快速开始指南

## 安装

AI Core是AI Test Platform的一部分，无需单独安装。

```bash
# 确保已安装项目依赖
cd ai-test-platform
pip install -r requirements.txt
```

## 5分钟快速上手

### 1. 导入模块

```python
from ai_core import TestAgent, TestWorkflow, PytestSkill, OrchestrationRunner
```

### 2. 使用TestAgent（智能代理）

```python
# 创建代理
agent = TestAgent()

# 定义任务
task = {
    "id": "task_001",
    "name": "登录功能测试",
    "requirement": "测试用户登录功能，包括正常登录、错误密码、账号不存在等场景",
    "doc_path": "requirements/login.docx"  # 可选
}

# 执行任务
result = agent.execute_task(task)

# 查看结果
print(f"状态: {result['status']}")
print(f"测试点数量: {result['artifacts']['summary']['testpoint_count']}")
print(f"测试用例数量: {result['artifacts']['summary']['testcase_count']}")
```

### 3. 使用TestWorkflow（工作流）

```python
# 创建工作流
workflow = TestWorkflow()

# 准备输入数据
input_data = {
    "doc_path": "requirements/feature.docx",
    "project": "AI Test Platform"
}

# 运行完整工作流
result = workflow.run(input_data)

# 查看各阶段结果
for stage_name, stage_result in result['stages'].items():
    print(f"{stage_name}: {stage_result['status']}")
```

### 4. 使用PytestSkill（测试技能）

```python
# 创建技能
skill = PytestSkill()

# 执行测试
result = skill.execute(
    test_files=["tests/test_login.py", "tests/test_api.py"],
    options={"verbose": True, "coverage": True}
)

# 查看测试结果
summary = result['summary']
print(f"总计: {summary['total']}")
print(f"通过: {summary['passed']}")
print(f"失败: {summary['failed']}")
```

### 5. 使用OrchestrationRunner（调度器）

```python
# 创建调度器
runner = OrchestrationRunner(config={"max_workers": 4})

# 注册组件
runner.register_agent("test_agent", TestAgent())
runner.register_workflow("test_workflow", TestWorkflow())
runner.register_skill("pytest", PytestSkill())

# 运行Agent任务
agent_result = runner.run_agent_task("test_agent", task)

# 运行Workflow
workflow_result = runner.run_workflow("test_workflow", input_data)

# 运行Skill
skill_result = runner.run_skill("pytest", test_files=["tests/test_example.py"])

# 查看调度器状态
status = runner.get_status()
print(status)

# 关闭调度器
runner.shutdown()
```

## 进阶使用

### 并行执行多个测试

```python
runner = OrchestrationRunner(config={"max_workers": 4})
runner.register_skill("pytest", PytestSkill())

# 定义并行任务
tasks = [
    {
        "type": "skill",
        "params": {
            "skill_name": "pytest",
            "kwargs": {"test_files": ["tests/test_module1.py"]}
        }
    },
    {
        "type": "skill",
        "params": {
            "skill_name": "pytest",
            "kwargs": {"test_files": ["tests/test_module2.py"]}
        }
    },
    {
        "type": "skill",
        "params": {
            "skill_name": "pytest",
            "kwargs": {"test_files": ["tests/test_module3.py"]}
        }
    }
]

# 并行执行
results = runner.run_parallel_tasks(tasks)

# 查看结果
for i, result in enumerate(results):
    print(f"任务{i+1}: {result['status']}")

runner.shutdown()
```

### 创建测试流水线

```python
runner = OrchestrationRunner()
runner.register_agent("test_agent", TestAgent())
runner.register_skill("pytest", PytestSkill())

# 定义流水线
pipeline_config = {
    "stages": [
        {
            "name": "需求分析",
            "type": "sequential",
            "task": {
                "type": "agent",
                "params": {
                    "agent_name": "test_agent",
                    "task": {
                        "requirement": "用户注册功能",
                        "doc_path": "requirements/register.docx"
                    }
                }
            }
        },
        {
            "name": "并行测试执行",
            "type": "parallel",
            "tasks": [
                {
                    "type": "skill",
                    "params": {
                        "skill_name": "pytest",
                        "kwargs": {"test_files": ["tests/test_register_ui.py"]}
                    }
                },
                {
                    "type": "skill",
                    "params": {
                        "skill_name": "pytest",
                        "kwargs": {"test_files": ["tests/test_register_api.py"]}
                    }
                }
            ]
        }
    ]
}

# 执行流水线
result = runner.create_pipeline(pipeline_config)

# 查看流水线结果
print(f"流水线状态: {result['status']}")
for stage in result['stages']:
    print(f"  {stage['stage']}: 完成")

runner.shutdown()
```

### 使用Workflow钩子

```python
workflow = TestWorkflow()

# 注册before钩子
def before_execute(input_data):
    print("准备执行测试...")
    print(f"测试文件: {input_data.get('scripts', [])}")

workflow.register_hook("before_stage", WorkflowStage.EXECUTE, before_execute)

# 注册after钩子
def after_execute(result):
    print("测试执行完成!")
    print(f"结果: {result.get('status')}")

workflow.register_hook("after_stage", WorkflowStage.EXECUTE, after_execute)

# 运行工作流（钩子会自动触发）
result = workflow.run(input_data)
```

### 失败重试

```python
skill = PytestSkill()

# 执行测试，失败自动重试最多3次
result = skill.execute_with_retry(
    test_files=["tests/test_flaky.py"],
    max_retries=3
)

# 查看重试情况
print(f"总尝试次数: {result['total_attempts']}")
print(f"最终结果: {result['final_result']['status']}")
```

## 完整示例

运行示例代码：

```bash
cd ai-test-platform/ai_core/examples
python demo_ai_core.py
```

## 常见问题

### Q: 如何只运行Workflow的部分阶段？

```python
from ai_core.workflow.test_workflow import WorkflowStage

workflow = TestWorkflow()

# 只运行解析和设计阶段
result = workflow.run_partial(
    stages=[WorkflowStage.PARSE, WorkflowStage.DESIGN],
    input_data={"doc_path": "requirements/feature.docx"}
)
```

### Q: 如何自定义Agent？

```python
from ai_core.agents.test_agent import TestAgent

class MyCustomAgent(TestAgent):
    def custom_analysis(self, data):
        # 自定义分析逻辑
        return self.ai_client.analyze(data)

# 使用自定义Agent
agent = MyCustomAgent()
runner.register_agent("custom_agent", agent)
```

### Q: 如何添加新的Skill？

```python
class SeleniumSkill:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def execute(self, test_files, **kwargs):
        # Selenium测试逻辑
        return {"status": "completed", "results": [...]}

# 注册新Skill
runner.register_skill("selenium", SeleniumSkill())
```

## 下一步

- 查看 [README.md](README.md) 了解详细文档
- 查看 [STRUCTURE.md](STRUCTURE.md) 了解架构设计
- 运行 `examples/demo_ai_core.py` 查看完整示例

## 技术支持

如有问题，请查看项目文档或联系开发团队。
