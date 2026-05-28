"""
P2-2 / Phase 10A / D2-2 统一异常处理
- 全局 HTTPException handler → 标准化结构
- 通用 Exception handler → INTERNAL_ERROR 结构
- 全面使用 services.sanitize 做异常消息/路径/SQL/Traceback 脱敏
- 接入 trace_id：响应体含 trace_id，日志含 trace_id

D2-2 标准错误结构（所有异常统一）：
{
  "code": "ERROR_CODE",
  "message": "用户可理解的错误说明",
  "trace_id": "当前请求追踪ID",
  "details": {},
  "detail": "..."  // 向后兼容字段，值同 message
}
"""
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError

from services.sanitize import (
    sanitize_exception_message,
    sanitize_exception,
    sanitize_value,
)
from backend.trace_middleware import current_trace_id

logger = logging.getLogger("exception_handler")

INTERNAL_ERROR_CODE = "INTERNAL_ERROR"
INTERNAL_ERROR_MESSAGE = "系统内部错误，请查看后端日志"

# HTTP 状态码 → 错误码映射
_STATUS_CODE_MAP = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    503: "SERVICE_UNAVAILABLE",
}


def register_exception_handlers(app: FastAPI):
    """注册全局异常处理器"""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        tid = current_trace_id()
        detail_raw = exc.detail
        error_code = _STATUS_CODE_MAP.get(exc.status_code, f"HTTP_{exc.status_code}")

        if isinstance(detail_raw, dict):
            # 已经是结构化 detail（如 danger_guard 返回的）
            sanitized = sanitize_value(detail_raw)
            message = sanitized.get("message") or sanitized.get("detail") or str(sanitized)
            content = {
                "code": sanitized.get("code", error_code),
                "message": message,
                "trace_id": tid,
                "details": {k: v for k, v in sanitized.items() if k not in ("code", "message", "detail", "trace_id", "suggestion")},
                "detail": message,  # 向后兼容
            }
            if "suggestion" in sanitized:
                content["suggestion"] = sanitized.get("suggestion")
        elif isinstance(detail_raw, list):
            content = {
                "code": error_code,
                "message": str(detail_raw),
                "trace_id": tid,
                "details": {"items": sanitize_value(detail_raw)},
                "detail": str(detail_raw),
            }
        else:
            message = sanitize_exception_message(str(detail_raw)) if detail_raw else ""
            content = {
                "code": error_code,
                "message": message,
                "trace_id": tid,
                "details": {},
                "detail": message,  # 向后兼容
            }
        headers = {"X-Trace-Id": tid}
        return JSONResponse(status_code=exc.status_code, content=content, headers=headers)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        tid = current_trace_id()
        errors = exc.errors()
        # 构建用户友好的摘要消息
        field_errors = []
        for err in errors:
            loc = " -> ".join(str(l) for l in err.get("loc", []))
            msg = err.get("msg", "")
            field_errors.append(f"{loc}: {msg}" if loc else msg)
        message = "; ".join(field_errors[:5])  # 最多展示 5 个字段错误
        if len(field_errors) > 5:
            message += f" (及其他 {len(field_errors) - 5} 个错误)"
        content = {
            "code": "VALIDATION_ERROR",
            "message": message or "请求参数验证失败",
            "trace_id": tid,
            "details": {"errors": sanitize_value(errors)},
            "detail": message or "请求参数验证失败",
        }
        headers = {"X-Trace-Id": tid}
        return JSONResponse(status_code=422, content=content, headers=headers)

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
            "details": {},
        }
        headers = {"X-Trace-Id": tid}
        return JSONResponse(status_code=500, content=content, headers=headers)
