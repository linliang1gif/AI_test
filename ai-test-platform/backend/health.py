"""
P2-2 Health / Readiness / Admin 端点
- /health 保持兼容
- /readiness K8s 就绪探针
- /admin/app-mode 仅 mock/test 模式可用
- D2-2: /api/v2/health/full 全量健康检查
"""
import os
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request

from backend.trace_middleware import current_trace_id

logger = logging.getLogger("health")
router = APIRouter()


def _module_flags() -> dict:
    """收集可选模块可用性标志（运行时读取）"""
    # 这些全局变量由 router_registry 在导入时设置
    from backend.router_registry import MODULE_FLAGS
    return MODULE_FLAGS


@router.get("/")
async def root():
    return {
        "message": "AI Test Platform Backend API",
        "version": "1.2.0",
        "status": "running",
    }


@router.get("/health")
async def health_check():
    app_mode = os.getenv("APP_MODE", "mock")
    ai_provider = os.getenv("AI_PROVIDER") or os.getenv("DEFAULT_AI_PROVIDER") or "none"
    health_status = {
        "status": "healthy",
        "app_mode": app_mode,
        "ai_provider": ai_provider,
        "timestamp": datetime.now().isoformat(),
        "database": {
            "connected": False,
            "tables_ready": False,
            "missing_tables": [],
        },
        "modules": _module_flags(),
    }

    try:
        from database import get_db_session
        from sqlalchemy import inspect, text

        with get_db_session() as db:
            db.execute(text("SELECT 1"))
            health_status["database"]["connected"] = True

            inspector = inspect(db.bind)
            existing = inspector.get_table_names()
            required = ["projects", "test_cases", "test_runs", "run_cases", "run_steps"]
            missing = [t for t in required if t not in existing]
            health_status["database"]["missing_tables"] = missing
            health_status["database"]["tables_ready"] = len(missing) == 0
            if missing:
                health_status["status"] = "degraded"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["database"]["error"] = str(e)

    return health_status


@router.get("/api/v2/health/full")
async def health_full(request: Request):
    """D2-2: 全量平台健康检查，返回 backend / db / ai / env / latest_run 综合状态"""
    tid = current_trace_id()
    now = datetime.now()

    result = {
        "backend_status": "ok",
        "database_status": "unknown",
        "ai_config_status": "unknown",
        "environment_status": "unknown",
        "latest_run_status": "unknown",
        "trace_id": tid,
        "timestamp": now.isoformat(),
        "modules": _module_flags(),
    }

    # ── database ──
    try:
        from database import get_db_session
        from sqlalchemy import inspect, text

        with get_db_session() as db:
            db.execute(text("SELECT 1"))
            inspector = inspect(db.bind)
            existing = set(inspector.get_table_names())
            required = {"projects", "test_cases", "test_runs", "run_cases", "run_steps", "iterations"}
            missing = required - existing
            if missing:
                result["database_status"] = "degraded"
                result["database_missing_tables"] = sorted(missing)
            else:
                result["database_status"] = "ok"
                # 统计
                proj_count = db.execute(text("SELECT count(*) FROM projects")).scalar()
                tc_count = db.execute(text("SELECT count(*) FROM test_cases")).scalar()
                tr_count = db.execute(text("SELECT count(*) FROM test_runs")).scalar()
                result["database_counts"] = {
                    "projects": proj_count,
                    "test_cases": tc_count,
                    "test_runs": tr_count,
                }
    except Exception as e:
        result["database_status"] = "error"
        result["database_error"] = str(type(e).__name__)
        logger.warning("health/full db check failed: %s", e)

    # ── ai_config ──
    try:
        ai_provider = os.getenv("AI_PROVIDER", "")
        ai_api_key = os.getenv("AI_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("DASHSCOPE_API_KEY") or ""
        if ai_provider and ai_api_key:
            result["ai_config_status"] = "configured"
            result["ai_provider"] = ai_provider
        elif ai_provider:
            result["ai_config_status"] = "partial"
            result["ai_provider"] = ai_provider
            result["ai_config_hint"] = "provider已配置但未检测到API Key环境变量"
        else:
            result["ai_config_status"] = "not_configured"
            result["ai_config_hint"] = "未设置AI_PROVIDER环境变量"
    except Exception:
        result["ai_config_status"] = "error"

    # ── environment ──
    try:
        app_mode = os.getenv("APP_MODE", "mock")
        result["environment_status"] = "ok"
        result["environment"] = {
            "app_mode": app_mode,
            "python_version": __import__("sys").version.split()[0],
            "backend_port": os.getenv("BACKEND_PORT", "8000"),
        }
    except Exception:
        result["environment_status"] = "error"

    # ── latest_run ──
    try:
        from database import get_db_session
        from sqlalchemy import text as sa_text

        with get_db_session() as db:
            row = db.execute(sa_text(
                "SELECT id, status, started_at, finished_at FROM test_runs ORDER BY id DESC LIMIT 1"
            )).first()
            if row:
                result["latest_run_status"] = "found"
                result["latest_run"] = {
                    "run_id": row[0],
                    "status": row[1],
                    "started_at": str(row[2]) if row[2] else None,
                    "finished_at": str(row[3]) if row[3] else None,
                }
            else:
                result["latest_run_status"] = "no_runs"
    except Exception as e:
        result["latest_run_status"] = "error"
        logger.warning("health/full latest_run check failed: %s", e)

    return result


@router.get("/readiness")
async def readiness_check():
    try:
        from database import get_db_session
        from sqlalchemy import inspect, text

        with get_db_session() as db:
            db.execute(text("SELECT 1"))
            inspector = inspect(db.bind)
            existing = inspector.get_table_names()
            required = ["projects", "test_cases", "test_runs"]
            missing = [t for t in required if t not in existing]
            if missing:
                raise HTTPException(status_code=503, detail=f"缺少表: {', '.join(missing)}")
        return {"status": "ready"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"系统未就绪: {e}")


@router.put("/admin/app-mode")
async def set_app_mode(mode: str = "mock", request: Request = None):
    """切换 APP_MODE — 默认禁用，仅 TESTING=true 或 ENABLE_ADMIN_APP_MODE=true 或带有正确的 X-Testing-Key 时启用"""
    # P2-2.1: 默认禁用，必须显式启用
    testing = os.getenv("TESTING", "").lower() == "true"
    admin_enabled = os.getenv("ENABLE_ADMIN_APP_MODE", "").lower() == "true"
    # P2-4.1: 允许测试脚本通过 header 访问
    testing_key = os.getenv("TESTING_KEY", "")
    header_key = ""
    if request:
        header_key = request.headers.get("X-Testing-Key", "")
    if testing_key and header_key and header_key == testing_key:
        testing = True
    if not testing and not admin_enabled:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=403, content={
            "code": "ADMIN_APP_MODE_DISABLED",
            "message": "admin app-mode endpoint is disabled outside testing mode",
        })
    if mode not in ("mock", "real"):
        raise HTTPException(status_code=400, detail="mode must be 'mock' or 'real'")
    os.environ["APP_MODE"] = mode
    return {"success": True, "app_mode": mode}
