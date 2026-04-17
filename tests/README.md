# API自动化测试脚本

## 概述
本目录包含自动生成的API接口自动化测试脚本，使用pytest + requests框架。

## 文件说明
- `test_*.py` - 具体的测试脚本文件
- `conftest.py` - pytest配置文件，包含fixtures和基础配置
- `requirements.txt` - 项目依赖
- `README.md` - 本说明文件

## 环境准备

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置测试环境
编辑 `conftest.py` 文件，修改以下配置：
- `BASE_URL`: API服务的基础URL
- `auth_headers`: 认证信息（如果需要）

## 运行测试

### 基础运行
```bash
# 运行所有测试
pytest tests/ -v

# 运行特定模块
pytest tests/test_login.py -v

# 运行特定测试函数
pytest tests/test_login.py::test_user_login -v
```

### 生成报告
```bash
# 生成HTML报告
pytest tests/ --html=report.html --self-contained-html

# 生成Allure报告
pytest tests/ --alluredir=allure-results
allure serve allure-results
```

### 并行执行
```bash
# 使用多进程并行执行
pytest tests/ -n 4
```

## 测试数据管理
- 测试数据建议放在单独的数据文件中
- 可以使用pytest的参数化功能进行数据驱动测试
- 敏感信息（如密码、token）建议使用环境变量

## 注意事项
1. 运行测试前确保API服务正常运行
2. 根据实际API接口调整URL和参数
3. 添加适当的测试数据清理逻辑
4. 考虑测试的幂等性，避免重复执行产生副作用

## 扩展建议
- 添加数据库验证
- 集成CI/CD流水线
- 添加性能测试
- 实现测试数据的自动准备和清理
