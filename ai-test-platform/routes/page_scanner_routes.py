"""
页面扫描 & 登录会话管理 API

POST /api/v2/ui/scan          - 扫描页面元素
POST /api/v2/ui/login-session - 执行登录并保存会话
GET  /api/v2/ui/login-session/{project_id} - 获取已保存的会话
DELETE /api/v2/ui/login-session/{project_id} - 删除会话
"""
import asyncio
import base64
import json
import logging
import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional

from database.models import Environment
from database.session import get_db
from services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/ui", tags=["UI Testing"])


def _decode_jwt_payload(token: str) -> Dict[str, Any]:
    try:
        part = token.split(".")[1]
        part += "=" * (-len(part) % 4)
        return json.loads(base64.urlsafe_b64decode(part.encode("utf-8")).decode("utf-8"))
    except Exception:
        return {}


def _extract_session_token(session: Dict[str, Any]) -> Dict[str, str]:
    local_storage = session.get("local_storage") or session.get("storage") or {}
    if isinstance(local_storage, dict) and local_storage.get("token"):
        return {"token": str(local_storage["token"]), "source": "localStorage.token"}

    for cookie in session.get("cookies") or []:
        if cookie.get("name") == "staticToken" and cookie.get("value"):
            return {"token": str(cookie["value"]), "source": "cookie.staticToken"}
    return {"token": "", "source": ""}


def _business_validate_url(base_url: str) -> str:
    base = (base_url or "").rstrip("/")
    if not base:
        return ""
    return f"{base}/userCenter/sysUser/currentUser/info"


def _validate_business_token(base_url: str, token: str) -> Dict[str, Any]:
    if not base_url or not token:
        return {"valid": False, "status": "missing", "message": "缺少环境地址或 token"}

    url = _business_validate_url(base_url)
    try:
        import requests

        resp = requests.post(
            url,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=8,
        )
        text = resp.text[:500]
        try:
            body = resp.json()
        except Exception:
            body = {}
        code = body.get("code")
        msg = str(body.get("message") or body.get("msg") or text)
        valid = resp.status_code == 200 and str(code) == "200"
        reason = "ok" if valid else "auth_error"
        msg_lower = msg.lower()
        if "refresh token" in msg_lower:
            reason = "refresh_token_used"
            msg = "当前 token 是 refresh_token，不能作为 access_token 使用"
        elif "黑名单" in msg or "black" in msg_lower:
            reason = "blacklisted"
        elif str(code) in ("401", "402", "403", "405", "407"):
            reason = "unauthorized"
        return {
            "valid": valid,
            "status": "ok" if valid else reason,
            "http_status": resp.status_code,
            "business_code": code,
            "message": msg,
            "url": url,
        }
    except Exception as e:
        return {
            "valid": False,
            "status": "request_failed",
            "message": str(e)[:300],
            "url": url,
        }


def _session_health(db, session_file: str) -> Dict[str, Any]:
    with open(session_file, "r", encoding="utf-8") as f:
        session = json.load(f)

    raw_project_id = session.get("project_id") or os.path.basename(session_file).replace("session_", "").replace(".json", "")
    try:
        project_id = int(raw_project_id)
    except Exception:
        project_id = raw_project_id

    token_info = _extract_session_token(session)
    token = token_info["token"]
    payload = _decode_jwt_payload(token) if token else {}
    exp = payload.get("exp")
    expires_at = datetime.fromtimestamp(exp).isoformat() if exp else ""
    expired = bool(exp and datetime.now().timestamp() > float(exp))

    env = None
    if isinstance(project_id, int):
        env = db.query(Environment).filter(Environment.project_id == project_id).first()

    validation = {"valid": False, "status": "not_checked", "message": "未找到可校验的 token 或环境"}
    if token and env and not expired:
        validation = _validate_business_token(env.base_url, token)
    elif expired:
        validation = {"valid": False, "status": "expired", "message": "Token 已过期"}
    elif not token:
        validation = {"valid": False, "status": "missing_token", "message": "会话中没有 token"}
    elif not env:
        validation = {"valid": False, "status": "missing_environment", "message": "未找到项目对应环境"}

    return {
        "project_id": project_id,
        "environment_id": getattr(env, "id", None),
        "environment_name": getattr(env, "name", ""),
        "base_url": getattr(env, "base_url", ""),
        "saved_at": session.get("saved_at"),
        "page_url": session.get("page_url"),
        "page_title": session.get("page_title"),
        "cookie_count": len(session.get("cookies") or []),
        "local_storage_count": len(session.get("local_storage") or {}),
        "token_source": token_info["source"],
        "token_present": bool(token),
        "token_expired": expired,
        "token_expires_at": expires_at,
        "token_type_hint": "refresh_token" if payload.get("ati") else "access_token_or_unknown",
        "pin": payload.get("pin", ""),
        "validation": validation,
    }


