#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Test Platform - Prompt库

包含所有AI生成任务的Prompt模板，是平台的核心知识库。
"""

class PromptLibrary:
    """Prompt库类"""
    
    @staticmethod
    def get_test_strategy_prompt(requirement: str) -> str:
        """测试策略生成Prompt"""
        return f"""
你是一名资深的测试架构师。请根据以下需求文档，生成全面的测试策略。

需求文档：
{requirement}

请生成测试策略，包含以下内容：
1. 测试目标和范围
2. 测试类型（功能测试、性能测试、安全测试等）
3. 测试优先级
4. 风险评估
5. 测试环境要求
6. 测试数据策略
7. 测试工具和框架
8. 测试进度安排

请以结构化的方式输出，每个部分都要详细说明。
"""

    @staticmethod
    def get_module_split_prompt(requirement: str) -> str:
        """功能模块拆分Prompt"""
        return f"""
你是一名系统分析师。请根据以下需求文档，将系统拆分为独立的功能模块。

需求文档：
{requirement}

请按照以下原则进行模块拆分：
1. 每个模块应该有明确的职责边界
2. 模块之间的耦合度要低
3. 模块内部的内聚度要高
4. 考虑业务流程的完整性

请以JSON格式返回结果：
{{
    "modules": [
        {{
            "name": "模块名称",
            "description": "模块描述",
            "functions": ["功能1", "功能2", "功能3"],
            "dependencies": ["依赖的其他模块"],
            "priority": "高/中/低"
        }}
    ]
}}
"""

    @staticmethod
    def get_testpoint_generation_prompt(module_info: str) -> str:
        """测试点生成Prompt"""
        return f"""
你是一名测试设计专家。请根据以下功能模块信息，生成全面的测试点。

模块信息：
{module_info}

请从以下维度生成测试点：
1. 功能测试点 - 验证核心功能是否正常工作
2. 边界测试点 - 验证边界条件和极值情况
3. 异常测试点 - 验证异常输入和错误处理
4. 权限测试点 - 验证访问控制和权限管理
5. 安全测试点 - 验证安全漏洞和攻击防护
6. 性能测试点 - 验证响应时间和并发处理
7. 兼容性测试点 - 验证不同环境下的兼容性
8. 易用性测试点 - 验证用户体验和操作便利性

请以JSON格式返回结果：
{{
    "testpoints": [
        {{
            "category": "测试类型",
            "name": "测试点名称",
            "description": "测试点描述",
            "priority": "高/中/低",
            "complexity": "简单/中等/复杂"
        }}
    ]
}}
"""

    @staticmethod
    def get_scenario_matrix_prompt(testpoints: str) -> str:
        """测试场景矩阵生成Prompt"""
        return f"""
你是一名测试场景设计专家。请根据以下测试点，生成全面详细的测试场景矩阵。

测试点：
{testpoints}

请考虑以下测试维度的组合，并为每个测试点生成至少20个不同场景：
1. 输入数据：有效数据、无效数据、边界数据、空数据、特殊字符、超长数据、SQL注入、XSS攻击
2. 用户状态：已登录、未登录、权限不足、账户锁定、账户过期、首次登录、多设备登录
3. 系统状态：正常运行、高负载、维护模式、异常状态、数据库故障、缓存失效、服务降级
4. 网络环境：正常网络、慢网络、网络中断、不稳定网络、超时、丢包
5. 设备环境：Chrome、Firefox、Safari、Edge、IE、移动端、平板、不同分辨率
6. 数据状态：数据存在、数据不存在、数据过期、数据损坏、数据重复、数据冲突、并发修改

