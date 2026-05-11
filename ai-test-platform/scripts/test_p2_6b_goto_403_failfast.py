"""
P2-6B.1 回归：goto 遇到 403/401/forbidden 必须 fail-fast。

背景：之前 _execute_step() 中 goto 检测到 /403 重定向时只设了 error_message，
未设 sr.status，导致代码继续走到 sr.status = "passed"，造成 step 假通过 + 后续步骤连环莫名失败。

本测试通过 mock 一个最小 Playwright Page/Frame 接口，验证修复后的行为：
  - goto /list 被服务端重定向到 /403 → sr.status == "failed"
  - 错误消息包含 [权限异常] 关键字
  - sr.duration_ms 已设
  - 登录跳转 /login 仍保持 warning（不 fail，向后兼容）
  - 普通 redirect 仍保持 warning（不 fail）
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

passed = 0
failed = 0


def t(name, fn):
    global passed, failed
    print(f"  [{name}] ", end="", flush=True)
    try:
        fn()
        passed += 1
        print("PASS")
    except AssertionError as e:
        failed += 1
        print(f"FAIL: {e}")
    except Exception as e:
        failed += 1
        import traceback
        traceback.print_exc()
        print(f"ERROR: {e}")


class FakeFrame:
    def __init__(self, page):
        self._page = page

    def wait_for_selector(self, *a, **k):
        return None

    def fill(self, *a, **k):
        pass

    def click(self, *a, **k):
        pass


class FakePage:
    def __init__(self, redirect_to=None):
        self._url = "https://example.com/"
        self._redirect_to = redirect_to

    @property
    def url(self):
        return self._url

    def goto(self, url, **kwargs):
        # 模拟服务端重定向
        if self._redirect_to:
            self._url = self._redirect_to
        else:
            self._url = url

    def on(self, *a, **k):
        pass


def make_ctx(redirect_to=None):
    page = FakePage(redirect_to=redirect_to)
    frame = FakeFrame(page)
    return {"page": page, "context": None, "active_frame": frame}


# ════════════════════════════════════════════════════════════════
print("=" * 64)
print("  P2-6B.1  goto 403 fail-fast 回归")
print("=" * 64)


def test_goto_403_fails():
    """目标 /list 被重定向到 /403 → status=failed + [权限异常] 消息"""
    from services.playwright_engine import _execute_step
    ctx = make_ctx(redirect_to="https://example.com/403")
    sr = _execute_step(
        ctx,
        {"action": "goto", "target": "/list", "value": ""},
        idx=0,
        base_url="https://example.com",
        case_id="tc_perm_test",
    )
    assert sr.status == "failed", f"应当 failed 但 status={sr.status}"
    assert "[权限异常]" in (sr.error_message or ""), f"消息应包含 [权限异常]: {sr.error_message}"
    assert sr.duration_ms >= 0, "duration_ms 应已设置（>=0）"


def test_goto_401_fails():
    """重定向到 /401/unauthorized 也应当 fail"""
    from services.playwright_engine import _execute_step
    ctx = make_ctx(redirect_to="https://example.com/401/unauthorized")
    sr = _execute_step(
        ctx,
        {"action": "goto", "target": "/admin", "value": ""},
        idx=0,
        base_url="https://example.com",
        case_id="tc_perm_test",
    )
    assert sr.status == "failed"
    assert "[权限异常]" in (sr.error_message or "")


def test_goto_forbidden_path_fails():
    """重定向到 /forbidden 也应 fail"""
    from services.playwright_engine import _execute_step
    ctx = make_ctx(redirect_to="https://example.com/forbidden")
    sr = _execute_step(
        ctx,
        {"action": "goto", "target": "/admin", "value": ""},
        idx=0,
        base_url="https://example.com",
        case_id="tc_perm_test",
    )
    assert sr.status == "failed"


def test_goto_login_redirect_still_warns_only():
    """重定向到 /login → 仍是 warning（status=passed），向后兼容"""
    from services.playwright_engine import _execute_step
    # NOTE: target=/admin 而不是 /list，避免 ?from=/admin 让 query 含路径绕开检测
    ctx = make_ctx(redirect_to="https://example.com/sso/login")
    sr = _execute_step(
        ctx,
        {"action": "goto", "target": "/admin", "value": ""},
        idx=0,
        base_url="https://example.com",
        case_id="tc_login_redir_test",
    )
    assert sr.status == "passed", f"登录跳转应保持 passed 但 status={sr.status}, err={sr.error_message}"
    assert "[登录跳转]" in (sr.error_message or ""), f"消息应含 [登录跳转]: {sr.error_message!r}"


def test_goto_generic_redirect_still_warns_only():
    """重定向到普通页 → 仍是 warning"""
    from services.playwright_engine import _execute_step
    ctx = make_ctx(redirect_to="https://example.com/dashboard")
    sr = _execute_step(
        ctx,
        {"action": "goto", "target": "/list", "value": ""},
        idx=0,
        base_url="https://example.com",
        case_id="tc_redir_test",
    )
    assert sr.status == "passed"
    assert "[重定向]" in (sr.error_message or "")


def test_goto_normal_passes():
    """无重定向 → 正常 passed，无 error_message"""
    from services.playwright_engine import _execute_step
    ctx = make_ctx(redirect_to="https://example.com/list")
    sr = _execute_step(
        ctx,
        {"action": "goto", "target": "/list", "value": ""},
        idx=0,
        base_url="https://example.com",
        case_id="tc_ok_test",
    )
    assert sr.status == "passed"
    assert not sr.error_message, f"正常 goto 不应有 error_message: {sr.error_message}"


t("goto /list 被重定向到 /403 → failed", test_goto_403_fails)
t("goto 被重定向到 /401 → failed", test_goto_401_fails)
t("goto 被重定向到 /forbidden → failed", test_goto_forbidden_path_fails)
t("goto 被重定向到 /login → 仍 passed (兼容)", test_goto_login_redirect_still_warns_only)
t("goto 普通 redirect → 仍 passed (兼容)", test_goto_generic_redirect_still_warns_only)
t("goto 无 redirect → 正常 passed", test_goto_normal_passes)

print()
print("=" * 64)
print(f"  结果: {passed} passed, {failed} failed")
print("=" * 64)
sys.exit(0 if failed == 0 else 1)
