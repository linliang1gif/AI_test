"""
蓝点项目知识库快速访问工具
帮助快速查找和使用蓝点项目的代码和文档
"""
import os
from pathlib import Path
import json

# 蓝点项目路径
LANDIAN_ROOT = Path(r"D:\360Downloads\蓝点")
FRONTEND_ROOT = LANDIAN_ROOT / "recycle-front-feature-1.2.2 (1)" / "recycle-front-feature-1.2.2"
BACKEND_ROOT = LANDIAN_ROOT / "recycle-server-feature-1.2.2 (1)" / "recycle-server-feature-1.2.2"

def show_menu():
    """显示主菜单"""
    print("\n" + "=" * 60)
    print("🔍 蓝点项目知识库快速访问")
    print("=" * 60)
    print("\n选择你想查看的内容:")
    print("\n【前端相关】")
    print("  1. 前端项目结构")
    print("  2. 前端环境配置")
    print("  3. 前端源代码目录")
    print("  4. 前端组件列表")
    
    print("\n【后端相关】")
    print("  5. 后端项目结构")
    print("  6. 后端模块列表")
    print("  7. 后端配置文件")
    print("  8. 后端 API 接口")
    
    print("\n【测试相关】")
    print("  9. 测试文档列表")
    print("  10. 测试脚本列表")
    print("  11. Postman 集合")
    print("  12. API 测试数据")
    
    print("\n【快速操作】")
    print("  13. 打开前端项目目录")
    print("  14. 打开后端项目目录")
    print("  15. 查看所有文档")
    print("  16. 搜索文件")
    
    print("\n  0. 退出")
    print("=" * 60)

def list_frontend_structure():
    """列出前端项目结构"""
    print("\n📁 前端项目结构")
    print("=" * 60)
    
    if not FRONTEND_ROOT.exists():
        print("❌ 前端项目路径不存在")
        return
    
    key_dirs = ['src', 'public', 'config', 'build', 'mock', 'tests']
    
    for dir_name in key_dirs:
        dir_path = FRONTEND_ROOT / dir_name
        if dir_path.exists():
            print(f"\n📂 {dir_name}/")
            try:
                items = list(dir_path.iterdir())[:10]  # 只显示前10个
                for item in items:
                    icon = "📁" if item.is_dir() else "📄"
                    print(f"  {icon} {item.name}")
                if len(list(dir_path.iterdir())) > 10:
                    print(f"  ... 还有 {len(list(dir_path.iterdir())) - 10} 个项目")
            except Exception as e:
                print(f"  ❌ 无法读取: {e}")

def list_frontend_env():
    """列出前端环境配置"""
    print("\n⚙️ 前端环境配置")
    print("=" * 60)
    
    if not FRONTEND_ROOT.exists():
        print("❌ 前端项目路径不存在")
        return
    
    env_files = list(FRONTEND_ROOT.glob(".env*"))
    
    if env_files:
        print(f"\n找到 {len(env_files)} 个环境配置文件:\n")
        for env_file in sorted(env_files):
            env_name = env_file.name.replace('.env.', '').replace('.env', 'default')
            print(f"  📄 {env_file.name:<30} → {env_name} 环境")
    else:
        print("❌ 未找到环境配置文件")

def list_backend_structure():
    """列出后端项目结构"""
    print("\n📁 后端项目结构")
    print("=" * 60)
    
    if not BACKEND_ROOT.exists():
        print("❌ 后端项目路径不存在")
        return
    
    key_dirs = ['recycle', 'recycle-components', 'test-scripts']
    
    for dir_name in key_dirs:
        dir_path = BACKEND_ROOT / dir_name
        if dir_path.exists():
            print(f"\n📂 {dir_name}/")
            try:
                items = list(dir_path.iterdir())[:10]
                for item in items:
                    icon = "📁" if item.is_dir() else "📄"
                    print(f"  {icon} {item.name}")
                if len(list(dir_path.iterdir())) > 10:
                    print(f"  ... 还有 {len(list(dir_path.iterdir())) - 10} 个项目")
            except Exception as e:
                print(f"  ❌ 无法读取: {e}")

