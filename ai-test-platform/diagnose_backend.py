#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后端模块诊断脚本
检查所有模块是否能正常导入
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("后端模块导入诊断")
print("=" * 60)

# 测试各个模块导入
modules_to_test = [
    ("Agent", "agent.controller", "router"),
    ("Strategy", "strategy.controller", "router"),
    ("Orchestrator", "orchestrator.controller", "router"),
    ("Self-Healing", "self_healing.controller", "router"),
    ("Pipeline", "pipeline.controller", "router"),
    ("Case Generator", "case_generator.controller", "case_router"),
]

results = []

for name, module_path, attr_name in modules_to_test:
    try:
        module = __import__(module_path, fromlist=[attr_name])
        router = getattr(module, attr_name)
        print(f"✅ {name:20s} - 导入成功")
        results.append((name, True, None))
    except Exception as e:
        print(f"❌ {name:20s} - 导入失败: {str(e)}")
        results.append((name, False, str(e)))

print("\n" + "=" * 60)
print("诊断总结")
print("=" * 60)

success_count = sum(1 for _, success, _ in results if success)
total_count = len(results)

print(f"成功: {success_count}/{total_count}")
print(f"失败: {total_count - success_count}/{total_count}")

if success_count < total_count:
    print("\n失败详情:")
    for name, success, error in results:
        if not success:
            print(f"\n{name}:")
            print(f"  错误: {error}")

print("\n" + "=" * 60)
