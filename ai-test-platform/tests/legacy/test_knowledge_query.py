"""测试知识库查询"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from knowledge.knowledge_manager import KnowledgeManager

print("=" * 60)
print("🔍 测试知识库查询")
print("=" * 60)

km = KnowledgeManager()
collection = km.kb.get_collection("apis")

# 测试不同的查询
test_queries = [
    "付款单",
    "付款",
    "应付",
    "财务",
    "payment",
    "finance"
]

for query in test_queries:
    print(f"\n查询: '{query}'")
    try:
        results = collection.query(
            query_texts=[query],
            n_results=5
        )
        
        if results and results['ids'] and len(results['ids'][0]) > 0:
            print(f"✅ 找到 {len(results['ids'][0])} 个结果:")
            for i, (api_id, metadata) in enumerate(zip(results['ids'][0], results['metadatas'][0]), 1):
                print(f"  {i}. {metadata['method']} {metadata['path']}")
                print(f"     {metadata['summary']}")
        else:
            print("❌ 未找到结果")
    except Exception as e:
        print(f"❌ 查询失败: {e}")

print("\n" + "=" * 60)
