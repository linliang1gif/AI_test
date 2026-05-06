# -*- coding: utf-8 -*-
"""冒烟测试: req_code_diff v2 引擎"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.req_code_diff import (
    run_req_code_diff, _extract_code_items, _build_code_index,
    _tokenize, _score_code_items,
)


def main():
    req = {
        "features": [
            {"name": "订单详情页可以查看商品列表", "description": "点击订单进入详情页，展示订单内的商品清单"},
            {"name": "支持按订单状态筛选", "description": "订单列表页提供状态下拉，用户可按已发货/已完成等筛选"},
            {"name": "退款金额校验：金额必须小于等于订单金额", "description": "提交退款单时校验金额边界"},
        ],
        "rules": [],
        "fields": [],
    }

    code = {
        "directory": "/test",
        "languages_detected": ["Vue", "TypeScript"],
        "stats": {"total_files": 3, "total_lines": 200},
        "components": [
            {"name": "OrderDetail 订单详情", "type": "vue_component", "file": "pages/order/detail.vue",
             "methods": ["fetchOrder", "renderItems"],
             "data_fields": ["orderId", "items", "amount", "商品列表"],
             "template_conditions": ["order.status==2", "items.length>0", "显示商品列表"]},
            {"name": "OrderList 订单列表", "type": "vue_component", "file": "pages/order/list.vue",
             "methods": ["filterByStatus", "fetchList"],
             "data_fields": ["statusFilter", "list", "订单状态"],
             "template_conditions": ["statusFilter", "按状态筛选"]},
        ],
        "routes": [
            {"method": "GET", "path": "/api/order/detail", "handler": "getOrderDetail", "file": "api/order.ts"},
        ],
        "functions": [
            {"name": "submitRefund", "file": "pages/refund/submit.vue", "line": 88, "params": ["amount"]},
        ],
        "api_calls": [],
        "conditions": [],
    }

    items = _extract_code_items(code)
    print(f"[1] 扩展后代码项: {len(items)}")
    for i in items[:8]:
        print(f"    {i['id']} [{i['type']}] {i['name']} @ {i['file']}")

    idx = _build_code_index(items)
    print(f"[2] 倒排索引 token 数: {len(idx)}")

    toks = _tokenize("订单状态筛选 status filter")
    print(f"[3] tokens for '订单状态筛选': {sorted(toks)[:15]}")
    hits = _score_code_items(toks, items, idx, top_k=5)
    print(f"[4] top 召回:")
    for h in hits:
        print(f"    {h['id']} {h['name']} ({h['file']})")

    res = run_req_code_diff(req, code, ai_client=None)
    print()
    print(f"[5] 规则对比结果 summary: {res['summary']}")
    print(f"    matched={len(res['matched'])} unimplemented={len(res['unimplemented'])}")
    for m in res["matched"]:
        print(f"    matched: {m['requirement']} -> {m['code_item']} (conf={m['confidence']})")
    for u in res["unimplemented"]:
        print(f"    missing: {u['requirement']}")

    assert len(items) >= 5, "代码项扩展失败"
    assert len(idx) > 10, "倒排索引为空"
    assert len(hits) > 0, "召回失败"
    assert len(res["matched"]) >= 1, "规则对比未召回"
    print()
    print("✅ 冒烟测试通过")


if __name__ == "__main__":
    main()
