#!/usr/bin/env python3
"""
完整的API自动化测试脚本生成工作流程演示
从需求文档到可执行的pytest脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from app.config import load_config
from app.core.document_loader import read_document
from app.core.chunker import split_text
from app.test_design.testpoint_generator import TestPointGenerator
from app.test_design.testcase_generator import TestCaseGenerator
from app.automation.api_script_generator import ApiScriptGenerator


def demo_complete_api_workflow():
    """演示完整的API自动化测试工作流程"""
    
    print("=" * 70)
    print("🚀 完整API自动化测试脚本生成工作流程演示")
    print("📋 流程：需求文档 → 测试点 → 测试用例 → API自动化脚本")
    print("=" * 70)
    
    # 1. 加载配置
    print("\n📋 第1步：加载配置")
    config = load_config()
    print(f"   ✅ API密钥: {'已配置' if config.api_key else '未配置'}")
    print(f"   ✅ 模型: {config.model}")
    
    if not config.api_key:
        print("❌ 错误：未配置API密钥，请检查.env文件")
        return
    
    # 2. 准备示例数据（如果没有文档文件）
    print("\n📄 第2步：准备测试数据")
    
    # 使用示例测试用例数据进行演示
    sample_test_cases = [
        {
            "test_point": "验证用户登录功能",
            "title": "测试用户使用正确用户名密码登录",
            "precondition": "用户已注册，系统正常运行",
            "steps": "Step1. 调用登录接口POST /api/auth/login\nStep2. 传入用户名和密码\nStep3. 验证返回结果",
            "expected": "登录成功，返回200状态码和用户token"
        },
        {
            "test_point": "验证用户登录失败场景",
            "title": "测试用户使用错误密码登录",
            "precondition": "用户已注册",
            "steps": "Step1. 调用登录接口POST /api/auth/login\nStep2. 传入正确用户名和错误密码\nStep3. 验证返回结果",
            "expected": "登录失败，返回401状态码和错误信息"
        },
        {
            "test_point": "验证订单创建功能",
            "title": "测试创建新订单",
            "precondition": "用户已登录，商品库存充足",
            "steps": "Step1. 调用创建订单接口POST /api/orders\nStep2. 传入商品ID、数量等信息\nStep3. 验证订单创建结果",
            "expected": "订单创建成功，返回201状态码和订单ID"
        },
        {
            "test_point": "验证订单查询功能",
            "title": "测试根据ID查询订单详情",
            "precondition": "订单已存在",
            "steps": "Step1. 调用订单查询接口GET /api/orders/{id}\nStep2. 传入订单ID\nStep3. 验证返回结果",
            "expected": "返回200状态码和订单详细信息"
        },
        {
            "test_point": "验证商品列表查询功能",
            "title": "测试获取商品列表",
            "precondition": "系统中存在商品数据",
            "steps": "Step1. 调用商品列表接口GET /api/products\nStep2. 可选传入分页参数\nStep3. 验证返回结果",
            "expected": "返回200状态码和商品列表数据"
        },
        {
            "test_point": "验证库存更新功能",
            "title": "测试更新商品库存",
            "precondition": "商品存在，用户有权限",
            "steps": "Step1. 调用库存更新接口PUT /api/inventory/{productId}\nStep2. 传入新的库存数量\nStep3. 验证更新结果",
            "expected": "库存更新成功，返回200状态码"
        }
    ]
    
    print(f"   ✅ 准备了 {len(sample_test_cases)} 个示例测试用例")
    for i, case in enumerate(sample_test_cases, 1):
        print(f"      {i}. {case['test_point']}")
    
    # 3. 生成API自动化测试脚本
    print("\n🤖 第3步：AI生成API自动化测试脚本")
    print("   正在调用AI生成pytest + requests脚本...")
    
    try:
        api_generator = ApiScriptGenerator(config)
        
        # 按模块生成脚本
        api_scripts = api_generator.generate_scripts_by_module(sample_test_cases)
        
        if api_scripts:
            print(f"   ✅ 脚本生成成功，共生成 {len(api_scripts)} 个文件")
            
            # 显示生成的脚本预览
            for filename, content in api_scripts.items():
                print(f"\n   📄 文件：{filename}")
                print("   " + "=" * 40)
                # 显示前20行
                lines = content.split('\n')[:20]
                for line in lines:
                    print(f"   {line}")
                if len(content.split('\n')) > 20:
                    print("   ... (更多内容)")
            
            # 保存脚本到文件
            print(f"\n💾 第4步：保存脚本文件")
            saved_files = api_generator.save_scripts_to_files(api_scripts)
            print(f"   ✅ 脚本已保存到以下文件：")
            for file_path in saved_files:
                print(f"      📄 {file_path}")
            
            # 生成配置文件
            print(f"\n⚙️ 第5步：生成配置文件")
            
            # conftest.py
            conftest_content = api_generator.generate_conftest_py()
            conftest_path = Path("tests") / "conftest.py"
            conftest_path.write_text(conftest_content, encoding="utf-8")
            print(f"   ✅ pytest配置文件：{conftest_path}")
            
            # requirements.txt
            requirements_content = api_generator.generate_requirements_txt()
            req_path = Path("tests") / "requirements.txt"
            req_path.write_text(requirements_content, encoding="utf-8")
            print(f"   ✅ 依赖文件：{req_path}")
            
            # 生成运行说明
            readme_content = generate_test_readme()
            readme_path = Path("tests") / "README.md"
            readme_path.write_text(readme_content, encoding="utf-8")
            print(f"   ✅ 运行说明：{readme_path}")
            
        else:
            print("❌ 未生成任何脚本")
            return
            
    except Exception as e:
        print(f"❌ 脚本生成失败：{e}")
        import traceback
        traceback.print_exc()
        return
    
    # 6. 总结和使用指南
    print(f"\n🎉 第6步：完成总结")
    print("=" * 70)
    print("✅ API自动化测试脚本生成完成！")
    print(f"📊 统计信息:")
    print(f"   - 输入测试用例: {len(sample_test_cases)} 个")
    print(f"   - 生成脚本文件: {len(saved_files)} 个")
    print(f"   - 配置文件: 3 个 (conftest.py, requirements.txt, README.md)")
    
    print(f"\n📁 输出文件:")
    print(f"   tests/")
    for file_path in saved_files:
        print(f"   ├── {file_path.name}")
    print(f"   ├── conftest.py")
    print(f"   ├── requirements.txt")
    print(f"   └── README.md")
    
    print(f"\n🚀 使用方法:")
    print(f"   1. 安装依赖: pip install -r tests/requirements.txt")
    print(f"   2. 修改配置: 编辑 tests/conftest.py 中的BASE_URL")
    print(f"   3. 运行测试: pytest tests/ -v")
    print(f"   4. 生成报告: pytest tests/ --html=report.html")
    print("=" * 70)


def generate_test_readme() -> str:
    """生成测试运行说明文档"""
    readme_content = '''# API自动化测试脚本

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
'''
    return readme_content


if __name__ == "__main__":
    demo_complete_api_workflow()