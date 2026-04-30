#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能修复测试用例标题
提取关键信息,生成简洁明了的标题
"""

import requests
import re

BASE_URL = "http://localhost:8000"

def extract_key_info(text):
    """从长文本中提取关键信息"""
    # 移除序号前缀
    text = re.sub(r'^\d+[\.\、]\s*', '', text)
    
    # 移除特殊符号
    text = text.replace('【', '').replace('】', '')
    
    # 提取第一句话或第一个逗号前的内容
    for sep in ['。', '，', ',', '；', ';']:
        if sep in text:
            text = text.split(sep)[0]
            break
    
    # 限制长度
    if len(text) > 30:
        text = text[:27] + '...'
    
    return text.strip()

def generate_smart_title(old_title, module='', case_id=''):
    """生成智能标题"""
    # 分离后缀
    suffixes = [' - 正常流程', ' - 参数校验', ' - 权限控制', ' - 边界条件']
    suffix = ''
    title = old_title
    
    for s in suffixes:
        if title.endswith(s):
            suffix = s
            title = title[:-len(s)].strip()
            break
    
    # 提取关键信息
    key_info = extract_key_info(title)
    
    # 如果提取后太短,使用模块名
    if len(key_info) < 5 and module:
        key_info = module
    
    # 如果还是太短,使用ID
    if len(key_info) < 3:
        key_info = f"测试用例 {case_id}"
    
    # 组合标题
    new_title = key_info + suffix
    
    return new_title

def main():
    print("="*60)
    print("  智能修复测试用例标题")
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
    
    # 2. 智能修复标题
    print("\n2. 智能修复标题...")
    fixed_count = 0
    
    for case in cases:
        old_title = case.get('title', '')
        case_id = case.get('id', 'unknown')
        module = case.get('module', '')
        
        # 生成新标题
        new_title = generate_smart_title(old_title, module, case_id)
        
        # 如果标题有变化
        if new_title != old_title:
            case['title'] = new_title
            fixed_count += 1
            
            if fixed_count <= 10:  # 只显示前10个
                print(f"\n   ✅ {case_id}")
                print(f"      旧: {old_title}")
                print(f"      新: {new_title}")
    
    print(f"\n   共修复 {fixed_count} 个标题")
    
    # 3. 保存修复后的数据
    print("\n3. 保存修复...")
    try:
        from pathlib import Path
        import sys
        
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))
        sys.path.insert(0, str(project_root / 'ai-test-platform'))
        
        from utils.data_manager import get_data_manager
        
        data_manager = get_data_manager()
        data_manager.set_data("test_cases", cases, save=True)
        
        print("   ✅ 保存成功")
        
    except Exception as e:
        print(f"   ⚠️  保存失败: {e}")
    
    # 4. 验证修复
    print("\n4. 验证修复...")
    print("\n   修复后的标题示例:")
    for i, case in enumerate(cases[:10], 1):
        print(f"   {i}. {case.get('title', 'N/A')}")
    
    print("\n" + "="*60)
    print("  修复完成!")
    print("  提示: 刷新前端页面查看效果")
    print("="*60)

if __name__ == "__main__":
    main()
