#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Test Platform - API自动化脚本生成器

根据接口测试用例生成pytest自动化测试脚本。
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from ai.ai_client import get_ai_client
from ai.prompt_library import PromptLibrary
from config.config import get_config

class ApiScriptGenerator:
    """API自动化脚本生成器"""
    
    def __init__(self):
        self.config = get_config()
        self.ai_client = get_ai_client()
        self.prompt_lib = PromptLibrary()
    
    def generate_api_scripts(self, api_testcases: List[Dict[str, Any]]) -> Dict[str, str]:
        """生成API自动化脚本"""
        scripts = {}
        
        # 按模块分组测试用例
        grouped_testcases = self._group_testcases_by_module(api_testcases)
        
        for module_name, testcases in grouped_testcases.items():
            try:
                script_content = self._generate_module_script(module_name, testcases)
                scripts[f"test_{module_name.lower().replace(' ', '_')}.py"] = script_content
            except Exception as e:
                print(f"为模块 {module_name} 生成脚本失败: {str(e)}")
                # 使用默认脚本
                scripts[f"test_{module_name.lower().replace(' ', '_')}.py"] = self._get_default_script(module_name, testcases)
        
        # 生成配置文件
        scripts['conftest.py'] = self._generate_conftest()
        scripts['requirements.txt'] = self._generate_requirements()
        
        # 保存脚本文件
        self._save_scripts(scripts)
        
        return scripts
    
    def _group_testcases_by_module(self, api_testcases: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """按模块分组测试用例"""
        grouped = {}
        
        for testcase in api_testcases:
            # 从API名称或标题中提取模块名
            module_name = self._extract_module_name(testcase)
            
            if module_name not in grouped:
                grouped[module_name] = []
            
            grouped[module_name].append(testcase)
        
        return grouped
    
    def _extract_module_name(self, testcase: Dict[str, Any]) -> str:
        """从测试用例中提取模块名"""
        api_name = testcase.get('api_name', '')
        title = testcase.get('title', '')
        
        # 常见模块关键词
        module_keywords = {
            'user': '用户管理',
            'login': '用户管理', 
            'register': '用户管理',
            'profile': '用户管理',
            'order': '订单管理',
            'product': '商品管理',
            'payment': '支付管理',
            'admin': '系统管理'
        }
        
        text = f"{api_name} {title}".lower()
        
        for keyword, module in module_keywords.items():
            if keyword in text:
                return module
        
        return '通用模块'
    
    def _generate_module_script(self, module_name: str, testcases: List[Dict[str, Any]]) -> str:
        """为单个模块生成脚本"""
        # 准备测试用例信息
        testcases_info = self._format_testcases_info(testcases)
        
        # 生成脚本prompt
        prompt = self.prompt_lib.get_automation_script_prompt(testcases_info)
        system_prompt = self.prompt_lib.get_system_prompt()
        
        # 调用AI生成脚本
        script_content = self.ai_client.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.2
        )
        
        # 清理和格式化脚本
        formatted_script = self._format_script_content(script_content, module_name, testcases)
        
        return formatted_script
    
    def _format_testcases_info(self, testcases: List[Dict[str, Any]]) -> str:
        """格式化测试用例信息"""
        info_lines = []
        
        for testcase in testcases:
            info_lines.append(f"测试用例: {testcase['title']}")
            info_lines.append(f"  API: {testcase['method']} {testcase['url']}")
            info_lines.append(f"  请求数据: {json.dumps(testcase['request_data'], ensure_ascii=False)}")
            info_lines.append(f"  预期状态码: {testcase['expected_status']}")
            info_lines.append(f"  预期响应: {json.dumps(testcase['expected_response'], ensure_ascii=False)}")
            info_lines.append("")
        
        return "\n".join(info_lines)
    
    def _format_script_content(self, script_content: str, module_name: str, testcases: List[Dict[str, Any]]) -> str:
        """格式化脚本内容"""
        # 提取代码块
        if "```python" in script_content:
            start = script_content.find("```python") + 9
            end = script_content.find("```", start)
            if end != -1:
                script_content = script_content[start:end].strip()
        
        # 如果AI生成的脚本不完整，使用模板生成
        if len(script_content) < 200 or "import" not in script_content:
            script_content = self._generate_script_template(module_name, testcases)
        
        return script_content
    
    def _generate_script_template(self, module_name: str, testcases: List[Dict[str, Any]]) -> str:
        """生成脚本模板"""
        template = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
{module_name} - API自动化测试脚本
自动生成时间: {self._get_current_time()}
"""

import pytest
import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

class Test{module_name.replace(" ", "")}:
    """
    {module_name}测试类
    """
    
    def setup_method(self):
        """测试前置设置"""
        self.session = requests.Session()
        self.session.headers.update({{"Content-Type": "application/json"}})
    
    def teardown_method(self):
        """测试后置清理"""
        if hasattr(self, 'session'):
            self.session.close()
'''
        
        # 为每个测试用例生成测试方法
        for i, testcase in enumerate(testcases):
            method_name = self._generate_method_name(testcase, i)
            method_code = self._generate_test_method(testcase, method_name)
            template += "\n" + method_code
        
        return template
    
    def _generate_method_name(self, testcase: Dict[str, Any], index: int) -> str:
        """生成测试方法名"""
        title = testcase.get('title', f'test_{index}')
        
        # 提取关键词
        keywords = []
        if '登录' in title or 'login' in title.lower():
            keywords.append('login')
        elif '注册' in title or 'register' in title.lower():
            keywords.append('register')
        elif '查询' in title or 'get' in title.lower():
            keywords.append('get')
        elif '创建' in title or 'create' in title.lower():
            keywords.append('create')
        elif '更新' in title or 'update' in title.lower():
            keywords.append('update')
        elif '删除' in title or 'delete' in title.lower():
            keywords.append('delete')
        else:
            keywords.append(f'case_{index}')
        
        return f"test_{'_'.join(keywords)}"
    
    def _generate_test_method(self, testcase: Dict[str, Any], method_name: str) -> str:
        """生成测试方法"""
        method_code = f'''
    def {method_name}(self):
        """
        {testcase['title']}
        """
        # 准备测试数据
        url = BASE_URL + "{testcase['url']}"
        data = {json.dumps(testcase['request_data'], ensure_ascii=False, indent=8)}
        
        # 发送请求
        response = self.session.{testcase['method'].lower()}(url, json=data)
        
        # 验证响应
        assert response.status_code == {testcase['expected_status']}, f"期望状态码 {testcase['expected_status']}, 实际 {{response.status_code}}"
        
        # 验证响应内容
        response_data = response.json()
        expected_data = {json.dumps(testcase['expected_response'], ensure_ascii=False, indent=8)}
        
        # 基本字段验证
        for key, expected_value in expected_data.items():
            assert key in response_data, f"响应中缺少字段: {{key}}"
            if expected_value is not None:
                assert response_data[key] == expected_value, f"字段 {{key}} 值不匹配"
        
        print(f"✅ {testcase['title']} - 测试通过")
'''
        
        return method_code
    
    def _get_default_script(self, module_name: str, testcases: List[Dict[str, Any]]) -> str:
        """获取默认脚本"""
        return self._generate_script_template(module_name, testcases)
    
    def _generate_conftest(self) -> str:
        """生成pytest配置文件"""
        return '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
pytest配置文件
"""

