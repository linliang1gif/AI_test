"""
API自动化测试脚本生成器
根据测试用例自动生成pytest + requests的接口自动化脚本
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from openai import OpenAI

from app.config import Config

# API脚本生成的系统提示词
API_SCRIPT_SYSTEM_PROMPT = """你是一位拥有 10 年经验的Python自动化测试架构师和API测试专家。
你的专长是将测试用例转换为高质量的pytest + requests自动化测试脚本。

你的核心能力：
- 分析测试用例，识别API接口信息
- 生成标准的pytest测试函数
- 设计合理的测试数据和断言
- 编写清晰、可维护的自动化测试代码
- 遵循最佳实践和编码规范"""

# API脚本生成的提示词模板
API_SCRIPT_PROMPT_TEMPLATE = """请根据以下测试用例，生成对应的pytest + requests接口自动化测试脚本。

## 代码生成要求：

### 1. 函数命名规则
- 使用 `test_` 前缀
- 函数名要简洁明确，体现测试目标
- 使用下划线分隔单词

### 2. 代码结构
```python
def test_function_name():
    \"\"\"测试用例标题\"\"\"
    # 测试数据准备
    url = "http://api.example.com/endpoint"
    data = {{
        "key": "value"
    }}
    headers = {{
        "Content-Type": "application/json"
    }}
    
    # 发送请求
    response = requests.post(url, json=data, headers=headers)
    
    # 断言验证
    assert response.status_code == 200
    assert "expected_field" in response.json()
```

### 3. 技术要求
- 使用 pytest 框架
- 使用 requests 库发送HTTP请求
- 根据测试步骤推断API接口信息
- 生成合理的测试数据
- 添加适当的断言验证

### 4. 接口信息推断规则
- 从测试步骤中提取接口路径、请求方法、参数
- 根据业务场景推断合理的URL和数据结构
- 如果无法确定具体信息，使用占位符和注释说明

## 输出格式：
请严格按照以下 JSON 格式输出，不要输出任何其他内容：

```json
{{
  "functions": [
    {{
      "function_name": "test_function_name",
      "docstring": "测试用例标题",
      "code": "完整的测试函数代码",
      "imports": ["import requests", "import pytest"],
      "api_info": {{
        "method": "POST|GET|PUT|DELETE",
        "endpoint": "/api/endpoint",
        "description": "接口描述"
      }}
    }}
  ]
}}
```

## 注意事项：
1. 每个测试用例生成一个pytest测试函数
2. 代码要完整可执行
3. 添加必要的注释和文档字符串
4. 使用合理的变量名和数据结构
5. 断言要覆盖状态码和关键业务字段

【测试用例列表】
{test_cases}"""

# 带上下文的API脚本生成提示词
API_SCRIPT_PROMPT_WITH_CONTEXT = """请根据以下测试用例，生成pytest接口自动化测试脚本。

注意：这是第 {batch_index} 批测试用例（共 {total_batches} 批）。
{prev_context}

## 生成要求：
- 基于当前批次的测试用例生成函数
- 保持函数命名的一致性
- 避免与之前批次的函数名重复

## 输出格式：
请严格按照以下 JSON 格式输出：

```json
{{
  "functions": [
    {{
      "function_name": "test_function_name",
      "docstring": "测试用例标题",
      "code": "完整的测试函数代码",
      "imports": ["import requests", "import pytest"],
      "api_info": {{
        "method": "POST|GET|PUT|DELETE",
        "endpoint": "/api/endpoint",
        "description": "接口描述"
      }}
    }}
  ]
}}
```