def list_test_docs():
    """列出测试文档"""
    print("\n📚 测试文档列表")
    print("=" * 60)
    
    if not LANDIAN_ROOT.exists():
        print("❌ 蓝点项目路径不存在")
        return
    
    # 查找所有 .md 文件
    md_files = list(LANDIAN_ROOT.glob("*.md"))
    
    if md_files:
        print(f"\n找到 {len(md_files)} 个 Markdown 文档:\n")
        for md_file in sorted(md_files):
            size = md_file.stat().st_size / 1024  # KB
            print(f"  📄 {md_file.name:<50} ({size:.1f} KB)")
    else:
        print("❌ 未找到测试文档")

def list_test_scripts():
    """列出测试脚本"""
    print("\n🧪 测试脚本列表")
    print("=" * 60)
    
    if not LANDIAN_ROOT.exists():
        print("❌ 蓝点项目路径不存在")
        return
    
    # Python 脚本
    py_files = list(LANDIAN_ROOT.glob("*.py"))
    # PowerShell 脚本
    ps1_files = list(LANDIAN_ROOT.glob("*.ps1"))
    # 批处理脚本
    bat_files = list(LANDIAN_ROOT.glob("*.bat"))
    
    if py_files:
        print(f"\n🐍 Python 脚本 ({len(py_files)} 个):")
        for py_file in sorted(py_files):
            print(f"  📄 {py_file.name}")
    
    if ps1_files:
        print(f"\n💻 PowerShell 脚本 ({len(ps1_files)} 个):")
        for ps1_file in sorted(ps1_files):
            print(f"  📄 {ps1_file.name}")
    
    if bat_files:
        print(f"\n⚙️ 批处理脚本 ({len(bat_files)} 个):")
        for bat_file in sorted(bat_files):
            print(f"  📄 {bat_file.name}")

def list_postman_collections():
    """列出 Postman 集合"""
    print("\n📮 Postman 测试集合")
    print("=" * 60)
    
    if not LANDIAN_ROOT.exists():
        print("❌ 蓝点项目路径不存在")
        return
    
    # 查找所有 Postman 和 Apifox JSON 文件
    postman_files = list(LANDIAN_ROOT.glob("Postman*.json"))
    apifox_files = list(LANDIAN_ROOT.glob("Apifox*.json"))
    api_files = [f for f in LANDIAN_ROOT.glob("*.json") 
                 if 'api' in f.name.lower() and f not in postman_files + apifox_files]
    
    if postman_files:
        print(f"\n📮 Postman 集合 ({len(postman_files)} 个):")
        for file in sorted(postman_files):
            size = file.stat().st_size / 1024
            print(f"  📄 {file.name:<50} ({size:.1f} KB)")
    
    if apifox_files:
        print(f"\n🦊 Apifox 集合 ({len(apifox_files)} 个):")
        for file in sorted(apifox_files):
            size = file.stat().st_size / 1024
            print(f"  📄 {file.name:<50} ({size:.1f} KB)")
    
    if api_files:
        print(f"\n🔌 API 定义 ({len(api_files)} 个):")
        for file in sorted(api_files):
            size = file.stat().st_size / 1024
            print(f"  📄 {file.name:<50} ({size:.1f} KB)")

def open_directory(path):
    """打开目录"""
    if path.exists():
        os.startfile(path)
        print(f"✅ 已打开目录: {path}")
    else:
        print(f"❌ 目录不存在: {path}")

def search_files(keyword):
    """搜索文件"""
    print(f"\n🔍 搜索包含 '{keyword}' 的文件")
    print("=" * 60)
    
    if not LANDIAN_ROOT.exists():
        print("❌ 蓝点项目路径不存在")
        return
    
    results = []
    
    # 搜索根目录
    for file in LANDIAN_ROOT.glob("*"):
        if file.is_file() and keyword.lower() in file.name.lower():
            results.append(file)
    
    if results:
        print(f"\n找到 {len(results)} 个匹配的文件:\n")
        for file in sorted(results):
            print(f"  📄 {file.name}")
    else:
        print(f"❌ 未找到包含 '{keyword}' 的文件")

