"""
视觉测试企业级 Phase 4.1 回归：Webhook 通知。

覆盖：
  W1  事件投递：baseline.created / diff.failed / diff.passed / baseline.approved /
                config_updated / deleted 都能被 _test_sink 收到（订阅时）
  W2  默认订阅策略：visual.diff.passed 默认不订阅
  W3  白名单订阅：VISUAL_WEBHOOK_EVENTS 仅订阅指定事件
  W4  HMAC 签名：设置 secret 时请求头带 X-Visual-Signature: sha256=...
  W5  无 URL 不发：未配置 URL 时不抛错，sink 不被触发（真实 path）
  W6  非 2xx 不抛主流程：模拟 _post 抛错，主流程仍正常完成
"""
import os
import sys
import io
import time
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def make_png(color=(255, 255, 255), size=(80, 60)):
    from PIL import Image
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _purge_baseline(bid):
    from services.visual_diff import _safe_baseline_path, CURRENT_DIR, DIFF_DIR
    for ext in (".png", ".meta.json"):
        try:
            p = _safe_baseline_path(bid, ext)
            if os.path.exists(p):
                os.remove(p)
            if os.path.exists(p + ".prev"):
                os.remove(p + ".prev")
        except Exception:
            pass
    for d in (CURRENT_DIR, DIFF_DIR):
        if os.path.isdir(d):
            for fn in os.listdir(d):
                if fn.startswith(bid + "_") or fn.startswith(bid + "."):
                    try:
                        os.remove(os.path.join(d, fn))
                    except OSError:
                        pass


