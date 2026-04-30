"""
蓝点知识库使用演示
展示如何将蓝点项目作为知识库使用
"""
import json
from pathlib import Path

# 蓝点项目路径
LANDIAN_ROOT = Path(r"D:\360Downloads\蓝点")

def demo_1_list_documents():
    """演示 1: 列出所有测试文档"""
    print("\n" + "=" * 60)
    print("演示 1: 列出蓝点项目的测试文档")
    print("=" * 60)
    
    if not LANDIAN_ROOT.exists():
        print(f"❌ 蓝点项目路径不存在: {LANDIAN_ROOT}")
        return
    
    md_files = list(LANDIAN_ROOT.glob("*.md"))
    
    print(f"\n找到 {len(md_files)} 个 Markdown 文档:\n")
    
    for i, md_file in enumerate(sorted(md_files), 1):
        size = md_file.stat().st_size / 1024
        print(f"{i:2d}. {md_file.name:<50} ({size:>6.1f} KB)")
    
    print("\n💡 这些文档可以作为:")
    print("   - 测试用例设计参考")
    print("   - 测试报告模板")
    print("   - 业务需求理解")
    print("   - Bug 跟踪格式")

def demo_2_list_test_scripts():
    """演示 2: 列出所有测试脚本"""
    print("\n" + "=" * 60)
    print("演示 2: 列出蓝点项目的测试脚本")
    print("=" * 60)
    
    if not LANDIAN_ROOT.exists():
        print(f"❌ 蓝点项目路径不存在: {LANDIAN_ROOT}")
        return
    
    py_files = list(LANDIAN_ROOT.glob("test_*.py"))
    ps1_files = list(LANDIAN_ROOT.glob("*.ps1"))
    
    if py_files:
        print(f"\n🐍 Python 测试脚本 ({len(py_files)} 个):\n")
        for i, py_file in enumerate(sorted(py_files), 1):
            print(f"{i}. {py_file.name}")
    
    if ps1_files:
        print(f"\n💻 PowerShell 脚本 ({len(ps1_files)} 个):\n")
        for i, ps1_file in enumerate(sorted(ps1_files), 1):
            print(f"{i}. {ps1_file.name}")
    
    print("\n💡 这些脚本可以作为:")
    print("   - 自动化测试模板")
    print("   - API 测试参考")
    print("   - 测试流程学习")

def demo_3_list_api_collections():
    """演示 3: 列出 API 测试集合"""
    print("\n" + "=" * 60)
    print("演示 3: 列出 Postman/Apifox 测试集合")
    print("=" * 60)
    
    if not LANDIAN_ROOT.exists():
        print(f"❌ 蓝点项目路径不存在: {LANDIAN_ROOT}")
        return
    
    postman_files = list(LANDIAN_ROOT.glob("Postman*.json"))
    apifox_files = list(LANDIAN_ROOT.glob("Apifox*.json"))
    
    if postman_files:
        print(f"\n📮 Postman 集合 ({len(postman_files)} 个):\n")
        for i, file in enumerate(sorted(postman_files), 1):
            size = file.stat().st_size / 1024
            print(f"{i}. {file.name:<50} ({size:>6.1f} KB)")
    
    if apifox_files:
        print(f"\n🦊 Apifox 集合 ({len(apifox_files)} 个):\n")
        for i, file in enumerate(sorted(apifox_files), 1):
            size = file.stat().st_size / 1024
            print(f"{i}. {file.name:<50} ({size:>6.1f} KB)")
    
    print("\n💡 这些集合可以:")
    print("   - 导入 Postman 直接使用")
    print("   - 了解 API 接口定义")
    print("   - 学习 API 测试用例设计")
    print("   - 生成 AI 测试平台的测试用例")

def demo_4_analyze_api_definition():
    """演示 4: 分析 API 定义"""
    print("\n" + "=" * 60)
    print("演示 4: 分析蓝点项目的 API 定义")
    print("=" * 60)
    
    api_file = LANDIAN_ROOT / "api.json"
    
    if not api_file.exists():
        print(f"❌ API 定义文件不存在: {api_file}")
        return
    
    try:
        with open(api_file, 'r', encoding='utf-8') as f:
            api_data = json.load(f)
        
        print(f"\n✅ 成功读取 API 定义")
        print(f"   文件大小: {api_file.stat().st_size / 1024:.1f} KB")
        
        # 分析 API 结构
        if isinstance(api_data, dict):
            print(f"\n📊 API 定义结构:")
            for key in api_data.keys():
                value = api_data[key]
                if isinstance(value, list):
                    print(f"   - {key}: {len(value)} 项")
                elif isinstance(value, dict):
                    print(f"   - {key}: {len(value)} 个键")
                else:
                    print(f"   - {key}: {type(value).__name__}")
        
        print("\n💡 可以使用此 API 定义:")
        print("   - 生成 Swagger 文档")
        print("   - 自动生成测试用例")
        print("   - 导入 AI 测试平台")
        
    except Exception as e:
        print(f"❌ 读取失败: {e}")

