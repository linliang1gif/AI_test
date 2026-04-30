#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证可观测性 - 查看请求/响应快照
"""

import sys
import json
from pathlib import Path
from sqlalchemy import desc

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database import get_db, TestRun, RunCase, RunStep


def verify_observability():
    """验证可观测性"""
    print("\n" + "=" * 70)
    print("P0-4 可观测性验证")
    print("=" * 70 + "\n")
    
    db = next(get_db())
    
    try:
        # 获取最新的TestRun
        latest_run = db.query(TestRun).order_by(desc(TestRun.created_at)).first()
        if not latest_run:
            print("❌ 没有找到TestRun记录")
            return False
        
        print(f"📊 TestRun: {latest_run.id}")
        print(f"   Trace ID: {latest_run.trace_id}")
        print(f"   状态: {latest_run.status}")
        print(f"   统计: {latest_run.passed_cases}通过 / {latest_run.failed_cases}失败 / {latest_run.total_cases}总计")
        print()
        
        # 获取所有RunCase
        run_cases = db.query(RunCase).filter(RunCase.run_id == latest_run.id).all()
        
        for run_case in run_cases:
            print(f"🔍 RunCase#{run_case.id}: {run_case.test_case_id}")
            print(f"   状态: {run_case.status}")
            print(f"   耗时: {run_case.duration:.2f}秒" if run_case.duration else "   耗时: N/A")
            
            if run_case.error_message:
                print(f"   错误: {run_case.error_message[:100]}")
            
            # 获取RunStep
            run_steps = db.query(RunStep).filter(
                RunStep.run_case_id == run_case.id
            ).order_by(RunStep.step_order).all()
            
            for step in run_steps:
                print(f"\n   Step {step.step_order}: {step.step_name}")
                print(f"     状态: {step.status}")
                print(f"     耗时: {step.duration:.2f}秒" if step.duration else "     耗时: N/A")
                
                # 显示请求快照
                if step.input_snapshot:
                    print(f"\n     📤 请求快照:")
                    snapshot = step.input_snapshot
                    print(f"       Method: {snapshot.get('method')}")
                    print(f"       URL: {snapshot.get('url')}")
                    if snapshot.get('headers'):
                        print(f"       Headers:")
                        for k, v in snapshot.get('headers', {}).items():
                            print(f"         {k}: {v}")
                    if snapshot.get('params'):
                        print(f"       Params: {snapshot.get('params')}")
                    if snapshot.get('json'):
                        print(f"       JSON: {json.dumps(snapshot.get('json'), ensure_ascii=False)}")
                
                # 显示响应快照
                if step.output_snapshot:
                    print(f"\n     📥 响应快照:")
                    snapshot = step.output_snapshot
                    print(f"       Status Code: {snapshot.get('status_code')}")
                    print(f"       Response Time: {snapshot.get('response_time'):.3f}秒" if snapshot.get('response_time') else "       Response Time: N/A")
                    if snapshot.get('headers'):
                        print(f"       Headers: {len(snapshot.get('headers'))}个")
                    if snapshot.get('body'):
                        body = snapshot.get('body')
                        if isinstance(body, dict):
                            body_str = json.dumps(body, ensure_ascii=False, indent=2)
                            if len(body_str) > 300:
                                print(f"       Body: {body_str[:300]}...")
                            else:
                                print(f"       Body: {body_str}")
                        else:
                            body_str = str(body)
                            if len(body_str) > 300:
                                print(f"       Body: {body_str[:300]}...")
                            else:
                                print(f"       Body: {body_str}")
                
                if step.error_message:
                    print(f"\n     ❌ 错误信息: {step.error_message}")
            
            print()
        
        print("=" * 70)
        print("✅ 可观测性验证完成")
        print("=" * 70)
        
        return True
        
    finally:
        db.close()


if __name__ == '__main__':
    success = verify_observability()
    sys.exit(0 if success else 1)
