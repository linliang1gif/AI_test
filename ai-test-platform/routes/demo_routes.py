"""
Phase 17: Demo 项目初始化/重置路由
一键初始化 ERP Demo System，跑通完整闭环。
"""
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.session import get_db
from database.models import Project, Environment, AuthProfile, ApiSpec, TestCase, TestRun, RunCase
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/demo", tags=["Demo"])

DEMO_PROJECT_NAME = "ERP Demo System"
DEMO_ENV_NAME = "Demo Local"
DEMO_BASE_URL = "http://localhost:8000"
DEMO_TOKEN = "demo-token"
DEMO_OPENAPI_FILE = Path(__file__).parent.parent / "demo" / "demo_openapi.json"


def _find_demo_project(db: Session) -> Optional[Project]:
    return db.query(Project).filter(Project.name == DEMO_PROJECT_NAME).first()


def _clean_demo_data(db: Session):
    """删除所有 Demo 相关数据"""
    project = _find_demo_project(db)
    if not project:
        return
    pid = project.id

    # 删除执行记录
    runs = db.query(TestRun).filter(TestRun.project_id == pid).all()
    for run in runs:
        db.query(RunCase).filter(RunCase.run_id == run.id).delete()
    db.query(TestRun).filter(TestRun.project_id == pid).delete()

    # 删除 Demo 测试用例 (按 source='demo_swagger' 或按 project 关联的 api_spec)
    specs = db.query(ApiSpec).filter(ApiSpec.project_id == pid).all()
    spec_ids = [s.id for s in specs]
    # 删除 swagger 导入的 + seed 的 demo 用例
    db.query(TestCase).filter(TestCase.source == 'demo_swagger').delete()
    db.query(TestCase).filter(TestCase.source == 'demo_seed').delete()

    # 删除 ApiSpec
    db.query(ApiSpec).filter(ApiSpec.project_id == pid).delete()

    # 删除项目 (cascade 会删 Environment + AuthProfile)
    db.delete(project)
    db.commit()


