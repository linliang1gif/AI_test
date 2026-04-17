#!/usr/bin/env python3
"""
API自动化测试脚本生成演示
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from app.config import load_config
from app.automation.api_script_generator import ApiScriptGenerator


def demo_api_script_generation():
    """演示API自动化测试脚本生成"""
    
    print("🚀 API自动化测试脚本生成演示")
    print("=" * 50)
    
    # 1. 加载配置
    config = load_config()
    print(f"✅ 配置加载完成，使用模型: {config.model}")
    
    # 2. 准备示例测试用例数据
    sample_test_cases = [
        {
            "test_point": "验证用户登录功能",
            "title": "测试用户使用正确用户名密码登录",
            "precondition": "用户已注册，系统正常运行",
            "steps": "Step1. 打开登录页面\nStep2. 输入用户名：admin\nStep3. 输入密码：123456\nStep4. 点击登录按钮",
            "expected": "登录成功，跳转到首页，返回用户信息和token"
        },
        {
            "test_point": "验证订单创建功能", 
            "title": "测试创建新订单",
            "precondition": "用户已登录，商品库存充足",
            "steps": "Step1. 调用创建订单接口\nStep2. 传入商品ID和数量\nStep3. 提交订单信息",
            "expected": "订单创建成功，返回订单ID和状态"
        },
        {
            "test_point": "验证商品查询功能",
            "title": "测试根据ID查询商品详情", 
            "precondition": "商品数据存在",
            "steps": "Step1. 调用商品查询接口\nStep2. 传入商品ID参数\nStep3. 发送GET请求",
            "expected": "返回商品详细信息，包括名称、价格、库存等"
        }
    ]
    
    print(f"📋 准备了 {len(sample_test_cases)} 个示例测试用例")
    
    # 3. 创建API脚本生成器
    generator = ApiScriptGenerator(config)
    print("✅ API脚本生成器创建成功")
    
    # 4. 生成API测试脚本
    print("\n🧠 正在生成API自动化测试脚本...")
    
    try:
        scripts = generator.generate_scripts_by_module(sample_test_cases)
        
        if scripts:
            print(f"✅ 脚本生成成功，共生成 {len(scripts)} 个文件")
            
            # 显示生成的脚本
            for filename, content in scripts.items():
                print(f"\n📄 文件：{filename}")
                print("=" * 30)
                print(content[:500] + "..." if len(content) > 500 else content)
            
            # 保存到文件
            saved_files = generator.save_scripts_to_files(scripts)
            print(f"\n💾 脚本已保存到以下文件：")
            for file_path in saved_files:
                print(f"   - {file_path}")
            
            # 生成配置文件
            conftest_content = generator.generate_conftest_py()
            conftest_path = Path("tests") / "conftest.py"
            conftest_path.write_text(conftest_content, encoding="utf-8")
            print(f"   - {conftest_path}")
            
            requirements_content = generator.generate_requirements_txt()
            req_path = Path("tests") / "requirements.txt"
            req_path.write_text(requirements_content, encoding="utf-8")
            print(f"   - {req_path}")
            
        else:
            print("❌ 未生成任何脚本")
            
    except Exception as e:
        print(f"❌ 脚本生成失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    demo_api_script_generation()