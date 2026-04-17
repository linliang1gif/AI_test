"""
AI Core 使用示例
演示如何使用AI调度层的各个组件
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_core import TestAgent, TestWorkflow, PytestSkill, OrchestrationRunner


def demo_test_agent():
    """演示TestAgent使用"""
    print("\n=== TestAgent 演示 ===")
    
    agent = TestAgent()
    
    task = {
        "id": "task_001",
        "name": "登录功能测试",
        "requirement": "测试用户登录功能，包括正常登录、错误密码、账号不存在等场景"
    }
    
    result = agent.execute_task(task)
    print(f"任务执行结果: {result['status']}")
    print(f"生成测试点数量: {result.get('artifacts', {}).get('summary', {}).get('testpoint_count', 0)}")


def demo_test_workflow():
    """演示TestWorkflow使用"""
    print("\n=== TestWorkflow 演示 ===")
    
    workflow = TestWorkflow()
    
    input_data = {
        "doc_path": "test_requirement.docx",
        "project": "AI Test Platform"
    }
    
    result = workflow.run(input_data)
    print(f"工作流执行结果: {result['status']}")
    print(f"完成阶段: {list(result['stages'].keys())}")


def demo_pytest_skill():
    """演示PytestSkill使用"""
    print("\n=== PytestSkill 演示 ===")
    
    skill = PytestSkill()
    
    test_files = ["tests/test_example.py"]
    
    result = skill.execute(test_files, options={"verbose": True})
    print(f"测试执行结果: {result['status']}")
    print(f"测试摘要: {result.get('summary', {})}")


def demo_orchestration_runner():
    """演示OrchestrationRunner使用"""
    print("\n=== OrchestrationRunner 演示 ===")
    
    # 创建调度器
    runner = OrchestrationRunner(config={"max_workers": 4})
    
    # 注册组件
    runner.register_agent("test_agent", TestAgent())
    runner.register_workflow("test_workflow", TestWorkflow())
    runner.register_skill("pytest", PytestSkill())
    
    # 查看状态
    status = runner.get_status()
    print(f"调度器状态: {status}")
    
    # 运行Agent任务
    task = {
        "id": "task_002",
        "requirement": "API接口测试"
    }
    result = runner.run_agent_task("test_agent", task)
    print(f"Agent任务结果: {result['status']}")
    
    # 关闭调度器
    runner.shutdown()


def demo_parallel_execution():
    """演示并行执行"""
    print("\n=== 并行执行演示 ===")
    
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
        }
    ]
    
    results = runner.run_parallel_tasks(tasks)
    print(f"并行执行完成，共 {len(results)} 个任务")
    
    runner.shutdown()


def demo_pipeline():
    """演示流水线"""
    print("\n=== 流水线演示 ===")
    
    runner = OrchestrationRunner()
    runner.register_agent("test_agent", TestAgent())
    runner.register_skill("pytest", PytestSkill())
    
    pipeline_config = {
        "stages": [
            {
                "name": "需求分析",
                "type": "sequential",
                "task": {
                    "type": "agent",
                    "params": {
                        "agent_name": "test_agent",
                        "task": {"requirement": "用户注册功能"}
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
                            "kwargs": {"test_files": ["tests/test_register.py"]}
                        }
                    }
                ]
            }
        ]
    }
    
    result = runner.create_pipeline(pipeline_config)
    print(f"流水线执行结果: {result['status']}")
    print(f"执行阶段数: {len(result['stages'])}")
    
    runner.shutdown()


if __name__ == "__main__":
    print("AI Core 使用示例")
    print("=" * 50)
    
    # 运行各个演示
    demo_test_agent()
    demo_test_workflow()
    demo_pytest_skill()
    demo_orchestration_runner()
    demo_parallel_execution()
    demo_pipeline()
    
    print("\n" + "=" * 50)
    print("演示完成！")
