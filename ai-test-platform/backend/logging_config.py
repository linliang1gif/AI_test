"""
P2-2 / Phase 10A 统一日志配置
- 敏感字段全文本脱敏（sanitize_text）
- 路径/SQL/Traceback 脱敏（用于错误日志）
- LogRecord 自动注入 trace_id
- 不打印完整 request body / AI prompt
"""
import logging

from services.sanitize import sanitize_text


class TraceIdFilter(logging.Filter):
    """给每条 LogRecord 注入 trace_id 字段；非请求上下文为 '-'。"""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            from backend.trace_middleware import current_trace_id  # 延迟导入避免循环
            tid = current_trace_id()
        except Exception:
            tid = "-"
        record.trace_id = tid or "-"
        return True


class SanitizingFormatter(logging.Formatter):
    """日志格式化器：自动脱敏敏感字段（基于 services.sanitize.sanitize_text）"""

    def format(self, record: logging.LogRecord) -> str:
        # 确保 record 有 trace_id 属性（即使 filter 没绑定也不会 KeyError）
        if not hasattr(record, "trace_id"):
            record.trace_id = "-"
        msg = super().format(record)
        try:
            return sanitize_text(msg)
        except Exception:
            return msg


def setup_logging(level: str = "INFO"):
    """初始化统一日志"""
    fmt = SanitizingFormatter(
        "%(asctime)s [%(levelname)s] [tid=%(trace_id)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    trace_filter = TraceIdFilter()

    # 避免重复 handler
    if not any(isinstance(h, logging.StreamHandler) and getattr(h, "_sanitized", False) for h in root.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(fmt)
        handler.addFilter(trace_filter)
        handler._sanitized = True  # type: ignore
        root.addHandler(handler)
    else:
        # 已有 sanitized handler 时也补上 filter
        for h in root.handlers:
            if isinstance(h, logging.StreamHandler) and getattr(h, "_sanitized", False):
                if not any(isinstance(f, TraceIdFilter) for f in h.filters):
                    h.addFilter(trace_filter)
                # 升级 formatter 到含 trace_id 版
                if not isinstance(h.formatter, SanitizingFormatter) or "%(trace_id)s" not in (h.formatter._fmt or ""):
                    h.setFormatter(fmt)

    # 降低第三方库噪音
    for noisy in ("httpx", "httpcore", "chromadb", "urllib3", "uvicorn.access"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
