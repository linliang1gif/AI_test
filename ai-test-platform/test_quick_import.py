#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
快速测试导入 - 只导入少量数据用于测试
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("🧪 快速测试导入")
print("=" * 70)

from knowledge.knowledge_manager import get_knowledge_manager

km = get_knowledge_manager()

# 创建测试API数据
test_apis = [
    {
        "path": "/api/purchase/order/create",
        "method": "POST",
        "summary": "创建采购订单",
        "description": "创建新的采购订单",
        "tags": ["采购管理"],
        "operationId": "createPurchaseOrder"
    },
    {
        "path": "/api/purchase/order/list",
        "method": "GET",
        "summary": "查询采购订单列表",
        "description": "分页查询采购订单",
        "tags": ["采购管理"],
        "operationId": "listPurchaseOrders"
    },
    {
        "path": "/api/warehouse/stock/in",
        "method": "POST",
        "summary": "创建入库单",
        "description": "创建新的入库单",
        "tags": ["仓库管理"],
        "operationId": "createStockIn"
    },
    {
        "path": "/api/warehouse/stock/query",
        "method": "GET",
        "summary": "查询库存",
        "description": "查询当前库存信息",
        "tags": ["仓库管理"],
        "operationId": "queryStock"
    },
    {
        "path": "/api/payment/create",
        "method": "POST",
        "summary": "创建支付订单",
        "description": "创建支付订单",
        "tags": ["支付管理"],
        "operationId": "createPayment"
    }
]

print(f"\n📝 准备导入 {len(test_apis)} 个测试API...")

try:
    # 导入API
    for i, api in enumerate(test_apis, 1):
        print(f"   {i}. {api['method']} {api['path']}")
        km.add_api(api)
    
    print(f"\n✅ 导入完成!")
    
    # 检查状态
    stats = km.get_knowledge_stats()
    api_count = stats.get('apis', {}).get('total', 0)
    
    print(f"\n📊 知识库状态:")
    print(f"   - APIs: {api_count}")
    
    if api_count > 0:
        print(f"\n🎉 测试成功!知识库已有数据")
        print(f"\n💡 现在可以运行完整测试:")
        print(f"   py test_complete_rag_integration.py")
    else:
        print(f"\n⚠️  导入失败,API数量仍为0")
        
except Exception as e:
    print(f"\n❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
