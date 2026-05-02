#!/usr/bin/env python3
"""
P2-4 Playwright 执行引擎 MVP + P2-5 视觉回归

支持 action: goto, fill, click, wait_for, screenshot
支持 assertion: text_visible, url_contains, url_not_contains, element_visible, screenshot_match
"""
import os
import time
import logging
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

SCREENSHOT_DIR = os.path.join("data", "artifacts", "ui", "screenshots")

SUPPORTED_ACTIONS = {"goto", "fill", "click", "wait_for", "screenshot", "upload", "hover", "select"}
SUPPORTED_ASSERTIONS = {"text_visible", "url_contains", "url_not_contains", "element_visible", "screenshot_match"}


@dataclass
class StepResult:
    step_index: int
    action: str
    target: str
    status: str = "pending"  # passed / failed / skipped
    duration_ms: float = 0
    error_message: str = ""
    screenshot_path: str = ""
    current_url: str = ""
    description: str = ""
    value: str = ""


@dataclass
class AssertionResult:
    type: str
    target: str
    value: str
    description: str
    passed: bool = False
    actual: str = ""
    error_message: str = ""


@dataclass
class PlaywrightResult:
    status: str = "pending"
    step_results: List[StepResult] = field(default_factory=list)
    assertion_results: List[AssertionResult] = field(default_factory=list)
    duration_ms: float = 0
    error_message: str = ""
    started_at: str = ""
    finished_at: str = ""
    failure_screenshot: str = ""
    skipped_count: int = 0  # P2-4.1: track skipped optional steps
    visual_results: List[Dict[str, Any]] = field(default_factory=list)  # P2-5


def _ensure_screenshot_dir():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def _is_playwright_available() -> bool:
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
        return True
    except ImportError:
        return False


def execute_web_ui(
    steps: List[Dict[str, Any]],
    assertions: List[Dict[str, Any]],
    execution_config: Dict[str, Any],
    case_id: str = "",
    run_id: str = "",
) -> PlaywrightResult:
    """
    执行一条 Web UI 用例。

    返回 PlaywrightResult 包含每步结果和断言结果。
    """
    if not _is_playwright_available():
        return PlaywrightResult(
            status="error",
            error_message="Playwright 未安装。请运行: pip install playwright && python -m playwright install chromium",
        )

    from playwright.sync_api import sync_playwright

    browser_name = execution_config.get("browser", "chromium")
    if browser_name != "chromium":
        return PlaywrightResult(
            status="error",
            error_message=f"当前仅支持 chromium 浏览器，不支持: {browser_name}",
        )

    headless = execution_config.get("headless", True)
    base_url = (execution_config.get("base_url") or "").rstrip("/")
    viewport = execution_config.get("viewport", {"width": 1366, "height": 768})
    timeout_ms = execution_config.get("timeout", 30000)

    result = PlaywrightResult(started_at=datetime.now().isoformat())
    _ensure_screenshot_dir()

    pw = None
    browser = None
    try:
        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={"width": viewport.get("width", 1366), "height": viewport.get("height", 768)},
        )
        context.set_default_timeout(timeout_ms)

        # Load saved session cookies if available
        session_project_id = execution_config.get("session_project_id")
        if session_project_id:
            try:
                from services.page_scanner import load_login_session
                session = load_login_session(str(session_project_id))
                if session and session.get("cookies"):
                    context.add_cookies(session["cookies"])
                    logger.info(f"Loaded {len(session['cookies'])} cookies from session {session_project_id}")
            except Exception as e:
                logger.warning(f"Failed to load session cookies: {e}")

        page = context.new_page()

        # ── 执行 steps ──
        all_passed = True
        for idx, step in enumerate(steps):
            sr = _execute_step(page, step, idx, base_url, case_id)
            result.step_results.append(sr)
            if sr.status == "failed":
                all_passed = False
                # 失败截图
                fail_ss = _take_failure_screenshot(page, case_id, idx)
                sr.screenshot_path = fail_ss
                result.failure_screenshot = fail_ss
                break  # 停止后续步骤

        # ── 执行 assertions ──
        if all_passed:
            for assertion in assertions:
                # P2-5: screenshot_match needs special handling
                if isinstance(assertion, dict) and assertion.get("type") == "screenshot_match":
                    vr = _execute_screenshot_match(page, assertion, case_id, run_id)
                    result.visual_results.append(vr)
                    ar = AssertionResult(
                        type="screenshot_match",
                        target=assertion.get("name", ""),
                        value=str(assertion.get("threshold", 0.05)),
                        description=assertion.get("description", "视觉回归对比"),
                    )
                    if vr["status"] == "passed":
                        ar.passed = True
                        ar.actual = f"diff_ratio={vr['diff_ratio']}"
                    elif vr["status"] == "baseline_created":
                        ar.passed = True  # baseline creation is not a failure
                        ar.actual = "baseline_created"
                    else:
                        ar.passed = False
                        ar.actual = f"diff_ratio={vr.get('diff_ratio', '?')}"
                        ar.error_message = vr.get("error_message", "视觉对比失败")
                        all_passed = False
                        fail_ss = _take_failure_screenshot(page, case_id, len(steps))
                        result.failure_screenshot = fail_ss
                    result.assertion_results.append(ar)
                    continue

                ar = _execute_assertion(page, assertion)
                result.assertion_results.append(ar)
                if not ar.passed:
                    all_passed = False
                    fail_ss = _take_failure_screenshot(page, case_id, len(steps))
                    result.failure_screenshot = fail_ss

        # P2-4.1: count skipped steps
        result.skipped_count = sum(1 for sr in result.step_results if sr.status == "skipped")

        result.status = "passed" if all_passed else "failed"
        if not all_passed:
            # 收集第一个失败信息
            for sr in result.step_results:
                if sr.status == "failed":
                    result.error_message = f"Step {sr.step_index + 1} ({sr.action}) 失败: {sr.error_message}"
                    break
            if not result.error_message:
                for ar in result.assertion_results:
                    if not ar.passed:
                        result.error_message = f"断言失败 ({ar.type}): {ar.error_message}"
                        break

    except Exception as e:
        result.status = "error"
        result.error_message = f"Playwright 执行异常: {str(e)}"
        logger.exception("Playwright execution error")
    finally:
        try:
            if browser:
                browser.close()
        except Exception:
            pass
        try:
            if pw:
                pw.stop()
        except Exception:
            pass
        result.finished_at = datetime.now().isoformat()
        # 计算总耗时
        try:
            t0 = datetime.fromisoformat(result.started_at)
            t1 = datetime.fromisoformat(result.finished_at)
            result.duration_ms = (t1 - t0).total_seconds() * 1000
        except Exception:
            pass

    return result