def _create_demo_project(db: Session) -> dict:
    """创建 Demo 项目并返回摘要"""

    # 1. 创建/复用项目
    project = _find_demo_project(db)
    if project:
        # 项目已存在，先清理再重建
        _clean_demo_data(db)

    project = Project(
        name=DEMO_PROJECT_NAME,
        description="Phase 17 Demo 标准项目 - 用于展示平台完整闭环能力",
        status="active",
        owner="demo",
        team="demo",
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # 2. 创建环境
    env = Environment(
        project_id=project.id,
        name=DEMO_ENV_NAME,
        base_url=DEMO_BASE_URL,
        is_protected=False,
        allow_write=True,
        timeout_seconds=10,
    )
    db.add(env)
    db.commit()
    db.refresh(env)

    # 3. 创建认证配置
    auth = AuthProfile(
        environment_id=env.id,
        auth_type="bearer",
        auth_config=json.dumps({"token": DEMO_TOKEN}),
        default_headers={"Authorization": f"Bearer {DEMO_TOKEN}"},
    )
    db.add(auth)
    db.commit()

    # 4. 导入 OpenAPI → ApiSpec
    openapi_data = json.loads(DEMO_OPENAPI_FILE.read_text(encoding="utf-8"))
    paths = openapi_data.get("paths", {})
    api_count = sum(len(methods) for methods in paths.values())

    # 保存一份到 uploads
    upload_dir = Path(__file__).parent.parent / "uploads" / "swagger"
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved_path = upload_dir / f"demo_openapi_{project.id}.json"
    saved_path.write_text(json.dumps(openapi_data, indent=2, ensure_ascii=False), encoding="utf-8")

    api_spec = ApiSpec(
        project_id=project.id,
        source_type="file",
        source_url="demo_openapi.json",
        version=openapi_data.get("info", {}).get("version", "1.0.0"),
        raw_spec_path=str(saved_path),
        api_count=api_count,
        imported_at=datetime.now(),
    )
    db.add(api_spec)
    db.commit()
    db.refresh(api_spec)

    # 5. 使用 SwaggerService 生成基础用例
    generated_ids = []
    try:
        from services.swagger_service import SwaggerService
        svc = SwaggerService(db)
        generated = svc._generate_test_cases(api_spec.id, str(saved_path), project.id)
        generated_ids = [tc.id for tc in generated]
        # 标记来源为 demo_swagger
        for tc in generated:
            tc.source = "demo_swagger"
        db.commit()
    except Exception as e:
        logger.info(f"⚠️ Swagger 自动生成用例失败: {e}，将仅使用 seed 用例")

    # 6. 插入 seed 异常用例
    seed_cases = _build_seed_cases()
    seed_count = 0
    for sc in seed_cases:
        existing = db.query(TestCase).filter(TestCase.id == sc["id"]).first()
        if existing:
            continue
        tc = TestCase(
            id=sc["id"],
            title=sc["title"],
            module=sc.get("module", ""),
            priority=sc.get("priority", "medium"),
            status="pending",
            steps=[],
            expected=sc.get("expected", ""),
            data_type=sc.get("data_type", "positive"),
            expected_behavior=sc.get("expected_behavior", "success"),
            execution_config=sc["execution_config"],
            assertions=sc.get("assertions", []),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by="demo_seed",
            tags=sc.get("tags", []),
            source="demo_seed",
        )
        db.add(tc)
        seed_count += 1
    db.commit()

    all_demo_ids = generated_ids + [sc["id"] for sc in seed_cases]

    # 7. Phase 16 治理推断
    governed = 0
    try:
        from services.case_governance_service import CaseGovernanceService
        gov_svc = CaseGovernanceService(db)
        result = gov_svc.govern_all(force=True)
        governed = result.get("updated", 0)
    except Exception as e:
        logger.info(f"⚠️ 治理推断失败: {e}")

    total_cases = db.query(TestCase).filter(
        TestCase.source.in_(["demo_swagger", "demo_seed"])
    ).count()

    return {
        "project_id": project.id,
        "environment_id": env.id,
        "api_count": api_count,
        "test_case_count": total_cases,
        "generated_count": len(generated_ids),
        "seed_count": seed_count,
        "governed_count": governed,
        "recommended_sets": ["smoke", "query-safe", "p0", "failed-rerun", "regression"],
    }


def _build_seed_cases():
    """构建 Demo 异常/边界测试用例种子"""
    base = "http://localhost:8000"
    token_header = {"Authorization": "Bearer demo-token"}
    cases = []

    def _add(id_, title, module, method, url, headers=None, body=None,
             priority="medium", data_type="negative", expected_behavior="error",
             assertions=None, tags=None):
        cases.append({
            "id": id_,
            "title": title,
            "module": module,
            "priority": priority,
            "data_type": data_type,
            "expected_behavior": expected_behavior,
            "expected": title,
            "execution_config": {
                "method": method,
                "url": url,
                "headers": headers or {},
                "body": body or {},
            },
            "assertions": assertions or [{"type": "status_code", "expected": 200}],
            "tags": tags or ["demo"],
        })

    # ─── Auth 异常 ───
    _add("DEMO_AUTH_001", "[异常] 错误密码登录", "Auth", "POST",
         f"{base}/api/mock/login", body={"username": "admin", "password": "wrong"},
         assertions=[{"type": "status_code", "expected": 401}], tags=["demo", "negative"])

    _add("DEMO_AUTH_002", "[异常] 无Token访问商品列表", "Product", "GET",
         f"{base}/api/mock/products", headers={},
         assertions=[{"type": "status_code", "expected": 401}], tags=["demo", "negative"])

    _add("DEMO_AUTH_003", "[异常] 错误Token访问用户信息", "User", "GET",
         f"{base}/api/mock/users/profile", headers={"Authorization": "Bearer wrong-token"},
         assertions=[{"type": "status_code", "expected": 401}], tags=["demo", "negative"])

    # ─── 参数缺失 ───
    _add("DEMO_REQ_001", "[异常] 新增商品缺少name", "Product", "POST",
         f"{base}/api/mock/products", headers=token_header, body={"price": 100},
         assertions=[{"type": "status_code", "expected": 400}], tags=["demo", "negative"])

    _add("DEMO_REQ_002", "[异常] 创建订单缺少product_id", "Order", "POST",
         f"{base}/api/mock/orders", headers=token_header, body={"quantity": 1},
         assertions=[{"type": "status_code", "expected": 400}], tags=["demo", "negative"])

    _add("DEMO_REQ_003", "[异常] 创建订单缺少quantity", "Order", "POST",
         f"{base}/api/mock/orders", headers=token_header, body={"product_id": "1"},
         assertions=[{"type": "status_code", "expected": 400}], tags=["demo", "negative"])

    # ─── 资源不存在 ───
    _add("DEMO_404_001", "[异常] 查询不存在商品", "Product", "GET",
         f"{base}/api/mock/products/999999", headers=token_header,
         assertions=[{"type": "status_code", "expected": 404}], tags=["demo", "negative"])

    _add("DEMO_404_002", "[异常] 查询不存在订单", "Order", "GET",
         f"{base}/api/mock/orders/999999", headers=token_header,
         assertions=[{"type": "status_code", "expected": 404}], tags=["demo", "negative"])

    _add("DEMO_404_003", "[异常] 查询不存在付款单", "PaymentBill", "GET",
         f"{base}/api/mock/payment-bills/999999", headers=token_header,
         assertions=[{"type": "status_code", "expected": 404}], tags=["demo", "negative"])

    # ─── 业务状态错误 ───
    _add("DEMO_BIZ_001", "[异常] 重复取消已取消订单", "Order", "POST",
         f"{base}/api/mock/orders/3/cancel", headers=token_header,
         assertions=[{"type": "json_path", "path": "$.code", "expected": 40001}],
         tags=["demo", "negative"])

    _add("DEMO_BIZ_002", "[异常] 未提交付款单直接审批", "PaymentBill", "POST",
         f"{base}/api/mock/payment-bills/1/approve", headers=token_header,
         assertions=[{"type": "json_path", "path": "$.code", "expected": 40004}],
         tags=["demo", "negative"])

    _add("DEMO_BIZ_003", "[异常] 未审批付款单直接付款", "PaymentBill", "POST",
         f"{base}/api/mock/payment-bills/2/pay", headers=token_header,
         assertions=[{"type": "json_path", "path": "$.code", "expected": 40006}],
         tags=["demo", "negative"])

    _add("DEMO_BIZ_004", "[异常] 已付款付款单重复付款", "PaymentBill", "POST",
         f"{base}/api/mock/payment-bills/4/pay", headers=token_header,
         assertions=[{"type": "json_path", "path": "$.code", "expected": 40005}],
         tags=["demo", "negative"])

    # ─── 正常 seed (补充 swagger 未生成的) ───
    _add("DEMO_OK_001", "[正常] 管理员登录", "Auth", "POST",
         f"{base}/api/mock/login", body={"username": "admin", "password": "123456"},
         priority="high", data_type="positive", expected_behavior="success",
         assertions=[{"type": "status_code", "expected": 200}, {"type": "json_path", "path": "$.code", "expected": 0}],
         tags=["demo", "smoke"])

    _add("DEMO_OK_002", "[正常] 获取用户信息", "User", "GET",
         f"{base}/api/mock/users/profile", headers=token_header,
         priority="high", data_type="positive", expected_behavior="success",
         assertions=[{"type": "status_code", "expected": 200}, {"type": "json_path", "path": "$.code", "expected": 0}],
         tags=["demo", "smoke"])

    _add("DEMO_OK_003", "[正常] 查询商品列表", "Product", "GET",
         f"{base}/api/mock/products", headers=token_header,
         priority="high", data_type="positive", expected_behavior="success",
         assertions=[{"type": "status_code", "expected": 200}, {"type": "json_path", "path": "$.code", "expected": 0}],
         tags=["demo", "smoke"])

    _add("DEMO_OK_004", "[正常] 查询商品详情", "Product", "GET",
         f"{base}/api/mock/products/1", headers=token_header,
         priority="medium", data_type="positive", expected_behavior="success",
         assertions=[{"type": "status_code", "expected": 200}, {"type": "json_path", "path": "$.code", "expected": 0}],
         tags=["demo", "smoke"])

    _add("DEMO_OK_005", "[正常] 新增商品", "Product", "POST",
         f"{base}/api/mock/products", headers=token_header,
         body={"name": "Demo测试商品", "price": 299.9, "stock": 50, "category": "测试"},
         priority="high", data_type="positive", expected_behavior="success",
         assertions=[{"type": "status_code", "expected": 200}, {"type": "json_path", "path": "$.code", "expected": 0}],
         tags=["demo"])

    _add("DEMO_OK_006", "[正常] 修改商品", "Product", "PUT",
         f"{base}/api/mock/products/1", headers=token_header,
         body={"name": "修改后商品", "price": 399.9},
         priority="medium", data_type="positive", expected_behavior="success",
         assertions=[{"type": "status_code", "expected": 200}, {"type": "json_path", "path": "$.code", "expected": 0}],
         tags=["demo"])

    _add("DEMO_OK_007", "[正常] 删除商品", "Product", "DELETE",
         f"{base}/api/mock/products/2", headers=token_header,
         priority="low", data_type="positive", expected_behavior="success",
         assertions=[{"type": "status_code", "expected": 200}, {"type": "json_path", "path": "$.code", "expected": 0}],
         tags=["demo", "destructive"])

    _add("DEMO_OK_008", "[正常] 查询订单列表", "Order", "GET",
         f"{base}/api/mock/orders", headers=token_header,
         priority="high", data_type="positive", expected_behavior="success",
         assertions=[{"type": "status_code", "expected": 200}, {"type": "json_path", "path": "$.code", "expected": 0}],
         tags=["demo", "smoke"])

    _add("DEMO_OK_009", "[正常] 查询订单详情", "Order", "GET",
         f"{base}/api/mock/orders/1", headers=token_header,
         priority="medium", data_type="positive", expected_behavior="success",
         assertions=[{"type": "status_code", "expected": 200}, {"type": "json_path", "path": "$.code", "expected": 0}],
         tags=["demo"])

    _add("DEMO_OK_010", "[正常] 创建订单", "Order", "POST",
         f"{base}/api/mock/orders", headers=token_header,
         body={"product_id": "1", "quantity": 3},
         priority="high", data_type="positive", expected_behavior="success",
         assertions=[{"type": "status_code", "expected": 200}, {"type": "json_path", "path": "$.code", "expected": 0}],
         tags=["demo"])

    _add("DEMO_OK_011", "[正常] 取消订单", "Order", "POST",
         f"{base}/api/mock/orders/1/cancel", headers=token_header,
         priority="medium", data_type="positive", expected_behavior="success",
         assertions=[{"type": "status_code", "expected": 200}, {"type": "json_path", "path": "$.code", "expected": 0}],
         tags=["demo", "destructive"])

    _add("DEMO_OK_012", "[正常] 查询付款单列表", "PaymentBill", "GET",
         f"{base}/api/mock/payment-bills", headers=token_header,
         priority="high", data_type="positive", expected_behavior="success",
         assertions=[{"type": "status_code", "expected": 200}, {"type": "json_path", "path": "$.code", "expected": 0}],
         tags=["demo", "smoke"])

    _add("DEMO_OK_013", "[正常] 查询付款单详情", "PaymentBill", "GET",
         f"{base}/api/mock/payment-bills/1", headers=token_header,
         priority="medium", data_type="positive", expected_behavior="success",
         assertions=[{"type": "status_code", "expected": 200}, {"type": "json_path", "path": "$.code", "expected": 0}],
         tags=["demo"])

    _add("DEMO_OK_014", "[正常] 提交付款单", "PaymentBill", "POST",
         f"{base}/api/mock/payment-bills/1/submit", headers=token_header,
         priority="high", data_type="positive", expected_behavior="success",
         assertions=[{"type": "status_code", "expected": 200}, {"type": "json_path", "path": "$.code", "expected": 0}],
         tags=["demo"])

    _add("DEMO_OK_015", "[正常] 审批付款单", "PaymentBill", "POST",
         f"{base}/api/mock/payment-bills/2/approve", headers=token_header,
         priority="high", data_type="positive", expected_behavior="success",
         assertions=[{"type": "status_code", "expected": 200}, {"type": "json_path", "path": "$.code", "expected": 0}],
         tags=["demo"])

    _add("DEMO_OK_016", "[正常] 付款", "PaymentBill", "POST",
         f"{base}/api/mock/payment-bills/3/pay", headers=token_header,
         priority="high", data_type="positive", expected_behavior="success",
         assertions=[{"type": "status_code", "expected": 200}, {"type": "json_path", "path": "$.code", "expected": 0}],
         tags=["demo"])

    _add("DEMO_OK_017", "[正常] 报表汇总", "Report", "GET",
         f"{base}/api/mock/reports/summary", headers=token_header,
         priority="medium", data_type="positive", expected_behavior="success",
         assertions=[{"type": "status_code", "expected": 200}, {"type": "json_path", "path": "$.code", "expected": 0}],
         tags=["demo", "smoke"])

    return cases


# ==================== 路由 ====================

@router.post("/init")
async def demo_init(db: Session = Depends(get_db)):
    """一键初始化 Demo 项目（幂等）"""
    try:
        result = _create_demo_project(db)
        return {"code": 0, "message": "Demo initialized successfully", "data": result}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"code": 500, "message": f"Demo init failed: {str(e)}", "data": None}


@router.post("/reset")
async def demo_reset(db: Session = Depends(get_db)):
    """重置 Demo 项目：清理后重新初始化"""
    try:
        _clean_demo_data(db)
        # 重置 Mock 内存数据
        from routes.mock_routes import reset_mock_data
        reset_mock_data()
        result = _create_demo_project(db)
        return {"code": 0, "message": "Demo reset and re-initialized successfully", "data": result}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"code": 500, "message": f"Demo reset failed: {str(e)}", "data": None}


@router.get("/status")
async def demo_status(db: Session = Depends(get_db)):
    """查询 Demo 项目状态"""
    project = _find_demo_project(db)
    if not project:
        return {"code": 0, "message": "Demo not initialized", "data": {"initialized": False}}

    env = db.query(Environment).filter(Environment.project_id == project.id).first()
    case_count = db.query(TestCase).filter(
        TestCase.source.in_(["demo_swagger", "demo_seed"])
    ).count()
    run_count = db.query(TestRun).filter(TestRun.project_id == project.id).count()

    return {
        "code": 0,
        "message": "Demo initialized",
        "data": {
            "initialized": True,
            "project_id": project.id,
            "environment_id": env.id if env else None,
            "test_case_count": case_count,
            "run_count": run_count,
        },
    }
