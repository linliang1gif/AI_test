"""验证 Phase 9: AI 智能断言生成"""
import sys
sys.path.insert(0, r"G:\AI项目\ai测试\ai-test-platform")

# 加载 .env
from dotenv import load_dotenv
load_dotenv(r"G:\AI项目\ai测试\ai-test-platform\.env")

import os
print(f"DEEPSEEK_API_KEY: {os.getenv('DEEPSEEK_API_KEY', '')[:15]}...")
print(f"DEEPSEEK_BASE_URL: {os.getenv('DEEPSEEK_BASE_URL', '')}")

from app.executor_v2.ai_assertion_gen import generate_assertions_batch

apis = [
    {
        "path": "/purchaseOrder/page",
        "method": "POST",
        "summary": "采购订单-分页列表",
        "tags": ["采购订单"],
    },
    {
        "path": "/basic/basicCurrency/list",
        "method": "POST",
        "summary": "币别-列表(启用)",
        "tags": ["币别"],
    },
    {
        "path": "/basic/basicWarehouseInfo/page",
        "method": "POST",
        "summary": "仓库-分页查询",
        "tags": ["仓库"],
    },
]

print(f"\n向 DeepSeek 发送 {len(apis)} 个 API 定义...")
result = generate_assertions_batch(apis, max_apis=10)

print(f"\n生成结果:")
for key, assertions in result.items():
    print(f"\n  {key}:")
    for a in assertions:
        print(f"    - {a['type']}: expected={a.get('expected')} path={a.get('path', '')}")

total = sum(len(v) for v in result.values())
print(f"\n共生成 {total} 条断言")
print("✅ Phase 9 AI 智能断言验证完成")
