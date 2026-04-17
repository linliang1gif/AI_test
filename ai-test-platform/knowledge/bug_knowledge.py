#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Bug 知识库

保存 Bug 分析结果，支持相似 Bug 检索，避免重复 AI 分析。
"""

import uuid
import time
import json
from typing import List, Dict, Any, Optional
from .db import get_knowledge_db

# 相似度阈值
THRESHOLD_HIT = 0.85    # 直接命中，跳过 AI
THRESHOLD_HINT = 0.60   # 注入 prompt 辅助分析


class BugKnowledge:
    """Bug 知识库"""

    def __init__(self):
        self._db = get_knowledge_db()

    # ── 写入 ──────────────────────────────────────────────────

    def save_bug(
        self,
        error_log: str,
        analysis_result: Dict[str, Any],
        fix_applied: str = "",
        fix_success: bool = False
    ) -> str:
        """将 Bug 分析结果入库，返回 bug_id"""
        bug_id = str(uuid.uuid4())[:8]
        try:
            db = self._db
            if db is None:
                return bug_id

            # 向量存入 ChromaDB
            collection = db.get_collection("bug_cases")
            if collection is not None:
                embedding = db.get_embedding(error_log)
                if embedding:
                    collection.upsert(
                        ids=[bug_id],
                        embeddings=[embedding],
                        metadatas=[{
                            "bug_type": analysis_result.get("bug_type", ""),
                            "severity": analysis_result.get("severity", ""),
                            "fix_success": int(fix_success),
                            "timestamp": time.time()
                        }],
                        documents=[error_log[:500]]
                    )

            # 结构化存入 SQLite
            if db.conn:
                db.conn.execute(
                    """INSERT OR REPLACE INTO bug_records
                       (bug_id, bug_type, severity, root_cause, fix_suggestion,
                        fix_success, error_log, timestamp)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (
                        bug_id,
                        analysis_result.get("bug_type", ""),
                        analysis_result.get("severity", ""),
                        analysis_result.get("root_cause", ""),
                        analysis_result.get("fix_suggestion", ""),
                        int(fix_success),
                        error_log[:1000],
                        time.time()
                    )
                )
                db.conn.commit()
                print(f"✅ Bug已入库: {bug_id}")

        except Exception as e:
            print(f"⚠️ Bug入库失败（静默）: {e}")

        return bug_id

    # ── 检索 ──────────────────────────────────────────────────

    def search_similar_bugs(self, error_log: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """检索相似 Bug，返回列表（含 similarity 字段）"""
        results = []
        try:
            db = self._db
            if db is None:
                return results

            collection = db.get_collection("bug_cases")
            if collection is None:
                return results

            embedding = db.get_embedding(error_log)
            if not embedding:
                return results

            count = collection.count()
            if count == 0:
                return results

            query_result = collection.query(
                query_embeddings=[embedding],
                n_results=min(top_k, count),
                include=["metadatas", "distances", "documents"]
            )

            ids = query_result.get("ids", [[]])[0]
            distances = query_result.get("distances", [[]])[0]
            metadatas = query_result.get("metadatas", [[]])[0]

            if db.conn:
                for bug_id, distance, meta in zip(ids, distances, metadatas):
                    similarity = max(0.0, 1.0 - distance)
                    row = db.conn.execute(
                        "SELECT * FROM bug_records WHERE bug_id=?", (bug_id,)
                    ).fetchone()
                    if row:
                        results.append({
                            "similarity": round(similarity, 4),
                            "bug_id": bug_id,
                            "bug_type": row["bug_type"],
                            "severity": row["severity"],
                            "root_cause": row["root_cause"],
                            "fix_suggestion": row["fix_suggestion"],
                            "fix_success": bool(row["fix_success"]),
                            "timestamp": row["timestamp"]
                        })

            results.sort(key=lambda x: x["similarity"], reverse=True)

        except Exception as e:
            print(f"⚠️ Bug检索失败（静默）: {e}")

        return results

    # ── 统计 ──────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """返回知识库统计"""
        stats = {"total": 0, "by_type": {}, "fix_success_rate": 0.0, "recent_7days": 0}
        try:
            db = self._db
            if db is None or db.conn is None:
                return stats

            rows = db.conn.execute("SELECT bug_type, fix_success, timestamp FROM bug_records").fetchall()
            total = len(rows)
            if total == 0:
                return stats

            by_type: Dict[str, int] = {}
            success_count = 0
            cutoff = time.time() - 7 * 86400

            for row in rows:
                bt = row["bug_type"] or "未知"
                by_type[bt] = by_type.get(bt, 0) + 1
                if row["fix_success"]:
                    success_count += 1
                if row["timestamp"] and row["timestamp"] >= cutoff:
                    stats["recent_7days"] += 1

            stats["total"] = total
            stats["by_type"] = by_type
            stats["fix_success_rate"] = round(success_count / total, 4)

        except Exception as e:
            print(f"⚠️ Bug统计失败（静默）: {e}")

        return stats
