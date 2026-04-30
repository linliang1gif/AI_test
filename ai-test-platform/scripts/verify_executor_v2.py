"""验收测试: Executor V2 后端API"""
import requests
import json

BASE = "http://localhost:8000"

def test_single_execute():
    print("=== Test 1: 单个用例执行 ===")
    resp = requests.post(f"{BASE}/api/v2/execute", json={
        "title": "GET /get - httpbin 连通测试",
        "method": "GET",
        "path": "/get",
        "base_url": "https://httpbin.org",
        "query_params": {"hello": "world"},
        "assertions": [
            {"type": "status_code", "expected": 200},
            {"type": "response_time", "expected": 10000},
            {"type": "field_exists", "path": "args"},
            {"type": "json_path", "path": "args.hello", "expected": "world"},
        ]
    })
    data = resp.json()
    result = data["result"]
    print(f"  Success: {data['success']}")
    print(f"  Status: {result['status']}")
    print(f"  HTTP Code: {result['response']['status_code']}")
    print(f"  Duration: {result['duration_ms']:.0f}ms")
    for a in result["assertions"]:
        mark = "PASS" if a["passed"] else "FAIL"
        print(f"  [{mark}] {a['type']}: expected={a['expected']}, actual={a['actual']}")
    assert data["success"] is True
    assert result["status"] == "passed"
    return data["run_id"]


def test_no_base_url():
    print("\n=== Test 2: 无 base_url 使用 .env 配置的 BASE_TEST_URL ===")
    resp = requests.post(f"{BASE}/api/v2/execute", json={
        "title": "fallback to config base_url",
        "method": "GET",
        "path": "/nonexistent",
    })
    data = resp.json()
    print(f"  Status code: {resp.status_code}")
    # 如果 .env 配了 BASE_TEST_URL, 会使用该值尝试请求
    # 如果没配则返回400错误
    if resp.status_code == 400:
        detail = data.get("detail", "")
        print(f"  Detail: {detail[:100]}")
        assert "未配置测试环境地址" in detail
    else:
        # fallback 到了 config 的 base_url, 可能连接失败但不报400
        result = data.get("result", {})
        status = result.get("status", "")
        print(f"  Fallback执行, status: {status}")
        print(f"  说明: .env 中配置了 BASE_TEST_URL, 作为 fallback 使用")
        assert data.get("success") is True


def test_query_run(run_id):
    print(f"\n=== Test 3: 查询运行结果 run_id={run_id} ===")
    resp = requests.get(f"{BASE}/api/v2/execute/runs/{run_id}")
    data = resp.json()
    print(f"  Summary: {data['summary']}")
    print(f"  Results count: {len(data['results'])}")
    assert data["success"] is True
    assert data["summary"]["total"] >= 1


def test_batch_execute():
    print("\n=== Test 4: 批量执行 ===")
    resp = requests.post(f"{BASE}/api/v2/execute/batch", json={
        "base_url": "https://httpbin.org",
        "cases": [
            {
                "title": "GET /get",
                "method": "GET",
                "path": "/get",
                "assertions": [{"type": "status_code", "expected": 200}]
            },
            {
                "title": "POST /post",
                "method": "POST",
                "path": "/post",
                "body": {"name": "test"},
                "assertions": [
                    {"type": "status_code", "expected": 200},
                    {"type": "field_exists", "path": "json"},
                ]
            },
            {
                "title": "GET /status/404 - 预期失败",
                "method": "GET",
                "path": "/status/404",
                "assertions": [{"type": "status_code", "expected": 200}]
            },
        ]
    })
    data = resp.json()
    summary = data["summary"]
    print(f"  Success: {data['success']}")
    print(f"  Summary: {summary}")
    for r in data["results"]:
        print(f"  [{r['status']:>6}] {r['case_title']} ({r['duration_ms']:.0f}ms)")

    assert data["success"] is True
    assert summary["total"] == 3
    assert summary["passed"] == 2  # /get and /post pass
    assert summary["failed"] == 1  # /status/404 fails assertion
    return data["run_id"]


def test_result_detail(run_id):
    print(f"\n=== Test 5: 查询单条详情 ===")
    # Get run results first
    resp = requests.get(f"{BASE}/api/v2/execute/runs/{run_id}")
    results = resp.json()["results"]
    record_id = results[0]["id"]
    
    resp2 = requests.get(f"{BASE}/api/v2/execute/results/{record_id}")
    data = resp2.json()
    result = data["result"]
    print(f"  Record ID: {record_id}")
    print(f"  Case: {result['case_title']}")
    print(f"  Has request: {result['request'] is not None}")
    print(f"  Has response: {result['response'] is not None}")
    print(f"  Has assertions: {len(result['assertions'])} items")
    assert data["success"] is True
    assert result["request"] is not None
    assert result["response"] is not None


if __name__ == "__main__":
    run_id = test_single_execute()
    test_no_base_url()
    test_query_run(run_id)
    batch_run_id = test_batch_execute()
    test_result_detail(batch_run_id)
    print("\n" + "=" * 50)
    print("ALL 5 TESTS PASSED - Executor V2 验收通过!")
    print("=" * 50)
