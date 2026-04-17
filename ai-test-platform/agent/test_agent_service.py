#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Agent Service - AI测试决策服务 V3
分析需求和代码变更，智能决策测试范围和优先级
V2增强：输出可执行决策指令，驱动Strategy/Orchestrator/CI
V3增强：接入传统文档解析能力（RequirementParser + ModuleSplitter）
"""

import json
import time
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from .llm_client import get_llm_client

# 引入传统流程的解析能力
try:
    from parser.requirement_parser import RequirementParser
    from test_design.module_splitter import ModuleSplitter
    _parser_available = True
except ImportError:
    _parser_available = False
    print("⚠️  传统解析模块未找到，将使用简化模式")

# 引入决策级RAG
try:
    from knowledge.decision_rag import get_decision_rag
    _decision_rag_available = True
except ImportError:
    _decision_rag_available = False
    print("⚠️  决策级RAG未找到，将不使用知识库增强")


def enhance_decision(result: dict) -> dict:
    """
    V2决策增强函数
    将基础分析结果转换为可执行决策指令
    
    Args:
        result: 基础分析结果
        
    Returns:
        增强后的决策结果
    """
    # 1. 新增 action 字段
    result['action'] = "run_tests" if result.get('need_test', True) else "skip"
    
    # 2. 新增 confidence 字段
    confidence = 0.8  # 默认置信度
    if result.get('risk_level') == "高":
        confidence = 0.9
    elif result.get('priority') == "P2":
        confidence = 0.6
    result['confidence'] = confidence
    
    # 3. 新增 test_scope 字段
    test_types = result.get('test_types', [])
    scope_types = []
    
    # 根据测试类型映射
    for test_type in test_types:
        if "接口" in test_type or "API" in test_type:
            if "api" not in scope_types:
                scope_types.append("api")
        if "功能" in test_type or "UI" in test_type or "界面" in test_type:
            if "ui" not in scope_types:
                scope_types.append("ui")
    
    # 默认为api测试
    if not scope_types:
        scope_types = ["api"]
    
    # 根据优先级估算用例数
    priority = result.get('priority', 'P1')
    estimated_cases = {
        'P0': 30,
        'P1': 20,
        'P2': 10
    }.get(priority, 20)
    
    result['test_scope'] = {
        "types": scope_types,
        "estimated_cases": estimated_cases
    }
    
    # 4. 新增 execution_hint 字段
    parallel = True if priority == "P0" else (False if priority == "P2" else True)
    
    result['execution_hint'] = {
        "parallel": parallel,
        "retry": 1
    }
    
    # 5. 新增 timestamp 字段
    result['timestamp'] = datetime.now().isoformat()
    
    return result


class TestAgentService:
    """AI测试决策服务 - V3增强版（接入文档解析能力）"""
    
    def __init__(self):
        self.llm_client = get_llm_client()
        self.decision_history = []
        self.log_dir = Path("output/agent_logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # V3增强：初始化传统解析能力
        if _parser_available:
            self.requirement_parser = RequirementParser()
            self.module_splitter = ModuleSplitter()
        else:
            self.requirement_parser = None
            self.module_splitter = None
        
        # V4增强：初始化决策级RAG
        if _decision_rag_available:
            self.decision_rag = get_decision_rag()
            print("✅ 决策级RAG已加载")
        else:
            self.decision_rag = None
    
    def parse_requirement(self, requirement: str) -> Dict[str, Any]:
        """
        V3新增：解析需求文档，提取结构化信息
        
        Args:
            requirement: 需求文本
            
        Returns:
            {
                "modules": [模块列表],
                "sections": {章节信息},
                "key_info": {关键信息}
            }
        """
        if not _parser_available or not self.module_splitter:
            # 降级：简单解析
            return {
                "modules": self._simple_module_extract(requirement),
                "sections": {},
                "key_info": {}
            }
        
        try:
            print("📄 解析需求文档...")
            
            # 1. 使用 RequirementParser 解析章节
            sections = self.requirement_parser.parse_requirement_sections(requirement)
            
            # 2. 提取关键信息
            key_info = self.requirement_parser.extract_key_information(requirement)
            
            # 3. 使用 ModuleSplitter 拆分模块
            modules = self.module_splitter.split_modules(requirement)
            
            print(f"✅ 解析完成: {len(modules)} 个模块")
            
            return {
                "modules": modules,
                "sections": sections,
                "key_info": key_info
            }
            
        except Exception as e:
            print(f"⚠️  需求解析失败: {e}，使用简化模式")
            return {
                "modules": self._simple_module_extract(requirement),
                "sections": {},
                "key_info": {}
            }
    
    def _simple_module_extract(self, requirement: str) -> List[Dict[str, Any]]:
        """简单的模块提取（降级方案）"""
        # 从需求文本中提取关键词作为模块
        keywords = ["用户", "订单", "支付", "商品", "库存", "权限", "登录", "注册"]
        
        modules = []
        for i, keyword in enumerate(keywords):
            if keyword in requirement:
                modules.append({
                    "id": f"module_{i+1:03d}",
                    "name": f"{keyword}模块",
                    "description": f"{keyword}相关功能",
                    "functions": [f"{keyword}功能"],
                    "priority": "中",
                    "complexity": "中等"
                })
        
        # 如果没有匹配到任何模块，返回默认模块
        if not modules:
            modules = [{
                "id": "module_001",
                "name": "核心功能模块",
                "description": "系统核心功能",
                "functions": ["核心功能"],
                "priority": "高",
                "complexity": "中等"
            }]
        
        return modules
    
    def analyze(self, requirement: str, git_diff: str = "") -> Dict[str, Any]:
        """
        分析需求和代码变更，决策是否需要测试
        V2增强：返回可执行决策指令
        V3增强：先解析需求，提取结构化模块信息，再进行AI决策
        V4增强：使用决策级RAG提供知识支持
        
        Args:
            requirement: 需求描述文本
            git_diff: 代码变更内容（可选）
            
        Returns:
            增强后的决策结果字典
        """
        start_time = time.time()
        
        try:
            # ==================== V3增强：先解析需求 ====================
            print(f"🔍 V3增强：解析需求文档...")
            parsed_data = self.parse_requirement(requirement)
            
            # 提取模块信息
            parsed_modules = parsed_data.get('modules', [])
            module_names = [m.get('name', '') for m in parsed_modules]
            
            print(f"✅ 解析完成: 识别 {len(module_names)} 个模块")
            
            # ==================== V4增强：使用决策级RAG ====================
            knowledge = None
            if self.decision_rag:
                try:
                    print(f"🧠 V4增强：检索决策知识...")
                    knowledge = self.decision_rag.retrieve_knowledge_v2(
                        query=requirement,
                        context_type="agent_decision",
                        max_tokens=2000
                    )
                    print(f"✅ 知识检索完成:")
                    print(f"   - APIs: {len(knowledge.get('apis', []))}")
                    print(f"   - 模块: {knowledge.get('modules', [])}")
                    print(f"   - 优先级: {knowledge.get('priority')}")
                    print(f"   - 风险: {knowledge.get('risk_level')}")
                    print(f"   - Token: {knowledge.get('token_count')}")
                except Exception as e:
                    print(f"⚠️  知识检索失败: {e}，继续使用基础分析")
                    knowledge = None
            
            # ==================== 构建增强的分析prompt ====================
            prompt = self._build_analysis_prompt_v4(
                requirement=requirement, 
                git_diff=git_diff,
                parsed_modules=parsed_modules,
                knowledge=knowledge
            )
            system_prompt = self._get_system_prompt()
            
            # 调用LLM分析
            print(f"🤖 Test Agent 正在分析...")
            llm_result = self.llm_client.generate_json(prompt, system_prompt)
            
            # 检查返回值
            if llm_result is None:
                print(f"⚠️  LLM返回None，使用默认决策")
                return self._get_default_decision_v4("LLM返回None", parsed_modules, knowledge)
            
            # 验证和规范化结果
            result = self._normalize_result(llm_result)
            
            # ==================== V3增强：合并解析的模块信息 ====================
            # 如果 LLM 没有返回 modules，使用解析的模块
            if not result.get('modules') or len(result['modules']) == 0:
                result['modules'] = module_names
            
            # 添加详细的模块信息（供后续阶段使用）
            result['parsed_modules'] = parsed_modules
            result['parsed_sections'] = parsed_data.get('sections', {})
            
            # ==================== V4增强：合并知识库信息 ====================
            if knowledge:
                result['knowledge'] = {
                    'apis': knowledge.get('apis', []),
                    'modules': knowledge.get('modules', []),
                    'priority': knowledge.get('priority'),
                    'risk_level': knowledge.get('risk_level'),
                    'confidence': knowledge.get('confidence'),
                    'token_count': knowledge.get('token_count')
                }
                
                # 如果知识库提供了更高的优先级或风险，使用知识库的判断
                if knowledge.get('priority') in ['P0', 'P1'] and result.get('priority') == 'P2':
                    print(f"📊 知识库建议提升优先级: {result['priority']} → {knowledge['priority']}")
                    result['priority'] = knowledge['priority']
                
                if knowledge.get('risk_level') in ['high', 'medium'] and result.get('risk_level') == '低':
                    print(f"⚠️  知识库建议提升风险等级: {result['risk_level']} → {knowledge['risk_level']}")
                    result['risk_level'] = knowledge['risk_level']
            
            # V2增强：调用决策增强函数
            result = enhance_decision(result)
            
            # 添加元数据
            result['analyzed_at'] = datetime.now().isoformat()
            result['duration'] = f"{time.time() - start_time:.2f}s"
            result['provider'] = self.llm_client.provider
            result['model'] = self.llm_client.model
            result['version'] = "v4"  # 标记为V4版本
            
            # 记录决策历史
            self._log_decision(requirement, git_diff, result)
            
            print(f"✅ 分析完成: {'需要测试' if result['need_test'] else '无需测试'}")
            
            return result
            
        except Exception as e:
            print(f"❌ 分析失败: {e}")
            import traceback
            traceback.print_exc()
            # 返回保守的默认决策（也经过增强）
            return self._get_default_decision_v4(str(e), [], None)
    
    def _build_analysis_prompt_v3(self, requirement: str, git_diff: str, parsed_modules: List[Dict[str, Any]]) -> str:
        """
        V3增强：构建分析prompt（包含解析的模块信息）
        
        Args:
            requirement: 需求文本
            git_diff: 代码变更
            parsed_modules: 已解析的模块列表
            
        Returns:
            增强的prompt
        """
        # 格式化模块信息
        modules_context = self._format_modules_context(parsed_modules)
        
        prompt = f"""# 测试决策分析任务（V3增强版）

