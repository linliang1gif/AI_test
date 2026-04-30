#!/usr/bin/env python3
"""验证ChromaDB中的数据"""
import chromadb
from chromadb.config import Settings

def main():
    print("=" * 60)
    print("🔍 验证ChromaDB数据")
    print("=" * 60)
    
    # 初始化ChromaDB
    client = chromadb.PersistentClient(
        path="./chroma_db",
        settings=Settings(anonymized_telemetry=False)
    )
    
    # 获取所有collection
    collections = client.list_collections()
    print(f"\n📚 Collections数量: {len(collections)}")
    
    for collection in collections:
        print(f"\n📦 Collection: {collection.name}")
        count = collection.count()
        print(f"   - 文档数量: {count}")
        
        if count > 0:
            # 获取前5条数据
            results = collection.get(limit=5, include=["metadatas", "documents"])
            print(f"   - 前5条数据:")
            for i, (doc, meta) in enumerate(zip(results['documents'], results['metadatas']), 1):
                print(f"      {i}. {meta.get('type', 'unknown')}: {doc[:100]}...")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
