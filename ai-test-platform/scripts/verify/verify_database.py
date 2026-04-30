#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库验证脚本
验证数据库是否正确创建和数据是否成功迁移
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from database import (
    get_db_session,
    get_db_info,
    Project,
    Environment,
    TestCase,
    TestRun,
    Report
)


def verify_database():
    """验证数据库"""
    print("=" * 60)
    print("AI测试平台 - 数据库验证")
    print("=" * 60)
    
    # 1. 验证数据库连接
    print(f"\n📊 数据库信息:")
    db_info = get_db_info()
    print(f"   类型: {db_info['type']}")
    print(f"   URL: {db_info['url']}")
    
    # 2. 验证表和数据
    print(f"\n🔍 验证表结构和数据...")
    
    try:
        with get_db_session() as db:
            # 验证projects表
            project_count = db.query(Project).count()
            print(f"   ✓ projects表: {project_count} 条记录")
            
            # 验证environments表
            env_count = db.query(Environment).count()
            print(f"   ✓ environments表: {env_count} 条记录")
            
            # 验证test_cases表
            tc_count = db.query(TestCase).count()
            print(f"   ✓ test_cases表: {tc_count} 条记录")
            
            # 验证test_runs表
            run_count = db.query(TestRun).count()
            print(f"   ✓ test_runs表: {run_count} 条记录")
            
            # 验证reports表
            report_count = db.query(Report).count()
            print(f"   ✓ reports表: {report_count} 条记录")
            
            # 显示示例数据
            if project_count > 0:
                print(f"\n📋 示例项目:")
                projects = db.query(Project).limit(3).all()
                for proj in projects:
                    print(f"   - {proj.name} (ID: {proj.id}, 状态: {proj.status})")
            
            if tc_count > 0:
                print(f"\n📝 示例测试用例:")
                test_cases = db.query(TestCase).limit(3).all()
                for tc in test_cases:
                    print(f"   - {tc.title} (ID: {tc.id}, 优先级: {tc.priority})")
            
            print(f"\n✅ 数据库验证通过!")
            print(f"\n📊 统计:")
            print(f"   项目: {project_count}")
            print(f"   环境: {env_count}")
            print(f"   测试用例: {tc_count}")
            print(f"   测试执行: {run_count}")
            print(f"   报告: {report_count}")
            
            return True
            
    except Exception as e:
        print(f"\n❌ 数据库验证失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    success = verify_database()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