## 已解析的模块信息
{modules_context}

## 需求描述
{requirement}
"""
        
        if git_diff:
            prompt += f"""
## 代码变更
```diff
{git_diff[:2000]}
```
"""
        
        prompt += """
## 分析要求

基于上述已解析的模块信息，请分析：
1. **是否需要测试**: 判断此变更是否需要执行测试
2. **影响模块**: 从已解析的模块中选择受影响的模块（使用模块名称）
3. **优先级**: 评估测试优先级（P0/P1/P2）
4. **原因**: 说明决策理由
5. **测试类型**: 需要执行的测试类型
6. **预估工作量**: 测试所需时间
7. **风险等级**: 评估风险（高/中/低）

## 输出格式

**重要：只返回JSON，不要任何说明文字！**

```json
{
  "need_test": true,
  "modules": ["模块1", "模块2"],
  "priority": "P0",
  "reason": "详细的决策理由",
  "test_types": ["功能测试", "接口测试"],
  "estimated_effort": "2小时",
  "risk_level": "高"
}
```

**再次强调：只输出JSON，不要任何解释或说明！**
"""
        
        return prompt
    
    def _build_analysis_prompt_v4(self, requirement: str, git_diff: str, 
                                  parsed_modules: List[Dict[str, Any]],
                                  knowledge: Optional[Dict[str, Any]]) -> str:
        """
        V4增强：构建分析prompt（包含解析的模块信息 + 知识库信息）
        
        Args:
            requirement: 需求文本
            git_diff: 代码变更
            parsed_modules: 已解析的模块列表
            knowledge: 知识库检索结果
            
        Returns:
            增强的prompt
        """
        # 格式化模块信息
        modules_context = self._format_modules_context(parsed_modules)
        
        prompt = f"""# 测试决策分析任务（V4增强版 - 知识库支持）

