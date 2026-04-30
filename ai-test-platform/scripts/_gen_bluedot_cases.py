"""从蓝点 Swagger 生成测试用例并用 Executor V2 执行"""
import json
import requests

SWAGGER_FILE = r"G:\AI项目\ai测试\ai-test-platform\uploads\swagger\014d88e2-4405-4ec7-a921-7064c04857ab_bluedot_openapi.json"
BASE_URL = "https://dev-recycle.szhibu.com/dev-api/recycle"
BACKEND = "http://localhost:8000"

# 从 swagger 中选取测试接口
TEST_APIS = [
    {
        "title": "币别 - 分页查询",
        "method": "POST",
        "path": "/basic/basicCurrency/page",
        "body": {"pageNum": 1, "pageSize": 10},
    },
    {
        "title": "币别 - 列表(启用)",
        "method": "POST",
        "path": "/basic/basicCurrency/list",
        "body": {},
    },
    {
        "title": "汇率 - 分页查询",
        "method": "POST",
        "path": "/basic/basicExchangeRate/page",
        "body": {"pageNum": 1, "pageSize": 10},
    },
    {
        "title": "仓库 - 列表",
        "method": "POST",
        "path": "/basic/basicWarehouseInfo/list",
        "body": {},
    },
    {
        "title": "仓库分类 - 列表",
        "method": "POST",
        "path": "/basic/basicWarehouseClassification/list",
        "body": {},
    },
    {
        "title": "仓位 - 分页查询",
        "method": "POST",
        "path": "/basic/basicLocationInfo/page",
        "body": {"pageNum": 1, "pageSize": 10},
    },
    {
        "title": "客户信息 - 分页列表",
        "method": "POST",
        "path": "/davinci/crm/customer/page",
        "body": {"pageNum": 1, "pageSize": 10},
    },
    {
        "title": "文件下载(不存在ID) - 预期404或错误",
        "method": "GET",
        "path": "/applet/file/download/999999",
    },
]

# 为每个用例添加通用断言
cases = []
for api in TEST_APIS:
    case = {
        "title": api["title"],
        "method": api["method"],
        "path": api["path"],
        "headers": {"Content-Type": "application/json"},
        "assertions": [
            {"type": "response_time", "expected": 10000},
        ],
    }
    if "body" in api:
        case["body"] = api["body"]
    # POST 接口一般返回 200
    if api["method"] == "POST":
        case["assertions"].insert(0, {"type": "status_code", "expected": 200})
    cases.append(case)

print(f"准备执行 {len(cases)} 个蓝点接口测试")
print(f"目标服务: {BASE_URL}")
print("=" * 60)

# 调用 Executor V2 批量执行
resp = requests.post(
    f"{BACKEND}/api/v2/execute/batch",
    json={
        "base_url": BASE_URL,
        "cases": cases,
    },
    timeout=120,
)

data = resp.json()
if not data.get("success"):
    print(f"执行失败: {data}")
    exit(1)

summary = data["summary"]
results = data["results"]

print()
for r in results:
    status = r["status"].upper()
    title = r["case_title"]
    duration = r["duration_ms"]
    resp_code = r.get("response", {}).get("status_code", "N/A") if r.get("response") else "N/A"
    print(f"  [{status:>6}] {title}  (HTTP {resp_code}, {duration:.0f}ms)")
    
    # 如果失败，显示原因
    if r["status"] != "passed":
        if r.get("error_message"):
            print(f"          错误: {r['error_message'][:100]}")
        for a in r.get("assertions", []):
            if not a["passed"]:
                print(f"          断言失败: {a['type']} - {a['message']}")

print()
print("=" * 60)
print(f"汇总: {summary['passed']}/{summary['total']} 通过, "
      f"{summary['failed']} 失败, {summary.get('error', 0)} 错误")
print(f"总耗时: {summary['total_duration_ms']:.0f}ms")
print(f"Run ID: {data['run_id']}")
