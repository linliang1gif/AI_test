#!/usr/bin/env python3
"""只测试API搜索"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from utils.knowledge_prompt_helper import get_knowledge_helper


def test():
    print("=" * 60)
    print("🧪 测试API搜索")
    print("=" * 60)
    
    helper = get_knowledge_helper()
    print("✅ Helper已加载")
    
    print("\n🔍 搜索: 采购订单")
    apis = helper.search_related_apis("采购订单", top_k=5)
    
    print(f"✅ 找到 {len(apis)} 个API:")
    for i, api in enumerate(apis, 1):
        print(f"{i}. {api['method']} {api['path']}")
        print(f"   {api['summary']}")
        print(f"   相似度: {api.get('similarity', 0):.2%}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test()
