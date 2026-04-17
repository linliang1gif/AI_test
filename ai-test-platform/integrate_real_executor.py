#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成真实测试执行器到backend_api_server.py
"""

import re

# 读取backend_api_server.py
with open('backend_api_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 要替换的旧代码模式
old_pattern = r'''                # 模拟测试执行
                await asyncio\.sleep\(2\)  # 模拟测试执行时间
                
                # 随机决定测试结果\(80%通过率\)
                import random
                test_passed = random\.random\(\) < 0\.8'''

# 新代码
new_code = '''                # 真实执行或模拟执行
                if use_real_executor:
                    # 使用真实测试执行器
                    result = await executor.execute_test_case(test_case)
                    test_passed = result["status"] == "passed"
                    result_message = result.get("message", "")
                    result_details = result.get("details", "")
                else:
                    # 模拟执行
                    await asyncio.sleep(2)
                    import random
                    test_passed = random.random() < 0.8
                    result_message = "模拟执行"
                    result_details = ""'''

# 替换
content = re.sub(old_pattern, new_code, content)

# 在_execute_test_run方法开始处添加执行器导入
old_start = r'''(async def _execute_test_run\(self, task_id: str, run_id: int, test_cases: List\[Dict\[str, Any\]\], resume: bool = False\):
        """执行测试运行.*?"""
        try:
            run = next\(\(r for r in self\.test_runs if r\["id"\] == run_id\), None\)
            if not run:
                return
            
            start_time = time\.time\(\))'''

new_start = r'''\1
            
            # 导入真实测试执行器
            try:
                from executor.real_test_executor import get_test_executor
                executor = get_test_executor()
                use_real_executor = True
            except ImportError:
                print("⚠️ 真实测试执行器不可用,使用模拟模式")
                use_real_executor = False'''

content = re.sub(old_start, new_start, content, flags=re.DOTALL)

# 更新日志消息
content = content.replace(
    'f"开始执行测试运行,共 {total_tests} 个测试用例"',
    'f"开始执行测试运行,共 {total_tests} 个测试用例 ({\'真实执行\' if use_real_executor else \'模拟执行\'})"'
)

# 更新通过日志
content = content.replace(
    'f"✓ {test_case[\'title\']} - 通过"',
    'f"✓ {test_case[\'title\']} - 通过 {result_details}"'
)

# 更新失败日志
content = content.replace(
    'f"✗ {test_case[\'title\']} - 失败"',
    'f"✗ {test_case[\'title\']} - 失败: {result_message}"'
)

# 保存
with open('backend_api_server.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 真实测试执行器集成完成!")
print("\n修改内容:")
print("1. 添加了真实测试执行器导入")
print("2. 替换了模拟执行逻辑为真实执行")
print("3. 更新了日志消息")
print("\n请重启后端服务器以应用更改")
