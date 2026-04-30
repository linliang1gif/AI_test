#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复测试用例标题
将过长或格式不正确的标题修复为简洁明了的格式
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def fix_title(old_title, case_id):
    """修复标题格式"""
    # 移除序号前缀 (如 "5. ", "6. ")
    title = old_title
    
    # 如果标题以数字开头,移除
    import re
    title = re.sub(r'^\d+\.\s*', '', title)
    
    # 如果标题太长,截取主要部分
    if len(title) > 100:
        # 尝试在第一个句号或逗号处截断
        for sep in ['。', '，', ',', '-']:
            if sep in title:
                title = title.split(sep)[0]
                break
    
    # 如果标题包含 " - 正常流程" 等后缀,保留
    suffixes = [' - 正常流程', ' - 参数校验', ' - 权限控制', ' - 边界条件']
    suffix = ''
    for s in suffixes:
        if title.endswith(s):
            suffix = s
            title = title[:-len(s)]
            break
    
    # 限制标题长度
    if len(title) > 50:
        title = title[:47] + '...'
    
    # 重新添加后缀
    title = title + suffix
    
    # 如果标题为空或太短,使用默认格式
    if len(title.strip()) < 3:
        title = f"测试用例 {case_id}"
    
    return title

def main():
    print("="*60)
    print("  修复测试用例标题")
    print("="*60)
    
    # 1. 获取所有测试用例
    print("\n1. 获取测试用例...")
    try:
        r = requests.get(f"{BASE_URL}/api/test-cases")
        data = r.json()
        cases = data.get('data', [])
        print(f"   找到 {len(cases)} 个测试用例")
    except Exception as e:
        print(f"   ❌ 获取失败: {e}")
        return
    
    # 2. 修复标题
    print("\n2. 修复标题...")
    fixed_count = 0
    
    for case in cases:
        old_title = case.get('title', '')
        case_id = case.get('id', 'unknown')
        
        # 检查是否需要修复
        needs_fix = (
            len(old_title) > 60 or  # 标题太长
            old_title.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')) or  # 以数字开头
            '...' in old_title  # 已被截断
        )
        
        if needs_fix:
            new_title = fix_title(old_title, case_id)
            case['title'] = new_title
            fixed_count += 1
            print(f"   ✅ {case_id}")
            print(f"      旧: {old_title[:50]}...")
            print(f"      新: {new_title}")
    
    print(f"\n   共修复 {fixed_count} 个标题")
    
    # 3. 保存修复后的数据
    print("\n3. 保存修复...")
    try:
        # 注意: 这里需要后端提供批量更新API
        # 目前只能通过数据管理器直接修改
        from pathlib import Path
        import sys
        
        # 添加项目路径
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))
        sys.path.insert(0, str(project_root / 'ai-test-platform'))
        
        from utils.data_manager import get_data_manager
        
        data_manager = get_data_manager()
        data_manager.set_data("test_cases", cases, save=True)
        
        print("   ✅ 保存成功")
        
    except Exception as e:
        print(f"   ⚠️  保存失败: {e}")
        print("   提示: 需要重启后端服务才能看到更改")
    
    # 4. 验证修复
    print("\n4. 验证修复...")
    try:
        r = requests.get(f"{BASE_URL}/api/test-cases")
        data = r.json()
        cases = data.get('data', [])
        
        print("\n   修复后的标题示例:")
        for i, case in enumerate(cases[:5], 1):
            print(f"   {i}. {case.get('title', 'N/A')}")
        
    except Exception as e:
        print(f"   ⚠️  验证失败: {e}")
    
    print("\n" + "="*60)
    print("  修复完成!")
    print("="*60)

if __name__ == "__main__":
    main()
