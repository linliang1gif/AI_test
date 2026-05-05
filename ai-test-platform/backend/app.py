"""
P2-2 create_app() 工厂函数
集中创建 FastAPI 实例、注册中间件、路由、异常处理和启动事件。
"""
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 确保项目根目录在 sys.path
_root = str(Path(__file__).parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用"""

    # 1. 配置 & 日志
    from backend.config import settings
    from backend.logging_config import setup_logging
    setup_logging(settings.LOG_LEVEL)

    # 2. lifespan
    from backend.startup import on_startup

    @asynccontextmanager
    async def lifespan(application):
        await on_startup()
        yield

    # 3. FastAPI 实例
    app = FastAPI(
        title="AI Test Platform Backend API",
        description="AI测试平台完整后端API",
        version="1.2.0",
        lifespan=lifespan,
    )

    # 3. CORS — Phase C2: 收紧 allow_origins，不再使用 ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOW_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 4. 全局异常处理
    from backend.exception_handlers import register_exception_handlers
    register_exception_handlers(app)

    # 5. 路由注册（集中）
    from backend.router_registry import register_routers
    register_routers(app)

    # 7. P2-4: 截图静态文件服务
    import os
    from fastapi.staticfiles import StaticFiles
    screenshots_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "artifacts", "ui", "screenshots")
    os.makedirs(screenshots_dir, exist_ok=True)
    app.mount("/screenshots", StaticFiles(directory=screenshots_dir), name="screenshots")

    # 8. P2-5: 视觉回归静态文件服务
    visual_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "artifacts", "visual")
    for sub in ("baselines", "current", "diff"):
        d = os.path.join(visual_dir, sub)
        os.makedirs(d, exist_ok=True)
    app.mount("/visual", StaticFiles(directory=visual_dir), name="visual")

    # 9. P2-7.2: /traces 静态挂载已移除，trace 下载统一走安全 API:
    #    GET /api/v2/web-ui/traces/{filename}  (含路径穿越防御 + zip-only)
    traces_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "artifacts", "ui", "traces")
    os.makedirs(traces_dir, exist_ok=True)

    return app
