#!/usr/bin/env python3
"""将蓝点操作手册导入知识库（ChromaDB）"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.document_parser import parse_document
from knowledge.db import get_knowledge_db

DOC_PATH = r"E:\企业微信\WXWork\1688849993696418\Cache\File\2026-05\蓝点新生 操作手册  V1.1 260121.docx"
COLLECTION_NAME = "operation_manual"
CHUNK_SIZE = 800  # 每段约800字，适合向量检索


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> list:
    """按段落分块，保持语义完整"""
    paragraphs = text.split('\n')
    chunks = []
    current = ""
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        if len(current) + len(p) > chunk_size and current:
            chunks.append(current.strip())
            current = p
        else:
            current += "\n" + p if current else p
    if current.strip():
        chunks.append(current.strip())
    return chunks


def main():
    # 1. 解析文档
    print(f"📄 解析文档: {DOC_PATH}")
    text = parse_document(DOC_PATH)
    print(f"   文档长度: {len(text)} 字符")

    # 2. 分块
    chunks = chunk_text(text)
    print(f"   分块数量: {len(chunks)}")

    # 3. 写入 ChromaDB
    kb = get_knowledge_db()
    if not kb or not kb.available:
        print("❌ ChromaDB 不可用，请安装: pip install chromadb")
        return

    collection = kb.get_collection(COLLECTION_NAME)
    if collection is None:
        print("❌ 无法创建 collection")
        return

    # 清除旧数据
    try:
        existing = collection.count()
        if existing > 0:
            print(f"   清除旧数据: {existing} 条")
            collection.delete(where={"source": "operation_manual"})
    except Exception:
        pass

    # 写入
    ids = [f"manual_{i:04d}" for i in range(len(chunks))]
    metadatas = [{"source": "operation_manual", "doc": "蓝点新生操作手册V1.1", "chunk_index": i} for i in range(len(chunks))]

    # ChromaDB 批量写入限制，分批
    batch = 50
    for start in range(0, len(chunks), batch):
        end = min(start + batch, len(chunks))
        collection.add(
            ids=ids[start:end],
            documents=chunks[start:end],
            metadatas=metadatas[start:end],
        )
        print(f"   写入 {start+1}-{end} / {len(chunks)}")

    final_count = collection.count()
    print(f"\n✅ 导入完成! collection='{COLLECTION_NAME}', 总条目: {final_count}")

    # 4. 验证：测试检索
    print("\n--- 检索测试 ---")
    for q in ["采购订单怎么操作", "如何新增产品", "仓库出库流程"]:
        results = collection.query(query_texts=[q], n_results=2)
        print(f"\nQ: {q}")
        for doc in results['documents'][0]:
            print(f"  → {doc[:120]}...")


if __name__ == "__main__":
    main()