## 已解析的模块信息
{modules_context}

## 需求描述
{requirement}
"""
        
        if git_diff:
            prompt += f"""
## 代码变更
```diff
{git_diff[:2000]}
```
"""
        
        # V4增强：添加知识库信息
        if knowledge and not knowledge.get('fallback', False):
            prompt += f"""
## 知识库分析结果

**系统已自动分析相关API和代码，提供以下参考信息：**

- **相关API数量**: {len(knowledge.get('apis', []))}
- **识别模块**: {', '.join(knowledge.get('modules', []))}
- **建议优先级**: {knowledge.get('priority')}
- **风险评估**: {knowledge.get('risk_level')}
- **置信度**: {knowledge.get('confidence', 0):.2f}

**相关API列表**:
"""
            for i, api in enumerate(knowledge.get('apis', [])[:5], 1):
                prompt += f"\n{i}. {api.get('method')} {api.get('path')} - {api.get('summary', '')}"
            
            if len(knowledge.get('apis', [])) > 5:
                prompt += f"\n... 还有 {len(knowledge['apis']) - 5} 个相关API"
        
        prompt += """

## 分析要求

基于上述信息（包括知识库分析结果），请综合判断：
1. **是否需要测试**: 判断此变更是否需要执行测试
2. **影响模块**: 从已解析的模块中选择受影响的模块（使用模块名称）
3. **优先级**: 评估测试优先级（P0/P1/P2），参考知识库建议
4. **原因**: 说明决策理由
5. **测试类型**: 需要执行的测试类型
6. **预估工作量**: 测试所需时间
7. **风险等级**: 评估风险（高/中/低），参考知识库评估

