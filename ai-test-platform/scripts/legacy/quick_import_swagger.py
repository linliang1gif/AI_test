"""快速导入Swagger到知识库"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from parser.swagger_parser import SwaggerParser
from knowledge.knowledge_manager import KnowledgeManager

print("=" * 60)
print("🚀 快速导入Swagger到知识库")
print("=" * 60)

# 1. 加载Swagger
print("\n📂 加载Swagger文件...")
parser = SwaggerParser()
swagger_data = parser.load_swagger_file("swaggerApi (1).json")
apis = parser.parse_apis()
print(f"✅ 解析了 {len(apis)} 个API")

# 2. 获取知识库
print("\n💾 连接知识库...")
km = KnowledgeManager()
if not km.kb or not km.kb.available:
    print("❌ 知识库不可用")
    sys.exit(1)

collection = km.kb.get_collection("apis")
print("✅ 知识库已连接")

# 3. 批量导入(每100个一批)
print(f"\n📥 开始导入 {len(apis)} 个API...")
batch_size = 100
success_count = 0

for i in range(0, len(apis), batch_size):
    batch = apis[i:i+batch_size]
    
    documents = []
    metadatas = []
    ids = []
    
    for api in batch:
        api_id = f"{api['method']}_{api['path'].replace('/', '_')}"
        
        doc_text = f"""
API: {api['method']} {api['path']}
摘要: {api.get('summary', '')}
描述: {api.get('description', '')}
标签: {', '.join(api.get('tags', []))}
        """.strip()
        
        metadata = {
            "api_id": api_id,
            "method": api['method'],
            "path": api['path'],
            "summary": api.get('summary', ''),
            "tags": ','.join(api.get('tags', [])),
            "source": "swagger_import"
        }
        
        documents.append(doc_text)
        metadatas.append(metadata)
        ids.append(api_id)
    
    try:
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        success_count += len(batch)
        print(f"  ✅ 已导入 {success_count}/{len(apis)}")
    except Exception as e:
        print(f"  ⚠️  批次导入失败: {e}")

print(f"\n✅ 导入完成! 成功导入 {success_count} 个API")

# 4. 测试查询
print("\n🔍 测试查询...")
test_query = "付款单"
results = collection.query(query_texts=[test_query], n_results=3)

if results and results['ids']:
    print(f"✅ 查询'{test_query}'找到 {len(results['ids'][0])} 个结果:")
    for i, metadata in enumerate(results['metadatas'][0], 1):
        print(f"  {i}. {metadata['method']} {metadata['path']}")
        print(f"     {metadata['summary']}")

print("\n" + "=" * 60)
print("🎉 知识库导入成功!")
print("=" * 60)
