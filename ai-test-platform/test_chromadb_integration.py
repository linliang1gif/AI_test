#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ChromaDB集成验证脚本
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from knowledge.db import get_knowledge_db


def test_chromadb_integration():
    """测试ChromaDB集成"""
    
    print("=" * 60)
    print("ChromaDB 集成验证")
    print("=" * 60)
    
    # 1. 初始化知识库
    print("\n1️⃣ 初始化知识库...")
    kb = get_knowledge_db()
    
    if kb is None:
        print("❌ 知识库初始化失败")
        return False
    
    print("✅ 知识库初始化成功")
    
    # 2. 测试SQLite
    print("\n2️⃣ 测试SQLite...")
    if kb.conn:
        cursor = kb.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"✅ SQLite可用，表数量: {len(tables)}")
        print(f"   表列表: {', '.join(tables)}")
    else:
        print("❌ SQLite不可用")
        return False
    
    # 3. 测试ChromaDB
    print("\n3️⃣ 测试ChromaDB...")
    test_collection = kb.get_collection("test_collection")
    
    if test_collection is None:
        print("❌ ChromaDB不可用")
        return False
    
    print("✅ ChromaDB可用")
    
    # 4. 测试向量存储
    print("\n4️⃣ 测试向量存储...")
    try:
        # 添加测试数据
        test_collection.add(
            documents=["这是一个测试文档", "这是另一个测试文档"],
            metadatas=[{"type": "test1"}, {"type": "test2"}],
            ids=["test1", "test2"]
        )
        print("✅ 向量存储成功")
        
        # 查询测试
        results = test_collection.query(
            query_texts=["测试"],
            n_results=2
        )
        print(f"✅ 向量查询成功，返回 {len(results['ids'][0])} 条结果")
        
        # 清理测试数据
        test_collection.delete(ids=["test1", "test2"])
        print("✅ 测试数据清理完成")
        
    except Exception as e:
        print(f"❌ 向量操作失败: {e}")
        return False
    
    # 5. 测试Embedding
    print("\n5️⃣ 测试Embedding...")
    embedding = kb.get_embedding("测试文本")
    
    if embedding and len(embedding) > 0:
        print(f"✅ Embedding生成成功，维度: {len(embedding)}")
    else:
        print("⚠️ Embedding生成失败（可选功能）")
    
    print("\n" + "=" * 60)
    print("✅ ChromaDB 集成验证完成!")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    success = test_chromadb_integration()
    sys.exit(0 if success else 1)
