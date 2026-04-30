"""
诊断测试用例生成问题
1. 显示生成10个但页面有20条
2. 知识库没有被调用
"""
import requests
import json

def check_backend_testcases():
    """检查后端测试用例数量"""
    print("=" * 60)
    print("1. 检查后端测试用例数量")
    print("=" * 60)
    
    try:
        response = requests.get('http://localhost:8000/api/test-cases')
        if response.status_code == 200:
            data = response.json()
            count = data.get('count', 0)
            items = data.get('data', [])
            
            print(f"✅ 后端响应成功")
            print(f"   API 返回的 count: {count}")
            print(f"   实际数据条数: {len(items)}")
            
            if count != len(items):
                print(f"\n   ⚠️  数量不一致!")
                print(f"   这可能导致前端显示混乱")
            
            # 检查数据来源
            sources = {}
            for item in items:
                source = item.get('source', 'unknown')
                sources[source] = sources.get(source, 0) + 1
            
            print(f"\n   数据来源统计:")
            for source, count in sources.items():
                print(f"   - {source}: {count} 条")
            
            return items
        else:
            print(f"❌ 后端响应失败: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return []

def analyze_generation_issue():
    """分析生成数量问题"""
    print("\n" + "=" * 60)
    print("2. 分析生成数量问题")
    print("=" * 60)
    
    print("""
问题分析:
---------
1. 提示显示"生成10个用例"
   - 这是 AI 生成函数返回的数量
   - 代码: print(f"✅ AI生成成功: {len(standardized_cases)} 个测试用例")
   
2. 页面显示20条
   - 这是后端 API 返回的总数量
   - 包含了之前生成的测试用例
   
3. 原因
   - 每次生成都会追加到 test_cases_db
   - test_cases_db.extend(final_cases)
   - 没有清空旧数据
   
解决方案:
---------
方案 1: 生成前清空旧数据
   - 在生成新用例前清空 test_cases_db
   - 适合: 每次都想要全新的测试用例
   
方案 2: 修改提示信息
   - 显示"新增10个用例,总计20个"
   - 适合: 想要累积测试用例
   
方案 3: 提供清空选项
   - 在前端添加"清空现有用例"选项
   - 让用户自己决定
    """)

def analyze_knowledge_issue():
    """分析知识库调用问题"""
    print("\n" + "=" * 60)
    print("3. 分析知识库调用问题")
    print("=" * 60)
    
    print("""
问题分析:
---------
1. 代码中有知识库调用逻辑
   - from knowledge.decision_rag import get_decision_rag
   - rag.retrieve_knowledge_v2(...)
   
2. 但可能没有实际调用
   - 可能是 try-except 捕获了异常
   - 可能是知识库模块未安装
   - 可能是知识库为空
   
3. 日志输出
   - ✅ 知识库检索成功: 找到 X 个相关API
   - ⚠️  知识库模块未安装
   - ⚠️  知识库检索失败
   
检查步骤:
---------
1. 查看后端日志
   - 查找"知识库"相关的日志
   - 确认是否有错误信息
   
2. 检查知识库模块
   - 检查 knowledge/decision_rag.py 是否存在
   - 检查知识库数据是否已导入
   
3. 检查 Skill 文档
   - 检查 skills/test-case-generator/SKILL.md 是否存在
   - 确认 Skill 内容是否正确
    """)

def check_knowledge_module():
    """检查知识库模块"""
    print("\n" + "=" * 60)
    print("4. 检查知识库模块")
    print("=" * 60)
    
    from pathlib import Path
    
    # 检查知识库模块
    knowledge_path = Path("ai-test-platform/knowledge/decision_rag.py")
    if knowledge_path.exists():
        print(f"✅ 知识库模块存在: {knowledge_path}")
    else:
        print(f"❌ 知识库模块不存在: {knowledge_path}")
    
    # 检查 Skill 文档
    skill_path = Path("ai-test-platform/skills/test-case-generator/SKILL.md")
    if skill_path.exists():
        print(f"✅ Skill 文档存在: {skill_path}")
        
        # 读取 Skill 内容
        with open(skill_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"   文件大小: {len(content)} 字符")
            print(f"   前100字符: {content[:100]}...")
    else:
        print(f"❌ Skill 文档不存在: {skill_path}")
    
    # 检查知识库数据
    knowledge_data_path = Path("ai-test-platform/knowledge")
    if knowledge_data_path.exists():
        print(f"\n✅ 知识库目录存在: {knowledge_data_path}")
        
        # 列出知识库文件
        files = list(knowledge_data_path.glob("*.json"))
        if files:
            print(f"   找到 {len(files)} 个知识库文件:")
            for file in files[:5]:
                print(f"   - {file.name}")
        else:
            print(f"   ⚠️  没有找到知识库数据文件")
    else:
        print(f"❌ 知识库目录不存在: {knowledge_data_path}")

def provide_solutions():
    """提供解决方案"""
    print("\n" + "=" * 60)
    print("5. 解决方案")
    print("=" * 60)
    
    print("""
解决方案 1: 修复数量显示问题
---------------------------
修改文件: ai-test-platform/backend_api_server.py

在生成测试用例后,修改日志输出:

# 当前代码 (第1851行):
print(f"✅ AI生成成功: {len(standardized_cases)} 个测试用例 (使用Skill增强)")

# 修改为:
new_count = len(standardized_cases)
total_count = len(test_cases_db) + new_count
print(f"✅ AI生成成功: 新增 {new_count} 个测试用例,总计 {total_count} 个 (使用Skill增强)")


解决方案 2: 添加清空选项
---------------------------
在前端添加"清空现有用例"复选框:

<input type="checkbox" id="clearExisting" />
<label for="clearExisting">清空现有测试用例</label>

在后端添加清空逻辑:

if request.get('clearExisting'):
    test_cases_db.clear()
    data_manager.set_data("test_cases", [], save=True)
    print("🗑️  已清空现有测试用例")


解决方案 3: 修复知识库调用
---------------------------
1. 确保知识库模块已安装
   cd ai-test-platform
   # 检查 knowledge/decision_rag.py 是否存在

2. 导入知识库数据
   # 如果有蓝点项目的 API 数据
   python import_knowledge.py

3. 检查后端日志
   # 查看是否有知识库相关的错误信息
   # 查找"知识库检索"相关的日志


解决方案 4: 验证 Skill 调用
---------------------------
1. 检查 Skill 文档
   cat ai-test-platform/skills/test-case-generator/SKILL.md

2. 在代码中添加调试日志
   print(f"📚 Skill 内容长度: {len(skill_guidance)}")
   print(f"📚 Skill 前100字符: {skill_guidance[:100]}")

3. 检查 AI 提示词
   print(f"🤖 System Prompt: {system_prompt[:200]}")
   print(f"🤖 User Prompt: {prompt[:200]}")
    """)

def create_fix_script():
    """创建修复脚本"""
    print("\n" + "=" * 60)
    print("6. 创建修复脚本")
    print("=" * 60)
    
    fix_script = """
# 修复脚本: fix_testcase_generation.py

import sys
sys.path.insert(0, 'ai-test-platform')

from pathlib import Path

# 1. 修复数量显示
print("1. 修复数量显示...")
backend_file = Path('ai-test-platform/backend_api_server.py')

if backend_file.exists():
    with open(backend_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找并替换
    old_line = 'print(f"✅ AI生成成功: {len(standardized_cases)} 个测试用例 (使用Skill增强)")'
    new_line = '''new_count = len(standardized_cases)
        total_count = len(test_cases_db) + new_count
        print(f"✅ AI生成成功: 新增 {new_count} 个测试用例,总计 {total_count} 个 (使用Skill增强)")'''
    
    if old_line in content:
        content = content.replace(old_line, new_line)
        with open(backend_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print("   ✅ 已修复数量显示")
    else:
        print("   ⚠️  未找到需要修复的代码")
else:
    print("   ❌ 文件不存在")

# 2. 检查知识库
print("\\n2. 检查知识库...")
knowledge_path = Path('ai-test-platform/knowledge/decision_rag.py')
if knowledge_path.exists():
    print("   ✅ 知识库模块存在")
else:
    print("   ❌ 知识库模块不存在,需要创建")

# 3. 检查 Skill
print("\\n3. 检查 Skill...")
skill_path = Path('ai-test-platform/skills/test-case-generator/SKILL.md')
if skill_path.exists():
    print("   ✅ Skill 文档存在")
else:
    print("   ❌ Skill 文档不存在,需要创建")

print("\\n✅ 修复完成!")
    """
    
    with open('fix_testcase_generation.py', 'w', encoding='utf-8') as f:
        f.write(fix_script)
    
    print("✅ 已创建修复脚本: fix_testcase_generation.py")
    print("   运行: py fix_testcase_generation.py")

def main():
    print("\n🔍 测试用例生成问题诊断")
    print("=" * 60)
    
    # 检查后端数据
    testcases = check_backend_testcases()
    
    # 分析生成数量问题
    analyze_generation_issue()
    
    # 分析知识库问题
    analyze_knowledge_issue()
    
    # 检查知识库模块
    check_knowledge_module()
    
    # 提供解决方案
    provide_solutions()
    
    # 创建修复脚本
    create_fix_script()
    
    print("\n" + "=" * 60)
    print("✅ 诊断完成")
    print("=" * 60)
    print("\n💡 下一步:")
    print("   1. 查看后端日志,确认知识库是否被调用")
    print("   2. 运行修复脚本: py fix_testcase_generation.py")
    print("   3. 重启后端服务")
    print("   4. 重新测试生成功能")
    print()

if __name__ == "__main__":
    main()
