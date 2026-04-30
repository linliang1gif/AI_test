#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 SQLite 数据库中的 Swagger 测试用例
"""

import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent / 'ai-test-platform'))

# 切换到 ai-test-platform 目录以使用正确的数据库路径
import os
os.chdir(Path(__file__).parent / 'ai-test-platform')

from database.session import get_db_session
from database.models import TestCase

def main():
    print("=" * 60)
    print("检查 SQLite 数据库中的测试用例")
    print("=" * 60)
    
    with get_db_session() as db:
        # 查询所有测试用例
        all_cases = db.query(TestCase).all()
        print(f"\n总测试用例数: {len(all_cases)}")
        
        # 查询 swagger 来源的测试用例
        swagger_cases = db.query(TestCase).filter(TestCase.source == 'swagger').all()
        print(f"Swagger 来源的测试用例数: {len(swagger_cases)}")
        
        # 按来源分组统计
        sources = {}
        for tc in all_cases:
            source = tc.source or 'null'
            sources[source] = sources.get(source, 0) + 1
        
        print(f"\n按来源分组:")
        for source, count in sources.items():
            print(f"  - {source}: {count}")
        
        # 显示前5个 swagger 用例
        if swagger_cases:
            print(f"\n前5个 Swagger 用例:")
            for tc in swagger_cases[:5]:
                print(f"  - ID: {tc.id}")
                print(f"    Title: {tc.title}")
                print(f"    Module: {tc.module}")
                print(f"    Priority: {tc.priority}")
                print(f"    Source: {tc.source}")
                print()
        
        # 显示所有用例的来源字段
        print(f"\n所有用例的来源字段:")
        for tc in all_cases[:10]:
            print(f"  - {tc.id}: source='{tc.source}'")

if __name__ == "__main__":
    main()