def demo_5_integration_example():
    """演示 5: 集成到 AI 测试平台的示例"""
    print("\n" + "=" * 60)
    print("演示 5: 如何将蓝点知识库集成到 AI 测试平台")
    print("=" * 60)
    
    print("\n📝 集成步骤:\n")
    
    print("步骤 1: 导入 API 定义")
    print("---------------------------------------")
    print("""
from modules.swagger import SwaggerTestCaseGenerator

# 使用蓝点的 API 定义
generator = SwaggerTestCaseGenerator(
    r"D:\\360Downloads\\蓝点\\api.json"
)

# 生成测试用例
test_cases = generator.generate_all_testcases()
print(f"生成了 {len(test_cases)} 个测试用例")
    """)
    
    print("\n步骤 2: 参考测试场景")
    print("---------------------------------------")
    print("""
import json

# 读取蓝点的测试场景
with open(r"D:\\360Downloads\\蓝点\\分账支付测试场景.json", 'r') as f:
    scenarios = json.load(f)

# 转换为 AI 测试平台格式
from core import create_test_case

for scenario in scenarios:
    test_case = create_test_case(
        id=scenario['id'],
        title=scenario['title'],
        module=scenario['module']
    )
    """)
    
    print("\n步骤 3: 执行测试")
    print("---------------------------------------")
    print("""
from modules.executor import ExecutionEngine

# 配置执行引擎
engine = ExecutionEngine({
    'base_url': 'http://localhost:8080',
    'timeout': 30
})

# 执行测试
results = engine.execute(test_cases)

# 生成报告
from modules.report import ReportGenerator
report_gen = ReportGenerator()
report = report_gen.generate(results)
    """)
    
    print("\n💡 集成优势:")
    print("   - 复用现有的 API 定义")
    print("   - 参考真实的测试场景")
    print("   - 学习测试用例设计")
    print("   - 快速生成测试用例")

def demo_6_knowledge_statistics():
    """演示 6: 知识库统计"""
    print("\n" + "=" * 60)
    print("演示 6: 蓝点知识库统计信息")
    print("=" * 60)
    
    if not LANDIAN_ROOT.exists():
        print(f"❌ 蓝点项目路径不存在: {LANDIAN_ROOT}")
        return
    
    # 统计各类文件
    md_files = list(LANDIAN_ROOT.glob("*.md"))
    py_files = list(LANDIAN_ROOT.glob("*.py"))
    ps1_files = list(LANDIAN_ROOT.glob("*.ps1"))
    bat_files = list(LANDIAN_ROOT.glob("*.bat"))
    json_files = list(LANDIAN_ROOT.glob("*.json"))
    sql_files = list(LANDIAN_ROOT.glob("*.sql"))
    
    print("\n📊 文件统计:\n")
    print(f"   📝 Markdown 文档:     {len(md_files):3d} 个")
    print(f"   🐍 Python 脚本:       {len(py_files):3d} 个")
    print(f"   💻 PowerShell 脚本:   {len(ps1_files):3d} 个")
    print(f"   ⚙️  批处理脚本:        {len(bat_files):3d} 个")
    print(f"   📋 JSON 文件:         {len(json_files):3d} 个")
    print(f"   🗄️  SQL 文件:          {len(sql_files):3d} 个")
    
    # 计算总大小
    total_size = 0
    for file in LANDIAN_ROOT.glob("*"):
        if file.is_file():
            total_size += file.stat().st_size
    
    print(f"\n   💾 总大小: {total_size / 1024 / 1024:.2f} MB")
    
    # 检查前后端项目
    frontend_path = LANDIAN_ROOT / "recycle-front-feature-1.2.2 (1)" / "recycle-front-feature-1.2.2"
    backend_path = LANDIAN_ROOT / "recycle-server-feature-1.2.2 (1)" / "recycle-server-feature-1.2.2"
    
    print("\n📁 项目结构:\n")
    print(f"   🎨 前端项目: {'✅ 存在' if frontend_path.exists() else '❌ 不存在'}")
    print(f"   ⚙️  后端项目: {'✅ 存在' if backend_path.exists() else '❌ 不存在'}")
    
    print("\n💡 知识库价值:")
    print("   - 完整的前后端代码参考")
    print("   - 丰富的测试文档和脚本")
    print("   - 真实的业务场景案例")
    print("   - 可直接使用的 API 定义")

def main():
    """主函数"""
    print("\n🚀 蓝点知识库使用演示")
    print("=" * 60)
    print("此演示展示如何使用蓝点项目作为知识库")
    print("=" * 60)
    
    # 检查路径
    if not LANDIAN_ROOT.exists():
        print(f"\n⚠️  警告: 蓝点项目路径不存在")
        print(f"   路径: {LANDIAN_ROOT}")
        print(f"\n   请确认路径是否正确")
        return
    
    # 运行所有演示
    demos = [
        demo_1_list_documents,
        demo_2_list_test_scripts,
        demo_3_list_api_collections,
        demo_4_analyze_api_definition,
        demo_5_integration_example,
        demo_6_knowledge_statistics
    ]
    
    for demo in demos:
        try:
            demo()
            input("\n按 Enter 继续下一个演示...")
        except KeyboardInterrupt:
            print("\n\n👋 演示已取消")
            break
        except Exception as e:
            print(f"\n❌ 演示出错: {e}")
            input("\n按 Enter 继续...")
    
    print("\n" + "=" * 60)
    print("✅ 演示完成")
    print("=" * 60)
    print("\n💡 下一步:")
    print("   1. 运行 'python 使用蓝点知识库.py' 浏览知识库")
    print("   2. 查看 '蓝点项目知识库索引.md' 了解详情")
    print("   3. 查看 '蓝点知识库使用指南.md' 学习使用方法")
    print("\n")

if __name__ == "__main__":
    main()