【测试用例列表（第 {batch_index} 批）】
{test_cases}"""


class ApiScriptGenerator:
    """API自动化测试脚本生成器"""
    
    def __init__(self, config: Config) -> None:
        self.config = config
        self._client = OpenAI(api_key=config.api_key, base_url=config.base_url)
        self.tests_dir = Path("tests")
    
    def generate_api_scripts(
        self, 
        test_cases: List[Dict[str, str]], 
        module_name: str = "api",
        retries: int = 3, 
        delay: float = 3.0
    ) -> Dict[str, str]:
        """
        根据测试用例生成API自动化测试脚本
        
        Args:
            test_cases: 测试用例列表
            module_name: 模块名称，用于文件命名
            retries: 重试次数
            delay: 重试延迟
            
        Returns:
            生成的脚本文件字典 {文件名: 脚本内容}
        """
        if not test_cases:
            return {}
        
        # 确保tests目录存在
        self.tests_dir.mkdir(exist_ok=True)
        
        # 如果测试用例太多，分批处理
        if len(test_cases) > 8:
            return self._generate_scripts_in_batches(test_cases, module_name, retries, delay)
        
        # 单批处理
        functions = self._generate_functions(test_cases, retries, delay)
        if not functions:
            return {}
        
        # 生成脚本文件
        script_content = self._build_script_content(functions, module_name)
        filename = f"test_{module_name}.py"
        
        return {filename: script_content}
    
    def generate_scripts_by_module(
        self, 
        test_cases: List[Dict[str, str]], 
        retries: int = 3, 
        delay: float = 3.0
    ) -> Dict[str, str]:
        """
        按模块分组生成API测试脚本
        
        Args:
            test_cases: 测试用例列表
            retries: 重试次数
            delay: 重试延迟
            
        Returns:
            生成的脚本文件字典 {文件名: 脚本内容}
        """
        # 按模块分组
        modules = self._group_by_module(test_cases)
        
        all_scripts = {}
        for module_name, cases in modules.items():
            scripts = self.generate_api_scripts(cases, module_name, retries, delay)
            all_scripts.update(scripts)
        
        return all_scripts
    
    def save_scripts_to_files(self, scripts: Dict[str, str]) -> List[Path]:
        """
        将生成的脚本保存到文件
        
        Args:
            scripts: 脚本内容字典 {文件名: 内容}
            
        Returns:
            保存的文件路径列表
        """
        saved_files = []
        
        for filename, content in scripts.items():
            file_path = self.tests_dir / filename
            file_path.write_text(content, encoding="utf-8")
            saved_files.append(file_path)
        
        return saved_files
    
    def _generate_scripts_in_batches(
        self, 
        test_cases: List[Dict[str, str]], 
        module_name: str, 
        retries: int, 
        delay: float
    ) -> Dict[str, str]:
        """分批生成API测试脚本"""
        batch_size = 6
        all_functions = []
        batches = [test_cases[i:i + batch_size] for i in range(0, len(test_cases), batch_size)]
        
        for batch_idx, batch_cases in enumerate(batches, 1):
            prev_context = ""
            if all_functions:
                prev_names = [func.get("function_name", "") for func in all_functions[-3:]]
                prev_context = f"前面批次已生成的函数名：{'、'.join(prev_names)}"
            
            try:
                batch_functions = self._generate_functions_with_context(
                    batch_cases, batch_idx, len(batches), prev_context, retries, delay
                )
                all_functions.extend(batch_functions)
            except Exception as e:
                print(f"批次 {batch_idx} 生成失败: {e}")
                continue
        
        if not all_functions:
            return {}
        
        # 生成脚本文件
        script_content = self._build_script_content(all_functions, module_name)
        filename = f"test_{module_name}.py"
        
        return {filename: script_content}
    
    def _generate_functions(self, test_cases: List[Dict[str, str]], retries: int, delay: float) -> List[Dict]:
        """生成测试函数"""
        cases_text = self._format_test_cases(test_cases)
        prompt = API_SCRIPT_PROMPT_TEMPLATE.format(test_cases=cases_text)
        response = self._call_api(prompt, retries, delay)
        return self._parse_functions(response)
    
    def _generate_functions_with_context(
        self, 
        test_cases: List[Dict[str, str]], 
        batch_idx: int, 
        total_batches: int,
        prev_context: str,
        retries: int, 
        delay: float
    ) -> List[Dict]:
        """带上下文生成测试函数"""
        cases_text = self._format_test_cases(test_cases)
        prompt = API_SCRIPT_PROMPT_WITH_CONTEXT.format(
            test_cases=cases_text,
            batch_index=batch_idx,
            total_batches=total_batches,
            prev_context=prev_context
        )
        response = self._call_api(prompt, retries, delay)
        return self._parse_functions(response)
    
    def _format_test_cases(self, test_cases: List[Dict[str, str]]) -> str:
        """格式化测试用例为文本"""
        formatted = []
        for i, case in enumerate(test_cases, 1):
            formatted.append(f"""
{i}. 测试用例：
   测试点：{case.get('test_point', '')}
   标题：{case.get('title', '')}
   前置条件：{case.get('precondition', '')}
   操作步骤：{case.get('steps', '')}
   预期结果：{case.get('expected', '')}