import pytest
import requests
from typing import Generator

@pytest.fixture(scope="session")
def api_client() -> Generator[requests.Session, None, None]:
    """API客户端fixture"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    
    yield session
    
    session.close()

@pytest.fixture(scope="function")
def test_data():
    """测试数据fixture"""
    return {
        "test_user": {
            "username": "testuser",
            "password": "password123",
            "email": "test@example.com"
        },
        "test_product": {
            "name": "测试商品",
            "price": 99.99,
            "category": "测试分类"
        }
    }

def pytest_configure(config):
    """pytest配置"""
    config.addinivalue_line(
        "markers", "smoke: 冒烟测试标记"
    )
    config.addinivalue_line(
        "markers", "regression: 回归测试标记"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试标记"
    )

def pytest_collection_modifyitems(config, items):
    """修改测试项配置"""
    for item in items:
        # 为所有测试添加默认标记
        if "test_login" in item.name:
            item.add_marker(pytest.mark.smoke)
        elif "test_register" in item.name:
            item.add_marker(pytest.mark.smoke)
'''
    
    def _generate_requirements(self) -> str:
        """生成依赖文件"""
        return '''# API自动化测试依赖包
pytest==7.4.3
pytest-html==4.1.1
pytest-json-report==1.5.0
requests==2.31.0
jsonschema==4.20.0
allure-pytest==2.13.2
'''
    
    def _save_scripts(self, scripts: Dict[str, str]) -> None:
        """保存脚本文件"""
        tests_dir = self.config.paths.tests_dir
        tests_dir.mkdir(parents=True, exist_ok=True)
        
        for filename, content in scripts.items():
            file_path = tests_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"📝 已生成脚本文件: {file_path}")
    
    def _get_current_time(self) -> str:
        """获取当前时间"""
        import datetime
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def generate_script_summary(self, scripts: Dict[str, str]) -> Dict[str, Any]:
        """生成脚本摘要"""
        total_files = len(scripts)
        test_files = len([f for f in scripts.keys() if f.startswith('test_')])
        config_files = len([f for f in scripts.keys() if f in ['conftest.py', 'requirements.txt']])
        
        # 统计测试方法数量
        total_methods = 0
        for filename, content in scripts.items():
            if filename.startswith('test_'):
                total_methods += content.count('def test_')
        
        return {
            'total_files': total_files,
            'test_files': test_files,
            'config_files': config_files,
            'total_test_methods': total_methods,
            'average_methods_per_file': total_methods / max(test_files, 1),
            'files_generated': list(scripts.keys())
        }