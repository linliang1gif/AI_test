#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
业务规则知识库（第三阶段）

需求条目持久化，建立需求×接口双向映射，暴露覆盖盲区。
"""

import uuid
import time
from typing import List, Dict, Any, Optional
from .db import get_knowledge_db

THRESHOLD_MAPPING = 0.70  # 需求-接口映射阈值


class BusinessKnowledge:
    """业务规则知识库"""

    def __init__(self):
        self._db = get_knowledge_db()

    # ── 需求入库 ──────────────────────────────────────────────

    def save_requirement(
        self,
        req_id: str,
        content: str,
        module: str,
        source_file: str
    ) -> str:
        try:
            db = self._db
            if db is None:
                return req_id

            collection = db.get_collection("requirements")
            if collection is not None:
                embedding = db.get_embedding(content)
                if embedding:
                    collection.upsert(
                        ids=[req_id],
                        embeddings=[embedding],
                        metadatas=[{"module": module, "source_file": source_file}],
                        documents=[content[:500]]
                    )

            if db.conn:
                db.conn.execute(
                    """INSERT OR REPLACE INTO requirement_records
                       (req_id, content, module, source_file, created_at)
                       VALUES (?,?,?,?,?)""",
                    (req_id, content[:2000], module, source_file, time.time())
                )
                db.conn.commit()

        except Exception as e:
            print(f"⚠️ 需求入库失败（静默）: {e}")

        return req_id

    # ── 业务规则入库 ──────────────────────────────────────────

    def save_business_rule(
        self,
        rule_text: str,
        module: str,
        source_req_id: str = ""
    ) -> str:
        rule_id = str(uuid.uuid4())[:8]
        try:
            db = self._db
            if db is None:
                return rule_id

            collection = db.get_collection("business_rules")
            if collection is not None:
                embedding = db.get_embedding(rule_text)
                if embedding:
                    collection.upsert(
                        ids=[rule_id],
                        embeddings=[embedding],
                        metadatas=[{"module": module, "source_req_id": source_req_id}],
                        documents=[rule_text[:500]]
                    )

            if db.conn:
                db.conn.execute(
                    """INSERT OR REPLACE INTO business_rule_records
                       (rule_id, rule_text, module, source_req_id, created_at)
                       VALUES (?,?,?,?,?)""",
                    (rule_id, rule_text[:1000], module, source_req_id, time.time())
                )
                db.conn.commit()

        except Exception as e:
            print(f"⚠️ 业务规则入库失败（静默）: {e}")

        return rule_id

    # ── 检索业务规则 ──────────────────────────────────────────

    def search_relevant_rules(
        self,
        query: str,
        module: str = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        results = []
        try:
            db = self._db
            if db is None:
                return results

            collection = db.get_collection("business_rules")
            if collection is None or collection.count() == 0:
                return results

            embedding = db.get_embedding(query)
            if not embedding:
                return results

            count = collection.count()
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
            docs = query_result.get("documents", [[]])[0]
            metadatas = query_result.get("metadatas", [[]])[0]

            for rule_id, distance, doc, meta in zip(ids, distances, docs, metadatas):
                similarity = max(0.0, 1.0 - distance)
                results.append({
                    "similarity": round(similarity, 4),
                    "rule_id": rule_id,
                    "rule_text": doc,
                    "module": meta.get("module", ""),
                    "source_req_id": meta.get("source_req_id", "")
                })

            results.sort(key=lambda x: x["similarity"], reverse=True)

        except Exception as e:
            print(f"⚠️ 业务规则检索失败（静默）: {e}")

        return results

    # ── 需求-接口映射 ─────────────────────────────────────────

    def save_req_api_mapping(
        self,
        req_id: str,
        api_path: str,
        api_method: str,
        confidence: float
    ):
        try:
            db = self._db
            if db is None or db.conn is None:
                return

            # 避免重复映射
            existing = db.conn.execute(
                "SELECT id FROM req_api_mapping WHERE req_id=? AND api_path=? AND api_method=?",
                (req_id, api_path, api_method)
            ).fetchone()

            if not existing:
                db.conn.execute(
                    """INSERT INTO req_api_mapping
                       (req_id, api_path, api_method, confidence, created_at)
                       VALUES (?,?,?,?,?)""",
                    (req_id, api_path, api_method, confidence, time.time())
                )
                db.conn.commit()

        except Exception as e:
            print(f"⚠️ 需求-接口映射失败（静默）: {e}")

    def get_unmapped_requirements(self) -> List[Dict[str, Any]]:
        """返回没有接口映射的需求条目"""
        results = []
        try:
            db = self._db
            if db is None or db.conn is None:
                return results

            rows = db.conn.execute(
                """SELECT r.req_id, r.content, r.module, r.source_file
                   FROM requirement_records r
                   WHERE r.req_id NOT IN (
                       SELECT DISTINCT req_id FROM req_api_mapping
                   )"""
            ).fetchall()

            for row in rows:
                results.append({
                    "req_id": row["req_id"],
                    "content": row["content"],
                    "module": row["module"],
                    "source_file": row["source_file"]
                })

        except Exception as e:
            print(f"⚠️ 未映射需求查询失败（静默）: {e}")

        return results

    def get_coverage_report(self) -> Dict[str, Any]:
        """返回需求-接口覆盖率报告"""
        report = {
            "total_reqs": 0,
            "mapped_reqs": 0,
            "unmapped_reqs": 0,
            "coverage_rate": 0.0,
            "unmapped_list": []
        }
        try:
            db = self._db
            if db is None or db.conn is None:
                return report

            total = db.conn.execute(
                "SELECT COUNT(*) as cnt FROM requirement_records"
            ).fetchone()["cnt"]

            mapped = db.conn.execute(
                "SELECT COUNT(DISTINCT req_id) as cnt FROM req_api_mapping"
            ).fetchone()["cnt"]

            unmapped_list = self.get_unmapped_requirements()

            report["total_reqs"] = total
            report["mapped_reqs"] = mapped
            report["unmapped_reqs"] = total - mapped
            report["coverage_rate"] = round(mapped / total, 4) if total > 0 else 0.0
            report["unmapped_list"] = unmapped_list

        except Exception as e:
            print(f"⚠️ 覆盖率报告失败（静默）: {e}")

        return report

    def get_stats(self) -> Dict[str, Any]:
        stats = {"total_requirements": 0, "total_rules": 0, "coverage_rate": 0.0}
        try:
            db = self._db
            if db is None or db.conn is None:
                return stats

            stats["total_requirements"] = db.conn.execute(
                "SELECT COUNT(*) as cnt FROM requirement_records"
            ).fetchone()["cnt"]

            stats["total_rules"] = db.conn.execute(
                "SELECT COUNT(*) as cnt FROM business_rule_records"
            ).fetchone()["cnt"]

            report = self.get_coverage_report()
            stats["coverage_rate"] = report["coverage_rate"]

        except Exception as e:
            print(f"⚠️ 业务统计失败（静默）: {e}")

        return stats