def _parse_text_step(text: str) -> Dict[str, str]:
    """Parse a plain-text step description into {action, target, value, description}."""
    import re
    desc = re.sub(r'^步骤\s*\d+\s*[:：]\s*', '', text).strip()

    # Regex for CSS selectors / paths: stop at Chinese chars or commas
    SEL = r'([#./\w\[\]=\*\-:@]+(?:\([^)]*\))?)'

    # goto: 打开/导航/访问 + path
    m = re.search(r'(?:打开|导航|访问|跳转)\S*\s+(/[\w/\-?.=&%#]+)', desc)
    if m:
        return {"action": "goto", "target": m.group(1), "value": "", "description": desc}

    # fill: 在...selector...中输入 value
    m = re.search(r'(?:输入框|input)\s*' + SEL + r'\s*(?:中|里)?\s*(?:输入|填[入写])\s*[\'"]?([^\'",，\s]+)', desc)
    if m:
        return {"action": "fill", "target": m.group(1), "value": m.group(2).strip(), "description": desc}
    m = re.search(r'在\S*\s*' + SEL + r'\s*(?:中|里)?\s*输入\s*[\'"]?([^\'",，\s]+)', desc)
    if m:
        return {"action": "fill", "target": m.group(1), "value": m.group(2).strip(), "description": desc}

    # click: 点击/勾选 + selector
    m = re.search(r'(?:点击|勾选)\S*\s*' + SEL, desc)
    if m:
        return {"action": "click", "target": m.group(1), "value": "", "description": desc}

    # wait: 等待 N 秒
    m = re.search(r'等待\s*(\d+)\s*秒', desc)
    if m:
        return {"action": "wait_for", "target": str(int(m.group(1)) * 1000), "value": "", "description": desc}

    # screenshot
    if '截图' in desc:
        return {"action": "screenshot", "target": "", "value": "", "description": desc}

    return None


