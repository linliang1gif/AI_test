#!/usr/bin/env python3
"""测试 Axure 文件夹解析"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.document_parser import parse_axure_folder_structured

r = parse_axure_folder_structured(r"G:\需求\付款单-企业小程序_v1.2.3_files")
s = r["stats"]
print(f"注释={s['axure_notes']}, 功能点={s['features']}, 规则={s['rules']}, 字段={s['fields']}, 总字符={s['total_chars']}")

print("\n--- 注释 (前10条) ---")
for n in r["axure_notes"][:10]:
    print(f"  {n[:150]}")

print("\n--- 规则 (前10条) ---")
for rule in r["rules"][:10]:
    print(f"  {rule[:150]}")

print("\n--- 功能点 (前10) ---")
for f in r["features"][:10]:
    print(f"  {f['name']}")

print(f"\n--- raw_text 前1500字 ---")
print(r["raw_text"][:1500])