@router.post("/scan")
async def scan_page_endpoint(req: Dict[str, Any]):
    """
    扫描页面，提取所有可交互元素。
    Body: { url, project_id? (用于加载已保存的登录 cookie) }
    """
    url = req.get("url", "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="请提供 url")

    project_id = req.get("project_id")
    cookies = None

    # 如果提供了 project_id，尝试加载已保存的登录会话
    if project_id:
        from services.page_scanner import load_login_session
        session = load_login_session(str(project_id))
        if session:
            cookies = session.get("cookies")

    from services.page_scanner import scan_page
    result = await asyncio.to_thread(scan_page, url, cookies)

    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])

    return result


@router.post("/login-session")
async def save_login_session_endpoint(req: Dict[str, Any]):
    """
    执行登录步骤并保存 Cookie 会话。
    Body: {
        base_url: str,
        project_id: str,
        login_steps: [{ action, target, value }]
    }
    """
    base_url = req.get("base_url", "").strip()
    project_id = str(req.get("project_id", ""))
    login_steps = req.get("login_steps", [])

    if not base_url:
        raise HTTPException(status_code=400, detail="请提供 base_url")
    if not project_id:
        raise HTTPException(status_code=400, detail="请提供 project_id")
    if not login_steps:
        raise HTTPException(status_code=400, detail="请提供 login_steps")

    from services.page_scanner import save_login_session
    result = await asyncio.to_thread(save_login_session, base_url, login_steps, project_id)

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "登录失败"))

    return result


@router.get("/login-session/{project_id}")
async def get_login_session_endpoint(project_id: str):
    """获取已保存的登录会话信息（不返回完整 cookie 内容）"""
    from services.page_scanner import load_login_session
    session = load_login_session(project_id)
    if not session:
        return {"has_session": False}

    return {
        "has_session": True,
        "saved_at": session.get("saved_at"),
        "page_url": session.get("page_url"),
        "page_title": session.get("page_title"),
        "cookie_count": len(session.get("cookies", [])),
        "local_storage_count": len(session.get("local_storage") or {}),
    }


@router.get("/login-sessions/health")
async def get_login_sessions_health(db=Depends(get_db)):
    """检查所有 Web UI 登录会话是否仍可被业务系统识别。"""
    from services.page_scanner import SESSION_DIR

    if not os.path.isdir(SESSION_DIR):
        return {"success": True, "sessions": [], "summary": {"total": 0, "valid": 0, "invalid": 0}}

    sessions = []
    for name in sorted(os.listdir(SESSION_DIR)):
        if not name.startswith("session_") or not name.endswith(".json"):
            continue
        path = os.path.join(SESSION_DIR, name)
        try:
            sessions.append(_session_health(db, path))
        except Exception as e:
            sessions.append({
                "project_id": name.replace("session_", "").replace(".json", ""),
                "validation": {"valid": False, "status": "read_failed", "message": str(e)[:300]},
            })

    valid_count = sum(1 for item in sessions if item.get("validation", {}).get("valid"))
    return {
        "success": True,
        "sessions": sessions,
        "summary": {
            "total": len(sessions),
            "valid": valid_count,
            "invalid": len(sessions) - valid_count,
        },
    }


@router.post("/ai-generate")
async def ai_generate_endpoint(req: Dict[str, Any]):
    """
    AI 智能生成测试用例（基于扫描结果）。
    Body: { page_title, page_url, elements: [...] }
    """
    from services.page_scanner import ai_generate_ui_test
    result = await asyncio.to_thread(ai_generate_ui_test, req)
    return result


@router.delete("/login-session/{project_id}")
async def delete_login_session_endpoint(project_id: str):
    """删除已保存的登录会话"""
    from services.page_scanner import delete_login_session
    deleted = delete_login_session(project_id)
    return {"deleted": deleted}
