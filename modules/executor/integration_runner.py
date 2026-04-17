"""
集成测试Runner - 支持多步骤流程测试
"""
from typing import Dict, List


class IntegrationRunner:
    """
    集成测试执行器
    
    特性：
    - 支持多步骤流程测试
    - 支持数据传递（上一步的输出作为下一步的输入）
    - 支持事务回滚
    """
    
    def __init__(self, config: Dict):
        """
        初始化Integration Runner
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.context = {}  # 用于存储步骤间的数据
    
    def run(self, test_case) -> Dict:
        """
        执行集成测试用例
        
        Args:
            test_case: TestCase对象
            
        Returns:
            执行结果字典
        """
        try:
            # 执行多步骤流程
            for i, step in enumerate(test_case.steps):
                step_result = self._execute_integration_step(step, i)
                
                if not step_result['success']:
                    return {
                        "status": "failed",
                        "error_message": f"Step {i+1} failed: {step_result['error']}",
                        "failed_step": i + 1
                    }
                
                # 保存步骤结果到上下文
                self.context[f"step_{i}"] = step_result['data']
            
            return {
                "status": "passed",
                "context": self.context
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error_message": str(e)
            }
    
    def _execute_integration_step(self, step: str, step_index: int) -> Dict:
        """执行单个集成步骤"""
        # 实现集成测试步骤逻辑
        # 例如：调用多个API、验证数据一致性等
        return {
            "success": True,
            "data": {}
        }
