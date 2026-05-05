#!/usr/bin/env python3
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# 直接读取文件内容
content = open(r"G:\需求\付款单-企业小程序_v1.2.3_files\data.js.下载", "r", encoding="utf-8").read()

# 手动调用 _extract_axure_annotations
from utils.document_parser import _extract_axure_annotations
results = _extract_axure_annotations(content, "data.js.下载")
print(f"提取结果: {len(results)} 条")
for r in results[:20]:
    t = r['type']
    c = r['content'][:120]
    lb = r.get('label', '')
    print(f"  [{t}] {f'【{lb}】 ' if lb else ''}{c}")

# 也测 _parse_axure_datajs 传入文件夹
print("\n\n=== 测试 _parse_axure_datajs(folder) ===")
from utils.document_parser import _parse_axure_datajs
folder = Path(r"G:\需求\付款单-企业小程序_v1.2.3_files")
print(f"is_file={folder.is_file()}, is_dir={folder.is_dir()}")
r2 = _parse_axure_datajs(folder)
print(f"结果: {len(r2)} 条")
