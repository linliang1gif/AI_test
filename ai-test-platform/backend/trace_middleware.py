"""Phase 10A: trace_id middleware

每个请求生成或透传 X-Trace-Id。trace_id 通过 contextvars 暴露给：
  - 日志记录（logging filter）
  - 异常处理器（写入响应体）
  - 业务代码（可读 current_trace_id() 写入审计）

启用方式：
    from backend.trace_middleware import TraceIdMiddleware
    app.add_middleware(TraceIdMiddleware)
"""
from __future__ import annotations
import contextvars
import uuid
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# ContextVar：跨 async 边界传递 trace_id
_trace_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "trace_id", default="-"
)

TRACE_HEADER = "X-Trace-Id"


def current_trace_id() -> str:
    """获取当前请求 trace_id；非请求上下文返回 '-'。"""
    try:
        return _trace_id_var.get()
    except LookupError:
        return "-"


def set_trace_id(tid: str) -> contextvars.Token:
    """显式设置 trace_id，返回 token 以便恢复。测试用。"""
    return _trace_id_var.set(tid)


def reset_trace_id(token: contextvars.Token) -> None:
    _trace_id_var.reset(token)


def _gen_trace_id() -> str:
    return uuid.uuid4().hex[:16]


def _is_valid_trace_id(s: Optional[str]) -> bool:
    if not s:
        return False
    if len(s) > 128:
        return False
    # 仅允许 [a-zA-Z0-9_-]，防止注入
    for ch in s:
        if not (ch.isalnum() or ch in ("_", "-", ".")):
            return False
    return True


class TraceIdMiddleware(BaseHTTPMiddleware):
    """
    1. 优先使用客户端传入的 X-Trace-Id（合法时）
    2. 否则生成 uuid4[:16]
    3. 写入 contextvar 供 logger / exception handler 使用
    4. 写入 request.state.trace_id 供路由直接读取
    5. 响应头回写 X-Trace-Id
    """

    async def dispatch(self, request: Request, call_next):
        incoming = request.headers.get(TRACE_HEADER)
        tid = incoming if _is_valid_trace_id(incoming) else _gen_trace_id()

        token = _trace_id_var.set(tid)
        request.state.trace_id = tid
        try:
            response: Response = await call_next(request)
        finally:
            _trace_id_var.reset(token)

        response.headers[TRACE_HEADER] = tid
        return response


__all__ = [
    "TraceIdMiddleware",
    "TRACE_HEADER",
    "current_trace_id",
    "set_trace_id",
    "reset_trace_id",
]
