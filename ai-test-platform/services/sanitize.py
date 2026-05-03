"""P2-7: Sensitive data sanitization for console/network logs."""
import re
from typing import Any, Dict, List, Optional

SENSITIVE_HEADERS = {
    "authorization", "cookie", "set-cookie", "x-api-key",
    "x-auth-token", "x-csrf-token", "proxy-authorization",
}
SENSITIVE_URL_PARAMS = {"token", "access_token", "api_key", "key", "secret", "password", "passwd"}
SENSITIVE_PATTERN = re.compile(
    r'(Bearer\s+|Basic\s+|token=|access_token=|api_key=|password=|secret=)\S+',
    re.IGNORECASE,
)


def sanitize_headers(headers: Optional[Dict[str, str]]) -> Dict[str, str]:
    if not headers:
        return {}
    out = {}
    for k, v in headers.items():
        if k.lower() in SENSITIVE_HEADERS:
            out[k] = "[REDACTED]"
        else:
            out[k] = v
    return out


def sanitize_url(url: str) -> str:
    if not url:
        return url
    for param in SENSITIVE_URL_PARAMS:
        url = re.sub(
            rf'([?&]){param}=[^&]*',
            rf'\1{param}=[REDACTED]',
            url,
            flags=re.IGNORECASE,
        )
    return url


def sanitize_text(text: str) -> str:
    if not text:
        return text
    return SENSITIVE_PATTERN.sub(r'\1[REDACTED]', text)


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
