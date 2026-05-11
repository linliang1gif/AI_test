"""Phase 10A: 危险操作 confirm_text 守卫

设计：
  - 不引入 auth/JWT/RBAC，仅给危险接口加确认参数防误触
  - 调用方需要在请求体 / query 提供 confirm=True 且 confirm_text=指定字符串
  - 缺少 / 错误 → 400 DANGEROUS_OPERATION_CONFIRM_REQUIRED

使用：
    from backend.danger_guard import require_confirm

    @router.delete("/baselines/{bid}")
    def delete_baseline(bid: str, body: DeleteBody, _=require_confirm("DELETE_BASELINE")):
        ...

    其中 DeleteBody 需含 confirm: bool = False, confirm_text: str = ""

也支持纯依赖：
    @router.delete("/baselines/{bid}")
    def delete_baseline(
        bid: str,
        confirm: bool = Body(False),
        confirm_text: str = Body(""),
    ):
        check_confirm("DELETE_BASELINE", confirm, confirm_text)
        ...
"""
from __future__ import annotations
from typing import Any, Optional

from fastapi import HTTPException
from pydantic import BaseModel

from backend.trace_middleware import current_trace_id


CONFIRM_ERROR_CODE = "DANGEROUS_OPERATION_CONFIRM_REQUIRED"


class ConfirmRequest(BaseModel):
    """Mixin：危险操作请求体应继承或包含这两个字段。"""
    confirm: bool = False
    confirm_text: str = ""


def check_confirm(required_text: str, confirm: bool, confirm_text: str) -> None:
    """
    校验 confirm_text 是否匹配。
    缺少或错误时抛 HTTPException(400)，结构：
        {
          "code": "DANGEROUS_OPERATION_CONFIRM_REQUIRED",
          "message": "危险操作需要确认参数",
          "required_confirm_text": "DELETE_BASELINE",
          "trace_id": "..."
        }
    """
    if confirm is True and isinstance(confirm_text, str) and confirm_text == required_text:
        return  # 通过

    detail = {
        "code": CONFIRM_ERROR_CODE,
        "message": "危险操作需要确认参数",
        "required_confirm_text": required_text,
        "trace_id": current_trace_id(),
    }
    raise HTTPException(status_code=400, detail=detail)


def extract_confirm(body: Any) -> tuple[bool, str]:
    """从任意 pydantic / dict 取出 confirm + confirm_text。"""
    if body is None:
        return False, ""
    if isinstance(body, dict):
        return bool(body.get("confirm")), str(body.get("confirm_text") or "")
    return bool(getattr(body, "confirm", False)), str(getattr(body, "confirm_text", "") or "")


__all__ = [
    "ConfirmRequest",
    "check_confirm",
    "extract_confirm",
    "CONFIRM_ERROR_CODE",
]
