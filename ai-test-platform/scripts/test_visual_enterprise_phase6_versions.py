"""
视觉测试企业级 Phase 6 — 基线版本历史 + 回滚。

覆盖：
  V1  首次创建 → 自动归档 v1（source=created）
  V2  approve N 次 → versions 增长 + history 同步
  V3  超过保留上限自动剪枝（旧物理文件 + sidecar 条目同时删）
  V4  list_versions 返回正确顺序 + file_path 可定位
  V5  rollback：把当前基线指回旧版本，自动留 pre_rollback + 写入 source=rollback 新条目，可再 rollback 回去
  V6  rollback 不存在的 version_id → FileNotFoundError
  V7  delete_baseline 同步清理 versions/ 物理目录
  V8  版本剪枝在并发 approve 下不丢/不重复（5 线程 → 上限 == _keep_versions()）
"""
import os
import sys
import io
import time
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def make_png(color=(255, 255, 255), size=(60, 40)):
    from PIL import Image
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _purge(bid):
    from services.visual_diff import _safe_baseline_path, CURRENT_DIR, DIFF_DIR, _versions_dir_for
    import shutil
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
    vdir = _versions_dir_for(bid)
    if os.path.isdir(vdir):
        try:
            shutil.rmtree(vdir)
        except Exception:
            pass


