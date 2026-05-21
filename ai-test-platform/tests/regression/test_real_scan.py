#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快速扫描蓝点真实代码，验证中文标签提取"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.code_analyzer import scan_code_directory

CODE_DIR = r"D:\360Downloads\蓝点\recycle-applet-feature-1.2.3-latest\subpackages"

if not Path(CODE_DIR).is_dir():
    print(f"目录不存在: {CODE_DIR}")
    sys.exit(1)

r = scan_code_directory(CODE_DIR)
print(f"Files: {r['stats']['total_files']}")
print(f"Components: {len(r['components'])}")

vue_comps = [c for c in r["components"] if c["type"] == "vue_component"]
print(f"Vue components: {len(vue_comps)}")
print(f"Vue with chinese_labels: {sum(1 for c in vue_comps if c.get('chinese_labels'))}")

all_labels = set()
for c in vue_comps:
    all_labels.update(c.get("chinese_labels", []))
print(f"Unique chinese labels: {len(all_labels)}")
print(f"\nSample labels (前30):")
for lb in sorted(all_labels)[:30]:
    print(f"  - {lb}")
