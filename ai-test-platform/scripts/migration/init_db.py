#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
一键创建所有表结构
"""

import sys
import argparse
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from database import init_db, get_db_info


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='初始化AI测试平台数据库')
    parser.add_argument('--force', '-f', action='store_true', help='强制初始化,不询问确认')
    parser.add_argument('--yes', '-y', action='store_true', help='自动确认所有提示')
    args = parser.parse_args()
    
    print("=" * 60)
    print("AI测试平台 - 数据库初始化")
    print("=" * 60)
    
    # 显示数据库信息
    db_info = get_db_info()
    print(f"\n📊 数据库信息:")
    print(f"   类型: {db_info['type']}")
    print(f"   URL: {db_info['url']}")
    
    # 确认操作(除非使用--force或--yes)
    if not (args.force or args.yes):
        print(f"\n⚠️  即将初始化数据库,创建所有表结构")
        confirm = input("   是否继续? (y/n): ")
        
        if confirm.lower() != 'y':
            print("❌ 操作已取消")
            return
    
    # 初始化数据库
    print(f"\n🔧 正在初始化数据库...")
    success = init_db()
    
    if success:
        print(f"\n✅ 数据库初始化完成!")
        print(f"\n📋 已创建的表:")
        tables = [
            "projects - 项目表",
            "environments - 环境表",
            "auth_profiles - 鉴权配置表",
            "api_specs - API规范表",
            "test_cases - 测试用例表",
            "test_runs - 测试执行表",
            "run_cases - 用例执行记录表",
            "run_steps - 执行步骤表",
            "run_status_history - 执行状态历史表(P0-3新增)",
            "reports - 测试报告表",
            "healing_records - 修复记录表",
            "system_settings - 系统设置表"
        ]
        for table in tables:
            print(f"   ✓ {table}")
        
        print(f"\n🎉 数据库已就绪,可以开始使用!")
        print(f"\n💡 下一步:")
        print(f"   1. 运行 python migrate_json_to_db.py 迁移现有数据")
        print(f"   2. 启动后端服务 python backend_api_server.py")
    else:
        print(f"\n❌ 数据库初始化失败,请检查错误信息")
        sys.exit(1)


if __name__ == "__main__":
    main()
