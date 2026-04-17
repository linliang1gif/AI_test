#!/usr/bin/env python3
"""检查知识库导入状态"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from knowledge.knowledge_manager import KnowledgeManager


def check_status():
    print("=" * 60)
    print("📊 知识库导入状态")
    print("=" * 60)
    
    km = KnowledgeManager()
    
    # 检查各个collection
    collections = {
        'apis': 'API接口',
        'backend_code': '后端代码',
        'frontend_code': '前端代码'
    }
    
    for coll_name, coll_desc in collections.items():
        try:
            collection = km.kb.get_collection(coll_name)
            if collection:
                count = collection.count()
                print(f"\n✅ {coll_desc} ({coll_name}): {count} 个文档")
            else:
                print(f"\n❌ {coll_desc} ({coll_name}): 集合不存在")
        except Exception as e:
            print(f"\n⚠️ {coll_desc} ({coll_name}): 检查失败 - {e}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    check_status()
