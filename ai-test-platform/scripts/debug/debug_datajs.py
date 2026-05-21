#!/usr/bin/env python3
"""调试 data.js 解析"""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

p = r"G:\需求\付款单-企业小程序_v1.2.3_files\data.js.下载"
content = open(p, "r", encoding="utf-8").read()

# 解析 var 声明
var_map = {}
var_line_pattern = re.compile(r'var\s+(.+?)(?:;|$)', re.MULTILINE)
for m in var_line_pattern.finditer(content):
    assignments = m.group(1)
    pair_pattern = re.compile(r'([A-Za-z_][A-Za-z0-9_]*)\s*=\s*"((?:[^"\\]|\\.)*)"')
    for pm in pair_pattern.finditer(assignments):
        var_map[pm.group(1)] = pm.group(2)

print(f"变量总数: {len(var_map)}")

# 找关键变量
for k, v in sorted(var_map.items()):
    if v in ('label', '说明', 'fn', 'annotations', 'name', 'description', 'note', 'notes'):
        print(f"  ★ {k} = \"{v}\"")

print("\n--- label/说明相关变量 ---")
label_var = desc_var = fn_var = None
for k, v in var_map.items():
    if v == 'label':
        label_var = k
        print(f"  label变量: {k}")
    elif v == '说明':
        desc_var = k
        print(f"  说明变量: {k}")
    elif v == 'fn':
        fn_var = k
        print(f"  fn变量: {k}")

# 看看annotations数组
print(f"\n  fn_var={fn_var}, label_var={label_var}, desc_var={desc_var}")

# 尝试直接用 _extract_axure_annotations
from utils.document_parser import _extract_axure_annotations
results = _extract_axure_annotations(content, "data.js.下载")
print(f"\n提取结果: {len(results)} 条")
for r in results[:15]:
    t = r['type']
    c = r['content'][:100]
    lb = r.get('label', '')
    print(f"  [{t}] {f'【{lb}】' if lb else ''}{c}")
