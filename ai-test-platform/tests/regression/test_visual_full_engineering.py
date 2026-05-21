"""
Visual Testing - 工程级完整能力测试。

覆盖：
  P1  baseline_id 安全规则 + 路径穿越拦截
  P2  首次执行自动创建基线 + sidecar metadata
  P3  二次执行 + 像素 diff + sidecar 优先
  P4  mask 区域屏蔽（动态变化的区域被忽略）
  P5  SSIM 算法（如 scikit-image 可用）
  P6  baseline_service: list / detail / approve / update_config / delete
  P7  REST API 接口（list / approve / config / delete / pending-reviews / stats）
  P8  路径穿越攻击防御

运行：
  python scripts/test_visual_full_engineering.py
"""
import os
import sys
import io
import time
import shutil
import tempfile
import traceback
from typing import List

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


passed = 0
failed = 0
results: List[str] = []


def t(name: str, fn):
    global passed, failed
    print(f"  [{name}] ", end="", flush=True)
    try:
        fn()
        passed += 1
        print("PASS")
        results.append(f"  ✓ {name}")
    except AssertionError as e:
        failed += 1
        print(f"FAIL: {e}")
        results.append(f"  ✗ {name}: {e}")
    except Exception as e:
        failed += 1
        print(f"ERROR: {e}")
        traceback.print_exc()
        results.append(f"  ✗ {name}: {e}")