def list_all_docs():
    """列出所有文档"""
    print("\n📚 所有文档列表")
    print("=" * 60)
    
    if not LANDIAN_ROOT.exists():
        print("❌ 蓝点项目路径不存在")
        return
    
    # 所有文档类型
    doc_patterns = ["*.md", "*.txt", "*.json"]
    all_docs = []
    
    for pattern in doc_patterns:
        all_docs.extend(LANDIAN_ROOT.glob(pattern))
    
    if all_docs:
        # 按类型分组
        md_docs = [f for f in all_docs if f.suffix == '.md']
        txt_docs = [f for f in all_docs if f.suffix == '.txt']
        json_docs = [f for f in all_docs if f.suffix == '.json']
        
        if md_docs:
            print(f"\n📝 Markdown 文档 ({len(md_docs)} 个):")
            for doc in sorted(md_docs)[:20]:  # 只显示前20个
                print(f"  📄 {doc.name}")
            if len(md_docs) > 20:
                print(f"  ... 还有 {len(md_docs) - 20} 个文档")
        
        if txt_docs:
            print(f"\n📄 文本文档 ({len(txt_docs)} 个):")
            for doc in sorted(txt_docs):
                print(f"  📄 {doc.name}")
        
        if json_docs:
            print(f"\n📋 JSON 文件 ({len(json_docs)} 个):")
            for doc in sorted(json_docs)[:15]:
                print(f"  📄 {doc.name}")
            if len(json_docs) > 15:
                print(f"  ... 还有 {len(json_docs) - 15} 个文件")
    else:
        print("❌ 未找到文档")

def main():
    """主函数"""
    while True:
        show_menu()
        
        try:
            choice = input("\n请选择 (0-16): ").strip()
            
            if choice == '0':
                print("\n👋 再见!")
                break
            elif choice == '1':
                list_frontend_structure()
            elif choice == '2':
                list_frontend_env()
            elif choice == '3':
                src_path = FRONTEND_ROOT / "src"
                open_directory(src_path)
            elif choice == '4':
                components_path = FRONTEND_ROOT / "src" / "components"
                if components_path.exists():
                    print(f"\n📦 前端组件:")
                    for item in sorted(components_path.iterdir())[:20]:
                        print(f"  📄 {item.name}")
                else:
                    print("❌ 组件目录不存在")
            elif choice == '5':
                list_backend_structure()
            elif choice == '6':
                recycle_path = BACKEND_ROOT / "recycle"
                if recycle_path.exists():
                    print(f"\n📦 后端模块:")
                    for item in sorted(recycle_path.iterdir())[:20]:
                        icon = "📁" if item.is_dir() else "📄"
                        print(f"  {icon} {item.name}")
                else:
                    print("❌ 模块目录不存在")
            elif choice == '7':
                pom_path = BACKEND_ROOT / "pom.xml"
                if pom_path.exists():
                    print(f"✅ pom.xml: {pom_path}")
                    os.startfile(pom_path)
                else:
                    print("❌ pom.xml 不存在")
            elif choice == '8':
                print("\n💡 提示: 请查看 Postman 集合了解 API 接口")
                list_postman_collections()
            elif choice == '9':
                list_test_docs()
            elif choice == '10':
                list_test_scripts()
            elif choice == '11':
                list_postman_collections()
            elif choice == '12':
                sql_files = list(LANDIAN_ROOT.glob("*.sql"))
                if sql_files:
                    print(f"\n🗄️ SQL 测试数据:")
                    for sql_file in sql_files:
                        print(f"  📄 {sql_file.name}")
                else:
                    print("❌ 未找到 SQL 文件")
            elif choice == '13':
                open_directory(FRONTEND_ROOT)
            elif choice == '14':
                open_directory(BACKEND_ROOT)
            elif choice == '15':
                list_all_docs()
            elif choice == '16':
                keyword = input("\n请输入搜索关键词: ").strip()
                if keyword:
                    search_files(keyword)
            else:
                print("❌ 无效选择，请重试")
            
            input("\n按 Enter 继续...")
            
        except KeyboardInterrupt:
            print("\n\n👋 再见!")
            break
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            input("\n按 Enter 继续...")

if __name__ == "__main__":
    print("\n🚀 启动蓝点项目知识库工具...")
    
    # 检查路径
    if not LANDIAN_ROOT.exists():
        print(f"\n⚠️  警告: 蓝点项目路径不存在")
        print(f"   路径: {LANDIAN_ROOT}")
        print(f"\n   请确认路径是否正确")
        input("\n按 Enter 退出...")
    else:
        main()
