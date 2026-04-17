#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LearningAgent - 学习型代理（构建测试反馈闭环）

核心能力：
1. 失败模式学习 - 识别常见失败模式
2. 修复策略学习 - 统计最优修复策略
3. 覆盖缺口分析 - 识别高风险但测试少的API
4. 数据持久化 - 存储学习结果

目标：让系统具备"学习能力"，基于历史执行结果优化未来测试
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from collections import defaultdict


class LearningAgent:
    """
    学习型代理 - 构建测试反馈闭环
    
    核心功能：
    1. 学习失败模式
    2. 学习修复策略
    3. 分析覆盖缺口
    4. 持久化知识
    """
    
    def __init__(self, knowledge_dir: str = "knowledge"):
        """
        初始化 Learning Agent
        
        Args:
            knowledge_dir: 知识库目录
        """
        self.knowledge_dir = Path(knowledge_dir)
        self.knowledge_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
        # 知识库文件路径
        self.failures_file = self.knowledge_dir / "failures.json"
        self.healing_stats_file = self.knowledge_dir / "healing_stats.json"
        self.coverage_gaps_file = self.knowledge_dir / "coverage_gaps.json"
        self.api_stats_file = self.knowledge_dir / "api_stats.json"
        
        # 加载已有知识
        self.failure_patterns = self._load_json(self.failures_file, {})
        self.healing_stats = self._load_json(self.healing_stats_file, {})
        self.coverage_gaps = self._load_json(self.coverage_gaps_file, [])
        self.api_stats = self._load_json(self.api_stats_file, {})
        
        self.logger.info(f"LearningAgent 初始化: 知识库={knowledge_dir}")
        self.logger.info(f"  已加载失败模式: {len(self.failure_patterns)}")
        self.logger.info(f"  已加载修复统计: {len(self.healing_stats)}")
        self.logger.info(f"  已加载覆盖缺口: {len(self.coverage_gaps)}")
    
    def learn(self, execution_results: List[Any], healing_records: List[Dict[str, Any]]):
        """
        学习执行结果和修复记录（核心学习函数）
        
        Args:
            execution_results: 执行结果列表
            healing_records: 修复记录列表
        """
        self.logger.info(f"开始学习: {len(execution_results)} 个执行结果, {len(healing_records)} 个修复记录")
        
        # 1. 学习失败模式
        self._learn_failure_patterns(execution_results)
        
        # 2. 学习修复策略
        self._learn_healing_strategies(execution_results, healing_records)
        
        # 3. 分析覆盖缺口
        self._analyze_coverage_gaps(execution_results)
        
        # 4. 更新 API 统计
        self._update_api_stats(execution_results)
        
        # 5. 持久化知识
        self._save_knowledge()
        
        self.logger.info("学习完成")
    
    # ==================== 1. 失败模式学习 ====================
    
    def _learn_failure_patterns(self, execution_results: List[Any]):
        """
        学习失败模式
        
        结构：
        {
            "api": "/payment",
            "error_type": "timeout",
            "frequency": 10,
            "last_seen": "2026-04-17T10:00:00",
            "severity": 0.8
        }
        """
        for result in execution_results:
            # 只学习失败的用例
            if self._is_passed(result):
                continue
            
            # 提取信息
            api = self._extract_api(result)
            error_type = self._classify_error(result)
            error_msg = self._get_error_message(result)
            
            # 创建模式键
            pattern_key = f"{api}::{error_type}"
            
            # 更新或创建失败模式
            if pattern_key not in self.failure_patterns:
                self.failure_patterns[pattern_key] = {
                    "api": api,
                    "error_type": error_type,
                    "frequency": 0,
                    "first_seen": datetime.now().isoformat(),
                    "last_seen": datetime.now().isoformat(),
                    "severity": 0.5,
                    "error_messages": []
                }
            
            pattern = self.failure_patterns[pattern_key]
            pattern["frequency"] += 1
            pattern["last_seen"] = datetime.now().isoformat()
            
            # 更新严重程度（基于频率）
            pattern["severity"] = min(0.9, 0.3 + (pattern["frequency"] * 0.05))
            
            # 保存错误信息样本（最多10个）
            if len(pattern["error_messages"]) < 10:
                pattern["error_messages"].append({
                    "message": error_msg[:200],
                    "timestamp": datetime.now().isoformat()
                })
        
        self.logger.info(f"学习了 {len(self.failure_patterns)} 个失败模式")
    
    # ==================== 2. 修复策略学习 ====================
    
    def _learn_healing_strategies(self, execution_results: List[Any], healing_records: List[Dict[str, Any]]):
        """
        学习修复策略
        
        统计每种错误类型 → 哪种修复策略成功率最高
        
        结构：
        {
            "timeout": {
                "L1_RETRY": {"success": 8, "total": 10, "rate": 0.8},
                "L2_DATA": {"success": 2, "total": 3, "rate": 0.67}
            }
        }
        """
        # 建立结果映射
        result_map = {self._get_testcase_id(r): r for r in execution_results}
        
        for record in healing_records:
            testcase_id = record.get('testcase_id', 'unknown')
            healing_level = record.get('healing_level', 'unknown')
            strategy = record.get('strategy', 'unknown')
            success = record.get('success', False)
            
            # 获取对应的执行结果
            result = result_map.get(testcase_id)
            if not result:
                continue
            
            # 分类错误类型
            error_type = self._classify_error(result)
            
            # 初始化统计结构
            if error_type not in self.healing_stats:
                self.healing_stats[error_type] = {}
            
            if healing_level not in self.healing_stats[error_type]:
                self.healing_stats[error_type][healing_level] = {
                    "success": 0,
                    "total": 0,
                    "rate": 0.0
                }
            
            # 更新统计
            stats = self.healing_stats[error_type][healing_level]
            stats["total"] += 1
            if success:
                stats["success"] += 1
            stats["rate"] = stats["success"] / stats["total"] if stats["total"] > 0 else 0.0
        
        self.logger.info(f"学习了 {len(self.healing_stats)} 种错误类型的修复策略")
    
    # ==================== 3. 覆盖缺口分析 ====================
    
    def _analyze_coverage_gaps(self, execution_results: List[Any]):
        """
        分析覆盖缺口
        
        识别：哪些接口频繁出问题但测试少
        
        输出：coverage_gaps = ["payment_refund", "order_cancel"]
        """
        # 统计每个 API 的测试次数和失败次数
        api_coverage = defaultdict(lambda: {"total": 0, "failed": 0})
        
        for result in execution_results:
            api = self._extract_api(result)
            api_coverage[api]["total"] += 1
            
            if not self._is_passed(result):
                api_coverage[api]["failed"] += 1
        
        # 识别覆盖缺口：失败率高但测试次数少
        gaps = []
        
        for api, stats in api_coverage.items():
            failure_rate = stats["failed"] / stats["total"] if stats["total"] > 0 else 0
            test_count = stats["total"]
            
            # 缺口判断：失败率 > 30% 且 测试次数 < 5
            if failure_rate > 0.3 and test_count < 5:
                gaps.append({
                    "api": api,
                    "test_count": test_count,
                    "failure_rate": failure_rate,
                    "priority": "high" if failure_rate > 0.5 else "medium",
                    "identified_at": datetime.now().isoformat()
                })
        
        # 按失败率排序
        gaps.sort(key=lambda x: x["failure_rate"], reverse=True)
        
        # 更新覆盖缺口（保留历史记录）
        existing_apis = {g["api"] for g in self.coverage_gaps if isinstance(g, dict)}
        for gap in gaps:
            if gap["api"] not in existing_apis:
                self.coverage_gaps.append(gap)
        
        self.logger.info(f"识别了 {len(gaps)} 个新的覆盖缺口")
    
    # ==================== 4. API 统计更新 ====================
    
    def _update_api_stats(self, execution_results: List[Any]):
        """更新 API 统计信息"""
        for result in execution_results:
            api = self._extract_api(result)
            
            if api not in self.api_stats:
                self.api_stats[api] = {
                    "total_executions": 0,
                    "total_failures": 0,
                    "failure_rate": 0.0,
                    "last_executed": None,
                    "risk_score": 0.0
                }
            
            stats = self.api_stats[api]
            stats["total_executions"] += 1
            
            if not self._is_passed(result):
                stats["total_failures"] += 1
            
            stats["failure_rate"] = stats["total_failures"] / stats["total_executions"]
            stats["last_executed"] = datetime.now().isoformat()
            
            # 计算风险分数（基于失败率和频率）
            stats["risk_score"] = min(1.0, stats["failure_rate"] * 0.7 + 
                                     min(stats["total_failures"] / 10, 0.3))

    # ==================== 查询接口 ====================
    
    def get_failure_patterns(self, api: Optional[str] = None, 
                            min_frequency: int = 1) -> List[Dict[str, Any]]:
        """
        获取失败模式
        
        Args:
            api: 可选，筛选特定 API
            min_frequency: 最小频率阈值
        
        Returns:
            失败模式列表，按频率降序排序
        """
        patterns = []
        
        for pattern_key, pattern in self.failure_patterns.items():
            # 筛选条件
            if api and pattern["api"] != api:
                continue
            
            if pattern["frequency"] < min_frequency:
                continue
            
            patterns.append(pattern)
        
        # 按频率降序排序
        patterns.sort(key=lambda x: x["frequency"], reverse=True)
        
        return patterns
    
    def get_best_healing_strategy(self, error_type: str) -> Optional[str]:
        """
        获取最优修复策略
        
        Args:
            error_type: 错误类型（timeout/connection/assertion等）
        
        Returns:
            最优修复策略（L1_RETRY/L2_DATA/L3_TOLERANCE/L4_MANUAL）
        """
        if error_type not in self.healing_stats:
            self.logger.debug(f"未找到错误类型 {error_type} 的修复统计")
            return None
        
        strategies = self.healing_stats[error_type]
        
        # 找到成功率最高的策略
        best_strategy = None
        best_rate = 0.0
        
        for strategy, stats in strategies.items():
            # 至少要有2次尝试才可信（降低阈值）
            if stats["total"] >= 2 and stats["rate"] > best_rate:
                best_strategy = strategy
                best_rate = stats["rate"]
        
        if best_strategy:
            self.logger.info(f"错误类型 {error_type} 的最优策略: {best_strategy} (成功率: {best_rate:.1%})")
        
        return best_strategy
    
    def get_high_risk_apis(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        获取高风险 API
        
        Args:
            top_n: 返回前 N 个
        
        Returns:
            高风险 API 列表，按风险分数降序排序
        """
        high_risk = []
        
        for api, stats in self.api_stats.items():
            if stats["risk_score"] > 0.3:  # 风险阈值
                high_risk.append({
                    "api": api,
                    "risk_score": stats["risk_score"],
                    "failure_rate": stats["failure_rate"],
                    "total_failures": stats["total_failures"],
                    "total_executions": stats["total_executions"]
                })
        
        # 按风险分数降序排序
        high_risk.sort(key=lambda x: x["risk_score"], reverse=True)
        
        return high_risk[:top_n]
    
    def get_coverage_gaps(self, priority: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取覆盖缺口
        
        Args:
            priority: 可选，筛选优先级（high/medium/low）
        
        Returns:
            覆盖缺口列表
        """
        gaps = []
        
        for gap in self.coverage_gaps:
            if not isinstance(gap, dict):
                continue
            
            if priority and gap.get("priority") != priority:
                continue
            
            gaps.append(gap)
        
        return gaps
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """
        获取学习摘要
        
        Returns:
            学习摘要字典
        """
        # 统计失败模式
        total_failures = sum(p["frequency"] for p in self.failure_patterns.values())
        
        # 统计修复策略
        total_healings = sum(
            sum(s["total"] for s in strategies.values())
            for strategies in self.healing_stats.values()
        )
        
        # 统计覆盖缺口
        high_priority_gaps = len([g for g in self.coverage_gaps 
                                  if isinstance(g, dict) and g.get("priority") == "high"])
        
        return {
            "failure_patterns": {
                "total_patterns": len(self.failure_patterns),
                "total_failures": total_failures,
                "top_apis": self._get_top_failing_apis(5)
            },
            "healing_strategies": {
                "error_types_learned": len(self.healing_stats),
                "total_healings": total_healings,
                "best_strategies": self._get_best_strategies()
            },
            "coverage_gaps": {
                "total_gaps": len(self.coverage_gaps),
                "high_priority": high_priority_gaps,
                "top_gaps": self.get_coverage_gaps()[:5]
            },
            "api_stats": {
                "total_apis": len(self.api_stats),
                "high_risk_apis": len(self.get_high_risk_apis())
            }
        }
    
    # ==================== 辅助方法 ====================
    
    def _get_top_failing_apis(self, top_n: int) -> List[Dict[str, Any]]:
        """获取失败最多的 API"""
        api_failures = defaultdict(int)
        
        for pattern in self.failure_patterns.values():
            api_failures[pattern["api"]] += pattern["frequency"]
        
        top_apis = sorted(api_failures.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        return [{"api": api, "failures": count} for api, count in top_apis]
    
    def _get_best_strategies(self) -> Dict[str, str]:
        """获取每种错误类型的最优策略"""
        best = {}
        
        for error_type in self.healing_stats.keys():
            strategy = self.get_best_healing_strategy(error_type)
            if strategy:
                best[error_type] = strategy
        
        return best
    
    def _extract_api(self, result: Any) -> str:
        """提取 API 路径"""
        # 尝试从 testcase_id 提取
        testcase_id = self._get_testcase_id(result)
        
        # 简单提取：假设 testcase_id 包含 API 路径
        # 例如：tc_payment_create_001 → /payment/create
        if '_' in testcase_id:
            parts = testcase_id.split('_')
            if len(parts) >= 3:
                return f"/{parts[1]}/{parts[2]}"
        
        return "/unknown"
    
    def _classify_error(self, result: Any) -> str:
        """分类错误类型"""
        error_msg = self._get_error_message(result)
        
        if not error_msg:
            return "unknown"
        
        error_lower = error_msg.lower()
        
        if 'timeout' in error_lower or 'timed out' in error_lower:
            return "timeout"
        elif 'connection' in error_lower or 'connect' in error_lower:
            return "connection"
        elif 'assertion' in error_lower or 'expected' in error_lower:
            return "assertion"
        elif 'invalid' in error_lower or 'validation' in error_lower:
            return "data_invalid"
        else:
            return "unknown"
    
    def _get_testcase_id(self, result: Any) -> str:
        """获取测试用例 ID"""
        if hasattr(result, 'test_case_id'):
            return result.test_case_id
        elif hasattr(result, 'testcase_id'):
            return result.testcase_id
        elif isinstance(result, dict):
            return result.get('test_case_id') or result.get('testcase_id', 'unknown')
        return 'unknown'
    
    def _get_error_message(self, result: Any) -> str:
        """获取错误信息"""
        if hasattr(result, 'error'):
            return result.error or ''
        elif isinstance(result, dict):
            return result.get('error', '') or result.get('message', '')
        return ''
    
    def _is_passed(self, result: Any) -> bool:
        """判断是否通过"""
        if hasattr(result, 'status'):
            s = result.status
            if hasattr(s, 'value'):
                return s.value.upper() == 'PASSED'
            return str(s).upper() == 'PASSED'
        
        if isinstance(result, dict):
            status = result.get('status', '')
            return str(status).upper() == 'PASSED'
        
        return False
    
    # ==================== 数据持久化 ====================
    
    def _save_knowledge(self):
        """保存知识到文件"""
        try:
            self._save_json(self.failures_file, self.failure_patterns)
            self._save_json(self.healing_stats_file, self.healing_stats)
            self._save_json(self.coverage_gaps_file, self.coverage_gaps)
            self._save_json(self.api_stats_file, self.api_stats)
            
            self.logger.info(f"知识已保存到: {self.knowledge_dir}")
        except Exception as e:
            self.logger.error(f"保存知识失败: {e}")
    
    def _load_json(self, file_path: Path, default: Any) -> Any:
        """加载 JSON 文件"""
        if not file_path.exists():
            return default
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.warning(f"加载 {file_path} 失败: {e}")
            return default
    
    def _save_json(self, file_path: Path, data: Any):
        """保存 JSON 文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def reset_knowledge(self):
        """重置知识库（用于测试）"""
        self.failure_patterns = {}
        self.healing_stats = {}
        self.coverage_gaps = []
        self.api_stats = {}
        self._save_knowledge()
        self.logger.info("知识库已重置")
