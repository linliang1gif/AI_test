"""
Self-Healing Service - 自动修复服务
分析错误、应用修复、重新执行测试
"""
import json
import time
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

from .analyzer import analyze_error, extract_error_context, calculate_fix_confidence
from .fixer import apply_fix, get_fix_strategy


class HealingService:
    """自动修复服务"""
    
    def __init__(self):
        self.healing_history = []
        self.log_dir = Path("output/healing_logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.max_retry = 1  # 最多重试1次，防止死循环
    
    def fix_and_retry(self, failure_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        修复并重试
        
        Args:
            failure_info: 失败信息 {
                "module": str,
                "error": str,
                "test_type": str
            }
            
        Returns:
            修复结果
        """
        try:
            module = failure_info.get("module", "未知模块")
            error = failure_info.get("error", "")
            test_type = failure_info.get("test_type", "api")
            
            print(f"\n🔧 Self-Healing 启动")
            print(f"   模块: {module}")
            print(f"   错误: {error[:100]}...")
            
            # 1. 分析错误
            print(f"\n   📊 分析错误...")
            error_analysis = analyze_error(error, module, test_type)
            error_context = extract_error_context(error)
            
            print(f"      类型: {error_analysis['type']}")
            print(f"      严重程度: {error_analysis['severity']}")
            print(f"      可修复: {error_analysis['fixable']}")
            
            # 2. 检查是否可修复
            if not error_analysis['fixable']:
                print(f"   ❌ 无法自动修复")
                return self._create_result(
                    fixed=False,
                    reason=error_analysis['details'],
                    error_analysis=error_analysis
                )
            
            # 3. 应用修复
            print(f"\n   🔨 应用修复...")
            fix_result = apply_fix(error_analysis['type'], module, error_context)
            
            print(f"      修复策略: {fix_result['fix_applied']}")
            
            # 4. 计算修复置信度
            confidence = calculate_fix_confidence(
                error_analysis['type'],
                error_analysis['severity']
            )
            
            # 5. 重试测试
            retry_result = None
            if fix_result['retry']:
                print(f"\n   🔄 重新执行测试...")
                retry_result = self._retry_test(module, test_type, fix_result['modifications'])
                
                print(f"      重试结果: {retry_result['status']}")
                print(f"      耗时: {retry_result['duration']}s")
            
            # 6. 构建结果
            result = self._create_result(
                fixed=True,
                reason=fix_result['fix_applied'],
                error_analysis=error_analysis,
                fix_result=fix_result,
                retry_result=retry_result,
                confidence=confidence
            )
            
            # 7. 记录历史
            self._log_healing(failure_info, result)
            
            if retry_result and retry_result['status'] == 'passed':
                print(f"\n   ✅ 修复成功！")
            else:
                print(f"\n   ⚠️  修复后仍失败")
            
            return result
            
        except Exception as e:
            print(f"\n   ❌ 修复过程异常: {e}")
            return self._create_result(
                fixed=False,
                reason=f"修复过程异常: {str(e)}"
            )
    
    def _retry_test(self, module: str, test_type: str, modifications: Dict[str, Any]) -> Dict[str, Any]:
        """
        重新执行测试
        
        Args:
            module: 模块名称
            test_type: 测试类型
            modifications: 修复修改
            
        Returns:
            重试结果
        """
        start = time.time()
        
        try:
            # Mock: 模拟重新执行测试
            # 实际应该调用 orchestrator 或 runner
            
            # 模拟修复后的成功率（70%）
            import random
            success = random.random() < 0.7
            
            time.sleep(0.1)  # 模拟执行时间
            
            duration = time.time() - start
            
            if success:
                return {
                    "status": "passed",
                    "duration": round(duration, 2),
                    "details": f"修复后重试成功: {module}",
                    "modifications_applied": modifications
                }
            else:
                return {
                    "status": "failed",
                    "duration": round(duration, 2),
                    "details": f"修复后重试仍失败: {module}",
                    "modifications_applied": modifications
                }
                
        except Exception as e:
            duration = time.time() - start
            return {
                "status": "error",
                "duration": round(duration, 2),
                "details": f"重试异常: {str(e)}",
                "modifications_applied": modifications
            }
    
    def _create_result(
        self,
        fixed: bool,
        reason: str,
        error_analysis: Dict[str, Any] = None,
        fix_result: Dict[str, Any] = None,
        retry_result: Dict[str, Any] = None,
        confidence: float = 0.0
    ) -> Dict[str, Any]:
        """创建标准结果格式"""
        result = {
            "fixed": fixed,
            "reason": reason,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        }
        
        if error_analysis:
            result["error_analysis"] = error_analysis
        
        if fix_result:
            result["fix_strategy"] = fix_result['fix_applied']
            result["modifications"] = fix_result['modifications']
        
        if retry_result:
            result["retry_result"] = retry_result
        
        return result
    
    def _log_healing(self, failure_info: Dict[str, Any], result: Dict[str, Any]):
        """记录修复历史"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "failure_info": failure_info,
                "healing_result": result
            }
            
            self.healing_history.append(log_entry)
            
            # 保存到文件
            log_file = self.log_dir / f"healing_{datetime.now().strftime('%Y%m%d')}.jsonl"
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
                
        except Exception as e:
            print(f"⚠️  记录修复历史失败: {e}")
    
    def get_healing_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取修复历史"""
        return self.healing_history[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.healing_history:
            return {
                "total_healings": 0,
                "successful_fixes": 0,
                "failed_fixes": 0,
                "success_rate": 0.0,
                "avg_confidence": 0.0
            }
        
        total = len(self.healing_history)
        successful = sum(
            1 for h in self.healing_history 
            if h['healing_result'].get('fixed') and 
               h['healing_result'].get('retry_result', {}).get('status') == 'passed'
        )
        
        confidences = [
            h['healing_result'].get('confidence', 0.0)
            for h in self.healing_history
        ]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return {
            "total_healings": total,
            "successful_fixes": successful,
            "failed_fixes": total - successful,
            "success_rate": round(successful / total * 100, 2) if total > 0 else 0.0,
            "avg_confidence": round(avg_confidence, 2)
        }
    
    def get_fix_suggestions(self, error_type: str) -> List[str]:
        """
        获取修复建议
        
        Args:
            error_type: 错误类型
            
        Returns:
            修复建议列表
        """
        suggestions = {
            "assertion": [
                "检查期望值是否正确",
                "验证响应格式是否变化",
                "考虑放宽断言条件"
            ],
            "timeout": [
                "增加超时时间",
                "检查网络连接",
                "优化请求性能"
            ],
            "server_error": [
                "检查服务器状态",
                "添加重试机制",
                "查看服务器日志"
            ],
            "not_found": [
                "验证 API 路径",
                "检查 API 版本",
                "确认资源是否存在"
            ],
            "auth_error": [
                "刷新认证 token",
                "检查权限配置",
                "验证用户凭证"
            ],
            "connection": [
                "检查服务是否启动",
                "验证网络连接",
                "检查防火墙设置"
            ]
        }
        
        return suggestions.get(error_type, ["需要人工分析"])


# 全局服务实例
_healing_service = None

def get_healing_service() -> HealingService:
    """获取修复服务实例"""
    global _healing_service
    if _healing_service is None:
        _healing_service = HealingService()
    return _healing_service
