"""
Executor V2 路由

提供真实 HTTP 测试执行的 REST API：
  POST /api/v2/execute                        执行单个用例
  POST /api/v2/execute/batch                  批量执行
  GET  /api/v2/execute/runs/{run_id}          获取运行结果
  GET  /api/v2/execute/runs/{run_id}/summary  获取运行摘要
  GET  /api/v2/execute/results/{record_id}    获取单条详情
  POST /api/v2/execute/generate-from-swagger  从 Swagger 自动生成用例
  POST /api/v2/execute/generate-and-run       生成并立即执行
  POST /api/v2/execute/ai/generate-assertions AI 智能生成断言
  POST /api/v2/execute/ai/enhance-cases       AI 增强用例断言
"""

import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.executor_v2.execution_engine import ExecutionEngineV2
from app.executor_v2.models import AssertionDef, TestCaseV2
from app.executor_v2.auth_manager import AuthManager
from config.config import get_config
from database.session import get_db


router = APIRouter(prefix="/api/v2/execute", tags=["ExecutorV2-真实执行"])


# ---------- Request / Response Models ----------

class AssertionDefIn(BaseModel):
    type: str = Field(..., description="断言类型: status_code/response_time/json_path/field_exists/field_equals/contains/schema")
    expected: Any = None
    path: str = ""
    operator: str = "eq"
    schema_def: Optional[dict] = Field(None, alias="schema")

class ExecuteCaseRequest(BaseModel):
    id: str = Field(default="", description="用例ID，为空则自动生成")
    title: str = Field(..., description="用例标题")
    method: str = Field(..., description="HTTP方法: GET/POST/PUT/DELETE/PATCH")
    path: str = Field(..., description="API路径，如 /api/users")
    base_url: str = Field(default="", description="目标服务地址，为空则使用系统配置")
    headers: Dict[str, str] = Field(default_factory=dict)
    cookies: Dict[str, str] = Field(default_factory=dict)
    query_params: Dict[str, Any] = Field(default_factory=dict)
    path_params: Dict[str, str] = Field(default_factory=dict)
    body: Any = None
    body_type: str = Field(default="json", description="json/form/raw")
    timeout: float = Field(default=30.0)
    assertions: List[AssertionDefIn] = Field(default_factory=list)

class ExecuteBatchRequest(BaseModel):
    base_url: str = Field(default="", description="目标服务地址")
    run_id: str = Field(default="", description="运行ID，为空则自动生成")
    cases: List[ExecuteCaseRequest] = Field(..., description="用例列表")


# ---------- 辅助函数 ----------

def _get_base_url(override: str = "") -> str:
    """获取 base_url：优先用请求传入的，其次用系统配置"""
    if override:
        return override
    config = get_config()
    url = config.test.base_url
    if not url or url == "http://localhost:8000":
        raise HTTPException(
            status_code=400,
            detail="未配置测试环境地址，无法执行真实接口测试。请在请求中传入 base_url 或在 .env 中设置 BASE_TEST_URL。"
        )
    return url


def _to_test_case(req: ExecuteCaseRequest, base_url: str) -> TestCaseV2:
    """将请求模型转为内部 TestCaseV2"""
    return TestCaseV2(
        id=req.id or f"case-{uuid.uuid4().hex[:8]}",
        title=req.title,
        method=req.method.upper(),
        path=req.path,
        base_url=req.base_url or base_url,
        headers=req.headers,
        cookies=req.cookies,
        query_params=req.query_params,
        path_params=req.path_params,
        body=req.body,
        body_type=req.body_type,
        timeout=req.timeout,
        assertions=[
            AssertionDef(
                type=a.type,
                expected=a.expected,
                path=a.path,
                operator=a.operator,
                schema=a.schema_def,
            )
            for a in req.assertions
        ],
    )


# ---------- 路由 ----------

