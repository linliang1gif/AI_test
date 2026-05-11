"""
视觉测试企业级 Phase 7 — Webhook 重试 + 死信队列。

覆盖：
  R1  指数退避：失败 N 次后才放弃，期间记录每次 attempt 间隔
  R2  中途成功：第 K 次重试成功 → 不入 DLQ，主流程不报错
  R3  最终失败 → 写入 DLQ（含 event_type / payload / last_error / attempts）
  R4  DLQ list / get / delete 增删查
  R5  DLQ retry：成功 → resolved；失败 → attempts++ 仍留库
  R6  stats：total / unresolved / by_event_type 正确

NOTE: 加速测试用 VISUAL_WEBHOOK_BACKOFF_BASE=0 以跳过实际 sleep。
"""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def main():
    from services import visual_notifier, visual_webhook_dlq

    visual_webhook_dlq.clear_all_for_test()

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

    # ════════════════════════════════════════════════════════════════
    section("R1  指数退避：N 次失败才放弃")
    # ════════════════════════════════════════════════════════════════
    def test_retry_exhausted_then_dlq():
        os.environ["VISUAL_WEBHOOK_URL"] = "http://127.0.0.1:65535/hook"
        os.environ["VISUAL_WEBHOOK_BACKOFF_BASE"] = "0"   # 不睡
        os.environ["VISUAL_WEBHOOK_MAX_RETRIES"] = "3"
        visual_webhook_dlq.clear_all_for_test()

        attempts = []

        def always_fail(url, body, headers, timeout):
            attempts.append(time.time())
            raise IOError("simulated network error")

        orig_post = visual_notifier._post
        visual_notifier._post = always_fail
        try:
            visual_notifier._send_sync("visual.diff.failed", {"foo": "bar"})
            # 总尝试 = 1 + 3 = 4
            assert len(attempts) == 4, f"应尝试 4 次，实际 {len(attempts)}"
            # DLQ 中应有 1 条
            items = visual_webhook_dlq.list_recent(limit=10)
            assert len(items) == 1, f"DLQ 应有 1 条，实际 {len(items)}"
            it = items[0]
            assert it["event_type"] == "visual.diff.failed"
            assert it["payload"]["foo"] == "bar"
            assert it["attempts"] == 4
            assert "simulated network error" in (it["last_error"] or "")
            assert it["resolved"] is False
        finally:
            visual_notifier._post = orig_post
            os.environ.pop("VISUAL_WEBHOOK_URL", None)
            os.environ.pop("VISUAL_WEBHOOK_BACKOFF_BASE", None)
            os.environ.pop("VISUAL_WEBHOOK_MAX_RETRIES", None)

    t("4 次都失败 → 入 DLQ + 不抛错", test_retry_exhausted_then_dlq)

    # ════════════════════════════════════════════════════════════════
    section("R2  中途成功不入 DLQ")
    # ════════════════════════════════════════════════════════════════
    def test_succeeds_on_second_attempt():
        os.environ["VISUAL_WEBHOOK_URL"] = "http://127.0.0.1:65535/hook"
        os.environ["VISUAL_WEBHOOK_BACKOFF_BASE"] = "0"
        os.environ["VISUAL_WEBHOOK_MAX_RETRIES"] = "3"
        visual_webhook_dlq.clear_all_for_test()

        calls = {"n": 0}

        def flaky(url, body, headers, timeout):
            calls["n"] += 1
            if calls["n"] < 2:
                raise IOError("flaky 1st")
            return 200

        orig_post = visual_notifier._post
        visual_notifier._post = flaky
        try:
            visual_notifier._send_sync("visual.baseline.created", {"k": 1})
            assert calls["n"] == 2, f"应在第 2 次成功，实际 calls={calls['n']}"
            # DLQ 中无记录
            items = visual_webhook_dlq.list_recent(limit=10, include_resolved=True)
            assert len(items) == 0, f"DLQ 不应有记录，实际 {items}"
        finally:
            visual_notifier._post = orig_post
            os.environ.pop("VISUAL_WEBHOOK_URL", None)
            os.environ.pop("VISUAL_WEBHOOK_BACKOFF_BASE", None)
            os.environ.pop("VISUAL_WEBHOOK_MAX_RETRIES", None)

    t("第 2 次成功 → 不入 DLQ", test_succeeds_on_second_attempt)

    # ════════════════════════════════════════════════════════════════
    section("R3-R5  DLQ CRUD + retry")
    # ════════════════════════════════════════════════════════════════
    def test_dlq_list_get_delete():
        visual_webhook_dlq.clear_all_for_test()
        id1 = visual_webhook_dlq.add("visual.diff.failed", {"a": 1}, "err1", attempts=4)
        id2 = visual_webhook_dlq.add("visual.baseline.approved", {"b": 2}, "err2", attempts=4)
        assert id1 != id2

        items = visual_webhook_dlq.list_recent(limit=10)
        # 最新在前 → id2 在前
        assert [i["id"] for i in items] == [id2, id1]

        # 按 event_type 过滤
        only_failed = visual_webhook_dlq.list_recent(limit=10, event_type="visual.diff.failed")
        assert len(only_failed) == 1 and only_failed[0]["id"] == id1

        # delete
        assert visual_webhook_dlq.delete(id1) is True
        assert visual_webhook_dlq.get(id1) is None
        assert visual_webhook_dlq.get(id2) is not None

        # 删完
        visual_webhook_dlq.delete(id2)

    def test_dlq_retry_success_then_resolved():
        os.environ["VISUAL_WEBHOOK_URL"] = "http://127.0.0.1:65535/hook"
        visual_webhook_dlq.clear_all_for_test()
        idx = visual_webhook_dlq.add("visual.diff.failed", {"x": 9}, "old err", attempts=4)

        def ok_post(*a, **kw):
            return 200

        orig_post = visual_notifier._post
        visual_notifier._post = ok_post
        try:
            r = visual_notifier.retry_dead_letter(idx)
            assert r["success"] is True and r["status"] == "sent"
            after = visual_webhook_dlq.get(idx)
            assert after["resolved"] is True
            # 默认 list（未解决）应不包含
            items = visual_webhook_dlq.list_recent(limit=10)
            assert all(i["id"] != idx for i in items)
            # include_resolved 时能看到
            items_all = visual_webhook_dlq.list_recent(limit=10, include_resolved=True)
            assert any(i["id"] == idx for i in items_all)
        finally:
            visual_notifier._post = orig_post
            os.environ.pop("VISUAL_WEBHOOK_URL", None)

    def test_dlq_retry_failure_increments_attempts():
        os.environ["VISUAL_WEBHOOK_URL"] = "http://127.0.0.1:65535/hook"
        visual_webhook_dlq.clear_all_for_test()
        idx = visual_webhook_dlq.add("visual.diff.failed", {"x": 9}, "old err", attempts=4)
        before = visual_webhook_dlq.get(idx)

        def bad_post(*a, **kw):
            raise IOError("still down")

        orig_post = visual_notifier._post
        visual_notifier._post = bad_post
        try:
            r = visual_notifier.retry_dead_letter(idx)
            assert r["success"] is False and r["status"] == "failed"
            after = visual_webhook_dlq.get(idx)
            assert after["resolved"] is False
            assert after["attempts"] == before["attempts"] + 1
            assert "still down" in after["last_error"]
        finally:
            visual_notifier._post = orig_post
            os.environ.pop("VISUAL_WEBHOOK_URL", None)
            visual_webhook_dlq.delete(idx)

    t("DLQ list/filter/get/delete 基本 CRUD", test_dlq_list_get_delete)
    t("DLQ retry 成功 → resolved=true", test_dlq_retry_success_then_resolved)
    t("DLQ retry 失败 → attempts++ 留库", test_dlq_retry_failure_increments_attempts)

    # ════════════════════════════════════════════════════════════════
    section("R6  stats 聚合")
    # ════════════════════════════════════════════════════════════════
    def test_stats():
        visual_webhook_dlq.clear_all_for_test()
        visual_webhook_dlq.add("visual.diff.failed", {}, "e", attempts=4)
        visual_webhook_dlq.add("visual.diff.failed", {}, "e", attempts=4)
        visual_webhook_dlq.add("visual.baseline.approved", {}, "e", attempts=4)
        s = visual_webhook_dlq.stats()
        assert s["total"] == 3
        assert s["unresolved"] == 3
        assert s["by_event_type"].get("visual.diff.failed") == 2
        assert s["by_event_type"].get("visual.baseline.approved") == 1

        # 解决 1 条后再统计
        items = visual_webhook_dlq.list_recent(limit=10)
        visual_webhook_dlq.mark_resolved(items[0]["id"])
        s2 = visual_webhook_dlq.stats()
        assert s2["total"] == 3
        assert s2["unresolved"] == 2

        visual_webhook_dlq.clear_all_for_test()

    t("stats(total/unresolved/by_event_type) 正确", test_stats)

    print()
    print("=" * 64)
    print(f"  结果: {passed} passed, {failed} failed")
    print("=" * 64)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
