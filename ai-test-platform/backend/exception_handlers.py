"""
P2-2 统一异常处理
- 全局 HTTPException handler
- 通用 Exception handler
- 敏感字段脱敏
"""
import re
import logging
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("exception_handler")

_SENSITIVE = re.compile(
    r"(token|authorization|password|secret|cookie|access_token|refresh_token|api[_-]?key)",
    re.IGNORECASE,
)


def _sanitize(text: str) -> str:
    """从错误消息中移除敏感值"""
    return _SENSITIVE.sub(r"\1=****", text)


def register_exception_handlers(app: FastAPI):
    """注册全局异常处理器"""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        # 保持原始 FastAPI 响应结构以兼容现有测试和前端
        if isinstance(exc.detail, (dict, list)):
            content = {"detail": exc.detail}
        else:
            content = {"detail": _sanitize(str(exc.detail))}
        return JSONResponse(status_code=exc.status_code, content=content)

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        tb = traceback.format_exc()
        logger.error("Unhandled exception on %s %s: %s\n%s",
                      request.method, request.url.path, _sanitize(str(exc)), _sanitize(tb))
        return JSONResponse(
            status_code=500,
            content={
                "code": 500,
                "message": "Internal Server Error",
                "detail": _sanitize(str(exc)) if __debug__ else None,
            },
        )
