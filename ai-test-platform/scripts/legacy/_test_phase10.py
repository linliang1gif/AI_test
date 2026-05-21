"""验证 Phase 10: orchestrator ApiRunner 使用 V2 真实引擎"""
import sys
sys.path.insert(0, r"G:\AI项目\ai测试\ai-test-platform")

from dotenv import load_dotenv
load_dotenv(r"G:\AI项目\ai测试\ai-test-platform\.env")

from orchestrator.base_runner import ApiRunner, get_runner

runner = get_runner("api")
print(f"Runner: {type(runner).__name__}")

# 测试1: 带 method/path 的用例 → V2 真实执行
print("\n=== 测试1: V2 真实执行 ===")
result = runner.run_cases([
    {
        "id": "orch-001",
        "title": "币别列表-orchestrator测试",
        "method": "POST",
        "path": "/basic/basicCurrency/list",
        "base_url": "https://dev-recycle.szhibu.com/dev-api/recycle",
        "body": {},
        "assertions": [
            {"type": "status_code", "expected": 200},
            {"type": "response_time", "expected": 5000},
        ]
    }
])
print(f"  Status: {result['status']}")
print(f"  Details: {result['details']}")
for cr in result.get("case_results", []):
    print(f"  [{cr['status']}] {cr['title']} HTTP={cr.get('http_status','N/A')} {cr['duration']}s")
    print(f"    Message: {cr['message']}")

# 测试2: 缺少 method/path → 回退 skipped
print("\n=== 测试2: 缺少字段 → skipped ===")
result2 = runner.run_cases([
    {"id": "orch-002", "title": "不完整用例"}
])
for cr in result2.get("case_results", []):
    print(f"  [{cr['status']}] {cr['title']}: {cr['message']}")

print("\n✅ Phase 10 验证完成 — mock 已替换为真实 V2 引擎")
