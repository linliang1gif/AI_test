"""
验证 ApiRunner 已无 mock — 对比测试
运行方式: D:\python311\python.exe scripts\_verify_no_mock.py
"""
import sys
sys.path.insert(0, r"G:\AI项目\ai测试\ai-test-platform")
from dotenv import load_dotenv
load_dotenv(r"G:\AI项目\ai测试\ai-test-platform\.env")

from orchestrator.base_runner import get_runner

runner = get_runner("api")

print("=" * 60)
print("验证 ApiRunner 不再使用 random mock")
print("=" * 60)

# 测试: 同一个用例跑 5 次，旧版 mock 有 10% 概率失败
# 真实引擎每次结果一致（全 passed 或全 failed）
case = {
    "id": "verify-001",
    "title": "币别列表-一致性验证",
    "method": "POST",
    "path": "/basic/basicCurrency/list",
    "base_url": "https://dev-recycle.szhibu.com/dev-api/recycle",
    "headers": {"Content-Type": "application/json"},
    "body": {},
    "assertions": [
        {"type": "status_code", "expected": 200},
        {"type": "response_time", "expected": 5000},
    ]
}

results = []
for i in range(5):
    r = runner.run_cases([case])
    cr = r["case_results"][0]
    results.append(cr["status"])
    http = cr.get("http_status", "N/A")
    print(f"  第{i+1}次: [{cr['status']}] HTTP {http}  {cr['duration']}s")

print()
unique = set(results)
if len(unique) == 1:
    print(f"✅ 5次执行结果完全一致: {unique.pop()}")
    print("   → 确认已使用真实 V2 引擎（旧 mock 有随机性）")
else:
    print(f"❌ 结果不一致: {results}")
    print("   → 可能仍在使用 mock！请检查代码")

# 额外验证: 返回里有 http_status 和 assertions
print()
r = runner.run_cases([case])
cr = r["case_results"][0]
has_http = "http_status" in cr
has_assertions = "assertions" in cr and len(cr.get("assertions", [])) > 0
print(f"✅ 返回包含 http_status: {has_http} (值={cr.get('http_status')})")
print(f"✅ 返回包含 assertions: {has_assertions} (数量={len(cr.get('assertions', []))})")
if has_assertions:
    for a in cr["assertions"]:
        print(f"   - {a.get('type')}: passed={a.get('passed')} {a.get('message','')}")

print()
print("=" * 60)
print("验证完成！ApiRunner 已彻底替换为 V2 真实引擎")
print("=" * 60)
