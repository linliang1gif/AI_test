"""
视觉测试企业级 Phase 1 回归：命名空间隔离 + 批量操作。

覆盖：
  N1  baseline_id 命名空间生成（默认/部分/全量）
  N2  parse_baseline_id 反向还原
  N3  normalize_viewport 多种输入
  N4  路径穿越拦截升级（@、单独 .. 仍被拦）
  N5  不同 env 同一 case → 完全隔离的两个基线
  N6  不同 viewport 同一 case → 完全隔离
  N7  list_baselines 按 env / viewport / branch 过滤
  N8  list_namespaces 列出所有出现过的 ns
  B1  bulk_approve 全部成功
  B2  bulk_approve 含失败项不会终止
  B3  bulk_delete 全部成功
  B4  bulk_update_config 阈值 + algorithm
  B5  REST API：bulk endpoints + namespaces endpoint
  C1  向后兼容：旧 baseline_id（无 @）仍能 list/parse/use
"""
import os
import sys
import io
import shutil

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


def make_png(color=(255, 255, 255), size=(200, 100)):
    from PIL import Image
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def section(t):
    print(f"\n{'=' * 64}\n  {t}\n{'=' * 64}")


# ════════════════════════════════════════════════════════════════
section("N1-N4  命名空间生成 / 解析 / 视口标准化 / 安全规则")
# ════════════════════════════════════════════════════════════════
def test_make_baseline_id_default():
    from services.visual_diff import make_baseline_id
    assert make_baseline_id("tc1", "home") == "tc1_home"


def test_make_baseline_id_partial():
    from services.visual_diff import make_baseline_id
    assert make_baseline_id("tc1", "home", env="prod") == "tc1_home@prod"
    assert make_baseline_id("tc1", "home", viewport="375x667") == "tc1_home@default@375x667"
    assert make_baseline_id("tc1", "home", branch="feat-x") == "tc1_home@default@default@feat-x"


def test_make_baseline_id_full():
    from services.visual_diff import make_baseline_id
    assert make_baseline_id("tc1", "home", env="prod", viewport=(1920, 1080), branch="main") == "tc1_home@prod@1920x1080@main"


def test_parse_baseline_id():
    from services.visual_diff import parse_baseline_id
    p = parse_baseline_id("tc1_home")
    assert p == {"core": "tc1_home", "env": "default", "viewport": "default", "branch": "default"}
    p = parse_baseline_id("tc1_home@prod@375x667@feat-x")
    assert p == {"core": "tc1_home", "env": "prod", "viewport": "375x667", "branch": "feat-x"}


def test_normalize_viewport():
    from services.visual_diff import normalize_viewport
    assert normalize_viewport(None) == "default"
    assert normalize_viewport("") == "default"
    assert normalize_viewport("default") == "default"
    assert normalize_viewport("1920x1080") == "1920x1080"
    assert normalize_viewport((375, 667)) == "375x667"
    assert normalize_viewport({"width": 1366, "height": 768}) == "1366x768"
    assert normalize_viewport("invalid") == "default"


def test_safety_at_allowed():
    """@ 允许（命名空间分隔符），但仍要拒 .. / / \\"""
    from services.visual_diff import _safe_baseline_path
    # @ 合法
    p = _safe_baseline_path("tc1_home@prod@1920x1080", ".png")
    assert "tc1_home@prod@1920x1080.png" in p
    # / 仍拦
    for bad in ("a/b@prod", "..@prod", "a@..", "a@b@..", "a;b"):
        try:
            _safe_baseline_path(bad)
            assert False, f"应当拒绝: {bad!r}"
        except ValueError:
            pass


t("make_baseline_id 默认值", test_make_baseline_id_default)
t("make_baseline_id 部分命名空间", test_make_baseline_id_partial)
t("make_baseline_id 全命名空间", test_make_baseline_id_full)
t("parse_baseline_id 反向还原", test_parse_baseline_id)
t("normalize_viewport 多种输入", test_normalize_viewport)
t("路径穿越拦截升级（@ 允许，.. 拒绝）", test_safety_at_allowed)


# ════════════════════════════════════════════════════════════════
section("N5-N8  命名空间隔离 + 列表过滤 + namespaces 接口")
# ════════════════════════════════════════════════════════════════
TEST_CASE = "test_ns_001"
TEST_NAME = "page_a"


def cleanup_ns():
    from services.visual_diff import (
        BASELINE_DIR, CURRENT_DIR, DIFF_DIR, META_DIR
    )
    for d in (BASELINE_DIR, CURRENT_DIR, DIFF_DIR, META_DIR):
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if f.startswith(TEST_CASE + "_"):
                try:
                    os.remove(os.path.join(d, f))
                except Exception:
                    pass


cleanup_ns()