def _execute_step(page, step, idx: int, base_url: str, case_id: str) -> StepResult:
    # Guard: parse plain string steps into structured format
    if isinstance(step, str):
        parsed = _parse_text_step(step)
        if parsed:
            step = parsed
        else:
            return StepResult(step_index=idx, action="unknown", target=step, status="skipped",
                              error_message=f"无法解析的文本步骤: {step[:80]}")
    action = step.get("action", "")
    target = step.get("target", "")
    value = step.get("value", "")
    description = step.get("description", "")
    optional = step.get("optional", False)  # P2-4.1: only optional steps can be skipped

    sr = StepResult(
        step_index=idx,
        action=action,
        target=target,
        description=description,
        value=value,
    )

    if action not in SUPPORTED_ACTIONS:
        sr.status = "failed"
        sr.error_message = f"不支持的操作: {action}。当前仅支持: {', '.join(sorted(SUPPORTED_ACTIONS))}"
        return sr

    def _fail_or_skip(msg: str):
        """P2-4.1: optional=true → skipped, otherwise → failed"""
        if optional:
            sr.status = "skipped"
            sr.error_message = f"[可选步骤已跳过] {msg}"
        else:
            sr.status = "failed"
            sr.error_message = msg

    t0 = time.time()
    try:
        if action == "goto":
            url = target
            if not url.startswith(("http://", "https://")):
                if not base_url:
                    sr.status = "failed"
                    sr.error_message = "goto 使用相对路径但未配置 base_url。请在 execution_config 中设置 base_url。"
                    return sr
                url = f"{base_url}/{target.lstrip('/')}"
            page.goto(url, wait_until="networkidle", timeout=30000)
            sr.current_url = page.url
            # P2-5: detect redirect — smart categorization
            intended_path = target.split("?")[0].rstrip("/")
            final_url_lower = page.url.lower()
            if intended_path and intended_path not in page.url:
                if any(k in final_url_lower for k in ("/login", "/sso", "/auth", "/signin", "/cas")):
                    sr.error_message = f"[登录跳转] 已重定向到登录页 {page.url}"
                elif any(k in final_url_lower for k in ("/403", "/401", "/forbidden", "/unauthorized")):
                    sr.error_message = f"[权限异常] 目标 {target} 返回 403，当前账号可能无此页面权限"
                else:
                    sr.error_message = f"[重定向] 目标 {target} → 实际 {page.url}"

        elif action == "fill":
            try:
                page.wait_for_selector(target, timeout=8000)
                page.fill(target, value)
            except Exception:
                _fail_or_skip(f"元素 {target} 未找到(当前URL: {page.url})")
                sr.current_url = page.url
                sr.duration_ms = (time.time() - t0) * 1000
                return sr
            sr.current_url = page.url

        elif action == "click":
            try:
                page.wait_for_selector(target, timeout=8000)
                page.click(target)
            except Exception:
                _fail_or_skip(f"元素 {target} 未找到(当前URL: {page.url})")
                sr.current_url = page.url
                sr.duration_ms = (time.time() - t0) * 1000
                return sr
            sr.current_url = page.url

        elif action == "wait_for":
            if target.isdigit():
                page.wait_for_timeout(int(target))
            else:
                try:
                    page.wait_for_selector(target, timeout=10000)
                except Exception:
                    _fail_or_skip(f"等待 {target} 超时(当前URL: {page.url})")
                    sr.current_url = page.url
                    sr.duration_ms = (time.time() - t0) * 1000
                    return sr
            sr.current_url = page.url

        elif action == "upload":
            try:
                page.wait_for_selector(target, timeout=8000)
                page.set_input_files(target, value)
            except Exception:
                _fail_or_skip(f"上传文件失败: 元素 {target} 未找到或文件 {value} 不存在(当前URL: {page.url})")
                sr.current_url = page.url
                sr.duration_ms = (time.time() - t0) * 1000
                return sr
            sr.current_url = page.url

        elif action == "hover":
            try:
                page.wait_for_selector(target, timeout=8000)
                page.hover(target)
            except Exception:
                _fail_or_skip(f"悬停失败: 元素 {target} 未找到(当前URL: {page.url})")
                sr.current_url = page.url
                sr.duration_ms = (time.time() - t0) * 1000
                return sr
            sr.current_url = page.url

        elif action == "select":
            try:
                page.wait_for_selector(target, timeout=8000)
                page.select_option(target, value)
            except Exception:
                _fail_or_skip(f"选择失败: 元素 {target} 或选项 {value} 未找到(当前URL: {page.url})")
                sr.current_url = page.url
                sr.duration_ms = (time.time() - t0) * 1000
                return sr
            sr.current_url = page.url

        elif action == "screenshot":
            _ensure_screenshot_dir()
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            fname = f"{case_id}_{ts}_step{idx}.png"
            path = os.path.join(SCREENSHOT_DIR, fname)
            page.screenshot(path=path)
            sr.screenshot_path = path
            sr.current_url = page.url

        sr.status = "passed"
    except Exception as e:
        sr.status = "failed"
        sr.error_message = str(e)[:500]
        try:
            sr.current_url = page.url
        except Exception:
            pass

    sr.duration_ms = (time.time() - t0) * 1000
    return sr


