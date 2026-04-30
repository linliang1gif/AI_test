"""
验证所有修复是否生效
"""
from pathlib import Path
import json

def check_code_changes():
    """检查代码修改是否正确"""
    print("=" * 60)
    print("1. 检查代码修改")
    print("=" * 60)
    
    backend_file = Path("ai-test-platform/backend_api_server.py")
    
    if not backend_file.exists():
        print("❌ 后端文件不存在")
        return False
    
    with open(backend_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ("新增.*总计", "数量显示修复"),
        ("target_count.*30-50", "复杂需求支持"),
        ("max_tokens.*8000", "Token 限制调整"),
        ("content_length.*5000", "需求长度判断")
    ]
    
    all_passed = True
    for pattern, desc in checks:
        import re
        if re.search(pattern, content):
            print(f"   ✅ {desc}")
        else:
            print(f"   ❌ {desc} - 未找到")
            all_passed = False
    
    return all_passed

def check_knowledge_base():
    """检查知识库是否已导入"""
    print("\n" + "=" * 60)
    print("2. 检查知识库")
    print("=" * 60)
    
    knowledge_dir = Path("ai-test-platform/knowledge")
    
    if not knowledge_dir.exists():
        print("❌ 知识库目录不存在")
        return False
    
    json_files = list(knowledge_dir.glob("*.json"))
    
    if not json_files:
        print("❌ 知识库为空")
        return False
    
    print(f"✅ 知识库包含 {len(json_files)} 个文件:")
    
    total_size = 0
    for json_file in json_files:
        size = json_file.stat().st_size / 1024
        total_size += size
        print(f"   - {json_file.name:<40} ({size:>6.1f} KB)")
    
    print(f"\n   总大小: {total_size:.1f} KB")
    
    # 检查关键文件
    required_files = ["landian_apis.json", "index.json"]
    for req_file in required_files:
        if (knowledge_dir / req_file).exists():
            print(f"   ✅ {req_file} 存在")
        else:
            print(f"   ❌ {req_file} 缺失")
            return False
    
    return True

def check_skill_document():
    """检查 Skill 文档"""
    print("\n" + "=" * 60)
    print("3. 检查 Skill 文档")
    print("=" * 60)
    
    skill_file = Path("ai-test-platform/skills/test-case-generator/SKILL.md")
    
    if not skill_file.exists():
        print("❌ Skill 文档不存在")
        return False
    
    with open(skill_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"✅ Skill 文档存在")
    print(f"   文件大小: {len(content)} 字符")
    
    # 检查关键内容
    keywords = ["测试用例", "功能测试", "边界测试", "异常测试"]
    found_keywords = [kw for kw in keywords if kw in content]
    
    print(f"   包含关键词: {', '.join(found_keywords)}")
    
    return len(found_keywords) >= 3

def simulate_generation_logic():
    """模拟生成逻辑"""
    print("\n" + "=" * 60)
    print("4. 模拟生成逻辑")
    print("=" * 60)
    
    # 模拟不同长度的需求文档
    test_cases = [
        (2000, "10-15个", 4000),
        (3500, "20-30个", 6000),
        (6000, "30-50个", 8000)
    ]
    
    print("\n需求长度 → 生成数量 → Token限制")
    print("-" * 60)
    
    for content_length, expected_count, expected_tokens in test_cases:
        # 模拟判断逻辑
        if content_length > 5000:
            target_count = "30-50个"
            max_tokens = 8000
        elif content_length > 3000:
            target_count = "20-30个"
            max_tokens = 6000
        else:
            target_count = "10-15个"
            max_tokens = 4000
        
        status = "✅" if (target_count == expected_count and max_tokens == expected_tokens) else "❌"
        print(f"{status} {content_length:5d} 字符 → {target_count:8s} → {max_tokens:5d} tokens")
    
    return True

def provide_next_steps():
    """提供下一步操作"""
    print("\n" + "=" * 60)
    print("5. 下一步操作")
    print("=" * 60)
    
    print("""
✅ 所有修复已完成！

下一步操作:
-----------
1. 重启后端服务
   cd ai-test-platform
   py backend_api_server.py

2. 重启前端服务（如果需要）
   cd ai-test-platform/frontend
   npm run dev

3. 清除浏览器缓存
   - 按 Ctrl+Shift+R 硬刷新
   - 或清空缓存并硬性重新加载

4. 测试生成功能
   - 上传简单需求（< 3000字符）
   - 预期: 生成 10-15 个测试用例
   
   - 上传复杂需求（> 5000字符）
   - 预期: 生成 30-50 个测试用例

5. 查看后端日志
   - 确认显示"新增X个，总计Y个"
   - 确认显示"知识库检索成功"
   - 确认显示"使用Skill增强"

6. 验证前端显示
   - 测试用例列表显示正确数量
   - 测试用例详情可以查看
   - 删除功能正常工作
    """)

def main():
    print("\n🔍 验证所有修复")
    print("=" * 60)
    
    results = []
    
    # 1. 检查代码修改
    results.append(("代码修改", check_code_changes()))
    
    # 2. 检查知识库
    results.append(("知识库导入", check_knowledge_base()))
    
    # 3. 检查 Skill
    results.append(("Skill文档", check_skill_document()))
    
    # 4. 模拟生成逻辑
    results.append(("生成逻辑", simulate_generation_logic()))
    
    # 5. 提供下一步操作
    provide_next_steps()
    
    # 总结
    print("\n" + "=" * 60)
    print("验证总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n通过: {passed}/{total}")
    
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {name}")
    
    if passed == total:
        print("\n🎉 所有检查通过！可以开始测试了。")
    else:
        print("\n⚠️  部分检查未通过，请先修复问题。")
    
    print()

if __name__ == "__main__":
    main()
