#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Pipeline V2 使用真实 ExecutionEngine
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from pipeline_v2 import run_pipeline_v2


def test_pipeline_with_real_engine():
    """测试 Pipeline V2 使用真实 ExecutionEngine"""
    print("=" * 80)
    print("🧪 测试 Pipeline V2 + 真实 ExecutionEngine")
    print("=" * 80)
    
    try:
        # 运行 Pipeline（使用真实 API）
        results = run_pipeline_v2(
            requirement="用户管理功能：支持用户注册、登录、获取用户信息",
            base_url="https://jsonplaceholder.typicode.com",
            environment="test",
            output_dir="output_real_engine"
        )
        
        if results is None:
            print("\n❌ Pipeline 执行失败")
            return False
        
        print(f"\n✅ Pipeline 执行完成，共 {len(results)} 个结果")
        
        # 验证结果包含 trace_id
        trace_ids = []
        for result in results:
            if hasattr(result, 'trace_id') and result.trace_id:
                trace_ids.append(result.trace_id)
        
        print(f"✅ 收集到 {len(trace_ids)} 个 trace_id")
        
        if trace_ids:
            print(f"\n示例 trace_id:")
            for i, tid in enumerate(trace_ids[:3], 1):
                print(f"  {i}. {tid}")
        
        # 检查 pipeline_summary_v2.json
        summary_file = Path("output_real_engine/pipeline_summary_v2.json")
        if summary_file.exists():
            with open(summary_file, 'r', encoding='utf-8') as f:
                summary = json.load(f)
            
            execution_info = summary.get('stages', {}).get('execution', {})
            
            print(f"\n📊 执行信息:")
            print(f"  引擎: {execution_info.get('engine')}")
            print(f"  Trace IDs: {len(execution_info.get('trace_ids', []))}")
            print(f"  失败用例: {len(execution_info.get('failures', []))}")
            
            # 验证引擎类型
            assert execution_info.get('engine') == 'real', "应该使用真实引擎"
            print(f"\n✅ 验证通过: 使用真实 ExecutionEngine")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("🚀 Pipeline V2 真实引擎测试")
    print("=" * 80)
    
    success = test_pipeline_with_real_engine()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ 所有测试通过！")
        print("=" * 80)
        return 0
    else:
        print("❌ 测试失败")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    exit(main())
