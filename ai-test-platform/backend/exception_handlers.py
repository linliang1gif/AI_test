"""
P2-2 / Phase 10A 统一异常处理
- 全局 HTTPException handler（业务异常透传）
- 通用 Exception handler（未知异常 → INTERNAL_ERROR 结构）
- 全面使用 services.sanitize 做异常消息/路径/SQL/Traceback 脱敏
- 接入 trace_id：响应体含 trace_id，日志含 trace_id

错误结构（generic）：
{
  "code": "INTERNAL_ERROR",
  "message": "系统内部错误，请查看后端日志",
  "trace_id": "..."
}

HTTPException 结构（保持向后兼容）：
{ "detail": ... , "trace_id": "..." }
"""
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from services.sanitize import (
    sanitize_exception_message,
    sanitize_exception,
    sanitize_value,
)
from backend.trace_middleware import current_trace_id

logger = logging.getLogger("exception_handler")

INTERNAL_ERROR_CODE = "INTERNAL_ERROR"
INTERNAL_ERROR_MESSAGE = "系统内部错误，请查看后端日志"


def register_exception_handlers(app: FastAPI):
    """注册全局异常处理器"""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        tid = current_trace_id()
        # 业务异常：保持原始 detail 结构以兼容前端 / 现有测试
        # 同时添加 trace_id 让客户端能定位
        detail = exc.detail
        if isinstance(detail, (dict, list)):
            content = {"detail": sanitize_value(detail), "trace_id": tid}
        else:
            content = {
                "detail": sanitize_exception_message(str(detail)) if detail else "",
                "trace_id": tid,
            }
        headers = {"X-Trace-Id": tid}
        return JSONResponse(status_code=exc.status_code, content=content, headers=headers)

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        tid = current_trace_id()
        # 服务端记录详细堆栈（含 sanitize），客户端只看到通用错误
        try:
            logger.exception(
                "Unhandled exception on %s %s tid=%s err=%s",
                request.method, request.url.path, tid, sanitize_exception(exc),
            )
        except Exception:
            # 兜底：日志失败也不能影响响应
            logger.error("Unhandled exception (logging itself failed) tid=%s", tid)

        content = {
            "code": INTERNAL_ERROR_CODE,
            "message": INTERNAL_ERROR_MESSAGE,
            "trace_id": tid,
        }
        headers = {"X-Trace-Id": tid}
        return JSONResponse(status_code=500, content=content, headers=headers)
