#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快速验证 Java @ApiModelProperty 中文标签提取 + code_items 索引匹配"""
import sys, tempfile, shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.code_analyzer import scan_code_directory
from utils.req_code_diff import _extract_code_items, _build_code_index, _tokenize

JAVA_SRC = '''\
package com.example;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import javax.validation.constraints.NotNull;
import javax.validation.constraints.NotBlank;

@ApiModel(description = "财务应付单")
public class PaymentOrder {

    @ApiModelProperty("财务应付单号")
    @NotBlank
    private String paymentNo;

    @ApiModelProperty("供应商")
    @NotNull
    private String supplier;

    @ApiModelProperty(value = "单据状态")
    private Integer status;

    @ApiModelProperty("制单人")
    private String creator;
}
'''

VUE_SRC = '''\
<template>
  <view>
    <u-form-item label="供应商">
      <u-input v-model="form.supplier" placeholder="请选择供应商"/>
    </u-form-item>
    <u-form-item label="财务应付单号">
      <text>{{ paymentNo }}</text>
    </u-form-item>
    <u-tabs :list="['全部','待审核','已审核','已完成']" />
    <text>单据状态</text>
  </view>
</template>
<script>
export default {
  data() {
    return {
      form: { supplier: '', paymentNo: '' },
      status: '全部',
    }
  },
  methods: {
    loadList() {
      uni.request({ url: '/finance/payment/list' })
    }
  }
}
</script>
'''


def main():
    tmpdir = tempfile.mkdtemp(prefix="test_labels_")
    java_dir = Path(tmpdir) / "src" / "main" / "java" / "com"
    java_dir.mkdir(parents=True)
    (java_dir / "PaymentOrder.java").write_text(JAVA_SRC, encoding="utf-8")

    vue_dir = Path(tmpdir) / "pages" / "payment"
    vue_dir.mkdir(parents=True)
    (vue_dir / "list.vue").write_text(VUE_SRC, encoding="utf-8")

    print("=" * 60)
    print("测试 code_analyzer 中文标签提取")
    print("=" * 60)

    analysis = scan_code_directory(tmpdir)

    # 检查 Java class
    java_comps = [c for c in analysis["components"] if c["type"] == "java_class"]
    assert java_comps, "未找到 Java class"
    jc = java_comps[0]
    print(f"\nJava class: {jc['name']}")
    print(f"  chinese_labels: {jc.get('chinese_labels', [])}")
    print(f"  description: {jc.get('description', '')}")
    print(f"  fields: {len(jc.get('fields', []))}")
    for f in jc.get("fields", []):
        print(f"    - {f['label']} → {f['field_name']} [{', '.join(f['validations'])}]")

    assert "供应商" in jc["chinese_labels"], f"Missing 供应商: {jc['chinese_labels']}"
    assert "财务应付单号" in jc["chinese_labels"], f"Missing 财务应付单号"
    assert jc.get("description") == "财务应付单", f"Desc: {jc.get('description')}"

    # 检查 Vue component
    vue_comps = [c for c in analysis["components"] if c["type"] == "vue_component"]
    assert vue_comps, "未找到 Vue component"
    vc = vue_comps[0]
    print(f"\nVue component: {vc['name']}")
    print(f"  chinese_labels: {vc.get('chinese_labels', [])}")
    assert "供应商" in vc["chinese_labels"], f"Missing 供应商: {vc['chinese_labels']}"
    assert "财务应付单号" in vc["chinese_labels"], f"Missing 财务应付单号"

    # 检查 code_items 索引匹配
    print("\n" + "=" * 60)
    print("测试 code_items 关键词匹配")
    print("=" * 60)

    code_items = _extract_code_items(analysis)
    code_index = _build_code_index(code_items)

    test_reqs = ["供应商", "财务应付单号", "单据状态", "制单人"]
    for req_text in test_reqs:
        tokens = _tokenize(req_text)
        # 找匹配
        score = {}
        for tok in tokens:
            for idx in code_index.get(tok, []):
                score[idx] = score.get(idx, 0) + 1
        if score:
            best_idx = max(score, key=score.get)
            best = code_items[best_idx]
            print(f"  需求 '{req_text}' → 匹配 code_item: '{best['name']}' (score={score[best_idx]}, file={best['file']})")
        else:
            print(f"  需求 '{req_text}' → ❌ 无匹配！")

    # 验证所有需求都能匹配
    all_matched = True
    for req_text in test_reqs:
        tokens = _tokenize(req_text)
        found = any(tok in code_index for tok in tokens)
        if not found:
            print(f"\n  FAIL: '{req_text}' 在索引中无命中")
            all_matched = False

    shutil.rmtree(tmpdir, ignore_errors=True)

    print("\n" + "=" * 60)
    if all_matched:
        print("✅ 全部中文需求 → 代码匹配成功")
    else:
        print("❌ 部分需求匹配失败")
    print("=" * 60)
    return 0 if all_matched else 1


if __name__ == "__main__":
    sys.exit(main())
