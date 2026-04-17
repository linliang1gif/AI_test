#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Self Healing 经验库

保存修复成功的模式，下次遇到相似错误直接复用，跳过 AI 生成。
"""

import uuid
import time
from typing import List, Dict, Any, Optional
from .db import get_knowledge_db

THRESHOLD_HIT = 0.80  # 直接应用历史修复


class HealingKnowledge:
    """Self Healing 经验库"""

    def __init__(self):
        self._db = get_knowledge_db()

    # ── 写入 ──────────────────────────────────────────────────

    def save_healing_pattern(
        self,
        error_type: str,
        error_snippet: str,
        fix_code: str,
        success: bool
    ) -> str:
        """将修复模式入库，返回 pattern_id"""
        pattern_id = str(uuid.uuid4())[:8]
        try:
            db = self._db
            if db is None:
                return pattern_id

            text = f"{error_type}\n{error_snippet}"

            collection = db.get_collection("healing_patterns")
            if collection is not None:
                embedding = db.get_embedding(text)
                if embedding:
                    collection.upsert(
                        ids=[pattern_id],
                        embeddings=[embedding],
                        metadatas=[{
                            "error_type": error_type,
                            "success": int(success),
                            "last_used": time.time()
                        }],
                        documents=[text[:500]]
                    )

            if db.conn:
                db.conn.execute(
                    """INSERT OR REPLACE INTO healing_records
                       (pattern_id, error_pattern, fix_pattern,
                        success_count, fail_count, last_used)
                       VALUES (?,?,?,?,?,?)""",
                    (
                        pattern_id,
                        text[:500],
                        fix_code[:2000],
                        1 if success else 0,
                        0 if success else 1,
                        time.time()
                    )
                )
                db.conn.commit()
                print(f"✅ Healing模式已入库: {pattern_id}")

        except Exception as e:
            print(f"⚠️ Healing入库失败（静默）: {e}")

        return pattern_id

    # ── 检索 ──────────────────────────────────────────────────

    def search_fix_pattern(self, error_info: Dict[str, Any], top_k: int = 3) -> List[Dict[str, Any]]:
        """检索历史修复方案"""
        results = []
        try:
            db = self._db
            if db is None:
                return results

            collection = db.get_collection("healing_patterns")
            if collection is None:
                return results

            query_text = f"{error_info.get('type', '')}\n{error_info.get('message', '')}"
            embedding = db.get_embedding(query_text)
            if not embedding:
                return results

            count = collection.count()
            if count == 0:
                return results

            query_result = collection.query(
                query_embeddings=[embedding],
                n_results=min(top_k, count),
                include=["metadatas", "distances"]
            )

            ids = query_result.get("ids", [[]])[0]
            distances = query_result.get("distances", [[]])[0]

            if db.conn:
                for pattern_id, distance in zip(ids, distances):
                    similarity = max(0.0, 1.0 - distance)
                    row = db.conn.execute(
                        "SELECT * FROM healing_records WHERE pattern_id=?", (pattern_id,)
                    ).fetchone()
                    if row:
                        total = (row["success_count"] or 0) + (row["fail_count"] or 0)
                        success_rate = row["success_count"] / total if total > 0 else 0.0
                        results.append({
                            "similarity": round(similarity, 4),
                            "pattern_id": pattern_id,
                            "fix_pattern": row["fix_pattern"],
                            "success_rate": round(success_rate, 4),
                            "applied_count": total
                        })

            results.sort(key=lambda x: x["similarity"], reverse=True)

        except Exception as e:
            print(f"⚠️ Healing检索失败（静默）: {e}")

        return results

    # ── 更新结果 ──────────────────────────────────────────────

    def update_pattern_result(self, pattern_id: str, success: bool):
        """更新修复成功/失败计数"""
        try:
            db = self._db
            if db is None or db.conn is None:
                return

            if success:
                db.conn.execute(
                    "UPDATE healing_records SET success_count=success_count+1, last_used=? WHERE pattern_id=?",
                    (time.time(), pattern_id)
                )
            else:
                db.conn.execute(
                    "UPDATE healing_records SET fail_count=fail_count+1, last_used=? WHERE pattern_id=?",
                    (time.time(), pattern_id)
                )
            db.conn.commit()

        except Exception as e:
            print(f"⚠️ 更新Healing结果失败（静默）: {e}")

    # ── 统计 ──────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        stats = {"total": 0, "hit_count": 0, "avg_success_rate": 0.0}
        try:
            db = self._db
            if db is None or db.conn is None:
                return stats

            rows = db.conn.execute(
                "SELECT success_count, fail_count FROM healing_records"
            ).fetchall()

            total = len(rows)
            if total == 0:
                return stats

            total_success = sum(r["success_count"] or 0 for r in rows)
            total_applied = sum((r["success_count"] or 0) + (r["fail_count"] or 0) for r in rows)

            stats["total"] = total
            stats["hit_count"] = total_applied
            stats["avg_success_rate"] = round(total_success / total_applied, 4) if total_applied > 0 else 0.0

        except Exception as e:
            print(f"⚠️ Healing统计失败（静默）: {e}")

        return stats
