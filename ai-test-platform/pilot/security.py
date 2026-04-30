from __future__ import annotations

from typing import Iterable, Optional

from fastapi import Header, HTTPException


ROLE_LEVEL = {
    "viewer": 1,
    "operator": 2,
    "admin": 3,
}


def current_role(x_user_role: Optional[str] = Header(default="admin")) -> str:
    role = (x_user_role or "admin").strip().lower()
    if role not in ROLE_LEVEL:
        raise HTTPException(status_code=400, detail=f"Unsupported role: {role}")
    return role


def require_role(required: str):
    def checker(role: str = Header(default="admin", alias="X-User-Role")) -> str:
        current = current_role(role)
        if ROLE_LEVEL[current] < ROLE_LEVEL[required]:
            raise HTTPException(status_code=403, detail=f"Role {current} cannot access this action")
        return current

    return checker


def mask_sensitive_map(data: Optional[dict], extra_keys: Optional[Iterable[str]] = None) -> dict:
    if not data:
        return {}
    sensitive = {"authorization", "token", "access_token", "api_key", "cookie", "secret"}
    if extra_keys:
        sensitive.update(key.lower() for key in extra_keys)
    masked = {}
    for key, value in data.items():
        if key.lower() in sensitive and value not in (None, ""):
            text = str(value)
            masked[key] = f"{text[:3]}***{text[-2:]}" if len(text) > 6 else "***"
        else:
            masked[key] = value
    return masked


def is_write_method(method: str) -> bool:
    return method.upper() in {"POST", "PUT", "PATCH", "DELETE"}
