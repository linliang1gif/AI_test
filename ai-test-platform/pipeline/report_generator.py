"""
Report Generator V2 - 测试报告生成器（可观测中心）

新增能力：
1. 覆盖率分析（基于用例）
2. 传统覆盖率模块接入
3. AI 总结增强

最终目标：Report = 可观测中心
"""
import json
import sys
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

# 尝试导入传统覆盖率分析器
try:
    from app.coverage_analyzer.coverage_analyzer import CoverageAnalyzer
    _coverage_analyzer_available = True
except ImportError:
    _coverage_analyzer_available = False
    print("⚠️  传统覆盖率分析器不可用")


def generate_report(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    生成测试报告 V2
    
    新增能力：
    1. 覆盖率分析（基于用例）
    2. 传统覆盖率模块接入
    3. AI 总结增强
    
    Args:
        context: Pipeline context（包含所有阶段数据）
        
    Returns:
        增强的测试报告
    """
    decision = context.get('decision', {})
    strategy = context.get('strategy', {})
    cases = context.get('cases', {})
    execution = context.get('execution', {})
    healing = context.get('healing', {})
    
    # 1. 构建摘要
    summary = _build_summary(decision, execution, healing)
    
    # 2. 构建详情
    details = _build_details(execution, healing)
    
    # 3. 覆盖率分析（新增）
    coverage = _analyze_coverage(strategy, cases, execution)
    
    # 4. 传统覆盖率接入（新增）
    traditional_coverage = _analyze_traditional_coverage(context)
    
    # 5. AI 总结增强（新增）
    ai_analysis = generate_ai_summary_v2(context, coverage)
    
    return {
        "summary": summary,
        "details": details,
        "coverage": coverage,  # 新增
        "traditional_coverage": traditional_coverage,  # 新增
        "ai_analysis": ai_analysis,
        "generated_at": datetime.now().isoformat()
    }


def _build_summary(decision: Dict[str, Any], execution: Dict[str, Any], healing: Dict[str, Any]) -> Dict[str, Any]:
    """构建报告摘要"""
    
    # 如果跳过执行
    if decision.get('action') in ['skip', 'skip_test']:
        return {
            "status": "skipped",
            "reason": decision.get('reason', '无需测试'),
            "total": 0,
            "passed": 0,
            "failed": 0
        }
    
    # 从执行结果获取统计
    exec_summary = execution.get('summary', {})
    total = exec_summary.get('total', 0)
    passed = exec_summary.get('passed', 0)
    failed = exec_summary.get('failed', 0)
    
    # 如果有修复
    if healing:
        healing_stats = healing.get('statistics', {})
        healed = healing_stats.get('successful_fixes', 0)
        
        # 修复成功的算作通过
        passed += healed
        failed -= healed
    
    # 确定最终状态
    if total == 0:
        status = "no_tests"
    elif failed == 0:
        status = "passed"
    elif passed > 0:
        status = "partial"
    else:
        status = "failed"
    
    return {
        "status": status,
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": round(passed / total * 100, 2) if total > 0 else 0.0
    }


def _build_details(execution: Dict[str, Any], healing: Dict[str, Any]) -> List[Dict[str, Any]]:
    """构建详细信息"""
    details = []
    
    # 如果没有执行数据，返回空列表
    if not execution:
        return details
    
    # 执行结果
    results = execution.get('results', [])
    
    for result in results:
        detail = {
            "module": result.get('module', '未知'),
            "status": result.get('status', 'unknown'),
            "duration": result.get('duration', 0.0),
            "details": result.get('details', ''),
            "healed": False
        }
        
        # 检查是否被修复
        if healing and result.get('status') == 'failed':
            healing_records = healing.get('records', [])
            for record in healing_records:
                if record.get('module') == result.get('module'):
                    detail['healed'] = record.get('fixed', False)
                    detail['healing_strategy'] = record.get('fix_strategy', '')
                    break
        
        details.append(detail)
    
    return details


def _analyze_coverage(strategy: Dict[str, Any], cases: Dict[str, Any], execution: Dict[str, Any]) -> Dict[str, Any]:
    """
    覆盖率分析（新增）
    
    如果 cases 存在：
        coverage = executed_cases / total_cases
    
    Args:
        strategy: 策略数据
        cases: 用例数据
        execution: 执行数据
        
    Returns:
        覆盖率分析结果
    """
    coverage_data = {
        "mode": "unknown",
        "total_cases": 0,
        "executed_cases": 0,
        "coverage_rate": 0.0,
        "module_coverage": []
    }
    
    try:
        # 如果有用例数据（Case Generator 模式）
        if cases and cases.get('cases'):
            coverage_data["mode"] = "case_based"
            
            # 总用例数
            total_cases = cases.get('total_cases', 0)
            coverage_data["total_cases"] = total_cases
            
            # 统计执行的用例数
            executed_cases = 0
            module_coverage_list = []
            
            execution_results = execution.get('results', [])
            
            for module_result in execution_results:
                module_name = module_result.get('module', '未知')
                case_results = module_result.get('case_results', [])
                
                # 统计该模块的用例数
                module_total = len(case_results)
                module_executed = sum(1 for cr in case_results if cr.get('status') in ['passed', 'failed'])
                
                executed_cases += module_executed
                
                module_coverage_list.append({
                    "module": module_name,
                    "total": module_total,
                    "executed": module_executed,
                    "coverage_rate": round(module_executed / module_total * 100, 2) if module_total > 0 else 0.0
                })
            
            coverage_data["executed_cases"] = executed_cases
            coverage_data["coverage_rate"] = round(executed_cases / total_cases * 100, 2) if total_cases > 0 else 0.0
            coverage_data["module_coverage"] = module_coverage_list
            
        # 如果只有策略数据（Strategy 模式）
        elif strategy and strategy.get('strategy'):
            coverage_data["mode"] = "strategy_based"
            
            strategy_list = strategy.get('strategy', [])
            total_cases = sum(s.get('case_count', 0) for s in strategy_list)
            
            coverage_data["total_cases"] = total_cases
            coverage_data["executed_cases"] = total_cases  # 策略模式假设全部执行
            coverage_data["coverage_rate"] = 100.0
            
            # 模块级别覆盖率
            for strategy_item in strategy_list:
                module_name = strategy_item.get('module', {}).get('name', '未知')
                case_count = strategy_item.get('case_count', 0)
                
                coverage_data["module_coverage"].append({
                    "module": module_name,
                    "total": case_count,
                    "executed": case_count,
                    "coverage_rate": 100.0
                })
        
    except Exception as e:
        print(f"⚠️  覆盖率分析失败: {e}")
    
    return coverage_data


def _analyze_traditional_coverage(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    传统覆盖率模块接入（新增）
    
    调用 app/coverage_analyzer/coverage_analyzer.py
    
    Args:
        context: Pipeline context
        
    Returns:
        传统覆盖率分析结果
    """
    if not _coverage_analyzer_available:
        return {
            "available": False,
            "message": "传统覆盖率分析器不可用"
        }
    
    try:
        # 尝试调用传统覆盖率分析器
        # 注意：传统分析器需要特定格式的输入，这里做简化处理
        
        return {
            "available": True,
            "message": "传统覆盖率分析器可用，但需要完整的需求和测试数据",
            "note": "当前 Pipeline 模式下暂不调用传统分析器"
        }
        
    except Exception as e:
        return {
            "available": False,
            "error": str(e)
        }


def generate_ai_summary_v2(context: Dict[str, Any], coverage: Dict[str, Any]) -> str:
    """
    生成 AI 总结 V2（增强版）
    
    Prompt: "分析测试执行结果、失败原因和覆盖率"
    
    输出：
    {
        "summary": "...",
        "coverage": "85%",
        "risk": "高"
    }
    
    Args:
        context: Pipeline context
        coverage: 覆盖率数据
        
    Returns:
        AI 总结（JSON 格式字符串）
    """
    try:
        # 尝试调用 LLM 生成总结
        from agent.llm_client import get_llm_client
        
        decision = context.get('decision', {})
        execution = context.get('execution') or {}
        healing = context.get('healing')
        
        # 安全获取执行数据
        exec_summary = execution.get('summary', {}) if execution else {}
        
        # 构建增强的 prompt
        prompt = f"""请分析本次测试执行结果、失败原因和覆盖率，并以JSON格式返回。

测试决策：
- 需要测试: {decision.get('need_test')}
- 风险等级: {decision.get('risk_level')}
- 测试类型: {', '.join(decision.get('test_types', []))}

执行结果：
- 总数: {exec_summary.get('total', 0)}
- 通过: {exec_summary.get('passed', 0)}
- 失败: {exec_summary.get('failed', 0)}
- 通过率: {exec_summary.get('pass_rate', 0)}%

覆盖率分析：
- 模式: {coverage.get('mode', 'unknown')}
- 总用例数: {coverage.get('total_cases', 0)}
- 已执行: {coverage.get('executed_cases', 0)}
- 覆盖率: {coverage.get('coverage_rate', 0)}%

修复情况：
- 修复次数: {len(healing.get('records', [])) if healing else 0}
- 成功修复: {healing.get('statistics', {}).get('successful_fixes', 0) if healing else 0}

请返回JSON格式：
{{
    "summary": "2-3句话总结测试结果和关键发现",
    "coverage": "覆盖率百分比（如85%）",
    "risk": "风险等级（高/中/低）",
    "key_findings": ["关键发现1", "关键发现2"],
    "recommendations": ["建议1", "建议2"]
}}"""

        client = get_llm_client()
        
        # 尝试生成 JSON 格式的总结
        summary_json = client.generate_json(prompt)
        
        if summary_json and isinstance(summary_json, dict):
            # 确保包含必要字段
            if 'summary' not in summary_json:
                summary_json['summary'] = _generate_rule_based_summary(context)
            if 'coverage' not in summary_json:
                summary_json['coverage'] = f"{coverage.get('coverage_rate', 0)}%"
            if 'risk' not in summary_json:
                summary_json['risk'] = decision.get('risk_level', '中')
            
            return json.dumps(summary_json, ensure_ascii=False)
        else:
            # Fallback
            return _generate_rule_based_summary_v2(context, coverage)
        
    except Exception as e:
        print(f"⚠️  AI 总结生成失败: {e}")
        # Fallback: 使用规则生成总结
        return _generate_rule_based_summary_v2(context, coverage)


def _generate_rule_based_summary_v2(context: Dict[str, Any], coverage: Dict[str, Any]) -> str:
    """基于规则生成总结 V2（Fallback）"""
    decision = context.get('decision', {})
    execution = context.get('execution') or {}
    healing = context.get('healing')
    
    exec_summary = execution.get('summary', {})
    total = exec_summary.get('total', 0)
    passed = exec_summary.get('passed', 0)
    failed = exec_summary.get('failed', 0)
    
    # 构建 JSON 格式的总结
    summary_obj = {
        "summary": "",
        "coverage": f"{coverage.get('coverage_rate', 0)}%",
        "risk": decision.get('risk_level', '中'),
        "key_findings": [],
        "recommendations": []
    }
    
    # 跳过执行
    if decision.get('action') in ['skip', 'skip_test']:
        summary_obj["summary"] = f"本次变更无需测试。原因：{decision.get('reason', '低风险变更')}。"
        summary_obj["risk"] = "低"
        return json.dumps(summary_obj, ensure_ascii=False)
    
    # 全部通过
    if failed == 0 and total > 0:
        summary_obj["summary"] = f"测试全部通过（{total}/{total}），覆盖率{coverage.get('coverage_rate', 0)}%。系统运行正常，无风险。"
        summary_obj["key_findings"] = ["所有测试通过", f"覆盖率达到{coverage.get('coverage_rate', 0)}%"]
        summary_obj["risk"] = "低"
        return json.dumps(summary_obj, ensure_ascii=False)
    
    # 部分失败
    if failed > 0:
        healed = healing.get('statistics', {}).get('successful_fixes', 0) if healing else 0
        
        if healed > 0:
            summary_obj["summary"] = f"测试发现 {failed} 个失败，已自动修复 {healed} 个。剩余 {failed - healed} 个需要人工处理。覆盖率{coverage.get('coverage_rate', 0)}%。"
            summary_obj["key_findings"] = [
                f"发现{failed}个失败",
                f"自动修复{healed}个",
                f"覆盖率{coverage.get('coverage_rate', 0)}%"
            ]
            summary_obj["recommendations"] = ["人工检查剩余失败用例", "分析失败原因并优化"]
        else:
            summary_obj["summary"] = f"测试发现 {failed} 个失败，无法自动修复。建议人工检查。覆盖率{coverage.get('coverage_rate', 0)}%。"
            summary_obj["key_findings"] = [
                f"发现{failed}个失败",
                "无法自动修复",
                f"覆盖率{coverage.get('coverage_rate', 0)}%"
            ]
            summary_obj["recommendations"] = ["立即人工检查失败用例", "分析根本原因"]
        
        return json.dumps(summary_obj, ensure_ascii=False)
    
    # 无测试
    summary_obj["summary"] = "未执行测试。"
    return json.dumps(summary_obj, ensure_ascii=False)




def generate_ai_summary(pipeline_data: Dict[str, Any]) -> str:
    """
    生成 AI 总结（原版本，保持兼容）
    
    Args:
        pipeline_data: 完整的流程数据
        
    Returns:
        AI 总结文本
    """
    try:
        # 尝试调用 LLM 生成总结
        from agent.llm_client import get_llm_client
        
        decision = pipeline_data.get('decision', {})
        execution = pipeline_data.get('execution', {})
        healing = pipeline_data.get('healing', {})
        
        # 构建 prompt
        prompt = f"""请总结本次测试结果，并指出风险点。

测试决策：
- 需要测试: {decision.get('need_test')}
- 风险等级: {decision.get('risk_level')}
- 测试类型: {decision.get('test_types')}

执行结果：
- 总数: {execution.get('summary', {}).get('total', 0)}
- 通过: {execution.get('summary', {}).get('passed', 0)}
- 失败: {execution.get('summary', {}).get('failed', 0)}

修复情况：
- 修复次数: {len(healing.get('records', []))}
- 成功修复: {healing.get('statistics', {}).get('successful_fixes', 0)}

请用2-3句话总结，重点指出风险。"""

        client = get_llm_client()
        summary = client.generate(prompt, max_tokens=200)
        
        return summary.strip()
        
    except Exception as e:
        # Fallback: 使用规则生成总结
        return _generate_rule_based_summary(pipeline_data)


def _generate_rule_based_summary(pipeline_data: Dict[str, Any]) -> str:
    """基于规则生成总结（Fallback）"""
    decision = pipeline_data.get('decision', {})
    execution = pipeline_data.get('execution', {})
    healing = pipeline_data.get('healing', {})
    
    exec_summary = execution.get('summary', {})
    total = exec_summary.get('total', 0)
    passed = exec_summary.get('passed', 0)
    failed = exec_summary.get('failed', 0)
    
    # 跳过执行
    if decision.get('action') in ['skip', 'skip_test']:
        return f"本次变更无需测试。原因：{decision.get('reason', '低风险变更')}。"
    
    # 全部通过
    if failed == 0 and total > 0:
        return f"测试全部通过（{total}/{total}）。系统运行正常，无风险。"
    
    # 部分失败
    if failed > 0:
        healed = healing.get('statistics', {}).get('successful_fixes', 0)
        
        if healed > 0:
            return f"测试发现 {failed} 个失败，已自动修复 {healed} 个。剩余 {failed - healed} 个需要人工处理。风险等级：{decision.get('risk_level', '中')}。"
        else:
            return f"测试发现 {failed} 个失败，无法自动修复。建议人工检查。风险等级：{decision.get('risk_level', '中')}。"
    
    # 无测试
    return "未执行测试。"