## 输出格式

**重要：只返回JSON，不要任何说明文字！**

```json
{
  "need_test": true,
  "modules": ["模块1", "模块2"],
  "priority": "P0",
  "reason": "详细的决策理由",
  "test_types": ["功能测试", "接口测试"],
  "estimated_effort": "2小时",
  "risk_level": "高"
}
```

**再次强调：只输出JSON，不要任何解释或说明！**
"""
        
        return prompt
    
    def _get_system_prompt(self) -> str:
        """获取系统prompt"""
        return """你是一个专业的测试决策专家，负责分析软件需求和代码变更，判断是否需要执行测试。

你的职责：
1. 准确判断变更的影响范围
2. 评估测试的必要性和优先级
3. 给出清晰的决策理由
4. 输出标准的JSON格式结果
5. 评估风险等级和工作量

你的特点：
- 专业：深入理解软件测试理论和实践
- 严谨：基于事实和规则做出判断
- 高效：快速识别关键风险点
- 清晰：给出明确的决策建议

**关键要求：只返回JSON，不要任何说明文字！**

输出必须是纯JSON格式，不要包含任何解释、说明或markdown标记。"""
    
    def _format_modules_context(self, modules: List[Dict[str, Any]]) -> str:
        """格式化模块信息为上下文"""
        if not modules:
            return "暂无模块信息"
        
        lines = []
        for i, module in enumerate(modules, 1):
            lines.append(f"{i}. **{module.get('name', '未知模块')}**")
            lines.append(f"   - 描述: {module.get('description', '无')}")
            lines.append(f"   - 功能: {', '.join(module.get('functions', []))}")
            lines.append(f"   - 优先级: {module.get('priority', '中')}")
            lines.append(f"   - 复杂度: {module.get('complexity', '中等')}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _normalize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """规范化LLM返回结果"""
        # 确保必需字段存在
        normalized = {
            "need_test": result.get("need_test", True),
            "modules": result.get("modules", []),
            "priority": result.get("priority", "P1"),
            "reason": result.get("reason", "需要进一步分析"),
            "test_types": result.get("test_types", ["功能测试"]),
            "estimated_effort": result.get("estimated_effort", "未评估"),
            "risk_level": result.get("risk_level", "中")
        }
        
        # 验证priority格式
        if normalized["priority"] not in ["P0", "P1", "P2"]:
            normalized["priority"] = "P1"
        
        # 确保modules是列表
        if not isinstance(normalized["modules"], list):
            normalized["modules"] = [str(normalized["modules"])]
        
        return normalized
    
    def _get_default_decision_v3(self, error_msg: str, parsed_modules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        V3版本：获取默认决策（包含解析的模块信息）
        
        Args:
            error_msg: 错误信息
            parsed_modules: 已解析的模块列表
            
        Returns:
            默认决策结果
        """
        module_names = [m.get('name', '') for m in parsed_modules] if parsed_modules else []
        
        base_result = {
            "need_test": False,
            "modules": module_names,
            "priority": "P2",
            "reason": f"LLM解析失败，默认跳过。错误: {error_msg}",
            "test_types": [],
            "estimated_effort": "0",
            "risk_level": "低"
        }
        
        # 应用V2增强
        result = enhance_decision(base_result)
        
        # V3增强：添加解析的模块详情
        result['parsed_modules'] = parsed_modules
        result['parsed_sections'] = {}
        
        # 添加元数据
        result['analyzed_at'] = datetime.now().isoformat()
        result['duration'] = "0s"
        result['provider'] = "fallback"
        result['model'] = "default"
        result['version'] = "v3"
        
        return result
    
    def _get_default_decision_v4(self, error_msg: str, parsed_modules: List[Dict[str, Any]], 
                                 knowledge: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        V4版本：获取默认决策（包含解析的模块信息 + 知识库信息）
        
        Args:
            error_msg: 错误信息
            parsed_modules: 已解析的模块列表
            knowledge: 知识库检索结果
            
        Returns:
            默认决策结果
        """
        module_names = [m.get('name', '') for m in parsed_modules] if parsed_modules else []
        
        # 如果有知识库信息，使用知识库的判断
        if knowledge and not knowledge.get('fallback', False):
            base_result = {
                "need_test": True if knowledge.get('priority') in ['P0', 'P1'] else False,
                "modules": knowledge.get('modules', module_names),
                "priority": knowledge.get('priority', 'P2'),
                "reason": f"LLM解析失败，使用知识库判断。错误: {error_msg}",
                "test_types": ["接口测试"],
                "estimated_effort": "2小时",
                "risk_level": knowledge.get('risk_level', '低')
            }
        else:
            base_result = {
                "need_test": False,
                "modules": module_names,
                "priority": "P2",
                "reason": f"LLM解析失败，默认跳过。错误: {error_msg}",
                "test_types": [],
                "estimated_effort": "0",
                "risk_level": "低"
            }
        
        # 应用V2增强
        result = enhance_decision(base_result)
        
        # V3增强：添加解析的模块详情
        result['parsed_modules'] = parsed_modules
        result['parsed_sections'] = {}
        
        # V4增强：添加知识库信息
        if knowledge:
            result['knowledge'] = {
                'apis': knowledge.get('apis', []),
                'modules': knowledge.get('modules', []),
                'priority': knowledge.get('priority'),
                'risk_level': knowledge.get('risk_level'),
                'confidence': knowledge.get('confidence'),
                'fallback': knowledge.get('fallback', False)
            }
        
        # 添加元数据
        result['analyzed_at'] = datetime.now().isoformat()
        result['duration'] = "0s"
        result['provider'] = "fallback"
        result['model'] = "default"
        result['version'] = "v4"
        
        return result
    
    def _log_decision(self, requirement: str, git_diff: str, decision: Dict[str, Any]):
        """记录决策历史"""
        try:
            # 添加到内存历史
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "requirement": requirement[:200],  # 截断
                "git_diff": git_diff[:200] if git_diff else "",
                "decision": decision
            }
            self.decision_history.append(log_entry)
            
            # 保存到文件
            log_file = self.log_dir / f"decision_{datetime.now().strftime('%Y%m%d')}.jsonl"
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
                
        except Exception as e:
            print(f"⚠️  记录决策历史失败: {e}")
    
    def get_decision_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取决策历史"""
        return self.decision_history[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.decision_history:
            return {
                "total_decisions": 0,
                "need_test_count": 0,
                "no_test_count": 0,
                "priority_distribution": {}
            }
        
        total = len(self.decision_history)
        need_test = sum(1 for d in self.decision_history if d['decision']['need_test'])
        
        priority_dist = {}
        for d in self.decision_history:
            p = d['decision']['priority']
            priority_dist[p] = priority_dist.get(p, 0) + 1
        
        return {
            "total_decisions": total,
            "need_test_count": need_test,
            "no_test_count": total - need_test,
            "need_test_rate": f"{need_test/total*100:.1f}%",
            "priority_distribution": priority_dist
        }


# 全局服务实例
_test_agent_service = None

def get_test_agent_service() -> TestAgentService:
    """获取Test Agent服务实例"""
    global _test_agent_service
    if _test_agent_service is None:
        _test_agent_service = TestAgentService()
    return _test_agent_service
