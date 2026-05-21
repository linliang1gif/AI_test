#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""模拟真实需求-代码匹配，验证中文标签能否桥接"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.code_analyzer import scan_code_directory
from utils.req_code_diff import _extract_code_items, _build_code_index, _tokenize, _score_code_items

CODE_DIR = r"D:\360Downloads\蓝点\recycle-applet-feature-1.2.3-latest\subpackages"

if not Path(CODE_DIR).is_dir():
    print(f"目录不存在: {CODE_DIR}")
    sys.exit(1)

analysis = scan_code_directory(CODE_DIR)
code_items = _extract_code_items(analysis)
code_index = _build_code_index(code_items)

print(f"Code items total: {len(code_items)}")
print(f"Index keys (tokens): {len(code_index)}")

# 模拟截图中的需求点
test_reqs = [
    "支持\"全部、待审核、已审核、已完成、\"筛选，默认\"全部\"",
    "财务应付单号",
    "供应商",
    "付款方向",
    "单据状态",
    "制单人",
    "付款币别",
    "业务日期",
    "个税承担方",
]

print("\n" + "=" * 70)
print("需求 → 代码匹配测试")
print("=" * 70)

matched_count = 0
for req_text in test_reqs:
    tokens = _tokenize(req_text)
    topk = _score_code_items(tokens, code_items, code_index, top_k=3)
    if topk:
        best = topk[0]
        overlap = len(tokens & best.get("_tokens", set()))
        denom = max(1, len(tokens))
        conf = min(overlap / denom + 0.2, 1.0)
        status = "✅" if conf > 0.3 else "⚠️"
        if conf > 0.3:
            matched_count += 1
        print(f"  {status} '{req_text[:30]}' → {best['name'][:40]} [{best['file'][:40]}] conf={conf:.2f}")
    else:
        print(f"  ❌ '{req_text[:30]}' → 无匹配")

print(f"\n匹配率: {matched_count}/{len(test_reqs)} = {matched_count/len(test_reqs)*100:.0f}%")
