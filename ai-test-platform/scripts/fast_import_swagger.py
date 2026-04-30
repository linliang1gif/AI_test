#!/usr/bin/env python3
"""快速导入Swagger - 批量处理"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from parser.swagger_parser import SwaggerParser
from knowledge.knowledge_manager import KnowledgeManager


def fast_import():
    print("=" * 60)
    print("🚀 快速导入Swagger")
    print("=" * 60)
    
    # 1. 解析Swagger
    parser = SwaggerParser()
    swagger_data = parser.load_swagger_file("swaggerApi (1).json")
    apis = parser.parse_apis()
    
    print(f"✅ 解析完成: {len(apis)} 个API")
    
    # 2. 准备批量数据
    print(f"\n💾 准备批量导入...")
    km = KnowledgeManager()
    collection = km.kb.get_collection("apis")
    
    if not collection:
        print("❌ 集合不可用")
        return
    
    # 批量准备数据
    documents = []
    metadatas = []
    ids = []
    
    for i, api in enumerate(apis):
        api_id = f"api_{i}_{api['method']}_{api['path'].replace('/', '_')}"
        
        doc_text = f"{api['method']} {api['path']} {api.get('summary', '')} {','.join(api.get('tags', []))}"
        
        metadata = {
            "method": api['method'],
            "path": api['path'],
            "summary": api.get('summary', ''),
            "tags": ','.join(api.get('tags', [])),
            "type": "api"
        }
        
        documents.append(doc_text)
        metadatas.append(metadata)
        ids.append(api_id)
    
    # 3. 批量导入 (分批,每批100个)
    batch_size = 100
    total = len(documents)
    
    print(f"\n📦 批量导入 (每批{batch_size}个)...")
    
    for i in range(0, total, batch_size):
        end = min(i + batch_size, total)
        batch_docs = documents[i:end]
        batch_metas = metadatas[i:end]
        batch_ids = ids[i:end]
        
        try:
            collection.add(
                documents=batch_docs,
                metadatas=batch_metas,
                ids=batch_ids
            )
            print(f"   ✅ 已导入 {end}/{total}")
        except Exception as e:
            print(f"   ❌ 批次 {i}-{end} 失败: {e}")
    
    # 4. 验证
    print(f"\n🔍 验证导入...")
    count = collection.count()
    print(f"✅ 集合中共有 {count} 个文档")
    
    # 测试搜索
    results = collection.query(
        query_texts=["用户登录"],
        n_results=3
    )
    
    if results and results['ids']:
        print(f"\n✅ 搜索测试通过:")
        for i, meta in enumerate(results['metadatas'][0], 1):
            print(f"   {i}. {meta['method']} {meta['path']} - {meta['summary']}")
    
    print(f"\n" + "=" * 60)
    print("🎉 导入完成!")
    print("=" * 60)


if __name__ == "__main__":
    fast_import()
