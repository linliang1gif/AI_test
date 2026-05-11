"""敏感数据脱敏模块。

P2-7: console/network 日志脱敏（最初版本）
Phase 10A: 大幅扩展，覆盖：
  - HTTP headers / URL query / 文本 token
  - 异常消息中的 Windows/Linux 路径
  - 异常消息中的 SQL/SQLite 关键字片段
  - 字典/列表的递归键值脱敏
  - 异常对象 → 安全字符串
"""
from __future__ import annotations
import os
import re
from typing import Any, Dict, Iterable, Mapping, Optional

# ───────────────────────────────────────────
# 敏感字段集合
# ───────────────────────────────────────────
SENSITIVE_HEADERS = {
    "authorization", "cookie", "set-cookie", "x-api-key",
    "x-auth-token", "x-csrf-token", "proxy-authorization",
    "x-token", "x-access-token", "x-secret",
}

SENSITIVE_URL_PARAMS = {
    "token", "access_token", "refresh_token", "api_key", "apikey",
    "key", "secret", "password", "passwd", "pwd", "auth", "session",
}

# 敏感字段名正则（用于字典键判定）
SENSITIVE_KEY_RE = re.compile(
    r"(token|authorization|password|passwd|pwd|secret|cookie|"
    r"access[_-]?token|refresh[_-]?token|api[_-]?key|client[_-]?secret|"
    r"session[_-]?id|csrf|auth)",
    re.IGNORECASE,
)

# 文本中 "key=value" 形式
SENSITIVE_INLINE_RE = re.compile(
    r'((?:Bearer|Basic|Token|token|authorization|access_token|refresh_token|'
    r'api_key|apikey|password|passwd|pwd|secret|cookie|client_secret)'
    r'\s*[:=]\s*)["\']?([^\s"\',;)&]{4,})["\']?',
    re.IGNORECASE,
)

# Bearer/Basic 头形式
BEARER_RE = re.compile(
    r'(Bearer|Basic)\s+([A-Za-z0-9_\-\.+/=]{8,})',
    re.IGNORECASE,
)

# Windows 路径：C:\path\to\file 或 D:/path/to/file
WIN_PATH_RE = re.compile(
    r'(?<![A-Za-z])([A-Za-z]:[\\/][^\s,;<>"\'`)*?|]+)'
)

# Linux/macOS 绝对路径：/Users/, /home/, /var/, /tmp/, /opt/, /etc/, /root/
LINUX_PATH_RE = re.compile(
    r'(/(?:Users|home|var|tmp|opt|etc|root|usr/local|private/var)/[^\s,;<>"\'`)]+)'
)

# Traceback 块：以 "Traceback (most recent call last):" 开头到下一个空行
TRACEBACK_RE = re.compile(
    r'Traceback \(most recent call last\):.*?(?=\n\S|\Z)',
    re.DOTALL,
)

# SQL 关键字 + 表/字段（出现就视为内部 SQL 泄露线索）
SQL_LEAK_RE = re.compile(
    r'\b(?:SELECT|INSERT INTO|UPDATE\s+\w+\s+SET|DELETE FROM|CREATE TABLE|'
    r'ALTER TABLE|DROP TABLE|sqlite_master|sqlite3\.OperationalError|'
    r'IntegrityError|OperationalError|ProgrammingError)\b[^\n]{0,200}',
    re.IGNORECASE,
)

REDACTED = "[REDACTED]"


# ───────────────────────────────────────────
# Headers / URL / Text 三件套（向后兼容）
# ───────────────────────────────────────────
def sanitize_headers(headers: Optional[Mapping[str, str]]) -> Dict[str, str]:
    if not headers:
        return {}
    out: Dict[str, str] = {}
    for k, v in headers.items():
        if k.lower() in SENSITIVE_HEADERS or SENSITIVE_KEY_RE.search(k):
            out[k] = REDACTED
        else:
            out[k] = v if isinstance(v, str) else str(v)
    return out


def sanitize_url(url: Optional[str]) -> str:
    if not url:
        return url or ""
    for param in SENSITIVE_URL_PARAMS:
        url = re.sub(
            rf'([?&]){param}=[^&#]*',
            rf'\1{param}=' + REDACTED,
            url,
            flags=re.IGNORECASE,
        )
    return url


