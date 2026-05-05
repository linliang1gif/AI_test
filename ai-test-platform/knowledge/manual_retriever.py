#!/usr/bin/env python3
"""操作手册知识库检索 — 为 AI 生成测试用例提供业务上下文"""

from typing import List, Optional
from knowledge.db import get_knowledge_db

COLLECTION_NAME = "operation_manual"


def retrieve_manual_context(query: str, n_results: int = 5) -> Optional[str]:
    """
    根据查询语句从操作手册知识库检索相关片段，拼接为 prompt 上下文。

    Args:
        query: 查询文本（需求描述、模块名等）
        n_results: 返回条数

    Returns:
        拼接后的上下文字符串，无结果时返回 None
    """
    kb = get_knowledge_db()
    if kb is None or kb._chroma_client is None:
        return None

    try:
        collection = kb._chroma_client.get_collection(COLLECTION_NAME)
    except Exception:
        return None

    if collection is None or collection.count() == 0:
        return None

    try:
        results = collection.query(query_texts=[query], n_results=n_results)
    except Exception:
        return None

    docs = results.get("documents", [[]])[0]
    if not docs:
        return None

    # 去重 + 拼接
    seen = set()
    unique = []
    for d in docs:
        key = d[:100]
        if key not in seen:
            seen.add(key)
            unique.append(d)

    context = "\n---\n".join(unique)
    return context


def retrieve_for_modules(module_names: List[str], n_per_module: int = 3) -> Optional[str]:
    """
    针对多个模块名分别检索，合并去重。

    Args:
        module_names: 模块名列表，如 ["采购管理", "仓储管理"]
        n_per_module: 每个模块检索条数

    Returns:
        合并后的上下文字符串
    """
    if not module_names:
        return None

    all_docs = []
    seen = set()

    for name in module_names[:10]:  # 最多10个模块
        ctx = retrieve_manual_context(name, n_results=n_per_module)
        if ctx:
            for seg in ctx.split("\n---\n"):
                key = seg[:100]
                if key not in seen:
                    seen.add(key)
                    all_docs.append(seg)

    if not all_docs:
        return None

    # 限制总长度
    result = ""
    for doc in all_docs:
        if len(result) + len(doc) > 6000:
            break
        result += doc + "\n---\n"

    return result.rstrip("\n---\n") if result else None