def test_diff_envs_isolated():
    """同一 case+name 在不同 env 下应当生成 2 个独立基线。"""
    from services.visual_diff import compare_screenshot, make_baseline_id
    png = make_png()
    bid_dev = make_baseline_id(TEST_CASE, TEST_NAME, env="dev")
    bid_prod = make_baseline_id(TEST_CASE, TEST_NAME, env="prod")
    assert bid_dev != bid_prod, f"两个 env 应不同 bid: dev={bid_dev} prod={bid_prod}"

    vr_dev = compare_screenshot(png, TEST_CASE, "r1", TEST_NAME, env="dev")
    vr_prod = compare_screenshot(png, TEST_CASE, "r1", TEST_NAME, env="prod")
    assert vr_dev.status == "baseline_created" and vr_prod.status == "baseline_created"
    assert vr_dev.baseline_id != vr_prod.baseline_id
    assert vr_dev.env == "dev" and vr_prod.env == "prod"


def test_diff_viewports_isolated():
    """不同 viewport 也应隔离。"""
    from services.visual_diff import compare_screenshot
    png = make_png()
    vr_a = compare_screenshot(png, TEST_CASE, "r1", "page_v", viewport=(1920, 1080))
    vr_b = compare_screenshot(png, TEST_CASE, "r1", "page_v", viewport=(375, 667))
    assert vr_a.baseline_id != vr_b.baseline_id
    assert vr_a.viewport == "1920x1080" and vr_b.viewport == "375x667"


def test_list_filter_by_env():
    from services.visual_baseline_service import list_baselines
    items_dev = list_baselines(case_id=TEST_CASE, env="dev")
    items_prod = list_baselines(case_id=TEST_CASE, env="prod")
    bids_dev = {x["baseline_id"] for x in items_dev}
    bids_prod = {x["baseline_id"] for x in items_prod}
    assert any("@dev" in b for b in bids_dev), f"过滤 dev 应只含 @dev 的基线: {bids_dev}"
    assert any("@prod" in b for b in bids_prod), f"过滤 prod 应只含 @prod 的基线: {bids_prod}"
    assert not (bids_dev & bids_prod), "过滤结果不应交叉"


def test_list_namespaces():
    from services.visual_baseline_service import list_namespaces
    ns = list_namespaces()
    assert "envs" in ns and "viewports" in ns and "branches" in ns
    assert "dev" in ns["envs"] and "prod" in ns["envs"]
    # 至少包含 default + 1920x1080 + 375x667
    assert "1920x1080" in ns["viewports"]
    assert "375x667" in ns["viewports"]


t("不同 env 同 case → 独立基线", test_diff_envs_isolated)
t("不同 viewport 同 case → 独立基线", test_diff_viewports_isolated)
t("list_baselines 按 env 过滤", test_list_filter_by_env)
t("list_namespaces 返回 envs/viewports/branches", test_list_namespaces)


# ════════════════════════════════════════════════════════════════
section("B1-B4  批量操作（service 层）")
# ════════════════════════════════════════════════════════════════
def test_bulk_approve_success():
    from services.visual_diff import compare_screenshot, make_baseline_id
    from services.visual_baseline_service import bulk_approve
    case = "test_bulk_001"
    bids = []
    for i in range(3):
        png = make_png()
        compare_screenshot(png, case, f"run-{i}", f"page_{i}")
        # 同样的 png 再跑一次，建立 current 历史
        compare_screenshot(make_png(color=(0, 0, 0)), case, f"run-{i}-2", f"page_{i}")
        bids.append(make_baseline_id(case, f"page_{i}"))
    r = bulk_approve(bids, source="latest_current", by="test_bulk")
    assert r["success_count"] == 3, f"全成: {r}"
    assert r["fail_count"] == 0


def test_bulk_approve_partial_fail():
    from services.visual_baseline_service import bulk_approve
    # 一个真实存在 + 一个假的
    bids = ["test_bulk_001_page_0", "test_nonexist_xyz"]
    r = bulk_approve(bids, by="test_bulk")
    assert r["success_count"] >= 1
    assert r["fail_count"] >= 1


def test_bulk_delete():
    from services.visual_baseline_service import bulk_delete, list_baselines
    from services.visual_diff import make_baseline_id
    case = "test_bulk_001"
    bids = [make_baseline_id(case, f"page_{i}") for i in range(3)]
    r = bulk_delete(bids, delete_currents=True, delete_diffs=True, by="test_bulk")
    assert r["success_count"] == 3, f"批量删除: {r}"
    items = list_baselines(case_id=case)
    assert not items, f"应已全删: {[x['baseline_id'] for x in items]}"


