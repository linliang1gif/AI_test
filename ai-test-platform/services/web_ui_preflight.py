# -*- coding: utf-8 -*-
"""
Web UI execution preflight checks.

Keep this module small and side-effect free: it validates environment/session
state before Playwright starts executing business steps.
"""
import base64
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

from fastapi import HTTPException
from sqlalchemy.orm import Session

from database.models import Environment
from services.auth_service import AuthService


DEFAULT_LOGIN_URL_KEYWORDS = ("/login", "login/page", "sso", "auth", "oauth", "signin")

ERRORS = {
    "PLAYWRIGHT_BROWSER_MISSING": {
        "message": "Playwright 浏览器未安装",
        "suggestion": "请运行 python -m playwright install chromium",
        "status_code": 503,
    },
    "AUTH_PROFILE_MISSING": {
        "message": "Web UI 登录态不存在",
        "suggestion": "请重新保存登录会话",
        "status_code": 400,
    },
    "AUTH_TOKEN_INVALID": {
        "message": "登录态已失效",
        "suggestion": "请重新登录并保存新的登录态",
        "status_code": 401,
    },
    "AUTH_TOKEN_BLACKLISTED": {
        "message": "登录态已失效",
        "suggestion": "请重新登录并保存新的登录态",
        "status_code": 401,
    },
    "WEB_UI_LOGIN_REQUIRED": {
        "message": "登录态失效，目标页面跳转到登录页",
        "suggestion": "请重新保存 Web UI 登录会话",
        "status_code": 401,
    },
    "TARGET_SYSTEM_UNREACHABLE": {
        "message": "目标系统不可访问",
        "suggestion": "请检查目标系统地址、网络、VPN、环境配置",
        "status_code": 503,
    },
}


def _error(code: str, details: Optional[Dict[str, Any]] = None, message: str = "") -> Dict[str, Any]:
    meta = ERRORS[code]
    return {
        "ok": False,
        "code": code,
        "message": message or meta["message"],
        "suggestion": meta["suggestion"],
        "status_code": meta["status_code"],
        "details": details or {},
    }


def raise_preflight_http_error(result: Dict[str, Any]) -> None:
    if result.get("ok", False):
        return
    detail = {
        "code": result.get("code") or "UNKNOWN_EXECUTION_ERROR",
        "message": result.get("message") or "Web UI 执行前预检失败",
        "suggestion": result.get("suggestion") or "请查看错误详情并重试",
    }
    raw_details = result.get("details") or {}
    if isinstance(raw_details, dict):
        detail.update(raw_details)
    else:
        detail["raw_details"] = raw_details
    raise HTTPException(
        status_code=int(result.get("status_code") or 400),
        detail=detail,
    )


def is_login_url(url: str, keywords: Optional[List[str]] = None) -> bool:
    text = (url or "").lower()
    keys = keywords or list(DEFAULT_LOGIN_URL_KEYWORDS)
    return any(str(k).lower() in text for k in keys if str(k).strip())


def _decode_jwt_payload(token: str) -> Dict[str, Any]:
    try:
        part = token.split(".")[1]
        part += "=" * (-len(part) % 4)
        return json.loads(base64.urlsafe_b64decode(part.encode("utf-8")).decode("utf-8"))
    except Exception:
        return {}


def _extract_token_from_session(session: Dict[str, Any]) -> Dict[str, str]:
    local_storage = session.get("local_storage") or session.get("storage") or {}
    if isinstance(local_storage, str):
        try:
            local_storage = json.loads(local_storage)
        except Exception:
            local_storage = {}
    if isinstance(local_storage, dict):
        for key in ("token", "access_token", "Authorization", "authorization"):
            value = local_storage.get(key)
            if value:
                return {"token": _normalize_token(str(value)), "source": f"localStorage.{key}"}

    for cookie in session.get("cookies") or []:
        name = cookie.get("name")
        value = cookie.get("value")
        if name in ("staticToken", "token", "access_token", "Authorization") and value:
            return {"token": _normalize_token(str(value)), "source": f"cookie.{name}"}
    return {"token": "", "source": ""}


def _normalize_token(token: str) -> str:
    token = (token or "").strip()
    if token.lower().startswith("bearer "):
        return token.split(None, 1)[1].strip()
    return token


def _extract_token_from_auth_config(auth_type: Any, auth_config: Dict[str, Any]) -> str:
    auth_type = getattr(auth_type, "value", auth_type) or ""
    auth_config = auth_config or {}
    if auth_type in ("bearer", "custom", "cookie"):
        return _normalize_token(
            auth_config.get("token") or auth_config.get("value") or auth_config.get("cookie_value") or ""
        )
    if auth_type == "oauth2":
        return _normalize_token(auth_config.get("access_token") or auth_config.get("token") or "")
    return ""


