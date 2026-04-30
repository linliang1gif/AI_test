
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
print("\n2. 检查知识库...")
knowledge_path = Path('ai-test-platform/knowledge/decision_rag.py')
if knowledge_path.exists():
    print("   ✅ 知识库模块存在")
else:
    print("   ❌ 知识库模块不存在,需要创建")

# 3. 检查 Skill
print("\n3. 检查 Skill...")
skill_path = Path('ai-test-platform/skills/test-case-generator/SKILL.md')
if skill_path.exists():
    print("   ✅ Skill 文档存在")
else:
    print("   ❌ Skill 文档不存在,需要创建")

print("\n✅ 修复完成!")
    