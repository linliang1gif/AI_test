#!/usr/bin/env python3
"""调试 annotation 匹配"""
import re

p = r"G:\需求\付款单-企业小程序_v1.2.3_files\data.js.下载"
content = open(p, "r", encoding="utf-8").read()

# 从已知 var 声明中看到: B="annotations", 对应数组中有 _(C,D,E,F,G,H,I,J)
# C=fn, D="1", E=ownerId, F=具体ID, G=label, H=标签文本, I=说明, J=说明文本
# 所以 annotation 项格式: _(C,序号,E,ownerID,G,标签文本,I,说明文本)
# 即 _(C,"1",E,"344e...",G,"(下拉列表)",I,"<p><span>支持筛选...</span></p>")

# 查找 B,[ 后面的数组
b_idx = content.find('B,[')
if b_idx == -1:
    print("未找到 B,[ 标记")
else:
    print(f"B,[ 位于 offset {b_idx}")
    # 从这里找到匹配的 ]
    snippet = content[b_idx:b_idx+3000]
    print(f"片段:\n{snippet[:1500]}")

print("\n\n--- 直接搜索 _(C, 模式 ---")
# 尝试匹配 _(C,D,E,F,G,xxx,I,xxx) 其中 xxx 可以是变量或字符串
pattern = re.compile(r'_\(C,\w+,E,\w+,G,(\w+),I,(\w+)\)')
matches = list(pattern.finditer(content))
print(f"匹配数: {len(matches)}")
for m in matches[:5]:
    print(f"  G_val={m.group(1)}, I_val={m.group(2)}")

# 也查找 G 和 I 后跟引号的情况
pattern2 = re.compile(r'_\(C,\w+,E,\w+,G,"([^"]*)",I,"([^"]*)"')
matches2 = list(pattern2.finditer(content))
print(f"\n引号匹配数: {len(matches2)}")

# 试试只匹配含 G 和 I 的短块
pattern3 = re.compile(r'_\(C,([^)]{10,300})\)')
matches3 = list(pattern3.finditer(content))
print(f"\n_\(C,...) 块数: {len(matches3)}")
for m in matches3[:3]:
    block = m.group(1)
    print(f"  块: {block[:200]}")