def main():
    from services.visual_diff import (
        compare_screenshot, make_baseline_id, list_versions,
        rollback_to_version, _versions_dir_for, read_meta, _keep_versions,
    )
    from services.visual_baseline_service import (
        approve_baseline, delete_baseline, get_baseline_detail,
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

    # ════════════════════════════════════════════════════════════════
    section("V1-V2  创建 → 批准 → versions 增长")
    # ════════════════════════════════════════════════════════════════
    def test_first_run_creates_v1():
        case = "test_v6_001"
        name = "page_v1"
        bid = make_baseline_id(case, name)
        _purge(bid)
        compare_screenshot(make_png((100, 200, 100)), case, "r0", name)
        versions = list_versions(bid)
        assert len(versions) == 1, f"首次创建应有 1 个版本，实际 {len(versions)}"
        v1 = versions[0]
        assert v1["source"] == "created"
        assert v1["exists"] is True
        assert v1["file"].endswith(".png")
        delete_baseline(bid, delete_currents=True, delete_diffs=True)

    def test_approve_grows_versions():
        case = "test_v6_002"
        name = "page_grow"
        bid = make_baseline_id(case, name)
        _purge(bid)
        compare_screenshot(make_png((100, 100, 100)), case, "r0", name)
        # 制造 3 次 current（颜色每次不同），各 approve 一次
        for i in range(3):
            compare_screenshot(make_png((50 + i * 50, 100, 200)), case, f"r{i+1}", name)
            approve_baseline(bid, source="latest_current", by=f"u{i}", note=f"approve {i}")
        versions = list_versions(bid)
        # 1 (created) + 3 (approved) = 4
        assert len(versions) == 4, f"应有 4 个版本，实际 {len(versions)}"
        assert versions[0]["source"] == "created"
        approve_sources = [v["source"] for v in versions[1:]]
        assert approve_sources == ["approved", "approved", "approved"], f"sources={approve_sources}"
        # 物理文件都在
        for v in versions:
            assert v["exists"], f"版本物理文件丢失: {v}"
        delete_baseline(bid, delete_currents=True, delete_diffs=True)

    t("首次创建 → v1(source=created)", test_first_run_creates_v1)
    t("approve N 次 → versions 与 sidecar 同步增长", test_approve_grows_versions)

    # ════════════════════════════════════════════════════════════════
    section("V3-V4  保留上限自动剪枝")
    # ════════════════════════════════════════════════════════════════
    def test_prune_when_over_limit():
        # 临时把上限调小到 3
        os.environ["VISUAL_KEEP_VERSIONS"] = "3"
        try:
            assert _keep_versions() == 3
            case = "test_v6_003"
            name = "page_prune"
            bid = make_baseline_id(case, name)
            _purge(bid)
            compare_screenshot(make_png((10, 10, 10)), case, "r0", name)
            # approve 5 次 → 总计 1+5=6 个 snapshot，但保留 3 个
            for i in range(5):
                compare_screenshot(make_png((20 + i * 30, 100, 200)), case, f"r{i+1}", name)
                approve_baseline(bid, source="latest_current", by="u")
            versions = list_versions(bid)
            assert len(versions) == 3, f"应保留 3 个版本，实际 {len(versions)}"
            # 最旧应被剪：留下的应都是后期的
            sources = [v["source"] for v in versions]
            assert sources == ["approved", "approved", "approved"], f"sources={sources}（最旧 created 被剪）"
            # 物理目录里也只剩 3 个文件
            vdir = _versions_dir_for(bid)
            files = [f for f in os.listdir(vdir) if f.endswith(".png")]
            assert len(files) == 3, f"物理 png 文件应为 3，实际 {len(files)}: {files}"
            delete_baseline(bid, delete_currents=True, delete_diffs=True)
        finally:
            os.environ.pop("VISUAL_KEEP_VERSIONS", None)

    def test_list_versions_order_and_paths():
        case = "test_v6_004"
        name = "page_list"
        bid = make_baseline_id(case, name)
        _purge(bid)
        compare_screenshot(make_png(), case, "r0", name)
        compare_screenshot(make_png((255, 0, 0)), case, "r1", name)
        approve_baseline(bid, source="latest_current", by="alice", note="for test")
        versions = list_versions(bid)
        assert versions[-1]["source"] == "approved"
        assert versions[-1]["by"] == "alice"
        for v in versions:
            assert os.path.exists(v["file_path"]), f"file_path 不可访问: {v['file_path']}"
        delete_baseline(bid, delete_currents=True, delete_diffs=True)

    t("超过 _keep_versions 自动剪枝物理 + sidecar", test_prune_when_over_limit)
    t("list_versions 返回顺序与可定位 file_path", test_list_versions_order_and_paths)

    # ════════════════════════════════════════════════════════════════
    section("V5-V6  rollback 正向 + 错误处理")
    # ════════════════════════════════════════════════════════════════
    def test_rollback_restores_old_version():
        case = "test_v6_005"
        name = "page_rb"
        bid = make_baseline_id(case, name)
        _purge(bid)
        # 创建（v1=红） → approve 一次（v2=蓝）
        compare_screenshot(make_png((255, 0, 0)), case, "r0", name)
        compare_screenshot(make_png((0, 0, 255)), case, "r1", name)
        approve_baseline(bid, source="latest_current", by="bob", note="改成蓝")
        versions = list_versions(bid)
        v_red = versions[0]   # v1 = red
        v_blue_size = versions[-1]["size"]

        # 当前生效基线应是蓝色（最大 size 不一定，但 sidecar last_run_id=r1）
        meta_before = read_meta(bid)
        assert meta_before["last_run_id"] == "r1"

        # 回滚到 v1
        result = rollback_to_version(bid, v_red["id"], by="carol", note="回到红版")
        assert result["success"] is True

        # 验证：versions 应增加 2 条（pre_rollback + rollback）
        versions2 = list_versions(bid)
        assert len(versions2) == len(versions) + 2, f"versions {len(versions)} → {len(versions2)}"
        sources_after = [v["source"] for v in versions2]
        assert "pre_rollback" in sources_after
        assert sources_after[-1] == "rollback"

        # 当前生效基线现在的字节大小应等于 v_red 的大小
        from services.visual_diff import _safe_baseline_path
        bp = _safe_baseline_path(bid, ".png")
        cur_size = os.path.getsize(bp)
        assert cur_size == v_red["size"], f"回滚后 size {cur_size} 应 == v_red.size {v_red['size']}"

        # history 里有 rolled_back 事件
        meta_after = read_meta(bid)
        events = [h["event"] for h in meta_after.get("history") or []]
        assert "rolled_back" in events, f"history events={events}"

        # 再回滚到 pre_rollback（蓝色） → size 应回到 v_blue_size
        pre_rb = next(v for v in versions2 if v["source"] == "pre_rollback")
        rollback_to_version(bid, pre_rb["id"], by="carol", note="再回到蓝")
        assert os.path.getsize(bp) == v_blue_size, "二次回滚未恢复"

        delete_baseline(bid, delete_currents=True, delete_diffs=True)

    def test_rollback_invalid_version():
        case = "test_v6_006"
        name = "page_rb_err"
        bid = make_baseline_id(case, name)
        _purge(bid)
        compare_screenshot(make_png(), case, "r0", name)
        try:
            rollback_to_version(bid, "v_does_not_exist", by="x")
        except FileNotFoundError:
            pass
        else:
            raise AssertionError("应抛 FileNotFoundError")
        delete_baseline(bid, delete_currents=True, delete_diffs=True)

    t("rollback 正向 + 双向恢复", test_rollback_restores_old_version)
    t("rollback 不存在的 version_id → FileNotFoundError", test_rollback_invalid_version)

    # ════════════════════════════════════════════════════════════════
    section("V7  delete_baseline 同步清理 versions/")
    # ════════════════════════════════════════════════════════════════
    def test_delete_clears_versions():
        case = "test_v6_007"
        name = "page_del"
        bid = make_baseline_id(case, name)
        _purge(bid)
        compare_screenshot(make_png(), case, "r0", name)
        compare_screenshot(make_png((1, 2, 3)), case, "r1", name)
        approve_baseline(bid, source="latest_current", by="u")
        vdir = _versions_dir_for(bid)
        assert os.path.isdir(vdir)
        files_before = os.listdir(vdir)
        assert len(files_before) >= 2

        result = delete_baseline(bid, delete_currents=True, delete_diffs=True)
        assert result["removed"]["versions"] == len(files_before)
        assert not os.path.isdir(vdir), "versions 子目录应被删除"

    t("delete_baseline 清理 versions 物理目录", test_delete_clears_versions)

    # ════════════════════════════════════════════════════════════════
    section("V8  并发 approve 下版本剪枝不出错")
    # ════════════════════════════════════════════════════════════════
    def test_concurrent_approve_prune():
        os.environ["VISUAL_KEEP_VERSIONS"] = "3"
        try:
            case = "test_v6_008"
            name = "page_conc"
            bid = make_baseline_id(case, name)
            _purge(bid)
            compare_screenshot(make_png(), case, "r0", name)
            compare_screenshot(make_png((50, 100, 150)), case, "r1", name)

            N = 5
            with ThreadPoolExecutor(max_workers=N) as ex:
                list(ex.map(lambda i: approve_baseline(bid, source="latest_current", by=f"u{i}"), range(N)))

            versions = list_versions(bid)
            # 总计 1 (created) + N (approved) = 6, 保留 3
            assert len(versions) == 3, f"versions {len(versions)} != 3"
            # 物理文件等于 sidecar 数量
            vdir = _versions_dir_for(bid)
            files = [f for f in os.listdir(vdir) if f.endswith(".png")]
            assert len(files) == 3, f"物理文件 {len(files)} != 3"
            # sidecar 引用的文件都还在
            for v in versions:
                assert v["exists"], f"版本物理丢失: {v}"
            delete_baseline(bid, delete_currents=True, delete_diffs=True)
        finally:
            os.environ.pop("VISUAL_KEEP_VERSIONS", None)

    t("5 线程并发 approve → 上限 3，物理与 sidecar 一致", test_concurrent_approve_prune)

    # ════════════════════════════════════════════════════════════════
    print()
    print("=" * 64)
    print(f"  结果: {passed} passed, {failed} failed")
    print("=" * 64)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
