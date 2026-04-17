import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from executor.pytest_runner import PytestRunner


class PytestSkill:
    """Pytest测试技能封装"""

    def __init__(self):
        self.runner = PytestRunner()

    def run(self, script_path):
        """
        执行pytest测试

        Args:
            script_path: 测试脚本路径

        Returns:
            {
                "success": bool,
                "result": dict,
                "error": str
            }
        """
        try:
            result = self.runner.run_tests(script_path)
            return {
                "success": result.get("success", False),
                "result": result,
                "error": result.get("error", "")
            }
        except Exception as e:
            return {
                "success": False,
                "result": {},
                "error": str(e)
            }
