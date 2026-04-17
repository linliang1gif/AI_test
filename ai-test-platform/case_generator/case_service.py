#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Case Service - 用例生成核心服务
整合传统流程的用例生成能力，提供统一的用例生成服务
"""

import json
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path

from .scenario_builder import ScenarioBuilder
from .case_builder import CaseBuilder


class CaseService:
    """用例生成服务"""
    
    def __init__(self):
        self.scenario_builder = ScenarioBuilder()
        self.case_builder = CaseBuilder()
        self.case_history = []
        self.log_dir = Path("output/case_logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_cases(self, strategy: dict) -> dict:
        """
        根据策略生成测试用例
        
        Args:
            strategy: Strategy Engine 的输出
            
        Returns:
            {
                "cases": [
                    {
                        "module": "模块名",
                        "cases": [用例列表]
                    }
                ],
                "total_cases": 总用例数,
                "generated_at": 生成时间,
                "source_strategy": 来源策略时间戳
            }
        """
        try:
            # 1. 提取策略信息
            strategy_list = strategy.get('strategy', [])
            
            if not strategy_list:
                print("⏭️  策略为空，返回空用例")
                return self._empty_cases(strategy)
            
            print(f"🎯 开始生成用例: {len(strategy_list)}个模块")
            
            # 2. 为每个模块生成用例
            all_cases = []
            total_count = 0
            
            for module_strategy in strategy_list:
                module_cases = self._generate_module_cases(module_strategy)
                all_cases.append(module_cases)
                total_count += len(module_cases['cases'])
                
                print(f"  ✅ {module_cases['module']}: {len(module_cases['cases'])}个用例")
            
            # 3. 构建结果
            result = {
                "cases": all_cases,
                "total_cases": total_count,
                "generated_at": datetime.now().isoformat(),
                "source_strategy": strategy.get('generated_at', '')
            }
            
            # 4. 记录历史
            self._log_cases(strategy, result)
            
            print(f"✅ 用例生成完成: {len(all_cases)}个模块, {total_count}个用例")
            
            return result
            
        except Exception as e:
            print(f"❌ 用例生成失败: {e}")
            import traceback
            traceback.print_exc()
            return self._empty_cases(strategy)
    
    def _generate_module_cases(self, module_strategy: Dict[str, Any]) -> Dict[str, Any]:
        """
        为单个模块生成用例
        
        Args:
            module_strategy: 单个模块的策略
            {
                "module": {"name": "...", "impact": "..."},
                "priority": "P0",
                "test_types": ["api", "ui"],
                "case_count": 10,
                "execution_order": 1,
                "risk_level": "高",
                "execution_hint": {"parallel": true, "timeout": 60}
            }
            
        Returns:
            {
                "module": "模块名",
                "cases": [用例列表]
            }
        """
        try:
            # 提取模块信息
            module_obj = module_strategy.get('module', {})
            module_name = module_obj.get('name', '未知模块')
            priority = module_strategy.get('priority', 'P1')
            test_types = module_strategy.get('test_types', ['api'])
            target_count = module_strategy.get('case_count', 5)
            
            # 构建模块信息（用于场景生成）
            # 传统组件需要完整的 module_info 格式
            module_info = {
                'id': f"mod_{module_name}",
                'name': module_name,
                'description': f"{module_name}功能模块",
                'functions': [f"{module_name}功能"],
                'priority': priority,
                'complexity': '中等',
                'test_types': test_types,
                'dependencies': []
            }
            
            # 1. 构建场景
            scenario_data = self.scenario_builder.build_scenarios(module_info)
            scenarios = scenario_data.get('scenarios', [])
            
            print(f"  📋 {module_name}: 生成了 {len(scenarios)} 个场景")
            
            # 2. 构建用例
            cases = self.case_builder.build_cases(
                module_info=module_info,
                scenarios=scenarios,
                target_count=target_count,
                priority=priority
            )
            
            return {
                "module": module_name,
                "cases": cases
            }
            
        except Exception as e:
            print(f"  ❌ 模块用例生成失败: {e}")
            import traceback
            traceback.print_exc()
            
            # 返回简化用例
            return {
                "module": module_strategy.get('module', {}).get('name', '未知模块'),
                "cases": []
            }
    
    def _empty_cases(self, strategy: dict) -> dict:
        """返回空用例"""
        return {
            "cases": [],
            "total_cases": 0,
            "generated_at": datetime.now().isoformat(),
            "source_strategy": strategy.get('generated_at', '')
        }
    
    def _log_cases(self, strategy: dict, cases: dict):
        """记录用例历史"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "strategy": {
                    "total_modules": strategy.get('total_modules'),
                    "total_cases": strategy.get('total_cases')
                },
                "cases": {
                    "total_cases": cases.get('total_cases'),
                    "modules": len(cases.get('cases', []))
                }
            }
            
            self.case_history.append(log_entry)
            
            # 保存到文件
            log_file = self.log_dir / f"cases_{datetime.now().strftime('%Y%m%d')}.jsonl"
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
                
        except Exception as e:
            print(f"⚠️  记录用例历史失败: {e}")
    
    def get_case_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取用例历史"""
        return self.case_history[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.case_history:
            return {
                "total_generations": 0,
                "total_cases": 0,
                "avg_cases_per_generation": 0
            }
        
        total = len(self.case_history)
        total_cases = sum(h['cases']['total_cases'] for h in self.case_history)
        
        return {
            "total_generations": total,
            "total_cases": total_cases,
            "avg_cases_per_generation": round(total_cases / total, 2) if total > 0 else 0
        }


# 全局服务实例
_case_service = None

def get_case_service() -> CaseService:
    """获取用例服务实例"""
    global _case_service
    if _case_service is None:
        _case_service = CaseService()
    return _case_service
