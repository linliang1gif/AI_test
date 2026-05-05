#!/usr/bin/env python3
import re

content = open(r"G:\需求\付款单-企业小程序_v1.2.3_files\data.js.下载", "r", encoding="utf-8").read()

# Build var_map
var_map = {}
pair_pattern = re.compile(r'(?:^|,|\s)([A-Za-z_][A-Za-z0-9_]*)\s*=\s*"((?:[^"\\]|\\.)*)"')
for pm in pair_pattern.finditer(content):
    var_map[pm.group(1)] = pm.group(2)

print(f"var_map size: {len(var_map)}")
print(f"G={var_map.get('G')}, I={var_map.get('I')}, C={var_map.get('C')}")
print(f"H={var_map.get('H','MISSING')[:30]}")
print(f"J={var_map.get('J','MISSING')[:50]}")

label_var = 'G'
desc_var = 'I'
fn_var = 'C'

# Match _(C,...) blocks
anno_pattern = re.compile(
    r'_\(' + re.escape(fn_var) + r',([^)]+)\)',
    re.DOTALL
)
matches = list(anno_pattern.finditer(content))
print(f"\n_(C,...) matches: {len(matches)}")

if matches:
    # Show first match
    block = matches[0].group(1)
    print(f"First block: {repr(block[:100])}")
    tokens = [t.strip() for t in block.split(',')]
    print(f"Tokens: {tokens}")
    
    # Build pairs
    pairs = {}
    for idx in range(0, len(tokens) - 1, 2):
        key = tokens[idx].strip()
        raw_val = tokens[idx + 1].strip()
        if raw_val.startswith('"') and raw_val.endswith('"'):
            val = raw_val[1:-1]
        else:
            val = var_map.get(raw_val, f'?{raw_val}')
        pairs[key] = val
    
    print(f"Pairs: { {k: v[:50] for k,v in pairs.items()} }")
    print(f"label_text = pairs[G] = {pairs.get('G', 'MISSING')}")
    print(f"desc_text = pairs[I] = {pairs.get('I', 'MISSING')[:80]}")
else:
    print("No matches! Let me check why...")
    # Try a simpler pattern
    idx = content.find('_(C,')
    if idx >= 0:
        print(f"Found '_(C,' at offset {idx}")
        snippet = content[idx:idx+100]
        print(f"Snippet: {repr(snippet)}")
    else:
        print("'_(C,' not found in content")
    
    # Check if C is being used differently
    idx2 = content.find('_(' + fn_var)
    if idx2 >= 0:
        print(f"Found '_({fn_var}' at offset {idx2}")
        print(f"Snippet: {repr(content[idx2:idx2+100])}")
