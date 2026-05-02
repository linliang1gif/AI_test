"""
页面扫描 & 登录会话管理 API

POST /api/v2/ui/scan          - 扫描页面元素
POST /api/v2/ui/login-session - 执行登录并保存会话
GET  /api/v2/ui/login-session/{project_id} - 获取已保存的会话
DELETE /api/v2/ui/login-session/{project_id} - 删除会话
"""
import asyncio
import logging
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/ui", tags=["UI Testing"])


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