请生成详尽的场景组合，确保覆盖所有重要的测试路径：
{{
    "scenarios": [
        {{
            "id": "场景ID",
            "name": "场景名称",
            "input_data": "输入数据类型",
            "user_state": "用户状态",
            "system_state": "系统状态",
            "network": "网络环境",
            "device": "设备环境",
            "data_state": "数据状态",
            "expected_result": "预期结果",
            "priority": "高/中/低"
        }}
    ]
}}
"""

    @staticmethod
    def get_testcase_generation_prompt(scenario_matrix: str, module_info: str, similar_cases=None) -> str:
        """测试用例生成Prompt（支持 RAG 历史用例注入）"""
        similar_section = ""
        if similar_cases:
            lines = ["以下是已有的相似测试用例，请生成不重复的新用例："]
            for c in similar_cases[:5]:
                lines.append(f"- [{c.get('priority','')}] {c.get('title','')}（相似度 {c.get('similarity',0):.2f}）")
            similar_section = "\n" + "\n".join(lines) + "\n"

        return f"""
你是一名测试用例设计专家。请根据以下测试场景矩阵和模块信息，生成详细全面的测试用例。

模块信息：
{module_info}

测试场景矩阵：
{scenario_matrix}

请为每个测试场景生成详细的测试用例，包含：
1. 用例标题 - 简洁明确地描述测试目的（不要包含"测试用例标题:"、"测试点:"等前缀，不要包含场景详细信息）
2. 前置条件 - 执行测试前需要满足的条件
3. 测试步骤 - 详细的操作步骤，每步都要清晰（至少5步）
4. 测试数据 - 具体的输入数据和参数（要具体，不要写"有效数据"）
5. 预期结果 - 明确的预期输出和行为
6. 优先级 - 高/中/低
7. 测试类型 - 功能/性能/安全/兼容性等

标题示例（正确）：
- "验证订单列表排序功能"
- "测试翻页功能"
- "检查字段自定义显示"

标题示例（错误，不要这样写）：
- "测试用例标题: 验证订单列表排序功能"
- "功能测试点1-输入数据：有效数据 用户状态：已登录..."

重要要求：
1. 每个模块必须生成至少100个测试用例
2. 覆盖所有正常流程、异常流程、边界条件
3. 包含安全测试、性能测试、兼容性测试
4. 测试步骤要详细具体，不要笼统描述
5. 测试数据要具体，给出实际的示例值
{similar_section}
请以JSON格式返回结果：
{{
    "testcases": [
        {{
            "id": "TC001",
            "title": "验证订单列表排序功能",
            "module": "所属模块",
            "testpoint": "对应测试点",
            "precondition": "前置条件",
            "steps": [
                "步骤1：具体操作",
                "步骤2：具体操作",
                "步骤3：具体操作",
                "步骤4：具体操作",
                "步骤5：具体操作"
            ],
            "test_data": "测试数据",
            "expected_result": "预期结果",
            "priority": "高/中/低",
            "type": "测试类型",
            "complexity": "简单/中等/复杂"
        }}
    ]
}}
"""

    @staticmethod
    def get_api_testcase_prompt(api_info: str, testpoints: str) -> str:
        """接口测试用例生成Prompt"""
        return f"""
你是一名接口测试专家。请根据以下接口信息和测试点，生成接口测试用例。

接口信息：
{api_info}

测试点：
{testpoints}

请生成以下类型的接口测试用例：
1. 正常流程测试 - 验证接口正常功能
2. 参数验证测试 - 验证必填参数、参数类型、参数范围
3. 边界值测试 - 验证参数的边界值情况
4. 异常处理测试 - 验证错误参数和异常情况
5. 权限验证测试 - 验证接口的访问权限
6. 数据格式测试 - 验证请求和响应的数据格式
7. 性能测试 - 验证接口的响应时间和并发能力
8. 安全测试 - 验证SQL注入、XSS等安全问题

请以JSON格式返回结果：
{{
    "api_testcases": [
        {{
            "id": "API_TC001",
            "title": "接口测试用例标题",
            "api_name": "接口名称",
            "method": "HTTP方法",
            "url": "接口URL",
            "headers": {{"Content-Type": "application/json"}},
            "request_data": {{"param1": "value1"}},
            "expected_status": 200,
            "expected_response": {{"result": "success"}},
            "test_type": "测试类型",
            "priority": "高/中/低"
        }}
    ]
}}
"""

    @staticmethod
    def get_automation_script_prompt(api_testcase: str) -> str:
        """自动化脚本生成Prompt"""
        return f"""
