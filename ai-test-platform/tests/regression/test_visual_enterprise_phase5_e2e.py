"""
视觉测试企业级 Phase 5 — e2e 集成测试。

不再 mock：起真实 Playwright chromium 跑 4 期所有改造的端到端链路。
覆盖：
  E1  命名空间自动注入：execution_config 提供 env/branch + page.viewport_size 兜底
      → baseline_id 含 @env@viewport@branch
  E2  selector mask 真实 bbox 解析：HTML 含 .timestamp 文本，建基线后改时间戳
       不带 mask → failed；加 selector mask → passed
  E3  selector 不可见容错：mask 中包含一个不存在的 selector，整体仍正常工作
  E4  Webhook 全链路：sink 收到 baseline.created → diff.failed → diff.passed →
       baseline.config_updated 的完整序列

依赖：
  pip install playwright
  python -m playwright install chromium
"""
import os
import sys
import time
import io

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


HTML_TEMPLATE = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>e2e</title>
<style>
  body {{ margin: 0; font-family: sans-serif; background: #fff; }}
  .header {{ background: #2563eb; color: #fff; padding: 16px; }}
  .content {{ padding: 24px; font-size: 18px; color: #111; }}
  .timestamp {{
    position: fixed; top: 0; right: 0;
    width: 320px; height: 96px;
    background: {bg};
    color: #fff;
    font-family: monospace; font-size: 28px; font-weight: bold;
    display: flex; align-items: center; justify-content: center;
  }}
  .footer {{ padding: 12px 24px; color: #6b7280; font-size: 12px; border-top: 1px solid #e5e7eb; }}
</style></head>
<body>
  <div class="header">订单管理系统</div>
  <div class="content">
    <h2>订单 #12345</h2>
    <p>客户：张三　金额：￥1,299.00　状态：待发货</p>
    <p>创建时间：2026-01-01 10:30:00</p>
  </div>
  <div class="timestamp">{ts}</div>
  <div class="footer">© 2026 Demo Inc.</div>
</body></html>"""


def _purge(bid):
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
    from playwright.sync_api import sync_playwright
    from services.playwright_engine import _execute_screenshot_match
    from services.visual_diff import make_baseline_id, read_meta
    from services.visual_baseline_service import update_baseline_config, delete_baseline
    from services import visual_notifier

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

    print("正在启动 chromium…", flush=True)
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True)
    try:
        # 用一个稍微特殊的 viewport，便于断言不同于默认
        context = browser.new_context(viewport={"width": 1024, "height": 720})
        page = context.new_page()

        captured = []

        def sink(event_type, payload):
            captured.append((event_type, payload))

        # 强订阅所有事件，便于断言
        os.environ["VISUAL_WEBHOOK_EVENTS"] = ",".join([
            "visual.baseline.created",
            "visual.diff.passed",
            "visual.diff.failed",
            "visual.baseline.approved",
            "visual.baseline.config_updated",
            "visual.baseline.deleted",
        ])
        visual_notifier.set_test_sink(sink)

        case_id = "test_e2e_001"
        name = "order_page"

        # 命名空间：env=prod, branch=feature_x, viewport 由 page 兜底（=1024x720）
        execution_config = {
            "visual_env": "prod",
            "visual_branch": "feature_x",
        }

        bid = make_baseline_id(case_id, name,
                               env="prod", viewport="1024x720", branch="feature_x")
        _purge(bid)

        try:
            # ════════════════════════════════════════════════════════════
            section("E1  命名空间自动注入 + 真截图首跑建基线")
            # ════════════════════════════════════════════════════════════
            def test_first_run_creates_namespaced_baseline():
                page.set_content(HTML_TEMPLATE.format(ts="10:00:00", bg="#f59e0b"))
                page.wait_for_load_state("domcontentloaded")
                ar = _execute_screenshot_match(
                    page,
                    {"type": "screenshot_match", "name": name, "threshold": 0.001},
                    case_id, "run-1", execution_config,
                )
                assert ar["status"] == "baseline_created", f"status={ar['status']}"
                # baseline_id 必须包含三段命名空间
                assert ar["baseline_id"] == bid, f"bid={ar['baseline_id']}, want {bid}"
                assert ar["env"] == "prod"
                assert ar["viewport"] == "1024x720"
                assert ar["branch"] == "feature_x"

                # sidecar 落盘
                meta = read_meta(bid)
                assert meta.get("env") == "prod"
                assert meta.get("viewport") == "1024x720"
                assert meta.get("branch") == "feature_x"

            t("env/branch + page.viewport_size 兜底 → bid 含三段命名空间", test_first_run_creates_namespaced_baseline)

            # ════════════════════════════════════════════════════════════
            section("E2  selector mask 真实 bbox 解析（含 padding）")
            # ════════════════════════════════════════════════════════════
            def test_no_mask_dynamic_change_fails():
                # 改时间戳 + 改背景色：differences 集中在 .timestamp 区域
                page.set_content(HTML_TEMPLATE.format(ts="23:59:59 X", bg="#dc2626"))
                page.wait_for_load_state("domcontentloaded")
                ar = _execute_screenshot_match(
                    page,
                    {"type": "screenshot_match", "name": name, "threshold": 0.001},
                    case_id, "run-2", execution_config,
                )
                assert ar["status"] == "failed", f"status={ar['status']}, ratio={ar['diff_ratio']}"
                assert ar["diff_ratio"] > 0

            def test_selector_mask_resolves_bbox_and_passes():
                # 配置 selector mask（持久化到 sidecar）
                update_baseline_config(bid, masks=[
                    {"type": "selector", "selector": ".timestamp", "padding": 6},
                    # 同时加一个不存在的 selector，验证容错
                    {"type": "selector", "selector": ".does_not_exist_xx"},
                ], by="e2e", note="e2e mask")
                meta = read_meta(bid)
                assert len(meta["masks"]) == 2

                # 再变时间戳 + 再换背景：因 selector mask 屏蔽 → passed
                page.set_content(HTML_TEMPLATE.format(ts="00:00:01 Y", bg="#10b981"))
                page.wait_for_load_state("domcontentloaded")
                ar = _execute_screenshot_match(
                    page,
                    {"type": "screenshot_match", "name": name, "threshold": 0.001},
                    case_id, "run-3", execution_config,
                )
                assert ar["status"] == "passed", (
                    f"selector mask 应屏蔽时钟变化但 status={ar['status']} "
                    f"ratio={ar['diff_ratio']} masks_applied={ar['masks_applied']}"
                )
                assert ar["masks_applied"] >= 1, f"应至少应用 1 个 mask，实际 {ar['masks_applied']}"

            t("无 mask 改时间戳 → failed", test_no_mask_dynamic_change_fails)
            t("配 selector mask（含不可见 selector 容错） → passed", test_selector_mask_resolves_bbox_and_passes)

            # ════════════════════════════════════════════════════════════
            section("E3  Webhook 全链路（sink 验证事件序列）")
            # ════════════════════════════════════════════════════════════
            def test_webhook_event_sequence():
                # 此时 captured 应已收到：
                #   baseline.created (run-1) → diff.failed (run-2) → diff.passed (run-3)
                #   + baseline.config_updated（在 E2 配 mask 时触发）
                types = [e for e, _ in captured]
                assert "visual.baseline.created" in types, f"types={types}"
                assert "visual.diff.failed" in types
                assert "visual.diff.passed" in types
                assert "visual.baseline.config_updated" in types

                # diff.failed 事件 payload 应包含命名空间字段 + 实际 diff_ratio
                failed_evt = next(p for e, p in captured if e == "visual.diff.failed")
                assert failed_evt["data"]["env"] == "prod"
                assert failed_evt["data"]["viewport"] == "1024x720"
                assert failed_evt["data"]["branch"] == "feature_x"
                assert failed_evt["data"]["diff_ratio"] > 0

            t("baseline.created → diff.failed → diff.passed → config_updated 全收到", test_webhook_event_sequence)

            # ════════════════════════════════════════════════════════════
            section("E4  无视口配置时也能工作（page.viewport_size 兜底）")
            # ════════════════════════════════════════════════════════════
            def test_viewport_fallback_to_page():
                # 切到不同 viewport 验证兜底
                page2 = browser.new_context(viewport={"width": 800, "height": 600}).new_page()
                try:
                    page2.set_content(HTML_TEMPLATE.format(ts="01:23:45", bg="#f59e0b"))
                    page2.wait_for_load_state("domcontentloaded")
                    case2 = "test_e2e_002_vp"
                    ar = _execute_screenshot_match(
                        page2,
                        {"type": "screenshot_match", "name": "page_b", "threshold": 0.001},
                        case2, "run-1", {"visual_env": "default"},   # 故意不传 viewport
                    )
                    # baseline_id 应自动带上 800x600
                    assert "800x600" in ar["baseline_id"], f"bid={ar['baseline_id']}, 应包含 800x600"
                    assert ar["viewport"] == "800x600"
                    # 清理
                    delete_baseline(ar["baseline_id"], delete_currents=True, delete_diffs=True, by="e2e")
                finally:
                    page2.context.close()

            t("execution_config 不传 viewport → 自动从 page.viewport_size 兜底", test_viewport_fallback_to_page)

        finally:
            visual_notifier.set_test_sink(None)
            os.environ.pop("VISUAL_WEBHOOK_EVENTS", None)
            try:
                delete_baseline(bid, delete_currents=True, delete_diffs=True, by="e2e")
            except Exception:
                pass
            try:
                context.close()
            except Exception:
                pass
    finally:
        try:
            browser.close()
        except Exception:
            pass
        pw.stop()

    print()
    print("=" * 64)
    print(f"  结果: {passed} passed, {failed} failed")
    print("=" * 64)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