def main():
    from services import visual_notifier
    from services.visual_diff import compare_screenshot, make_baseline_id
    from services.visual_baseline_service import (
        approve_baseline, update_baseline_config, delete_baseline,
    )

    passed = 0
    failed = 0

    def t(name, fn):
        nonlocal passed, failed
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

    def section(s):
        print(f"\n{'=' * 64}\n  {s}\n{'=' * 64}")

    # 用 sink 收事件
    captured = []

    def sink(event_type, payload):
        captured.append((event_type, payload))

    # ════════════════════════════════════════════════════════════════
    section("W1  全事件投递（sink 注入）")
    # ════════════════════════════════════════════════════════════════
    def test_full_lifecycle_events():
        captured.clear()
        # 强订阅所有事件（包括 diff.passed）
        os.environ["VISUAL_WEBHOOK_EVENTS"] = ",".join([
            "visual.baseline.created",
            "visual.diff.passed",
            "visual.diff.failed",
            "visual.baseline.approved",
            "visual.baseline.config_updated",
            "visual.baseline.deleted",
        ])
        visual_notifier.set_test_sink(sink)
        try:
            case = "test_wh_001"
            name = "page_a"
            bid = make_baseline_id(case, name)
            _purge_baseline(bid)

            # 1. 首跑：created
            vr1 = compare_screenshot(make_png((100, 100, 100)), case, "r1", name)
            assert vr1.status == "baseline_created"

            # 2. 相同截图：passed
            vr2 = compare_screenshot(make_png((100, 100, 100)), case, "r2", name)
            assert vr2.status == "passed", f"vr2.status={vr2.status}"

            # 3. 大幅变化：failed
            vr3 = compare_screenshot(make_png((255, 0, 0)), case, "r3", name)
            assert vr3.status == "failed"

            # 4. approve
            approve_baseline(bid, source="latest_current", by="alice", note="ok")

            # 5. update_config
            update_baseline_config(bid, threshold=0.2, by="bob")

            # 6. delete
            delete_baseline(bid, delete_currents=True, delete_diffs=True, by="carol")

            types = [e for e, _ in captured]
            expected = {
                "visual.baseline.created",
                "visual.diff.passed",
                "visual.diff.failed",
                "visual.baseline.approved",
                "visual.baseline.config_updated",
                "visual.baseline.deleted",
            }
            missing = expected - set(types)
            assert not missing, f"缺事件: {missing}, 实收: {types}"

            # 检查 payload 字段
            failed_evt = next(p for e, p in captured if e == "visual.diff.failed")
            assert failed_evt["data"]["case_id"] == case
            assert failed_evt["data"]["baseline_id"] == bid
            assert failed_evt["data"]["diff_ratio"] > 0
            assert failed_evt["source"] == "visual_testing"

            appr_evt = next(p for e, p in captured if e == "visual.baseline.approved")
            assert appr_evt["data"]["by"] == "alice"
            assert appr_evt["data"]["approve_count"] == 1

            cfg_evt = next(p for e, p in captured if e == "visual.baseline.config_updated")
            assert "threshold" in cfg_evt["data"]["changed"]
            assert cfg_evt["data"]["threshold"] == 0.2
        finally:
            visual_notifier.set_test_sink(None)
            os.environ.pop("VISUAL_WEBHOOK_EVENTS", None)

    t("生命周期 6 个事件全收到", test_full_lifecycle_events)

    # ════════════════════════════════════════════════════════════════
    section("W2  默认订阅：diff.passed 不发")
    # ════════════════════════════════════════════════════════════════
    def test_default_subscription_excludes_passed():
        captured.clear()
        os.environ.pop("VISUAL_WEBHOOK_EVENTS", None)   # 走默认
        visual_notifier.set_test_sink(sink)
        try:
            case = "test_wh_002"
            name = "page_default"
            bid = make_baseline_id(case, name)
            _purge_baseline(bid)
            compare_screenshot(make_png(), case, "r1", name)   # baseline_created 应发
            compare_screenshot(make_png(), case, "r2", name)   # passed 不发
            compare_screenshot(make_png((10, 200, 30)), case, "r3", name)   # failed 应发
            delete_baseline(bid, delete_currents=True, delete_diffs=True)

            types = [e for e, _ in captured]
            assert "visual.baseline.created" in types
            assert "visual.diff.failed" in types
            assert "visual.diff.passed" not in types, f"默认不应订阅 passed，但收到: {types}"
        finally:
            visual_notifier.set_test_sink(None)

    t("默认订阅排除 visual.diff.passed", test_default_subscription_excludes_passed)

    # ════════════════════════════════════════════════════════════════
    section("W3  白名单订阅")
    # ════════════════════════════════════════════════════════════════
    def test_whitelist_subscription():
        captured.clear()
        os.environ["VISUAL_WEBHOOK_EVENTS"] = "visual.baseline.approved"
        visual_notifier.set_test_sink(sink)
        try:
            case = "test_wh_003"
            name = "page_wl"
            bid = make_baseline_id(case, name)
            _purge_baseline(bid)
            compare_screenshot(make_png(), case, "r1", name)   # created 不在白名单
            approve_baseline(bid, source="latest_current", by="x")
            delete_baseline(bid, delete_currents=True, delete_diffs=True)

            types = [e for e, _ in captured]
            assert types == ["visual.baseline.approved"], f"白名单应只放行 approved, 实收 {types}"
        finally:
            visual_notifier.set_test_sink(None)
            os.environ.pop("VISUAL_WEBHOOK_EVENTS", None)

    t("VISUAL_WEBHOOK_EVENTS 白名单生效", test_whitelist_subscription)

    # ════════════════════════════════════════════════════════════════
    section("W4  HMAC 签名")
    # ════════════════════════════════════════════════════════════════
    def test_hmac_signature():
        # 直接走 _send_sync（同步），mock _post 抓取 headers
        os.environ["VISUAL_WEBHOOK_URL"] = "http://127.0.0.1:65535/hook"
        os.environ["VISUAL_WEBHOOK_SECRET"] = "topsecret"
        captured_headers = {}

        def fake_post(url, body, headers, timeout):
            captured_headers.update(headers)
            captured_headers["__body__"] = body
            return 200

        orig_post = visual_notifier._post
        visual_notifier._post = fake_post
        try:
            visual_notifier._send_sync("visual.diff.failed", {
                "event": "visual.diff.failed", "data": {"x": 1},
            })
            sig = captured_headers.get("X-Visual-Signature", "")
            assert sig.startswith("sha256="), f"未签名: {captured_headers}"
            # 重新算签名验证
            import hmac, hashlib
            mac = hmac.new(b"topsecret", captured_headers["__body__"], hashlib.sha256)
            expected = f"sha256={mac.hexdigest()}"
            assert sig == expected, f"签名不匹配: got {sig} vs {expected}"
            assert captured_headers.get("X-Visual-Event") == "visual.diff.failed"
        finally:
            visual_notifier._post = orig_post
            os.environ.pop("VISUAL_WEBHOOK_URL", None)
            os.environ.pop("VISUAL_WEBHOOK_SECRET", None)

    t("HMAC-SHA256 签名头", test_hmac_signature)

    # ════════════════════════════════════════════════════════════════
    section("W5  无 URL 不发")
    # ════════════════════════════════════════════════════════════════
    def test_no_url_silent():
        os.environ.pop("VISUAL_WEBHOOK_URL", None)
        visual_notifier.set_test_sink(None)   # 真实路径
        # 直接 send_event 不应抛错
        visual_notifier.send_event("visual.diff.failed", {"test": True})
        # 不抛即通过

    t("VISUAL_WEBHOOK_URL 未设 → 静默跳过", test_no_url_silent)

    # ════════════════════════════════════════════════════════════════
    section("W6  HTTP 失败不影响主流程")
    # ════════════════════════════════════════════════════════════════
    def test_http_failure_swallowed():
        os.environ["VISUAL_WEBHOOK_URL"] = "http://127.0.0.1:65535/hook"

        def bad_post(*a, **kw):
            raise OSError("connect refused (mock)")

        orig_post = visual_notifier._post
        visual_notifier._post = bad_post
        visual_notifier.set_test_sink(None)
        try:
            # 走完整异步路径：起后台线程 → 抛错 → 不影响调用方
            case = "test_wh_004"
            name = "page_err"
            bid = make_baseline_id(case, name)
            _purge_baseline(bid)
            vr = compare_screenshot(make_png(), case, "r1", name)
            assert vr.status == "baseline_created"
            time.sleep(0.5)   # 给后台线程一点时间
            delete_baseline(bid, delete_currents=True, delete_diffs=True)
        finally:
            visual_notifier._post = orig_post
            os.environ.pop("VISUAL_WEBHOOK_URL", None)

    t("HTTP 失败被吞，主流程不抛", test_http_failure_swallowed)

    # ════════════════════════════════════════════════════════════════
    print()
    print("=" * 64)
    print(f"  结果: {passed} passed, {failed} failed")
    print("=" * 64)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
