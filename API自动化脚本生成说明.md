# API自动化测试脚本生成模块

## 🎯 功能概述

新增的API自动化测试脚本生成模块，可以根据测试用例自动生成pytest + requests的接口自动化脚本。

## 📁 模块结构

```
ai测试/
├── app/
│   └── automation/                    # 新增：自动化模块
│       ├── __init__.py
│       └── api_script_generator.py    # API脚本生成器
├── tests/                             # 生成的测试脚本目录
│   ├── conftest.py                   # pytest配置文件
│   ├── requirements.txt              # 测试依赖
│   ├── test_login.py                 # 登录模块测试
│   ├── test_order.py                 # 订单模块测试
│   └── README.md                     # 使用说明
├── demo_api_script_generation.py     # 基础演示脚本
└── demo_complete_api_workflow.py     # 完整工作流程演示
```

## 🔧 核心功能

### 1. ApiScriptGenerator 类

**主要方法：**

- `generate_api_scripts()` - 生成单个模块的API测试脚本
- `generate_scripts_by_module()` - 按模块分组生成多个脚本文件
- `save_scripts_to_files()` - 保存脚本到文件系统
- `generate_conftest_py()` - 生成pytest配置文件
- `generate_requirements_txt()` - 生成依赖文件

### 2. 输入数据格式

```python
test_case = {
    "test_point": "验证用户登录功能",
    "title": "测试用户使用正确用户名密码登录", 
    "precondition": "用户已注册，系统正常运行",
    "steps": "Step1. 调用登录接口POST /api/auth/login\nStep2. 传入用户名和密码",
    "expected": "登录成功，返回200状态码和用户token"
}
```

### 3. 生成代码格式

```python
def test_user_login():
    """测试用户使用正确用户名密码登录"""
    # 测试数据准备
    url = get_full_url("/api/auth/login")
    data = {
        "username": "admin",
        "password": "123456"
    }
    headers = DEFAULT_HEADERS
    
    # 发送请求
    response = requests.post(url, json=data, headers=headers)
    
    # 断言验证
    assert response.status_code == 200
    assert "token" in response.json()
    assert response.json()["success"] == True
```

## 🚀 使用方法

### 方法1: 基础演示
```bash
# 激活虚拟环境
.venv\Scripts\activate

# 运行基础演示
python demo_api_script_generation.py
```

### 方法2: 完整工作流程演示
```bash
# 运行完整演示（包含示例数据）
python demo_complete_api_workflow.py
```

### 方法3: 集成到现有流程
```bash
# 使用修改后的main.py（包含API脚本生成）
python main.py 需求文档.docx
```

### 方法4: 程序化调用
```python
from app.config import load_config
from app.automation.api_script_generator import ApiScriptGenerator

# 加载配置
config = load_config()

# 创建生成器
generator = ApiScriptGenerator(config)

# 生成脚本
scripts = generator.generate_scripts_by_module(test_cases)

# 保存文件
saved_files = generator.save_scripts_to_files(scripts)
```

## 📊 功能特性

### 1. 智能模块分组
- 自动从测试用例中提取模块信息
- 支持中文关键词识别（登录→login, 订单→order等）
- 按模块生成独立的测试文件

### 2. 代码生成能力
- 根据测试步骤推断API接口信息
- 自动生成合理的测试数据结构
- 添加适当的断言验证
- 生成标准的pytest测试函数

### 3. 批量处理
- 支持大量测试用例的分批处理
- 自动去重和上下文感知
- 错误恢复机制

### 4. 完整的项目结构
- 生成pytest配置文件（conftest.py）
- 生成依赖文件（requirements.txt）
- 生成使用说明（README.md）
- 提供测试基类和工具函数

## 📋 生成的文件说明

### 1. 测试脚本文件 (test_*.py)
- 包含具体的测试函数
- 遵循pytest命名规范
- 包含完整的文档字符串和注释

### 2. 配置文件 (conftest.py)
- pytest fixtures定义
- API客户端配置
- 测试基类和工具方法
- 全局配置参数

### 3. 依赖文件 (requirements.txt)
```
pytest>=7.0.0
requests>=2.28.0
pytest-html>=3.1.0
pytest-xdist>=2.5.0
allure-pytest>=2.10.0
```

### 4. 使用说明 (README.md)
- 环境准备指南
- 运行测试方法
- 报告生成说明
- 扩展建议

## 🎯 技术要求达成

### ✅ 使用 pytest + requests
- 生成标准的pytest测试函数
- 使用requests库发送HTTP请求
- 遵循pytest最佳实践

### ✅ 输入数据结构支持
- 完全支持指定的测试用例数据结构
- 智能解析测试步骤中的API信息

### ✅ 生成代码格式
- 严格按照要求的代码格式生成
- 包含URL、data、requests调用、断言

### ✅ 功能要求
- ✅ 每个测试用例生成一个pytest测试函数
- ✅ 自动生成测试文件
- ✅ 文件命名规则：test_模块名.py
- ✅ 代码写入tests/目录
- ✅ 支持批量生成

### ✅ 示例输出
- 生成 tests/test_login.py
- 生成 tests/test_order.py
- 生成 tests/test_product.py 等

## 🔄 集成到现有流程

新的完整流程：
```
需求文档 → 测试点 → 测试用例 → Excel + API自动化脚本
```

修改后的main.py已经集成了API脚本生成功能，在生成Excel后会自动生成对应的API测试脚本。

## 🎉 优势

1. **自动化程度高** - 从需求文档直接生成可执行的测试脚本
2. **智能识别** - 自动识别API接口信息和模块分组
3. **标准化输出** - 生成符合行业标准的pytest脚本
4. **完整项目结构** - 不仅生成测试代码，还包含配置和说明
5. **易于维护** - 生成的代码结构清晰，便于后续维护和扩展

这个模块将测试设计工作延伸到了自动化测试实现，大大提高了测试开发效率！