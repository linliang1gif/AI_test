"""
P2-2 Health / Readiness / Admin 端点
- /health 保持兼容
- /readiness K8s 就绪探针
- /admin/app-mode 仅 mock/test 模式可用
"""
import os
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request

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
    ai_provider = os.getenv("AI_PROVIDER", "none")
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
