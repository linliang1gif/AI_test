#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
知识库管理器 - AI闭环的核心
实现: 自动入库 + 智能检索 + 反馈闭环
"""

import time
import json
import hashlib
from typing import Dict, List, Any, Optional
from knowledge.db import get_knowledge_db


class KnowledgeManager:
    """知识库管理器 - 打通AI闭环"""
    
    def __init__(self):
        self.kb = get_knowledge_db()
        
    # ═══════════════════════════════════════════════════════
    # 1. 自动入库 (测试执行后自动写入)
    # ═══════════════════════════════════════════════════════
    
    def record_test_failure(self, test_case: Dict, error_info: Dict) -> str:
        """
        记录测试失败 - 自动入库
        
        Args:
            test_case: 测试用例信息
            error_info: 错误信息 {error_type, error_message, stack_trace}
            
        Returns:
            bug_id: Bug记录ID
        """
        if not self.kb or not self.kb.available:
            return None
            
        # 生成Bug ID
        bug_id = self._generate_bug_id(test_case, error_info)
        
        # 提取关键信息
        bug_type = error_info.get('error_type', 'Unknown')
        error_msg = error_info.get('error_message', '')
        stack_trace = error_info.get('stack_trace', '')
        
        # 分析根因(简单版)
        root_cause = self._analyze_root_cause(error_msg, stack_trace)
        
        # 写入SQLite
        try:
            self.kb.conn.execute("""
                INSERT OR REPLACE INTO bug_records 
                (bug_id, bug_type, severity, root_cause, error_log, timestamp, fix_success)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                bug_id,
                bug_type,
                self._determine_severity(error_info),
                root_cause,
                json.dumps({'error': error_msg, 'stack': stack_trace}, ensure_ascii=False),
                time.time(),
                0  # 初始未修复
            ))
            self.kb.conn.commit()
            
            # 同时写入ChromaDB(向量化)
            self._store_bug_vector(bug_id, root_cause, error_msg)
            
            print(f"✅ Bug已入库: {bug_id}")
            return bug_id
            
        except Exception as e:
            print(f"❌ Bug入库失败: {e}")
            return None
    
    def record_test_case(self, test_case: Dict) -> bool:
        """
        记录测试用例 - 自动入库
        
        Args:
            test_case: 测试用例完整信息
            
        Returns:
            是否成功
        """
        if not self.kb or not self.kb.available:
            return False
            
        try:
            tc_id = test_case.get('id', '')
            title = test_case.get('title', '')
            module = test_case.get('module', '')
            priority = test_case.get('priority', 'medium')
            steps = test_case.get('steps', [])
            expected = test_case.get('expected_result', '')
            source = test_case.get('source', 'manual')
            
            # 写入SQLite
            self.kb.conn.execute("""
                INSERT OR REPLACE INTO testcase_records
                (tc_id, title, module, priority, steps_json, expected, source, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tc_id, title, module, priority,
                json.dumps(steps, ensure_ascii=False),
                expected, source, time.time()
            ))
            self.kb.conn.commit()
            
            # 写入ChromaDB(向量化)
            self._store_testcase_vector(tc_id, title, expected)
            
            return True
            
        except Exception as e:
            print(f"❌ 测试用例入库失败: {e}")
            return False
    
    def record_healing_success(self, bug_id: str, fix_pattern: str, 
                              error_pattern: str) -> bool:
        """
        记录修复成功 - 学习修复模式
        
        Args:
            bug_id: Bug ID
            fix_pattern: 修复模式(代码/配置)
            error_pattern: 错误模式
            
        Returns:
            是否成功
        """
        if not self.kb or not self.kb.available:
            return False
            
        try:
            # 更新Bug记录为已修复
            self.kb.conn.execute("""
                UPDATE bug_records 
                SET fix_success = 1, fix_suggestion = ?
                WHERE bug_id = ?
            """, (fix_pattern, bug_id))
            
            # 生成模式ID
            pattern_id = hashlib.md5(error_pattern.encode()).hexdigest()[:16]
            
            # 更新或插入修复模式
            cursor = self.kb.conn.execute("""
                SELECT success_count FROM healing_records WHERE pattern_id = ?
            """, (pattern_id,))
            
            row = cursor.fetchone()
            if row:
                # 已存在,增加成功次数
                self.kb.conn.execute("""
                    UPDATE healing_records 
                    SET success_count = success_count + 1, last_used = ?
                    WHERE pattern_id = ?
                """, (time.time(), pattern_id))
            else:
                # 新模式,插入
                self.kb.conn.execute("""
                    INSERT INTO healing_records
                    (pattern_id, error_pattern, fix_pattern, success_count, last_used)
                    VALUES (?, ?, ?, 1, ?)
                """, (pattern_id, error_pattern, fix_pattern, time.time()))
            
            self.kb.conn.commit()
            
            # 写入ChromaDB
            self._store_healing_vector(pattern_id, error_pattern, fix_pattern)
            
            print(f"✅ 修复模式已学习: {pattern_id}")
            return True
            
        except Exception as e:
            print(f"❌ 修复模式记录失败: {e}")
            return False
    
    # ═══════════════════════════════════════════════════════
    # 2. 智能检索 (失败时自动查询相似案例)
    # ═══════════════════════════════════════════════════════
    
    def find_similar_bugs(self, error_message: str, top_k: int = 5) -> List[Dict]:
        """
        查找相似Bug - 语义检索
        
        Args:
            error_message: 错误信息
            top_k: 返回前K个结果
            
        Returns:
            相似Bug列表
        """
        if not self.kb or not self.kb.available:
            return []
        
        results = []
        
        # 1. ChromaDB语义检索
        collection = self.kb.get_collection("bugs")
        if collection:
            try:
                chroma_results = collection.query(
                    query_texts=[error_message],
                    n_results=top_k
                )
                
                if chroma_results and chroma_results['ids']:
                    bug_ids = chroma_results['ids'][0]
                    distances = chroma_results['distances'][0]
                    
                    # 从SQLite获取详细信息
                    for bug_id, distance in zip(bug_ids, distances):
                        cursor = self.kb.conn.execute("""
                            SELECT * FROM bug_records WHERE bug_id = ?
                        """, (bug_id,))
                        row = cursor.fetchone()
                        if row:
                            results.append({
                                'bug_id': row['bug_id'],
                                'bug_type': row['bug_type'],
                                'root_cause': row['root_cause'],
                                'fix_suggestion': row['fix_suggestion'],
                                'fix_success': row['fix_success'],
                                'similarity': 1 - distance,  # 转换为相似度
                                'source': 'chromadb'
                            })
            except Exception as e:
                print(f"⚠️ ChromaDB检索失败: {e}")
        
        # 2. SQLite关键词检索(补充)
        if len(results) < top_k:
            try:
                # 提取关键词
                keywords = self._extract_keywords(error_message)
                if keywords:
                    keyword_pattern = '%' + '%'.join(keywords) + '%'
                    cursor = self.kb.conn.execute("""
                        SELECT * FROM bug_records 
                        WHERE root_cause LIKE ? OR error_log LIKE ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (keyword_pattern, keyword_pattern, top_k - len(results)))
                    
                    for row in cursor.fetchall():
                        if row['bug_id'] not in [r['bug_id'] for r in results]:
                            results.append({
                                'bug_id': row['bug_id'],
                                'bug_type': row['bug_type'],
                                'root_cause': row['root_cause'],
                                'fix_suggestion': row['fix_suggestion'],
                                'fix_success': row['fix_success'],
                                'similarity': 0.5,  # 关键词匹配给较低相似度
                                'source': 'sqlite'
                            })
            except Exception as e:
                print(f"⚠️ SQLite检索失败: {e}")
        
        return results
    
    def find_healing_patterns(self, error_pattern: str, top_k: int = 3) -> List[Dict]:
        """
        查找修复模式 - 从历史中学习
        
        Args:
            error_pattern: 错误模式
            top_k: 返回前K个结果
            
        Returns:
            修复模式列表
        """
        if not self.kb or not self.kb.available:
            return []
        
        results = []
        
        # 1. ChromaDB语义检索
        collection = self.kb.get_collection("healing_patterns")
        if collection:
            try:
                chroma_results = collection.query(
                    query_texts=[error_pattern],
                    n_results=top_k
                )
                
                if chroma_results and chroma_results['ids']:
                    pattern_ids = chroma_results['ids'][0]
                    
                    for pattern_id in pattern_ids:
                        cursor = self.kb.conn.execute("""
                            SELECT * FROM healing_records WHERE pattern_id = ?
                        """, (pattern_id,))
                        row = cursor.fetchone()
                        if row:
                            results.append({
                                'pattern_id': row['pattern_id'],
                                'error_pattern': row['error_pattern'],
                                'fix_pattern': row['fix_pattern'],
                                'success_count': row['success_count'],
                                'fail_count': row['fail_count'],
                                'success_rate': row['success_count'] / max(1, row['success_count'] + row['fail_count'])
                            })
            except Exception as e:
                print(f"⚠️ 修复模式检索失败: {e}")
        
        # 按成功率排序
        results.sort(key=lambda x: x['success_rate'], reverse=True)
        
        return results[:top_k]
    
    def find_similar_testcases(self, requirement: str, top_k: int = 5) -> List[Dict]:
        """
        查找相似测试用例 - 用于推荐
        
        Args:
            requirement: 需求描述
            top_k: 返回前K个结果
            
        Returns:
            相似测试用例列表
        """
        if not self.kb or not self.kb.available:
            return []
        
        results = []
        
        collection = self.kb.get_collection("testcases")
        if collection:
            try:
                chroma_results = collection.query(
                    query_texts=[requirement],
                    n_results=top_k
                )
                
                if chroma_results and chroma_results['ids']:
                    tc_ids = chroma_results['ids'][0]
                    
                    for tc_id in tc_ids:
                        cursor = self.kb.conn.execute("""
                            SELECT * FROM testcase_records WHERE tc_id = ?
                        """, (tc_id,))
                        row = cursor.fetchone()
                        if row:
                            results.append({
                                'tc_id': row['tc_id'],
                                'title': row['title'],
                                'module': row['module'],
                                'priority': row['priority'],
                                'steps': json.loads(row['steps_json']),
                                'expected': row['expected'],
                                'quality_score': row['quality_score']
                            })
            except Exception as e:
                print(f"⚠️ 测试用例检索失败: {e}")
        
        return results
    
    # ═══════════════════════════════════════════════════════
    # 3. 反馈闭环 (评估和优化)
    # ═══════════════════════════════════════════════════════
    
    def evaluate_healing_result(self, pattern_id: str, success: bool) -> bool:
        """
        评估修复结果 - 反馈闭环
        
        Args:
            pattern_id: 修复模式ID
            success: 是否成功
            
        Returns:
            是否记录成功
        """
        if not self.kb or not self.kb.available:
            return False
        
        try:
            if success:
                self.kb.conn.execute("""
                    UPDATE healing_records 
                    SET success_count = success_count + 1
                    WHERE pattern_id = ?
                """, (pattern_id,))
            else:
                self.kb.conn.execute("""
                    UPDATE healing_records 
                    SET fail_count = fail_count + 1
                    WHERE pattern_id = ?
                """, (pattern_id,))
            
            self.kb.conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ 修复结果评估失败: {e}")
            return False
    
    def get_knowledge_stats(self) -> Dict:
        """获取知识库统计信息"""
        if not self.kb or not self.kb.available:
            return {}
        
        try:
            stats = {}
            
            # Bug统计
            cursor = self.kb.conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN fix_success = 1 THEN 1 ELSE 0 END) as fixed
                FROM bug_records
            """)
            row = cursor.fetchone()
            stats['bugs'] = {
                'total': row['total'],
                'fixed': row['fixed'],
                'fix_rate': row['fixed'] / max(1, row['total'])
            }
            
            # 测试用例统计
            cursor = self.kb.conn.execute("SELECT COUNT(*) as total FROM testcase_records")
            stats['testcases'] = {'total': cursor.fetchone()['total']}
            
            # 修复模式统计
            cursor = self.kb.conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    AVG(success_count * 1.0 / (success_count + fail_count)) as avg_success_rate
                FROM healing_records
                WHERE success_count + fail_count > 0
            """)
            row = cursor.fetchone()
            stats['healing_patterns'] = {
                'total': row['total'],
                'avg_success_rate': row['avg_success_rate'] or 0
            }
            
            return stats
            
        except Exception as e:
            print(f"❌ 统计信息获取失败: {e}")
            return {}
    
    # ═══════════════════════════════════════════════════════
    # 辅助方法
    # ═══════════════════════════════════════════════════════
    
    def _generate_bug_id(self, test_case: Dict, error_info: Dict) -> str:
        """生成Bug ID"""
        content = f"{test_case.get('id', '')}{error_info.get('error_message', '')}"
        return f"BUG-{hashlib.md5(content.encode()).hexdigest()[:12]}"
    
    def _analyze_root_cause(self, error_msg: str, stack_trace: str) -> str:
        """简单的根因分析"""
        # 这里可以集成AI进行更智能的分析
        if 'ConnectionError' in error_msg or 'timeout' in error_msg.lower():
            return "网络连接问题"
        elif 'AssertionError' in error_msg:
            return "断言失败"
        elif '404' in error_msg:
            return "接口不存在"
        elif '500' in error_msg:
            return "服务器内部错误"
        elif 'KeyError' in error_msg or 'AttributeError' in error_msg:
            return "数据结构问题"
        else:
            return "未知错误"
    
    def _determine_severity(self, error_info: Dict) -> str:
        """判断严重程度"""
        error_type = error_info.get('error_type', '')
        if 'Critical' in error_type or '500' in str(error_info):
            return "critical"
        elif 'Error' in error_type:
            return "high"
        else:
            return "medium"
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取
        import re
        words = re.findall(r'\w+', text.lower())
        # 过滤常见词
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        keywords = [w for w in words if len(w) > 3 and w not in stop_words]
        return keywords[:5]  # 返回前5个关键词
    
    def _store_bug_vector(self, bug_id: str, root_cause: str, error_msg: str):
        """存储Bug向量到ChromaDB"""
        collection = self.kb.get_collection("bugs")
        if collection:
            try:
                collection.add(
                    documents=[f"{root_cause} {error_msg}"],
                    metadatas=[{"bug_id": bug_id}],
                    ids=[bug_id]
                )
            except Exception as e:
                print(f"⚠️ Bug向量存储失败: {e}")
    
    def _store_testcase_vector(self, tc_id: str, title: str, expected: str):
        """存储测试用例向量到ChromaDB"""
        collection = self.kb.get_collection("testcases")
        if collection:
            try:
                collection.add(
                    documents=[f"{title} {expected}"],
                    metadatas=[{"tc_id": tc_id}],
                    ids=[tc_id]
                )
            except Exception as e:
                print(f"⚠️ 测试用例向量存储失败: {e}")
    
    def _store_healing_vector(self, pattern_id: str, error_pattern: str, fix_pattern: str):
        """存储修复模式向量到ChromaDB"""
        collection = self.kb.get_collection("healing_patterns")
        if collection:
            try:
                collection.add(
                    documents=[error_pattern],
                    metadatas={"pattern_id": pattern_id, "fix": fix_pattern},
                    ids=[pattern_id]
                )
            except Exception as e:
                print(f"⚠️ 修复模式向量存储失败: {e}")


# 全局单例
_manager_instance: Optional[KnowledgeManager] = None


def get_knowledge_manager() -> KnowledgeManager:
    """获取知识库管理器单例"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = KnowledgeManager()
    return _manager_instance
