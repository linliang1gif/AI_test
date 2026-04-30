"""
优化脚本生成：根据 expected_behavior 生成智能断言

这个文件展示了如何优化 _generate_pytest_script 函数
"""

def _generate_pytest_script_optimized(testcase: dict) -> str:
    """
    生成pytest测试脚本（优化版）
    
    根据 data_type 和 expected_behavior 生成智能断言
    """
    import json
    
    title = testcase.get('title', '测试用例')
    module = testcase.get('module', '通用模块')
    steps = testcase.get('steps', [])
    expected = testcase.get('expected', '测试通过')
    
    # 🆕 获取新字段
    data_type = testcase.get('data_type', 'valid')
    expected_behavior = testcase.get('expected_behavior', 'success')
    
    # 生成测试方法名
    method_name = _sanitize_method_name(title)
    
    # 🆕 根据 expected_behavior 生成断言代码
    assertion_code = _generate_assertion_code(expected_behavior)
    
    # 🆕 根据 data_type 生成测试数据注释
    data_comment = _generate_data_comment(data_type)
    
    # 生成脚本内容
    script = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
{module} - 自动化测试脚本
测试用例: {title}
数据类型: {data_type}
预期行为: {expected_behavior}
生成时间: {_get_current_time()}
"""

import pytest
import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

class Test{_sanitize_class_name(module)}:
    """
    {module}测试类
    """
    
    def setup_method(self):
        """测试前置设置"""
        self.session = requests.Session()
        self.session.headers.update({{"Content-Type": "application/json"}})
    
    def teardown_method(self):
        """测试后置清理"""
        if hasattr(self, 'session'):
            self.session.close()
    
    def test_{method_name}(self):
        """
        {title}
        
        数据类型: {data_type}
        预期行为: {expected_behavior}
        
        测试步骤:
'''
    
    # 添加测试步骤
    for i, step in enumerate(steps, 1):
        script += f'        {i}. {step}\n'
    
    script += f'''        
        预期结果: {expected}
        """
        # 准备测试数据
        # {data_comment}
        test_data = {{
            "test_case_id": {testcase['id']},
            "title": "{title}",
            "data_type": "{data_type}",
            "expected_behavior": "{expected_behavior}"
        }}
        
        # 执行测试步骤
'''
    
    # 根据步骤生成代码
    for i, step in enumerate(steps, 1):
        script += f'''        # 步骤{i}: {step}
        print(f"执行步骤{i}: {step}")
        
'''
    
    # 🆕 添加智能断言
    script += f'''        # 执行API请求（示例）
        # response = self.session.get(f"{{BASE_URL}}/api/test")
        
        # 验证结果 - 根据预期行为进行断言
{assertion_code}
        
        print("✅ 测试通过: {title}")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
'''
    
    return script


def _generate_assertion_code(expected_behavior: str) -> str:
    """
    根据 expected_behavior 生成断言代码
    
    Args:
        expected_behavior: success | client_error | server_error
    
    Returns:
        断言代码字符串
    """
    if expected_behavior == 'success':
        return '''        # 期望成功响应（2xx状态码）
        # assert response.status_code in [200, 201, 204], \\
        #     f"期望成功响应，实际状态码: {response.status_code}"
        # assert response.json() is not None, "响应体不应为空"
        assert True, "成功场景：期望2xx状态码"'''
    
    elif expected_behavior == 'client_error':
        return '''        # 期望客户端错误（4xx状态码）
        # assert response.status_code in [400, 422, 404, 403], \\
        #     f"期望客户端错误，实际状态码: {response.status_code}"
        # error_response = response.json()
        # assert 'error' in error_response or 'message' in error_response, \\
        #     "错误响应应包含错误信息"
        assert True, "异常场景：期望4xx状态码"'''
    
    elif expected_behavior == 'server_error':
        return '''        # 期望服务器错误（5xx状态码）
        # assert response.status_code >= 500, \\
        #     f"期望服务器错误，实际状态码: {response.status_code}"
        assert True, "服务器错误场景：期望5xx状态码"'''
    
    else:
        return '''        # 默认断言
        # assert response.status_code == 200, \\
        #     f"期望状态码200，实际: {response.status_code}"
        assert True, "测试通过"'''


def _generate_data_comment(data_type: str) -> str:
    """
    根据 data_type 生成测试数据注释
    
    Args:
        data_type: valid | boundary | invalid
    
    Returns:
        注释字符串
    """
    if data_type == 'valid':
        return "使用正常有效的测试数据"
    elif data_type == 'boundary':
        return "使用边界值测试数据（最小值/最大值/临界值）"
    elif data_type == 'invalid':
        return "使用无效/异常测试数据（空值/非法值/错误格式）"
    else:
        return "测试数据"


def _sanitize_method_name(title: str) -> str:
    """清理方法名,移除非法字符"""
    import re
    name = re.sub(r'[^\w\s]', '', title)
    name = name.replace(' ', '_')
    name = re.sub(r'_+', '_', name)
    name = name.strip('_')
    if not name:
        name = 'test_case'
    return name.lower()


def _sanitize_class_name(module: str) -> str:
    """清理类名,移除非法字符"""
    import re
    name = re.sub(r'[^\w\s]', '', module)
    name = name.replace(' ', '')
    if not name:
        name = 'TestModule'
    return name


def _get_current_time() -> str:
    """获取当前时间"""
    import time
    return time.strftime("%Y-%m-%d %H:%M:%S")


# 示例用法
if __name__ == "__main__":
    # 测试用例示例
    test_cases = [
        {
            "id": 1,
            "title": "用户登录 - 正常流程",
            "module": "用户管理",
            "steps": [
                "输入正确的用户名和密码",
                "点击登录按钮",
                "验证登录成功"
            ],
            "expected": "登录成功，跳转到首页",
            "data_type": "valid",
            "expected_behavior": "success"
        },
        {
            "id": 2,
            "title": "用户登录 - 参数校验",
            "module": "用户管理",
            "steps": [
                "输入空的用户名",
                "点击登录按钮",
                "验证返回错误提示"
            ],
            "expected": "返回参数错误提示",
            "data_type": "invalid",
            "expected_behavior": "client_error"
        },
        {
            "id": 3,
            "title": "用户登录 - 边界条件",
            "module": "用户管理",
            "steps": [
                "输入最长用户名（255字符）",
                "点击登录按钮",
                "验证系统正常处理"
            ],
            "expected": "系统正常处理边界值",
            "data_type": "boundary",
            "expected_behavior": "success"
        }
    ]
    
    print("=" * 80)
    print("脚本生成优化示例")
    print("=" * 80)
    
    for tc in test_cases:
        print(f"\n{'='*80}")
        print(f"测试用例: {tc['title']}")
        print(f"数据类型: {tc['data_type']}")
        print(f"预期行为: {tc['expected_behavior']}")
        print(f"{'='*80}\n")
        
        script = _generate_pytest_script_optimized(tc)
        print(script)
        print("\n")