def _resolve_environment(
    db: Session,
    project_id: Optional[int],
    environment_id: Optional[int],
    base_url: str,
) -> Optional[Environment]:
    if environment_id:
        env = db.query(Environment).filter(Environment.id == environment_id).first()
        if env:
            return env

    envs = []
    if project_id:
        envs = db.query(Environment).filter(Environment.project_id == project_id).all()
    if not envs:
        envs = db.query(Environment).all()

    if base_url:
        target_host = urlparse(base_url).netloc
        matched = [env for env in envs if urlparse(env.base_url or "").netloc == target_host]
        if matched:
            return matched[0]
    return envs[0] if envs else None


def _resolve_target_url(steps: List[Dict[str, Any]], base_url: str) -> str:
    for step in steps or []:
        if not isinstance(step, dict) or step.get("action") != "goto":
            continue
        target = (step.get("target") or "").strip()
        if not target:
            continue
        if target.startswith(("http://", "https://")):
            return target
        if base_url:
            return urljoin(base_url.rstrip("/") + "/", target.lstrip("/"))
    return base_url or ""


def _validate_business_token(base_url: str, token: str) -> Dict[str, Any]:
    if not base_url or not token:
        return {"valid": False, "status": "missing", "message": "缺少环境地址或 token"}
    try:
        import requests

        url = f"{base_url.rstrip('/')}/userCenter/sysUser/currentUser/info"
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
        msg_lower = msg.lower()
        valid = resp.status_code == 200 and str(code) == "200"
        status = "ok" if valid else "auth_error"
        if "refresh token" in msg_lower:
            status = "refresh_token_used"
            msg = "当前 token 是 refresh_token，不能作为 access_token 使用"
        elif "黑名单" in msg or "black" in msg_lower:
            status = "blacklisted"
        elif str(code) in ("401", "402", "403", "405", "407") or resp.status_code in (401, 403):
            status = "unauthorized"
        return {
            "valid": valid,
            "status": status,
            "http_status": resp.status_code,
            "business_code": code,
            "message": msg,
            "url": url,
        }
    except Exception as exc:
        return {"valid": False, "status": "request_failed", "message": str(exc)[:300]}


def _check_playwright_browser(headless: bool = True) -> Dict[str, Any]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        return _error("PLAYWRIGHT_BROWSER_MISSING", {"phase": "import", "error": str(exc)})

    pw = None
    browser = None
    try:
        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=headless)
        return {"ok": True}
    except Exception as exc:
        return _error("PLAYWRIGHT_BROWSER_MISSING", {"phase": "launch", "error": str(exc)[:800]})
    finally:
        try:
            if browser:
                browser.close()
        finally:
            if pw:
                pw.stop()


def _check_auth_state(
    db: Session,
    env: Optional[Environment],
    execution_config: Dict[str, Any],
    base_url: str,
) -> Dict[str, Any]:
    from services.page_scanner import load_login_session

    session_project_id = execution_config.get("session_project_id") or getattr(env, "project_id", None)
    session = load_login_session(str(session_project_id)) if session_project_id else None
    token_info = _extract_token_from_session(session or {}) if session else {"token": "", "source": ""}

    auth_token = ""
    auth_profile_present = False
    if env:
        service = AuthService(db)
        auth_profile = service.get_by_environment(env.id)
        if auth_profile:
            auth_profile_present = True
            auth_config = service.get_decrypted_config(auth_profile) or {}
            if isinstance(auth_config, str):
                try:
                    auth_config = json.loads(auth_config)
                except Exception:
                    auth_config = {}
            auth_token = _extract_token_from_auth_config(auth_profile.auth_type, auth_config)

    token = token_info.get("token") or auth_token
    has_session_state = bool(
        session
        and ((session.get("cookies") or []) or (session.get("local_storage") or session.get("storage") or {}))
    )
    if not auth_profile_present and not has_session_state:
        return _error(
            "AUTH_PROFILE_MISSING",
            {
                "environment_id": getattr(env, "id", None),
                "session_project_id": session_project_id,
                "reason": "auth_profile_and_web_session_missing",
            },
        )
    if not token and not has_session_state:
        return _error(
            "AUTH_PROFILE_MISSING",
            {
                "environment_id": getattr(env, "id", None),
                "session_project_id": session_project_id,
                "reason": "token_cookie_local_storage_missing",
            },
        )

    if token:
        payload = _decode_jwt_payload(token)
        exp = payload.get("exp")
        if exp and time.time() > float(exp):
            return _error(
                "AUTH_TOKEN_INVALID",
                {"reason": "expired", "token_source": token_info.get("source") or "auth_profile"},
                "登录态已过期",
            )

        validation = _validate_business_token(base_url or getattr(env, "base_url", ""), token)
        if not validation.get("valid"):
            status = validation.get("status")
            if status == "blacklisted":
                return _error("AUTH_TOKEN_BLACKLISTED", {"validation": validation}, "登录态已进入黑名单")
            if status == "request_failed":
                return _error("TARGET_SYSTEM_UNREACHABLE", {"validation": validation})
            if status in ("unauthorized", "auth_error", "refresh_token_used", "expired"):
                return _error("AUTH_TOKEN_INVALID", {"validation": validation})

    return {
        "ok": True,
        "details": {
            "environment_id": getattr(env, "id", None),
            "session_project_id": session_project_id,
            "token_source": token_info.get("source") or ("auth_profile" if auth_token else ""),
            "auth_profile_present": auth_profile_present,
            "web_session_present": bool(session),
        },
    }