def sanitize_text(text: Optional[str]) -> str:
    """对文本中的 Bearer/key=value 形式做掩码"""
    if not text:
        return text or ""
    text = BEARER_RE.sub(lambda m: f"{m.group(1)} " + REDACTED, text)
    text = SENSITIVE_INLINE_RE.sub(lambda m: m.group(1) + REDACTED, text)
    return text


# ───────────────────────────────────────────
# Phase 10A: 路径脱敏
# ───────────────────────────────────────────
def sanitize_path(text: Optional[str]) -> str:
    """脱敏 Windows / Linux 文件路径，保留 basename 提示"""
    if not text:
        return text or ""

    def _win(m: re.Match) -> str:
        p = m.group(1)
        base = os.path.basename(p.replace("\\", "/")) or "?"
        return f"<path:{base}>"

    def _nix(m: re.Match) -> str:
        p = m.group(1)
        base = os.path.basename(p) or "?"
        return f"<path:{base}>"

    text = WIN_PATH_RE.sub(_win, text)
    text = LINUX_PATH_RE.sub(_nix, text)
    return text


# ───────────────────────────────────────────
# Phase 10A: 异常消息脱敏
# ───────────────────────────────────────────
def sanitize_exception_message(msg: Optional[str]) -> str:
    """
    脱敏异常消息：
      1. 去掉 Traceback 块
      2. 去掉 SQL 片段（防 sqlite/SELECT/...）
      3. 去掉 Windows / Linux 文件路径
      4. 去掉 Bearer/token=xxx 等敏感字面值
    用于直接返回到 HTTP 响应中。
    """
    if not msg:
        return msg or ""
    s = str(msg)
    s = TRACEBACK_RE.sub("<traceback redacted>", s)
    s = SQL_LEAK_RE.sub("<sql redacted>", s)
    s = sanitize_path(s)
    s = sanitize_text(s)
    return s


def sanitize_exception(exc: BaseException) -> str:
    """异常对象 → 已脱敏的安全字符串"""
    try:
        return sanitize_exception_message(f"{type(exc).__name__}: {exc}")
    except Exception:
        return f"{type(exc).__name__}: <unprintable>"


# ───────────────────────────────────────────
# Phase 10A: 递归值脱敏
# ───────────────────────────────────────────
_MAX_DEPTH = 8


def sanitize_value(value: Any, _depth: int = 0) -> Any:
    """
    递归脱敏 Python 数据结构：
      - dict: 敏感键名的值替换为 [REDACTED]
      - list/tuple: 逐项脱敏
      - str: 对 Bearer/key=value 做掩码
      - 其他类型原样返回
    """
    if _depth >= _MAX_DEPTH:
        return "<truncated>"
    if isinstance(value, Mapping):
        out: Dict[Any, Any] = {}
        for k, v in value.items():
            key_str = str(k)
            if SENSITIVE_KEY_RE.search(key_str):
                if isinstance(v, str) and len(v) > 4:
                    out[k] = v[:2] + "****" + v[-2:]
                else:
                    out[k] = REDACTED
            else:
                out[k] = sanitize_value(v, _depth + 1)
        return out
    if isinstance(value, (list, tuple)):
        return type(value)(sanitize_value(v, _depth + 1) for v in value)
    if isinstance(value, str):
        return sanitize_text(value)
    return value


# ───────────────────────────────────────────
# 兼容入口
# ───────────────────────────────────────────
def sanitize_console_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(entry)
    if "text" in out:
        out["text"] = sanitize_text(out["text"])
    return out


def sanitize_network_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(entry)
    if "url" in out:
        out["url"] = sanitize_url(out["url"])
    if "headers" in out:
        out["headers"] = sanitize_headers(out["headers"])
    return out


__all__ = [
    "sanitize_headers", "sanitize_url", "sanitize_text",
    "sanitize_path", "sanitize_exception_message", "sanitize_exception",
    "sanitize_value",
    "sanitize_console_entry", "sanitize_network_entry",
    "SENSITIVE_HEADERS", "SENSITIVE_URL_PARAMS", "SENSITIVE_KEY_RE",
    "REDACTED",
]
