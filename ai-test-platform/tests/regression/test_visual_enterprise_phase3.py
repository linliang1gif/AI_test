"""
视觉测试企业级 Phase 3 回归：写并发文件锁。

覆盖：
  L1  _FileLock：互斥语义（拿到锁的线程独占临界区）
  L2  _FileLock：锁释放后下一位可立即取得
  L3  _FileLock：超时抛 TimeoutError
  L4  _FileLock：stale lock 自愈（>60s）
  L5  原子写：临时文件 + os.replace（中断不会留下半截 JSON）

  C1  线程并发 approve：N 次并发批准 → history 长度 == N，approve_count == N
  C2  线程并发 update_config：N 次并发改 threshold → 不抛错，history 长度 == N
  C3  线程并发首跑 compare_screenshot：仅一次 baseline_created

  P1  进程并发 approve：4 进程并发批准同一基线 → history 长度 == 4，approve_count == 4

NOTE: Windows 下 multiprocessing 用 spawn，子进程会重新 import 本脚本，
      所以测试主体必须放在 `if __name__ == "__main__":` 保护下。
"""
import os
import sys
import time
import io
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Process, Queue

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# ────────── 子进程 worker（顶层定义，spawn 必需） ──────────
def _proc_approve_worker(bid, idx, q):
    """子进程入口：approve_baseline 一次。"""
    import sys, os
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if here not in sys.path:
        sys.path.insert(0, here)
    try:
        from services.visual_baseline_service import approve_baseline
        approve_baseline(bid, source="latest_current", by=f"p{idx}", note=f"proc-{idx}")
        q.put(("ok", idx))
    except Exception as e:
        q.put(("err", idx, repr(e)))