你是一名自动化测试工程师。请根据以下接口测试用例，生成pytest自动化测试脚本。

接口测试用例：
{api_testcase}

请生成符合以下要求的pytest脚本：
1. 使用requests库发送HTTP请求
2. 包含完整的断言验证
3. 添加适当的测试数据参数化
4. 包含错误处理和重试机制
5. 添加详细的测试文档和注释
6. 遵循pytest最佳实践

脚本模板：
```python
import pytest
import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

class TestAPI:
    
    def setup_method(self):
        \"\"\"测试前置设置\"\"\"
        pass
    
    def teardown_method(self):
        \"\"\"测试后置清理\"\"\"
        pass
    
    def test_api_function(self):
        \"\"\"测试用例描述\"\"\"
        # 测试实现
        pass
```

请生成完整的可执行pytest脚本。
"""

    @staticmethod
    def get_bug_analysis_prompt(error_log: str, test_context: str) -> str:
        """Bug分析Prompt"""
        return f"""
你是一名资深的Bug分析专家。请根据以下错误日志和测试上下文，进行深入的Bug分析。

错误日志：
{error_log}

测试上下文：
{test_context}

请从以下角度进行分析：
1. Bug类型分类 - 功能缺陷、性能问题、安全漏洞、兼容性问题等
2. 根本原因分析 - 代码逻辑错误、配置问题、环境问题、数据问题等
3. 影响范围评估 - 影响的功能模块、用户群体、业务流程
4. 严重程度评级 - 致命、严重、一般、轻微
5. 复现步骤 - 详细的Bug复现步骤
6. 修复建议 - 具体的修复方案和建议
7. 预防措施 - 如何避免类似问题再次发生
8. 测试建议 - 需要补充的测试用例和测试策略

请以JSON格式返回分析结果：
{{
    "bug_analysis": {{
        "bug_type": "Bug类型",
        "root_cause": "根本原因",
        "impact_scope": "影响范围",
        "severity": "严重程度",
        "reproduce_steps": ["复现步骤1", "复现步骤2"],
        "fix_suggestion": "修复建议",
        "prevention": "预防措施",
        "test_recommendation": "测试建议"
    }}
}}
"""

    @staticmethod
    def get_test_report_prompt(test_results: str, bug_analysis: str) -> str:
        """测试报告生成Prompt"""
        return f"""
你是一名测试报告专家。请根据以下测试结果和Bug分析，生成专业的测试报告。

测试结果：
{test_results}

Bug分析：
{bug_analysis}

请生成包含以下内容的测试报告：
1. 执行摘要 - 测试概况和主要结论
2. 测试统计 - 用例总数、通过率、失败率等
3. 功能覆盖 - 各功能模块的测试覆盖情况
4. 质量评估 - 系统质量评级和风险评估
5. Bug统计 - Bug数量、类型分布、严重程度分布
6. 性能分析 - 响应时间、并发能力等性能指标
7. 风险提示 - 主要风险点和注意事项
8. 改进建议 - 产品改进和测试改进建议

请以结构化的Markdown格式返回报告内容，包含图表和统计数据。
"""

    @staticmethod
    def get_system_prompt() -> str:
        """系统级Prompt"""
        return """
你是AI Test Platform的核心AI助手，专门负责软件测试相关的任务。

你的专业领域包括：
- 测试策略设计
- 测试用例设计
- 自动化测试
- 接口测试
- 性能测试
- 安全测试
- Bug分析
- 测试报告

请始终保持专业、准确、详细的回答风格，确保生成的内容符合软件测试行业标准和最佳实践。

在生成JSON格式的响应时，请确保格式正确，字段完整，数据有效。
在生成代码时，请确保代码可执行，符合相关框架的规范。
在进行分析时，请提供深入的见解和实用的建议。
"""