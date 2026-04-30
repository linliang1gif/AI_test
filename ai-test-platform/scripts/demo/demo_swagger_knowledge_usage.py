#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
演示如何在AI测试流程中使用Swagger知识库
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from knowledge.knowledge_manager import KnowledgeManager


def demo_api_search():
    """演示1: API语义检索"""
    print("=" * 60)
    print("演示1: API语义检索")
    print("=" * 60)
    
    km = KnowledgeManager()
    collection = km.kb.get_collection("apis")
    
    if not collection:
        print("❌ API集合不存在,请先运行: py import_swagger_to_knowledge.py")
        return
    
    # 测试场景
    scenarios = [
        {
            "name": "用户登录测试",
            "query": "用户登录 认证 token",
            "description": "需要测试用户登录功能"
        },
        {
            "name": "采购订单管理",
            "query": "采购订单 新增 查询 修改",
            "description": "需要测试采购订单的CRUD操作"
        },
        {
            "name": "库存查询",
            "query": "库存 查询 明细 统计",
            "description": "需要测试库存查询和统计功能"
        },
        {
            "name": "财务应收管理",
            "query": "财务 应收 收款 核销",
            "description": "需要测试财务应收相关功能"
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📋 测试场景: {scenario['name']}")
        print(f"   描述: {scenario['description']}")
        print(f"   查询: {scenario['query']}")
        print(f"\n   🔍 找到的相关API:")
        
        results = collection.query(
            query_texts=[scenario['query']],
            n_results=5
        )
        
        if results and results['ids']:
            for i, (api_id, distance) in enumerate(zip(results['ids'][0], results['distances'][0]), 1):
                metadata = results['metadatas'][0][i-1]
                similarity = 1 - distance
                
                if similarity > 0.15:  # 只显示相似度>15%的结果
                    print(f"\n   {i}. {metadata['method']} {metadata['path']}")
                    print(f"      摘要: {metadata['summary']}")
                    print(f"      标签: {metadata['tags']}")
                    print(f"      相似度: {similarity:.2%}")


def demo_test_case_generation():
    """演示2: 基于API知识生成测试用例"""
    print("\n" + "=" * 60)
    print("演示2: 基于API知识生成测试用例")
    print("=" * 60)
    
    km = KnowledgeManager()
    collection = km.kb.get_collection("apis")
    
    if not collection:
        print("❌ API集合不存在")
        return
    
    # 需求: 测试币别管理功能
    requirement = "测试币别管理功能,包括新增、查询、编辑、删除币别"
    
    print(f"\n📝 需求: {requirement}")
    print(f"\n🔍 检索相关API...")
    
    results = collection.query(
        query_texts=[requirement],
        n_results=10
    )
    
    if results and results['ids']:
        # 过滤币别相关的API
        currency_apis = []
        for i, api_id in enumerate(results['ids'][0]):
            metadata = results['metadatas'][0][i]
            if '币别' in metadata['tags'] or 'currency' in metadata['path'].lower():
                currency_apis.append({
                    'method': metadata['method'],
                    'path': metadata['path'],
                    'summary': metadata['summary'],
                    'tags': metadata['tags']
                })
        
        print(f"\n✅ 找到 {len(currency_apis)} 个币别相关API:")
        for i, api in enumerate(currency_apis, 1):
            print(f"\n{i}. {api['method']} {api['path']}")
            print(f"   {api['summary']}")
        
        # 生成测试用例
        print(f"\n📋 生成测试用例:")
        
        test_cases = [
            {
                "id": "TC_CURRENCY_001",
                "title": "新增币别-正常流程",
                "api": "/basic/basicCurrency/add",
                "method": "POST",
                "priority": "高",
                "steps": [
                    "准备币别数据(币别名称、符号、小数位)",
                    "调用新增币别API",
                    "验证返回结果"
                ],
                "expected": "币别新增成功,返回code=200"
            },
            {
                "id": "TC_CURRENCY_002",
                "title": "查询币别列表",
                "api": "/basic/basicCurrency/list",
                "method": "POST",
                "priority": "高",
                "steps": [
                    "调用币别列表API",
                    "验证返回数据格式",
                    "验证数据完整性"
                ],
                "expected": "返回币别列表,包含所有启用的币别"
            },
            {
                "id": "TC_CURRENCY_003",
                "title": "编辑币别信息",
                "api": "/basic/basicCurrency/update",
                "method": "POST",
                "priority": "中",
                "steps": [
                    "准备要修改的币别UUID",
                    "准备修改后的数据",
                    "调用编辑API",
                    "验证修改成功"
                ],
                "expected": "币别信息修改成功"
            },
            {
                "id": "TC_CURRENCY_004",
                "title": "删除币别",
                "api": "/basic/basicCurrency/delete",
                "method": "POST",
                "priority": "中",
                "steps": [
                    "准备要删除的币别UUID",
                    "调用删除API",
                    "验证删除成功",
                    "验证列表中不再显示"
                ],
                "expected": "币别删除成功"
            },
            {
                "id": "TC_CURRENCY_005",
                "title": "启用/禁用币别",
                "api": "/basic/basicCurrency/enabled",
                "method": "POST",
                "priority": "中",
                "steps": [
                    "准备币别UUID",
                    "调用启用/禁用API",
                    "验证状态变更成功"
                ],
                "expected": "币别状态变更成功"
            }
        ]
        
        for tc in test_cases:
            print(f"\n   {tc['id']}: {tc['title']}")
            print(f"   API: {tc['method']} {tc['api']}")
            print(f"   优先级: {tc['priority']}")
            print(f"   步骤: {' → '.join(tc['steps'])}")
            print(f"   预期: {tc['expected']}")


def demo_test_data_generation():
    """演示3: 基于API参数生成测试数据"""
    print("\n" + "=" * 60)
    print("演示3: 基于API参数生成测试数据")
    print("=" * 60)
    
    # 模拟从Swagger中提取的API参数信息
    api_info = {
        "path": "/basic/basicCurrency/add",
        "method": "POST",
        "summary": "新增币别",
        "parameters": {
            "currencyName": {
                "type": "string",
                "required": True,
                "description": "币别名称"
            },
            "currencySymbol": {
                "type": "string",
                "required": True,
                "description": "币别符号"
            },
            "currencyNameEn": {
                "type": "string",
                "required": False,
                "description": "币别英文名称"
            },
            "baseCurrency": {
                "type": "integer",
                "required": False,
                "description": "是否基准币别：0-否，1-是"
            },
            "unitPriceDecimalPlace": {
                "type": "integer",
                "required": False,
                "description": "单价小数位"
            },
            "totalPriceDecimalPlace": {
                "type": "integer",
                "required": False,
                "description": "金额小数位"
            }
        }
    }
    
    print(f"\n📋 API信息:")
    print(f"   {api_info['method']} {api_info['path']}")
    print(f"   {api_info['summary']}")
    
    print(f"\n🎲 生成测试数据:")
    
    # 正常数据
    normal_data = {
        "currencyName": "美元",
        "currencySymbol": "USD",
        "currencyNameEn": "US Dollar",
        "baseCurrency": 0,
        "unitPriceDecimalPlace": 2,
        "totalPriceDecimalPlace": 2,
        "remark": "美元币别"
    }
    
    print(f"\n   1. 正常数据:")
    print(f"      {json.dumps(normal_data, ensure_ascii=False, indent=6)}")
    
    # 边界数据
    boundary_data = {
        "currencyName": "A" * 50,  # 最大长度
        "currencySymbol": "XXX",
        "unitPriceDecimalPlace": 8,  # 最大小数位
        "totalPriceDecimalPlace": 8
    }
    
    print(f"\n   2. 边界数据:")
    print(f"      {json.dumps(boundary_data, ensure_ascii=False, indent=6)}")
    
    # 异常数据
    abnormal_data = {
        "currencyName": "",  # 空值
        "currencySymbol": "",  # 空值
        "unitPriceDecimalPlace": -1,  # 负数
        "totalPriceDecimalPlace": 100  # 超大值
    }
    
    print(f"\n   3. 异常数据:")
    print(f"      {json.dumps(abnormal_data, ensure_ascii=False, indent=6)}")


def demo_api_dependency_analysis():
    """演示4: API依赖关系分析"""
    print("\n" + "=" * 60)
    print("演示4: API依赖关系分析")
    print("=" * 60)
    
    print(f"\n📊 业务流程: 采购订单完整流程")
    
    workflow = [
        {
            "step": 1,
            "name": "创建采购订单",
            "apis": [
                "POST /purchase/order/add",
                "POST /purchase/order/save"
            ],
            "dependencies": []
        },
        {
            "step": 2,
            "name": "审核采购订单",
            "apis": [
                "POST /purchase/order/audit",
                "POST /purchase/order/approve"
            ],
            "dependencies": ["创建采购订单"]
        },
        {
            "step": 3,
            "name": "采购入库",
            "apis": [
                "POST /purchase/stockin/add",
                "POST /purchase/stockin/save"
            ],
            "dependencies": ["审核采购订单"]
        },
        {
            "step": 4,
            "name": "质检",
            "apis": [
                "POST /quality/inspection/add",
                "POST /quality/inspection/check"
            ],
            "dependencies": ["采购入库"]
        },
        {
            "step": 5,
            "name": "财务应付",
            "apis": [
                "POST /finance/payment/add",
                "POST /finance/payment/pay"
            ],
            "dependencies": ["质检"]
        }
    ]
    
    for step_info in workflow:
        print(f"\n   步骤{step_info['step']}: {step_info['name']}")
        print(f"   相关API:")
        for api in step_info['apis']:
            print(f"      - {api}")
        if step_info['dependencies']:
            print(f"   依赖: {', '.join(step_info['dependencies'])}")
    
    print(f"\n💡 测试建议:")
    print(f"   1. 按流程顺序执行测试")
    print(f"   2. 每个步骤完成后验证数据状态")
    print(f"   3. 测试异常场景(跳过某个步骤)")
    print(f"   4. 测试并发场景(多个订单同时处理)")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🎯 Swagger知识库使用演示")
    print("=" * 60)
    
    # 演示1: API语义检索
    demo_api_search()
    
    # 演示2: 基于API知识生成测试用例
    demo_test_case_generation()
    
    # 演示3: 基于API参数生成测试数据
    demo_test_data_generation()
    
    # 演示4: API依赖关系分析
    demo_api_dependency_analysis()
    
    print("\n" + "=" * 60)
    print("✅ 演示完成!")
    print("=" * 60)
    print("\n💡 提示:")
    print("   1. 知识库已包含814个API")
    print("   2. 可以通过自然语言查询相关API")
    print("   3. AI会自动使用这些知识生成测试用例")
    print("   4. 测试数据会根据API参数自动生成")
    print("=" * 60)
