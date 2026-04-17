#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Decision-Aware RAG (决策级RAG)
让知识库直接参与决策,而不仅仅是提供信息
"""

import json
from typing import Dict, List, Any, Optional
from utils.knowledge_prompt_helper import get_knowledge_helper
from knowledge.knowledge_manager import get_knowledge_manager


class DecisionAwareRAG:
    """决策级RAG - 结构化知识检索与决策支持"""
    
    def __init__(self):
        self.helper = get_knowledge_helper()
        self.km = get_knowledge_manager()
        
        # 核心模块定义(用于优先级和风险计算)
        self.core_modules = {
            '支付': {'priority_weight': 5, 'risk_weight': 5},
            '订单': {'priority_weight': 4, 'risk_weight': 4},
            '库存': {'priority_weight': 4, 'risk_weight': 3},
            '采购': {'priority_weight': 3, 'risk_weight': 3},
            '财务': {'priority_weight': 4, 'risk_weight': 4},
            '用户': {'priority_weight': 2, 'risk_weight': 2},
            '权限': {'priority_weight': 3, 'risk_weight': 4},
        }
    
    # ═══════════════════════════════════════════════════════
    # 核心方法: retrieve_knowledge_v2
    # ═══════════════════════════════════════════════════════
    
    def retrieve_knowledge_v2(self, query: str, context_type: str = "general",
                             max_tokens: int = 2000) -> Dict[str, Any]:
        """
        结构化知识检索 V2
        
        Args:
            query: 查询关键词
            context_type: 上下文类型
                - agent_decision: Agent决策
                - strategy_planning: 策略规划
                - case_generation: 用例生成
                - general: 通用
            max_tokens: 最大token数
            
        Returns:
            结构化知识字典:
            {
                "apis": [...],           # 高质量API列表
                "code": {...},           # 高质量代码
                "modules": [...],        # 识别的模块
                "priority": "P0/P1/P2",  # 优先级(规则计算)
                "risk_level": "high/medium/low",  # 风险等级(规则计算)
                "confidence": 0.85,      # 置信度
                "token_count": 1500,     # 实际token数
                "fallback": False        # 是否使用fallback
            }
        """
        try:
            # 1. 检索原始知识
            raw_knowledge = self._retrieve_raw_knowledge(query, context_type)
            
            # 2. 质量筛选
            filtered_knowledge = self.filter_knowledge(raw_knowledge)
            
            # 3. 模块识别(规则)
            modules = self.identify_modules(filtered_knowledge)
            
            # 4. 优先级计算(规则)
            priority = self.calculate_priority(modules, filtered_knowledge)
            
            # 5. 风险评估(规则)
            risk = self.calculate_risk(modules, filtered_knowledge)
            
            # 6. 构建结构化知识
            knowledge = {
                "apis": filtered_knowledge.get('apis', []),
                "code": {
                    "backend": filtered_knowledge.get('backend', []),
                    "frontend": filtered_knowledge.get('frontend', [])
                },
                "modules": modules,
                "priority": priority,
                "risk_level": risk,
                "confidence": self._calculate_confidence(filtered_knowledge),
                "metadata": {
                    "query": query,
                    "context_type": context_type
                }
            }
            
            # 7. Token控制
            knowledge = self.limit_tokens(knowledge, max_tokens)
            
            # 8. 添加token统计
            knowledge['token_count'] = self._estimate_tokens(knowledge)
            knowledge['fallback'] = False
            
            return knowledge
            
        except Exception as e:
            print(f"⚠️ 知识检索失败: {e}")
            return self._get_fallback_knowledge(query)
    
    # ═══════════════════════════════════════════════════════
    # 1. 原始知识检索
    # ═══════════════════════════════════════════════════════
    
    def _retrieve_raw_knowledge(self, query: str, context_type: str) -> Dict:
        """检索原始知识"""
        
        # 根据上下文类型调整检索策略
        if context_type == "agent_decision":
            # Agent决策: 需要API + 后端代码
            api_count = 10
            backend_count = 5
            frontend_count = 0
        elif context_type == "strategy_planning":
            # 策略规划: 需要API + 少量代码
            api_count = 8
            backend_count = 3
            frontend_count = 2
        elif context_type == "case_generation":
            # 用例生成: 需要详细API + 代码示例
            api_count = 10
            backend_count = 5
            frontend_count = 5
        else:
            # 通用: 平衡检索
            api_count = 8
            backend_count = 3
            frontend_count = 3
        
        # 检索API
        apis = self.helper.search_related_apis(query, top_k=api_count)
        
        # 检索后端代码
        backend = []
        if backend_count > 0:
            backend = self.helper.search_related_code(query, "backend", top_k=backend_count)
        
        # 检索前端代码
        frontend = []
        if frontend_count > 0:
            frontend = self.helper.search_related_code(query, "frontend", top_k=frontend_count)
        
        return {
            'apis': apis,
            'backend': backend,
            'frontend': frontend
        }
    
    # ═══════════════════════════════════════════════════════
    # 2. 质量筛选
    # ═══════════════════════════════════════════════════════
    
    def filter_knowledge(self, raw_knowledge: Dict, 
                        api_threshold: float = 0.7,
                        code_threshold: float = 0.6) -> Dict:
        """
        高质量筛选
        
        Args:
            raw_knowledge: 原始知识
            api_threshold: API相似度阈值
            code_threshold: 代码相似度阈值
            
        Returns:
            筛选后的高质量知识
        """
        filtered = {}
        
        # 筛选API
        apis = raw_knowledge.get('apis', [])
        filtered['apis'] = [
            api for api in apis 
            if api.get('similarity', 0) >= api_threshold
        ]
        
        # 筛选后端代码
        backend = raw_knowledge.get('backend', [])
        filtered['backend'] = [
            code for code in backend
            if code.get('similarity', 0) >= code_threshold
        ]
        
        # 筛选前端代码
        frontend = raw_knowledge.get('frontend', [])
        filtered['frontend'] = [
            code for code in frontend
            if code.get('similarity', 0) >= code_threshold
        ]
        
        return filtered
    
    # ═══════════════════════════════════════════════════════
    # 3. 模块识别(规则)
    # ═══════════════════════════════════════════════════════
    
    def identify_modules(self, knowledge: Dict) -> List[str]:
        """
        模块识别 - 基于规则
        
        Args:
            knowledge: 筛选后的知识
            
        Returns:
            识别的模块列表
        """
        modules = set()
        
        # 从API路径提取模块
        for api in knowledge.get('apis', []):
            path = api.get('path', '').lower()
            
            # 规则匹配
            if '/purchase/' in path or '/pms/' in path:
                modules.add('采购')
            if '/order/' in path:
                modules.add('订单')
            if '/stock/' in path or '/wms/' in path:
                modules.add('库存')
            if '/payment/' in path or '/pay/' in path:
                modules.add('支付')
            if '/finance/' in path or '/fi/' in path:
                modules.add('财务')
            if '/user/' in path or '/auth/' in path:
                modules.add('用户')
            if '/quality/' in path:
                modules.add('质检')
            if '/sales/' in path:
                modules.add('销售')
        
        # 从代码文件名提取模块
        for code in knowledge.get('backend', []) + knowledge.get('frontend', []):
            filename = code.get('filename', '').lower()
            
            if 'purchase' in filename:
                modules.add('采购')
            if 'order' in filename:
                modules.add('订单')
            if 'stock' in filename or 'warehouse' in filename:
                modules.add('库存')
            if 'payment' in filename or 'pay' in filename:
                modules.add('支付')
            if 'finance' in filename:
                modules.add('财务')
            if 'user' in filename or 'auth' in filename:
                modules.add('用户')
            if 'quality' in filename:
                modules.add('质检')
        
        return list(modules)
    
    # ═══════════════════════════════════════════════════════
    # 4. 优先级计算(规则)
    # ═══════════════════════════════════════════════════════
    
    def calculate_priority(self, modules: List[str], knowledge: Dict) -> str:
        """
        优先级计算 - 基于规则,不依赖LLM
        
        Args:
            modules: 识别的模块
            knowledge: 知识数据
            
        Returns:
            优先级: P0/P1/P2
        """
        score = 0
        
        # 规则1: API数量 (越多越重要)
        api_count = len(knowledge.get('apis', []))
        if api_count >= 5:
            score += 3
        elif api_count >= 3:
            score += 2
        elif api_count >= 1:
            score += 1
        
        # 规则2: 核心模块权重
        for module in modules:
            if module in self.core_modules:
                score += self.core_modules[module]['priority_weight']
        
        # 规则3: 历史Bug数量
        try:
            stats = self.km.get_knowledge_stats()
            bug_count = stats.get('bugs', {}).get('total', 0)
            if bug_count > 10:
                score += 2
            elif bug_count > 5:
                score += 1
        except:
            pass
        
        # 规则4: 代码复杂度(文件数量)
        code_count = len(knowledge.get('backend', [])) + len(knowledge.get('frontend', []))
        if code_count >= 5:
            score += 2
        elif code_count >= 3:
            score += 1
        
        # 映射到优先级
        if score >= 8:
            return "P0"
        elif score >= 4:
            return "P1"
        else:
            return "P2"
    
    # ═══════════════════════════════════════════════════════
    # 5. 风险评估(规则)
    # ═══════════════════════════════════════════════════════
    
    def calculate_risk(self, modules: List[str], knowledge: Dict) -> str:
        """
        风险评估 - 基于规则,不依赖LLM
        
        Args:
            modules: 识别的模块
            knowledge: 知识数据
            
        Returns:
            风险等级: high/medium/low
        """
        risk_score = 0
        
        # 规则1: 核心模块风险高
        for module in modules:
            if module in self.core_modules:
                risk_score += self.core_modules[module]['risk_weight']
        
        # 规则2: API数量多风险高
        api_count = len(knowledge.get('apis', []))
        if api_count > 5:
            risk_score += 2
        elif api_count > 3:
            risk_score += 1
        
        # 规则3: 历史Bug修复率
        try:
            stats = self.km.get_knowledge_stats()
            bugs = stats.get('bugs', {})
            fix_rate = bugs.get('fix_rate', 1.0)
            if fix_rate < 0.5:  # 修复率低于50%
                risk_score += 3
            elif fix_rate < 0.7:
                risk_score += 2
        except:
            pass
        
        # 规则4: 代码复杂度
        code_count = len(knowledge.get('backend', [])) + len(knowledge.get('frontend', []))
        if code_count > 8:
            risk_score += 2
        elif code_count > 5:
            risk_score += 1
        
        # 映射到风险等级
        if risk_score >= 10:
            return "high"
        elif risk_score >= 5:
            return "medium"
        else:
            return "low"
    
    # ═══════════════════════════════════════════════════════
    # 6. Token控制
    # ═══════════════════════════════════════════════════════
    
    def limit_tokens(self, knowledge: Dict, max_tokens: int = 2000) -> Dict:
        """
        严格控制token数量
        
        Args:
            knowledge: 知识数据
            max_tokens: 最大token数
            
        Returns:
            限制后的知识
        """
        # 估算当前token数
        current_tokens = self._estimate_tokens(knowledge)
        
        if current_tokens <= max_tokens:
            return knowledge
        
        # 需要裁剪
        # 策略: 保留最重要的信息
        # 1. 保留前3个API
        knowledge['apis'] = knowledge['apis'][:3]
        
        # 2. 保留前2个后端代码
        if 'code' in knowledge and 'backend' in knowledge['code']:
            knowledge['code']['backend'] = knowledge['code']['backend'][:2]
        
        # 3. 保留前2个前端代码
        if 'code' in knowledge and 'frontend' in knowledge['code']:
            knowledge['code']['frontend'] = knowledge['code']['frontend'][:2]
        
        # 4. 简化API信息(只保留关键字段)
        for api in knowledge.get('apis', []):
            # 移除不必要的字段
            api.pop('description', None)
            api.pop('parameters', None)
            api.pop('responses', None)
        
        # 5. 简化代码信息
        for code in knowledge.get('code', {}).get('backend', []):
            code.pop('functions', None)
            code.pop('content', None)
        
        for code in knowledge.get('code', {}).get('frontend', []):
            code.pop('functions', None)
            code.pop('content', None)
        
        return knowledge
    
    def _estimate_tokens(self, knowledge: Dict) -> int:
        """估算token数量 (粗略估算: 1 token ≈ 4 字符)"""
        text = json.dumps(knowledge, ensure_ascii=False)
        return len(text) // 4
    
    # ═══════════════════════════════════════════════════════
    # 7. 辅助方法
    # ═══════════════════════════════════════════════════════
    
    def _calculate_confidence(self, knowledge: Dict) -> float:
        """计算置信度"""
        apis = knowledge.get('apis', [])
        if not apis:
            return 0.0
        
        # 基于相似度计算平均置信度
        similarities = [api.get('similarity', 0) for api in apis]
        return sum(similarities) / len(similarities) if similarities else 0.0
    
    def _get_fallback_knowledge(self, query: str) -> Dict:
        """Fallback知识 - 确保系统不会因知识库失败而中断"""
        return {
            "apis": [],
            "code": {"backend": [], "frontend": []},
            "modules": [],
            "priority": "P2",  # 默认低优先级
            "risk_level": "low",  # 默认低风险
            "confidence": 0.0,
            "token_count": 0,
            "fallback": True,
            "metadata": {
                "query": query,
                "error": "Knowledge retrieval failed, using fallback"
            }
        }


# 全局单例
_decision_rag_instance: Optional[DecisionAwareRAG] = None


def get_decision_rag() -> DecisionAwareRAG:
    """获取决策级RAG单例"""
    global _decision_rag_instance
    if _decision_rag_instance is None:
        _decision_rag_instance = DecisionAwareRAG()
    return _decision_rag_instance