""")
        return '\n'.join(formatted)
    
    def _call_api(self, prompt: str, retries: int, delay: float) -> str:
        """调用AI API"""
        last_error: Exception | None = None
        
        for attempt in range(retries):
            try:
                response = self._client.chat.completions.create(
                    model=self.config.model,
                    messages=[
                        {"role": "system", "content": API_SCRIPT_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=self.config.temperature,
                )
                return response.choices[0].message.content
            except Exception as exc:
                last_error = exc
                time.sleep(delay * (attempt + 1))
        
        raise RuntimeError(f"API脚本生成失败（已重试 {retries} 次）: {last_error}")
    
    def _parse_functions(self, ai_output: str) -> List[Dict]:
        """解析AI输出，提取测试函数信息"""
        try:
            data = self._extract_json(ai_output)
            if data and "functions" in data:
                return data["functions"]
        except Exception:
            pass
        
        # 如果JSON解析失败，尝试文本解析
        return self._parse_text_functions(ai_output)
    
    def _extract_json(self, text: str) -> Optional[dict]:
        """从文本中提取JSON"""
        # 尝试代码块
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass
        
        # 尝试整个文本
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass
        
        # 尝试查找JSON对象
        match = re.search(r"\{[\s\S]*\"functions\"[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        
        return None
    
    def _parse_text_functions(self, text: str) -> List[Dict]:
        """从纯文本中解析测试函数（备用方案）"""
        functions = []
        
        # 查找函数定义
        function_pattern = r'def\s+(test_\w+)\s*\([^)]*\):'
        matches = re.finditer(function_pattern, text)
        
        for match in matches:
            func_name = match.group(1)
            start_pos = match.start()
            
            # 提取函数代码（简单实现）
            lines = text[start_pos:].split('\n')
            func_lines = []
            indent_level = None
            
            for line in lines:
                if line.strip().startswith('def '):
                    func_lines.append(line)
                    indent_level = len(line) - len(line.lstrip())
                elif indent_level is not None:
                    current_indent = len(line) - len(line.lstrip())
                    if line.strip() and current_indent <= indent_level and not line.startswith(' '):
                        break
                    func_lines.append(line)
            
            if func_lines:
                functions.append({
                    "function_name": func_name,
                    "docstring": f"测试函数：{func_name}",
                    "code": '\n'.join(func_lines),
                    "imports": ["import requests", "import pytest"],
                    "api_info": {
                        "method": "POST",
                        "endpoint": "/api/unknown",
                        "description": "自动生成的测试函数"
                    }
                })
        
        return functions
    
    def _build_script_content(self, functions: List[Dict], module_name: str) -> str:
        """构建完整的脚本文件内容"""
        # 收集所有导入
        all_imports = set()
        for func in functions:
            imports = func.get("imports", [])
            all_imports.update(imports)
        
        # 构建文件头部
        header = f'''"""
{module_name}模块API自动化测试脚本
自动生成于：{time.strftime("%Y-%m-%d %H:%M:%S")}
"""
'''
        
        # 添加导入语句
        imports_section = '\n'.join(sorted(all_imports)) + '\n\n'
        
        # 添加配置和工具函数
        config_section = '''
# 测试配置
BASE_URL = "http://localhost:8080"  # 请根据实际情况修改
DEFAULT_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def get_full_url(endpoint: str) -> str:
    """获取完整的API URL"""
    return f"{BASE_URL.rstrip('/')}{endpoint}"

'''
        
        # 添加测试函数
        functions_section = '\n\n'.join(func.get("code", "") for func in functions)
        
        return header + imports_section + config_section + functions_section
    
    def _group_by_module(self, test_cases: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
        """按模块分组测试用例"""
        modules = {}
        
        for case in test_cases:
            # 尝试从测试点或标题中提取模块名
            module_name = self._extract_module_name(case)
            
            if module_name not in modules:
                modules[module_name] = []
            modules[module_name].append(case)
        
        return modules
    
    def _extract_module_name(self, case: Dict[str, str]) -> str:
        """从测试用例中提取模块名"""
        # 优先从测试点提取
        test_point = case.get("test_point", "")
        title = case.get("title", "")
        
        # 常见的模块关键词
        module_keywords = {
            "登录": "login",
            "注册": "register", 
            "用户": "user",
            "订单": "order",
            "商品": "product",
            "支付": "payment",
            "购物车": "cart",
            "库存": "inventory",
            "仓库": "warehouse",
            "入库": "stockin",
            "出库": "stockout",
            "采购": "purchase",
            "销售": "sales",
            "财务": "finance",
            "报表": "report"
        }
        
        # 在测试点和标题中查找关键词
        text = (test_point + " " + title).lower()
        for keyword, module in module_keywords.items():
            if keyword in text:
                return module
        
        # 如果没有找到，使用默认模块名
        return "api"
    
    def generate_conftest_py(self) -> str:
        """生成pytest配置文件conftest.py"""
        conftest_content = '''"""
pytest配置文件
"""
import pytest
import requests
from typing import Generator


@pytest.fixture(scope="session")
def api_client() -> Generator[requests.Session, None, None]:
    """API客户端fixture"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json"
    })
    yield session
    session.close()


@pytest.fixture(scope="session")
def base_url() -> str:
    """基础URL fixture"""
    return "http://localhost:8080"  # 请根据实际情况修改


@pytest.fixture
def auth_headers() -> dict:
    """认证头部fixture"""
    return {
        "Authorization": "Bearer your_token_here"  # 请根据实际情况修改
    }


class ApiTestBase:
    """API测试基类"""
    
    def assert_success_response(self, response: requests.Response):
        """断言成功响应"""
        assert response.status_code == 200
        assert response.headers.get("content-type", "").startswith("application/json")
    
    def assert_error_response(self, response: requests.Response, expected_code: int = 400):
        """断言错误响应"""
        assert response.status_code == expected_code
        data = response.json()
        assert "error" in data or "message" in data
'''
        return conftest_content
    
    def generate_requirements_txt(self) -> str:
        """生成requirements.txt文件"""
        requirements = '''# API自动化测试依赖
pytest>=7.0.0
requests>=2.28.0
pytest-html>=3.1.0
pytest-xdist>=2.5.0
allure-pytest>=2.10.0
'''
        return requirements