@router.post("", summary="执行单个测试用例")
async def execute_single(req: ExecuteCaseRequest):
    """
    真实执行单个 API 测试用例。

    - 发送真实 HTTP 请求到目标服务
    - 执行断言验证
    - 结果写入数据库
    """
    try:
        base_url = _get_base_url(req.base_url)
        engine = ExecutionEngineV2(base_url=base_url)
        case = _to_test_case(req, base_url)
        run_id = f"single-{uuid.uuid4().hex[:8]}"
        result = engine.execute_case(case, run_id=run_id)
        return {
            "success": True,
            "run_id": run_id,
            "result": result.to_dict(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行失败: {e}")


@router.post("/batch", summary="批量执行测试用例")
async def execute_batch(req: ExecuteBatchRequest):
    """
    批量执行多个 API 测试用例。

    - 按顺序依次执行
    - 所有结果写入同一个 run_id
    - 返回汇总统计
    """
    try:
        base_url = _get_base_url(req.base_url)
        engine = ExecutionEngineV2(base_url=base_url)
        run_id = req.run_id or f"batch-{uuid.uuid4().hex[:8]}"

        cases = [_to_test_case(c, base_url) for c in req.cases]
        results = engine.execute_cases(cases, run_id=run_id)

        return {
            "success": True,
            "run_id": run_id,
            "summary": engine.get_run_summary(run_id),
            "results": [r.to_dict() for r in results],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量执行失败: {e}")


@router.get("/runs/{run_id}", summary="获取运行结果列表")
async def get_run_results(run_id: str):
    """获取某次运行的全部执行结果"""
    try:
        from app.executor_v2.result_writer import ResultWriter
        writer = ResultWriter()
        results = writer.get_by_run(run_id)
        summary = writer.get_summary(run_id)
        return {
            "success": True,
            "run_id": run_id,
            "summary": summary,
            "results": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{run_id}/summary", summary="获取运行摘要")
async def get_run_summary(run_id: str):
    """获取某次运行的统计摘要"""
    try:
        from app.executor_v2.result_writer import ResultWriter
        writer = ResultWriter()
        return {
            "success": True,
            "run_id": run_id,
            "summary": writer.get_summary(run_id),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results/{record_id}", summary="获取单条结果详情")
async def get_result_detail(record_id: int):
    """获取单条执行结果详情，包含完整请求/响应/断言"""
    try:
        from app.executor_v2.result_writer import ResultWriter
        writer = ResultWriter()
        detail = writer.get_by_id(record_id)
        if not detail:
            raise HTTPException(status_code=404, detail="记录不存在")
        return {
            "success": True,
            "result": detail,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------- Swagger → 用例生成 ----------

class GenerateFromSwaggerRequest(BaseModel):
    swagger_file: str = Field(default="", description="Swagger文件路径，为空则使用最新导入的")
    base_url: str = Field(default="", description="覆盖base_url")
    include_tags: Optional[List[str]] = Field(None, description="只包含这些tag")
    exclude_tags: Optional[List[str]] = Field(None, description="排除这些tag")
    include_patterns: Optional[List[str]] = Field(None, description="只包含模式: page/list/detail/save/delete/other")
    exclude_patterns: Optional[List[str]] = Field(None, description="排除模式: save/delete (安全起见)")
    max_cases: int = Field(default=0, description="最大用例数，0=不限")

class GenerateAndRunRequest(GenerateFromSwaggerRequest):
    run_id: str = Field(default="", description="运行ID")


def _find_swagger_file(override: str = "") -> str:
    """找到 swagger 文件路径"""
    if override and Path(override).exists():
        return override

    # 搜索 uploads/swagger 目录，找最新的
    upload_dir = Path(__file__).parent.parent / "uploads" / "swagger"
    if upload_dir.exists():
        files = sorted(upload_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
        for f in files:
            try:
                import json as _json
                with open(f, "r", encoding="utf-8") as fh:
                    data = _json.load(fh)
                if "paths" in data and len(data["paths"]) > 5:
                    return str(f)
            except Exception:
                continue

    # 搜索 scripts 目录
    scripts_dir = Path(__file__).parent.parent / "scripts"
    if scripts_dir.exists():
        for f in scripts_dir.glob("*swagger*.json"):
            return str(f)

    raise HTTPException(status_code=404, detail="未找到 Swagger 文件，请先导入或指定路径")


@router.post("/generate-from-swagger", summary="从Swagger自动生成V2用例")
async def generate_from_swagger(req: GenerateFromSwaggerRequest):
    """
    从 Swagger/OpenAPI 文件自动生成 Executor V2 格式的测试用例。

    默认排除 save/delete 模式以保证安全（只做查询类测试）。
    """
    try:
        from app.executor_v2.swagger_to_cases import generate_cases_from_swagger

        swagger_path = _find_swagger_file(req.swagger_file)
        cases, meta = generate_cases_from_swagger(
            swagger_path,
            include_tags=req.include_tags,
            exclude_tags=req.exclude_tags,
            include_patterns=req.include_patterns,
            exclude_patterns=req.exclude_patterns or ["save", "update", "delete"],
            max_cases=req.max_cases,
        )

        base_url = req.base_url or meta.get("base_url", "")

        return {
            "success": True,
            "base_url": base_url,
            "cases": cases,
            "meta": meta["stats"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败: {e}")


@router.post("/generate-and-run", summary="从Swagger生成用例并立即执行")
async def generate_and_run(req: GenerateAndRunRequest):
    """
    一键流程：从 Swagger 生成用例 → 立即批量执行 → 返回结果。

    默认排除 save/delete 模式，只测试查询类接口。
    """
    try:
        from app.executor_v2.swagger_to_cases import generate_cases_from_swagger

        swagger_path = _find_swagger_file(req.swagger_file)
        cases, meta = generate_cases_from_swagger(
            swagger_path,
            include_tags=req.include_tags,
            exclude_tags=req.exclude_tags,
            include_patterns=req.include_patterns,
            exclude_patterns=req.exclude_patterns or ["save", "update", "delete"],
            max_cases=req.max_cases,
        )

        base_url = req.base_url or meta.get("base_url", "")
        if not base_url:
            base_url = _get_base_url()

        engine = ExecutionEngineV2(base_url=base_url)
        run_id = req.run_id or f"swagger-{uuid.uuid4().hex[:8]}"

        # 转为 TestCaseV2
        tc_list = []
        for c in cases:
            tc = TestCaseV2(
                id=f"sg-{uuid.uuid4().hex[:6]}",
                title=c["title"],
                method=c["method"],
                path=c["path"],
                base_url=base_url,
                headers=c.get("headers", {}),
                body=c.get("body"),
                body_type="json",
                timeout=30.0,
                assertions=[
                    AssertionDef(
                        type=a["type"],
                        expected=a.get("expected"),
                        path=a.get("path", ""),
                    )
                    for a in c.get("assertions", [])
                ],
            )
            tc_list.append(tc)

        results = engine.execute_cases(tc_list, run_id=run_id)

        return {
            "success": True,
            "run_id": run_id,
            "base_url": base_url,
            "meta": meta["stats"],
            "summary": engine.get_run_summary(run_id),
            "results": [r.to_dict() for r in results],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行失败: {e}")


# ---------- 认证管理 ----------

class SetTokenRequest(BaseModel):
    token: str = Field(..., description="认证令牌（JWT / API Key 等）")
    auth_type: str = Field(default="bearer", description="认证类型: bearer/basic/api_key/cookie/custom")
    env_key: str = Field(default="default", description="环境标识")
    expires_in: int = Field(default=0, description="过期秒数，0=不过期")
    extra: Optional[Dict[str, Any]] = Field(None, description="附加配置，如 header_name")


@router.post("/auth/set-token", summary="设置认证Token")
async def set_auth_token(req: SetTokenRequest):
    """保存认证 Token，后续所有执行请求会自动注入"""
    AuthManager.set_token(
        token=req.token,
        auth_type=req.auth_type,
        env_key=req.env_key,
        expires_in=req.expires_in,
        extra=req.extra,
    )
    preview = req.token[:20] + "..." if len(req.token) > 20 else req.token
    return {
        "success": True,
        "message": f"Token 已保存 (env={req.env_key}, type={req.auth_type})",
        "token_preview": preview,
    }


@router.get("/auth/status", summary="查看认证状态")
async def get_auth_status():
    """查看当前所有环境的 Token 状态"""
    return {
        "success": True,
        "envs": AuthManager.list_envs(),
    }


@router.delete("/auth/clear", summary="清除认证Token")
async def clear_auth_token(env_key: str = "default"):
    """清除指定环境的 Token"""
    AuthManager.clear_token(env_key)
    return {"success": True, "message": f"已清除 env={env_key} 的 Token"}


@router.delete("/auth/clear-all", summary="清除所有认证Token")
async def clear_all_auth_tokens():
    """清除所有环境的 Token"""
    AuthManager.clear_all()
    return {"success": True, "message": "已清除所有 Token"}


class OAuth2TestRequest(BaseModel):
    token_url: str = Field(..., description="OAuth2 Token 端点")
    client_authorization: str = Field(default="", description="Basic Auth (Base64)")
    username: str = Field(default="", description="用户名 (password grant)")
    password: str = Field(default="", description="密码")
    grant_type: str = Field(default="password", description="授权类型")
    scope: str = Field(default="all", description="scope")


@router.post("/auth/oauth2/test", summary="测试 OAuth2 连通性")
async def test_oauth2_connection(req: OAuth2TestRequest):
    """
    测试 OAuth2 配置是否能成功获取 Token。
    不会持久化，仅返回结果。
    """
    from app.executor_v2.oauth2_token_fetcher import fetch_oauth2_token
    config = req.dict()
    try:
        access_token, token_type = fetch_oauth2_token(config, env_key="__test__", force=True)
        preview = access_token[:30] + "..." if len(access_token) > 30 else access_token
        # 清理测试缓存
        from app.executor_v2.oauth2_token_fetcher import clear_oauth2_cache
        clear_oauth2_cache("__test__")
        return {
            "success": True,
            "message": "OAuth2 Token 获取成功",
            "token_type": token_type,
            "token_preview": preview,
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"OAuth2 Token 获取失败: {str(e)}",
        }


@router.post("/auth/oauth2/refresh", summary="手动刷新 OAuth2 Token")
async def refresh_oauth2_token(env_key: str = "default", db: Session = Depends(get_db)):
    """
    手动刷新指定环境的 OAuth2 Token。
    从数据库读取该环境的 OAuth2 配置，强制重新获取。
    """
    from app.executor_v2.oauth2_token_fetcher import fetch_oauth2_token
    from database.models import Environment
    from services.auth_service import AuthService

    # 根据 env_key 解析 env_id
    env_id = None
    if env_key.startswith("env_"):
        try:
            env_id = int(env_key.replace("env_", ""))
        except ValueError:
            pass

    if not env_id:
        return {"success": False, "message": f"无法解析 env_key={env_key}，格式应为 env_<id>"}

    service = AuthService(db)
    auth_profile = service.get_by_environment(env_id)
    if not auth_profile or auth_profile.auth_type != "oauth2":
        return {"success": False, "message": f"环境 {env_id} 没有 OAuth2 鉴权配置"}

    auth_config = service.get_decrypted_config(auth_profile) or {}

    try:
        access_token, token_type = fetch_oauth2_token(auth_config, env_key=env_key, force=True)
        AuthManager.set_token(
            token=access_token,
            auth_type="custom",
            env_key=env_key,
            extra={"header_name": "Authorization", "prefix": f"{token_type} "},
        )
        preview = access_token[:20] + "..." if len(access_token) > 20 else access_token
        return {
            "success": True,
            "message": "OAuth2 Token 已刷新",
            "token_preview": preview,
            "token_type": token_type,
        }
    except Exception as e:
        return {"success": False, "message": f"刷新失败: {str(e)}"}


# ---------- AI 智能断言 ----------

class AIGenerateAssertionsRequest(BaseModel):
    apis: List[Dict[str, Any]] = Field(
        ...,
        description="API列表，每项含 path/method/summary/tags/request_schema"
    )
    max_apis: int = Field(default=10, description="单次最多处理的API数")

class AIEnhanceCasesRequest(BaseModel):
    base_url: str = Field(default="", description="覆盖base_url")
    include_patterns: Optional[List[str]] = Field(None)
    exclude_patterns: Optional[List[str]] = Field(None)
    max_cases: int = Field(default=10, description="最多增强的用例数")


@router.post("/ai/generate-assertions", summary="AI智能生成断言")
async def ai_generate_assertions(req: AIGenerateAssertionsRequest):
    """
    用 DeepSeek 为指定 API 列表生成智能断言。

    输入 API 定义（path/method/summary），输出每个 API 的断言规则。
    """
    try:
        from app.executor_v2.ai_assertion_gen import generate_assertions_batch
        result = generate_assertions_batch(req.apis, max_apis=req.max_apis)
        return {
            "success": True,
            "assertions": result,
            "count": sum(len(v) for v in result.values()),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 断言生成失败: {e}")


@router.post("/ai/enhance-cases", summary="AI增强Swagger用例断言")
async def ai_enhance_cases(req: AIEnhanceCasesRequest):
    """
    一键流程：从 Swagger 生成用例 → AI 为每个用例生成智能断言 → 返回增强后的用例。

    默认只增强查询类接口（page/list/detail）。
    """
    try:
        from app.executor_v2.swagger_to_cases import generate_cases_from_swagger
        from app.executor_v2.ai_assertion_gen import generate_assertions_batch

        swagger_path = _find_swagger_file()
        cases, meta = generate_cases_from_swagger(
            swagger_path,
            include_patterns=req.include_patterns or ["page", "list", "detail"],
            exclude_patterns=req.exclude_patterns or ["save", "update", "delete"],
            max_cases=req.max_cases,
        )

        base_url = req.base_url or meta.get("base_url", "")

        # 构建 API 信息给 AI
        api_infos = []
        for c in cases:
            api_infos.append({
                "path": c["path"],
                "method": c["method"],
                "summary": c["title"],
                "tags": [],
            })

        # AI 生成断言
        ai_assertions = generate_assertions_batch(api_infos, max_apis=req.max_cases)

        # 合并回用例
        enhanced = 0
        for c in cases:
            key = f"{c['method']} {c['path']}"
            if key in ai_assertions:
                c["assertions"] = ai_assertions[key]
                enhanced += 1

        return {
            "success": True,
            "base_url": base_url,
            "cases": cases,
            "meta": meta["stats"],
            "ai_enhanced": enhanced,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 增强失败: {e}")


# ---------- 风险分级 & 环境保护 ----------

@router.get("/risk/scan", summary="扫描全部API风险等级")
async def scan_api_risks():
    """扫描 Swagger 中所有 API，返回风险分级结果"""
    try:
        from app.executor_v2.risk_classifier import scan_swagger_risks
        swagger_path = _find_swagger_file()
        result = scan_swagger_risks(swagger_path)
        return {
            "success": True,
            "total": result["total"],
            "low": result["low"],
            "medium": result["medium"],
            "high": result["high"],
            "recommended_regression": result["recommended_regression"],
            "high_apis": result["high_apis"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"风险扫描失败: {e}")


class RiskCheckRequest(BaseModel):
    base_url: str = Field(default="", description="目标环境地址")
    env_name: str = Field(default="", description="环境名称")
    method: str = Field(default="POST")
    path: str = Field(default="")
    summary: str = Field(default="")
    force: bool = Field(default=False, description="中风险二次确认")

@router.post("/risk/check", summary="单接口风险检查")
async def check_api_risk(req: RiskCheckRequest):
    """检查单个接口在指定环境下是否允许执行"""
    from app.executor_v2.env_guard import EnvGuard
    allowed, risk, msg = EnvGuard.check_permission(
        base_url=req.base_url,
        method=req.method,
        path=req.path,
        summary=req.summary,
        env_name=req.env_name,
        force=req.force,
    )
    return {
        "allowed": allowed,
        "risk": risk,
        "is_production": EnvGuard.is_production(req.base_url, req.env_name),
        "message": msg,
    }