def test_bulk_update_config():
    from services.visual_diff import compare_screenshot, make_baseline_id
    from services.visual_baseline_service import bulk_update_config, get_baseline_detail
    case = "test_bulk_cfg_001"
    bids = []
    for i in range(2):
        compare_screenshot(make_png(), case, "r0", f"p_{i}")
        bids.append(make_baseline_id(case, f"p_{i}"))
    r = bulk_update_config(bids, threshold=0.12, algorithm="ssim", by="test_bulk")
    assert r["success_count"] == 2
    for bid in bids:
        meta = get_baseline_detail(bid)["metadata"]
        assert abs(meta["threshold"] - 0.12) < 1e-6
        assert meta["algorithm"] == "ssim"
    # 清理
    from services.visual_baseline_service import bulk_delete
    bulk_delete(bids, delete_currents=True, delete_diffs=True)


t("bulk_approve 全成功", test_bulk_approve_success)
t("bulk_approve 部分失败不终止", test_bulk_approve_partial_fail)
t("bulk_delete 完整清理", test_bulk_delete)
t("bulk_update_config 修改阈值+算法", test_bulk_update_config)


# ════════════════════════════════════════════════════════════════
section("B5  REST API：bulk + namespaces")
# ════════════════════════════════════════════════════════════════
def test_api_namespaces_and_bulk():
    from fastapi.testclient import TestClient
    from backend.app import create_app
    from services.visual_diff import compare_screenshot, make_baseline_id
    from services.visual_baseline_service import bulk_delete

    app = create_app()
    client = TestClient(app)

    # 准备数据
    case = "test_api_bulk_001"
    bids = []
    for i in range(2):
        compare_screenshot(make_png(), case, "r0", f"x_{i}", env="staging")
        bids.append(make_baseline_id(case, f"x_{i}", env="staging"))

    # namespaces 接口
    r = client.get("/api/v2/visual/namespaces")
    assert r.status_code == 200
    ns = r.json()["namespaces"]
    assert "staging" in ns["envs"]

    # 列表带 env 过滤
    r = client.get("/api/v2/visual/baselines?case_id={}&env=staging".format(case))
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) >= 2
    assert all("@staging" in x["baseline_id"] for x in items)
    assert all(x["env"] == "staging" for x in items)

    # bulk approve
    r = client.post("/api/v2/visual/bulk/approve",
                    json={"baseline_ids": bids, "by": "api_test"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success_count"] == 2

    # bulk config
    r = client.post("/api/v2/visual/bulk/config",
                    json={"baseline_ids": bids, "threshold": 0.09, "by": "api_test"})
    assert r.status_code == 200
    assert r.json()["success_count"] == 2

    # bulk delete
    r = client.post("/api/v2/visual/bulk/delete",
                    json={"baseline_ids": bids, "delete_currents": True, "delete_diffs": True})
    assert r.status_code == 200
    assert r.json()["success_count"] == 2

    # bulk 空列表 → 400
    r = client.post("/api/v2/visual/bulk/approve", json={"baseline_ids": []})
    assert r.status_code == 400


t("REST API：namespaces + bulk approve/config/delete", test_api_namespaces_and_bulk)


# ════════════════════════════════════════════════════════════════
section("C1  向后兼容：旧 baseline_id（无 @）仍可用")
# ════════════════════════════════════════════════════════════════
def test_backward_compat_old_bid():
    from services.visual_diff import compare_screenshot, parse_baseline_id, make_baseline_id
    from services.visual_baseline_service import get_baseline_detail, list_baselines, delete_baseline

    case = "test_compat_001"
    name = "old_style"
    # 调用时不传 env/viewport/branch，应当生成无 @ 的旧式 bid
    vr = compare_screenshot(make_png(), case, "r0", name)
    assert vr.baseline_id == f"{case}_{name}"
    assert "@" not in vr.baseline_id
    assert vr.env == "default" and vr.viewport == "default" and vr.branch == "default"

    # parse 应当返回全 default
    p = parse_baseline_id(vr.baseline_id)
    assert p["env"] == "default"

    # 详情接口正常
    detail = get_baseline_detail(vr.baseline_id)
    assert detail["metadata"]["env"] == "default"

    # 列表里能看到
    items = list_baselines(case_id=case)
    assert any(x["baseline_id"] == vr.baseline_id for x in items)

    # 清理
    delete_baseline(vr.baseline_id, delete_currents=True, delete_diffs=True)


t("旧 baseline_id（无 @）完整可用", test_backward_compat_old_bid)


# 清理 N5/N6 留下的测试基线
def final_cleanup():
    from services.visual_baseline_service import list_baselines, bulk_delete
    items = list_baselines(case_id=TEST_CASE)
    if items:
        bulk_delete([x["baseline_id"] for x in items],
                    delete_currents=True, delete_diffs=True)


final_cleanup()

# ════════════════════════════════════════════════════════════════
print()
print("=" * 64)
print(f"  结果: {passed} passed, {failed} failed")
print("=" * 64)
sys.exit(0 if failed == 0 else 1)
