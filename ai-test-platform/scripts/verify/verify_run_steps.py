#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证RunStep记录
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database import get_db, RunStep, RunCase, TestRun, RunStatusHistory
from sqlalchemy import desc


def verify_run_steps():
    """验证RunStep记录"""
    print("\n" + "=" * 60)
    print("验证RunStep记录")
    print("=" * 60 + "\n")
    
    db = next(get_db())
    
    try:
        # 1. 获取最新的TestRun
        latest_run = db.query(TestRun).order_by(desc(TestRun.created_at)).first()
        if not latest_run:
            print("❌ 没有找到TestRun记录")
            return False
        
        print(f"📊 最新TestRun: {latest_run.id}")
        print(f"   状态: {latest_run.status}")
        print(f"   总用例: {latest_run.total_cases}")
        print()
        
        # 2. 获取该Run的所有RunCase
        run_cases = db.query(RunCase).filter(RunCase.run_id == latest_run.id).all()
        print(f"📝 RunCase数量: {len(run_cases)}")
        print()
        
        # 3. 遍历每个RunCase,查看其RunStep
        total_steps = 0
        for run_case in run_cases:
            run_steps = db.query(RunStep).filter(
                RunStep.run_case_id == run_case.id
            ).order_by(RunStep.step_order).all()
            
            print(f"🔍 RunCase#{run_case.id} ({run_case.test_case_id}):")
            print(f"   状态: {run_case.status}")
            print(f"   步骤数: {len(run_steps)}")
            
            for step in run_steps:
                print(f"     Step {step.step_order}: {step.step_name}")
                print(f"       状态: {step.status}")
                if step.start_time:
                    print(f"       开始: {step.start_time.strftime('%H:%M:%S')}")
                if step.end_time:
                    print(f"       结束: {step.end_time.strftime('%H:%M:%S')}")
                if step.duration:
                    print(f"       耗时: {step.duration:.2f}秒")
                if step.error_message:
                    print(f"       错误: {step.error_message[:100]}")
                
                # 查询该step的状态历史
                step_history = db.query(RunStatusHistory).filter(
                    RunStatusHistory.entity_type == 'run_step',
                    RunStatusHistory.entity_id == str(step.id)
                ).order_by(RunStatusHistory.changed_at).all()
                
                if step_history:
                    print(f"       状态历史: {len(step_history)}条")
                    for h in step_history:
                        from_str = h.from_status or '(初始)'
                        print(f"         {from_str} → {h.to_status} | {h.changed_at.strftime('%H:%M:%S')}")
            
            total_steps += len(run_steps)
            print()
        
        print(f"✅ 总计: {len(run_cases)}个RunCase, {total_steps}个RunStep")
        print()
        
        # 4. 验证预期
        expected_steps_per_case = 2  # 准备执行 + 执行测试
        expected_total_steps = len(run_cases) * expected_steps_per_case
        
        if total_steps == expected_total_steps:
            print(f"✅ RunStep数量正确: {total_steps}/{expected_total_steps}")
            return True
        else:
            print(f"❌ RunStep数量不符: {total_steps}/{expected_total_steps}")
            return False
        
    finally:
        db.close()


if __name__ == '__main__':
    success = verify_run_steps()
    sys.exit(0 if success else 1)
