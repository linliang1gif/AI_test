#!/usr/bin/env python3
"""完全模拟 _extract_axure_annotations 逻辑，带详细 debug"""
import re

content = open(r"G:\需求\付款单-企业小程序_v1.2.3_files\data.js.下载", "r", encoding="utf-8").read()

# Step 1: Build var_map
var_map = {}
pair_pattern = re.compile(r'(?:^|,|\s)([A-Za-z_][A-Za-z0-9_]*)\s*=\s*"((?:[^"\\]|\\.)*)"')
for pm in pair_pattern.finditer(content):
    var_map[pm.group(1)] = pm.group(2)
print(f"var_map size: {len(var_map)}")

# Step 2: Find key vars
label_var = desc_var = fn_var = None
for k, v in var_map.items():
    if v == 'label': label_var = k
    elif v == '说明' or v == 'description': desc_var = k
    elif v == 'fn': fn_var = k
print(f"fn={fn_var}, label={label_var}, desc={desc_var}")

# Step 3: Match annotations
anno_pattern = re.compile(r'_\(' + re.escape(fn_var) + r',([^)]+)\)', re.DOTALL)
seen = set()

for i, m in enumerate(anno_pattern.finditer(content)):
    block = m.group(1)
    tokens = [t.strip() for t in block.split(',')]
    pairs = {}
    for idx in range(1, len(tokens) - 1, 2):
        key = tokens[idx].strip()
        raw_val = tokens[idx + 1].strip() if idx + 1 < len(tokens) else ''
        if raw_val.startswith('"') and raw_val.endswith('"'):
            val = raw_val[1:-1]
        else:
            val = var_map.get(raw_val, raw_val)
        pairs[key] = val

    label_text = pairs.get(label_var, '').strip()
    desc_text = pairs.get(desc_var, '').strip()

    # HTML cleanup
    if desc_text:
        desc_clean = re.sub(r'<[^>]+>', '', desc_text).strip()
    else:
        desc_clean = ''
    if label_text:
        label_clean = re.sub(r'<[^>]+>', '', label_text).strip()
    else:
        label_clean = ''

    if i < 5:
        print(f"\n--- Match {i} ---")
        print(f"  tokens({len(tokens)}): {tokens}")
        print(f"  pairs keys: {list(pairs.keys())}")
        print(f"  label_var='{label_var}' in pairs? {label_var in pairs}")
        print(f"  desc_var='{desc_var}' in pairs? {desc_var in pairs}")
        print(f"  label_text: '{label_text[:50]}' -> clean: '{label_clean[:50]}'")
        print(f"  desc_text: '{desc_text[:80]}' -> clean: '{desc_clean[:80]}'")
        
        would_be = "annotation" if label_clean and desc_clean else ("label" if label_clean else "skip")
        print(f"  -> would be: {would_be}")
