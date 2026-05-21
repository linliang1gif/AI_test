#!/usr/bin/env python3
import re

content = open(r"G:\需求\付款单-企业小程序_v1.2.3_files\data.js.下载", "r", encoding="utf-8").read()

var_map = {}
pair_pattern = re.compile(r'(?:^|,|\s)([A-Za-z_][A-Za-z0-9_]*)\s*=\s*"((?:[^"\\]|\\.)*)"')
for pm in pair_pattern.finditer(content):
    var_map[pm.group(1)] = pm.group(2)

label_var = 'G'
desc_var = 'I'
fn_var = 'C'

anno_pattern = re.compile(r'_\(' + re.escape(fn_var) + r',([^)]+)\)', re.DOTALL)
matches = list(anno_pattern.finditer(content))

for i, m in enumerate(matches[:3]):
    block = m.group(1)
    tokens = [t.strip() for t in block.split(',')]
    print(f"\n--- Match {i} ---")
    print(f"Tokens: {tokens}")
    
    pairs = {}
    for idx in range(1, len(tokens) - 1, 2):
        key = tokens[idx].strip()
        raw_val = tokens[idx + 1].strip() if idx + 1 < len(tokens) else ''
        if raw_val.startswith('"') and raw_val.endswith('"'):
            val = raw_val[1:-1]
        else:
            val = var_map.get(raw_val, f'?{raw_val}')
        pairs[key] = val
        print(f"  key_var={key} -> key_val={var_map.get(key, key)}, val={val[:50]}")
    
    print(f"  pairs.get('G')={pairs.get('G', 'MISSING')[:50]}")
    print(f"  pairs.get('I')={pairs.get('I', 'MISSING')[:50]}")
