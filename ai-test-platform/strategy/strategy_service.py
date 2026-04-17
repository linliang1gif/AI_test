"""
Test Strategy Service - 测试策略服务
根据 Test Agent 决策生成结构化测试策略
"""
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from .rules import apply_strategy_rules, calculate_execution_order
from utils.knowledge_prompt_helper import get_knowledge_helper

# V4增强：引入决策级RAG
try:
    from knowledge.decision_rag import get_decision_rag
    _decision_rag_available = True
except ImportError:
    _decision_rag_available = False
    print("⚠️  决策级RAG未找到，将不使用知识库增强")


class StrategyService:
    """测试策略服务 - V4增强版（决策级RAG支持）"""
    
    def __init__(self):
        self.helper = get_knowledge_helper()
        self.strategy_history = []
        self.log_dir = Path("output/strategy_logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # V4增强：初始化决策级RAG
        if _decision_rag_available:
            self.decision_rag = get_decision_rag()
            print("✅ 决策级RAG已加载到Strategy Service")
        else:
            self.decision_rag = None
    
    def generate_strategy(self, agent_decision: dict) -> dict:
        """
        根据 Agent 决策生成测试策略
        V4增强：使用决策级RAG动态调整策略
        
        Args:
            agent_decision: Test Agent 的决策结果
            
        Returns:
            结构化测试策略
        """
        try:
            # 1. 检查 action
            if agent_decision.get('action') == 'skip':
                print("⏭️  决策为跳过，返回空策略")
                return self._empty_strategy(agent_decision)
            
            # 2. 提取基础信息
            modules = agent_decision.get('modules', [])
            priority = agent_decision.get('priority', 'P1')
            risk_level = agent_decision.get('risk_level', '中')
            
            if not modules:
                print("⚠️  没有影响模块，返回空策略")
                return self._empty_strategy(agent_decision)
            
            print(f"🎯 生成策略: {len(modules)}个模块, 优先级{priority}, 风险{risk_level}")
            
            # ==================== V4增强：使用决策级RAG ====================
            knowledge = None
            if self.decision_rag:
                try:
                    # 从agent_decision中提取需求信息
                    requirement = agent_decision.get('metadata', {}).get('query', '')
                    if not requirement and modules:
                        requirement = ' '.join(modules)
                    
                    if requirement:
                        print(f"🧠 V4增强：检索策略知识...")
                        knowledge = self.decision_rag.retrieve_knowledge_v2(
                            query=requirement,
                            context_type="strategy_planning",
                            max_tokens=2000
                        )
                        print(f"✅ 知识检索完成:")
                        print(f"   - APIs: {len(knowledge.get('apis', []))}")
                        print(f"   - 模块: {knowledge.get('modules', [])}")
                        print(f"   - 优先级: {knowledge.get('priority')}")
                        print(f"   - 风险: {knowledge.get('risk_level')}")
                        
                        # 根据知识库调整优先级和风险
                        if knowledge.get('priority') in ['P0', 'P1'] and priority == 'P2':
                            print(f"📊 知识库建议提升优先级: {priority} → {knowledge['priority']}")
                            priority = knowledge['priority']
                        
                        kb_risk_map = {'high': '高', 'medium': '中', 'low': '低'}
                        kb_risk = kb_risk_map.get(knowledge.get('risk_level', 'low'), '中')
                        if kb_risk in ['高', '中'] and risk_level == '低':
                            print(f"⚠️  知识库建议提升风险等级: {risk_level} → {kb_risk}")
                            risk_level = kb_risk
                            
                except Exception as e:
                    print(f"⚠️  知识检索失败: {e}，继续使用基础策略")
                    knowledge = None
            
            # 3. 为每个模块生成策略（传递知识库信息）
            strategies = []
            for idx, module in enumerate(modules):
                module_strategy = self._generate_module_strategy(
                    module=module,
                    priority=priority,
                    risk_level=risk_level,
                    index=idx,
                    knowledge=knowledge  # V4增强：传递知识库
                )
                strategies.append(module_strategy)
            
            # 4. 排序（按执行顺序）
            strategies.sort(key=lambda x: x['execution_order'])
            
            # 5. 构建最终策略 - V4增强：添加知识库信息
            total_cases = sum(s['case_count'] for s in strategies)
            
            result = {
                "strategy": strategies,
                "total_modules": len(strategies),
                "total_cases": total_cases,
                "generated_at": datetime.now().isoformat(),
                "source_decision": agent_decision.get('timestamp', ''),
                "confidence": agent_decision.get('confidence', 0.8),
                "summary": {
                    "total_modules": len(strategies),
                    "estimated_total_cases": total_cases,
                    "risk_level": risk_level
                }
            }
            
            # V4增强：添加知识库信息
            if knowledge and not knowledge.get('fallback', False):
                result['knowledge'] = {
                    'apis': knowledge.get('apis', []),
                    'modules': knowledge.get('modules', []),
                    'priority': knowledge.get('priority'),
                    'risk_level': knowledge.get('risk_level'),
                    'confidence': knowledge.get('confidence'),
                    'token_count': knowledge.get('token_count'),
                    'enhanced': True
                }
                print(f"📊 策略已使用知识库增强")
            else:
                result['knowledge'] = {'enhanced': False}
            
            # 6. 记录策略历史
            self._log_strategy(agent_decision, result)
            
            print(f"✅ 策略生成完成: {result['total_modules']}个模块, {result['total_cases']}个用例")
            
            return result
            
        except Exception as e:
            print(f"❌ 策略生成失败: {e}")
            return self._empty_strategy(agent_decision)
    
    def _generate_module_strategy(
        self, 
        module: str, 
        priority: str, 
        risk_level: str,
        index: int,
        knowledge: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        为单个模块生成策略 - V4增强版（知识库支持）
        
        Args:
            module: 模块名称
            priority: 优先级
            risk_level: 风险等级
            index: 模块索引
            knowledge: 知识库检索结果
            
        Returns:
            模块策略字典
        """
        # 应用规则引擎
        rules_result = apply_strategy_rules(module, priority, risk_level)
        
        # V4增强：根据知识库调整测试类型和用例数量
        if knowledge and not knowledge.get('fallback', False):
            kb_risk = knowledge.get('risk_level', 'low')
            api_count = len(knowledge.get('apis', []))
            kb_priority = knowledge.get('priority', 'P2')
            
            # 根据风险等级调整测试类型
            if kb_risk == 'high':
                # 高风险：添加安全测试
                if 'security' not in rules_result['test_types']:
                    rules_result['test_types'].append('security')
                base_case_count = 10
            elif kb_risk == 'medium':
                # 中风险：确保有UI测试
                if 'ui' not in rules_result['test_types'] and len(rules_result['test_types']) < 2:
                    rules_result['test_types'].append('ui')
                base_case_count = 5
            else:
                base_case_count = 3
            
            # 根据API数量调整用例数
            if api_count > 5:
                case_count = int(base_case_count * 1.5)
            elif api_count > 3:
                case_count = base_case_count
            else:
                case_count = max(3, base_case_count - 2)
            
            # 根据优先级调整
            if kb_priority == 'P0':
                case_count = int(case_count * 1.5)
            
            # 更新用例数量
            rules_result['case_count'] = max(rules_result['case_count'], case_count)
            
            print(f"   📊 模块[{module}]知识库调整: 测试类型={rules_result['test_types']}, 用例数={rules_result['case_count']}")
        
        # 计算执行顺序
        execution_order = calculate_execution_order(priority, risk_level)
        
        # V2增强：计算 impact
        impact = self._calculate_impact(priority, risk_level)
        
        # V2增强：生成 execution_hint
        execution_hint = self._generate_execution_hint(priority)
        
        # 构建模块策略 - V4结构
        strategy = {
            "module": {
                "name": module,
                "impact": impact
            },
            "priority": priority,
            "test_types": rules_result['test_types'],
            "case_count": rules_result['case_count'],
            "execution_order": execution_order,
            "risk_level": risk_level,
            "execution_hint": execution_hint
        }
        
        return strategy
    
    def _calculate_impact(self, priority: str, risk_level: str) -> str:
        """
        计算影响程度
        
        规则：
        - P0 + 高风险 → high
        - P0 + 中风险 → high
        - P1 + 高风险 → high
        - P1 + 中风险 → medium
        - P2 → low
        """
        if priority == "P0":
            return "high"
        elif priority == "P1":
            return "high" if risk_level == "高" else "medium"
        else:  # P2
            return "low"
    
    def _generate_execution_hint(self, priority: str) -> Dict[str, Any]:
        """
        生成执行建议 - V2增强
        
        规则：
        - P0 → parallel=true, timeout=60
        - P1 → parallel=true, timeout=90
        - P2 → parallel=false, timeout=120
        """
        if priority == "P0":
            return {"parallel": True, "timeout": 60}
        elif priority == "P1":
            return {"parallel": True, "timeout": 90}
        else:  # P2
            return {"parallel": False, "timeout": 120}
    
    def _empty_strategy(self, agent_decision: dict) -> dict:
        """返回空策略 - V2增强：添加 summary"""
        return {
            "strategy": [],
            "total_modules": 0,
            "total_cases": 0,
            "generated_at": datetime.now().isoformat(),
            "source_decision": agent_decision.get('timestamp', ''),
            "confidence": agent_decision.get('confidence', 0.0),
            "summary": {
                "total_modules": 0,
                "estimated_total_cases": 0,
                "risk_level": agent_decision.get('risk_level', '低')
            }
        }
    
    def _log_strategy(self, agent_decision: dict, strategy: dict):
        """记录策略历史"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "agent_decision": {
                    "action": agent_decision.get('action'),
                    "priority": agent_decision.get('priority'),
                    "modules": agent_decision.get('modules'),
                    "confidence": agent_decision.get('confidence')
                },
                "strategy": strategy
            }
            
            self.strategy_history.append(log_entry)
            
            # 保存到文件
            log_file = self.log_dir / f"strategy_{datetime.now().strftime('%Y%m%d')}.jsonl"
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
                
        except Exception as e:
            print(f"⚠️  记录策略历史失败: {e}")
    
    def get_strategy_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取策略历史"""
        return self.strategy_history[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.strategy_history:
            return {
                "total_strategies": 0,
                "total_modules": 0,
                "total_cases": 0,
                "avg_modules_per_strategy": 0
            }
        
        total = len(self.strategy_history)
        total_modules = sum(s['strategy']['total_modules'] for s in self.strategy_history)
        total_cases = sum(s['strategy']['total_cases'] for s in self.strategy_history)
        
        return {
            "total_strategies": total,
            "total_modules": total_modules,
            "total_cases": total_cases,
            "avg_modules_per_strategy": round(total_modules / total, 2) if total > 0 else 0,
            "avg_cases_per_strategy": round(total_cases / total, 2) if total > 0 else 0
        }


# 全局服务实例
_strategy_service = None

def get_strategy_service() -> StrategyService:
    """获取策略服务实例"""
    global _strategy_service
    if _strategy_service is None:
        _strategy_service = StrategyService()
    return _strategy_service
