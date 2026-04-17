#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试用例知识库（第二阶段）

历史用例入库，AI 生成时检索避免重复，质量随项目积累提升。
"""

import uuid
import time
import json
from typing import List, Dict, Any, Tuple, Optional
from .db import get_knowledge_db

THRESHOLD_DEDUP = 0.90  # 去重阈值


class TestCaseKnowledge:
    """测试用例知识库"""

    def __init__(self):
        self._db = get_knowledge_db()

    # ── 写入 ──────────────────────────────────────────────────

    def save_testcase(
        self,
        testcase: Dict[str, Any],
        source: str,
        quality_score: float = 1.0
    ) -> str:
        """将测试用例入库，返回 tc_id"""
        tc_id = str(uuid.uuid4())[:8]
        try:
            db = self._db
            if db is None:
                return tc_id

            steps = testcase.get("steps", [])
            steps_text = " ".join(steps) if isinstance(steps, list) else str(steps)
            text = f"{testcase.get('title', '')} {steps_text} {testcase.get('expected_result', testcase.get('expected', ''))}"

            collection = db.get_collection("testcases")
            if collection is not None:
                embedding = db.get_embedding(text)
                if embedding:
                    collection.upsert(
                        ids=[tc_id],
                        embeddings=[embedding],
                        metadatas=[{
                            "module": testcase.get("module", ""),
                            "priority": testcase.get("priority", ""),
                            "source": source,
                            "quality_score": quality_score,
                            "created_at": time.time()
                        }],
                        documents=[text[:500]]
                    )

            if db.conn:
                db.conn.execute(
                    """INSERT OR REPLACE INTO testcase_records
                       (tc_id, title, module, priority, steps_json,
                        expected, source, quality_score, created_at)
                       VALUES (?,?,?,?,?,?,?,?,?)""",
                    (
                        tc_id,
                        testcase.get("title", ""),
                        testcase.get("module", ""),
                        testcase.get("priority", ""),
                        json.dumps(steps, ensure_ascii=False),
                        testcase.get("expected_result", testcase.get("expected", "")),
                        source,
                        quality_score,
                        time.time()
                    )
                )
                db.conn.commit()

        except Exception as e:
            print(f"⚠️ 用例入库失败（静默）: {e}")

        return tc_id

    def batch_save(self, testcases: List[Dict[str, Any]], source: str):
        """批量入库"""
        for tc in testcases:
            self.save_testcase(tc, source)
        print(f"✅ 批量入库 {len(testcases)} 条用例（来源: {source}）")

    # ── 检索 ──────────────────────────────────────────────────

    def search_similar_cases(
        self,
        query: str,
        module: str = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """检索相似测试用例"""
        results = []
        try:
            db = self._db
            if db is None:
                return results

            collection = db.get_collection("testcases")
            if collection is None:
                return results

            embedding = db.get_embedding(query)
            if not embedding:
                return results

            count = collection.count()
            if count == 0:
                return results

            where = {"module": module} if module else None
            query_kwargs = dict(
                query_embeddings=[embedding],
                n_results=min(top_k, count),
                include=["metadatas", "distances", "documents"]
            )
            if where:
                query_kwargs["where"] = where

            query_result = collection.query(**query_kwargs)

            ids = query_result.get("ids", [[]])[0]
            distances = query_result.get("distances", [[]])[0]
            metadatas = query_result.get("metadatas", [[]])[0]

            if db.conn:
                for tc_id, distance, meta in zip(ids, distances, metadatas):
                    similarity = max(0.0, 1.0 - distance)
                    row = db.conn.execute(
                        "SELECT * FROM testcase_records WHERE tc_id=?", (tc_id,)
                    ).fetchone()
                    if row:
                        steps = []
                        try:
                            steps = json.loads(row["steps_json"] or "[]")
                        except Exception:
                            pass
                        results.append({
                            "similarity": round(similarity, 4),
                            "tc_id": tc_id,
                            "title": row["title"],
                            "module": row["module"],
                            "priority": row["priority"],
                            "steps": steps,
                            "expected_result": row["expected"],
                            "source": row["source"],
                            "quality_score": row["quality_score"]
                        })

            results.sort(key=lambda x: x["similarity"], reverse=True)

        except Exception as e:
            print(f"⚠️ 用例检索失败（静默）: {e}")

        return results

    # ── 去重 ──────────────────────────────────────────────────

    def deduplicate(
        self,
        new_cases: List[Dict[str, Any]],
        threshold: float = THRESHOLD_DEDUP
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        去重，返回 (unique_cases, duplicate_cases)
        """
        unique, duplicates = [], []
        try:
            db = self._db
            if db is None:
                return new_cases, []

            collection = db.get_collection("testcases")
            if collection is None or collection.count() == 0:
                return new_cases, []

            for tc in new_cases:
                steps = tc.get("steps", [])
                steps_text = " ".join(steps) if isinstance(steps, list) else str(steps)
                text = f"{tc.get('title', '')} {steps_text} {tc.get('expected_result', tc.get('expected', ''))}"
                embedding = db.get_embedding(text)
                if not embedding:
                    unique.append(tc)
                    continue

                result = collection.query(
                    query_embeddings=[embedding],
                    n_results=1,
                    include=["distances"]
                )
                distances = result.get("distances", [[]])[0]
                if distances and (1.0 - distances[0]) >= threshold:
                    duplicates.append(tc)
                else:
                    unique.append(tc)

            if duplicates:
                print(f"✅ 去重过滤 {len(duplicates)} 条重复用例，保留 {len(unique)} 条")

        except Exception as e:
            print(f"⚠️ 去重失败（静默），全部保留: {e}")
            return new_cases, []

        return unique, duplicates

    # ── 统计 ──────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        stats = {"total": 0, "by_module": {}, "avg_quality_score": 0.0}
        try:
            db = self._db
            if db is None or db.conn is None:
                return stats

            rows = db.conn.execute(
                "SELECT module, quality_score FROM testcase_records"
            ).fetchall()

            total = len(rows)
            if total == 0:
                return stats

            by_module: Dict[str, int] = {}
            total_quality = 0.0
            for row in rows:
                m = row["module"] or "未知"
                by_module[m] = by_module.get(m, 0) + 1
                total_quality += row["quality_score"] or 1.0

            stats["total"] = total
            stats["by_module"] = by_module
            stats["avg_quality_score"] = round(total_quality / total, 4)

        except Exception as e:
            print(f"⚠️ 用例统计失败（静默）: {e}")

        return stats
