"""
视觉测试企业级 Phase 2 回归：元素级 selector mask。

覆盖：
  M1  _resolve_mask_rect 兼容旧 rect 格式（无 type）
  M2  _resolve_mask_rect 处理 type=rect
  M3  _resolve_mask_rect 处理已展开的 type=selector + bbox
  M4  _resolve_mask_rect 拒绝未展开的 selector（无 bbox）
  M5  _resolve_mask_rect 处理 selector + padding（外扩）
  M6  _apply_masks 混合 rect + selector(已展开) 同时生效
  M7  _apply_masks 跳过未展开 selector，不报错
  M8  update_baseline_config 把 selector mask 持久化为 typed 结构
  M9  compare_screenshot 接受 typed mask，selector(已展开) 屏蔽动态区域
  E1  _resolve_selector_masks 用假 page mock 返回 bbox
  E2  _resolve_selector_masks 元素不可见 → 跳过
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


def make_png_with_rect(rect_color=(255, 0, 0), rect=(10, 10, 60, 30), bg=(255, 255, 255), size=(400, 200)):
    from PIL import Image, ImageDraw
    img = Image.new("RGB", size, bg)
    d = ImageDraw.Draw(img)
    x, y, w, h = rect
    d.rectangle([x, y, x + w, y + h], fill=rect_color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def section(t):
    print(f"\n{'=' * 64}\n  {t}\n{'=' * 64}")


# ════════════════════════════════════════════════════════════════
section("M1-M5  _resolve_mask_rect 单元")
# ════════════════════════════════════════════════════════════════
def test_resolve_legacy_rect():
    from services.visual_diff import _resolve_mask_rect
    r = _resolve_mask_rect({"x": 1, "y": 2, "w": 3, "h": 4})
    assert r == {"x": 1, "y": 2, "w": 3, "h": 4}


def test_resolve_typed_rect():
    from services.visual_diff import _resolve_mask_rect
    r = _resolve_mask_rect({"type": "rect", "x": 5, "y": 6, "w": 7, "h": 8})
    assert r == {"x": 5, "y": 6, "w": 7, "h": 8}


def test_resolve_selector_with_bbox():
    from services.visual_diff import _resolve_mask_rect
    r = _resolve_mask_rect({"type": "selector", "selector": ".x", "bbox": {"x": 10, "y": 20, "w": 30, "h": 40}})
    assert r == {"x": 10, "y": 20, "w": 30, "h": 40}


def test_resolve_selector_without_bbox_returns_none():
    from services.visual_diff import _resolve_mask_rect
    r = _resolve_mask_rect({"type": "selector", "selector": ".x"})
    assert r is None


def test_resolve_selector_with_padding():
    from services.visual_diff import _resolve_mask_rect
    r = _resolve_mask_rect({"type": "selector", "selector": ".x", "bbox": {"x": 10, "y": 20, "w": 30, "h": 40}, "padding": 5})
    # 外扩：x-5, y-5, w+10, h+10
    assert r == {"x": 5, "y": 15, "w": 40, "h": 50}


t("旧 rect 格式（无 type）", test_resolve_legacy_rect)
t("typed rect", test_resolve_typed_rect)
t("已展开 selector + bbox", test_resolve_selector_with_bbox)
t("未展开 selector → None", test_resolve_selector_without_bbox_returns_none)
t("selector + padding 外扩", test_resolve_selector_with_padding)


# ════════════════════════════════════════════════════════════════
section("M6-M7  _apply_masks 混合应用")
# ════════════════════════════════════════════════════════════════
def test_apply_mixed_masks():
    from PIL import Image
    from services.visual_diff import _apply_masks
    img = Image.new("RGB", (200, 100), (255, 255, 255))
    img2, applied = _apply_masks(img, [
        {"x": 10, "y": 10, "w": 30, "h": 30},                                          # 旧 rect
        {"type": "rect", "x": 60, "y": 10, "w": 30, "h": 30},                          # typed rect
        {"type": "selector", "selector": ".s", "bbox": {"x": 110, "y": 10, "w": 30, "h": 30}},  # selector 已展开
    ])
    assert applied == 3
    # 验证三块区域都涂黑
    assert img2.getpixel((25, 25)) == (0, 0, 0)
    assert img2.getpixel((75, 25)) == (0, 0, 0)
    assert img2.getpixel((125, 25)) == (0, 0, 0)
    # 没涂的位置仍是白色
    assert img2.getpixel((50, 50))[0] > 200


def test_apply_skips_unresolved_selector():
    from PIL import Image
    from services.visual_diff import _apply_masks
    img = Image.new("RGB", (200, 100), (255, 255, 255))
    img2, applied = _apply_masks(img, [
        {"type": "selector", "selector": ".unresolved"},   # 缺 bbox
        {"x": 5, "y": 5, "w": 30, "h": 30},                 # 仍生效
    ])
    assert applied == 1, f"未展开 selector 应被跳过，仅 rect 生效。applied={applied}"


t("混合 rect + 已展开 selector 同时生效", test_apply_mixed_masks)
t("未展开 selector 跳过不报错", test_apply_skips_unresolved_selector)


# ════════════════════════════════════════════════════════════════
section("M8  update_baseline_config 持久化 selector mask")
# ════════════════════════════════════════════════════════════════
def test_update_config_persists_selector():
    from services.visual_diff import compare_screenshot, make_baseline_id
    from services.visual_baseline_service import update_baseline_config, get_baseline_detail, delete_baseline

    case = "test_p2_sel_001"
    name = "page_with_clock"
    # 建基线
    compare_screenshot(make_png_with_rect(), case, "r0", name)
    bid = make_baseline_id(case, name)

    # 配置 mixed mask
    update_baseline_config(bid, masks=[
        {"x": 10, "y": 10, "w": 50, "h": 50},                                          # rect
        {"type": "selector", "selector": ".timestamp", "padding": 4},                  # selector
        {"type": "rect", "x": 100, "y": 0, "w": 30, "h": 20},                          # typed rect
    ], by="test")

    meta = get_baseline_detail(bid)["metadata"]
    masks = meta["masks"]
    assert len(masks) == 3
    types = {m["type"] for m in masks}
    assert types == {"rect", "selector"}
    sel_mask = next(m for m in masks if m["type"] == "selector")
    assert sel_mask["selector"] == ".timestamp"
    assert sel_mask["padding"] == 4
    rect_masks = [m for m in masks if m["type"] == "rect"]
    assert len(rect_masks) == 2
    # 旧式 rect 也被规范化为 typed
    assert all("x" in m and "y" in m for m in rect_masks)

    delete_baseline(bid, delete_currents=True, delete_diffs=True)


t("update_baseline_config 把 selector mask 持久化为 typed 结构", test_update_config_persists_selector)


# ════════════════════════════════════════════════════════════════
section("M9  compare_screenshot 接受展开后的 selector mask")
# ════════════════════════════════════════════════════════════════
def test_compare_with_resolved_selector_mask():
    from services.visual_diff import compare_screenshot, make_baseline_id
    from services.visual_baseline_service import update_baseline_config, delete_baseline

    case = "test_p2_sel_002"
    name = "dynamic_clock"

    # 1. 基线：页面在 (300,10,80,40) 处有红色矩形（模拟时钟）
    png_v1 = make_png_with_rect(rect_color=(255, 0, 0), rect=(300, 10, 80, 40))
    vr1 = compare_screenshot(png_v1, case, "r1", name, threshold=0.001)
    assert vr1.status == "baseline_created"

    # 2. 不带 mask → 颜色变蓝肯定 fail
    png_v2 = make_png_with_rect(rect_color=(0, 0, 255), rect=(300, 10, 80, 40))
    vr2 = compare_screenshot(png_v2, case, "r2", name, threshold=0.001)
    assert vr2.status == "failed"

    # 3. 通过 assertion 直接传一个已展开的 selector mask（模拟 engine 解析后的格式）
    bid = make_baseline_id(case, name)
    resolved_mask = [{
        "type": "selector",
        "selector": ".clock",
        "padding": 5,
        "bbox": {"x": 295, "y": 5, "w": 90, "h": 50},
    }]
    vr3 = compare_screenshot(png_v2, case, "r3", name, threshold=0.001, masks=resolved_mask)
    assert vr3.masks_applied >= 1
    assert vr3.status == "passed", f"selector mask 应屏蔽时钟变化但 status={vr3.status} ratio={vr3.diff_ratio}"

    delete_baseline(bid, delete_currents=True, delete_diffs=True)


t("compare_screenshot 接受展开后的 selector mask 屏蔽动态区域", test_compare_with_resolved_selector_mask)


# ════════════════════════════════════════════════════════════════
section("E1-E2  _resolve_selector_masks（mock playwright page）")
# ════════════════════════════════════════════════════════════════
class FakeLocator:
    def __init__(self, box):
        self._box = box

    @property
    def first(self):
        return self

    def bounding_box(self, timeout=None):
        return self._box


class FakePage:
    def __init__(self, mapping):
        # mapping: {selector: bounding_box_dict_or_None}
        self._map = mapping

    def locator(self, sel):
        return FakeLocator(self._map.get(sel))


def test_resolve_selector_masks_normal():
    from services.playwright_engine import _resolve_selector_masks
    page = FakePage({
        ".banner": {"x": 100, "y": 50, "width": 200, "height": 80},
    })
    out = _resolve_selector_masks(page, [
        {"type": "rect", "x": 0, "y": 0, "w": 10, "h": 10},   # 直接透传
        {"type": "selector", "selector": ".banner", "padding": 2},
    ])
    assert len(out) == 2
    rect = out[0]
    assert rect["type"] == "rect" and rect["w"] == 10
    sel = out[1]
    assert sel["type"] == "selector"
    assert sel["bbox"] == {"x": 100, "y": 50, "w": 200, "h": 80}
    assert sel["padding"] == 2


def test_resolve_selector_masks_invisible():
    from services.playwright_engine import _resolve_selector_masks
    page = FakePage({
        ".invisible": None,   # bounding_box 返回 None 表示不可见
    })
    out = _resolve_selector_masks(page, [
        {"type": "selector", "selector": ".invisible"},
    ])
    assert out == [], f"不可见元素应被跳过: {out}"


t("_resolve_selector_masks 正常解析 bbox", test_resolve_selector_masks_normal)
t("_resolve_selector_masks 不可见元素跳过", test_resolve_selector_masks_invisible)


# ════════════════════════════════════════════════════════════════
print()
print("=" * 64)
print(f"  结果: {passed} passed, {failed} failed")
print("=" * 64)
sys.exit(0 if failed == 0 else 1)