def _check_target_page(
    target_url: str,
    execution_config: Dict[str, Any],
    login_keywords: List[str],
) -> Dict[str, Any]:
    if not target_url:
        return {"ok": True, "details": {"target_url": ""}}

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        return _error("PLAYWRIGHT_BROWSER_MISSING", {"phase": "import", "error": str(exc)})

    pw = None
    browser = None
    try:
        from services.page_scanner import load_login_session

        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=execution_config.get("headless", True))
        context = browser.new_context(viewport=execution_config.get("viewport") or {"width": 1366, "height": 768})
        context.set_default_timeout(int(execution_config.get("timeout", 30000)))

        session_project_id = execution_config.get("session_project_id")
        if session_project_id:
            session = load_login_session(str(session_project_id)) or {}
            cookies = session.get("cookies") or []
            if cookies:
                context.add_cookies(cookies)
            local_storage = session.get("local_storage") or session.get("storage") or {}
            if local_storage:
                storage_json = json.dumps(local_storage, ensure_ascii=False)
                context.add_init_script(
                    script=(
                        "(() => {"
                        f"const storage = {storage_json};"
                        "for (const [key, value] of Object.entries(storage)) {"
                        "window.localStorage.setItem(key, String(value));"
                        "}"
                        "})();"
                    )
                )

        page = context.new_page()
        page.goto(target_url, wait_until="domcontentloaded", timeout=int(execution_config.get("preflight_timeout", 15000)))
        try:
            page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            pass
        current_url = page.url
        if is_login_url(current_url, login_keywords):
            return _error(
                "WEB_UI_LOGIN_REQUIRED",
                {"target_url": target_url, "current_url": current_url, "login_keywords": login_keywords},
            )
        return {"ok": True, "details": {"target_url": target_url, "current_url": current_url}}
    except Exception as exc:
        return _error("TARGET_SYSTEM_UNREACHABLE", {"target_url": target_url, "error": str(exc)[:800]})
    finally:
        try:
            if browser:
                browser.close()
        finally:
            if pw:
                pw.stop()


def preflight_web_ui_execution(
    db: Session,
    case_type: str,
    steps: List[Dict[str, Any]],
    assertions: List[Dict[str, Any]],
    execution_config: Dict[str, Any],
    project_id: Optional[int] = None,
    environment_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Run P0 Web UI preflight checks before business steps execute."""
    cfg = dict(execution_config or {})
    base_url = (cfg.get("base_url") or "").strip().rstrip("/")
    env = _resolve_environment(db, project_id, environment_id, base_url)
    if env and not base_url:
        base_url = (env.base_url or "").strip().rstrip("/")
        cfg["base_url"] = base_url
    if env and not cfg.get("session_project_id"):
        cfg["session_project_id"] = str(env.project_id)
    elif project_id and not cfg.get("session_project_id"):
        cfg["session_project_id"] = str(project_id)

    browser_check = _check_playwright_browser(headless=cfg.get("headless", True))
    if not browser_check.get("ok"):
        return browser_check

    auth_required = cfg.get("requires_auth")
    if auth_required is None:
        auth_required = bool(cfg.get("session_project_id") or environment_id or project_id)
    if auth_required:
        auth_check = _check_auth_state(db, env, cfg, base_url)
        if not auth_check.get("ok"):
            return auth_check

    target_url = _resolve_target_url(steps, base_url)
    login_keywords = cfg.get("login_url_keywords") or cfg.get("sso_url_keywords") or list(DEFAULT_LOGIN_URL_KEYWORDS)
    target_check = _check_target_page(target_url, cfg, login_keywords)
    if not target_check.get("ok"):
        return target_check

    return {
        "ok": True,
        "warnings": [],
        "details": {
            "case_type": case_type,
            "target_url": target_url,
            "current_url": target_check.get("details", {}).get("current_url", ""),
            "environment_id": getattr(env, "id", None),
            "session_project_id": cfg.get("session_project_id"),
        },
        "execution_config": cfg,
    }
