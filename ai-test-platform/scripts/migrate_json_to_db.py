#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON数据迁移到SQLite数据库
自动备份、迁移、验证
"""

import sys
import json
import shutil
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from database import (
    get_db_session,
    Project,
    TestCase,
    TestRun,
    Report
)


class DataMigrator:
    """数据迁移器"""
    
    def __init__(self):
        self.json_file = Path("data/platform_data.json")
        self.backup_dir = Path("data/backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.stats = {
            "projects": {"total": 0, "migrated": 0, "failed": 0},
            "test_cases": {"total": 0, "migrated": 0, "failed": 0},
            "test_runs": {"total": 0, "migrated": 0, "failed": 0},
            "reports": {"total": 0, "migrated": 0, "failed": 0}
        }
    
    def backup_json(self):
        """备份JSON文件"""
        if not self.json_file.exists():
            print("⚠️  JSON文件不存在,跳过备份")
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"platform_data_{timestamp}.json"
        
        shutil.copy2(self.json_file, backup_file)
        print(f"✅ JSON文件已备份: {backup_file}")
        return backup_file
    
    def load_json_data(self):
        """加载JSON数据"""
        if not self.json_file.exists():
            print("⚠️  JSON文件不存在,返回空数据")
            return {}
        
        with open(self.json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ JSON数据加载成功")
        return data
    
    def migrate_projects(self, data, db):
        """迁移项目数据"""
        projects = data.get('projects', [])
        self.stats['projects']['total'] = len(projects)
        
        print(f"\n📦 迁移项目数据 ({len(projects)}条)...")
        
        for proj_data in projects:
            try:
                # 检查是否已存在
                existing = db.query(Project).filter(Project.id == proj_data.get('id')).first()
                if existing:
                    print(f"   ⏭️  项目 {proj_data.get('name')} 已存在,跳过")
                    continue
                
                project = Project(
                    id=proj_data.get('id'),
                    name=proj_data.get('name', ''),
                    description=proj_data.get('description', ''),
                    status=proj_data.get('status', 'active'),
                    owner=proj_data.get('owner'),
                    team=proj_data.get('team'),
                    created_at=datetime.fromisoformat(proj_data['createdAt']) if 'createdAt' in proj_data else datetime.now()
                )
                
                db.add(project)
                db.commit()
                
                self.stats['projects']['migrated'] += 1
                print(f"   ✓ {proj_data.get('name')}")
                
            except Exception as e:
                self.stats['projects']['failed'] += 1
                print(f"   ✗ {proj_data.get('name')}: {str(e)}")
                db.rollback()
    
    def migrate_test_cases(self, data, db):
        """迁移测试用例数据"""
        test_cases = data.get('test_cases', [])
        self.stats['test_cases']['total'] = len(test_cases)
        
        print(f"\n📝 迁移测试用例数据 ({len(test_cases)}条)...")
        
        for tc_data in test_cases:
            try:
                # 检查是否已存在
                existing = db.query(TestCase).filter(TestCase.id == tc_data.get('id')).first()
                if existing:
                    print(f"   ⏭️  用例 {tc_data.get('id')} 已存在,跳过")
                    continue
                
                test_case = TestCase(
                    id=tc_data.get('id', ''),
                    title=tc_data.get('title', ''),
                    module=tc_data.get('module', 'default'),
                    priority=tc_data.get('priority', 'medium'),
                    status=tc_data.get('status', 'pending'),
                    steps=tc_data.get('steps', []),
                    expected=tc_data.get('expected', ''),
                    data_type=tc_data.get('data_type', 'valid'),
                    expected_behavior=tc_data.get('expected_behavior', 'success'),
                    execution_config=tc_data.get('execution_config'),
                    assertions=tc_data.get('assertions', []),
                    tags=tc_data.get('tags', []),
                    test_point_id=tc_data.get('test_point_id'),
                    api_id=tc_data.get('api_id'),
                    dataset_id=tc_data.get('dataset_id'),
                    source=tc_data.get('source', 'manual'),
                    created_by=tc_data.get('created_by', 'system')
                )
                
                db.add(test_case)
                db.commit()
                
                self.stats['test_cases']['migrated'] += 1
                if self.stats['test_cases']['migrated'] % 10 == 0:
                    print(f"   已迁移 {self.stats['test_cases']['migrated']} 条...")
                
            except Exception as e:
                self.stats['test_cases']['failed'] += 1
                print(f"   ✗ {tc_data.get('id')}: {str(e)}")
                db.rollback()
        
        print(f"   ✓ 完成")
    
    def migrate_test_runs(self, data, db):
        """迁移测试执行数据"""
        test_runs = data.get('test_runs', [])
        self.stats['test_runs']['total'] = len(test_runs)
        
        print(f"\n🏃 迁移测试执行数据 ({len(test_runs)}条)...")
        
        for run_data in test_runs:
            try:
                # 检查是否已存在
                existing = db.query(TestRun).filter(TestRun.id == run_data.get('id')).first()
                if existing:
                    print(f"   ⏭️  执行 {run_data.get('id')} 已存在,跳过")
                    continue
                
                test_run = TestRun(
                    id=run_data.get('id', ''),
                    project_id=run_data.get('project_id'),
                    environment_id=run_data.get('environment_id'),
                    trigger_type=run_data.get('trigger_type', 'manual'),
                    status=run_data.get('status', 'completed'),
                    trace_id=run_data.get('trace_id'),
                    start_time=datetime.fromisoformat(run_data['start_time']) if 'start_time' in run_data else None,
                    end_time=datetime.fromisoformat(run_data['end_time']) if 'end_time' in run_data else None,
                    duration=run_data.get('duration'),
                    total_cases=run_data.get('total_cases', 0),
                    passed_cases=run_data.get('passed_cases', 0),
                    failed_cases=run_data.get('failed_cases', 0),
                    skipped_cases=run_data.get('skipped_cases', 0),
                    summary=run_data.get('summary'),
                    created_by=run_data.get('created_by', 'system')
                )
                
                db.add(test_run)
                db.commit()
                
                self.stats['test_runs']['migrated'] += 1
                print(f"   ✓ {run_data.get('id')}")
                
            except Exception as e:
                self.stats['test_runs']['failed'] += 1
                print(f"   ✗ {run_data.get('id')}: {str(e)}")
                db.rollback()
    
    def migrate_reports(self, data, db):
        """迁移报告数据"""
        reports = data.get('reports', [])
        self.stats['reports']['total'] = len(reports)
        
        print(f"\n📊 迁移报告数据 ({len(reports)}条)...")
        
        for report_data in reports:
            try:
                # 检查是否已存在
                existing = db.query(Report).filter(Report.id == str(report_data.get('id'))).first()
                if existing:
                    print(f"   ⏭️  报告 {report_data.get('id')} 已存在,跳过")
                    continue
                
                # 生成报告ID
                report_id = f"REPORT_{report_data.get('id')}"
                
                report = Report(
                    id=report_id,
                    run_id=report_data.get('run_id'),
                    title=report_data.get('name', ''),
                    report_type=report_data.get('type', 'comprehensive').lower().replace(' ', '_'),
                    format=report_data.get('format', 'html').lower(),
                    total_tests=report_data.get('testRuns', 0),
                    pass_rate=report_data.get('passRate', 0.0)
                )
                
                db.add(report)
                db.commit()
                
                self.stats['reports']['migrated'] += 1
                print(f"   ✓ {report_data.get('name')}")
                
            except Exception as e:
                self.stats['reports']['failed'] += 1
                print(f"   ✗ {report_data.get('name')}: {str(e)}")
                db.rollback()
    
    def print_summary(self):
        """打印迁移摘要"""
        print(f"\n" + "=" * 60)
        print("迁移摘要")
        print("=" * 60)
        
        for entity, stats in self.stats.items():
            total = stats['total']
            migrated = stats['migrated']
            failed = stats['failed']
            
            if total > 0:
                success_rate = (migrated / total) * 100
                print(f"\n{entity}:")
                print(f"   总数: {total}")
                print(f"   成功: {migrated} ({success_rate:.1f}%)")
                print(f"   失败: {failed}")
        
        total_all = sum(s['total'] for s in self.stats.values())
        migrated_all = sum(s['migrated'] for s in self.stats.values())
        
        print(f"\n总计:")
        print(f"   总数: {total_all}")
        print(f"   成功: {migrated_all}")
        print(f"   成功率: {(migrated_all/total_all*100) if total_all > 0 else 0:.1f}%")
    
    def migrate(self):
        """执行迁移"""
        print("=" * 60)
        print("AI测试平台 - 数据迁移工具")
        print("=" * 60)
        
        # 1. 备份JSON
        print(f"\n📦 步骤1: 备份JSON数据...")
        backup_file = self.backup_json()
        
        # 2. 加载JSON数据
        print(f"\n📖 步骤2: 加载JSON数据...")
        data = self.load_json_data()
        
        if not data:
            print("⚠️  没有数据需要迁移")
            return
        
        # 3. 迁移数据
        print(f"\n🔄 步骤3: 迁移数据到数据库...")
        
        try:
            with get_db_session() as db:
                self.migrate_projects(data, db)
                self.migrate_test_cases(data, db)
                self.migrate_test_runs(data, db)
                self.migrate_reports(data, db)
            
            # 4. 打印摘要
            self.print_summary()
            
            print(f"\n✅ 数据迁移完成!")
            if backup_file:
                print(f"💾 原始数据已备份至: {backup_file}")
            
        except Exception as e:
            print(f"\n❌ 迁移失败: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    """主函数"""
    migrator = DataMigrator()
    migrator.migrate()


if __name__ == "__main__":
    main()
