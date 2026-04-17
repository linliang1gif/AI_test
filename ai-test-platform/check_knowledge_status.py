#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from knowledge.knowledge_manager import get_knowledge_manager

km = get_knowledge_manager()
stats = km.get_knowledge_stats()

print("📊 知识库状态:")
print(f"   - APIs: {stats.get('apis', {}).get('total', 0)}")
print(f"   - Backend代码: {stats.get('code', {}).get('backend', 0)}")
print(f"   - Frontend代码: {stats.get('code', {}).get('frontend', 0)}")
