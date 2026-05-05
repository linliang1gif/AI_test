#!/usr/bin/env python3
import re

c = open(r"G:\需求\付款单-企业小程序_v1.2.3_files\data.js.下载", "r", encoding="utf-8").read()

# Current regex
p = re.compile(r'(?:^|,|\s)([A-Za-z_][A-Za-z0-9_]*)\s*=\s*"((?:[^"\\]|\\.)*)"')
ms = list(p.finditer(c))
print(f"当前正则匹配数: {len(ms)}")

var_map = {m.group(1): m.group(2) for m in ms}
print(f"H in var_map? {'H' in var_map}")
print(f"J in var_map? {'J' in var_map}")

# 手动查找 H=
idx = c.find(',H=')
if idx >= 0:
    snippet = c[idx:idx+50]
    print(f"\nH= snippet: {repr(snippet)}")
    # 尝试从 H= 位置匹配
    test = c[idx+1:]  # skip comma
    m = re.match(r'([A-Za-z_]\w*)\s*=\s*"((?:[^"\\]|\\.)*)"', test)
    if m:
        print(f"H matched: key={m.group(1)}, val={m.group(2)[:50]}")
    else:
        print("H not matched by regex!")
        # 看看为什么不匹配
        m2 = re.match(r'([A-Za-z_]\w*)\s*=\s*"', test)
        if m2:
            start = m2.end()
            # 找下一个未转义的引号
            pos = start
            while pos < len(test):
                if test[pos] == '"' and (pos == 0 or test[pos-1] != '\\'):
                    break
                pos += 1
            val = test[start:pos]
            print(f"  Manual extract H val ({len(val)} chars): {repr(val[:100])}")
        else:
            print("  Can't even match H=\" !")

# 也检查 J
idx2 = c.find(',J=')
if idx2 >= 0:
    snippet2 = c[idx2:idx2+200]
    print(f"\nJ= snippet: {repr(snippet2[:200])}")
