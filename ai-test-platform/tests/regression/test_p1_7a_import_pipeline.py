#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P1-7A 真实项目导入链路修复 — 回归测试脚本

覆盖场景:
1. 普通公开 OpenAPI 导入
2. 带中文字段的 OpenAPI 导入
3. 带 Bearer Token 的 Swagger 检测和导入
4. YApi import-yapi 接口参数校验
5. 重复导入同一 source_url 返回 409
6. Token 不出现在响应中
7. check-swagger 返回 source_type
8. 编码安全（中文 title/description）

运行: python scripts/test_p1_7a_import_pipeline.py
前置: 后端 http://localhost:8000 已启动
"""
import json
import os
import sys
import time
import requests
from datetime import datetime

BASE_URL = "http://localhost:8000"
TS = int(time.time())


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


passed = 0
failed = 0
skipped = 0
results = []


def report(name, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
        tag = f"{Colors.GREEN}✅ PASS{Colors.END}"
    else:
        failed += 1
        tag = f"{Colors.RED}❌ FAIL{Colors.END}"
    line = f"{tag}  {name}"
    if detail:
        line += f"  ({detail})"
    print(line)
    results.append((name, ok, detail))


def create_project(suffix=""):
    """创建一个临时项目用于测试"""
    name = f"P1-7A-Test-{TS}{suffix}"
    resp = requests.post(f"{BASE_URL}/api/v2/projects", json={
        "name": name,
        "description": "P1-7A import pipeline test"
    }, timeout=10)
    if resp.status_code == 201:
        return resp.json()["id"], name
    return None, name


# =============================================================================
# 测试 1: 普通公开 OpenAPI 导入
# =============================================================================
def test_1_basic_import():
    print(f"\n{Colors.YELLOW}【测试1: 普通 OpenAPI URL 导入】{Colors.END}")
    pid, _ = create_project("-basic")
    if not pid:
        report("创建项目", False, "无法创建项目")
        return

    # 使用本地后端自身的 /openapi.json 作为公开 Swagger
    swagger_url = f"{BASE_URL}/openapi.json"

    # check-swagger
    check_resp = requests.post(f"{BASE_URL}/api/v2/real-project/check-swagger", json={
        "swagger_url": swagger_url,
        "timeout": 10
    }, timeout=15)
    check_data = check_resp.json()
    report("check-swagger 成功", check_data.get("success") is True, f"ops={check_data.get('swagger_info', {}).get('total_operations', '?')}")
    report("check-swagger 返回 source_type", check_data.get("source_type") in ("openapi", "swagger"), f"source_type={check_data.get('source_type')}")

    # import-url
    import_resp = requests.post(f"{BASE_URL}/api/v2/swagger/import-url", json={
        "project_id": pid,
        "url": swagger_url,
        "generate_cases": True
    }, timeout=30)
    report("import-url 成功", import_resp.status_code == 200, f"status={import_resp.status_code}")
    if import_resp.status_code == 200:
        data = import_resp.json()
        report("api_spec 落库", data.get("api_spec_id") is not None, f"api_spec_id={data.get('api_spec_id')}")
        report("test_cases 生成", data.get("test_cases_generated", 0) >= 0, f"count={data.get('test_cases_generated')}")

        # 检查响应中没有 Token
        resp_text = import_resp.text
        report("响应无 Token 泄漏", "Bearer" not in resp_text and "token" not in resp_text.lower().replace("token\":", ""), "checked response body")


# =============================================================================
# 测试 2: 带中文字段的 OpenAPI 导入（编码安全）
# =============================================================================
def test_2_chinese_openapi():
    print(f"\n{Colors.YELLOW}【测试2: 中文 OpenAPI 导入（编码安全）】{Colors.END}")

    # 生成临时中文 OpenAPI JSON 文件并通过 import-file 上传
    pid, _ = create_project("-chinese")
    if not pid:
        report("创建项目", False)
        return

    chinese_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "中文测试API — 商城后端",
            "version": "1.0.0",
            "description": "这是一个包含中文描述的接口文档，用于验证编码安全性。特殊字符：①②③"
        },
        "paths": {
            "/api/商品/列表": {
                "get": {
                    "summary": "获取商品列表（分页）",
                    "tags": ["商品管理"],
                    "responses": {"200": {"description": "成功返回商品列表"}}
                }
            },
            "/api/订单/创建": {
                "post": {
                    "summary": "创建订单",
                    "tags": ["订单管理"],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "商品ID": {"type": "integer"},
                                        "数量": {"type": "integer"},
                                        "备注": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "订单创建成功"}}
                }
            }
        }
    }

    # 使用文件上传接口
    file_content = json.dumps(chinese_spec, ensure_ascii=False).encode('utf-8')
    files = {"file": ("chinese_swagger.json", file_content, "application/json")}
    resp = requests.post(
        f"{BASE_URL}/api/v2/swagger/import-file",
        params={"project_id": pid, "generate_cases": True},
        files=files,
        timeout=30
    )
    report("中文 OpenAPI 文件导入", resp.status_code == 200, f"status={resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        report("api_spec 落库", data.get("api_spec_id") is not None)
        report("test_cases 生成（无崩溃）", data.get("test_cases_generated", -1) >= 0, f"count={data.get('test_cases_generated')}")


# =============================================================================
# 测试 3: 带 Bearer Token 的 Swagger 导入
# =============================================================================
def test_3_auth_import():
    print(f"\n{Colors.YELLOW}【测试3: 带 Bearer Token 的导入（鉴权传递）】{Colors.END}")
    pid, _ = create_project("-auth")
    if not pid:
        report("创建项目", False)
        return

    swagger_url = f"{BASE_URL}/openapi.json"
    fake_token = "test_fake_bearer_token_12345"

    # check-swagger with token
    check_resp = requests.post(f"{BASE_URL}/api/v2/real-project/check-swagger", json={
        "swagger_url": swagger_url,
        "token": fake_token,
        "auth_type": "bearer",
        "timeout": 10
    }, timeout=15)
    check_data = check_resp.json()
    report("check-swagger 带 Token 成功", check_data.get("success") is True)

    # import-url with auth_type + token
    import_resp = requests.post(f"{BASE_URL}/api/v2/swagger/import-url", json={
        "project_id": pid,
        "url": swagger_url,
        "generate_cases": True,
        "auth_type": "bearer",
        "token": fake_token
    }, timeout=30)
    report("import-url 带 Token 成功", import_resp.status_code == 200, f"status={import_resp.status_code}")

    if import_resp.status_code == 200:
        data = import_resp.json()
        # Token 不应出现在响应中
        report("响应不含 Token 明文", fake_token not in import_resp.text)
        # api_spec 落库后检查数据库不含 token
        # （无法直接查数据库，通过 api_spec 响应字段验证）
        report("api_spec_id 存在", data.get("api_spec_id") is not None)


# =============================================================================
# 测试 4: YApi import-yapi 接口参数校验
# =============================================================================
def test_4_yapi_import_validation():
    print(f"\n{Colors.YELLOW}【测试4: YApi import-yapi 参数校验】{Colors.END}")

    # 缺少 project_id
    r1 = requests.post(f"{BASE_URL}/api/v2/swagger/import-yapi", json={
        "yapi_base": "https://yapi.example.com",
        "yapi_project_id": 123
    }, timeout=10)
    report("缺少 project_id → 400", r1.status_code == 400, f"status={r1.status_code}")

    # 缺少 yapi_email / yapi_password
    r2 = requests.post(f"{BASE_URL}/api/v2/swagger/import-yapi", json={
        "project_id": 999,
        "yapi_base": "https://yapi.example.com",
        "yapi_project_id": 123
    }, timeout=10)
    report("缺少登录信息 → 400", r2.status_code == 400, f"status={r2.status_code}")

    # 缺少 yapi_base
    r3 = requests.post(f"{BASE_URL}/api/v2/swagger/import-yapi", json={
        "project_id": 999,
        "yapi_project_id": 123,
        "yapi_email": "a@b.com",
        "yapi_password": "xxx"
    }, timeout=10)
    report("缺少 yapi_base → 400", r3.status_code == 400, f"status={r3.status_code}")


# =============================================================================
# 测试 5: 重复导入同一 source_url → 409
# =============================================================================
def test_5_duplicate_409():
    print(f"\n{Colors.YELLOW}【测试5: 重复导入 → 409】{Colors.END}")
    pid, _ = create_project("-dup")
    if not pid:
        report("创建项目", False)
        return

    swagger_url = f"{BASE_URL}/openapi.json"

    # 第一次导入
    r1 = requests.post(f"{BASE_URL}/api/v2/swagger/import-url", json={
        "project_id": pid,
        "url": swagger_url,
        "generate_cases": False
    }, timeout=30)
    report("第一次导入成功", r1.status_code == 200, f"status={r1.status_code}")

    # 第二次导入
    r2 = requests.post(f"{BASE_URL}/api/v2/swagger/import-url", json={
        "project_id": pid,
        "url": swagger_url,
        "generate_cases": False
    }, timeout=30)
    report("重复导入 → 409", r2.status_code == 409, f"status={r2.status_code}")
    if r2.status_code == 409:
        detail = r2.json().get("detail", {})
        report("409 含 SWAGGER_ALREADY_IMPORTED", detail.get("code") == "SWAGGER_ALREADY_IMPORTED")


# =============================================================================
# 测试 6: import-url schema 校验（新增 auth_type / token 字段可选）
# =============================================================================
def test_6_schema_accepts_auth():
    print(f"\n{Colors.YELLOW}【测试6: import-url 接受 auth_type/token 字段】{Colors.END}")
    pid, _ = create_project("-schema")
    if not pid:
        report("创建项目", False)
        return

    # 不带 auth 字段（兼容旧调用）
    r1 = requests.post(f"{BASE_URL}/api/v2/swagger/import-url", json={
        "project_id": pid,
        "url": f"{BASE_URL}/openapi.json",
        "generate_cases": False
    }, timeout=30)
    report("不带 auth 字段 → 正常", r1.status_code == 200, f"status={r1.status_code}")

    # 带 auth 字段
    pid2, _ = create_project("-schema2")
    if not pid2:
        report("创建项目2", False)
        return
    r2 = requests.post(f"{BASE_URL}/api/v2/swagger/import-url", json={
        "project_id": pid2,
        "url": f"{BASE_URL}/openapi.json",
        "generate_cases": False,
        "auth_type": "bearer",
        "token": "some_test_token"
    }, timeout=30)
    report("带 auth 字段 → 正常", r2.status_code == 200, f"status={r2.status_code}")
    report("响应不含 Token", "some_test_token" not in r2.text)


# =============================================================================
# 测试 7: check-swagger 返回 source_type
# =============================================================================
def test_7_source_type():
    print(f"\n{Colors.YELLOW}【测试7: check-swagger 返回 source_type】{Colors.END}")
    r = requests.post(f"{BASE_URL}/api/v2/real-project/check-swagger", json={
        "swagger_url": f"{BASE_URL}/openapi.json",
        "timeout": 10
    }, timeout=15)
    data = r.json()
    report("check-swagger 返回 source_type", data.get("source_type") in ("openapi", "swagger"), f"source_type={data.get('source_type')}")
    report("success=True", data.get("success") is True)


# =============================================================================
# 主函数
# =============================================================================
def main():
    print("=" * 100)
    print(f"{Colors.BLUE}P1-7A 真实项目导入链路修复 — 回归测试{Colors.END}")
    print("=" * 100)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"后端: {BASE_URL}")
    print("=" * 100)

    # 前置检查
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        if r.status_code != 200:
            print(f"{Colors.RED}后端未就绪 (status={r.status_code}){Colors.END}")
            sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}后端不可达: {e}{Colors.END}")
        sys.exit(1)

    test_1_basic_import()
    test_2_chinese_openapi()
    test_3_auth_import()
    test_4_yapi_import_validation()
    test_5_duplicate_409()
    test_6_schema_accepts_auth()
    test_7_source_type()

    # 汇总
    total = passed + failed
    print("\n" + "=" * 100)
    print(f"{Colors.BLUE}测试汇总{Colors.END}")
    print(f"  总计: {total}  通过: {Colors.GREEN}{passed}{Colors.END}  失败: {Colors.RED}{failed}{Colors.END}")
    rate = (passed / total * 100) if total > 0 else 0
    print(f"  通过率: {rate:.1f}%")
    print("=" * 100)

    if failed > 0:
        print(f"\n{Colors.RED}失败用例:{Colors.END}")
        for name, ok, detail in results:
            if not ok:
                print(f"  ❌ {name}  {detail}")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