def make_png(color=(255, 255, 255), size=(400, 200)):
    from PIL import Image
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def make_png_with_rect(rect_color=(255, 0, 0), rect=(10, 10, 60, 30), bg=(255, 255, 255), size=(400, 200)):
    """生成带一个矩形的 PNG。rect=(x,y,w,h)"""
    from PIL import Image, ImageDraw
    img = Image.new("RGB", size, bg)
    d = ImageDraw.Draw(img)
    x, y, w, h = rect
    d.rectangle([x, y, x + w, y + h], fill=rect_color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def section(title):
    print(f"\n{'=' * 64}\n  {title}\n{'=' * 64}")


# ════════════════════════════════════════════════════════════════
section("P1  baseline_id 安全规则 + 路径穿越拦截")
# ════════════════════════════════════════════════════════════════
def test_safe_path_legal():
    from services.visual_diff import _safe_baseline_path, BASELINE_DIR, META_DIR
    p = _safe_baseline_path("case_001_login", ".png")
    assert p.endswith("case_001_login.png")
    assert os.path.normpath(BASELINE_DIR) in os.path.normpath(p)
    p2 = _safe_baseline_path("case_001_login", ".meta.json")
    assert p2.endswith(".meta.json")
    assert os.path.normpath(META_DIR) in os.path.normpath(p2)


def test_safe_path_traversal_rejected():
    from services.visual_diff import _safe_baseline_path
    bad_ids = ["../etc/passwd", "..", "../foo", "a/b", "a\\b", "x;y", "x|y"]
    for bid in bad_ids:
        try:
            _safe_baseline_path(bid)
            assert False, f"应当拒绝: {bid!r}"
        except ValueError:
            pass


def test_safe_path_unicode_ok():
    from services.visual_diff import _safe_baseline_path
    p = _safe_baseline_path("case_001_登录页", ".png")
    assert "登录页" in p


t("合法 baseline_id 解析", test_safe_path_legal)
t("路径穿越被拦截", test_safe_path_traversal_rejected)
t("中文 baseline_id 允许", test_safe_path_unicode_ok)


# ════════════════════════════════════════════════════════════════
section("P2  首次执行自动创建基线 + sidecar metadata")
# ════════════════════════════════════════════════════════════════
TEST_CASE = "test_eng_001"
TEST_NAME = "home_page"


def cleanup_test_case():
    from services.visual_diff import (
        BASELINE_DIR, CURRENT_DIR, DIFF_DIR, META_DIR, make_baseline_id,
    )
    bid = make_baseline_id(TEST_CASE, TEST_NAME)
    for d, suffix in [(BASELINE_DIR, ""), (META_DIR, ""), (CURRENT_DIR, ""), (DIFF_DIR, "")]:
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if f.startswith(bid):
                try:
                    os.remove(os.path.join(d, f))
                except Exception:
                    pass


cleanup_test_case()


def test_first_run_creates_baseline():
    from services.visual_diff import compare_screenshot, make_baseline_id, _safe_baseline_path, read_meta
    bid = make_baseline_id(TEST_CASE, TEST_NAME)
    png = make_png_with_rect()
    vr = compare_screenshot(png, TEST_CASE, "run-1", TEST_NAME, threshold=0.05)
    assert vr.status == "baseline_created", f"status={vr.status}"
    assert vr.baseline_id == bid
    assert os.path.exists(_safe_baseline_path(bid, ".png"))
    meta = read_meta(bid)
    assert meta.get("case_id") == TEST_CASE
    assert meta.get("name") == TEST_NAME
    assert len(meta.get("history", [])) == 1
    assert meta["history"][0]["event"] == "created"


t("首次执行：自动创建基线 + sidecar", test_first_run_creates_baseline)


# ════════════════════════════════════════════════════════════════
section("P3  二次执行 + 像素 diff + sidecar 优先")
# ════════════════════════════════════════════════════════════════
def test_second_run_passes_when_identical():
    from services.visual_diff import compare_screenshot
    png = make_png_with_rect()  # 相同
    vr = compare_screenshot(png, TEST_CASE, "run-2", TEST_NAME, threshold=0.05)
    assert vr.status == "passed", f"status={vr.status} ratio={vr.diff_ratio}"
    assert vr.diff_ratio <= 0.05
    assert os.path.exists(vr.diff_path)


def test_second_run_fails_when_different():
    from services.visual_diff import compare_screenshot
    # 把矩形改大，让 diff 显著超过 5%
    png = make_png_with_rect(rect=(10, 10, 200, 150))
    vr = compare_screenshot(png, TEST_CASE, "run-3", TEST_NAME, threshold=0.05)
    assert vr.status == "failed", f"status={vr.status} ratio={vr.diff_ratio}"
    assert vr.diff_ratio > 0.05


t("相同截图 → passed", test_second_run_passes_when_identical)
t("显著变化 → failed", test_second_run_fails_when_different)


# ════════════════════════════════════════════════════════════════
section("P4  mask 区域屏蔽")
# ════════════════════════════════════════════════════════════════
MASK_CASE = "test_mask_001"
MASK_NAME = "with_clock"


def cleanup_mask_case():
    from services.visual_diff import (
        BASELINE_DIR, CURRENT_DIR, DIFF_DIR, META_DIR, make_baseline_id,
    )
    bid = make_baseline_id(MASK_CASE, MASK_NAME)
    for d in (BASELINE_DIR, META_DIR, CURRENT_DIR, DIFF_DIR):
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if f.startswith(bid):
                try:
                    os.remove(os.path.join(d, f))
                except Exception:
                    pass


cleanup_mask_case()


def test_mask_blocks_dynamic_region():
    """模拟一个变化的"时钟"区域，配置 mask 覆盖后 diff 应当为 ≈0。"""
    from services.visual_diff import compare_screenshot, update_baseline_config_path  # noqa
    # 1. 首次 baseline，时钟显示 12:00（红色矩形）
    png_v1 = make_png_with_rect(rect_color=(255, 0, 0), rect=(300, 10, 80, 40))
    vr1 = compare_screenshot(png_v1, MASK_CASE, "run-1", MASK_NAME, threshold=0.001)
    assert vr1.status == "baseline_created"

    # 2. 不带 mask 时，时钟变化导致失败
    png_v2 = make_png_with_rect(rect_color=(0, 0, 255), rect=(300, 10, 80, 40))  # 蓝色
    vr2 = compare_screenshot(png_v2, MASK_CASE, "run-2", MASK_NAME, threshold=0.001)
    assert vr2.status == "failed", f"应当失败但 status={vr2.status} ratio={vr2.diff_ratio}"

    # 3. 配置 mask 覆盖时钟区域
    from services.visual_baseline_service import update_baseline_config
    from services.visual_diff import make_baseline_id
    bid = make_baseline_id(MASK_CASE, MASK_NAME)
    update_baseline_config(bid, masks=[{"x": 295, "y": 5, "w": 95, "h": 50}], by="test")

    # 4. 再次执行，时钟变化但被 mask 屏蔽 → 应当 passed
    vr3 = compare_screenshot(png_v2, MASK_CASE, "run-3", MASK_NAME, threshold=0.001)
    assert vr3.masks_applied >= 1, f"masks_applied={vr3.masks_applied}"
    assert vr3.status == "passed", f"加 mask 后应当 passed 但 status={vr3.status} ratio={vr3.diff_ratio}"


# 修：visual_diff 没有 update_baseline_config_path，去掉 noqa 引用
def test_mask_blocks_dynamic_region_v2():
    from services.visual_diff import compare_screenshot, make_baseline_id
    from services.visual_baseline_service import update_baseline_config

    cleanup_mask_case()

    png_v1 = make_png_with_rect(rect_color=(255, 0, 0), rect=(300, 10, 80, 40))
    vr1 = compare_screenshot(png_v1, MASK_CASE, "run-1", MASK_NAME, threshold=0.001)
    assert vr1.status == "baseline_created"

    png_v2 = make_png_with_rect(rect_color=(0, 0, 255), rect=(300, 10, 80, 40))
    vr2 = compare_screenshot(png_v2, MASK_CASE, "run-2", MASK_NAME, threshold=0.001)
    assert vr2.status == "failed"

    bid = make_baseline_id(MASK_CASE, MASK_NAME)
    update_baseline_config(bid, masks=[{"x": 295, "y": 5, "w": 95, "h": 50}], by="test")

    vr3 = compare_screenshot(png_v2, MASK_CASE, "run-3", MASK_NAME, threshold=0.001)
    assert vr3.masks_applied >= 1, f"masks_applied={vr3.masks_applied}"
    assert vr3.status == "passed", f"加 mask 后应当 passed 但 status={vr3.status} ratio={vr3.diff_ratio}"


t("mask 屏蔽动态区域 → 由失败变 passed", test_mask_blocks_dynamic_region_v2)


# ════════════════════════════════════════════════════════════════
section("P5  SSIM 算法（可选）")
# ════════════════════════════════════════════════════════════════
def test_ssim_or_fallback():
    SSIM_CASE = "test_ssim_001"
    SSIM_NAME = "ssim_page"

    from services.visual_diff import (
        compare_screenshot, make_baseline_id, BASELINE_DIR, META_DIR, CURRENT_DIR, DIFF_DIR
    )
    bid = make_baseline_id(SSIM_CASE, SSIM_NAME)
    for d in (BASELINE_DIR, META_DIR, CURRENT_DIR, DIFF_DIR):
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if f.startswith(bid):
                try:
                    os.remove(os.path.join(d, f))
                except Exception:
                    pass

    png = make_png_with_rect()
    vr1 = compare_screenshot(png, SSIM_CASE, "run-1", SSIM_NAME, algorithm="ssim")
    assert vr1.status == "baseline_created"

    # 配置 algorithm=ssim
    from services.visual_baseline_service import update_baseline_config
    update_baseline_config(bid, algorithm="ssim", by="test")

    vr2 = compare_screenshot(png, SSIM_CASE, "run-2", SSIM_NAME)
    # 不论 ssim 是否安装，都应该是 passed（相同图）
    assert vr2.status == "passed", f"status={vr2.status} algorithm={vr2.algorithm}"
    print(f"      [info] 使用算法: {vr2.algorithm}")


t("SSIM/Pixel 算法切换可工作（自动 fallback）", test_ssim_or_fallback)


# ════════════════════════════════════════════════════════════════
section("P6  visual_baseline_service 单元测试")
# ════════════════════════════════════════════════════════════════
def test_list_baselines_contains_test():
    from services.visual_baseline_service import list_baselines
    items = list_baselines(limit=1000)
    bids = {x["baseline_id"] for x in items}
    assert f"{TEST_CASE}_{TEST_NAME}" in bids, f"未找到测试基线; 现有: {sorted(bids)[:5]}"


def test_get_baseline_detail():
    from services.visual_baseline_service import get_baseline_detail
    bid = f"{TEST_CASE}_{TEST_NAME}"
    detail = get_baseline_detail(bid)
    assert detail["baseline_id"] == bid
    assert detail["exists"]
    assert detail["metadata"]["case_id"] == TEST_CASE
    assert len(detail["recent_currents"]) >= 1
    assert len(detail["recent_diffs"]) >= 1


def test_approve_baseline_latest():
    from services.visual_baseline_service import approve_baseline, get_baseline_detail
    bid = f"{TEST_CASE}_{TEST_NAME}"
    before = get_baseline_detail(bid)["metadata"].get("approve_count", 0)
    r = approve_baseline(bid, source="latest_current", by="pytest", note="测试批准")
    assert r["success"]
    after = get_baseline_detail(bid)["metadata"].get("approve_count", 0)
    assert after == before + 1
    history = get_baseline_detail(bid)["metadata"]["history"]
    assert any(h["event"] == "approved" and h["by"] == "pytest" for h in history)


def test_approve_baseline_specific_run():
    from services.visual_baseline_service import approve_baseline
    bid = f"{TEST_CASE}_{TEST_NAME}"
    r = approve_baseline(bid, source="specific_run", run_id="run-2", by="pytest", note="指定 run")
    assert r["success"]


def test_update_config():
    from services.visual_baseline_service import update_baseline_config, get_baseline_detail
    bid = f"{TEST_CASE}_{TEST_NAME}"
    r = update_baseline_config(bid, threshold=0.08, algorithm="pixel", masks=[
        {"x": 0, "y": 0, "w": 50, "h": 50}
    ], by="pytest")
    assert r["success"]
    meta = get_baseline_detail(bid)["metadata"]
    assert abs(meta["threshold"] - 0.08) < 1e-6
    assert len(meta["masks"]) == 1


def test_delete_baseline():
    from services.visual_baseline_service import delete_baseline
    from services.visual_diff import _safe_baseline_path
    # 用一个一次性的 case
    from services.visual_diff import compare_screenshot, make_baseline_id
    case = "test_eng_delete"
    name = "tmp"
    bid = make_baseline_id(case, name)
    png = make_png()
    compare_screenshot(png, case, "run-d", name)
    assert os.path.exists(_safe_baseline_path(bid, ".png"))
    r = delete_baseline(bid, delete_currents=True, delete_diffs=True, by="pytest")
    assert r["success"]
    assert not os.path.exists(_safe_baseline_path(bid, ".png"))


t("list_baselines 包含测试基线", test_list_baselines_contains_test)
t("get_baseline_detail 返回完整字段", test_get_baseline_detail)
t("approve_baseline (latest_current)", test_approve_baseline_latest)
t("approve_baseline (specific_run)", test_approve_baseline_specific_run)
t("update_baseline_config", test_update_config)
t("delete_baseline 完整清理", test_delete_baseline)


# ════════════════════════════════════════════════════════════════
section("P7  REST API（仅在 backend 启动后跑）")
# ════════════════════════════════════════════════════════════════
def test_api_via_test_client():
    from fastapi.testclient import TestClient
    from backend.app import create_app
    app = create_app()
    client = TestClient(app)

    # stats
    r = client.get("/api/v2/visual/stats")
    assert r.status_code == 200, r.text
    assert "stats" in r.json()

    # list
    r = client.get("/api/v2/visual/baselines?limit=10")
    assert r.status_code == 200
    body = r.json()
    assert "items" in body

    # detail（用 P2/P3 留下来的基线）
    bid = f"{TEST_CASE}_{TEST_NAME}"
    r = client.get(f"/api/v2/visual/baselines/{bid}")
    assert r.status_code == 200
    assert r.json()["baseline"]["baseline_id"] == bid

    # config 更新
    r = client.post(f"/api/v2/visual/baselines/{bid}/config", json={
        "threshold": 0.07,
        "algorithm": "pixel",
        "masks": [{"x": 1, "y": 1, "w": 10, "h": 10}],
        "by": "test_api",
        "note": "api_test"
    })
    assert r.status_code == 200, r.text

    # 路径穿越拦截
    r = client.get("/api/v2/visual/baselines/..%2Fpasswd")
    assert r.status_code in (400, 404), f"应当拦截但 {r.status_code}"

    # pending-reviews（需要 DB，但能正常返回结构）
    r = client.get("/api/v2/visual/pending-reviews?days=1&limit=5")
    assert r.status_code == 200
    assert "items" in r.json()


t("FastAPI TestClient 全链路", test_api_via_test_client)


# ════════════════════════════════════════════════════════════════
print()
print("=" * 64)
print(f"  结果: {passed} passed, {failed} failed")
print("=" * 64)
for line in results:
    print(line)

sys.exit(0 if failed == 0 else 1)
