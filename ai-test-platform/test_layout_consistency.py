#!/usr/bin/env python3
"""
测试AI测试控制台布局一致性
验证布局是否与全局风格统一
"""

def test_layout_structure():
    """测试布局结构"""
    import re
    
    # 读取AI测试控制台文件
    with open('frontend/src/pages/AiTestConsole.jsx', 'r', encoding='utf-8') as f:
        console_content = f.read()
    
    # 读取参考页面
    with open('frontend/src/pages/Dashboard.jsx', 'r', encoding='utf-8') as f:
        dashboard_content = f.read()
    
    with open('frontend/src/pages/Projects.jsx', 'r', encoding='utf-8') as f:
        projects_content = f.read()
    
    print("✅ 测试1: 主容器样式")
    # 检查主容器使用 p-8 space-y-8
    assert 'className="p-8 space-y-8"' in console_content, "主容器应使用 p-8 space-y-8"
    print("   ✓ 主容器样式正确")
    
    print("\n✅ 测试2: Header布局")
    # 检查Header使用 flex items-center justify-between
    assert 'className="flex items-center justify-between"' in console_content, "Header应使用flex布局"
    assert 'className="space-y-1"' in console_content, "Header标题区域应使用space-y-1"
    print("   ✓ Header布局正确")
    
    print("\n✅ 测试3: 卡片样式")
    # 检查卡片使用统一样式
    card_pattern = r'className="bg-white rounded-xl.*?border border-gray-200.*?shadow-sm"'
    card_matches = re.findall(card_pattern, console_content)
    assert len(card_matches) > 0, "应该有使用统一样式的卡片"
    print(f"   ✓ 找到 {len(card_matches)} 个统一样式的卡片")
    
    print("\n✅ 测试4: 卡片标题分离")
    # 检查卡片标题使用 border-b 分隔
    title_pattern = r'className="p-6 border-b border-gray-200"'
    title_matches = re.findall(title_pattern, console_content)
    assert len(title_matches) > 0, "卡片标题应使用border-b分隔"
    print(f"   ✓ 找到 {len(title_matches)} 个使用border-b分隔的标题")
    
    print("\n✅ 测试5: 卡片内容区域")
    # 检查卡片内容使用 p-6
    content_pattern = r'<div className="p-6">'
    content_matches = re.findall(content_pattern, console_content)
    assert len(content_matches) > 0, "卡片内容应使用p-6内边距"
    print(f"   ✓ 找到 {len(content_matches)} 个使用p-6的内容区域")
    
    print("\n✅ 测试6: 响应式布局")
    # 检查使用grid布局
    assert 'grid-cols-1 lg:grid-cols-2' in console_content, "应使用响应式grid布局"
    print("   ✓ 响应式布局正确")
    
    print("\n✅ 测试7: 与Dashboard样式对比")
    # 对比关键样式类
    common_classes = [
        'p-8 space-y-8',
        'bg-white rounded-xl border border-gray-200 shadow-sm',
        'p-6 border-b border-gray-200',
        'text-lg font-semibold text-gray-900'
    ]
    
    for cls in common_classes:
        assert cls in console_content, f"缺少通用样式类: {cls}"
        assert cls in dashboard_content or cls in projects_content, f"参考页面中也应有: {cls}"
    
    print("   ✓ 与Dashboard样式一致")
    
    print("\n" + "="*60)
    print("🎉 所有布局一致性测试通过!")
    print("="*60)
    
    return True

def test_component_structure():
    """测试组件结构"""
    with open('frontend/src/pages/AiTestConsole.jsx', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n✅ 测试8: 组件结构完整性")
    
    # 检查关键组件
    components = [
        ('Header', 'AI测试控制台'),
        ('输入卡片', '📝 输入信息'),
        ('执行进度', '⚡ 执行进度'),
        ('AI决策', '🤖 AI决策'),
        ('测试策略', '📋 测试策略'),
        ('执行过程', '⚡ 执行过程'),
        ('自愈过程', '🔧 自愈过程'),
        ('最终报告', '📊 最终报告'),
        ('底部说明', '💡 使用说明')
    ]
    
    for name, text in components:
        assert text in content, f"缺少组件: {name}"
        print(f"   ✓ {name} 存在")
    
    print("\n✅ 测试9: 双模式支持")
    assert 'executionMode' in content, "应支持执行模式切换"
    assert 'decision-only' in content, "应支持仅决策模式"
    assert 'full' in content, "应支持完整流程模式"
    print("   ✓ 双模式支持正确")
    
    print("\n✅ 测试10: 无语法错误")
    # 检查常见语法问题
    assert content.count('{') == content.count('}'), "大括号应该匹配"
    assert content.count('(') == content.count(')'), "小括号应该匹配"
    print("   ✓ 括号匹配正确")
    
    return True

if __name__ == '__main__':
    try:
        test_layout_structure()
        test_component_structure()
        
        print("\n" + "="*60)
        print("✅ 所有测试通过! AI测试控制台布局已与全局统一")
        print("="*60)
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        exit(1)
