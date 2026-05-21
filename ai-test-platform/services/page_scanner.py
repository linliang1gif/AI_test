"""
Page Scanner & Login Session Manager

1. scan_page(url, cookies) → screenshot + interactive elements list
2. save_login_session(url, steps) → execute login, save cookies
3. load_login_session(project_id) → cookies
"""
import os
import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

SCREENSHOT_DIR = os.path.join("data", "artifacts", "ui", "screenshots")
SESSION_DIR = os.path.join("data", "sessions")


def _ensure_dirs():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    os.makedirs(SESSION_DIR, exist_ok=True)


def _session_path(project_id: str) -> str:
    return os.path.join(SESSION_DIR, f"session_{project_id}.json")


def _chrome_executable_candidates() -> List[str]:
    candidates = [
        os.getenv("PLAYWRIGHT_CHROME_EXECUTABLE", ""),
        r"D:\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    seen = set()
    existing = []
    for path in candidates:
        if not path or path in seen:
            continue
        seen.add(path)
        if os.path.exists(path):
            existing.append(path)
    return existing


def _launch_chromium(pw, headless: bool = True):
    try:
        return pw.chromium.launch(headless=headless)
    except Exception as default_error:
        logger.warning("Default Playwright Chromium launch failed, trying local Chrome: %s", default_error)
        for executable_path in _chrome_executable_candidates():
            try:
                return pw.chromium.launch(executable_path=executable_path, headless=headless)
            except Exception as fallback_error:
                logger.debug("Chrome fallback launch failed (%s): %s", executable_path, fallback_error)
        raise default_error


def scan_page(url: str, cookies: Optional[List[Dict]] = None,
              viewport: Dict = None) -> Dict[str, Any]:
    """
    Visit a URL with Playwright, extract all interactive elements.
    Returns: { screenshot_url, elements: [...], page_title, page_url }
    """
    _ensure_dirs()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {"error": "Playwright 未安装"}

    vp = viewport or {"width": 1366, "height": 768}
    pw = None
    browser = None
    result = {"elements": [], "screenshot_url": "", "page_title": "", "page_url": ""}

    try:
        pw = sync_playwright().start()
        browser = _launch_chromium(pw, headless=True)
        context = browser.new_context(viewport=vp)
        context.set_default_timeout(15000)

        # Load cookies if provided
        if cookies:
            context.add_cookies(cookies)

        page = context.new_page()
        page.goto(url, wait_until="networkidle", timeout=20000)
        page.wait_for_timeout(2000)

        result["page_title"] = page.title()
        result["page_url"] = page.url

        # Screenshot
        ts = int(time.time())
        ss_name = f"scan_{ts}.png"
        ss_path = os.path.join(SCREENSHOT_DIR, ss_name)
        page.screenshot(path=ss_path, full_page=False)
        result["screenshot_url"] = f"/screenshots/{ss_name}"

        # Extract interactive elements using JS
        elements = page.evaluate("""() => {
            const results = [];
            const seen = new Set();

            function getSelector(el) {
                if (el.id) return '#' + el.id;
                if (el.name) return el.tagName.toLowerCase() + '[name=' + el.name + ']';
                if (el.type && el.tagName === 'INPUT') return 'input[type=' + el.type + ']';
                if (el.className && typeof el.className === 'string') {
                    const cls = el.className.trim().split(/\\s+/).filter(c => c && !c.startsWith('el-') || c === el.className.trim().split(/\\s+/)[0]).slice(0, 2).join('.');
                    if (cls) return el.tagName.toLowerCase() + '.' + cls;
                }
                if (el.getAttribute('placeholder')) return el.tagName.toLowerCase() + '[placeholder="' + el.getAttribute('placeholder') + '"]';
                return el.tagName.toLowerCase();
            }

            function getLabel(el) {
                // text content
                let text = (el.innerText || el.textContent || '').trim().substring(0, 50);
                if (!text && el.getAttribute('placeholder')) text = el.getAttribute('placeholder');
                if (!text && el.getAttribute('aria-label')) text = el.getAttribute('aria-label');
                if (!text && el.getAttribute('title')) text = el.getAttribute('title');
                if (!text && el.getAttribute('value')) text = el.getAttribute('value');
                return text;
            }

            function getBounds(el) {
                const r = el.getBoundingClientRect();
                return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
            }

            // Buttons
            document.querySelectorAll('button, [role=button], input[type=button], input[type=submit]').forEach(el => {
                if (el.offsetParent === null) return; // hidden
                const sel = getSelector(el);
                const key = sel + getLabel(el);
                if (seen.has(key)) return;
                seen.add(key);
                results.push({
                    type: 'button',
                    selector: sel,
                    label: getLabel(el),
                    tag: el.tagName.toLowerCase(),
                    bounds: getBounds(el),
                    action_hint: 'click'
                });
            });

            // Input fields
            document.querySelectorAll('input:not([type=hidden]):not([type=button]):not([type=submit]):not([type=checkbox]):not([type=radio]), textarea').forEach(el => {
                if (el.offsetParent === null) return;
                const sel = getSelector(el);
                const key = sel;
                if (seen.has(key)) return;
                seen.add(key);
                results.push({
                    type: 'input',
                    selector: sel,
                    label: getLabel(el) || el.getAttribute('placeholder') || el.getAttribute('name') || '',
                    tag: el.tagName.toLowerCase(),
                    input_type: el.type || 'text',
                    bounds: getBounds(el),
                    action_hint: 'fill'
                });
            });

            // Checkboxes & radios
            document.querySelectorAll('input[type=checkbox], input[type=radio]').forEach(el => {
                if (el.offsetParent === null) return;
                const sel = getSelector(el);
                if (seen.has(sel)) return;
                seen.add(sel);
                results.push({
                    type: 'checkbox',
                    selector: sel,
                    label: getLabel(el) || el.getAttribute('name') || '',
                    tag: 'input',
                    input_type: el.type,
                    bounds: getBounds(el),
                    action_hint: 'click'
                });
            });

            // Links
            document.querySelectorAll('a[href]').forEach(el => {
                if (el.offsetParent === null) return;
                const text = getLabel(el);
                if (!text) return;
                const sel = getSelector(el);
                const key = sel + text;
                if (seen.has(key)) return;
                seen.add(key);
                results.push({
                    type: 'link',
                    selector: sel,
                    label: text,
                    href: el.getAttribute('href'),
                    tag: 'a',
                    bounds: getBounds(el),
                    action_hint: 'click'
                });
            });

            // Select/dropdown
            document.querySelectorAll('select').forEach(el => {
                if (el.offsetParent === null) return;
                const sel = getSelector(el);
                if (seen.has(sel)) return;
                seen.add(sel);
                const options = Array.from(el.options).map(o => o.text).slice(0, 10);
                results.push({
                    type: 'select',
                    selector: sel,
                    label: getLabel(el) || el.getAttribute('name') || '',
                    tag: 'select',
                    options: options,
                    bounds: getBounds(el),
                    action_hint: 'select'
                });
            });

            return results;
        }""")

        result["elements"] = elements
        result["element_count"] = len(elements)

    except Exception as e:
        logger.error(f"Page scan error: {e}")
        result["error"] = str(e)
    finally:
        try:
            if browser:
                browser.close()
        except Exception as _e:
            logger.debug("browser.close() failed: %s", _e)
        try:
            if pw:
                pw.stop()
        except Exception as _e:
            logger.debug("playwright.stop() failed: %s", _e)

    return result


def save_login_session(
    base_url: str,
    login_steps: List[Dict],
    project_id: str,
    viewport: Dict = None
) -> Dict[str, Any]:
    """
    Execute login steps, then save cookies/storage for later reuse.
    Returns: { success, cookie_count, session_file }
    """
    _ensure_dirs()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {"success": False, "error": "Playwright 未安装"}

    vp = viewport or {"width": 1366, "height": 768}
    pw = None
    browser = None

    try:
        pw = sync_playwright().start()
        browser = _launch_chromium(pw, headless=True)
        context = browser.new_context(viewport=vp)
        context.set_default_timeout(15000)
        page = context.new_page()

        # Execute login steps
        for step in login_steps:
            action = step.get("action", "")
            target = step.get("target", "")
            value = step.get("value", "")

            if action == "goto":
                url = target
                if not url.startswith(("http://", "https://")):
                    url = f"{base_url.rstrip('/')}/{target.lstrip('/')}"
                page.goto(url, wait_until="networkidle", timeout=20000)
            elif action == "fill":
                page.fill(target, value)
            elif action == "click":
                page.click(target)
            elif action == "wait_for":
                if target.isdigit():
                    page.wait_for_timeout(int(target))
                else:
                    page.wait_for_selector(target, timeout=10000)

        # Save cookies and localStorage
        cookies = context.cookies()
        local_storage = page.evaluate(
            "() => Object.fromEntries(Object.entries(window.localStorage))"
        )
        session_data = {
            "project_id": project_id,
            "base_url": base_url,
            "cookies": cookies,
            "local_storage": local_storage,
            "saved_at": datetime.now().isoformat(),
            "page_url": page.url,
            "page_title": page.title(),
        }

        path = _session_path(project_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)

        # Screenshot after login
        ts = int(time.time())
        ss_name = f"login_{project_id}_{ts}.png"
        ss_path = os.path.join(SCREENSHOT_DIR, ss_name)
        page.screenshot(path=ss_path)

        return {
            "success": True,
            "cookie_count": len(cookies),
            "session_file": path,
            "screenshot_url": f"/screenshots/{ss_name}",
            "page_url": page.url,
            "page_title": page.title(),
        }

    except Exception as e:
        logger.error(f"Login session save error: {e}")
        return {"success": False, "error": str(e)}
    finally:
        try:
            if browser:
                browser.close()
        except Exception as _e:
            logger.debug("browser.close() failed: %s", _e)
        try:
            if pw:
                pw.stop()
        except Exception as _e:
            logger.debug("playwright.stop() failed: %s", _e)


def load_login_session(project_id: str) -> Optional[Dict]:
    """Load saved login session (cookies) for a project."""
    path = _session_path(project_id)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def ai_generate_ui_test(page_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Use AI (LLM) to analyze scanned page elements and generate smart test cases.
    
    Args:
        page_info: { page_title, page_url, elements: [...] }
    Returns:
        { title, module, steps: [...], assertions: [...] }
    """
    try:
        from agent.llm_client import LLMClient
        client = LLMClient()
    except Exception as e:
        logger.warning(f"AI client init failed: {e}, falling back to rule-based")
        return _rule_based_generate(page_info)

    elements_desc = []
    for el in (page_info.get("elements") or [])[:30]:
        elements_desc.append(f"- [{el.get('type')}] selector=\"{el.get('selector')}\" label=\"{el.get('label','')}\"")
    elements_text = "\n".join(elements_desc) if elements_desc else "(no elements)"

    prompt = f"""你是一个Web UI自动化测试专家。根据以下页面扫描结果，生成一个完整的Playwright测试用例。

页面标题: {page_info.get('page_title', '')}
页面URL: {page_info.get('page_url', '')}
页面上的可交互元素:
{elements_text}

请生成JSON格式的测试用例:
{{
  "title": "测试用例标题(中文)",
  "module": "所属模块(中文)",
  "steps": [
    {{"action": "goto|click|fill|wait_for|screenshot", "target": "路径或CSS选择器", "value": "填入的值(fill时需要)", "description": "步骤说明(中文)"}}
  ],
  "assertions": [
    {{"type": "url_contains|url_not_contains|text_visible|element_visible", "target": "CSS选择器(element_visible时)", "value": "匹配值", "description": "断言说明(中文)"}}
  ]
}}

要求:
1. 第一步用goto打开页面(用相对路径)
2. 对输入框用fill操作，value留空让用户自己填
3. 对按钮用click操作
4. 适当加wait_for等待
5. 最后加screenshot截图
6. 至少加1-2个断言验证页面正确性
7. steps不要超过15步
8. 只返回JSON，不要其他内容
9. 重要：如果是登录页，断言应验证登录成功后跳转离开登录页，用url_not_contains检查不再包含login/sso，而不是url_contains检查还在登录页
10. url_contains的value应该是登录成功后的目标页关键词(如index、dashboard等)"""

    try:
        result = client.generate_json(prompt, system_prompt="你是Web自动化测试专家，只返回JSON格式。")
        if result and result.get("steps"):
            return result
        else:
            logger.warning("AI returned invalid result, falling back")
            return _rule_based_generate(page_info)
    except Exception as e:
        logger.error(f"AI generation failed: {e}")
        return _rule_based_generate(page_info)


def _rule_based_generate(page_info: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback rule-based test case generation."""
    elements = page_info.get("elements") or []
    inputs = [e for e in elements if e.get("type") == "input"]
    buttons = [e for e in elements if e.get("type") == "button"]
    links = [e for e in elements if e.get("type") == "link"]
    
    page_url = page_info.get("page_url", "")
    page_title = page_info.get("page_title", "")
    try:
        from urllib.parse import urlparse
        path = urlparse(page_url).path or "/"
    except Exception as _e:
        logger.debug("urlparse(%s) failed: %s", page_url, _e)
        path = "/"

    steps = [
        {"action": "goto", "target": path, "value": "", "description": "打开页面"},
        {"action": "wait_for", "target": "2000", "value": "", "description": "等待加载"},
    ]
    
    if len(inputs) >= 2 and len(buttons) >= 1:
        for inp in inputs[:6]:
            steps.append({"action": "fill", "target": inp["selector"], "value": "", "description": inp.get("label", "填写")})
        submit = next((b for b in buttons if any(k in (b.get("label","") + b.get("selector","")) for k in ["提交","保存","确定","登录","submit"])), buttons[0] if buttons else None)
        if submit:
            steps.append({"action": "click", "target": submit["selector"], "value": "", "description": submit.get("label", "提交")})
        steps.append({"action": "wait_for", "target": "2000", "value": "", "description": "等待响应"})
        title = f"表单测试 - {page_title or path}"
        module = "业务测试"
    elif len(links) >= 3:
        title = f"页面导航 - {page_title or path}"
        module = "UI测试"
    else:
        title = f"页面测试 - {page_title or path}"
        module = "UI测试"

    steps.append({"action": "screenshot", "target": "", "value": "", "description": "截图"})

    return {
        "title": title,
        "module": module,
        "steps": steps,
        "assertions": [
            {"type": "element_visible", "target": "body", "value": "", "description": "页面正常"},
            {"type": "url_contains", "target": "", "value": path.split("?")[0], "description": "URL正确"},
        ]
    }


def delete_login_session(project_id: str) -> bool:
    """Delete saved login session."""
    path = _session_path(project_id)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False