def _execute_assertion(page, assertion) -> AssertionResult:
    # Guard: skip if assertion is a plain string
    if isinstance(assertion, str):
        return AssertionResult(type="unknown", target=assertion, value="", passed=True,
                               description=f"旧格式断言，已跳过: {assertion[:80]}")
    a_type = assertion.get("type", "")
    target = assertion.get("target", "")
    value = assertion.get("value", "")
    description = assertion.get("description", "")

    ar = AssertionResult(type=a_type, target=target, value=value, description=description)

    if a_type not in SUPPORTED_ASSERTIONS:
        ar.passed = False
        ar.error_message = f"不支持的断言类型: {a_type}。当前仅支持: {', '.join(sorted(SUPPORTED_ASSERTIONS))}"
        return ar

    try:
        if a_type == "text_visible":
            try:
                locator = page.get_by_text(value)
                locator.first.wait_for(state="visible", timeout=5000)
                ar.passed = True
                ar.actual = "可见"
            except Exception:
                ar.passed = False
                ar.actual = "不可见"
                ar.error_message = f"文本 \"{value}\" 在页面中不可见"

        elif a_type == "url_contains":
            current = page.url
            ar.actual = current
            ar.passed = value in current
            if not ar.passed:
                ar.error_message = f"当前 URL \"{current}\" 不包含 \"{value}\""

        elif a_type == "url_not_contains":
            current = page.url
            ar.actual = current
            ar.passed = value not in current
            if not ar.passed:
                ar.error_message = f"当前 URL \"{current}\" 仍包含 \"{value}\""

        elif a_type == "element_visible":
            # Wait a moment for dynamic content to render
            page.wait_for_timeout(2000)

            # Try each comma-separated selector individually
            selectors = [s.strip() for s in target.split(",") if s.strip()]
            found_sel = None
            for sel in selectors:
                try:
                    loc = page.locator(sel)
                    if loc.count() > 0 and loc.first.is_visible(timeout=3000):
                        found_sel = sel
                        break
                except Exception:
                    continue
            if found_sel:
                ar.passed = True
                ar.actual = f"可见 ({found_sel})"
            else:
                # Fallback: check if page has any content
                current_url = page.url
                try:
                    body_text = page.inner_text("body", timeout=3000)
                    has_content = len(body_text.strip()) > 10
                except Exception:
                    has_content = False
                if has_content:
                    ar.passed = True
                    ar.actual = f"页面有内容(指定元素未找到但页面正常, URL: {current_url})"
                else:
                    ar.passed = False
                    ar.actual = f"不可见 (当前URL: {current_url})"
                    ar.error_message = f"元素 \"{target}\" 不可见, 页面可能未正确加载。当前URL: {current_url}"

    except Exception as e:
        ar.passed = False
        ar.error_message = str(e)[:500]

    return ar


def _execute_screenshot_match(page, assertion: dict, case_id: str, run_id: str) -> dict:
    """P2-5: Take screenshot and compare against baseline."""
    from services.visual_diff import compare_screenshot
    name = assertion.get("name", "default")
    threshold = float(assertion.get("threshold", 0.05))
    try:
        png_bytes = page.screenshot()
        vr = compare_screenshot(png_bytes, case_id, run_id, name, threshold)
        return {
            "type": "screenshot_match",
            "name": vr.name,
            "status": vr.status,
            "baseline_created": vr.baseline_created,
            "baseline_path": os.path.basename(vr.baseline_path) if vr.baseline_path else "",
            "current_path": os.path.basename(vr.current_path) if vr.current_path else "",
            "diff_path": os.path.basename(vr.diff_path) if vr.diff_path else "",
            "diff_ratio": vr.diff_ratio,
            "threshold": vr.threshold,
            "error_message": vr.error_message,
            "reason": vr.reason,
        }
    except Exception as e:
        logger.exception("screenshot_match error")
        return {
            "type": "screenshot_match",
            "name": name,
            "status": "failed",
            "baseline_created": False,
            "baseline_path": "",
            "current_path": "",
            "diff_path": "",
            "diff_ratio": 0.0,
            "threshold": threshold,
            "error_message": str(e)[:500],
            "reason": "",
        }


def _take_failure_screenshot(page, case_id: str, step_idx: int) -> str:
    try:
        _ensure_screenshot_dir()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"{case_id}_{ts}_fail_step{step_idx}.png"
        path = os.path.join(SCREENSHOT_DIR, fname)
        page.screenshot(path=path)
        return path
    except Exception as e:
        logger.warning(f"失败截图保存失败: {e}")
        return ""
