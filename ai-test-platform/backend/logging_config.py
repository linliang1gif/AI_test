"""
P2-2 统一日志配置
- 敏感字段脱敏
- 不打印完整 request body / AI prompt
"""
import logging
import re

_SENSITIVE_KEYS = re.compile(
    r"(token|authorization|password|secret|cookie|access_token|refresh_token|api[_-]?key)",
    re.IGNORECASE,
)

_SENSITIVE_PATTERN = re.compile(
    r"((?:token|authorization|password|secret|cookie|access_token|refresh_token|api[_-]?key)"
    r'\s*[=:]\s*["\']?)([^\s"\'&]{4,})',
    re.IGNORECASE,
)


class SanitizingFormatter(logging.Formatter):
    """日志格式化器：自动脱敏敏感字段"""

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        return _SENSITIVE_PATTERN.sub(lambda m: m.group(1) + m.group(2)[:4] + "****", msg)


def setup_logging(level: str = "INFO"):
    """初始化统一日志"""
    fmt = SanitizingFormatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # 避免重复 handler
    if not any(isinstance(h, logging.StreamHandler) and getattr(h, "_sanitized", False) for h in root.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(fmt)
        handler._sanitized = True  # type: ignore
        root.addHandler(handler)

    # 降低第三方库噪音
    for noisy in ("httpx", "httpcore", "chromadb", "urllib3", "uvicorn.access"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
