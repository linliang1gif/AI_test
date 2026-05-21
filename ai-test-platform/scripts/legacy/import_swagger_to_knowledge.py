#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Swagger导入知识库脚本
将用户的Swagger JSON文件解析并导入到ChromaDB知识库中
"""

import json
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from parser.swagger_parser import SwaggerParser
from knowledge.knowledge_manager import KnowledgeManager


def import_swagger_to_knowledge(swagger_file: str = "swaggerApi (1).json"):
    """
    将Swagger文件导入到知识库
    
    Args:
        swagger_file: Swagger JSON文件路径
    """
    print("=" * 60)
    print("🚀 Swagger导入知识库")
    print("=" * 60)
    
    # 1. 加载Swagger文件
    print(f"\n📂 加载Swagger文件: {swagger_file}")
    parser = SwaggerParser()
    
    try:
        swagger_data = parser.load_swagger_file(swagger_file)
        print(f"✅ Swagger文件加载成功")
        print(f"   系统名称: {swagger_data.get('info', {}).get('title', 'Unknown')}")
        print(f"   版本: {swagger_data.get('info', {}).get('version', 'Unknown')}")
    except Exception as e:
        print(f"❌ Swagger文件加载失败: {e}")
        return False
    
    # 2. 解析API
    print(f"\n🔍 解析API接口...")
    try:
        apis = parser.parse_apis()
        print(f"✅ 成功解析 {len(apis)} 个API接口")
        
        # 统计信息
        summary = parser.generate_api_summary()
        print(f"\n📊 API统计:")
        print(f"   总API数: {summary['total_apis']}")
        print(f"   路径数: {summary['paths']}")
        print(f"   HTTP方法分布:")
        for method, count in summary['methods'].items():
            print(f"      {method}: {count}")
        print(f"   标签分类 (前10个):")
        for tag, count in list(summary['tags'].items())[:10]:
            print(f"      {tag}: {count}")
        
    except Exception as e:
        print(f"❌ API解析失败: {e}")
        return False
    
    # 3. 导入到知识库
    print(f"\n💾 导入到知识库...")
    km = KnowledgeManager()
    
    if not km.kb or not km.kb.available:
        print("❌ 知识库不可用,请先安装ChromaDB")
        print("   运行: pip install chromadb")
        return False
    
    # 获取或创建API集合
    try:
        collection = km.kb.get_collection("apis")
        if not collection:
            print("❌ 集合获取失败")
            return False
        print("✅ 使用API集合")
    except Exception as e:
        print(f"❌ 集合获取失败: {e}")
        return False
    
    # 导入API到ChromaDB
    success_count = 0
    error_count = 0
    
    for api in apis:
        try:
            # 生成API ID
            api_id = f"{api['method']}_{api['path'].replace('/', '_')}"
            
            # 生成文档文本(用于向量化)
            doc_text = f"""
API: {api['method']} {api['path']}
摘要: {api.get('summary', '')}
描述: {api.get('description', '')}
标签: {', '.join(api.get('tags', []))}
参数: {json.dumps(api.get('parameters', []), ensure_ascii=False)}
            """.strip()
            
            # 元数据
            metadata = {
                "api_id": api_id,
                "method": api['method'],
                "path": api['path'],
                "summary": api.get('summary', ''),
                "tags": ','.join(api.get('tags', [])),
                "source": "swagger_import"
            }
            
            # 添加到ChromaDB
            collection.add(
                documents=[doc_text],
                metadatas=[metadata],
                ids=[api_id]
            )
            
            success_count += 1
            
        except Exception as e:
            error_count += 1
            print(f"⚠️ API导入失败: {api['method']} {api['path']} - {e}")
    
    print(f"\n✅ 导入完成:")
    print(f"   成功: {success_count}")
    print(f"   失败: {error_count}")
    
    # 4. 验证导入结果
    print(f"\n🔍 验证导入结果...")
    try:
        # 测试查询
        test_queries = [
            "币别管理",
            "采购订单",
            "库存管理",
            "财务应收",
            "用户登录"
        ]
        
        print(f"\n测试查询 (前3个):")
        for query in test_queries[:3]:
            results = collection.query(
                query_texts=[query],
                n_results=3
            )
            
            if results and results['ids']:
                print(f"\n   查询: '{query}'")
                for i, (api_id, distance) in enumerate(zip(results['ids'][0], results['distances'][0]), 1):
                    metadata = results['metadatas'][0][i-1]
                    similarity = 1 - distance
                    print(f"      {i}. {metadata['method']} {metadata['path']}")
                    print(f"         {metadata['summary']}")
                    print(f"         相似度: {similarity:.2%}")
        
    except Exception as e:
        print(f"⚠️ 验证查询失败: {e}")
    
    # 5. 生成导入报告
    print(f"\n" + "=" * 60)
    print("📋 导入报告")
    print("=" * 60)
    print(f"✅ Swagger文件: {swagger_file}")
    print(f"✅ 系统名称: {swagger_data.get('info', {}).get('title', 'Unknown')}")
    print(f"✅ API总数: {len(apis)}")
    print(f"✅ 导入成功: {success_count}")
    print(f"✅ 导入失败: {error_count}")
    print(f"✅ 知识库集合: apis")
    print(f"\n💡 现在AI可以通过语义检索理解你的系统API了!")
    print(f"💡 在生成测试用例时,AI会自动检索相关API信息")
    print("=" * 60)
    
    return True


def test_api_search(query: str = "用户登录"):
    """
    测试API搜索功能
    
    Args:
        query: 搜索关键词
    """
    print(f"\n🔍 测试API搜索: '{query}'")
    print("-" * 60)
    
    km = KnowledgeManager()
    collection = km.kb.get_collection("apis")
    
    if not collection:
        print("❌ API集合不存在,请先导入Swagger")
        return
    
    try:
        results = collection.query(
            query_texts=[query],
            n_results=5
        )
        
        if results and results['ids']:
            print(f"✅ 找到 {len(results['ids'][0])} 个相关API:\n")
            
            for i, (api_id, distance) in enumerate(zip(results['ids'][0], results['distances'][0]), 1):
                metadata = results['metadatas'][0][i-1]
                similarity = 1 - distance
                
                print(f"{i}. {metadata['method']} {metadata['path']}")
                print(f"   摘要: {metadata['summary']}")
                print(f"   标签: {metadata['tags']}")
                print(f"   相似度: {similarity:.2%}")
                print()
        else:
            print("❌ 未找到相关API")
            
    except Exception as e:
        print(f"❌ 搜索失败: {e}")


if __name__ == "__main__":
    # 导入Swagger
    success = import_swagger_to_knowledge()
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 Swagger导入成功!")
        print("=" * 60)
        
        # 测试搜索
        print("\n" + "=" * 60)
        print("🧪 测试API搜索功能")
        print("=" * 60)
        
        test_queries = [
            "用户登录",
            "采购订单查询",
            "库存管理",
            "财务应收单",
            "产品信息"
        ]
        
        for query in test_queries:
            test_api_search(query)
            print()