# ────────── 工具 ──────────
def make_png(color=(255, 255, 255), size=(80, 60)):
    from PIL import Image
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def main():
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
    section("L1-L5  文件锁基础语义")
    # ════════════════════════════════════════════════════════════════
    def test_lock_mutex():
        from services.visual_diff import _FileLock
        lock_path = os.path.join(ROOT, "data", "artifacts", "visual", "meta", ".test_mutex.lock")
        if os.path.exists(lock_path):
            os.remove(lock_path)
        overlap = []
        in_critical = [0]

        def worker():
            with _FileLock(lock_path, timeout=5.0):
                in_critical[0] += 1
                overlap.append(in_critical[0])
                time.sleep(0.05)
                in_critical[0] -= 1

        with ThreadPoolExecutor(max_workers=8) as ex:
            list(ex.map(lambda _: worker(), range(8)))
        assert max(overlap) == 1, f"互斥失败：临界区重叠 {max(overlap)}"
        assert len(overlap) == 8

    def test_lock_release_and_reacquire():
        from services.visual_diff import _FileLock
        lock_path = os.path.join(ROOT, "data", "artifacts", "visual", "meta", ".test_release.lock")
        if os.path.exists(lock_path):
            os.remove(lock_path)
        with _FileLock(lock_path, timeout=2.0):
            pass
        with _FileLock(lock_path, timeout=0.5):
            pass

    def test_lock_timeout():
        from services.visual_diff import _FileLock
        lock_path = os.path.join(ROOT, "data", "artifacts", "visual", "meta", ".test_timeout.lock")
        if os.path.exists(lock_path):
            os.remove(lock_path)
        held = _FileLock(lock_path, timeout=2.0)
        held.__enter__()
        try:
            try:
                with _FileLock(lock_path, timeout=0.3):
                    raise AssertionError("不该拿到锁")
            except TimeoutError:
                pass
            else:
                raise AssertionError("应抛 TimeoutError")
        finally:
            held.__exit__(None, None, None)

    def test_lock_stale_self_heal():
        from services.visual_diff import _FileLock
        lock_path = os.path.join(ROOT, "data", "artifacts", "visual", "meta", ".test_stale.lock")
        os.makedirs(os.path.dirname(lock_path), exist_ok=True)
        with open(lock_path, "w") as f:
            f.write("pid=99999\n")
        old = time.time() - 120
        os.utime(lock_path, (old, old))
        with _FileLock(lock_path, timeout=2.0):
            pass

    def test_atomic_write_no_partial():
        from services.visual_diff import write_meta, read_meta, _safe_baseline_path
        from services.visual_baseline_service import delete_baseline
        from services.visual_diff import compare_screenshot, make_baseline_id
        case = "test_atomic_001"
        name = "page_a"
        compare_screenshot(make_png(), case, "r0", name)
        bid = make_baseline_id(case, name)
        write_meta(bid, {"baseline_id": bid, "stub": "ok"})
        meta_path = _safe_baseline_path(bid, ".meta.json")
        assert os.path.exists(meta_path)
        assert not os.path.exists(meta_path + ".tmp"), ".tmp 残留"
        assert read_meta(bid)["stub"] == "ok"
        delete_baseline(bid, delete_currents=True, delete_diffs=True)

    t("互斥（8 线程不重叠）", test_lock_mutex)
    t("释放后可立即重获", test_lock_release_and_reacquire)
    t("超时抛 TimeoutError", test_lock_timeout)
    t("stale lock (>60s) 自愈", test_lock_stale_self_heal)
    t("原子写：无 .tmp 残留", test_atomic_write_no_partial)

    # ════════════════════════════════════════════════════════════════
    section("C1-C3  线程并发：sidecar 不丢写")
    # ════════════════════════════════════════════════════════════════
    def _purge_baseline(bid: str):
        """删除 baseline + meta + 同 bid 的 currents（防上次失败残留污染）。"""
        from services.visual_diff import _safe_baseline_path, CURRENT_DIR
        for ext in (".png", ".meta.json"):
            try:
                p = _safe_baseline_path(bid, ext)
                if os.path.exists(p):
                    os.remove(p)
                if os.path.exists(p + ".prev"):
                    os.remove(p + ".prev")
            except Exception:
                pass
        if os.path.isdir(CURRENT_DIR):
            for fname in os.listdir(CURRENT_DIR):
                if fname.startswith(bid + "_") or fname.startswith(bid + "."):
                    try:
                        os.remove(os.path.join(CURRENT_DIR, fname))
                    except OSError:
                        pass

    def test_concurrent_approve():
        from services.visual_diff import compare_screenshot, make_baseline_id
        from services.visual_baseline_service import (
            approve_baseline, get_baseline_detail, delete_baseline,
        )
        case = "test_conc_appr_001"
        name = "page_x"
        bid = make_baseline_id(case, name)
        _purge_baseline(bid)
        compare_screenshot(make_png((250, 250, 250)), case, "r0", name)
        compare_screenshot(make_png((100, 200, 100)), case, "r1", name)

        N = 8
        errors = []

        def worker(i):
            try:
                approve_baseline(bid, source="latest_current", by=f"u{i}", note=f"c{i}")
            except Exception as e:
                errors.append(repr(e))

        with ThreadPoolExecutor(max_workers=N) as ex:
            list(ex.map(worker, range(N)))

        assert not errors, f"approve 抛错: {errors}"
        meta = get_baseline_detail(bid)["metadata"]
        appr = [h for h in meta.get("history", []) if h.get("event") == "approved"]
        assert len(appr) == N, f"approved {len(appr)} != {N}"
        assert int(meta["approve_count"]) == N, f"approve_count={meta['approve_count']}"
        delete_baseline(bid, delete_currents=True, delete_diffs=True)

    def test_concurrent_update_config():
        from services.visual_diff import compare_screenshot, make_baseline_id
        from services.visual_baseline_service import (
            update_baseline_config, get_baseline_detail, delete_baseline,
        )
        case = "test_conc_cfg_001"
        name = "page_y"
        bid = make_baseline_id(case, name)
        _purge_baseline(bid)
        compare_screenshot(make_png(), case, "r0", name)

        N = 8
        errors = []

        def worker(i):
            try:
                update_baseline_config(bid, threshold=0.01 * (i + 1), by=f"u{i}")
            except Exception as e:
                errors.append(repr(e))

        with ThreadPoolExecutor(max_workers=N) as ex:
            list(ex.map(worker, range(N)))

        assert not errors, f"抛错: {errors}"
        meta = get_baseline_detail(bid)["metadata"]
        cfg = [h for h in meta.get("history", []) if h.get("event") == "config_updated"]
        assert len(cfg) == N, f"config_updated {len(cfg)} != {N}"
        final = float(meta["threshold"])
        valid = {round(0.01 * (i + 1), 6) for i in range(N)}
        assert final in valid, f"final {final} not in {valid}"
        delete_baseline(bid, delete_currents=True, delete_diffs=True)

    def test_concurrent_first_run_creates_once():
        from services.visual_diff import (
            compare_screenshot, make_baseline_id, _safe_baseline_path,
        )
        from services.visual_baseline_service import delete_baseline
        case = "test_conc_first_001"
        name = "page_z"
        bid = make_baseline_id(case, name)
        # 全清理（baseline + meta + 旧 current）
        try:
            for ext in (".png", ".meta.json"):
                p = _safe_baseline_path(bid, ext)
                if os.path.exists(p):
                    os.remove(p)
            from services.visual_diff import CURRENT_DIR
            for fname in os.listdir(CURRENT_DIR):
                if fname.startswith(bid):
                    try:
                        os.remove(os.path.join(CURRENT_DIR, fname))
                    except OSError:
                        pass
        except Exception:
            pass

        N = 6
        results = []
        lock = __import__("threading").Lock()

        def worker(i):
            vr = compare_screenshot(make_png((i * 30 % 255, 200, 200)), case, f"r{i}", name)
            with lock:
                results.append(vr)

        with ThreadPoolExecutor(max_workers=N) as ex:
            list(ex.map(worker, range(N)))

        created = [r for r in results if r.baseline_created]
        statuses = [r.status for r in results]
        assert len(created) == 1, f"baseline_created 应为 1，实际 {len(created)}, 全 status={statuses}"
        delete_baseline(bid, delete_currents=True, delete_diffs=True)

    t("并发 approve 8 次 → history 不丢写", test_concurrent_approve)
    t("并发 update_config 8 次 → history 不丢写", test_concurrent_update_config)
    t("并发首跑 → baseline 只创建一次", test_concurrent_first_run_creates_once)

    # ════════════════════════════════════════════════════════════════
    section("P1  进程并发：跨进程文件锁生效")
    # ════════════════════════════════════════════════════════════════
    def test_multiprocess_approve():
        from services.visual_diff import compare_screenshot, make_baseline_id
        from services.visual_baseline_service import get_baseline_detail, delete_baseline
        case = "test_mp_appr_001"
        name = "page_mp"
        bid = make_baseline_id(case, name)
        _purge_baseline(bid)
        compare_screenshot(make_png((200, 200, 200)), case, "r0", name)
        compare_screenshot(make_png((100, 100, 100)), case, "r1", name)

        N = 4
        q = Queue()
        procs = [Process(target=_proc_approve_worker, args=(bid, i, q)) for i in range(N)]
        for p in procs:
            p.start()
        for p in procs:
            p.join(timeout=60)

        results = []
        while not q.empty():
            results.append(q.get())
        errs = [r for r in results if r[0] != "ok"]
        assert not errs, f"子进程错误: {errs}"
        assert len(results) == N, f"收到 {len(results)} 个结果，期望 {N}"

        meta = get_baseline_detail(bid)["metadata"]
        appr = [h for h in meta.get("history", []) if h.get("event") == "approved"]
        assert len(appr) == N, f"history.approved {len(appr)} != {N}"
        assert int(meta["approve_count"]) == N, f"approve_count={meta['approve_count']}"
        delete_baseline(bid, delete_currents=True, delete_diffs=True)

    t("4 进程并发 approve → 不丢写", test_multiprocess_approve)

    # ════════════════════════════════════════════════════════════════
    print()
    print("=" * 64)
    print(f"  结果: {passed} passed, {failed} failed")
    print("=" * 64)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
