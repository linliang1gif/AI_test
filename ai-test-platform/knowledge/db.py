#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
知识库核心初始化模块

ChromaDB 负责语义检索，SQLite 负责结构化查询。
懒加载设计：导入失败不影响主流程。
"""

import os
import sqlite3
from pathlib import Path
from typing import Optional

# 知识库数据目录
KB_DIR = Path(__file__).parent.parent / "data" / "knowledge_base"
CHROMA_DIR = KB_DIR / "chroma"
SQLITE_PATH = KB_DIR / "knowledge.db"


class KnowledgeDB:
    """知识库核心，管理 ChromaDB + SQLite"""

    def __init__(self):
        KB_DIR.mkdir(parents=True, exist_ok=True)
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)

        self._chroma_client = None
        self._sqlite_conn: Optional[sqlite3.Connection] = None
        self._embedding_fn = None

        self._init_chroma()
        self._init_sqlite()

    # ── ChromaDB ──────────────────────────────────────────────

    def _init_chroma(self):
        try:
            import chromadb
            self._chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
            print("✅ ChromaDB 初始化成功")
        except ImportError:
            print("⚠️ chromadb 未安装，向量检索不可用（pip install chromadb）")
        except Exception as e:
            print(f"⚠️ ChromaDB 初始化失败: {e}")

    def get_collection(self, name: str):
        """获取或创建 ChromaDB collection"""
        if self._chroma_client is None:
            return None
        try:
            return self._chroma_client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            print(f"⚠️ 获取 collection '{name}' 失败: {e}")
            return None

    # ── Embedding ─────────────────────────────────────────────

    def get_embedding(self, text: str) -> list:
        """获取文本向量，优先 Ollama nomic-embed-text，降级 sentence-transformers"""
        if not text or not text.strip():
            return []

        # 优先尝试 Ollama
        try:
            import requests
            resp = requests.post(
                "http://localhost:11434/api/embeddings",
                json={"model": "nomic-embed-text", "prompt": text},
                timeout=10
            )
            if resp.status_code == 200:
                return resp.json().get("embedding", [])
        except Exception:
            pass

        # 降级：sentence-transformers
        try:
            if self._embedding_fn is None:
                from sentence_transformers import SentenceTransformer
                self._embedding_fn = SentenceTransformer(
                    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
                )
            return self._embedding_fn.encode(text).tolist()
        except Exception:
            pass

        return []

    # ── SQLite ────────────────────────────────────────────────

    def _init_sqlite(self):
        try:
            self._sqlite_conn = sqlite3.connect(str(SQLITE_PATH), check_same_thread=False)
            self._sqlite_conn.row_factory = sqlite3.Row
            self._init_sqlite_tables()
            print("✅ SQLite 初始化成功")
        except Exception as e:
            print(f"⚠️ SQLite 初始化失败: {e}")

    def _init_sqlite_tables(self):
        ddl = """
        CREATE TABLE IF NOT EXISTS bug_records (
            bug_id      TEXT PRIMARY KEY,
            bug_type    TEXT,
            severity    TEXT,
            root_cause  TEXT,
            fix_suggestion TEXT,
            fix_success INTEGER DEFAULT 0,
            error_log   TEXT,
            timestamp   REAL
        );

        CREATE TABLE IF NOT EXISTS healing_records (
            pattern_id    TEXT PRIMARY KEY,
            error_pattern TEXT,
            fix_pattern   TEXT,
            success_count INTEGER DEFAULT 0,
            fail_count    INTEGER DEFAULT 0,
            last_used     REAL
        );

        CREATE TABLE IF NOT EXISTS testcase_records (
            tc_id          TEXT PRIMARY KEY,
            title          TEXT,
            module         TEXT,
            priority       TEXT,
            steps_json     TEXT,
            expected       TEXT,
            source         TEXT,
            quality_score  REAL DEFAULT 1.0,
            created_at     REAL
        );

        CREATE TABLE IF NOT EXISTS requirement_records (
            req_id      TEXT PRIMARY KEY,
            content     TEXT,
            module      TEXT,
            source_file TEXT,
            created_at  REAL
        );

        CREATE TABLE IF NOT EXISTS business_rule_records (
            rule_id       TEXT PRIMARY KEY,
            rule_text     TEXT,
            module        TEXT,
            source_req_id TEXT,
            created_at    REAL
        );

        CREATE TABLE IF NOT EXISTS req_api_mapping (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            req_id     TEXT,
            api_path   TEXT,
            api_method TEXT,
            confidence REAL,
            created_at REAL
        );
        """
        self._sqlite_conn.executescript(ddl)
        self._sqlite_conn.commit()

    @property
    def conn(self) -> Optional[sqlite3.Connection]:
        return self._sqlite_conn

    @property
    def available(self) -> bool:
        return self._sqlite_conn is not None


# 全局单例（懒加载）
_instance: Optional[KnowledgeDB] = None


def get_knowledge_db() -> Optional[KnowledgeDB]:
    global _instance
    if _instance is None:
        try:
            _instance = KnowledgeDB()
        except Exception as e:
            print(f"⚠️ 知识库初始化失败，降级为无知识库模式: {e}")
    return _instance
